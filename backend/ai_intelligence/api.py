"""Versioned local-admin API; dedicated signed workflow_run webhook."""
import hashlib
import hmac
import os
import uuid
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify
from .github import ActionsClient, GitHubError, repository_name, redact
from .store import Store
from .service import IntelligenceService


def register_ai(app,connect):
    service=IntelligenceService(Store(connect),ActionsClient())
    app.extensions['ai_intelligence']=service
    bp=Blueprint('ai_intelligence',__name__,url_prefix='/api/ai/v1')

    def authorize():
        token=os.getenv('AI_ADMIN_TOKEN','')
        origin=request.headers.get('Origin')
        local=request.remote_addr in ('127.0.0.1','::1') and request.host.split(':')[0] in ('localhost','127.0.0.1') and not request.headers.get('X-Forwarded-For')
        if origin and origin not in [f'http://{host}:{port}' for host in ['localhost','127.0.0.1'] for port in [5173,5174,5175,5000]]:
            return False
        if token:return hmac.compare_digest(request.headers.get('X-AI-Admin',''),token)
        return local

    @bp.before_request
    def protect():
        if os.getenv('PUBLIC_DEMO_MODE')=='1':
            public_reads={'overview','runs','predictions','reports','models','evaluation','outcomes'}
            if request.method=='OPTIONS':return None
            if request.method in ('GET','HEAD') and request.endpoint.split('.')[-1] in public_reads:return None
            return jsonify(status='FAILED',message='Public demo is read-only; AI mutations and webhooks are disabled.'),403
        if request.method=='OPTIONS' or request.endpoint=='ai_intelligence.workflow_hook':return None
        if not authorize():return jsonify(status='FAILED',message='AI administrator authorization required.'),403
        if request.method=='POST' and not request.is_json:return jsonify(status='FAILED',message='JSON request body required.'),415

    @bp.errorhandler(Exception)
    def error_response(error):
        if isinstance(error,ValueError):return jsonify(status='FAILED',message=redact(str(error))),400
        if isinstance(error,GitHubError):return jsonify(status='FAILED',message=str(error)),error.status
        app.logger.exception('AI API request failed')
        return jsonify(status='FAILED',message='AI service unavailable. Check backend configuration, migrations, and logs.'),503

    def repo_from(data):
        repo=repository_name(data.get('repository'))
        allowed={v.strip().lower() for v in os.getenv('AI_ALLOWED_REPOSITORIES','').split(',') if v.strip()}
        if allowed and repo not in allowed:raise ValueError('Repository is outside the configured AI allowlist.')
        if request.remote_addr not in ('127.0.0.1','::1') and not allowed:raise ValueError('Remote AI access requires a repository allowlist.')
        return repo

    def body():
        data=request.get_json(silent=True)
        if not isinstance(data,dict):raise ValueError('A JSON object is required.')
        return data

    def run_key(data):
        run_id=data.get('run_id');attempt=data.get('attempt',1)
        if type(run_id) is not int or run_id<1 or type(attempt) is not int or not 1<=attempt<=100:raise ValueError('Positive integer run_id and attempt (1–100) are required.')
        return run_id,attempt

    @bp.get('/overview')
    def overview():return jsonify(status='SUCCESS',data=service.overview(repo_from(request.args)))

    @bp.get('/runs')
    def runs():
        repo=repo_from(request.args)
        return jsonify(status='SUCCESS',data=[{'run_id':r['run_id'],'attempt':r['attempt'],**r['payload']} for r in reversed(service.store.runs(repo))])

    @bp.get('/predictions')
    def predictions():return jsonify(status='SUCCESS',data=service.store.predictions(repo_from(request.args)))

    @bp.get('/rca')
    def reports():return jsonify(status='SUCCESS',data=service.store.reports(repo_from(request.args)))

    @bp.get('/models')
    def models():return jsonify(status='SUCCESS',data=service.overview(repo_from(request.args))['model_versions'])

    @bp.get('/evaluation')
    def evaluation():return jsonify(status='SUCCESS',data=service.evaluation(repo_from(request.args)))

    @bp.get('/outcomes')
    def outcomes():return jsonify(status='SUCCESS',data=service.store.query('SELECT * FROM ai_outcomes WHERE repository=%s ORDER BY observed_at DESC',(repo_from(request.args),)))

    @bp.post('/sync')
    def sync():
        data=body();repo=repo_from(data)
        return jsonify(status='ACCEPTED',task_id=service.enqueue(repo,'sync',{})),202

    @bp.post('/train')
    def train():
        data=body();repo=repo_from(data)
        return jsonify(status='ACCEPTED',task_id=service.enqueue(repo,'train',{})),202

    @bp.post('/predictions')
    def predict():
        data=body();repo=repo_from(data);run_id,attempt=run_key(data)
        return jsonify(status='ACCEPTED',task_id=service.enqueue(repo,f'predict:{run_id}:{attempt}',{'run_id':run_id,'attempt':attempt})),202

    @bp.post('/rca')
    def rca():
        data=body();repo=repo_from(data);run_id,attempt=run_key(data)
        return jsonify(status='ACCEPTED',task_id=service.enqueue(repo,f'rca:{run_id}:{attempt}',{'run_id':run_id,'attempt':attempt})),202

    @bp.get('/tasks/<task_id>')
    def task(task_id):
        repo=repo_from(request.args);uuid.UUID(task_id)
        task=service.store.query('SELECT * FROM ai_tasks WHERE id=%s AND repository=%s',(task_id,repo),True)
        if not task:return jsonify(status='FAILED',message='Task not found.'),404
        return jsonify(status='SUCCESS',data=task)

    @bp.post('/rca/<report_id>/verify')
    def verify(report_id):
        data=body();repo=repo_from(data);uuid.UUID(report_id)
        fields=['category_correct','step_correct','evidence_correct','fix_correct','unsupported_claims']
        if any(type(data.get(field)) is not bool for field in fields):raise ValueError('All five independent review criteria must be boolean values.')
        reviewer=data.get('reviewer')
        if not isinstance(reviewer,str) or not 1<=len(reviewer.strip())<=80:raise ValueError('A distinct reviewer identifier (1–80 characters) is required.')
        review={field:data[field] for field in fields};review['reviewer']=redact(reviewer.strip())
        review['identity_status']='self_reported_local_admin';review['comment']=redact(str(data.get('comment','')))[:1000]
        from psycopg.types.json import Jsonb
        with service.store.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id FROM ai_rca_reports WHERE id=%s AND repository=%s FOR UPDATE',(report_id,repo))
                if not cursor.fetchone():return jsonify(status='FAILED',message='RCA report not found.'),404
                cursor.execute("""INSERT INTO ai_rca_reviews(report_id,reviewer,review) VALUES(%s,%s,%s)
                    ON CONFLICT(report_id,reviewer) DO UPDATE SET review=excluded.review,reviewed_at=now()""",(report_id,review['reviewer'],Jsonb(review)))
                cursor.execute('SELECT review FROM ai_rca_reviews WHERE report_id=%s',(report_id,))
                verdicts=[all(item[0][f] for f in fields[:4]) and not item[0]['unsupported_claims'] for item in cursor.fetchall()]
                status='verified' if all(verdicts) else 'rejected' if not any(verdicts) else 'disputed'
                cursor.execute('UPDATE ai_rca_reports SET verification_status=%s,review=%s WHERE id=%s',(status,Jsonb(review),report_id))
        return jsonify(status='SUCCESS',verification_status=status)

    @bp.post('/webhook')
    def workflow_hook():
        secret=os.getenv('GITHUB_WEBHOOK_SECRET','')
        if not secret:return jsonify(status='FAILED',message='Signed workflow webhook is not configured.'),503
        raw=request.get_data()
        if len(raw)>1_000_000:return jsonify(status='FAILED',message='Webhook body too large.'),413
        signature='sha256='+hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,request.headers.get('X-Hub-Signature-256','')):return jsonify(status='FAILED',message='Invalid webhook signature.'),401
        if request.headers.get('X-GitHub-Event')!='workflow_run':return jsonify(status='IGNORED'),200
        data=body();repo=repository_name(data.get('repository',{}).get('full_name'))
        allowed={v.strip().lower() for v in os.getenv('AI_ALLOWED_REPOSITORIES','').split(',') if v.strip()}
        if repo not in allowed:return jsonify(status='FAILED',message='Webhook repository not allowlisted.'),403
        run=data.get('workflow_run',{});run_id,attempt=run_key({'run_id':run.get('id'),'attempt':run.get('run_attempt',1)})
        action=data.get('action')
        if action not in ('requested','queued','completed'):return jsonify(status='IGNORED'),200
        payload={'run_id':run_id,'attempt':attempt,'predict':action in ('requested','queued')}
        return jsonify(status='ACCEPTED',task_id=service.enqueue(repo,f'observe:{run_id}:{attempt}:{action}',payload)),202

    app.register_blueprint(bp)
