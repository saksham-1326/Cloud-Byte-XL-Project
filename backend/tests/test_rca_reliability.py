"""Evidence invariants with independent expectations, not live model scores."""
import copy
import json
from pathlib import Path

import pytest

from backend.ai_intelligence.rca import analyze, extract_evidence, grounded_diagnosis, validate_diagnosis
from backend.tests.test_ai_ml_rca import job_case


def diagnosis(text):
    evidence=extract_evidence(job_case(text))
    return evidence,grounded_diagnosis(evidence)


def test_exit_command_and_actual_exit_are_separate_observations():
    evidence,result=diagnosis('exit 1\n1 passed\nProcess completed with exit code 1.')
    assert result['category']=='intentional_workflow_termination'
    assert evidence['facts']['explicit_exit_commands'][0]['code']==1
    assert evidence['facts']['exit_codes'][0]['code']==1
    assert evidence['facts']['pytest_summaries'][0]['counts']=={'passed':1}
    assert evidence['facts']['commands'][0]['execution_status']=='script_echo_not_execution_proof'


@pytest.mark.parametrize('text',[
    'python -m py_compile backend/app.py\nProcess completed with exit code 1.',
    '1 passed\nProcess completed with exit code 1.',
    'if some_condition; then\nexit 1\nfi\nProcess completed with exit code 1.',
    'echo "exit 1"\nProcess completed with exit code 1.',
    '',
])
def test_missing_or_ambiguous_cause_stays_unknown(text):
    assert analyze(job_case(text))['category']=='insufficient_evidence'


@pytest.mark.parametrize('text,category',[
    ('exit 1\nSyntaxError: invalid syntax\nProcess completed with exit code 1.','compilation_error'),
    ('exit 1\nModuleNotFoundError: No module named flask','dependency_error'),
    ('exit 1\n1 failed, 2 passed','unit_test_failure'),
    ('curl --fail -X POST "$CALLBACK_URL"\ncurl: (22) The requested URL returned error: 404\nProcess completed with exit code 22.','network_service_failure'),
])
def test_observed_diagnostics_outweigh_echoed_exit_or_step_name(text,category):
    assert analyze(job_case(text))['category']==category


def test_compiler_command_is_not_compiler_error():
    evidence,result=diagnosis('python -m py_compile backend/app.py\nexit 1\nProcess completed with exit code 1.')
    assert not evidence['facts']['compiler_errors']
    assert result['category']=='intentional_workflow_termination'


@pytest.mark.parametrize('claim',[
    'The compilation failed in backend/app.py.',
    'Fix the syntax errors in backend/app.py.',
    'A required dependency is unavailable.',
    'A missing dependency caused this failure.',
    'Pytest failed.',
    'There were failing unit tests.',
])
def test_correct_or_unknown_category_cannot_hide_unsupported_claims(claim):
    evidence,result=diagnosis('exit 1\n1 passed\nProcess completed with exit code 1.')
    result.update(category='insufficient_evidence',uncertainty='high',explanation=claim)
    with pytest.raises(ValueError):validate_diagnosis(result,evidence,grounded_diagnosis(evidence))


def test_negated_test_failure_is_not_a_false_positive():
    evidence,result=diagnosis('exit 1\n1 passed\nProcess completed with exit code 1.')
    result['explanation']='Pytest passed. There is no evidence of test failures. The shell contains exit 1.'
    assert validate_diagnosis(result,evidence,grounded_diagnosis(evidence))==result


def test_existing_but_irrelevant_citation_is_rejected():
    evidence,result=diagnosis('exit 1\n1 passed\nProcess completed with exit code 1.')
    result['evidence_refs']=[evidence['primary'][1]['id']]
    with pytest.raises(ValueError,match='cited primary content'):
        validate_diagnosis(result,evidence,grounded_diagnosis(evidence))


@pytest.mark.parametrize('field,value',[
    ('evidence_refs',['invented']),('failed_step','Compile everything'),('failed_job','another job'),
    ('explanation','The shell returned exit code 7.'),('explanation','Pytest reported 999 passed.'),
])
def test_invalid_citations_metadata_and_numeric_claims_rejected(field,value):
    evidence,result=diagnosis('exit 1\n1 passed\nProcess completed with exit code 1.')
    result[field]=value
    with pytest.raises(ValueError):validate_diagnosis(result,evidence,grounded_diagnosis(evidence))


def test_http_status_cannot_be_changed_even_with_real_citations():
    evidence,result=diagnosis('curl: (22) The requested URL returned error: 404\nProcess completed with exit code 22.')
    result['primary_cause']='HTTP 500 caused the callback failure.'
    with pytest.raises(ValueError,match='HTTP code'):
        validate_diagnosis(result,evidence,grounded_diagnosis(evidence))


def test_real_run21_primary_and_secondary_are_separate():
    fixture=json.loads((Path(__file__).parent/'fixtures/run21_real.json').read_text())
    evidence=extract_evidence(fixture['jobs'],workflow='CI')
    result=grounded_diagnosis(evidence)
    result.update(failed_job=evidence['failed_job'],failed_step=evidence['failed_step'],
                  secondary_evidence_refs=[evidence['secondary'][0]['id']],
                  secondary_explanation='Later Docker cleanup reports no such container.')
    assert evidence['failed_workflow']=='CI'
    assert evidence['secondary_facts']['docker_errors']
    assert validate_diagnosis(result,evidence,grounded_diagnosis(evidence))==result
    broken=copy.deepcopy(result);broken['evidence_refs']=result['secondary_evidence_refs']
    with pytest.raises(ValueError,match='unsupported evidence'):validate_diagnosis(broken,evidence,result)
    broken=copy.deepcopy(result);broken['secondary_evidence_refs']=[]
    with pytest.raises(ValueError,match='omitted'):validate_diagnosis(broken,evidence,result)
    broken=copy.deepcopy(result);broken['secondary_evidence_refs']=result['evidence_refs']
    with pytest.raises(ValueError,match='secondary evidence'):validate_diagnosis(broken,evidence,result)


def test_later_callback_failure_is_secondary_and_not_parallel():
    jobs=job_case('##[group]Run curl --fail "$URL"\n##[endgroup]\ncurl: (22) The requested URL returned error: 404\nProcess completed with exit code 22.\n##[group]Run curl --fail "$URL"\ncurl: (22) The requested URL returned error: 404')
    jobs[0]['payload']['steps'].append({'name':'Report failure','number':3,'conclusion':'failure',
                                      'started_at':'2025-01-01T00:00:05Z','completed_at':'2025-01-01T00:00:06Z'})
    evidence=extract_evidence(jobs)
    assert evidence['secondary_facts']['http_errors'][0]['code']==404
    assert evidence['parallel_failures']==0
    assert evidence['additional_failed_steps'][0]['relation']=='later_step_in_same_job'
    assert all(item['line']<5 for item in evidence['primary'])


def test_command_echo_is_not_a_diagnostic():
    jobs=job_case('##[group]Run echo "SyntaxError: demo"\necho "ModuleNotFoundError demo"\nshell: /usr/bin/bash -e {0}\n##[endgroup]\nProcess completed with exit code 1.')
    evidence=extract_evidence(jobs)
    assert not evidence['facts']['compiler_errors']
    assert not evidence['facts']['dependency_errors']
    assert grounded_diagnosis(evidence)['category']=='insufficient_evidence'


def test_nonfatal_cleanup_command_error_does_not_mean_cleanup_step_failed():
    fixture=json.loads((Path(__file__).parent/'fixtures/run21_real.json').read_text())
    evidence=extract_evidence(fixture['jobs'])
    result=grounded_diagnosis(evidence)
    result.update(secondary_evidence_refs=[evidence['secondary'][0]['id']],
                  secondary_explanation='A subsequent cleanup step failed because the container did not exist.')
    with pytest.raises(ValueError,match='successful step metadata'):
        validate_diagnosis(result,evidence,grounded_diagnosis(evidence))
    result['secondary_explanation']='The cleanup command reported no such container; the cleanup step still succeeded.'
    assert validate_diagnosis(result,evidence,grounded_diagnosis(evidence))==result


def test_potentially_tolerated_diagnostic_does_not_automatically_become_primary():
    evidence,result=diagnosis('python -m py_compile app.py || true\nSyntaxError: invalid syntax\nexit 1\nProcess completed with exit code 1.')
    assert evidence['facts']['tolerated_failure_commands']
    assert result['category']=='insufficient_evidence' and result['uncertainty']=='high'


def test_earlier_error_outside_failed_command_frame_is_not_primary():
    jobs=job_case('##[group]Run docker rm -f stale || true\nError response from daemon: No such container: stale\n##[group]Run exit 1\nshell: /usr/bin/bash -e {0}\n##[endgroup]\nProcess completed with exit code 1.')
    report=analyze(jobs)
    assert report['category']=='intentional_workflow_termination'
    assert not report['facts']['docker_errors']
    assert report['secondary_errors'][0]['line']==2


def test_truncated_frame_stays_uncertain():
    jobs=job_case('exit 1')
    jobs[0]['log_text']='\n'.join('2025-01-01T00:00:01Z '+line for line in
                                ['##[group]Run exit 1']+['echo context']*70+['shell: /usr/bin/bash -e {0}','##[endgroup]','Process completed with exit code 1.'])
    evidence=extract_evidence(jobs)
    assert evidence['evidence_truncated']
    assert len(evidence['primary'])==60
    result=grounded_diagnosis(evidence)
    assert result['category']=='insufficient_evidence' and result['uncertainty']=='high'


@pytest.mark.parametrize('run_number',[21,13,23,27])
def test_fresh_live_responses_replayed_offline_with_final_guards(run_number):
    fixture=json.loads((Path(__file__).parent/'fixtures/gemini_reliability_responses.json').read_text(encoding='utf-8'))
    case=next(row for row in fixture['cases'] if row['run_number']==run_number)
    result=case['diagnosis']
    assert result['category']==case['expected_category']
    anchor=grounded_diagnosis(case['evidence'])
    if case['expected_guard_status']=='rejected':
        with pytest.raises(ValueError,match='successful step metadata'):
            validate_diagnosis(result,case['evidence'],anchor)
    else:
        assert validate_diagnosis(result,case['evidence'],anchor)==result
