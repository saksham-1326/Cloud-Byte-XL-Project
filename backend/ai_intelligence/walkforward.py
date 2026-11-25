"""Chronological pre-outcome replay, supplementary to the untouched final holdout.

Every replayed prediction uses only labels of runs that completed before its
own creation. This is retrospective simulation, NOT a prospective live result.
Never use these replay outcomes to select the deployed model.
"""
from datetime import timezone
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .store import timestamp
from .ml import metrics

MIN_HISTORY = 10
MIN_PER_CLASS = 2
THRESHOLD = 0.5


def replay(rows):
    ordered = sorted(rows, key=lambda item: (
        timestamp(item["run"]["created_at"]), item["run"]["run_id"]
    ))
    scored, seen = [], set()
    exclusions = {"insufficient_prior_data": 0, "duplicate_commit": 0}
    for target in ordered:
        run = target["run"]
        sha = run["commit_sha"]
        if sha in seen:
            exclusions["duplicate_commit"] += 1
            continue
        seen.add(sha)
        prediction_time = timestamp(run["created_at"]).astimezone(timezone.utc)
        historical = [
            item for item in ordered
            if item["run"]["run_id"] != run["run_id"]
            and item["run"]["commit_sha"] != sha
            and timestamp(item["run"]["completed_at"]).astimezone(timezone.utc) < prediction_time
        ]
        # One attempt per unique commit: a repeated commit cannot vote twice.
        unique = {}
        for item in historical:
            key = item["run"]["commit_sha"]
            if key not in unique:
                unique[key] = item
        historical = list(unique.values())
        labels = [item["label"] for item in historical]
        positives = sum(labels)
        if len(labels) < MIN_HISTORY or min(positives, len(labels) - positives) < MIN_PER_CLASS:
            exclusions["insufficient_prior_data"] += 1
            continue
        pipeline = make_pipeline(
            DictVectorizer(sparse=False),
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
        )
        pipeline.fit([item["values"] for item in historical], labels)
        probability = float(pipeline.predict_proba([target["values"]])[0, 1])
        baseline = positives / len(labels)
        scored.append({
            "run_id": run["run_id"],
            "attempt": run["attempt"],
            "prediction_time": prediction_time.isoformat(),
            "training_count": len(labels),
            "training_latest_completion": max(
                timestamp(item["run"]["completed_at"]) for item in historical
            ).astimezone(timezone.utc).isoformat(),
            "actual_failure": int(target["label"]),
            "failure_probability": probability,
            "historical_base_rate": baseline,
        })
    failures = sum(item["actual_failure"] for item in scored)
    successes = len(scored) - failures
    both = failures > 0 and successes > 0
    output = {
        "mode": "retrospective_preoutcome_replay",
        "limitation": "Historical walk-forward simulation only; no live prediction timing proof, no model-selection claims, and no independent prospective validation.",
        "protocol": "Expanding historical first-attempt outcomes, completed strictly before each target creation, excluding same-commit observations, deterministic logistic baseline and fixed 0.5 threshold.",
        "eligible_evaluations": len(scored),
        "eligible_failures": failures,
        "eligible_successes": successes,
        "excluded": exclusions,
        "coverage": len(scored) / len(ordered) if ordered else 0.0,
        "threshold": THRESHOLD,
        "measurements_available": both,
        "comparisons": None,
        "examples": scored[-15:],
    }
    if scored:
        labels = [item["actual_failure"] for item in scored]
        model_probabilities = [item["failure_probability"] for item in scored]
        baseline_probabilities = [item["historical_base_rate"] for item in scored]
        output["comparisons"] = {
            "logistic": metrics(labels, model_probabilities, THRESHOLD),
            "historical_base_rate": metrics(labels, baseline_probabilities, THRESHOLD),
        }
    return output
