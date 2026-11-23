"""Opt-in local observation orchestrator; delegates prediction to the service."""
from datetime import timedelta

from . import ml
from .collector import validate_attempt, synchronize_attempt
from .github import repository_name
from .observation import ObservationError, aware, digest, positive, utc
from .service import IntelligenceService


READBACK = """SELECT p.*,r.commit_sha,r.payload AS run_payload,
    o.label AS actual_label,o.conclusion AS actual_conclusion,
    m.artifact_sha256,m.created_at AS model_created_at,m.trained_through,
    clock_timestamp() AS database_read_at
    FROM ai_predictions p JOIN ai_runs r USING(repository,run_id,attempt)
    JOIN ai_models m ON m.version=p.model_version AND m.repository=p.repository
    LEFT JOIN ai_outcomes o ON o.repository=p.repository AND o.run_id=p.run_id AND o.attempt=p.attempt
    WHERE p.repository=%s AND p.run_id=%s AND p.attempt=%s AND p.mode='shadow'"""
ORIGINAL = ('id','repository','run_id','attempt','model_version','predicted_at',
            'feature_snapshot','probability','threshold','predicted_class','mode')


def evidence(run, jobs):
    return dict(run={k:run.get(k) for k in ('id','run_attempt','workflow_id','head_sha',
                 'status','conclusion','created_at','updated_at','run_started_at')},
                jobs=[{k:j.get(k) for k in ('id','run_id','run_attempt','head_sha','name',
                       'status','conclusion','started_at','completed_at')} for j in jobs])


class PinnedStore:
    """Delegate storage, exposing only the operator-pinned existing model."""
    def __init__(self, store, version, artifact_sha256, stop=None):
        self.store,self.version,self.artifact_sha256,self.stop=store,str(version),artifact_sha256,stop

    def __getattr__(self, key):
        return getattr(self.store,key)

    def models(self, repo):
        models=[r for r in self.store.models(repo) if str(r['version'])==self.version]
        if (len(models)!=1 or models[0].get('artifact_sha256')!=self.artifact_sha256
            or models[0]['status']!='experimental'
            or models[0]['metrics'].get('feature_version')!=ml.FEATURE_VERSION
            or not models[0].get('trained_through')):
            raise ObservationError('pinned_model_unavailable_or_incompatible')
        return models

    def predict(self, *args):
        if self.stop is not None and self.stop.is_set():
            raise ObservationError('cancelled')
        return self.store.predict(*args)


class Observer:
    def __init__(self, repo, allowlist, writer, reader, client, ledger, model_version,
                 model_digest, interval=15, max_polls=60, clock_uncertainty=None,
                 clock_evidence=None, timestamp_precision=1, now=utc,
                 session_kind='observation', database_ref='explicit-injected-connections'):
        self.repo=repository_name(repo)
        if self.repo not in {repository_name(v) for v in allowlist}:
            raise ObservationError('repository_not_allowlisted')
        if reader is writer:
            raise ObservationError('independent_reader_required')
        self.interval=positive(interval,'poll_interval',5)
        self.max_polls=int(positive(max_polls,'poll_count'))
        if clock_uncertainty is not None:
            positive(clock_uncertainty,'clock_uncertainty',0)
            if session_kind!='controlled_test' and not isinstance(clock_evidence,dict):
                raise ObservationError('validated_clock_evidence_required')
        positive(timestamp_precision,'timestamp_precision',1)
        self.now,self.reader,self.client,self.ledger=now,reader,client,ledger
        self.version,self.model_digest=str(model_version),model_digest
        self.clock_uncertainty,self.clock_evidence=clock_uncertainty,clock_evidence
        self.precision=timestamp_precision
        self.kind=session_kind
        self.writer=PinnedStore(writer,model_version,model_digest,client.stop)
        self.service=IntelligenceService(self.writer,client)
        profile=dict(protocol_version=1,repository=self.repo,model_version=self.version,model_digest=model_digest,
                     interval=interval,max_polls=max_polls,request_budget=client.budget,
                     duration=client.duration,clock_uncertainty=clock_uncertainty,
                     clock_evidence=clock_evidence,timestamp_precision=timestamp_precision,
                     session_kind=session_kind,database_ref=database_ref)
        sessions=[r for r in ledger.records if r['event']=='session']
        if sessions and sessions[0]['data']['profile_digest']!=digest(profile):
            self.service.executor.shutdown(wait=True)
            raise ObservationError('restart_configuration_mismatch')
        if not sessions:
            ledger.append('session',profile=profile,profile_digest=digest(profile))
        self.pending=set()
        self.finished=set()
        self.proofs={}
        for record in ledger.records:
            data=record['data']
            if 'run_id' not in data or 'attempt' not in data:
                continue
            key=(data['run_id'],data['attempt'])
            if record['event']=='attempt_seen':
                self.pending.add(key)
            if record['event']=='prediction_readback':
                self.proofs.setdefault(key,data)
            if record['event']=='evaluation':
                self.finished.add(key);self.pending.discard(key)

    def preflight(self):
        model=self.writer.models(self.repo)[0]
        ml.load_model(model)  # Existing integrity/path guard, not retraining.
        self.read(1,1)  # Verify the independent reader is usable before inference.

    def read(self, run_id, attempt):
        rows=self.reader.query(READBACK,(self.repo,run_id,attempt))
        if len(rows)>1:
            raise ObservationError('duplicate_shadow_readback')
        return (rows[0] if rows else None),aware(self.now())

    def event(self, name, key, **data):
        return self.ledger.append(name,repository=self.repo,run_id=key[0],attempt=key[1],**data)

    def final(self,key,decision,reason):
        self.event('evaluation',key,decision=decision,reason=reason,session_kind=self.kind,
                   human_verified=False)
        self.pending.discard(key);self.finished.add(key)

    def proof(self,key,row,seen_at,run):
        if (str(row['model_version'])!=self.version or row['artifact_sha256']!=self.model_digest
            or row['repository']!=self.repo or row['run_id']!=key[0] or row['attempt']!=key[1]
            or row['commit_sha']!=run['head_sha'] or row['mode']!='shadow'):
            raise ObservationError('prediction_identity_or_model_mismatch')
        feature=row['feature_snapshot']
        provenance=feature.get('provenance',{})
        feature_time=aware(provenance.get('prediction_time'))
        predicted=aware(row['predicted_at'])
        if (provenance.get('historical_ref')!=run['head_sha']
            or provenance.get('feature_version')!=ml.FEATURE_VERSION
            or feature_time>predicted or predicted>seen_at
            or aware(row['model_created_at'])>predicted
            or aware(row['trained_through'])>=aware(run['created_at'])
            or any(aware(r['completed_at'])>=feature_time for r in provenance.get('prior_runs',[]))):
            raise ObservationError('prediction_provenance_unverifiable')
        checksum=digest({k:row[k] for k in ORIGINAL})
        previous=self.proofs.get(key)
        if previous:
            if previous['original_sha256']!=checksum:
                raise ObservationError('prediction_fields_changed')
            return previous
        receipt=dict(prediction_id=str(row['id']),original_sha256=checksum,
                     prediction_timestamp=predicted.isoformat(),readback_completed_at=seen_at.isoformat(),
                     database_read_at=aware(row['database_read_at']).isoformat(),database_commit_at=None,
                     database_commit_note='No commit timestamp exists; independent visibility is an upper bound.',
                     model_version=self.version,model_digest=self.model_digest,
                     feature_snapshot_ref='ai_predictions:'+str(row['id']),
                     feature_snapshot_sha256=digest(feature),probability=row['probability'],
                     threshold=row['threshold'],predicted_class=row['predicted_class'],
                     persistence='independently_read_committed')
        stored=self.event('prediction_readback',key,**receipt)['data']
        self.proofs[key]=stored
        return stored

    def evaluate(self,key,row,run,jobs,receipt):
        if run['conclusion'] not in ('success','failure'):
            return self.final(key,'excluded','nonbinary_outcome')
        if row['actual_conclusion']!=run['conclusion'] or row['actual_label']!=int(run['conclusion']=='failure'):
            return self.final(key,'unverifiable','outcome_readback_mismatch')
        if self.clock_uncertainty is None or not self.clock_evidence:
            return self.final(key,'unverifiable','clock_uncertainty_not_established')
        if self.kind!='controlled_test':
            try:
                if (aware(self.clock_evidence['valid_until'])<aware(self.now())
                    or self.clock_uncertainty<self.clock_evidence['max_error_seconds']):
                    return self.final(key,'unverifiable','clock_evidence_expired')
            except (KeyError,TypeError,ObservationError):
                return self.final(key,'unverifiable','invalid_clock_evidence')
        executed=[j for j in jobs if j.get('conclusion')!='skipped']
        if not executed or any(not j.get('started_at') or not j.get('completed_at')
                               or j.get('status')!='completed' for j in executed):
            return self.final(key,'unverifiable','incomplete_job_timing')
        try:
            starts=[aware(j['started_at']) for j in executed]
            ends=[aware(j['completed_at']) for j in executed]
            margin=timedelta(seconds=self.clock_uncertainty+self.precision)
            if any(end<start for start,end in zip(starts,ends)) or max(ends)>aware(self.now())+margin:
                return self.final(key,'unverifiable','inconsistent_job_timing')
            upper=max(aware(receipt['readback_completed_at']),aware(receipt['prediction_timestamp']))
            self.event('timing_comparison',key,earliest_job_start=min(starts).isoformat(),
                       persistence_upper_bound=upper.isoformat(),margin_seconds=margin.total_seconds(),
                       clock_evidence=self.clock_evidence)
            if upper+margin>=min(starts):
                return self.final(key,'excluded','late_or_ambiguous_persistence')
        except ObservationError:
            return self.final(key,'unverifiable','invalid_job_timing')
        if row['verification_status']!='matched':
            return self.final(key,'unverifiable','store_timing_not_matched')
        self.final(key,'eligible_prestart','independent_prestart_readback_and_exact_outcome')

    def process(self,key):
        run=self.client.run(self.repo,*key)
        jobs=self.client.jobs(self.repo,*key)
        try:
            validate_attempt(self.repo,*key,run,jobs)
        except ValueError:
            return self.final(key,'excluded','github_identity_mismatch')
        self.event('github_state',key,**evidence(run,jobs))
        row,seen=self.read(*key)
        if row is None:
            if run['status']!='queued' or run.get('conclusion') is not None:
                return self.final(key,'excluded','not_queued_without_outcome')
            if any(j.get('started_at') or (j.get('status') in ('in_progress','completed')
                                          and j.get('conclusion')!='skipped') for j in jobs):
                return self.final(key,'excluded','job_already_started')
            self.event('prediction_request',key,requested_at=aware(self.now()).isoformat())
            try:
                result=self.service.predict(self.repo,*key)
                self.event('prediction_result',key,result=result,completed_at=aware(self.now()).isoformat())
            except Exception as error:
                # A post-insert error is possible; read back instead of assuming rollback.
                self.event('prediction_result',key,result='error',error_type=type(error).__name__,
                           completed_at=aware(self.now()).isoformat())
                if isinstance(error,ObservationError):
                    raise
            row,seen=self.read(*key)
            if row is None:
                if isinstance(locals().get('result'),dict) and result.get('status') in ('skipped','insufficient_data'):
                    return self.final(key,'excluded','prediction_service_'+result['status'])
                # Retry only while exact fresh state still qualifies next poll.
                self.event('prediction_missing',key,reason='no_independent_persistence_readback')
                return
        try:
            receipt=self.proof(key,row,seen,run)
        except ObservationError as error:
            return self.final(key,'unverifiable',str(error))
        if run['status']=='completed':
            result=synchronize_attempt(self.client,self.writer,self.repo,*key)
            self.event('outcome_reconciliation',key,reconciled=result['reconciled'],
                       **evidence(result['run'],result['jobs']))
            if result['reconciled']:
                after,seen=self.read(*key)
                if after is None:
                    return self.final(key,'unverifiable','outcome_prediction_missing')
                try:
                    self.proof(key,after,seen,result['run'])
                except ObservationError as error:
                    return self.final(key,'unverifiable',str(error))
                self.evaluate(key,after,result['run'],result['jobs'],receipt)

    def tick(self):
        candidates=self.client.discover()
        keys=set(self.pending)
        for run in candidates:
            try:
                run_id,attempt=run['id'],run['run_attempt']
                if type(run_id) is not int or run_id<1 or type(attempt) is not int or not 1<=attempt<=100:
                    raise ValueError()
                validate_attempt(self.repo,run_id,attempt,run,[])
                keys.add((run_id,attempt))
            except (ValueError, KeyError, TypeError):
                self.ledger.append('discovery_rejected',reason='invalid_repository_or_identity')
        for key in sorted(keys-self.finished):
            if key not in self.pending:
                self.event('attempt_seen',key)
                self.pending.add(key)
            try:
                self.process(key)
            except ObservationError:
                raise
            except Exception as error:
                # No exception message/DSN/body is exposed. Pending state survives restart.
                self.event('attempt_error',key,error_type=type(error).__name__,reason='retryable_local_failure')

    def run(self):
        reason='poll_limit_reached'
        try:
            self.client.guard()
            self.preflight()
            polls=sum(r['event']=='poll' for r in self.ledger.records)
            while polls<self.max_polls:
                self.client.guard()
                polls+=1
                self.ledger.append('poll',number=polls)
                try:
                    self.tick()
                except ObservationError as error:
                    if str(error) not in ('github_network_unavailable','github_unavailable','github_rate_limited'):
                        raise
                    self.ledger.append('poll_error',reason=str(error))
                if polls<self.max_polls:
                    self.client.pause(self.interval)
        except ObservationError as error:
            reason=str(error)
        except Exception as error:
            reason='local_or_database_failure'
            self.ledger.append('session_error',reason=reason,error_type=type(error).__name__)
        finally:
            self.service.executor.shutdown(wait=True)
            self.ledger.append('session_stopped',reason=reason,requests_reserved=self.client.requests,
                               pending_attempts=len(self.pending),session_kind=self.kind)
        return dict(reason=reason,requests_reserved=self.client.requests,pending_attempts=len(self.pending),
                    session_kind=self.kind,accuracy=None)
