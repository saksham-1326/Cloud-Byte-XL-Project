"""Real transactions and loopback HTTP only; never uses a development database."""
import concurrent.futures
import contextlib
import http.client
import json
import os
import runpy
import shutil
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

import psycopg
from psycopg import sql
from flask import Flask
import pytest

from backend.ci_callbacks import (
    CallbackError, register_ci_callbacks, register_execution, validate_payload,
)
from backend.app import get_db_connection
from backend.ai_intelligence.migrations import migrate


def payload():
    return dict(repository='test/repo', run_id=21, attempt=1, commit_sha='a'*40,
        delivery_id=str(uuid.uuid4()), workflow='CI', status='SUCCESS',
        build='PASSED', tests='PASSED', docker='PASSED')


def app_for(connect):
    app = Flask(__name__)
    register_ci_callbacks(app, connect)
    return app


@pytest.mark.parametrize('change', [
    {'run_id':True}, {'run_id':0}, {'run_id':2**63}, {'attempt':0}, {'attempt':'1'},
    {'commit_sha':'short'}, {'delivery_id':[]}, {'repository':'https://evil.invalid'},
    {'workflow':'x'*161}, {'status':[]}, {'build':[]}, {'status':'unknown'},
    {'status':'SUCCESS','tests':'FAILED'}, {'unexpected':'value'},
    {'workflow':'\ud800'},
])
def test_payload_rejected(change):
    with pytest.raises(CallbackError): validate_payload({**payload(), **change})


def test_auth_and_allowlist_fail_before_database(monkeypatch):
    def forbidden(): raise AssertionError('No database access expected')
    client = app_for(forbidden).test_client()
    monkeypatch.delenv('CI_STATUS_TOKEN', raising=False)
    assert client.post('/api/ci/v1/status', json=payload()).status_code == 503
    monkeypatch.setenv('CI_STATUS_TOKEN','unit-test-token')
    for header in ['', 'Bearer wrong', 'Bearer non-ascii-\u00e9']:
        assert client.post('/api/ci/v1/status', json=payload(), headers={'Authorization':header}).status_code == 401
    headers = {'Authorization':'Bearer unit-test-token'}
    monkeypatch.setenv('CI_ALLOWED_REPOSITORIES','other/repo')
    assert client.post('/api/ci/v1/status', json=payload(), headers=headers).status_code == 403
    monkeypatch.setenv('CI_ALLOWED_REPOSITORIES','test/repo')
    for body in [None, [], {}, 'not-json']:
        assert client.post('/api/ci/v1/status', json=body, headers=headers).status_code in (400,415)
    assert client.post('/api/ci/v1/status', data='x'*16385, content_type='application/json', headers=headers).status_code == 413
    assert client.get('/api/ci/v1/receipts/'+str(uuid.uuid4())+'?repository=other/repo', headers=headers).status_code == 403


def test_database_connection_failure_is_safe(monkeypatch):
    def fail(): raise psycopg.OperationalError('private connection details')
    monkeypatch.setenv('CI_STATUS_TOKEN','unit-test-token')
    monkeypatch.setenv('CI_ALLOWED_REPOSITORIES','test/repo')
    response = app_for(fail).test_client().post('/api/ci/v1/status', json=payload(), headers={'Authorization':'Bearer unit-test-token'})
    assert response.status_code == 503 and response.json['persisted'] is False
    assert 'private' not in response.get_data(as_text=True)


@pytest.fixture
def db(monkeypatch, request, tmp_path):
    if os.getenv('AI_TEST_DATABASE') != '1': pytest.skip('Isolated PostgreSQL integration opt-in required')
    assert os.getenv('DB_NAME') == 'cloud_bytexl_ci_test'
    assert os.getenv('DB_USER') == 'cloud_bytexl_ci'
    assert os.getenv('DB_HOST') == '127.0.0.1'
    schema = 'ci_test_' + uuid.uuid4().hex
    token = secrets.token_urlsafe(32)
    with get_db_connection() as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    def connect():
        conn = get_db_connection()
        conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        return conn
    try:
        with connect() as connection:
            # Minimal contract of the pre-existing deployment schema; no real
            # project/deployment rows or production migrations are touched.
            connection.execute('CREATE TABLE repositories(id bigint PRIMARY KEY,url text NOT NULL)')
            connection.execute('''CREATE TABLE deployments(id bigint PRIMARY KEY,
                repository_id bigint REFERENCES repositories(id),commit_id text,
                status text NOT NULL,completed_at timestamptz)''')
            connection.execute("INSERT INTO repositories VALUES(1,'https://github.com/test/repo')")
            connection.execute("INSERT INTO deployments VALUES(11,1,%s,'RECEIVED',NULL),(12,1,%s,'RECEIVED',NULL)", ('a'*40,'b'*40))
        if getattr(request, 'param', None) == 'pre005':
            # Run the unchanged migration loader against the original four SQL
            # files, reproducing a pre-005 database without touching a real one.
            backend = Path(__file__).resolve().parents[1]
            legacy = tmp_path/'backend'
            (legacy/'ai_intelligence').mkdir(parents=True)
            (legacy/'migrations').mkdir()
            loader = legacy/'ai_intelligence'/'migrations.py'
            shutil.copyfile(backend/'ai_intelligence'/'migrations.py', loader)
            for path in sorted((backend/'migrations').glob('00[1-4]_*.sql')):
                shutil.copyfile(path, legacy/'migrations'/path.name)
            runpy.run_path(str(loader))['migrate'](connect)
        else:
            migrate(connect); migrate(connect)
            register_execution(connect, 'test/repo', 21, 1, 'a'*40, 11)
        monkeypatch.setenv('CI_STATUS_TOKEN',token)
        monkeypatch.setenv('CI_ALLOWED_REPOSITORIES','test/repo')
        yield SimpleNamespace(connect=connect, schema=schema, token=token,
                              app=app_for(connect), headers={'Authorization':'Bearer '+token})
    finally:
        with get_db_connection() as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def post(db, body):
    return db.app.test_client().post('/api/ci/v1/status', json=body, headers=db.headers)


def readback(db):
    with db.connect() as connection:
        return (connection.execute('SELECT count(*) FROM ci_callback_receipts').fetchone()[0],
                connection.execute('SELECT id,status FROM deployments ORDER BY id').fetchall())


@pytest.mark.parametrize('db', ['pre005'], indirect=True)
def test_005_upgrades_populated_existing_database_without_data_loss(db):
    model_id = uuid.uuid4()
    with db.connect() as connection:
        assert connection.execute('SELECT count(*) FROM ai_schema_migrations').fetchone()[0] == 4
        connection.execute('''INSERT INTO ai_runs(repository,run_id,attempt,workflow_id,
            commit_sha,created_at,status,conclusion,payload) VALUES
            ('test/repo',21,1,9,%s,now(),'completed','success','{"preserved":true}')''', ('a'*40,))
        connection.execute('''INSERT INTO ai_models(version,repository,status,metrics,feature_names)
            VALUES(%s,'test/repo','insufficient_data','{"preserved":true}','[]')''', (model_id,))
        before_runs = connection.execute('SELECT * FROM ai_runs').fetchall()
        before_models = connection.execute('SELECT * FROM ai_models').fetchall()
        before_deployments = connection.execute('SELECT * FROM deployments ORDER BY id').fetchall()
        before_checksums = connection.execute('SELECT name,checksum FROM ai_schema_migrations ORDER BY name').fetchall()
    migrate(db.connect); migrate(db.connect)
    with db.connect() as connection:
        assert connection.execute('SELECT count(*) FROM ai_schema_migrations').fetchone()[0] == 5
        assert connection.execute('SELECT * FROM ai_runs').fetchall() == before_runs
        assert connection.execute('SELECT * FROM ai_models').fetchall() == before_models
        assert connection.execute('SELECT * FROM deployments ORDER BY id').fetchall() == before_deployments
        assert connection.execute('SELECT name,checksum FROM ai_schema_migrations ORDER BY name LIMIT 4').fetchall() == before_checksums
    register_execution(db.connect, 'test/repo', 21, 1, 'a'*40, 11)
    assert post(db, payload()).status_code == 200
    assert readback(db) == (1,[(11,'SUCCESS'),(12,'RECEIVED')])


def test_atomic_persistence_duplicate_and_latest_untouched(db):
    body = payload()
    first = post(db,body)
    assert first.status_code == 200 and first.json['persisted'] is True
    assert first.json['deployment_id'] == 11 and not first.json['duplicate']
    duplicate = post(db,body)
    assert duplicate.status_code == 200 and duplicate.json['duplicate']
    assert duplicate.json['receipt_id'] == first.json['receipt_id']
    assert readback(db) == (1,[(11,'SUCCESS'),(12,'RECEIVED')])
    # A fresh Flask instance reads the persisted receipt, not in-memory state.
    response = app_for(db.connect).test_client().get('/api/ci/v1/receipts/'+first.json['receipt_id']+'?repository=test/repo',headers=db.headers)
    assert response.status_code == 200 and response.json['persisted'] is True


@pytest.mark.parametrize('change,code', [
    ({'run_id':22},'execution_not_found'),
    ({'commit_sha':'b'*40},'association_mismatch'),
    ({'attempt':2},'unregistered_attempt'),
])
def test_wrong_execution_has_no_effect(db,change,code):
    response = post(db,{**payload(),**change})
    assert response.status_code in (404,409) and response.json['code'] == code
    assert readback(db) == (0,[(11,'RECEIVED'),(12,'RECEIVED')])


def test_receipt_conflicts_and_stale_attempts(db):
    first = payload(); assert post(db,first).status_code == 200
    assert post(db,{**first,'status':'FAILURE'}).json['code'] == 'delivery_conflict'
    assert post(db,payload()).json['code'] == 'attempt_conflict'
    register_execution(db.connect,'test/repo',21,2,'a'*40,11)
    stale = post(db,payload())
    assert stale.status_code == 409 and stale.json['code'] == 'stale_attempt'
    second = {**payload(),'attempt':2,'status':'FAILURE','tests':'FAILED'}
    assert post(db,second).status_code == 200
    # A genuine replay acknowledges its original receipt without reverting state.
    assert post(db,first).json['duplicate'] is True
    assert readback(db) == (2,[(11,'FAILED'),(12,'RECEIVED')])
    with pytest.raises(CallbackError): register_execution(db.connect,'test/repo',21,1,'a'*40,11)
    with pytest.raises(CallbackError): register_execution(db.connect,'test/repo',21,3,'b'*40,12)


def test_concurrent_duplicate_deliveries(db):
    body = payload()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        responses = list(executor.map(lambda _:post(db,body), range(6)))
    assert all(r.status_code == 200 for r in responses)
    assert len({r.json['receipt_id'] for r in responses}) == 1
    assert sum(not r.json['duplicate'] for r in responses) == 1
    assert readback(db) == (1,[(11,'SUCCESS'),(12,'RECEIVED')])


def test_concurrent_conflicting_terminal_deliveries(db):
    bodies = [payload(), {**payload(),'status':'FAILURE','tests':'FAILED'}]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda body:post(db,body), bodies))
    assert sorted(r.status_code for r in responses) == [200,409]
    assert readback(db)[0] == 1


def test_concurrent_reuse_of_delivery_id_with_changed_payload(db):
    first = payload()
    second = {**first, 'status':'FAILURE', 'tests':'FAILED'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda body:post(db,body), [first, second]))
    assert sorted(r.status_code for r in responses) == [200,409]
    assert next(r for r in responses if r.status_code == 409).json['code'] == 'delivery_conflict'
    assert readback(db)[0] == 1


def test_registration_rejects_wrong_deployment_repository_or_commit(db):
    with pytest.raises(CallbackError): register_execution(db.connect,'test/repo',99,1,'a'*40,999)
    with pytest.raises(CallbackError): register_execution(db.connect,'other/repo',99,1,'a'*40,11)
    with pytest.raises(CallbackError): register_execution(db.connect,'test/repo',99,1,'b'*40,11)
    with db.connect() as connection:
        assert connection.execute('SELECT count(*) FROM ci_callback_executions').fetchone()[0] == 1
    assert readback(db) == (0,[(11,'RECEIVED'),(12,'RECEIVED')])


def test_deleted_deployment_is_not_replaced_by_latest(db):
    with db.connect() as connection:
        connection.execute('DELETE FROM deployments WHERE id=11')
    response = post(db,payload())
    assert response.status_code == 404 and response.json['code'] == 'deployment_not_found'
    assert readback(db) == (0,[(12,'RECEIVED')])


def test_unauthorized_delivery_has_no_database_effect(db,monkeypatch):
    body = payload()
    client = db.app.test_client()
    assert client.post('/api/ci/v1/status', json=body).status_code == 401
    monkeypatch.setenv('CI_ALLOWED_REPOSITORIES','other/repo')
    assert post(db,body).status_code == 403
    assert readback(db) == (0,[(11,'RECEIVED'),(12,'RECEIVED')])


def test_transaction_failure_rolls_back_deployment_and_receipt(db):
    with db.connect() as connection:
        connection.execute('''CREATE FUNCTION reject_receipt() RETURNS trigger LANGUAGE plpgsql AS
            $$ BEGIN RAISE EXCEPTION 'private database diagnostic'; END $$''')
        connection.execute('''CREATE TRIGGER reject_receipt BEFORE INSERT ON ci_callback_receipts
            FOR EACH ROW EXECUTE FUNCTION reject_receipt()''')
    response = post(db,payload())
    assert response.status_code == 503 and response.json['persisted'] is False
    assert 'private' not in response.get_data(as_text=True)
    assert readback(db) == (0,[(11,'RECEIVED'),(12,'RECEIVED')])


def test_commit_time_failure_never_acknowledges(db):
    with db.connect() as connection:
        connection.execute('''CREATE FUNCTION reject_commit() RETURNS trigger LANGUAGE plpgsql AS
            $$ BEGIN RAISE EXCEPTION 'private commit diagnostic'; END $$''')
        connection.execute('''CREATE CONSTRAINT TRIGGER reject_commit AFTER INSERT ON ci_callback_receipts
            DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION reject_commit()''')
    response = post(db,payload())
    assert response.status_code == 503 and response.json['persisted'] is False
    assert readback(db) == (0,[(11,'RECEIVED'),(12,'RECEIVED')])


@contextlib.contextmanager
def running_flask(env):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable,'-c',
        "from backend.app import app; import os; app.run(host='127.0.0.1',port=int(os.environ['CI_TEST_PORT']),use_reloader=False)"],
        env={**env,'CI_TEST_PORT':str(port)},cwd=Path(__file__).resolve().parents[2],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic()+30
        while time.monotonic()<deadline:
            if process.poll() is not None: raise AssertionError('Isolated Flask failed to start')
            try:
                conn = http.client.HTTPConnection('127.0.0.1',port,timeout=1)
                conn.request('GET','/'); response = conn.getresponse(); response.read(); conn.close()
                if response.status == 200: break
            except OSError: pass
            time.sleep(.1)
        else: raise AssertionError('Isolated Flask startup timeout')
        yield port
    finally:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)


def test_real_sender_http_database_readback_and_process_restart(db):
    env = {**os.environ,'PGOPTIONS':'-c search_path='+db.schema,
        'CI_CALLBACK_ENABLED':'1','CI_CALLBACK_TEST_LOOPBACK':'1',
        'PYTHON_DOTENV_DISABLED':'1','FLASK_DEBUG':'0','RCA_PROVIDER':'none','OPENAI_API_KEY':'',
        'GEMINI_API_KEY':'','GITHUB_TOKEN':'','GITHUB_REPOSITORY':'test/repo',
        'GITHUB_RUN_ID':'21','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40,
        'GITHUB_WORKFLOW':'CI','PIPELINE_STATUS':'success','SYNTAX_OUTCOME':'success',
        'TEST_OUTCOME':'success','DOCKER_OUTCOME':'success'}
    sender = [sys.executable,'-m','backend.tools.ci_callback']
    with running_flask(env) as port:
        result = subprocess.run(sender,env={**env,'CI_STATUS_URL':f'http://127.0.0.1:{port}/api/ci/v1/status'},
            text=True,capture_output=True,timeout=30,cwd=Path(__file__).resolve().parents[2])
        assert result.returncode == 0, 'Sender did not confirm durable persistence'
        assert 'persistence acknowledged' in result.stdout
        assert db.token not in result.stdout+result.stderr
        assert readback(db) == (1,[(11,'SUCCESS'),(12,'RECEIVED')])
        with db.connect() as connection:
            receipt_id = str(connection.execute('SELECT id FROM ci_callback_receipts').fetchone()[0])
    with running_flask(env) as port:
        conn = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
        conn.request('GET','/api/ci/v1/receipts/'+receipt_id+'?repository=test/repo',headers=db.headers)
        response = conn.getresponse(); receipt = json.loads(response.read()); conn.close()
        assert response.status == 200 and receipt['persisted'] is True
        assert receipt['receipt_id'] == receipt_id and receipt['deployment_id'] == 11
        # Replay the actual sender after a new process starts: same receipt/row.
        replay = subprocess.run(sender,env={**env,'CI_STATUS_URL':f'http://127.0.0.1:{port}/api/ci/v1/status'},
            text=True,capture_output=True,timeout=30,cwd=Path(__file__).resolve().parents[2])
        assert replay.returncode == 0
        assert readback(db) == (1,[(11,'SUCCESS'),(12,'RECEIVED')])
        count, deployments = readback(db)
        print('DURABLE_CALLBACK_EVIDENCE '+json.dumps(dict(
            receipt_count_after_restart_and_replay=count,
            deployment_rows=deployments, receipt_id_survived_restart=receipt['receipt_id']==receipt_id,
            persisted_acknowledged=receipt['persisted'], sender_exit=result.returncode,
            replay_sender_exit=replay.returncode)))
