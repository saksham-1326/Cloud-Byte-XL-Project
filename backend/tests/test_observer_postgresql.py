"""Controlled HTTP fixtures with real disposable PostgreSQL; not live ML data."""
import base64
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import os
import re
import threading
import time
import urllib.parse
import uuid

import psycopg
from psycopg import sql
import pytest

from backend.app import get_db_connection
from backend.ai_intelligence.observation import Ledger, ObservationError, utc
from backend.ai_intelligence.observer import Observer
from backend.ai_intelligence.observer_client import ObserverClient
from backend.ai_intelligence.store import Store
from backend.tests.test_observer_offline import Response
from backend.tests.test_shadow_postgresql import shadow_db  # noqa: F401; reuse isolated test model fixture


class TestClock:
    __test__=False
    def __init__(self): self.offset=0
    def now(self): return utc()+timedelta(seconds=self.offset)
    def mono(self): return time.monotonic()+self.offset
    def wait(self,seconds): self.offset+=seconds; return False


class GitHubFixture:
    def __init__(self,repo,run):
        self.repo=repo
        self.runs={(1,1):{**copy.deepcopy(run),'repository':{'full_name':repo}}}
        self.jobs_by_attempt={(1,1):[]}
        self.extra_discovery=[]
        self.override_discovery=None
        self.calls=[]
        self.exact_reads=0
        self.race_at=None

    def open(self,request,timeout):
        parsed=urllib.parse.urlsplit(request.full_url)
        path=parsed.path;self.calls.append(path)
        if path.endswith('/actions/runs'):
            runs=self.override_discovery if self.override_discovery is not None else [r for r in self.runs.values() if r['status']=='queued']
            latest={}
            for r in runs:
                if r['id'] not in latest or r['run_attempt']>latest[r['id']]['run_attempt']:
                    latest[r['id']]=r
            items=copy.deepcopy(list(latest.values())+self.extra_discovery)
            return Response({'workflow_runs':items,'total_count':len(items)})
        exact=re.search(r'/actions/runs/(\d+)/attempts/(\d+)(/jobs)?$',path)
        if exact:
            key=tuple(map(int,exact.group(1,2)))
            if exact.group(3):
                return Response({'jobs':copy.deepcopy(self.jobs_by_attempt[key])})
            self.exact_reads+=1
            if self.race_at==self.exact_reads:
                self.runs[key]['status']='in_progress'
            return Response(copy.deepcopy(self.runs[key]))
        if '/commits/' in path: return Response({'files':[]})
        if '/contents/' in path: return Response({'content':base64.b64encode(b'jobs:\n  test:').decode()})
        raise AssertionError('Unexpected MOCK HTTP path: '+path)


@pytest.fixture
def case(shadow_db,tmp_path):
    writer,repo,run,version=shadow_db
    role='observer_reader_'+uuid.uuid4().hex
    with get_db_connection() as conn:
        conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal('isolated-reader-only')))
        conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(os.environ['DB_NAME']),sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT SELECT ON ai_runs,ai_models,ai_predictions,ai_outcomes TO {}').format(sql.Identifier(role)))
    def connect_reader():
        return psycopg.connect(host='127.0.0.1',port=os.environ['DB_PORT'],dbname=os.environ['DB_NAME'],
            user=role,password='isolated-reader-only',connect_timeout=5,
            options='-c default_transaction_read_only=on -c statement_timeout=5000')
    reader=Store(connect_reader)
    clock=TestClock(); github=GitHubFixture(repo,run)
    opened=[]
    model=writer.models(repo)[0]
    def make(path=None,**overrides):
        ledger=Ledger(path or tmp_path/(str(len(opened))+'.jsonl'),
                      secrets=('offline-observer-token',),now=clock.now)
        client=ObserverClient(repo,'offline-observer-token',ledger,budget=500,duration=900,
            opener=github,now=clock.now,monotonic=clock.mono,wait=clock.wait,jitter=lambda:0)
        params=dict(repo=repo,allowlist=[repo],writer=writer,reader=reader,client=client,ledger=ledger,
                    model_version=version,model_digest=model['artifact_sha256'],now=clock.now,
                    clock_uncertainty=.5,clock_evidence='controlled-fixture-clock',session_kind='controlled_test')
        params.update(overrides)
        try:
            observer=Observer(**params)
        except Exception:
            ledger.close()
            raise
        opened.append((observer,ledger))
        return observer
    def completed(key=(1,1),start_offset=20,job_change=None,conclusion='failure'):
        start=utc()+timedelta(seconds=start_offset)
        github.runs[key].update(status='completed',conclusion=conclusion)
        job=dict(id=10+key[1],run_id=key[0],run_attempt=key[1],head_sha=run['head_sha'],
                 name='test',status='completed',conclusion=conclusion,
                 started_at=start.isoformat(),completed_at=(start+timedelta(seconds=1)).isoformat(),steps=[])
        if job_change:job.update(job_change)
        github.jobs_by_attempt[key]=[job]
        clock.offset=60
    try:
        yield dict(writer=writer,reader=reader,repo=repo,run=run,version=version,clock=clock,
                   github=github,make=make,completed=completed,tmp=tmp_path,model=model)
    finally:
        for observer,ledger in opened:
            observer.service.executor.shutdown(wait=True)
            ledger.close()
        with get_db_connection() as conn:
            conn.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
            conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))


def evaluations(observer):
    return [r['data'] for r in observer.ledger.records if r['event']=='evaluation']


def test_new_queue_prediction_real_readonly_readback_outcome_and_immutability(case):
    obs=case['make']();obs.preflight();obs.tick()
    before=case['writer'].predictions(case['repo'])[0]
    proof=obs.proofs[(1,1)]
    assert proof['database_commit_at'] is None and proof['persistence']=='independently_read_committed'
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        case['reader'].query('CREATE TABLE forbidden_observer_write(id int)')
    case['completed']();obs.tick()
    assert evaluations(obs)[-1]['decision']=='eligible_prestart'
    assert evaluations(obs)[-1]['session_kind']=='controlled_test'
    after=case['writer'].predictions(case['repo'])[0]
    from backend.tests.test_shadow_postgresql import immutable
    assert immutable(before)==immutable(after)
    assert after['actual_label']==1


@pytest.mark.parametrize('status,conclusion',[('in_progress',None),('completed','failure')])
def test_already_running_or_completed_discovery_never_predicts(case,status,conclusion):
    case['github'].runs[1,1].update(status=status,conclusion=conclusion)
    case['github'].override_discovery=[case['github'].runs[1,1]]
    obs=case['make']();obs.tick()
    assert not case['writer'].predictions(case['repo'])
    assert evaluations(obs)[-1]['reason']=='not_queued_without_outcome'


def test_short_queue_window_rechecked_by_original_prediction_service(case):
    case['github'].race_at=3  # queued precheck + service initial read, then start before final read
    obs=case['make']();obs.tick()
    assert not case['writer'].predictions(case['repo'])
    assert any(r['event']=='prediction_result' and r['data']['result']['status']=='skipped' for r in obs.ledger.records)


def test_rerun_old_run_id_uses_new_attempt_and_no_created_time_filter(case):
    github=case['github'];github.runs[1,1].update(status='completed',conclusion='success')
    github.runs[1,2]={**github.runs[1,1],'run_attempt':2,'status':'queued','conclusion':None,
                      'created_at':(utc()-timedelta(hours=1)).isoformat()}
    github.jobs_by_attempt[1,2]=[]
    obs=case['make']();obs.tick()
    assert case['writer'].predictions(case['repo'])[0]['attempt']==2
    case['completed']((1,2));obs.tick()
    assert evaluations(obs)[-1]['attempt']==2
    assert evaluations(obs)[-1]['decision']=='eligible_prestart'


def test_duplicate_discovery_results_do_not_duplicate_prediction_requests(case):
    case['github'].extra_discovery=[case['github'].runs[1,1]]*3
    obs=case['make']();obs.tick();obs.tick()
    assert len(case['writer'].predictions(case['repo']))==1
    assert sum(r['event']=='prediction_request' for r in obs.ledger.records)==1


def test_old_rerun_before_model_training_cutoff_is_conservatively_skipped(case):
    case['github'].runs[1,1]['created_at']=(utc()-timedelta(days=5)).isoformat()
    case['github'].runs[1,1]['run_attempt']=2
    case['github'].runs[1,2]=case['github'].runs.pop((1,1))
    case['github'].jobs_by_attempt[1,2]=[]
    obs=case['make']();obs.tick()
    assert not case['writer'].predictions(case['repo'])
    assert evaluations(obs)[-1]['reason']=='prediction_service_skipped'


def test_restart_recovers_original_readback_and_pending_outcome(case):
    path=case['tmp']/'restart.jsonl'
    first=case['make'](path);first.tick();original=first.proofs[(1,1)]
    first.service.executor.shutdown(wait=True);first.ledger.close()
    case['completed']()
    second=case['make'](path);second.tick()
    assert second.proofs[(1,1)]==original
    assert evaluations(second)[-1]['decision']=='eligible_prestart'
    assert sum(r['event']=='prediction_request' for r in second.ledger.records)==1


def test_lost_prestart_readback_cannot_be_invented_on_restart(case):
    obs=case['make']()
    original_read=obs.read
    calls=[0]
    def fail_after_prediction(*args):
        calls[0]+=1
        if calls[0]==2:raise psycopg.OperationalError('private DSN must not be logged')
        return original_read(*args)
    obs.read=fail_after_prediction
    obs.tick()
    assert len(case['writer'].predictions(case['repo']))==1 and not obs.proofs
    case['completed']();obs.read=original_read;obs.tick()
    assert evaluations(obs)[-1]['decision']=='excluded'
    assert evaluations(obs)[-1]['reason']=='late_or_ambiguous_persistence'
    assert 'private DSN' not in obs.ledger.path.read_text()


def test_reader_failure_before_prediction_blocks_inference(case):
    obs=case['make']()
    def unavailable(*args):raise psycopg.OperationalError('do not print private database details')
    obs.read=unavailable
    obs.tick()
    assert not case['writer'].predictions(case['repo'])
    assert not any(r['event']=='prediction_request' for r in obs.ledger.records)
    assert 'private database details' not in obs.ledger.path.read_text()


def test_queued_run_with_already_executing_job_cannot_request_prediction(case):
    case['github'].jobs_by_attempt[1,1]=[dict(id=1,run_id=1,run_attempt=1,
        head_sha=case['run']['head_sha'],status='in_progress',started_at=None)]
    obs=case['make']();obs.tick()
    assert evaluations(obs)[-1]['reason']=='job_already_started'
    assert not case['writer'].predictions(case['repo'])


def test_direct_runner_requires_explicit_allowlist(case):
    with pytest.raises(ObservationError,match='allowlisted'):case['make'](allowlist=[])


@pytest.mark.parametrize('change',[{'head_sha':None},{'repository':{'full_name':'other/repository'}}])
def test_missing_sha_or_repository_mismatch_is_rejected_before_inference(case,change):
    case['github'].runs[1,1].update(change)
    obs=case['make']();obs.tick()
    assert not case['writer'].predictions(case['repo'])
    assert any(r['event']=='discovery_rejected' for r in obs.ledger.records)


def test_operator_pins_existing_model_no_fallback_or_retraining(case):
    obs=case['make'](model_digest='b'*64)
    with pytest.raises(ObservationError,match='model'):obs.preflight()
    assert not case['github'].calls and not case['writer'].predictions(case['repo'])


def test_existing_prediction_with_wrong_model_is_not_accepted(case):
    obs=case['make']();obs.tick()
    new_version=str(uuid.uuid4())
    case['writer'].model(case['repo'],new_version,{'status':'experimental'})
    case['writer'].query('UPDATE ai_predictions SET model_version=%s WHERE repository=%s',
                         (new_version,case['repo']))  # Test-only administrator tampering.
    obs.tick()
    assert evaluations(obs)[-1]['reason']=='prediction_identity_or_model_mismatch'


@pytest.mark.parametrize('change',[{'started_at':None},{'completed_at':None}])
def test_missing_job_timestamps_remain_unverifiable(case,change):
    obs=case['make']();obs.tick();case['completed'](job_change=change);obs.tick()
    assert evaluations(obs)[-1]['decision']=='unverifiable'


@pytest.mark.parametrize('uncertainty,reference',[(None,None),(120,'declared-large-error')])
def test_unknown_or_large_clock_error_cannot_qualify(case,uncertainty,reference):
    obs=case['make'](clock_uncertainty=uncertainty,clock_evidence=reference)
    obs.tick();case['completed']();obs.tick()
    assert evaluations(obs)[-1]['decision']!='eligible_prestart'


def test_actual_job_start_before_persistence_is_excluded(case):
    obs=case['make']();obs.tick();case['completed'](start_offset=-5);obs.tick()
    assert evaluations(obs)[-1]['reason']=='late_or_ambiguous_persistence'


def test_concurrent_observers_separate_ledgers_share_one_original_prediction(case):
    first,second=case['make'](),case['make']()
    gate=threading.Barrier(2)
    def tick(observer):gate.wait(timeout=10);observer.tick()
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(tick,[first,second]))
    assert len(case['writer'].predictions(case['repo']))==1
    assert first.proofs[(1,1)]['original_sha256']==second.proofs[(1,1)]['original_sha256']


def test_prediction_database_constraint_failure_rolls_back_and_retries_idempotently(case,monkeypatch):
    obs=case['make']();original=case['writer'].predict
    def fail(*args):
        bad=list(args);bad[4]=2  # database probability CHECK must roll back
        return original(*bad)
    monkeypatch.setattr(case['writer'],'predict',fail)
    obs.tick()
    assert not case['writer'].predictions(case['repo'])
    monkeypatch.setattr(case['writer'],'predict',original)
    obs.tick()
    assert len(case['writer'].predictions(case['repo']))==1


def test_restart_rejects_configuration_drift(case):
    path=case['tmp']/'drift.jsonl';first=case['make'](path);first.ledger.close()
    with pytest.raises(ObservationError,match='configuration'):
        case['make'](path,interval=30)


def test_graceful_cancel_never_collects_gitHub_or_predicts(case):
    obs=case['make']();obs.client.stop.set()
    result=obs.run()
    assert result['reason']=='cancelled' and not case['github'].calls
    assert not case['writer'].predictions(case['repo'])
    assert obs.ledger.records[-1]['event']=='session_stopped'


def test_minimal_writer_grants_allow_lifecycle_but_prevent_model_or_probability_edits(case):
    role='observer_writer_'+uuid.uuid4().hex
    tables=['ai_models','ai_runs','ai_jobs','ai_steps','ai_predictions','ai_outcomes','ai_shadow_events']
    with get_db_connection() as conn:
        conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role),sql.Literal('isolated-writer-only')))
        conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(os.environ['DB_NAME']),sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(sql.SQL(',').join(map(sql.Identifier,tables)),sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT INSERT,UPDATE ON ai_runs,ai_jobs,ai_steps,ai_outcomes,ai_shadow_events TO {}').format(sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT INSERT ON ai_predictions TO {}').format(sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT UPDATE(verification_status) ON ai_predictions TO {}').format(sql.Identifier(role)))
    def connect():
        return psycopg.connect(host='127.0.0.1',hostaddr='127.0.0.1',port=os.environ['DB_PORT'],
            dbname=os.environ['DB_NAME'],user=role,password='isolated-writer-only',connect_timeout=5)
    restricted=Store(connect)
    try:
        obs=case['make'](writer=restricted);obs.preflight();obs.tick()
        case['completed']();obs.tick()
        assert evaluations(obs)[-1]['decision']=='eligible_prestart'
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            restricted.query('UPDATE ai_predictions SET probability=.99 WHERE repository=%s',(case['repo'],))
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            restricted.query("UPDATE ai_models SET status='replaced' WHERE repository=%s",(case['repo'],))
    finally:
        with get_db_connection() as conn:
            conn.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
            conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
