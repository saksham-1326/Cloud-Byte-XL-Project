"""Explicit opt-in observer. --dry-run never opens a socket or writes a ledger.

No .env loading, Flask listener, workflow triggers, provider calls or training.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import threading
import uuid
from datetime import timedelta

import psycopg
from psycopg.conninfo import conninfo_to_dict

from backend.ai_intelligence.github import repository_name
from backend.ai_intelligence.observation import Ledger, ObservationError, digest, positive, aware, utc
from backend.ai_intelligence.observer import Observer
from backend.ai_intelligence.observer_client import ObserverClient
from backend.ai_intelligence.store import Store


def database_settings(dsn):
    try:
        fields=conninfo_to_dict(dsn)
    except Exception:
        raise ObservationError('invalid_observation_database_configuration') from None
    if (set(fields)-{'host','port','dbname','user','password','sslmode'}
        or fields.get('host') not in ('127.0.0.1','::1','localhost')
        or not fields.get('port','').isdigit() or not 1<=int(fields['port'])<=65535
        or not fields.get('dbname','').startswith('cloud_bytexl_observation_')
        or not fields.get('user','').startswith('cloud_bytexl_observer_')
        or not fields.get('password')):
        raise ObservationError('explicit_dedicated_loopback_database_required')
    return fields


def connection_factory(fields, readonly=False):
    def connect():
        # Explicit hostaddr prevents inherited PGHOSTADDR/service configuration
        # from routing an apparently loopback DSN to a different network host.
        address='127.0.0.1' if fields['host']=='localhost' else fields['host']
        conn=psycopg.connect(**fields,hostaddr=address,connect_timeout=5,
            options='-c statement_timeout=10000 -c lock_timeout=5000'+
                    (' -c default_transaction_read_only=on' if readonly else ''))
        try:
            actual=conn.execute('SELECT current_database(),current_user,pg_is_in_recovery()').fetchone()
            if actual!=(fields['dbname'],fields['user'],False):
                raise ObservationError('unexpected_database_identity')
            if readonly and conn.execute('SHOW transaction_read_only').fetchone()[0]!='on':
                raise ObservationError('reader_not_readonly')
            return conn
        except Exception:
            conn.close()
            raise
    return connect


def clock_reference(path, bound, duration):
    """Validate operator-supplied clock evidence; never invent a measured bound."""
    if bound is None:
        return None
    try:
        raw=Path(path).read_bytes()
        data=json.loads(raw)
        measured,expires=aware(data['measured_at']),aware(data['valid_until'])
        observed_bound=positive(data['max_error_seconds'],'clock_evidence_bound',0)
        if (not isinstance(data['method'],str) or not data['method'].strip()
            or measured>utc() or expires<utc()+timedelta(seconds=duration)
            or bound<observed_bound):
            raise ValueError()
        return dict(reference_sha256=hashlib.sha256(raw).hexdigest(),
                    measured_at=measured.isoformat(),valid_until=expires.isoformat(),
                    max_error_seconds=observed_bound,method=data['method'])
    except Exception:
        raise ObservationError('clock_evidence_missing_stale_or_inconsistent') from None


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true')
    mode.add_argument('--run',action='store_true')
    p.add_argument('--repository',required=True)
    p.add_argument('--allow-repository',action='append',required=True)
    p.add_argument('--model-version',required=True)
    p.add_argument('--model-sha256',required=True)
    p.add_argument('--ledger',type=Path,default=Path('backend/reports/observations/session.jsonl'))
    p.add_argument('--interval',type=float,default=15)
    p.add_argument('--duration-seconds',type=float,default=900)
    p.add_argument('--max-requests',type=int,default=300)
    p.add_argument('--max-polls',type=int,default=60)
    p.add_argument('--clock-uncertainty-seconds',type=float)
    p.add_argument('--clock-evidence-ref')
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        repo=repository_name(args.repository)
        allowed={repository_name(v) for v in args.allow_repository}
        if repo not in allowed:
            raise ObservationError('repository_not_allowlisted')
        version=str(uuid.UUID(args.model_version))
        if not re.fullmatch(r'[a-f0-9]{64}',args.model_sha256):
            raise ObservationError('invalid_model_digest')
        positive(args.interval,'poll_interval',5)
        positive(args.duration_seconds,'duration')
        positive(args.max_requests,'request_budget')
        positive(args.max_polls,'poll_count')
        if args.clock_uncertainty_seconds is not None:
            positive(args.clock_uncertainty_seconds,'clock_uncertainty',0)
            if not args.clock_evidence_ref:
                raise ObservationError('clock_evidence_reference_required')
        clock=clock_reference(args.clock_evidence_ref,args.clock_uncertainty_seconds,args.duration_seconds)
        if not args.ledger.resolve().is_relative_to((Path.cwd()/'backend/reports/observations').resolve()):
            raise ObservationError('ledger_must_be_in_ignored_observation_directory')
        writer=database_settings(os.environ.get('OBSERVER_WRITER_DSN',''))
        reader=database_settings(os.environ.get('OBSERVER_READER_DSN',''))
        if ([(writer[k],reader[k]) for k in ('host','port','dbname') if writer[k]!=reader[k]]
            or writer['user']==reader['user']):
            raise ObservationError('separate_roles_same_database_required')
        token=os.environ.get('GITHUB_TOKEN','')
        if not token.strip():
            raise ObservationError('github_authentication_required')
        if args.dry_run:
            print(json.dumps(dict(mode='offline_configuration_dry_run',valid=True,
                network_access=False,database_access=False,prediction_submitted=False,
                limitation='Permissions, model registry, artifact and clock evidence are not verified.')))
            return 0
        stop=threading.Event()
        previous={}
        for sig in (signal.SIGINT,signal.SIGTERM):
            previous[sig]=signal.signal(sig,lambda *_:stop.set())
        try:
            secrets=(token,writer['password'],reader['password'],os.environ['OBSERVER_WRITER_DSN'],
                     os.environ['OBSERVER_READER_DSN'])
            with Ledger(args.ledger,secrets=secrets) as ledger:
                client=ObserverClient(repo,token,ledger,budget=args.max_requests,
                                      duration=args.duration_seconds,stop=stop)
                observer=Observer(repo,allowed,Store(connection_factory(writer)),
                    Store(connection_factory(reader,readonly=True)),client,ledger,version,args.model_sha256,
                    interval=args.interval,max_polls=args.max_polls,
                    clock_uncertainty=args.clock_uncertainty_seconds,clock_evidence=clock,
                    database_ref=digest({k:writer[k] for k in ('host','port','dbname','user')} |
                                        {'reader_user':reader['user']}))
                result=observer.run()
                print(json.dumps(result))
                return 0 if result['reason'] in ('poll_limit_reached','duration_exhausted','request_budget_exhausted','cancelled') else 1
        finally:
            for sig,handler in previous.items():
                signal.signal(sig,handler)
    except (ObservationError,ValueError,TypeError) as error:
        # ObservationError messages are fixed codes; parser/DSN exception strings
        # are never copied into terminal output or the observation ledger.
        print(json.dumps({'status':'stopped','reason':str(error) if isinstance(error,ObservationError)
                          else 'invalid_observer_configuration'}))
        return 1
    except Exception:
        print(json.dumps({'status':'stopped','reason':'local_or_database_failure'}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
