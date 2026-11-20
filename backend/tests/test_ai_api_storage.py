import hashlib
import hmac
import json
import uuid
import os
import pytest
from backend.app import app,get_db_connection
from backend.ai_intelligence.store import Store
from backend.ai_intelligence.migrations import migrate


def test_ai_api_input_validation_and_cors():
    client=app.test_client()
    for payload in [[],{}, {'repository':'https://evil.invalid'}, {'repository':'test/repo','run_id':True}]:
        response=client.post('/api/ai/v1/rca',json=payload,headers={'Origin':'http://localhost:5173'})
        assert response.status_code==400
        assert response.headers['Access-Control-Allow-Origin']=='http://localhost:5173'
        assert 'Traceback' not in response.get_data(as_text=True)


def test_ai_auth_rejects_remote_and_untrusted_origins(monkeypatch):
    monkeypatch.delenv('AI_ADMIN_TOKEN',raising=False)
    client=app.test_client()
    assert client.get('/api/ai/v1/overview?repository=test/repo',environ_base={'REMOTE_ADDR':'203.0.113.10'}).status_code==403
    assert client.get('/api/ai/v1/overview?repository=test/repo',headers={'Origin':'https://evil.invalid'}).status_code==403
    monkeypatch.setenv('AI_ADMIN_TOKEN','admin-secret')
    assert client.get('/api/ai/v1/overview?repository=test/repo').status_code==403


def test_task_submission_is_async_and_validated(monkeypatch):
    service=app.extensions['ai_intelligence'];calls=[]
    monkeypatch.setattr(service,'enqueue',lambda *args:calls.append(args) or 'task-id')
    response=app.test_client().post('/api/ai/v1/rca',json={'repository':'test/repo','run_id':21,'attempt':1})
    assert response.status_code==202 and calls[0][1]=='rca:21:1'


def test_signed_webhook_and_allowlist(monkeypatch):
    monkeypatch.setenv('GITHUB_WEBHOOK_SECRET','webhook-test-secret')
    monkeypatch.setenv('AI_ALLOWED_REPOSITORIES','test/repo')
    service=app.extensions['ai_intelligence'];calls=[]
    monkeypatch.setattr(service,'enqueue',lambda *args:calls.append(args) or 'id')
    payload=json.dumps({'action':'requested','repository':{'full_name':'test/repo'},'workflow_run':{'id':12,'run_attempt':1}}).encode()
    client=app.test_client()
    assert client.post('/api/ai/v1/webhook',data=payload,content_type='application/json').status_code==401
    signature='sha256='+hmac.new(b'webhook-test-secret',payload,hashlib.sha256).hexdigest()
    response=client.post('/api/ai/v1/webhook',data=payload,content_type='application/json',headers={'X-Hub-Signature-256':signature,'X-GitHub-Event':'workflow_run'})
    assert response.status_code==202 and calls[0][2]['predict'] is True


@pytest.mark.skipif(os.getenv('AI_TEST_DATABASE')!='1',reason='Explicit PostgreSQL integration opt-in required')
def test_postgresql_idempotency_attempts_predictions_and_outcomes():
    from datetime import datetime,timezone,timedelta
    migrate(get_db_connection);migrate(get_db_connection)
    store=Store(get_db_connection);repo='ai-test/'+uuid.uuid4().hex;version=str(uuid.uuid4());now=datetime.now(timezone.utc).isoformat()
    run={'id':1,'run_attempt':1,'workflow_id':1,'head_sha':'a'*40,'created_at':(datetime.now(timezone.utc)-timedelta(seconds=20)).isoformat(),'run_started_at':now,'status':'queued','conclusion':None,'path':'.github/workflows/ci.yml'}
    try:
        store.save_run(repo,run,[]);store.save_run(repo,run,[])
        assert len(store.runs(repo))==1
        store.model(repo,version,{'status':'experimental','threshold':.5})
        assert store.predict(repo,run,version,{'changed_files':1},.7,.5,(datetime.now(timezone.utc)-timedelta(seconds=5)).isoformat())
        assert store.predict(repo,run,version,{},.8,.5,now) is None
        done={**run,'status':'completed','conclusion':'failure'}
        job={'id':1,'name':'test','status':'completed','conclusion':'failure','started_at':now,'completed_at':now,'steps':[{'number':1,'name':'test','conclusion':'failure'}],'log_status':'available','log_text':'redacted test fixture'}
        store.save_run(repo,done,[job]);pred=store.predictions(repo)[0]
        assert pred['actual_label']==1 and pred['correct'] and pred['verification_status']=='matched'
        store.save_run(repo,{**done,'run_attempt':2,'conclusion':'success'},[job])
        assert len(store.runs(repo))==2
        assert len(store.jobs(repo,1,1))==1
        assert store.predictions(repo)[0]['actual_label']==1
        late={**run,'run_attempt':3}
        store.save_run(repo,late,[])
        store.predict(repo,late,version,{},.7,.5,datetime.now(timezone.utc))
        store.save_run(repo,{**late,'status':'completed','conclusion':'success'},[job])
        assert next(p for p in store.predictions(repo) if p['attempt']==3)['verification_status']=='invalid_timing'
        cancelled={**run,'run_attempt':4}
        store.save_run(repo,cancelled,[])
        store.predict(repo,cancelled,version,{},.7,.5,now)
        store.save_run(repo,{**cancelled,'status':'completed','conclusion':'cancelled'},[job])
        assert next(p for p in store.predictions(repo) if p['attempt']==4)['verification_status']=='excluded_outcome'

    finally:
        store.query('DELETE FROM ai_runs WHERE repository=%s',(repo,))
        store.query('DELETE FROM ai_models WHERE repository=%s',(repo,))

def test_admin_preflight_does_not_require_secret_header(monkeypatch):
    monkeypatch.setenv('AI_ADMIN_TOKEN','server-admin-test')
    response=app.test_client().options('/api/ai/v1/train',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-ai-admin'})
    assert response.status_code==200
    assert response.headers['Access-Control-Allow-Origin']=='http://localhost:5173'

@pytest.mark.skipif(os.getenv('AI_TEST_DATABASE')!='1',reason='Explicit PostgreSQL integration opt-in required')
def test_distinct_manual_reviews_and_dispute_status(monkeypatch):
    from datetime import datetime,timezone
    repo='ai-test/'+uuid.uuid4().hex
    monkeypatch.setenv('AI_ALLOWED_REPOSITORIES',repo)
    monkeypatch.delenv('AI_ADMIN_TOKEN',raising=False)
    store=Store(get_db_connection);now=datetime.now(timezone.utc).isoformat()
    run={'id':1,'run_attempt':1,'workflow_id':1,'head_sha':'test-sha','created_at':now,'status':'completed','conclusion':'failure'}
    try:
        store.save_run(repo,run,[])
        report_id=store.save_report(repo,1,1,{'model_version':'synthetic-test','engine':'evidence_rules'})
        client=app.test_client()
        review={'repository':repo,'category_correct':True,'step_correct':True,'evidence_correct':True,'fix_correct':True,'unsupported_claims':False}
        assert client.post(f'/api/ai/v1/rca/{report_id}/verify',json=review).status_code==400
        first=client.post(f'/api/ai/v1/rca/{report_id}/verify',json={**review,'reviewer':'reviewer-a'})
        assert first.status_code==200 and first.json['verification_status']=='verified'
        client.post(f'/api/ai/v1/rca/{report_id}/verify',json={**review,'reviewer':'reviewer-a'})
        assert len(store.query('SELECT * FROM ai_rca_reviews WHERE report_id=%s',(report_id,)))==1
        second=client.post(f'/api/ai/v1/rca/{report_id}/verify',json={**review,'reviewer':'reviewer-b','fix_correct':False})
        assert second.json['verification_status']=='disputed'
        measured=app.extensions['ai_intelligence'].evaluation(repo)['rca']['human_reviewer_agreement']
        assert measured['agreement']==.8 and measured['reviewer_pairs']==1
    finally:
        store.query('DELETE FROM ai_runs WHERE repository=%s',(repo,))
