"""Chronological replay is retrospective only; future outcomes must not leak."""
from datetime import datetime, timedelta, timezone
import pytest
from backend.ai_intelligence.walkforward import replay


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def item(number, failure=False, *, completed_offset=1, commit=None):
    created = BASE + timedelta(days=number)
    return {
        "run": {
            "run_id": number,
            "attempt": 1,
            "commit_sha": commit or f"sha-{number}",
            "created_at": created,
            "completed_at": created + timedelta(hours=completed_offset),
        },
        "label": int(failure),
        "values": {"changed_files": number % 5, "prior_run_count": number},
    }


def test_walkforward_only_uses_completed_prior_outcomes():
    rows = [item(i, failure=(i % 4 == 0)) for i in range(1, 27)]
    report = replay(rows)
    assert report["mode"] == "retrospective_preoutcome_replay"
    assert report["eligible_evaluations"] > 0
    for example in report["examples"]:
        assert datetime.fromisoformat(example["training_latest_completion"]) < datetime.fromisoformat(example["prediction_time"])
    assert report["comparisons"]["logistic"]["n"] == report["eligible_evaluations"]


def test_walkforward_does_not_use_future_or_same_commit_labels():
    rows = [item(i, failure=(i % 3 == 0)) for i in range(1, 24)]
    original = replay(rows)
    # A long-running job that finishes after every prediction must never
    # count as a past labeled observation.
    rows[0]["run"]["completed_at"] = BASE + timedelta(days=100)
    changed = replay(rows)
    assert changed["eligible_evaluations"] <= original["eligible_evaluations"]
    duplicate = item(25, True, commit="sha-23")
    check = replay(rows + [duplicate])
    assert check["excluded"]["duplicate_commit"] >= 1


def test_walkforward_no_warranted_score_when_no_failure_class():
    rows = [item(i, failure=False) for i in range(1, 25)]
    report = replay(rows)
    assert report["eligible_evaluations"] == 0
    assert report["comparisons"] is None
    assert report["measurements_available"] is False


def test_walkforward_single_class_evaluation_not_claimed_as_valid():
    rows = [item(i, failure=(i <= 4 and i % 2 == 0)) for i in range(1, 25)]
    report = replay(rows)
    if report["eligible_evaluations"]:
        assert report["comparisons"]["logistic"]["roc_auc"] is None
        assert report["measurements_available"] is False
