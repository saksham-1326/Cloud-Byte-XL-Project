"""Plain-English rendering of preserved evidence and historical responses."""
import json


CONTEXT = {
    13: (
        'Check whether backend/app.py has valid Python syntax using py_compile.',
        'The displayed script runs the syntax check and then contains exit 1. The saved excerpt ends with exit code 1 and shows no syntax-error message. exit 1 tells the shell to report failure.',
        'The best supported explanation is deliberate script termination. The excerpt does not independently prove the compiler returned zero; obtain the full output if that distinction matters.',
        'Remove exit 1 only if the failure injection is no longer intended. Run the syntax check again and inspect its output. Do not change Python syntax without a real compiler diagnostic.',
        'Was exit 1 intentional, and is the saved compiler context enough to approve the proposed primary cause?'),
    21: (
        'Run the backend pytest test before building and running the Docker image.',
        'pytest reported 1 passed. The displayed script then contains exit 1, and the step ends with exit code 1. Passing tests do not make the step successful when a later command deliberately exits with failure.',
        'The pipeline failed because of explicit script termination, not a failed unit test. A later missing-container message is a cleanup issue.',
        'Remove the explicit exit 1 if unintended. Keep genuine test failures visible. Treat missing-container cleanup separately.',
        'Do you agree that the passing test summary rules out unit_test_failure as the category for this failure?'),
    23: (
        'Send a success-status message to the configured CI callback endpoint using curl --fail.',
        'The endpoint returned HTTP 404. With --fail, curl reports an HTTP error using exit code 22, so the success-notification step failed. A later failure-status notification also received 404.',
        'The observed failing operation is the callback request. The logs do not establish whether the 404 came from the tunnel, a proxy, or the application route. network_service_failure is the existing project category for this HTTP service failure.',
        'Check CI_STATUS_URL against the intended server route and inspect server or tunnel logs. Correct routing or restore the intended endpoint, then retry the callback. This is an investigation plan, not a proven server-side fix.',
        'Is the observed HTTP failure enough for acceptance, or do you require server logs and the missing secondary-error discussion?'),
    27: (
        'Send a success-status message to the configured CI callback endpoint using curl --fail.',
        'The callback returned HTTP 404 and curl exited 22. A later failure-status callback also failed. Text such as tests: PASSED in the posted JSON is a message being sent, not independent proof that tests passed.',
        'The callback HTTP error caused this step failure. The precise server-side reason for 404 remains unresolved; the existing category network_service_failure describes the observed service failure.',
        'Check the URL, route, service availability and server or tunnel logs. Retry only against the intended endpoint. Do not infer an expired tunnel or broken application route from 404 alone.',
        'Can you accept a diagnosis of the observed callback failure while leaving the origin of 404 unresolved?'),
}


def write_guide(root, output, proposals, notes):
    lines = ['# RCA human review guide', '',
             'All decisions here are suggestions from an automated evidence comparison. Your actual decisions stay empty in human_worksheet.json. No database submission or human verification has occurred.', '',
             '## How to review', '',
             'First read the logs and decide what they establish. Then read each Gemini response. A citation ID is only an address: check that the words on that line support the claim. A command printed in a script is not proof that it finished successfully. A daemon error inside cleanup does not prove that the cleanup step failed.', '',
             'Use true, false or null for each correctness field. null means unanswered or unresolved, not incorrect. For unsupported_claims, true means at least one unsupported claim was found. Choose accept, reject or uncertain separately; leave reviewer notes in comment. You may correct ground truth in corrected_ground_truth.', '',
             'When you finish assessing a report, enter your reviewer name, set review_source to human and completed to true. You may finish with an uncertain decision and null criteria. Incomplete rows do not contribute metrics. Suggestions are stored separately in suggested_decisions.json. Do not copy them as your answers without reviewing evidence.', '',
             'Earlier = live_rca_validation.json; improved = rca_reliability_validation.json. Improved refers to the later session, not a guarantee of correctness. Each session has four responses on the same four workflows. The historical report IDs below do not represent fresh database reads.', '',
             'Evidence limits: #13, #23 and #27 have selected saved excerpts, not full logs in this package; #21 also has ../../tests/fixtures/run21_real.json. Fresh GitHub and PostgreSQL access failed during the earlier preparation. No new external collection was attempted for this guide. This is not a blinded human study; see proposed_ground_truth.json for the independence limitations.', '']
    suggestions = []
    for number in sorted(proposals):
        p = proposals[number]
        e = p['evidence']
        goal, happened, cause, fix, question = CONTEXT[number]
        lines += [f'## Run #{number}', '',
                  f"Repository: {p['repository']}; run ID {p['run_id']}; attempt {p['attempt']}; failed job: {e['failed_job']}; failed step: {e['failed_step']}.", '',
                  f'**Goal:** {goal}', '', f'**What happened:** {happened}', '',
                  f'**Why it failed:** {cause}', '', f'**Developer action:** {fix}', '',
                  '**Original preserved evidence:**', '', '```text']
        lines += [f"{i['id']} {i['text']}" for i in e['primary'] + e['secondary']]
        lines += ['```', '', f"**Other errors and uncertainty:** {p['secondary_and_uncertainty']}", '']
        if number == 13:
            artifact = json.loads((root / 'reports' / 'rca_reliability_validation.json').read_text())
            saved = next(c for c in artifact['cases'] if c['run_number'] == 13)
            outcomes = [s for s in saved['report']['final_source_evidence']['step_outcomes']
                        if 'cleanup' in s['name'].lower()]
            lines += ['Saved step metadata (rca_reliability_validation.json, report.final_source_evidence.step_outcomes): ' + json.dumps(outcomes) + '. This is why a missing-container message must not be described as a failed cleanup step.', '']
        for filename, label in [('live_rca_validation.json', 'Earlier'), ('rca_reliability_validation.json', 'Improved')]:
            source = json.loads((root / 'reports' / filename).read_text())
            case = next(c for c in source['cases'] if c['run_number'] == number)
            response = case.get('provider_call', {}).get('diagnosis') or case['report']
            # Keep the exact stored response accessible; omit only nested audit
            # assessments, which are agent judgments rather than model output.
            fields = ['category', 'primary_cause', 'explanation', 'recommended_fix',
                      'failed_step', 'evidence_refs', 'secondary_evidence_refs',
                      'secondary_explanation', 'secondary_errors', 'parallel_failures']
            display = {k: response[k] for k in fields if k in response}
            decision, reason = notes[filename, number]
            lines += [f"### {label} response: {case['report_id']}", '',
                      f'Source: ../{filename}. Exact saved diagnosis fields:', '', '```json',
                      json.dumps(display, indent=2), '```', '',
                      f'**Suggested decision: {decision}.** {reason}', '',
                      f'**Before approval:** {question}', '']
            if number in (13, 21) and label == 'Earlier':
                lines += ['Failed-step assessment: the explanation names the expected step, but the saved raw diagnosis has no separate failed_step field. Do not invent one for the model response.', '']
            if number in (23, 27):
                lines += ['The primary HTTP diagnosis and category match the observed failure. Endpoint checks are appropriate recommendations; they do not prove why the server returned 404. The earlier response omits the later callback error; the improved response includes it.', '']
            suggestions.append(dict(report_id=case['report_id'], run_number=number,
                                    source=filename, suggested_decision=decision,
                                    explanation=reason, review_question=question,
                                    assessment_source='agent_not_human'))
    lines += ['## Evaluation without invented scores', '',
              'metrics.json contains pooled report results and by_session results. Each metric includes its resolved sample size and numerator. Null fields are excluded for that criterion; uncertain decisions are counted separately and excluded from accept/reject rejection rate. Missing evidence should remain null unless you can justify a true or false judgment. Distinct workflow counts show that repeated reports are not new independent failures.', '',
              'Initially all human metric sample sizes are zero and rates are null. No accuracy percentage can be claimed. Even after review, four workflows from one repository cannot establish production accuracy.', '',
              'Rebuild with python -m backend.tools.prepare_independent_review. This preserves your answers and refreshes metrics. Existing source responses and evidence are not changed. Stop here for your manual review; do not submit to the verification API yet.', '']
    (output / 'REVIEW_GUIDE.md').write_text('\n'.join(lines), encoding='utf-8')
    (output / 'suggested_decisions.json').write_text(json.dumps(suggestions, indent=2))
