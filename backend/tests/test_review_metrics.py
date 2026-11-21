import pytest

from backend.ai_intelligence.review_metrics import calculate


def test_agent_and_incomplete_rows_cannot_count_as_human_results():
    result = calculate([{'review_source': 'agent', 'completed': True},
                        {'review_source': 'human', 'completed': False}])
    assert result['human_reviewed_reports'] == 0
    assert all(m['sample_size'] == 0 and m['rate'] is None
               for m in result['metrics'].values())


def test_each_metric_has_its_own_resolved_denominator():
    rows = [dict(report_id='a', review_source='human', completed=True,
                 primary_cause_correct=True, category_correct=False,
                 evidence_correct=True, unsupported_claims=False,
                 fix_correct=None, decision='uncertain'),
            dict(report_id='b', review_source='human', completed=True,
                 primary_cause_correct=False, category_correct=True,
                 fix_correct=False, decision='reject')]
    result = calculate(rows)
    assert result['metrics']['primary_root_cause_accuracy']['rate'] == .5
    assert result['metrics']['evidence_support_rate']['sample_size'] == 1
    assert result['metrics']['recommended_fix_correctness']['rate'] == 0
    assert result['metrics']['rejection_rate']['sample_size'] == 1
    assert result['uncertain_decisions'] == 1


def test_duplicate_reports_require_adjudication():
    row = dict(report_id='a', review_source='human', completed=True)
    with pytest.raises(ValueError):
        calculate([row, row])


def test_sessions_and_reports_on_same_workflow_remain_separate():
    base = dict(review_source='human', completed=True, run_id=123,
                repository='owner/repo', attempt=1)
    rows = [dict(base, report_id='early', source='earlier', primary_cause_correct=False),
            dict(base, report_id='later', source='improved', primary_cause_correct=True)]
    result = calculate(rows)
    assert result['human_reviewed_reports'] == 2
    assert result['distinct_workflows'] == 1
    assert result['by_session']['earlier']['metrics']['primary_root_cause_accuracy']['rate'] == 0
    assert result['by_session']['improved']['metrics']['primary_root_cause_accuracy']['rate'] == 1


def test_missing_evidence_is_not_automatically_scored():
    result = calculate([dict(report_id='a', source='earlier', review_source='human',
                             completed=True, decision='uncertain', evidence_correct=None)])
    assert result['metrics']['evidence_support_rate']['sample_size'] == 0
    assert result['metrics']['evidence_support_rate']['rate'] is None
    assert result['metrics']['rejection_rate']['rate'] is None
    assert result['uncertain_decisions'] == 1


@pytest.mark.parametrize('change', [{'decision': 'approved'}, {'evidence_correct': 'true'},
                                    {'unsupported_claims': 1}])
def test_invalid_completed_values_fail_instead_of_silently_disappearing(change):
    with pytest.raises(ValueError):
        calculate([dict(report_id='a', review_source='human', completed=True, **change)])
