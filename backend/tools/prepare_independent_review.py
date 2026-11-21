"""Build an offline manual review package from frozen evidence proposals.

No provider, network, database, or review API calls. Existing source artifacts
are preserved; generated files are confined to reports/independent_review.
"""
import hashlib
import json
from pathlib import Path

from backend.ai_intelligence.review_metrics import calculate
from backend.tools.review_guide import write_guide


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / 'reports' / 'independent_review'
    ground = json.loads((output / 'proposed_ground_truth.json').read_text())
    proposals = {c['run_number']: c for c in ground['cases']}
    notes = {
        ('live_rca_validation.json', 21): ('reject', 'Cause and fix match, but unit_test_failure contradicts the passing pytest summary. Secondary cleanup omitted.'),
        ('live_rca_validation.json', 13): ('reject', 'Compilation failure and syntax repair are unsupported: the script includes exit 1 and no syntax diagnostic. Secondary cleanup omitted.'),
        ('live_rca_validation.json', 23): ('uncertain', 'Primary cause, category, step and diagnostic fix agree. Later callback failure omitted; parallel_failures=1 does not prove a separate concurrent job.'),
        ('live_rca_validation.json', 27): ('uncertain', 'Primary cause, category, step and diagnostic fix agree. Later callback failure omitted; PASSED strings in the posted JSON are not independent test or build results.'),
        ('rca_reliability_validation.json', 21): ('accept', 'Cause, category, step, fix and cleanup distinction agree with preserved evidence.'),
        ('rca_reliability_validation.json', 13): ('reject', 'Primary cause, category, step and fix agree. Secondary claim that cleanup step failed contradicts successful cleanup metadata; a daemon error is not a failed step. Full compiler output remains desirable.'),
        ('rca_reliability_validation.json', 23): ('accept', 'Cause, category, step, fix and subsequent callback distinction agree. Server-side origin of 404 remains unresolved.'),
        ('rca_reliability_validation.json', 27): ('accept', 'Cause, category, step, fix and subsequent callback distinction agree. Server-side origin of 404 remains unresolved.'),
    }
    lines = ['# Independent RCA review package', '',
             'Prepared 2026-11-21. All decisions below are agent suggestions pending your manual review. No human reviews were submitted.', '',
             '## Availability and independence', '',
             'Two saved validation sessions identify six distinct failed workflows (#4, #8, #13, #21, #23, #27); #4 and #8 have expired/unavailable logs. Four cases have preserved excerpts; only #21 also has a full real-log fixture. Eight Gemini response records across two sessions cover these four runs. Two additional no-log reports are rules-v1, not Gemini. The old ai_audit.json lists five failures in an earlier 27-run snapshot; it is not a current count. The user checkpoint of 21 total reports cannot be freshly verified.', '',
             'Current read-only PostgreSQL access failed with OperationalError; GitHub read failed with a connection error. Database report IDs and provenance below come from historical artifact readbacks, not a fresh database inventory. No original log availability was freshly established.', '',
             ground['independence'], '',
             '## Implementation inspected', '',
             '- github.py and collector.py collect exact run attempts, failed-job logs, redacted bounded responses and SHA workflow snapshots. Synchronize writes data and was not invoked.',
             '- rca.py selects the earliest failed non-cleanup step and bounded timestamped command context. rca_facts.py checks literal diagnostics, citations, categories and limited unsupported-claim patterns. Passing automated guards is not human verification.',
             '- GeminiProvider sends structured evidence; analyze records llm_grounded only after a completed provider response validates. evidence_rules/rules-v1 is a separate engine. Historical rejected responses can survive in provider_call artifacts.',
             '- Migrations 001 and 004 define ai_runs/jobs/steps/snapshots, append-only report IDs and distinct reviewer submissions. Store.reports limits retrieval to 100; this package does not infer database totals from that endpoint.',
             '- POST /api/ai/v1/rca/<report_id>/verify requires category_correct, step_correct, evidence_correct, fix_correct, unsupported_claims booleans plus reviewer. It upserts review and changes status; it has no primary-cause boolean or uncertain verdict. It was not called.',
             '- Existing service evaluation averages submissions by engine, not adjudicated unique reports, and omits primary-cause accuracy and rejection rate. The offline calculator supplies those with explicit per-metric sample sizes.', '',
             '## Manual workflow', '',
             'Read each evidence block before its diagnosis. Approve or correct proposed ground truth, then enter true/false/null rubric values and accept/reject/uncertain in human_worksheet.json. Keep unresolved values null. Only after personally completing a row set review_source to human and completed to true and enter your reviewer identifier. This file is not a database submission. Never send uncertain rows to the existing boolean-only verification endpoint.', '',
             'Questions: Was each exit 1 an intended failure injection? Is the limited #13 compiler context sufficient? Should earlier callback reports be rejected for omitted secondary errors? Can server logs identify the source of each 404? Do you agree that a successful cleanup step can contain a daemon error?', '']
    worksheet = []
    manifest = {}
    for number, proposal in proposals.items():
        e = proposal['evidence']
        lines += [f'## Run #{number}', '', f"Repository: {proposal['repository']}; run ID {proposal['run_id']}; attempt {proposal['attempt']}; job {e['failed_job']}; step {e['failed_step']}.", '',
                  f"Proposed cause: {proposal['proposed_cause']}", f"Category: `{proposal['proposed_category']}`. Fix: {proposal['proposed_fix']}", '', proposal['secondary_and_uncertainty'], '', 'Preserved original excerpts (IDs retain original line numbers):', '', '```text']
        lines += [f"{i['id']} {i['text']}" for i in e['primary'] + e['secondary']]
        lines += ['```', '']
        for filename in ['live_rca_validation.json', 'rca_reliability_validation.json']:
            path = root / 'reports' / filename
            manifest[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
            source = json.loads(path.read_text())
            case = next(c for c in source['cases'] if c['run_number'] == number)
            diagnosis = case.get('provider_call', {}).get('diagnosis') or case['report']
            keys = ['category', 'primary_cause', 'explanation', 'recommended_fix', 'failed_step', 'evidence_refs', 'secondary_evidence_refs', 'secondary_explanation', 'secondary_errors', 'parallel_failures']
            display = {k: diagnosis[k] for k in keys if k in diagnosis}
            refs = diagnosis.get('evidence_refs', []) + diagnosis.get('secondary_evidence_refs', [])
            available = {i['id'] for i in e['primary'] + e['secondary']}
            decision, note = notes[filename, number]
            lines += [f"### {filename}: `{case['report_id']}`", '', '```json', json.dumps(display, indent=2), '```', '',
                      f'Agent suggestion: **{decision}**. {note}', '',
                      f'Citation ID resolution: {sum(ref in available for ref in refs)}/{len(refs)} in preserved excerpts. ID resolution alone does not establish semantic support.', '']
            worksheet.append(dict(report_id=case['report_id'], run_number=number, source=filename,
                                  review_source=None, reviewer=None, completed=False,
                                  primary_cause_correct=None, category_correct=None, step_correct=None,
                                  evidence_correct=None, unsupported_claims=None, fix_correct=None,
                                  decision=None, corrected_ground_truth=None, comment=None))
    lines += ['## Metrics after manual approval', '',
              'For each metric, numerator is the number of true resolved human judgments and denominator is the number of boolean human judgments for that criterion. Unsupported-claim rate counts reports containing any unsupported claim, not individual claims. Rejection rate is reject/(accept+reject); uncertain decisions are separately counted. Duplicate report IDs require adjudication. Report early and later sessions separately to avoid hiding historical errors, and report distinct run count alongside report count.', '',
              'See metrics.json for current completed human rows, seven metric sample sizes and rates, and separate source sessions. Initially every sample size is zero and every rate is null. Eight candidate responses share only four runs, so even completed reviews cannot establish production accuracy. No scores from prior automated assessments are treated as human results.', '',
              'Recalculate locally: `python -c "import json; from backend.ai_intelligence.review_metrics import calculate; print(json.dumps(calculate(json.load(open(\'backend/reports/independent_review/human_worksheet.json\'))), indent=2))"`', '',
              'Rebuild package: `python -m backend.tools.prepare_independent_review`. Existing manual worksheet is preserved. Original responses are linked by source artifact and report ID; no response or database row is overwritten.', '']
    (output / 'REVIEW_PACKAGE.md').write_text('\n'.join(lines), encoding='utf-8')
    target = output / 'human_worksheet.json'
    if not target.exists():
        target.write_text(json.dumps(worksheet, indent=2))
    existing = json.loads(target.read_text())
    for row in existing:
        proposal = proposals[row['run_number']]
        row.setdefault('repository', proposal['repository'])
        row.setdefault('run_id', proposal['run_id'])
        row.setdefault('attempt', proposal['attempt'])
        row.setdefault('session', 'earlier' if row['source'] == 'live_rca_validation.json' else 'improved')
        row.setdefault('evidence_file', 'proposed_ground_truth.json')
        row.setdefault('evidence_limitations', proposal['secondary_and_uncertainty'])
        row.setdefault('additional_evidence_needed', None)
    target.write_text(json.dumps(existing, indent=2))
    (output / 'metrics.json').write_text(json.dumps(calculate(existing), indent=2))
    (output / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))
    write_guide(root, output, proposals, notes)


if __name__ == '__main__':
    main()
