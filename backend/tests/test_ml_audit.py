"""Leakage and historical replay checks; controlled rows are not real accuracy data."""
import copy
import json
from datetime import timedelta
from pathlib import Path

import pytest

from backend.ai_intelligence import ml
from backend.tests.test_ai_ml_rca import run, snapshot
from backend.tools.replay_historical_ml import replay


def test_replays_frozen_historical_metrics_and_dummy_prior():
    saved = json.loads((Path(__file__).parent / 'fixtures/historical_ml_evaluation.json').read_text())
    original = copy.deepcopy(saved)
    result = replay(saved)
    assert saved == original
    assert result['saved_selected_metrics_match'] and result['saved_dummy_metrics_match']
    assert result['split_class_counts']['train'] == dict(success=13, failure=3)
    assert result['selected_metrics']['confusion_matrix'] == [[3, 1], [2, 0]]
    assert result['dummy_metrics']['confusion_matrix'] == [[4, 0], [2, 0]]
    assert result['selected_metrics']['recall'] == result['dummy_metrics']['recall'] == 0
    assert result['selected_metrics']['pr_auc'] == pytest.approx(1/3)
    saved['backtest'].append(saved['backtest'][0])
    with pytest.raises(ValueError, match='Duplicate'):
        replay(saved)


def test_no_target_or_unavailable_history_enters_features():
    target = run(10, 1)
    valid = run(2, 1)
    unfinished = run(3, 1); unfinished['completed_at'] = None
    boundary = run(4, 1); boundary['completed_at'] = target['created_at']
    long_running = run(5, 1); long_running['completed_at'] = target['created_at'] + timedelta(hours=1)
    other_workflow = run(6, 1); other_workflow['workflow_id'] = 2
    sibling = run(7, 1, target['commit_sha'])
    unknown = run(8); unknown['conclusion'] = 'cancelled'
    history = [target, valid, unfinished, boundary, long_running, other_workflow, sibling, unknown]
    values, proof = ml.features(target, history, snapshot(target), target['created_at'])
    assert values['prior_run_count'] == 1
    assert [r['run_id'] for r in proof['prior_runs']] == [valid['run_id']]
    contaminated = copy.deepcopy(target)
    contaminated.update(conclusion='success', completed_at=target['created_at'], log_text='failure')
    contaminated['payload'].update(duration_seconds=999999, error='compiler failure', jobs=[{'failed': True}])
    changed = [contaminated if r['run_id'] == target['run_id'] else r for r in history]
    assert ml.features(contaminated, changed, snapshot(target), target['created_at'])[0] == values
    assert not {'conclusion', 'duration_seconds', 'log_text', 'error', 'jobs'} & values.keys()


def test_future_retry_cannot_replace_available_earlier_attempt():
    target = run(10)
    prior = run(2, 1)
    retry = {**prior, 'attempt': 2, 'conclusion': 'success',
             'completed_at': target['created_at'] + timedelta(hours=1)}
    values, proof = ml.features(target, [prior, retry], snapshot(target), target['created_at'])
    assert values['recent_failure_rate'] == 1
    assert proof['prior_runs'][0]['attempt'] == 1


def test_normal_split_training_and_validation_outcomes_precede_next_partition():
    rows = [{'run': run(i)} for i in range(20)]
    rows[11]['run']['completed_at'] = rows[13]['run']['created_at']
    rows[15]['run']['completed_at'] = rows[17]['run']['created_at']
    train, validation, test = ml.temporal_split(rows)
    assert all(r['run']['completed_at'] < validation[0]['run']['created_at'] for r in train)
    assert all(r['run']['completed_at'] < test[0]['run']['created_at'] for r in validation)


def test_empty_validation_still_requires_training_outcomes_before_test():
    rows = [{'run': run(i)} for i in range(10)]
    rows[6]['run']['commit_sha'] = rows[0]['run']['commit_sha']
    rows[7]['run']['commit_sha'] = rows[1]['run']['commit_sha']
    rows[5]['run']['completed_at'] = rows[9]['run']['created_at'] + timedelta(days=1)
    train, validation, test = ml.temporal_split(rows)
    assert not validation
    assert all(r['run']['completed_at'] < test[0]['run']['created_at'] for r in train)


def test_empty_partitions_are_safe_and_equal_cutoff_is_excluded():
    assert ml.temporal_split([]) == ([], [], [])
    rows = [{'run':run(i)} for i in range(10)]
    rows[6]['run']['commit_sha'] = rows[0]['run']['commit_sha']
    rows[7]['run']['commit_sha'] = rows[1]['run']['commit_sha']
    rows[5]['run']['completed_at'] = rows[8]['run']['created_at']
    train, validation, test = ml.temporal_split(rows)
    assert not validation and test
    assert rows[5] not in train
