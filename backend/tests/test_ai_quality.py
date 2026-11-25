"""Shadow risk scores require independent class support, replay skill and calibration."""
from backend.ai_intelligence.quality import assess


def passing_metrics():
    return {
        "selected_model":"logistic",
        "test":{"confusion_matrix":[[16,2],[1,8]]},
        "walkforward":{
            "eligible_failures":8,
            "eligible_successes":32,
            "comparisons":{
                "logistic":{"recall":0.85,"precision":0.70,"brier_score":0.14},
                "historical_base_rate":{"brier_score":0.21},
            },
        },
    }


def test_missing_model_evidence_never_qualifies():
    result=assess({})
    assert result["status"]=="insufficient_evidence"
    assert result["reasons"]


def test_replay_with_zero_detected_failures_does_not_qualify():
    metrics=passing_metrics()
    metrics["walkforward"]["comparisons"]["logistic"]["recall"]=0.0
    result=assess(metrics)
    assert result["status"]=="insufficient_evidence"
    assert any("recall" in reason for reason in result["reasons"])


def test_holdout_with_too_few_failures_does_not_qualify():
    metrics=passing_metrics()
    metrics["test"]["confusion_matrix"]=[[10,0],[0,1]]
    result=assess(metrics)
    assert result["status"]=="insufficient_evidence"
    assert any("too few" in reason for reason in result["reasons"])


def test_other_model_cannot_borrow_logistic_replay_score():
    metrics=passing_metrics()
    metrics["selected_model"]="random_forest"
    result=assess(metrics)
    assert result["status"]=="insufficient_evidence"
    assert any("selected model family" in reason for reason in result["reasons"])


def test_replay_must_beat_historical_probability_baseline():
    metrics=passing_metrics()
    metrics["walkforward"]["comparisons"]["logistic"]["brier_score"]=0.25
    result=assess(metrics)
    assert result["status"]=="insufficient_evidence"
    assert any("baseline" in reason for reason in result["reasons"])


def test_supported_shadow_eligibility_is_not_proof_of_prospective_accuracy():
    result=assess(passing_metrics())
    assert result["status"]=="shadow_eligible"
    assert "never prove prospective accuracy" in result["limitation"]


def test_unvalidated_model_skips_queued_run_without_fetching_snapshot():
    from backend.ai_intelligence.service import IntelligenceService

    class Store:
        def models(self,repo):
            return [{"status":"experimental","version":"bad","created_at":"2025-01-01T00:00:00+00:00",
                     "metrics":{"feature_version":"prequeue-v2-utc-standardized","test":{"confusion_matrix":[[10,0],[0,0]]}}}]
        def query(self,*args,**kwargs):return []
    class Client:
        def run(self,*args):
            return {"id":1,"run_attempt":1,"head_sha":"a"*40,"created_at":"2025-10-01T00:00:00Z","status":"queued","conclusion":None}
        def snapshot(self,*args):
            raise AssertionError("Unvalidated inference must not fetch target features")
    answer=IntelligenceService(Store(),Client()).predict("example/repo",1,1)
    assert answer["status"]=="insufficient_data"
    assert "not approved" in answer["reason"]
