import importlib
import json
import urllib.error

import pytest

from backend.tools import ci_callback


def test_missing_callback_skips(monkeypatch):
    monkeypatch.delenv('CI_STATUS_URL', raising=False)
    assert ci_callback.main() == 0


@pytest.mark.parametrize('url,token', [
    ('http://example.com/api/ci/status', 'test'),
    ('https://example.com/wrong', 'test'),
    ('https://example.com/api/ci/status', ''),
    ('https://user:password@example.com/api/ci/status', 'test'),
])
def test_unsafe_callback_configuration(monkeypatch, url, token):
    monkeypatch.setenv('CI_STATUS_URL', url)
    monkeypatch.setenv('CI_STATUS_TOKEN', token)
    assert ci_callback.main() == 1


@pytest.mark.parametrize('status', ['success', 'failure', 'cancelled'])
def test_callback_payload_and_auth(monkeypatch, status):
    monkeypatch.setenv('CI_STATUS_URL', 'https://example.com/api/ci/status')
    monkeypatch.setenv('CI_STATUS_TOKEN', 'test-secret')
    monkeypatch.setenv('PIPELINE_STATUS', status)
    monkeypatch.setenv('SYNTAX_OUTCOME', 'success')
    monkeypatch.setenv('TEST_OUTCOME', 'failure')
    monkeypatch.setenv('DOCKER_OUTCOME', 'skipped')
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
    def send(self, request, timeout):
        assert timeout == 15
        assert request.get_header('Authorization') == 'Bearer test-secret'
        body = json.loads(request.data)
        assert body['status'] == ('SUCCESS' if status == 'success' else 'FAILURE')
        assert body['build'] == 'PASSED'
        assert body['tests'] == body['docker'] == 'FAILED_OR_SKIPPED'
        return Response()
    monkeypatch.setattr(ci_callback.urllib.request.OpenerDirector, 'open', send)
    assert ci_callback.main() == 0


def test_callback_http_failure_hides_body_and_token(monkeypatch, capsys):
    monkeypatch.setenv('CI_STATUS_URL', 'https://example.com/api/ci/status')
    monkeypatch.setenv('CI_STATUS_TOKEN', 'test-secret')
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError('https://example.com', 401, 'private-body', {}, None)
    monkeypatch.setattr(ci_callback.urllib.request.OpenerDirector, 'open', fail)
    assert ci_callback.main() == 1
    output = capsys.readouterr().out
    assert '401' in output and 'test-secret' not in output and 'private-body' not in output


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
