import importlib
import hashlib
import json
import urllib.error
import uuid

import pytest

from backend.tools import ci_callback


@pytest.fixture(autouse=True)
def sender_environment(monkeypatch):
    for key,value in {
        'CI_CALLBACK_ENABLED':'1', 'CI_STATUS_URL':'https://example.com/api/ci/v1/status',
        'CI_STATUS_TOKEN':'test-secret', 'GITHUB_REPOSITORY':'test/repo',
        'GITHUB_RUN_ID':'21', 'GITHUB_RUN_ATTEMPT':'1', 'GITHUB_SHA':'a'*40,
        'GITHUB_WORKFLOW':'CI', 'PIPELINE_STATUS':'success',
        'SYNTAX_OUTCOME':'success', 'TEST_OUTCOME':'success', 'DOCKER_OUTCOME':'success',
    }.items(): monkeypatch.setenv(key,value)
    monkeypatch.delenv('CI_CALLBACK_TEST_LOOPBACK',raising=False)


def test_callback_disabled_by_default(monkeypatch):
    monkeypatch.delenv('CI_CALLBACK_ENABLED')
    assert ci_callback.main()==0


@pytest.mark.parametrize('url,token', [
    ('http://example.com/api/ci/v1/status','test'),
    ('https://example.com/wrong','test'),
    ('https://example.com/api/ci/v1/status',''),
    ('https://user:password@example.com/api/ci/v1/status','test'),
    ('https://example.com/api/ci/v1/status?secret=example','test'),
    ('https://[invalid','test'), ('','test'),
])
def test_unsafe_callback_configuration(monkeypatch,url,token):
    monkeypatch.setenv('CI_STATUS_URL',url);monkeypatch.setenv('CI_STATUS_TOKEN',token)
    assert ci_callback.main()==1


@pytest.mark.parametrize('status',['success','failure','cancelled'])
def test_callback_payload_and_auth(monkeypatch,status):
    monkeypatch.setenv('PIPELINE_STATUS',status)
    monkeypatch.setenv('TEST_OUTCOME','success' if status=='success' else 'failure')
    class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,limit):return json.dumps(self.body).encode()
    def send(self,request,timeout):
        assert timeout==15
        assert request.get_header('Authorization')=='Bearer test-secret'
        payload=json.loads(request.data)
        assert payload['status']=={'success':'SUCCESS','failure':'FAILURE','cancelled':'CANCELLED'}[status]
        assert payload['repository']=='test/repo' and payload['run_id']==21 and payload['attempt']==1
        response=Response();response.body={**payload,'status':'SUCCESS','persisted':True,
            'receipt_id':str(uuid.uuid4()),'deployment_id':1,'duplicate':False,
            'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
        return response
    monkeypatch.setattr(ci_callback.urllib.request.OpenerDirector,'open',send)
    assert ci_callback.main()==0
    assert ci_callback.payload_from_environment()['delivery_id']==ci_callback.payload_from_environment()['delivery_id']


@pytest.mark.parametrize('change',[
    {'persisted':False},{'persisted':1},{'receipt_id':'invalid'},
    {'run_id':22},{'attempt':True},{'commit_sha':'b'*40},
    {'delivery_id':str(uuid.uuid4())},{'repository':'other/repo'},
    {'deployment_id':True},{'status':'FAILED'}, {'duplicate':'false'},
    {'payload_sha256':'0'*64},
])
def test_sender_rejects_false_or_mismatched_acknowledgment(change):
    payload=ci_callback.payload_from_environment()
    body={**payload,'status':'SUCCESS','persisted':True,'receipt_id':str(uuid.uuid4()),
          'deployment_id':1,'duplicate':False,
          'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(),**change}
    assert not ci_callback.valid_acknowledgment(body,payload)


@pytest.mark.parametrize('raw',[b'{}',b'not-json',b'[]',b'x'*16385])
def test_sender_rejects_unpersisted_response(monkeypatch,raw):
    class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,limit):return raw
    monkeypatch.setattr(ci_callback.urllib.request.OpenerDirector,'open',lambda *a,**k:Response())
    assert ci_callback.main()==1


@pytest.mark.parametrize('error',[
    urllib.error.HTTPError('https://example.com',401,'private-body',{},None),
    urllib.error.URLError('private-connection-details'),
])
def test_callback_errors_hide_body_and_token(monkeypatch,capsys,error):
    def fail(*args,**kwargs):raise error
    monkeypatch.setattr(ci_callback.urllib.request.OpenerDirector,'open',fail)
    assert ci_callback.main()==1
    output=capsys.readouterr().out
    assert all(secret not in output for secret in ['test-secret','private-body','private-connection-details'])


def test_loopback_override_cannot_enable_public_http(monkeypatch):
    monkeypatch.setenv('CI_CALLBACK_TEST_LOOPBACK','1')
    monkeypatch.setenv('CI_STATUS_URL','http://example.com/api/ci/v1/status')
    assert ci_callback.main()==1


def test_flask_callback_auth_and_delivery(monkeypatch):
    module = importlib.import_module('backend.app')
    monkeypatch.setenv('CI_STATUS_TOKEN', 'test-secret')
    monkeypatch.setattr(module, 'latest_ci', dict(module.latest_ci))
    class Connection:
        def cursor(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, *args): pass
        def fetchone(self): return None
        def commit(self): pass
        def close(self): pass
    monkeypatch.setattr(module, 'get_db_connection', Connection)
    client = module.app.test_client()
    payload = dict(status='SUCCESS', build='PASSED', tests='PASSED', docker='PASSED')
    assert client.post('/api/ci/status', json=payload).status_code == 401
    assert client.post('/api/ci/status', json=payload,
        headers={'Authorization': 'Bearer wrong'}).status_code == 401
    response = client.post('/api/ci/status', json=payload,
        headers={'Authorization': 'Bearer test-secret'})
    assert response.status_code == 200
    assert response.json['ci']['status'] == 'SUCCESS'
    assert client.get('/api/ci/status').json['status'] == 'SUCCESS'
    monkeypatch.delenv('CI_STATUS_TOKEN')
    assert client.post('/api/ci/status', json=payload).status_code == 200
