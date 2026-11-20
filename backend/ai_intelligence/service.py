"""Application services, shadow-mode safeguards, and durable controlled tasks."""
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from psycopg.types.json import Jsonb
from .collector import synchronize
from .github import redact, GitHubError
from .store import label, timestamp
from . import ml
from .rca import analyze, configured_provider, provider_configuration


class IntelligenceService:
    def __init__(self,store,client):
        self.store=store;self.client=client
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix="bytexl-ai")

    def train(self,repo):
        result=ml.train(self.store,repo)
        if result['status']=='experimental':
            for item in result['backtest']:
                self.store.query("""INSERT INTO ai_predictions(id,repository,run_id,attempt,model_version,predicted_at,feature_snapshot,probability,threshold,predicted_class,mode,verification_status)
                    VALUES(gen_random_uuid(),%s,%s,%s,%s,now(),%s,%s,%s,%s,'backtest','historical_backtest') ON CONFLICT DO NOTHING""",
                    (repo,item['run_id'],item['attempt'],result['version'],Jsonb({'values':item['features'],'historical_feature_time':item['feature_time']}),item['probability'],result['threshold'],int(item['probability']>=result['threshold'])))
        return result

    def rca(self,repo,run_id,attempt):
        run=self.store.run(repo,run_id,attempt)
        if not run or run['status']!='completed' or run['conclusion']!='failure':
            raise ValueError("RCA requires a synchronized, completed failed run and exact attempt.")
        provider=configured_provider()
        report=analyze(self.store.jobs(repo,run_id,attempt),provider,workflow=run['payload'].get('name'))
        report.update(workflow=run['payload'].get('name'),run_id=run_id,attempt=attempt)
        report_id=self.store.save_report(repo,run_id,attempt,report)
        return {'report_id':report_id,'report':report}

    def _decision(self,repo,run,decision,reason):
        self.store.query("""INSERT INTO ai_shadow_events(repository,run_id,attempt,decision,reason) VALUES(%s,%s,%s,%s,%s)
             ON CONFLICT(repository,run_id,attempt) DO UPDATE SET observed_at=now(),decision=excluded.decision,reason=excluded.reason""",
             (repo,run['id'],run.get('run_attempt',1),decision,reason))
        return {'status':decision,'reason':reason,'run_id':run['id']}

    def predict(self,repo,run_id,attempt):
        # Never accept run status/features/outcomes supplied by a browser or webhook.
        run=self.client.run(repo,run_id,attempt)
        at=datetime.now(timezone.utc)
        if run['status']!='queued' or run.get('conclusion') is not None:
            return self._decision(repo,run,'skipped','Only a currently queued run is eligible; no retrospective live predictions.')
        models=[model for model in self.store.models(repo) if model['status']=='experimental' and model['metrics'].get('feature_version')==ml.FEATURE_VERSION and model['created_at']<=at]
        if not models:
            return self._decision(repo,run,'insufficient_data','No fitted experimental model is available. No probability generated.')
        model=models[0]
        if model['trained_through'] and timestamp(model['trained_through'])>=timestamp(run['created_at']):
            return self._decision(repo,run,'skipped','Training outcomes overlap the target prediction time.')
        snapshot=self.client.snapshot(repo,run)
        target={'run_id':run['id'],'attempt':run.get('run_attempt',1),'workflow_id':run['workflow_id'],'commit_sha':run['head_sha'],'payload':run}
        values,provenance=ml.features(target,self.store.runs(repo),snapshot,at)
        pipeline=ml.load_model(model);probability=float(pipeline.predict_proba([values])[0,1])
        fresh=self.client.run(repo,run_id,attempt)
        if fresh['status']!='queued' or fresh.get('conclusion') is not None or fresh['head_sha']!=run['head_sha'] or fresh.get('run_attempt',1)!=attempt:
            return self._decision(repo,run,'skipped','Run started, finished, or changed while collecting features; no live prediction persisted.')
        self.store.save_run(repo,fresh,[])
        predicted_at=datetime.now(timezone.utc)
        # Linear-model factors are descriptive model contributions, not causal claims.
        factors=[]
        if hasattr(pipeline[-1],'coef_'):
            transformed=pipeline[:-1].transform([values])[0]
            contributions=pipeline[-1].coef_[0]*transformed
            names=pipeline[0].get_feature_names_out()
            factors=[{'feature':str(names[i]),'log_odds_contribution':float(contributions[i])} for i in sorted(range(len(names)),key=lambda i:abs(contributions[i]),reverse=True)[:5]]
        stored=self.store.predict(repo,run,model['version'],{'values':values,'provenance':provenance,'factors':factors},probability,model['metrics']['threshold'],predicted_at)
        return self._decision(repo,run,'predicted' if stored else 'already_predicted','Experimental shadow prediction persisted before observing an outcome; CI behavior is unchanged.')

    def evaluation(self,repo):
        predictions=self.store.predictions(repo)
        live=[p for p in predictions if p['mode']=='shadow' and p.get('actual_label') is not None and p['verification_status']=='matched']
        result={'live_evaluated':len(live),'live_metrics':None,'backtest_count':sum(p['mode']=='backtest' for p in predictions)}
        if live:
            # Use each persisted decision threshold for classification metrics.
            from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,confusion_matrix
            y=[p['actual_label'] for p in live];pred=[p['predicted_class'] for p in live]
            result['live_metrics']=ml.metrics(y,[p['probability'] for p in live],.5)
            result['live_metrics'].update(accuracy=float(accuracy_score(y,pred)),precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)),confusion_matrix=confusion_matrix(y,pred,labels=[0,1]).tolist())
        reports=self.store.reports(repo)
        reviewed=self.store.query("SELECT v.report_id,v.reviewer,v.review,r.report FROM ai_rca_reviews v JOIN ai_rca_reports r ON r.id=v.report_id WHERE r.repository=%s",(repo,))
        fields=['category_correct','step_correct','evidence_correct','fix_correct']
        result['rca']={'reviewed':len(reviewed),'unverified':sum(r['verification_status']=='unverified' for r in reports),'by_engine':{}}
        for engine in ['llm_grounded','evidence_rules']:
            rows=[r for r in reviewed if r['report']['engine']==engine]
            result['rca']['by_engine'][engine]={'reviewed':len(rows),**{f:sum(bool(r['review'][f]) for r in rows)/len(rows) if rows else None for f in fields},'unsupported_claim_rate':sum(bool(r['review']['unsupported_claims']) for r in rows)/len(rows) if rows else None}
        from .reviews import agreement
        result['rca']['human_reviewer_agreement']=agreement(reviewed)
        result['rca']['agreement_note']='Agreement requires at least two distinct reviewer submissions for the same report; identifiers are self-reported.'
        from pathlib import Path
        import hashlib
        benchmark=Path(__file__).parents[1]/'reports'/'rca_regression.json'
        result['rca_benchmark']=None
        if benchmark.exists():
            measured=json.loads(benchmark.read_text())
            if measured.get('source_sha256')==hashlib.sha256(Path(__file__).with_name('rca.py').read_bytes()).hexdigest():
                result['rca_benchmark']=measured
        return result

    def overview(self,repo):
        runs=self.store.runs(repo);models=self.store.models(repo)
        compatible=[m for m in models if m['metrics'].get('feature_version')==ml.FEATURE_VERSION]
        latest=next((m for m in compatible if m['status']=='experimental'),compatible[0] if compatible else None)
        return {'repository':repo,'run_count':len({r['run_id'] for r in runs}),'attempt_count':len(runs),
                'model':{'version':str(latest['version']),'status':latest['status'],'created_at':latest['created_at'],'metrics':latest['metrics']} if latest else None,
                'runs':[{'run_id':r['run_id'],'attempt':r['attempt'],**r['payload']} for r in reversed(runs)],
                'model_versions':[{'version':str(m['version']),'status':m['status'],'created_at':m['created_at'],'metrics':m['metrics']} for m in models],
                'predictions':self.store.predictions(repo),'reports':self.store.reports(repo),'evaluation':self.evaluation(repo),
                'rca_provider':{key:value for key,value in provider_configuration().items() if key!='missing'},
                'shadow_events':self.store.query('SELECT * FROM ai_shadow_events WHERE repository=%s ORDER BY observed_at DESC LIMIT 50',(repo,))}

    def enqueue(self,repo,kind,payload):
        task_id=self.store.enqueue(repo,kind,payload)
        self.executor.submit(self.execute,task_id)
        return task_id

    def execute(self,task_id):
        task=self.store.query("UPDATE ai_tasks SET status='running',updated_at=now() WHERE id=%s AND status='queued' RETURNING *",(task_id,),True)
        if not task:return
        stop=threading.Event()
        def heartbeat():
            while not stop.wait(15):
                try:self.store.query('UPDATE ai_tasks SET updated_at=now() WHERE id=%s',(task_id,))
                except Exception: logging.getLogger('backend.app').exception('AI task heartbeat failed')
        threading.Thread(target=heartbeat,daemon=True).start()
        try:
            kind=task['kind'].split(':')[0];data=task['payload'];repo=task['repository']
            if kind=='sync':result=synchronize(self.client,self.store,repo)
            elif kind=='train':result=self.train(repo)
            elif kind=='rca':result=self.rca(repo,data['run_id'],data['attempt'])
            elif kind=='predict':result=self.predict(repo,data['run_id'],data['attempt'])
            elif kind=='observe':
                prediction=self.predict(repo,data['run_id'],data['attempt']) if data.get('predict') else None
                result=synchronize(self.client,self.store,repo)
                if prediction:result['prediction']=prediction
            else:raise ValueError('Unknown task kind.')
            self.store.query("UPDATE ai_tasks SET status='completed',result=%s,updated_at=now() WHERE id=%s",(Jsonb(result),task_id))
        except Exception as error:
            logging.getLogger('backend.app').exception('AI task failed')
            safe=str(error) if isinstance(error,(ValueError,GitHubError)) else 'AI task failed. Check backend logs, provider configuration, and database connectivity.'
            self.store.query("UPDATE ai_tasks SET status='failed',result=%s,updated_at=now() WHERE id=%s",(Jsonb({'message':redact(safe)}),task_id))
        finally:stop.set()

    def worker(self):
        while True:
            self.store.query("UPDATE ai_tasks SET status='queued' WHERE status='running' AND updated_at<now()-interval '15 minutes'")
            tasks=self.store.query("SELECT id FROM ai_tasks WHERE status='queued' ORDER BY created_at LIMIT 1")
            if tasks:self.execute(str(tasks[0]['id']))
            else:time.sleep(2)
