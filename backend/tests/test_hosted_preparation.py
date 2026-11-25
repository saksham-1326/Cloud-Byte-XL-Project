import importlib,logging
import pytest
from flask import Flask
from backend.database import configuration
from backend.hosting import validate_environment,register_public_demo,SafeLogFilter

def env():return dict(PUBLIC_DEMO_MODE='1',CORS_ORIGINS='https://demo.vercel.app',AI_ALLOWED_REPOSITORIES='o/r',DATABASE_URL='postgresql://reader:example-password@db.example.invalid/app?sslmode=require')

def test_hosted_config_uses_URL_and_requires_TLS():
    assert configuration(env())['dbname']=='app'
    assert validate_environment(env())=={'o/r'}
    for update in [{'CORS_ORIGINS':'*'},{'CORS_ORIGINS':'http://localhost:5173'},{'RCA_PROVIDER':'gemini'},{'CI_CALLBACK_ENABLED':'1'},{'FLASK_DEBUG':'1'},{'PUBLIC_DEMO_MODE':'0'},{'AI_ALLOWED_REPOSITORIES':''},{'DB_SSLMODE':'disable'}]:
        with pytest.raises(ValueError):validate_environment({**env(),**update})

def test_invalid_connection_does_not_expose_secret():
    with pytest.raises(ValueError,match='Invalid DATABASE_URL'):configuration({'DATABASE_URL':'postgresql://secret:password@host:bad/db'})

def test_public_gate_blocks_all_unapproved_routes_before_service_work():
    a=Flask(__name__);register_public_demo(a,lambda: (_ for _ in ()).throw(AssertionError('no SQL')),{'o/r'})
    client=a.test_client()
    for path in ['/webhook','/api/ci/status','/api/ai/v1/train','/api/ai/v1/predictions','/api/ai/v1/rca','/api/ai/v1/webhook','/api/ai/v1/rca/x/verify']:
        assert client.post(path,json={}).status_code==403
    assert client.get('/api/database/test').status_code==403
    assert client.get('/healthz').status_code==200
    assert client.get('/readyz').status_code==503
    assert client.post('/api/github/repository',json={'url':'https://github.com/other/private'}).status_code==403
    assert client.post('/api/github/repository',json={'url':'https://github.com/o/r?token=anything'}).status_code==400

def test_public_AI_reads_without_admin_but_mutations_are_denied(monkeypatch):
    from backend.ai_intelligence.api import register_ai
    monkeypatch.setenv('PUBLIC_DEMO_MODE','1');monkeypatch.setenv('AI_ALLOWED_REPOSITORIES','o/r')
    a=Flask(__name__);register_ai(a,lambda:None)
    monkeypatch.setattr(a.extensions['ai_intelligence'].store,'runs',lambda repo:[])
    client=a.test_client()
    assert client.get('/api/ai/v1/runs?repository=o/r',base_url='https://api.example.invalid').status_code==200
    assert client.post('/api/ai/v1/train',json={'repository':'o/r'}).status_code==403
    assert client.get('/api/ai/v1/tasks/anything?repository=o/r').status_code==403
    a.extensions['ai_intelligence'].executor.shutdown(wait=True)

def test_public_repository_analysis_never_attempts_persistence(monkeypatch):
    from backend.app import app
    module=importlib.import_module('backend.app');monkeypatch.setenv('PUBLIC_DEMO_MODE','1')
    responses={'/repos/o/r':dict(id=1,name='r',full_name='o/r',html_url='https://github.com/o/r',default_branch='main',owner={'login':'o'}),'/repos/o/r/commits/main':{'sha':'a'*40},'/repos/o/r/languages':{},'/repos/o/r/git/trees/'+'a'*40+'?recursive=1':{'tree':[],'truncated':False},'/repos/o/r/commits?per_page=10':[],'/repos/o/r/contributors?per_page=10':[]}
    monkeypatch.setattr(module,'github_request',lambda path:responses[path])
    monkeypatch.setattr(module,'save_github_repository',lambda repo:(_ for _ in ()).throw(AssertionError('write attempted')))
    response=app.test_client().post('/api/github/repository',json={'url':'https://github.com/o/r'})
    assert response.status_code==200 and 'read-only' in response.json['databaseWarning']
    assert 'databaseId' not in response.json['repository']

def test_log_filter_removes_configured_secret(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','postgresql://user:private-password@host/db')
    record=logging.LogRecord('test',logging.ERROR,'',1,'failed %s',( 'postgresql://user:private-password@host/db',),None)
    SafeLogFilter().filter(record);assert 'private-password' not in record.getMessage()

def test_real_wsgi_entrypoint_CORS_and_route_gate_without_external_calls():
    import os,subprocess,sys
    child={**os.environ,**env(),'DB_SSLMODE':'require','PYTHON_DOTENV_DISABLED':'1',
           'RCA_PROVIDER':'none','CI_CALLBACK_ENABLED':'0','FLASK_DEBUG':'0'}
    code="""
from backend.wsgi import app
c=app.test_client()
r=c.get('/healthz',headers={'Origin':'https://demo.vercel.app'})
assert r.status_code==200 and r.headers['Access-Control-Allow-Origin']=='https://demo.vercel.app'
assert 'Access-Control-Allow-Origin' not in c.get('/healthz',headers={'Origin':'https://unapproved.example.invalid'}).headers
assert c.post('/api/ai/v1/train',json={}).status_code==403
assert c.post('/api/github/repository',json={'url':'https://github.com/other/repo'}).status_code==403
assert c.get('/api/database/test').status_code==403
assert not app.debug
"""
    subprocess.run([sys.executable,'-c',code],env=child,check=True,capture_output=True,timeout=30)
