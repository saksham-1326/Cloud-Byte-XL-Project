"""Mocked HTTP and offline configuration tests; never contacts GitHub."""
from datetime import datetime, timedelta, timezone
import io
import json
import threading
import urllib.error

import pytest

from backend.ai_intelligence.observation import Ledger, ObservationError
from backend.ai_intelligence.observer_client import ObserverClient
from backend.tools.observe_actions import database_settings, main, clock_reference, connection_factory


class Clock:
    def __init__(self):
        self.start=datetime.now(timezone.utc)
        self.offset=0

    def now(self): return self.start+timedelta(seconds=self.offset)
    def mono(self): return self.offset
    def wait(self, seconds): self.offset+=seconds; return False


class Response:
    def __init__(self, data=None, headers=None, raw=None):
        self.body=raw if raw is not None else json.dumps(data).encode()
        self.headers=headers or {}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,size=-1):
        result=self.body if size<0 else self.body[:size]
        self.body=self.body[len(result):]
        return result


class Opener:
    def __init__(self, responses): self.responses=list(responses); self.requests=[]
    def open(self, request, timeout):
        self.requests.append(request)
        result=self.responses.pop(0)
        if isinstance(result,Exception): raise result
        return result


def http(code, headers=None, body=b'{}'):
    return urllib.error.HTTPError('https://api.github.com/repos/o/r/actions/runs',code,
                                  'private-error-text',headers or {},io.BytesIO(body))


@pytest.fixture
def transport(tmp_path):
    opened=[]
    def make(responses,budget=20,retries=3,**kwargs):
        clock=Clock()
        ledger=Ledger(tmp_path/(str(len(opened))+'.jsonl'),secrets=('private-observer-test-token',),now=clock.now)
        opened.append(ledger)
        opener=Opener(responses)
        client=ObserverClient('o/r','private-observer-test-token',ledger,budget=budget,
            opener=opener,now=clock.now,monotonic=clock.mono,wait=clock.wait,jitter=lambda:0,
            retries=retries,**kwargs)
        return client,opener,ledger,clock
    yield make
    for ledger in opened: ledger.close()


def test_conditional_discovery_cache_but_exact_attempt_always_fresh(transport):
    run=dict(id=1,run_attempt=1,workflow_id=1,head_sha='a'*40,repository={'full_name':'o/r'})
    client,opener,ledger,_=transport([
        Response({'workflow_runs':[run],'total_count':1},{'ETag':'"v1"'}),http(304),Response(run)])
    assert client.discover()==[run]
    assert client.discover()==[run]
    assert client.run('o/r',1,1)==run
    assert opener.requests[1].get_header('If-none-match')=='"v1"'
    assert not opener.requests[2].has_header('If-none-match')
    assert client.requests==3
    assert any(r['data'].get('cached') is True for r in ledger.records)


def test_paginated_discovery_follows_links_and_counts_every_request(transport):
    next_url='https://api.github.com/repos/o/r/actions/runs?status=queued&per_page=100&page=2'
    client,opener,_,_=transport([Response({'workflow_runs':[{'id':1}],'total_count':2},
        {'Link':f'<{next_url}>; rel="next"'}),Response({'workflow_runs':[{'id':2}],'total_count':2})])
    assert len(client.discover())==2
    assert opener.requests[-1].full_url==next_url and client.requests==2


@pytest.mark.parametrize('link', ['https://evil.example/repos/o/r/actions/runs',
                                'https://api.github.com/repos/other/repo/actions/runs'])
def test_pagination_never_leaks_token_to_other_origin_or_repo(transport,link):
    client,opener,_,_=transport([Response({'workflow_runs':[],'total_count':1}, {'Link':f'<{link}>; rel="next"'})])
    with pytest.raises(ObservationError,match='untrusted'):
        client.discover()
    assert len(opener.requests)==1


def test_truncated_discovery_is_not_complete_coverage(transport):
    client,_,_,_=transport([Response({'workflow_runs':[],'total_count':1001})])
    with pytest.raises(ObservationError,match='incomplete'): client.discover()


@pytest.mark.parametrize('status,headers,body', [
    (429,{'Retry-After':'75'},b'{}'),
    (403,{'X-RateLimit-Remaining':'0','X-RateLimit-Reset':'0'},b'{}'),
    (403,{},b'{"message":"secondary rate limit"}'),
])
def test_structured_rate_backoff_and_reservation_budget(transport,status,headers,body):
    client,_,ledger,clock=transport([http(status,headers,body),Response({})])
    assert client.get('/repos/o/r/actions/runs')=={}
    assert clock.offset>=60
    assert client.requests==2
    backoff=next(r for r in ledger.records if r['event']=='http_backoff')
    assert backoff['data']['reason']=='github_rate_limited'


@pytest.mark.parametrize('status',[401,403,404,302])
def test_permission_resource_and_redirect_errors_do_not_retry(transport,status):
    client,opener,_,_=transport([http(status)])
    with pytest.raises(ObservationError): client.get('/repos/o/r/actions/runs')
    assert len(opener.requests)==1


@pytest.mark.parametrize('error',[urllib.error.URLError('private connection string'),TimeoutError('private'),http(503)])
def test_network_outage_has_bounded_retries_and_no_error_body_logging(transport,error):
    client,opener,ledger,clock=transport([error,error,error])
    with pytest.raises(ObservationError): client.get('/repos/o/r/actions/runs')
    assert len(opener.requests)==3 and clock.offset>=3
    content=ledger.path.read_text()
    assert 'private connection string' not in content and 'private-error-text' not in content


def test_total_budget_includes_service_snapshot_paths(transport):
    client,opener,_,_=transport([Response({}),Response({})],budget=1)
    client.get('/repos/o/r/commits/'+'a'*40)
    with pytest.raises(ObservationError,match='budget'):
        client.get('/repos/o/r/actions/runs')
    assert len(opener.requests)==1


def test_backoff_does_not_bypass_session_duration(transport):
    client,opener,_,clock=transport([http(429,{'Retry-After':'300'})],duration=5)
    with pytest.raises(ObservationError,match='duration'): client.get('/repos/o/r/actions/runs')
    assert clock.offset==5 and len(opener.requests)==1


def test_cancellation_prevents_new_network_calls(transport):
    client,opener,_,_=transport([])
    client.stop.set()
    with pytest.raises(ObservationError,match='cancelled'):client.discover()
    assert not opener.requests


def test_cancellation_interrupts_rate_wait(transport):
    client,opener,_,_=transport([http(429,{'Retry-After':'90'})])
    client.waiter=lambda seconds: client.stop.set() or True
    with pytest.raises(ObservationError,match='cancelled'):client.discover()
    assert len(opener.requests)==1


def test_restart_preserves_budget_duration_and_chain(tmp_path):
    path=tmp_path/'restart.jsonl'; clock=Clock()
    with Ledger(path,now=clock.now) as ledger:
        ledger.append('session',profile_digest='test')
        client=ObserverClient('o/r','test-private-token',ledger,budget=1,opener=Opener([Response({})]),
                              now=clock.now,monotonic=clock.mono)
        client.get('/repos/o/r/actions/runs')
    original=path.read_bytes()
    with Ledger(path,now=clock.now) as ledger:
        client=ObserverClient('o/r','test-private-token',ledger,budget=1,now=clock.now,monotonic=clock.mono)
        with pytest.raises(ObservationError,match='budget'):client.discover()
    assert path.read_bytes()==original


def test_ledger_lock_corruption_and_secret_redaction(tmp_path):
    path=tmp_path/'evidence.jsonl'
    with Ledger(path,secrets=('private-token-value',)) as ledger:
        ledger.append('test',value='Bearer private-token-value',password='hidden',
                      url='postgresql://user:password@host/db',
                      headers={'Authorization':'Bearer an-unknown-secret','Cookie':'session=unknown'})
        with pytest.raises(ObservationError,match='in_use'):Ledger(path)
    text=path.read_text()
    assert 'private-token-value' not in text and 'hidden' not in text and 'user:password' not in text
    assert 'an-unknown-secret' not in text and 'session=unknown' not in text
    path.write_text(text.replace('"event":"test"','"event":"tampered"'))
    with pytest.raises(ObservationError):Ledger(path)


def test_partial_ledger_is_not_silently_truncated(tmp_path):
    path=tmp_path/'partial.jsonl';path.write_bytes(b'{"incomplete":')
    with pytest.raises(ObservationError):Ledger(path)
    assert path.read_bytes()==b'{"incomplete":'


def test_disallowed_api_paths_and_binary_logs_fail_before_http(transport):
    client,opener,_,_=transport([])
    for path in ['/repos/other/repo/actions/runs','https://evil.example','/repos/o/r/../other']:
        with pytest.raises(ObservationError):client.get(path)
    with pytest.raises(ObservationError):client.request('/repos/o/r/actions/jobs/1/logs',binary=True)
    assert not opener.requests


def test_dry_run_is_configuration_only_no_ledger_or_sockets(monkeypatch,capsys,tmp_path):
    import psycopg
    monkeypatch.setenv('GITHUB_TOKEN','offline-private-token')
    for kind,user in [('WRITER','writer'),('READER','reader')]:
        monkeypatch.setenv('OBSERVER_'+kind+'_DSN',f'host=127.0.0.1 port=55439 dbname=cloud_bytexl_observation_dry user=cloud_bytexl_observer_{user} password=offline-only')
    monkeypatch.setattr(psycopg,'connect',lambda **kwargs:pytest.fail('Dry run must not open a database'))
    monkeypatch.chdir(tmp_path)
    args=['--dry-run','--repository','o/r','--allow-repository','o/r',
          '--model-version','00000000-0000-0000-0000-000000000001','--model-sha256','a'*64]
    assert main(args)==0
    assert 'offline-private-token' not in capsys.readouterr().out
    assert not (tmp_path/'backend').exists()
    assert main(args+['--interval','0'])==1


@pytest.mark.parametrize('dsn',[
    '', 'host=remote.example port=5432 dbname=cloud_bytexl_observation_a user=cloud_bytexl_observer_writer password=test',
    'host=127.0.0.1 port=5432 dbname=bytexl user=postgres password=test',
    'service=personal',
])
def test_cli_rejects_personal_remote_or_implicit_database_configuration(dsn):
    with pytest.raises(ObservationError):database_settings(dsn)


def test_clock_evidence_needs_bounded_measurement_and_valid_session_horizon(tmp_path):
    path=tmp_path/'clock.json'; now=datetime.now(timezone.utc)
    data=dict(measured_at=(now-timedelta(seconds=5)).isoformat(),
              valid_until=(now+timedelta(hours=1)).isoformat(),max_error_seconds=2,
              method='controlled fixture, not an actual clock measurement')
    path.write_text(json.dumps(data))
    assert clock_reference(path,3,600)['max_error_seconds']==2
    with pytest.raises(ObservationError):clock_reference(path,1,600)
    with pytest.raises(ObservationError):clock_reference(path,3,7200)
    assert clock_reference(None,None,600) is None


def test_exhausted_retry_still_preserves_rate_cooldown_for_next_poll(transport):
    client,opener,_,clock=transport([http(429,{'Retry-After':'75'}),Response({})],retries=1)
    with pytest.raises(ObservationError,match='rate_limited'):client.get('/repos/o/r/actions/runs')
    assert client.get('/repos/o/r/actions/runs')=={}
    assert clock.offset>=75 and len(opener.requests)==2


def test_provider_poll_interval_is_respected_for_same_resource(transport):
    client,_,_,clock=transport([Response({}, {'X-Poll-Interval':'30'}),Response({})])
    client.get('/repos/o/r/actions/runs')
    client.get('/repos/o/r/actions/runs')
    assert clock.offset>=30


def test_rate_cooldown_survives_restart(tmp_path):
    clock=Clock();path=tmp_path/'cooldown.jsonl'
    with Ledger(path,now=clock.now) as ledger:
        client=ObserverClient('o/r','test-private-token',ledger,retries=1,
            opener=Opener([http(429,{'Retry-After':'75'})]),now=clock.now,
            monotonic=clock.mono,wait=clock.wait,jitter=lambda:0)
        with pytest.raises(ObservationError):client.get('/repos/o/r/actions/runs')
    with Ledger(path,now=clock.now) as ledger:
        client=ObserverClient('o/r','test-private-token',ledger,
            opener=Opener([Response({})]),now=clock.now,monotonic=clock.mono,
            wait=clock.wait,jitter=lambda:0)
        assert client.get('/repos/o/r/actions/runs')=={}
    assert clock.offset>=75


def test_response_size_and_invalid_json_fail_closed(transport):
    for raw in [b'not json',b'x'*5_000_001]:
        client,opener,_,_=transport([Response(raw=raw)])
        with pytest.raises(ObservationError):client.get('/repos/o/r/actions/runs')
        assert len(opener.requests)==1


def test_inherited_pg_hostaddr_cannot_redirect_loopback_connection(monkeypatch):
    import psycopg
    captured={}
    class Result:
        def __init__(self,row):self.row=row
        def fetchone(self):return self.row
    class Connection:
        def execute(self,query):
            return Result(('cloud_bytexl_observation_unit','cloud_bytexl_observer_reader',False)
                          if query.startswith('SELECT') else ('on',))
    def connect(**kwargs):captured.update(kwargs);return Connection()
    monkeypatch.setenv('PGHOSTADDR','192.0.2.1')
    monkeypatch.setattr(psycopg,'connect',connect)
    fields=database_settings('host=localhost port=55440 dbname=cloud_bytexl_observation_unit user=cloud_bytexl_observer_reader password=offline-test-only')
    connection_factory(fields,readonly=True)()
    assert captured['hostaddr']=='127.0.0.1'


def test_short_ledger_write_fails_closed_before_any_http(tmp_path):
    path=tmp_path/'short-write.jsonl'
    with Ledger(path) as ledger:
        original=ledger.file
        class ShortWrite:
            def write(self,data):return original.write(data[:5])
            def close(self):original.close()
        ledger.file=ShortWrite()
        client=ObserverClient('o/r','offline-token',ledger,opener=Opener([]))
        with pytest.raises(ObservationError,match='write_failed'):client.discover()
        assert not client.opener.requests and not ledger.records
        with pytest.raises(ObservationError,match='not_writable'):ledger.append('test')
    with pytest.raises(ObservationError):Ledger(path)
