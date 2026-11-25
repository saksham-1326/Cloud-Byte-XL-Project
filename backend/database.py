"""Explicit environment configuration shared by hosted runtime and bootstrap."""
import os
import psycopg
from psycopg.conninfo import conninfo_to_dict

def configuration(env=None):
    env=os.environ if env is None else env
    if env.get('DATABASE_URL'):
        try:cfg=conninfo_to_dict(env['DATABASE_URL'])
        except Exception:raise ValueError('Invalid DATABASE_URL configuration.') from None
    else:
        cfg=dict(host=env.get('DB_HOST','localhost'),port=env.get('DB_PORT','5432'),
                 dbname=env.get('DB_NAME','bytexl'),user=env.get('DB_USER','postgres'),password=env.get('DB_PASSWORD',''))
    if env.get('DB_SSLMODE'):cfg['sslmode']=env['DB_SSLMODE']
    if not str(cfg.get('port','5432')).isdigit() or not 1<=int(cfg.get('port','5432'))<=65535:
        raise ValueError('Invalid DATABASE_URL configuration.')
    return cfg

def connect(cfg=None,readonly=False):
    args=dict(configuration() if cfg is None else cfg)
    if readonly:
        args['options']='-c default_transaction_read_only=on -c statement_timeout=15000'
    args['connect_timeout']=5
    return psycopg.connect(**args)
