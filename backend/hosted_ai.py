"""Best-effort hosted AI processor. Public HTTP access remains SELECT-only.

Render Free sleeps after inactivity, so queued-run shadow predictions cannot
be guaranteed to execute before the workflow starts. Historical backtests and
rules-based RCA must not be presented as verified prospective performance.
"""
import logging
import os
import threading
import time

from .database import configuration, connect
from .ai_intelligence.github import ActionsClient, repository_name
from .ai_intelligence.store import Store
from .ai_intelligence.service import IntelligenceService

LOG = logging.getLogger("cloud_bytexl.hosted_ai")
RUN_LIMIT = 100
POLL_SECONDS = 90
HISTORY_SECONDS = 1800


def worker_connection():
    """A dedicated, restricted writer never used by a public HTTP route."""
    url = os.getenv("AI_WORKER_DATABASE_URL", "")
    if not url:
        raise ValueError("AI worker database URL is unavailable")
    cfg = configuration({"DATABASE_URL": url, "DB_SSLMODE": "require"})
    with connect(cfg, readonly=False) as conn:
        row = conn.execute("""SELECT current_user, current_database(), rolsuper,
            rolcreatedb, rolcreaterole,
            has_table_privilege(current_user,'public.ai_runs','INSERT')
            FROM pg_roles WHERE rolname=current_user""").fetchone()
        if row != ("cloud_bytexl_ai_worker", "neondb", False, False, False, True):
            raise ValueError("Dedicated AI writer identity or privileges are incorrect")
    return connect(cfg, readonly=False)


class BoundedClient(ActionsClient):
    def runs(self, repo):
        # One bounded GitHub request rather than paging through the full history.
        return self.get(f"/repos/{repository_name(repo)}/actions/runs?per_page={RUN_LIMIT}")["workflow_runs"]


def process_cycle(service, repo, history_due):
    runs = service.client.runs(repo)
    # Only actual queued runs are considered; failed timing checks skip rather
    # than manufacturing retrospective live predictions.
    for run in runs:
        if run.get("status") == "queued" and run.get("id") and run.get("run_attempt"):
            try:
                service.predict(repo, int(run["id"]), int(run["run_attempt"]))
            except Exception as exc:
                LOG.warning("Queued shadow prediction skipped: %s", type(exc).__name__)

    if not history_due:
        return

    # Recalculate the new evidence audit from already-synchronized rows first.
    # Remote log backfilling can take longer than a Render Free instance stays
    # awake, so never make model audit depend on that network-bound operation.
    try:
        saved = service.store.models(repo)
        if saved and ('walkforward' not in saved[0]['metrics'] or 'release_gate' not in saved[0]['metrics']):
            audited = service.train(repo)
            LOG.info("Existing history walk-forward audit status: %s", audited.get("status"))
    except Exception as exc:
        LOG.warning("Existing history replay unavailable: %s", type(exc).__name__)

    from .ai_intelligence.collector import synchronize
    result = synchronize(service.client, service.store, repo)
    LOG.info("Historical synchronization processed %s attempts", result["processed_attempts"])
    existing = service.store.models(repo)
    experimental = [m for m in existing if m["status"] == "experimental"]
    # Model artifacts reside on Render's ephemeral disk. Refit if unavailable
    # after an instance restart; preserve model-version identities in Neon.
    artifact_ok = bool(experimental and experimental[0].get("artifact_path")
                       and os.path.isfile(experimental[0]["artifact_path"]))
    # Refit only after enough genuinely new chronological examples exist.
    # An old fitted model is not silently treated as current after history grows.
    eligible = sum(r["attempt"] == 1 and r.get("completed_at")
                   and r.get("conclusion") in ("failure", "success")
                   for r in service.store.runs(repo))
    model_size = int(experimental[0]["metrics"].get("dataset_size", 0)) if experimental else 0
    # Deploy a one-time rolling audit for legacy versions that lack it.
    needs_refresh = eligible >= model_size + 12 or bool(experimental and ('walkforward' not in experimental[0]['metrics'] or 'release_gate' not in experimental[0]['metrics']))
    if not artifact_ok or needs_refresh:
        model = service.train(repo)
        LOG.info("Experimental training status: %s, observed=%s, previous=%s",
                 model.get("status"), eligible, model_size)

    failures = [r for r in reversed(service.store.runs(repo))
                if r["status"] == "completed" and r.get("conclusion") == "failure"]
    covered = {(r["run_id"], r["attempt"]) for r in service.store.reports(repo)}
    for run in failures[:8]:
        key = (run["run_id"], run["attempt"])
        if key in covered:
            continue
        try:
            # RCA_PROVIDER=none: evidence-based engine, no paid external calls.
            service.rca(repo, *key)
        except Exception as exc:
            LOG.warning("Rules-based RCA not available: %s", type(exc).__name__)


def _loop():
    repo = repository_name(os.environ.get("AI_ALLOWED_REPOSITORIES", "").split(",")[0].strip())
    service = IntelligenceService(Store(worker_connection), BoundedClient())
    last_full = 0.0
    while True:
        due = time.monotonic() - last_full >= HISTORY_SECONDS
        try:
            process_cycle(service, repo, due)
            if due:
                last_full = time.monotonic()
        except Exception as exc:
            LOG.error("Hosted AI cycle failed: %s", type(exc).__name__)
        threading.Event().wait(POLL_SECONDS)


def launch():
    if os.getenv("HOSTED_AI_ENABLED") != "1":
        return
    if os.getenv("PUBLIC_DEMO_MODE") != "1" or os.getenv("RCA_PROVIDER", "none") != "none":
        raise ValueError("Hosted AI requires read-only public API and free evidence-based RCA")
    if not os.getenv("AI_WORKER_DATABASE_URL"):
        raise ValueError("HOSTED_AI_ENABLED requires AI_WORKER_DATABASE_URL")
    threading.Thread(target=_loop, name="bytexl-hosted-ai", daemon=True).start()
