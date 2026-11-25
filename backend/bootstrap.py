"""Explicit fresh-database bootstrap. Never run from a web startup command."""
import argparse,hashlib,os,re
from pathlib import Path
from contextlib import contextmanager
import psycopg
from psycopg import sql
from .database import connect
from .ai_intelligence.migrations import migrate

SCHEMA=Path(__file__).with_name('schema')/'legacy_v1.sql'
LEGACY={'users','repositories','deployments','deployment_logs','failure_analysis'}

def bootstrap(factory,expected_database):
    raw=SCHEMA.read_text(encoding='utf-8');checksum=hashlib.sha256(raw.encode()).hexdigest()
    with factory() as conn:
        actual=conn.execute('select current_database()').fetchone()[0]
        if actual!=expected_database:raise ValueError('Database identity differs from explicit confirmation.')
        conn.execute('select pg_advisory_xact_lock(73492715)')
        tables={r[0] for r in conn.execute("select tablename from pg_tables where schemaname='public'")}
        if 'cloud_bytexl_bootstrap' not in tables:
            if tables:raise ValueError('Bootstrap requires an empty public schema; existing databases are not modified.')
            conn.execute(raw)
            conn.execute('create table cloud_bytexl_bootstrap(version integer primary key,checksum text not null)')
            conn.execute('insert into cloud_bytexl_bootstrap values(1,%s)',(checksum,))
        elif conn.execute('select version,checksum from cloud_bytexl_bootstrap').fetchall()!=[(1,checksum)]:
            raise ValueError('Bootstrap checksum mismatch; no changes applied.')
        required={'users':{'id','username','email'},'repositories':{'id','user_id','name','url','branch'},
                  'deployments':{'id','repository_id','commit_id','status'},'deployment_logs':{'id','deployment_id','log_message'},
                  'failure_analysis':{'id','deployment_id','failure_type'}}
        for table,columns in required.items():
            found={r[0] for r in conn.execute("select column_name from information_schema.columns where table_schema='public' and table_name=%s",(table,))}
            if not columns<=found:raise ValueError('Required legacy schema validation failed.')
            if conn.execute("select data_type from information_schema.columns where table_schema='public' and table_name=%s and column_name='id'",(table,)).fetchone()!=('integer',):
                raise ValueError('Legacy key type validation failed.')
            if conn.execute("select count(*) from pg_constraint where conrelid=%s::regclass and contype='p'",('public.'+table,)).fetchone()[0]!=1:
                raise ValueError('Legacy primary key validation failed.')
        @contextmanager
        def borrowed():yield conn
        migrate(borrowed)
    return {'database':actual,'legacy_tables':sorted(LEGACY),'AI_migrations':5,'records_imported':0}

def create_reader(factory,expected_database,role,password):
    if not re.fullmatch(r'cloud_bytexl_public_[a-z0-9_]{1,40}',role) or not password or len(password)<24:
        raise ValueError('Reader requires a dedicated role name and a strong PUBLIC_READER_PASSWORD.')
    with factory() as c:
        if c.execute('select current_database()').fetchone()[0]!=expected_database:raise ValueError('Unexpected database identity.')
        if c.execute('select 1 from pg_roles where rolname=%s',(role,)).fetchone():raise ValueError('Reader role already exists; no credentials or privileges changed.')
        c.execute(sql.SQL('create role {} login password {} nosuperuser nocreatedb nocreaterole noreplication').format(sql.Identifier(role),sql.Literal(password)))
        c.execute(sql.SQL('grant connect on database {} to {}').format(sql.Identifier(expected_database),sql.Identifier(role)))
        c.execute(sql.SQL('grant usage on schema public to {}').format(sql.Identifier(role)))
        c.execute(sql.SQL('grant select on all tables in schema public to {}').format(sql.Identifier(role)))
        c.execute(sql.SQL('alter role {} set default_transaction_read_only=on').format(sql.Identifier(role)))

def main():
    p=argparse.ArgumentParser();p.add_argument('--confirm-database',required=True);p.add_argument('--create-reader');args=p.parse_args()
    import json
    try:
        result=bootstrap(connect,args.confirm_database)
        if args.create_reader:create_reader(connect,args.confirm_database,args.create_reader,os.environ.get('PUBLIC_READER_PASSWORD',''))
        print(json.dumps(result))
    except Exception:
        # Never print a provider URL/password or raw database exception.
        print('Bootstrap failed; verify empty target, explicit identity, schema receipts and owner privileges. No raw credentials logged.')
        raise SystemExit(1)

if __name__=='__main__':main()
