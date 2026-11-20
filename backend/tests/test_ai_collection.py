import io
import os
import pytest
from backend.ai_intelligence.github import ActionsClient, GitHubError, redact, repository_name
from backend.ai_intelligence.store import label


class Response(io.BytesIO):
    def __init__(self,data,headers=None):
        super().__init__(data);self.headers=headers or {}


def test_pagination_and_auth_header():
    class Opener:
        def __init__(self):self.calls=[]
        def open(self,req,timeout):
            self.calls.append(req)
            return Response(b'{"workflow_runs":[{"id":1}]}' if len(self.calls)==1 else b'{"workflow_runs":[{"id":2}]}',{'Link':'<next>; rel="next"'} if len(self.calls)==1 else {})
    opener=Opener();client=ActionsClient('test-token',opener)
    assert [r['id'] for r in client.runs('test/repo')]==[1,2]
    assert 'page=2' in opener.calls[-1].full_url
    assert opener.calls[0].get_header('Authorization')=='Bearer test-token'


def test_pagination_does_not_silently_truncate():
    class Opener:
        def open(self,*args,**kwargs):return Response(b'{"jobs":[]}',{'Link':'<next>; rel="next"'})
    with pytest.raises(GitHubError,match='Pagination'):
        ActionsClient('',Opener()).pages('/repos/test/repo/actions/runs','jobs',max_pages=1)


def test_redaction(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN','configured-secret')
    text=redact('Authorization: Bearer abcdef\npassword=hello GITHUB_TOKEN=configured-secret\nghp_123456789abcdef\nhttps://bob:secret@host/')
    assert 'configured-secret' not in text and 'hello' not in text and 'abcdef' not in text and 'bob:secret' not in text


@pytest.mark.parametrize('value',['https://evil.com','../../file','repo','a/b/c','a b/c'])
def test_repo_validation(value):
    with pytest.raises(ValueError):repository_name(value)


def test_label_policy():
    assert label('success')==0 and label('failure')==1
    for value in ['cancelled','skipped','timed_out','action_required',None]:assert label(value) is None

def test_rate_limit_and_expired_log_handling():
    import urllib.error
    class Opener:
        def __init__(self,code):self.code=code
        def open(self,req,timeout):raise urllib.error.HTTPError(req.full_url,self.code,'not copied',{'Retry-After':'60'},None)
    for code,expected in [(429,429),(403,429),(404,404),(410,410)]:
        with pytest.raises(GitHubError) as caught:ActionsClient('',Opener(code)).get('/repos/test/repo/actions/runs')
        assert caught.value.status==expected
        assert 'not copied' not in str(caught.value)


def test_signed_log_redirect_never_forwards_github_token():
    import urllib.error
    class Opener:
        def __init__(self):self.calls=[]
        def open(self,req,timeout):
            self.calls.append(req)
            if len(self.calls)==1:raise urllib.error.HTTPError(req.full_url,302,'redirect',{'Location':'https://logs.blob.core.windows.net/signed-log'},None)
            return Response(b'example log')
    opener=Opener();text=ActionsClient('server-token',opener).job_log('test/repo',12)
    assert text=='example log'
    assert opener.calls[0].get_header('Authorization')
    assert opener.calls[1].get_header('Authorization') is None

def test_quoted_multispace_credentials_and_structured_scrubbing():
    from backend.ai_intelligence.github import scrub
    text=redact('password="two private words"\nSECRET_KEY=\'another private phrase\'\npostgresql://someone:private-value@db/service')
    assert 'private words' not in text and 'private phrase' not in text and 'private-value' not in text
    source={'head_commit':{'message':'set password="two private words"'},'nested':{'api_key':'fixture-value'}}
    cleaned=scrub(source)
    assert 'private words' not in cleaned['head_commit']['message']
    assert cleaned['nested']['api_key']=='[REDACTED]'


@pytest.mark.parametrize('cached_jobs', [[], [{
    'payload': {'status': 'in_progress', 'conclusion': None},
    'log_status': 'pending',
}]])
def test_sync_retries_incomplete_jobs_and_then_skips_complete_attempt(cached_jobs):
    from backend.ai_intelligence.collector import synchronize

    run = {'id': 21, 'run_attempt': 1, 'status': 'completed',
           'head_sha': 'abc', 'path': '.github/workflows/ci.yml'}

    class MemoryStore:
        jobs_cache = cached_jobs
        def run(self, *args):
            return {'status': 'completed', 'commit_sha': 'abc', 'payload': run}
        def jobs(self, *args): return self.jobs_cache
        def snapshot(self, *args): return {'historical_ref': 'abc'}
        def save_run(self, repo, latest, jobs):
            self.jobs_cache = [{'payload': job, 'log_status': job['log_status']} for job in jobs]
        def runs(self, repo): return [run]

    class Client:
        log_calls = 0
        def get(self, path): return {'id': 1}
        def runs(self, repo): return [run]
        def jobs(self, *args):
            return [{'id': 123, 'status': 'completed', 'conclusion': 'failure'}]
        def job_log(self, *args):
            self.log_calls += 1
            return 'explicit exit 1'

    store, client = MemoryStore(), Client()
    assert synchronize(client, store, 'test/repo')['processed_attempts'] == 1
    assert store.jobs_cache[0]['payload']['log_text'] == 'explicit exit 1'
    assert synchronize(client, store, 'test/repo')['processed_attempts'] == 0
    assert client.log_calls == 1


def test_sync_empty_completed_jobs_remain_retryable_and_warn():
    from backend.ai_intelligence.collector import synchronize
    from unittest.mock import Mock
    run = {'id': 21, 'run_attempt': 1, 'status': 'completed',
           'head_sha': 'abc', 'path': '.github/workflows/ci.yml'}
    client = Mock()
    client.get.return_value = {'id': 1}
    client.runs.return_value = [run]
    client.jobs.return_value = []
    store = Mock()
    store.run.return_value = {'status': 'completed', 'commit_sha': 'abc', 'payload': run}
    store.jobs.return_value = []
    store.snapshot.return_value = {'historical_ref': 'abc'}
    store.runs.return_value = [run]
    for _ in range(2):
        result = synchronize(client, store, 'test/repo')
        assert result['processed_attempts'] == 1
        assert 'No jobs returned' in result['warnings'][0]['message']
    assert client.jobs.call_count == 2


def test_sync_marks_running_jobs_pending():
    from backend.ai_intelligence.collector import synchronize
    from unittest.mock import Mock
    client, store = Mock(), Mock()
    client.get.return_value = {'id': 1}
    client.runs.return_value = [{'id': 21, 'status': 'in_progress', 'head_sha': 'abc'}]
    client.jobs.return_value = [{'id': 123, 'status': 'in_progress', 'conclusion': None}]
    store.run.return_value = None
    store.runs.return_value = []
    synchronize(client, store, 'test/repo')
    assert store.save_run.call_args.args[2][0]['log_status'] == 'pending'
    client.job_log.assert_not_called()
