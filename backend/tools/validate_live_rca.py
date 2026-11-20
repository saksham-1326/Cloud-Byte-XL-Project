"""RCA-only historical validation checkpoint; never trains or predicts.

Run from the project root with backend/venv/Scripts/python.exe -m
backend.tools.validate_live_rca. Missing provider settings are recorded as a
blocker, never represented as successful live inference or verification.
"""
import hashlib
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from backend.app import get_db_connection
from backend.ai_intelligence.rca import configured_provider, provider_configuration, analyze, extract_evidence, INSTRUCTIONS, PROVIDER_SCHEMA
from backend.ai_intelligence.github import scrub
from backend.ai_intelligence.store import Store


REPOSITORY = 'saksham-1326/cloud-byte-xl-project'


class AuditedProvider:
    def __init__(self,provider):
        self.provider=provider
        self.calls = []

    def generate(self, evidence, anchor):
        call = {'model': os.environ['RCA_MODEL'], 'status': 'attempted',
                'input_sha256': hashlib.sha256(json.dumps(
                    {'evidence': scrub(evidence)}, ensure_ascii=False).encode()).hexdigest(),
                'instructions_sha256':hashlib.sha256(INSTRUCTIONS.encode()).hexdigest(),
                'schema_sha256':hashlib.sha256(json.dumps(PROVIDER_SCHEMA,sort_keys=True).encode()).hexdigest(),
                'prompt_version':'rca-facts-v2'}
        self.calls.append(call)
        try:
            result = self.provider.generate(evidence, anchor)
        except Exception as error:
            call['status'] = 'failed'
            call['error_code']=getattr(error,'code','provider_error')
            call['error_details']=getattr(error,'details',{})
            call['metadata']=getattr(self.provider,'last_metadata',{})
            raise
        call.update(status='completed', diagnosis=scrub(result),metadata=getattr(self.provider,'last_metadata',{}))
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume',action='store_true',help='Continue the same model checkpoint without repeating tested cases.')
    parser.add_argument('--output-name',default='live_rca_validation.json',help='Report filename inside backend/reports.')
    parser.add_argument('--run-numbers',type=int,nargs='+',help='Only these historical run numbers, in the specified order.')
    args=parser.parse_args()
    if Path(args.output_name).name!=args.output_name:raise ValueError('Use a report filename without directory components.')
    output = Path(__file__).resolve().parents[1] / 'reports' / args.output_name
    if output.exists() and not args.resume:
        backup=output.with_name(output.stem+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
        backup.write_bytes(output.read_bytes())
    store = Store(get_db_connection)
    configuration=provider_configuration()
    missing=configuration['missing'][:]
    if configuration['provider']=='none':missing.append('RCA_PROVIDER must select an LLM')
    provider = None if missing else AuditedProvider(configured_provider())
    checkpoint = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'repository': REPOSITORY, 'status': 'blocked' if missing else 'review_required',
        'missing_configuration': missing, 'actual_llm_calls': 0,
        'model': os.getenv('RCA_MODEL') or None, 'provider':configuration['provider'],'cases': [],
        'limitations': ['Cached real GitHub logs; no fresh GitHub download in this validation.',
                        'Semantic cause, fix, and unsupported-claim review must be completed after live inference.',
                        'No ML prediction verification performed.'],
    }
    if args.resume:
        if missing or provider is None:
            raise ValueError('Resume requires a configured provider.')
        previous=json.loads(output.read_text(encoding='utf-8'))
        if previous['model']!=checkpoint['model'] or previous['provider']!=checkpoint['provider']:
            raise ValueError('Resume requires the same configured provider and model.')
        current_hash=hashlib.sha256(INSTRUCTIONS.encode()).hexdigest()
        if any(call.get('instructions_sha256')!=current_hash for call in previous.get('calls',[])):
            raise ValueError('Resume cannot mix responses from different prompt versions.')
        if previous.get('calls') and previous['calls'][-1]['status']=='failed':
            raise ValueError('Provider failure cannot be automatically resumed. Resolve access/quota first.')
        checkpoint['cases']=previous['cases']
        checkpoint['model_access']=previous.get('model_access')
        checkpoint['resumed_at']=checkpoint['created_at']
        checkpoint['created_at']=previous['created_at']
        provider.calls=previous.get('calls',[])
    if provider and not args.resume and hasattr(provider.provider,'check_model'):
        try:
            checkpoint['model_access']=provider.provider.check_model()
        except Exception as error:
            checkpoint['model_access']={'error_code':getattr(error,'code','provider_error'),'message':str(error),
                                        'details':getattr(error,'details',{})}
            missing.append('Gemini model-access check failed')
            checkpoint['status']='blocked'
    runs = [run for run in store.runs(REPOSITORY) if run['conclusion'] == 'failure']
    # Run #21 MUST be the first actual provider invocation.
    runs.sort(key=lambda run: (run['run_id'] != 32446985157, run['created_at']))
    if args.run_numbers:
        runs=[run for run in runs if run['payload'].get('run_number') in args.run_numbers]
        runs.sort(key=lambda run:args.run_numbers.index(run['payload']['run_number']))
        missing_runs=set(args.run_numbers)-{run['payload']['run_number'] for run in runs}
        if missing_runs:raise ValueError('Requested historical failed runs are not all synchronized.')
    checkpoint['candidate_runs']=[{'run_number':run['payload'].get('run_number'),'run_id':run['run_id'],
                                   'attempt':run['attempt']} for run in runs]
    for run in runs:
        if any(case['run_id']==run['run_id'] and case['attempt']==run['attempt'] for case in checkpoint['cases']):
            continue
        jobs = store.jobs(REPOSITORY, run['run_id'], run['attempt'])
        workflow=run['payload'].get('name')
        evidence = extract_evidence(jobs,workflow=workflow)
        case = {'run_number': run['payload'].get('run_number'),
                'run_id': run['run_id'], 'attempt': run['attempt'],
                'log_statuses': [job['log_status'] for job in jobs],
                'input_evidence':evidence,
                'verification_outcome': 'blocked_missing_provider' if missing else 'review_required',
                'review_criteria': {key: None for key in
                                    ('step_correct', 'primary_cause_correct', 'evidence_correct',
                                     'fix_correct', 'unsupported_claims')}}
        if not evidence['primary']:
            case['verification_outcome'] = 'insufficient_logs'
        try:
            report = analyze(jobs, provider if not missing else None,workflow=workflow)
        except Exception as error:
            # Preserve raw structured provider output for review even if the local
            # schema/anchor guard rejects it. Never relabel that as accepted RCA.
            case.update(verification_outcome='provider_or_validation_failed', error_type=type(error).__name__,
                        error_code=getattr(error,'code','validation'),message=str(error),
                        provider_call=provider.calls[-1] if provider and provider.calls else None)
            # A rule baseline holds the failed-attempt audit, never disguising it
            # as accepted AI output. Raw structured model output stays in the audit.
            report=analyze(jobs,workflow=workflow)
            report.update(run_id=run['run_id'],attempt=run['attempt'],live_validation=scrub(case.copy()))
            case['report_id']=store.save_report(REPOSITORY,run['run_id'],run['attempt'],report)
            checkpoint['cases'].append(case)
            checkpoint['status'] = 'blocked' if getattr(error,'code',None) else 'incomplete'
            saved=store.query('SELECT report FROM ai_rca_reports WHERE id=%s',(case['report_id'],),True)
            assert saved['report']['live_validation']==report['live_validation']
            if getattr(error,'code',None):break  # No retry after provider/quota errors.
            # A completed but rejected diagnosis is itself a validation outcome.
            # Preserve it and test different runs without coaching or retrying it.
            continue
        report.update(run_id=run['run_id'], attempt=run['attempt'],
                      workflow=run['payload'].get('name'), live_validation=case.copy())
        if provider and evidence['primary']:
            report['provider_metadata']=provider.calls[-1].get('metadata',{})
        case['report_id'] = store.save_report(REPOSITORY, run['run_id'], run['attempt'], report)
        case['report'] = report
        checkpoint['cases'].append(case)
        # Verify the saved checkpoint is readable without changing review status.
        saved = store.query('SELECT report FROM ai_rca_reports WHERE id=%s', (case['report_id'],), True)
        assert saved['report']['live_validation'] == report['live_validation']
    checkpoint['calls'] = provider.calls if provider else []
    checkpoint['actual_llm_calls'] = len(checkpoint['calls'])
    checkpoint['successful_live_calls']=sum(call['status']=='completed' for call in checkpoint['calls'])
    checkpoint['successful_generation_http_responses']=sum(
        call['status']=='completed' or call.get('metadata',{}).get('http_response_received',False)
        for call in checkpoint['calls'])
    checkpoint['accuracy']=None
    output.write_text(json.dumps(checkpoint, indent=2, default=str), encoding='utf-8')
    print(json.dumps({key: checkpoint[key] for key in
                      ('status', 'missing_configuration', 'actual_llm_calls', 'model')}, indent=2))
    saved_count=sum('report_id' in case for case in checkpoint['cases'])
    print(f'Persisted {saved_count} case checkpoints; report: {output}')


if __name__ == '__main__':
    main()
