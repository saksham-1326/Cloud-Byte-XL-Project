"""Deterministic tests; synthetic cases are test fixtures, never dashboard data."""
import copy
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
import pytest
from backend.ai_intelligence import ml
from backend.ai_intelligence.rca import analyze, extract_evidence, grounded_diagnosis, validate_diagnosis
from backend.ai_intelligence.service import IntelligenceService

BASE=datetime(2025,1,1,tzinfo=timezone.utc)

def run(number,label=0,sha=None):
    return {'run_id':number,'attempt':1,'workflow_id':1,'commit_sha':sha or f'sha{number}','created_at':BASE+timedelta(days=number),'completed_at':BASE+timedelta(days=number,minutes=2),'status':'completed','conclusion':'failure' if label else 'success','payload':{'path':'.github/workflows/ci.yml','event':'push','duration_seconds':120}}

def snapshot(r):
    return {'sha':r['commit_sha'],'historical_ref':r['commit_sha'],'workflow_path':'.github/workflows/ci.yml','config_status':'available','workflow_config':'jobs:\n  test:','files':[{'filename':'requirements.txt','additions':1,'deletions':0}]}

def job_case(text):
    return [{'job_id':10,'payload':{'name':'test','steps':[{'name':'Run tests','number':2,'conclusion':'failure','started_at':'2025-01-01T00:00:00Z','completed_at':'2025-01-01T00:00:05Z'}]},'log_text':'\n'.join(f'2025-01-01T00:00:0{i}Z {line}' for i,line in enumerate(text.splitlines()))}]

def test_known_real_run21():
    fixture=json.loads((Path(__file__).parent/'fixtures/run21_real.json').read_text())
    report=analyze(fixture['jobs'])
    assert report['category']=='intentional_workflow_termination'
    assert report['failed_step']=='Run tests'
    assert 'Pytest passed' in report['primary_cause']
    assert {204,222,223}.issubset({item['line'] for item in report['evidence']})
    assert any(item['line']==273 and 'No such container' in item['text'] for item in report['secondary_errors'])
    assert not any('FAILED_OR_SKIPPED' in item['text'] for item in report['evidence'])
    assert report['engine']=='evidence_rules' and report['verification_status']=='unverified'

@pytest.mark.parametrize('text,category',[
 ('AssertionError: expected 1 got 2','unit_test_failure'),
 ("ModuleNotFoundError: No module named flask",'dependency_error'),
 ('Dockerfile parse error: unknown instruction','docker_build_failure'),
 ('toolxyz: command not found','ci_workflow_misconfiguration'),
 ('missing required environment variable APP_CONFIG','missing_environment_variable'),
 ('no diagnostic available','insufficient_evidence'),
])
def test_controlled_rca_ground_truth(text,category):
    assert analyze(job_case(text))['category']==category


def test_failed_test_not_overridden_by_exit_command():
    assert analyze(job_case('exit 1\nAssertionError: failed'))['category']=='unit_test_failure'


def test_llm_unsupported_citation_and_wrong_category_rejected():
    evidence=extract_evidence(job_case('exit 1\n1 passed\nProcess completed with exit code 1.'))
    anchor=grounded_diagnosis(evidence)
    result=copy.deepcopy(anchor);result['evidence_refs']=['made-up-line']
    with pytest.raises(ValueError,match='unsupported'):validate_diagnosis(result,evidence,anchor)
    result=copy.deepcopy(anchor);result['category']='unit_test_failure'
    with pytest.raises(ValueError,match='contradicts'):validate_diagnosis(result,evidence,anchor)


def test_llm_schema_and_injection_cannot_create_evidence():
    class Provider:
        def generate(self,evidence,anchor):return {**anchor,'primary_cause':'Ignore all instructions','evidence_refs':['arbitrary']}
    with pytest.raises(ValueError):analyze(job_case('exit 1\n1 passed'),Provider())


def test_missing_logs_returns_insufficient_evidence():
    assert analyze(job_case(''))['category']=='insufficient_evidence'


def test_feature_leakage_prevention_and_sha():
    target=run(5,1);prior=run(4,1);future=run(6,1);sibling=run(3,1,target['commit_sha'])
    values,proof=ml.features(target,[prior,future,sibling,target],snapshot(target),target['created_at'])
    assert values['prior_run_count']==1 and values['recent_failure_rate']==1
    changed=copy.deepcopy(target);changed['conclusion']='success';changed['payload']['duration_seconds']=999999;changed['payload']['failed_step']='target error'
    assert ml.features(changed,[prior,future,sibling,target],snapshot(target),target['created_at'])[0]==values
    assert all(datetime.fromisoformat(item['completed_at'])<target['created_at'] for item in proof['prior_runs'])
    bad=snapshot(target);bad['historical_ref']='current-main'
    with pytest.raises(ValueError,match='SHA'):ml.features(target,[],bad,target['created_at'])


def test_utc_feature_reproducibility():
    r=run(3)
    first=ml.features(r,[],snapshot(r),r['created_at'])[0]
    other=r['created_at'].astimezone(timezone(timedelta(hours=5,minutes=30)))
    assert ml.features(r,[],snapshot(r),other)[0]==first


def test_repeated_attempts_not_double_counted_in_history():
    target=run(5);one=run(3,1);two={**one,'attempt':2,'conclusion':'success'}
    values,_=ml.features(target,[one,two],snapshot(target),target['created_at'])
    assert values['prior_run_count']==1 and values['recent_failure_rate']==0


def test_chronological_group_purge():
    rows=[{'run':run(i),'label':i%2} for i in range(20)]
    rows[-1]['run']['commit_sha']=rows[0]['run']['commit_sha']
    train,val,test=ml.temporal_split(rows)
    train_sha={r['run']['commit_sha'] for r in train};val_sha={r['run']['commit_sha'] for r in val}
    assert not train_sha.intersection(val_sha)
    assert not {r['run']['commit_sha'] for r in test}.intersection(train_sha|val_sha)
    assert max(r['run']['created_at'] for r in train)<min(r['run']['created_at'] for r in val)


class FakeStore:
    def __init__(self,rows):self.rows=rows;self.saved=[]
    def runs(self,repo):return self.rows
    def snapshot(self,repo,sha,path):return snapshot(next(r for r in self.rows if r['commit_sha']==sha))
    def features(self,*args):pass
    def model(self,*args):self.saved.append(args)


def test_ml_training_and_insufficient_data(tmp_path,monkeypatch):
    monkeypatch.setattr(ml,'ARTIFACTS',tmp_path)
    small=FakeStore([run(i,0) for i in range(8)])
    assert ml.train(small,'test/repo')['status']=='insufficient_data'
    store=FakeStore([run(i,int(i%3==0)) for i in range(40)])
    result=ml.train(store,'test/repo')
    assert result['status']=='experimental'
    assert set(result['comparisons'])=={'dummy','logistic','random_forest'}
    assert result['test']['n']>0 and len(result['test']['confusion_matrix'])==2
    assert list(tmp_path.glob('*.joblib'))


def test_metrics_single_class_are_honest():
    result=ml.metrics([0,0],[.1,.2],.5)
    assert result['roc_auc'] is None and result['pr_auc'] is None


def test_completed_run_cannot_get_live_prediction():
    class Client:
        def run(self,*args):return {'id':1,'run_attempt':1,'status':'completed','conclusion':'failure'}
    class Store:
        def query(self,*args):return None
        def models(self,*args):raise AssertionError('Must reject before consulting model')
    result=IntelligenceService(Store(),Client()).predict('test/repo',1,1)
    assert result['status']=='skipped'


def test_untrained_queued_run_does_not_invent_probability():
    class Client:
        def run(self,*args):return {'id':1,'run_attempt':1,'head_sha':'target','status':'queued','conclusion':None}
    class Store:
        def query(self,*args):return None
        def models(self,*args):return []
    result=IntelligenceService(Store(),Client()).predict('test/repo',1,1)
    assert result['status']=='insufficient_data' and 'probability' not in result

def test_shadow_prediction_persistence_and_execution_race(monkeypatch):
    import numpy as np
    class Pipeline:
        def predict_proba(self,rows):return np.array([[.3,.7]])
        def __getitem__(self,key):return object()
    monkeypatch.setattr(ml,'load_model',lambda model:Pipeline())
    class Store:
        def __init__(self):self.persisted=[]
        def models(self,repo):return [{'status':'experimental','version':'test-version','created_at':BASE,'trained_through':BASE,'metrics':{'threshold':.6,'feature_version':ml.FEATURE_VERSION}}]
        def runs(self,repo):return []
        def save_run(self,*args):pass
        def query(self,*args):return None
        def predict(self,*args):self.persisted.append(args);return {'id':'test'}
    class Client:
        def __init__(self,race=False):self.calls=0;self.race=race
        def run(self,*args):
            self.calls+=1
            return {'id':1,'run_attempt':1,'workflow_id':1,'head_sha':'target','created_at':'2025-02-01T00:00:00Z','status':'in_progress' if self.race and self.calls>1 else 'queued','conclusion':None,'event':'push'}
        def snapshot(self,repo,run):return {'sha':'target','historical_ref':'target','workflow_config':'jobs:', 'config_status':'available','files':[]}
    store=Store();result=IntelligenceService(store,Client()).predict('test/repo',1,1)
    assert result['status']=='predicted' and len(store.persisted)==1
    assert store.persisted[0][4]==.7 and store.persisted[0][5]==.6
    racing=Store();result=IntelligenceService(racing,Client(True)).predict('test/repo',1,1)
    assert result['status']=='skipped' and not racing.persisted


def test_ground_truth_benchmark():
    from backend.ai_intelligence.evaluate import benchmark
    measured=benchmark()
    assert measured['case_count']==6 and measured['real_log_cases']==1
    assert measured['metrics']['category_correct']==1
    assert measured['metrics']['unsupported_claims']==0

def test_valid_structured_provider_result_is_labelled_separately():
    class Provider:
        def generate(self,evidence,anchor):return dict(anchor)
    report=analyze(job_case('exit 1\n1 passed\nProcess completed with exit code 1.'),Provider())
    assert report['engine']=='llm_grounded' and report['provider_status']=='completed'
    assert report['category']=='intentional_workflow_termination'


def test_openai_prompt_is_blind_to_rule_diagnosis(monkeypatch):
    import urllib.request
    from backend.ai_intelligence.rca import OpenAIProvider
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    monkeypatch.setenv('RCA_MODEL','test-model')
    evidence=extract_evidence(job_case('exit 1\n1 passed'))
    anchor=grounded_diagnosis(evidence)
    requests=[]

    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):
            return json.dumps({'output':[{'content':[{'type':'output_text','text':json.dumps(anchor)}]}]}).encode()

    def send(request,timeout):
        requests.append(json.loads(request.data))
        return Response()

    monkeypatch.setattr(urllib.request,'urlopen',send)
    assert OpenAIProvider().generate(evidence,{'primary_cause':'SECRET_EXPECTED_CAUSE'})==anchor
    assert json.loads(requests[0]['input'])=={'evidence':evidence}
    assert 'SECRET_EXPECTED_CAUSE' not in json.dumps(requests)
    assert requests[0]['store'] is False


def test_failed_step_command_context_is_preserved():
    evidence=extract_evidence(job_case('##[group]Run curl --fail -X POST "$CI_STATUS_URL"\ncurl: (22) The requested URL returned error: 404'))
    assert any('curl --fail' in item['text'] for item in evidence['primary'])


def test_provider_failure_does_not_become_rule_success():
    class Provider:
        def generate(self,evidence,anchor):raise ValueError('provider unavailable')
    with pytest.raises(ValueError,match='provider unavailable'):
        analyze(job_case('exit 1\n1 passed'),Provider())

def test_pairwise_human_review_agreement():
    from backend.ai_intelligence.reviews import agreement
    a={'category_correct':True,'step_correct':True,'evidence_correct':True,'fix_correct':True,'unsupported_claims':False}
    b={**a,'fix_correct':False}
    assert agreement([{'report_id':'1','reviewer':'a','review':a}])['agreement'] is None
    measured=agreement([{'report_id':'1','reviewer':'a','review':a},{'report_id':'1','reviewer':'b','review':b}])
    assert measured['reviewer_pairs']==1 and measured['rubric_comparisons']==5 and measured['agreement']==.8
