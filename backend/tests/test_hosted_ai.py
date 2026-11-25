"""No hosted AI writes or provider calls are enabled without explicit opt-in."""
import pytest
from backend import hosted_ai


def test_worker_off_by_default(monkeypatch):
    monkeypatch.delenv("HOSTED_AI_ENABLED", raising=False)
    monkeypatch.delenv("AI_WORKER_DATABASE_URL", raising=False)
    assert hosted_ai.launch() is None


def test_worker_missing_writer_fails_closed(monkeypatch):
    monkeypatch.setenv("HOSTED_AI_ENABLED", "1")
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "1")
    monkeypatch.setenv("RCA_PROVIDER", "none")
    monkeypatch.delenv("AI_WORKER_DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="AI_WORKER_DATABASE_URL"):
        hosted_ai.launch()


def test_paid_provider_mode_is_not_silently_enabled(monkeypatch):
    monkeypatch.setenv("HOSTED_AI_ENABLED", "1")
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "1")
    monkeypatch.setenv("RCA_PROVIDER", "gemini")
    with pytest.raises(ValueError, match="free evidence-based RCA"):
        hosted_ai.launch()


def test_history_is_bounded_to_one_api_page(monkeypatch):
    calls = []
    def fake_get(self, path):
        calls.append(path)
        return {"workflow_runs":[{"id": i} for i in range(3)]}
    monkeypatch.setattr(hosted_ai.BoundedClient, "get", fake_get)
    results = hosted_ai.BoundedClient().runs("saksham-1326/cloud-byte-xl-project")
    assert len(results) == 3
    assert calls == [f"/repos/saksham-1326/cloud-byte-xl-project/actions/runs?per_page={hosted_ai.RUN_LIMIT}"]
