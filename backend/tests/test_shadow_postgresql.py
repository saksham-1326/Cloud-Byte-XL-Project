"""Simulated GitHub lifecycle with REAL isolated PostgreSQL and a test-only model.

These controlled executions are regression tests, never prospective accuracy data.
"""
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import os
import threading
import uuid

import joblib
import psycopg
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline

from backend.app import get_db_connection
from backend.ai_intelligence import ml
from backend.ai_intelligence.migrations import migrate
from backend.ai_intelligence.service import IntelligenceService
from backend.ai_intelligence.store import Store


@pytest.fixture
def shadow_db(tmp_path, monkeypatch):
    if os.getenv('AI_TEST_DATABASE') != '1':
        pytest.skip('Explicit isolated PostgreSQL integration opt-in required')
    assert os.environ['DB_NAME'] == 'cloud_bytexl_ci_test'
    assert os.environ['DB_USER'] == 'cloud_bytexl_ci'
    assert os.environ['DB_HOST'] == '127.0.0.1'
    migrate(get_db_connection)
    store = Store(get_db_connection)
    repo = 'shadow-test/' + uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    run = dict(id=1, run_attempt=1, workflow_id=1, head_sha='a'*40,
               created_at=(now-timedelta(seconds=20)).isoformat(), status='queued',
               conclusion=None, event='push', path='.github/workflows/ci.yml')
    version = str(uuid.uuid4())
    monkeypatch.setattr(ml, 'ARTIFACTS', tmp_path)
    pipeline = make_pipeline(DictVectorizer(sparse=False), DummyClassifier(strategy='prior'))
    pipeline.fit([{'changed_files': 0}, {'changed_files': 1}], [0, 1])
    artifact = tmp_path / (version + '.joblib')
    joblib.dump(pipeline, artifact)
    store.model(repo, version, dict(status='experimental', feature_version=ml.FEATURE_VERSION,
                                   trained_through=(now-timedelta(days=1)).isoformat(), threshold=.5),
                str(artifact), hashlib.sha256(artifact.read_bytes()).hexdigest())
    try:
        yield store, repo, run, version
    finally:
        store.query('DELETE FROM ai_runs WHERE repository=%s', (repo,))
        store.query('DELETE FROM ai_shadow_events WHERE repository=%s', (repo,))
        store.query('DELETE FROM ai_models WHERE repository=%s', (repo,))


class Client:
    def __init__(self, run, change=None):
        self.run_data = run
        self.change = change
        self.calls = 0

    def run(self, *args):
        self.calls += 1
        result = copy.deepcopy(self.run_data)
        if self.calls > 1 and self.change:
            result.update(self.change)
        return result

    def snapshot(self, repo, run):
        return dict(sha=run['head_sha'], historical_ref=run['head_sha'], files=[],
                    workflow_config='jobs:', config_status='available')


def finish(store, repo, run, conclusion='failure', start=None):
    start = start or datetime.now(timezone.utc)+timedelta(seconds=1)
    store.save_run(repo, {**run, 'status': 'completed', 'conclusion': conclusion},
                   [dict(id=10, name='test', status='completed', conclusion=conclusion,
                         started_at=start.isoformat(), completed_at=(start+timedelta(seconds=1)).isoformat(),
                         steps=[])])


def immutable(row):
    return {k: row[k] for k in ['id', 'repository', 'run_id', 'attempt', 'model_version',
                                'predicted_at', 'feature_snapshot', 'probability',
                                'threshold', 'predicted_class', 'mode']}


def test_service_lifecycle_real_persistence_and_duplicate_event(shadow_db):
    store, repo, run, version = shadow_db
    service = IntelligenceService(store, Client(run))
    assert service.predict(repo, 1, 1)['status'] == 'predicted'
    before = store.predictions(repo)[0]
    assert before['model_version'] == uuid.UUID(version)
    assert before['actual_label'] is None and before['mode'] == 'shadow'
    assert before['feature_snapshot']['provenance']['historical_ref'] == run['head_sha']
    assert not {'log_text', 'conclusion', 'duration_seconds'} & before['feature_snapshot']['values'].keys()
    assert service.predict(repo, 1, 1)['status'] == 'already_predicted'
    assert immutable(store.predictions(repo)[0]) == immutable(before)
    finish(store, repo, run)
    after = store.predictions(repo)[0]
    assert immutable(after) == immutable(before)
    assert after['actual_label'] == 1 and after['verification_status'] == 'matched'
    assert after['correct'] == (after['predicted_class'] == 1)
    # A stale event must not turn a completed run back into a queued run.
    store.save_run(repo, run, [])
    assert store.run(repo, 1, 1)['status'] == 'completed'
    assert store.predict(repo, run, version, {}, .9, .5, datetime.now(timezone.utc)) is None


@pytest.mark.parametrize('change', [dict(status='completed', conclusion='failure'),
                                   dict(status='in_progress'), dict(head_sha='b'*40),
                                   dict(head_sha=None), dict(run_attempt=2), dict(id=99)])
def test_run_changes_during_collection_never_persist_prediction(shadow_db, change):
    store, repo, run, _ = shadow_db
    assert IntelligenceService(store, Client(run, change)).predict(repo, 1, 1)['status'] == 'skipped'
    assert store.predictions(repo) == []


@pytest.mark.parametrize('sha', [None, 'b'*40])
def test_snapshot_sha_must_match_before_any_prediction(shadow_db, sha):
    store, repo, run, _ = shadow_db
    class BadSnapshot(Client):
        def snapshot(self, *args):
            return {**super().snapshot(*args), 'historical_ref':sha}
    with pytest.raises(ValueError, match='SHA'):
        IntelligenceService(store, BadSnapshot(run)).predict(repo, 1, 1)
    assert store.predictions(repo) == []


@pytest.mark.parametrize('change', [dict(status='completed', conclusion='success'),
                                   dict(head_sha=None), dict(run_attempt=2), dict(id=99)])
def test_ineligible_initial_identity_or_state(shadow_db, change):
    store, repo, run, _ = shadow_db
    assert IntelligenceService(store, Client({**run, **change})).predict(repo, 1, 1)['status'] == 'skipped'
    assert store.predictions(repo) == []


def test_attempt_and_repository_association_and_commit_guards(shadow_db):
    store, repo, run, version = shadow_db
    store.save_run(repo, run, [])
    now = datetime.now(timezone.utc)
    assert store.predict(repo, {**run, 'head_sha':'b'*40}, version, {}, .7, .5, now) is None
    assert store.predict(repo, {**run, 'run_attempt':2}, version, {}, .7, .5, now) is None
    assert store.predict(repo, run, version, {}, .7, .5, now)
    # Mismatched completed metadata must not attach an outcome to this SHA.
    finish(store, repo, {**run, 'head_sha':'b'*40})
    assert store.predictions(repo)[0]['actual_label'] is None
    second = {**run, 'run_attempt':2}
    store.save_run(repo, second, [])
    assert store.predict(repo, second, version, {}, .2, .5, now)
    finish(store, repo, second, 'success')
    first, later = sorted(store.predictions(repo), key=lambda r:r['attempt'])
    assert first['actual_label'] is None and later['actual_label'] == 0
    other = repo+'-other'
    try:
        store.save_run(other, run, [])
        finish(store, other, run)
        assert next(r for r in store.predictions(repo) if r['attempt']==1)['actual_label'] is None
        store.save_run(other, second, [])
        assert store.predict(other, second, version, {}, .8, .5, now) is None
    finally:
        store.query('DELETE FROM ai_runs WHERE repository=%s', (other,))


def test_concurrent_requests_keep_exactly_one_original_prediction(shadow_db):
    store, repo, run, version = shadow_db
    store.save_run(repo, run, [])
    gate = threading.Barrier(4)
    def request(number):
        gate.wait(timeout=10)
        return store.predict(repo, run, version, {'request':number}, .1*number, .5, datetime.now(timezone.utc))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(request, range(1, 5)))
    assert sum(r is not None for r in results) == 1
    original = immutable(store.predictions(repo)[0])
    finish(store, repo, run)
    assert immutable(store.predictions(repo)[0]) == original


def test_concurrent_service_requests_are_idempotent(shadow_db):
    store, repo, run, _ = shadow_db
    gate = threading.Barrier(4)
    def request(_):
        gate.wait(timeout=10)
        return IntelligenceService(store, Client(run)).predict(repo, 1, 1)['status']
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(request, range(4)))
    assert statuses.count('predicted') == 1
    assert statuses.count('already_predicted') == 3
    assert len(store.predictions(repo)) == 1


def test_completion_waits_for_prediction_transaction_then_reconciles(shadow_db):
    store, repo, run, version = shadow_db
    store.save_run(repo, run, [])
    inserted = threading.Event()
    finish_entered = threading.Event()
    release = threading.Event()
    def predict_uncommitted():
        with store.connect() as connection:
            # Store.predict uses this connection; its context must not commit
            # until the outer transaction releases the run row lock.
            with connection.transaction():
                class NestedConnection:
                    def __enter__(self): return connection
                    def __exit__(self, *args): pass
                result = Store(lambda:NestedConnection()).predict(repo, run, version, {}, .7, .5, datetime.now(timezone.utc))
                inserted.set()
                assert release.wait(10)
            return result
    def complete():
        finish_entered.set()
        finish(store, repo, run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        prediction = pool.submit(predict_uncommitted)
        assert inserted.wait(10)
        completion = pool.submit(complete)
        assert finish_entered.wait(10)
        release.set()
        assert prediction.result(timeout=10)
        completion.result(timeout=10)
    assert store.predictions(repo)[0]['verification_status'] == 'matched'


def test_missing_start_time_is_unverifiable_not_prospective(shadow_db):
    store, repo, run, _ = shadow_db
    assert IntelligenceService(store, Client(run)).predict(repo, 1, 1)['status'] == 'predicted'
    before = immutable(store.predictions(repo)[0])
    store.save_run(repo, {**run, 'status':'completed', 'conclusion':'failure'}, [])
    after = store.predictions(repo)[0]
    assert immutable(after) == before
    assert after['verification_status'] == 'unverifiable_timing'
    assert IntelligenceService(store, Client(run)).evaluation(repo)['live_evaluated'] == 0


def test_database_errors_roll_back_run_and_prediction_transactions(shadow_db):
    store, repo, run, version = shadow_db
    bad_job = dict(id=2, steps=[dict(number='not-an-integer')])
    with pytest.raises(psycopg.Error):
        store.save_run(repo, {**run, 'status':'completed', 'conclusion':'failure'}, [bad_job])
    assert store.run(repo, 1, 1) is None
    assert store.query('SELECT * FROM ai_outcomes WHERE repository=%s', (repo,)) == []
    store.save_run(repo, run, [])
    with pytest.raises(psycopg.errors.CheckViolation):
        store.predict(repo, run, version, {}, 2, .5, datetime.now(timezone.utc))
    assert store.predictions(repo) == []
    assert store.predict(repo, run, version, {}, .7, .5, datetime.now(timezone.utc))


def test_final_recheck_race_after_completion_does_not_restore_queued_state(shadow_db):
    store, repo, run, _ = shadow_db
    class RaceClient(Client):
        def run(self, *args):
            result = super().run(*args)
            if self.calls == 2:
                store.save_run(repo, run, [])
                finish(store, repo, run)
            return result  # Simulate an already stale final GitHub response.
    IntelligenceService(store, RaceClient(run)).predict(repo, 1, 1)
    assert store.run(repo, 1, 1)['status'] == 'completed'
    assert store.predictions(repo) == []


def test_actual_start_before_prediction_is_excluded_without_rewriting(shadow_db):
    store, repo, run, _ = shadow_db
    assert IntelligenceService(store, Client(run)).predict(repo, 1, 1)['status'] == 'predicted'
    before = store.predictions(repo)[0]
    finish(store, repo, run, start=before['predicted_at']-timedelta(seconds=1))
    after = store.predictions(repo)[0]
    assert immutable(after) == immutable(before)
    assert after['verification_status'] == 'invalid_timing'
    assert IntelligenceService(store, Client(run)).evaluation(repo)['live_evaluated'] == 0
