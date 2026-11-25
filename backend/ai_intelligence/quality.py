"""Conservative release policy for *experimental shadow* CI failure predictions.

Passing this gate permits only no-impact shadow inference, not autonomous
remediation, production reliability claims, or verified prospective accuracy.
"""
POLICY_VERSION = "shadow-release-v1"
MIN_HOLDOUT_FAILURES = 3
MIN_HOLDOUT_SUCCESSES = 10
MIN_REPLAY_FAILURES = 5
MIN_REPLAY_SUCCESSES = 20
MIN_RECALL = 0.70
MIN_PRECISION = 0.50


def _counts(result):
    matrix = result.get("confusion_matrix") if isinstance(result, dict) else None
    if not isinstance(matrix, list) or len(matrix) != 2:
        return None
    try:
        tn, fp = matrix[0]
        fn, tp = matrix[1]
        counts = (int(tn), int(fp), int(fn), int(tp))
        if min(counts) < 0:
            return None
        return counts
    except (ValueError, TypeError):
        return None


def assess(metrics):
    """Use evidence for the selected model, never a different-model replay."""
    metrics = metrics if isinstance(metrics, dict) else {}
    reasons = []
    selected = metrics.get("selected_model")
    holdout = metrics.get("test") or {}
    counts = _counts(holdout)
    if counts is None:
        reasons.append("The chronological holdout confusion matrix is unavailable.")
    else:
        tn, fp, fn, tp = counts
        if fn + tp < MIN_HOLDOUT_FAILURES or tn + fp < MIN_HOLDOUT_SUCCESSES:
            reasons.append("Chronological holdout has too few independently observed failures or successes.")
        elif (tp / (fn + tp) < MIN_RECALL or
              tp / max(tp + fp, 1) < MIN_PRECISION):
            reasons.append("Held-out failure recall or precision is below the shadow-release threshold.")

    replay = metrics.get("walkforward") or {}
    comparisons = replay.get("comparisons") if isinstance(replay, dict) else None
    # Current rolling evaluation implements only the fixed logistic baseline;
    # it MUST NOT be used to certify a different model family.
    if selected != "logistic":
        reasons.append("No comparable walk-forward evaluation exists for the selected model family.")
    elif not isinstance(comparisons, dict) or not comparisons.get("logistic") or not comparisons.get("historical_base_rate"):
        reasons.append("Comparable chronological replay and baseline results are unavailable.")
    else:
        count_fail = replay.get("eligible_failures", 0)
        count_ok = replay.get("eligible_successes", 0)
        if count_fail < MIN_REPLAY_FAILURES or count_ok < MIN_REPLAY_SUCCESSES:
            reasons.append("Chronological replay has insufficient distinct failures or successes.")
        else:
            model = comparisons["logistic"]
            baseline = comparisons["historical_base_rate"]
            if (model.get("recall") is None or model.get("precision") is None or
                model["recall"] < MIN_RECALL or model["precision"] < MIN_PRECISION):
                reasons.append("Rolling replay did not meet the failure-recall and precision thresholds.")
            if (model.get("brier_score") is None or baseline.get("brier_score") is None or
                model["brier_score"] >= baseline["brier_score"]):
                reasons.append("Rolling replay probability calibration did not beat the historical-rate baseline.")

    return {
        "policy_version": POLICY_VERSION,
        "status": "shadow_eligible" if not reasons else "insufficient_evidence",
        "reasons": reasons,
        "requirements": {
            "holdout_min_failures": MIN_HOLDOUT_FAILURES,
            "holdout_min_successes": MIN_HOLDOUT_SUCCESSES,
            "replay_min_failures": MIN_REPLAY_FAILURES,
            "replay_min_successes": MIN_REPLAY_SUCCESSES,
            "min_failure_recall": MIN_RECALL,
            "min_failure_precision": MIN_PRECISION,
            "rolling_brier_better_than_baseline": True,
        },
        "limitation": "Passing permits no-impact shadow inference only. These historical criteria never prove prospective accuracy or model generalization.",
    }
