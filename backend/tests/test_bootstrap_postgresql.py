"""Only brand-new disposable databases inside the explicitly opted-in CI cluster."""
import os,uuid,secrets
import pytest,psycopg
from psycopg import sql
from backend.app import DB_CONFIG
from backend.bootstrap import bootstrap,create_reader

@pytest.fixture
def empty_database():
    if os.getenv('AI_TEST_DATABASE')!='1':pytest.skip('Disposable PostgreSQL bootstrap tests require explicit CI opt-in')
    assert os.environ['DB_NAME']=='cloud_bytexl_ci_test' and os.environ['DB_HOST']=='127.0.0.1'
    name='cloud_bytexl_bootstrap_test_'+uuid.uuid4().hex
    with psycopg.connect(**DB_CONFIG,autocommit=True) as conn:conn.execute(sql.SQL('create database {}').format(sql.Identifier(name)))
    cfg={**DB_CONFIG,'dbname':name}
    try:yield name,lambda:psycopg.connect(**cfg)
    finally:
        with psycopg.connect(**DB_CONFIG,autocommit=True) as conn:conn.execute(sql.SQL('drop database {}').format(sql.Identifier(name)))

def test_fresh_bootstrap_repeatability_and_real_repository_persistence(empty_database,monkeypatch):
    name,factory=empty_database
    assert bootstrap(factory,name)['records_imported']==0
    bootstrap(factory,name)
    with factory() as conn:
        assert conn.execute('select count(*) from ai_schema_migrations').fetchone()[0]==5
        assert conn.execute('select count(*) from users').fetchone()[0]==0
    import importlib
    module=importlib.import_module('backend.app');monkeypatch.setattr(module,'get_db_connection',factory)
    repo={'name':'controlled-bootstrap-fixture','url':'https://github.com/fixture/bootstrap','branch':'main'}
    a=module.save_github_repository(repo);b=module.save_github_repository(repo);assert a==b
    with factory() as conn:assert conn.execute('select count(*) from repositories').fetchone()[0]==1

def test_existing_database_and_wrong_identity_are_not_modified(empty_database):
    name,factory=empty_database
    with pytest.raises(ValueError,match='identity'):bootstrap(factory,'incorrect_database')
    with factory() as c:c.execute('create table sentinel(id integer)');c.execute('insert into sentinel values(42)')
    with pytest.raises(ValueError,match='empty public schema'):bootstrap(factory,name)
    with factory() as c:
        assert c.execute('select * from sentinel').fetchall()==[(42,)]
        assert c.execute("select to_regclass('public.ai_runs')").fetchone()[0] is None

def test_bootstrap_checksum_mismatch_rejected(empty_database):
    name,factory=empty_database;bootstrap(factory,name)
    with factory() as c:c.execute("update cloud_bytexl_bootstrap set checksum='tampered'")
    with pytest.raises(ValueError,match='checksum'):bootstrap(factory,name)

def test_reader_role_can_read_but_cannot_insert(empty_database):
    name,factory=empty_database;bootstrap(factory,name)
    role='cloud_bytexl_public_'+uuid.uuid4().hex;password=secrets.token_urlsafe(32)
    try:
        create_reader(factory,name,role,password)
        cfg={**DB_CONFIG,'dbname':name,'user':role,'password':password}
        with psycopg.connect(**cfg) as c:
            assert c.execute('show transaction_read_only').fetchone()[0]=='on'
            assert c.execute('select count(*) from ai_runs').fetchone()[0]==0
            assert not c.execute("select has_table_privilege(current_user,'repositories','INSERT')").fetchone()[0]
        from flask import Flask
        from backend.hosting import register_public_demo
        app=Flask(__name__)
        register_public_demo(app,lambda:psycopg.connect(**cfg),{'fixture/bootstrap'})
        assert app.test_client().get('/readyz').status_code==200
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            with psycopg.connect(**cfg) as c:c.execute("insert into users(username,email) values('fixture','fixture@example.invalid')")
    finally:
        with factory() as c:
            c.execute(sql.SQL('drop owned by {}').format(sql.Identifier(role)))
        with psycopg.connect(**DB_CONFIG,autocommit=True) as c:c.execute(sql.SQL('drop role {}').format(sql.Identifier(role)))

def test_failed_AI_migration_rolls_back_entire_bootstrap(empty_database,monkeypatch):
    name,factory=empty_database
    def fail(_):raise RuntimeError('controlled migration failure')
    monkeypatch.setattr('backend.bootstrap.migrate',fail)
    with pytest.raises(RuntimeError):bootstrap(factory,name)
    with factory() as c:
        assert c.execute("select tablename from pg_tables where schemaname='public'").fetchall()==[]
