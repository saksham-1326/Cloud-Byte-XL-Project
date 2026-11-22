# Local prospective ML observation assessment

Follow-up: [local observer implementation](LOCAL_OBSERVER.md) now exists and is
being verified offline. The assessment below records the earlier design stage;
it does not establish live observation or current production readiness.

Assessment date: 2026-11-22. This is a plan, not an implemented observer or a
live observation session. No GitHub Actions executions were queried, predictions
submitted, databases started, workflows changed, or model artifacts replaced.
Official GitHub documentation was consulted to check API behavior.

## Recommendation in plain English

Use B: a small authenticated local polling runner. It asks GitHub whether an
eligible run exists, passes its identity to the existing prediction service,
then checks PostgreSQL through a separate read-only connection. It never needs
an internet-facing Flask server. GitHub is read-only; local prediction/outcome
persistence necessarily writes to a dedicated observation database.

The fewest-component variant calls IntelligenceService.predict directly as a
library, using the existing Store and ActionsClient. Flask and the task worker
are not required for this variant. A thin runner and evidence recorder still
need implementation and approval; none is added here. A loopback Flask API is
an alternative if preserving asynchronous task processing is preferred.

| Approach | Advantages | Limitations for this project |
| --- | --- | --- |
| A. Signed GitHub webhook | Event-driven; avoids frequent discovery requests | GitHub needs a reachable receiver/approved relay; current delivery unverified; requested events miss reruns; delivery may arrive after start |
| B. Authenticated local polling | Outbound HTTPS only; no hosting/public Flask; explicit run-attempt discovery | Misses short queue windows; consumes API budget; needs scheduler, evidence ledger and backoff |
| C. Webhook plus polling | Could recover missed events | Adds both operational paths without proving persistence timing; unjustified for this small local experiment |

GitHub generally recommends webhooks over polling. Polling is the local tradeoff
here because public exposure and external delivery are excluded, not because it
guarantees better capture. Neither method independently proves pre-start
persistence. The same conservative readback/start-time gate is needed for both.
See [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api).

## What exists and what does not

- github.py has authenticated, bounded GETs, pagination, exact attempt reads,
  attempt-specific jobs, redaction and historical SHA snapshots. runs() currently
  walks the entire repository history. It has no polling schedule, ETag/304
  cache, observer cursor or durable observation ledger.
- service.py predict() verifies exact identity, queued status, null conclusion,
  SHA, compatible experimental model and training cutoff; computes allowlisted
  features; rereads status; saves through the existing transactional Store.
  in_progress, requested, waiting and pending are NOT currently eligible.
- store.py locks the eligible run row, requires matching repository/run/attempt/
  SHA/model, and deduplicates shadow inserts. Outcomes and timing verification
  are recorded separately; original prediction fields are not rewritten.
- collector.synchronize fetches history/outcomes and uses the same Store. It may
  perform expensive repository-wide and log/snapshot requests, so it is not a
  cheap discovery poll. It must not be called before independent readback on
  the prediction's critical path.
- The API provides POST /api/ai/v1/predictions and /sync plus task/read endpoints.
  enqueue() persists a task and starts it in the API's single-thread executor.
  A 202 response is not proof a prediction was saved.
- CLI worker polls ai_tasks, NOT GitHub; it supports task recovery. The CLI has
  migrate/sync/train/rca/worker commands and no predict/observe command.
- The dedicated signed /api/ai/v1/webhook accepts workflow_run requested,
  queued and completed actions. queued is not a documented workflow_run action;
  in_progress is ignored and workflow_job events are ignored. The legacy
  /webhook and durable CI callbacks do not start ML prediction.
- ai_shadow_events stores only the latest decision per attempt. Prediction
  predicted_at is sampled before insertion, with no separate commit timestamp.
  service.evaluation counts matched shadow rows, but does not apply the stronger
  independent pre-start readback gate below. Its 500-row read limit also limits
  long-term evaluation. Do not use that output as a stronger evidence claim.

GitHub documents workflow_run requested/in_progress/completed, with requested
absent on reruns: [workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).

## Authentication, polling and rate budget

Use a repository-limited fine-grained token with Actions read and Contents read:
the prediction service reads job/run metadata AND commit/workflow configuration.
Do not reuse a write-capable publishing credential just for convenience. Public
Actions reads can be unauthenticated, but authentication is recommended for a
bounded session and private content requires it. This assessment has not tested
the current credential's permissions or queried its remaining allowance.

A local secret-safe presence check found GITHUB_TOKEN configured and webhook
secret, API repository allowlist and admin token absent. This is not a credential
permission test or proof of an existing process's configuration. The latter
settings are not required for direct polling; its explicit repository guard and
dedicated DB connection settings still need configuration. A genuine observation
database and authenticated model-registry copy have not been provisioned here.

REST discovery can use /repos/{owner}/{repo}/actions/runs?status=queued&per_page=100,
following pagination links with a hard session request budget. Exact attempt
reads and attempt-specific jobs must confirm each candidate. Filters can cap
search results; incomplete/truncated discovery must be reported, not treated as
complete coverage. Reference: [workflow runs](https://docs.github.com/en/rest/actions/workflow-runs).

Proposed starting interval: 15 seconds with small jitter, one repository and one
discovery query. This is a budget choice, not a GitHub requirement or capture
guarantee: 240 discovery GETs/hour, before pagination, inference, jobs and outcome
calls. A 30-second interval costs 120/hour but misses more short queues. Do not
use a one-second loop or multiply polls per candidate without budgeting.

Typical PAT primary allowance is 5,000/hour (unauthenticated 60/hour); the Actions
runner-issued GITHUB_TOKEN has a separate typical 1,000/hour/repository allowance.
The variable name GITHUB_TOKEN does not determine which credential type it is.
Shared use and secondary limits apply. Inspect response headers, use serialized
bounded requests, and account for the service's additional GETs. On 403/429,
honor Retry-After/reset; otherwise pause at least a minute for a secondary limit,
then bounded exponential backoff. Stop on authentication/permission failure.
Reference: [REST limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

Use stable request URLs and conditional ETag requests where supported. An
authorized 304 does not consume primary quota, but is not a new queued-state
observation: an exact fresh run read is still needed before prediction. The
current ActionsClient does not handle 304 or preserve structured retry metadata
for its callers and maps permission-related 403 to a rate/access error. A small
tested transport extension is needed before implementing reliable polling.
Reference: [conditional request behavior](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#use-conditional-requests).

## Queued timing and reruns

Key every record by normalized repository + run_id + run_attempt. Refresh the
latest run to discover its current attempt, then read the exact attempt and its
jobs. Never deduplicate only by run ID or apply an old attempt's start time to
a rerun. Inspect all pages of attempt jobs and retain source metadata. GitHub
provides the [attempt job endpoint](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt).

Do not discover only runs created after session start: a newly queued rerun can
retain an old creation date. Status-based discovery can see that old run's new
attempt. Keep pending attempts across restarts; never overwrite an earlier
attempt's prediction or resubmit a skipped/finished attempt as a new observation.
If an attempt finishes between polls, record a missed opportunity, not a
retrospective prediction. New attempts are evaluated separately.

Suggested ledger records: UTC/monotonic request and response times, repository,
workflow ID, run ID/attempt, SHA, state/conclusion, rate/ETag/request-ID headers,
redacted response digest, model/version/hash, feature provenance, prediction ID,
original probability/threshold/class, separate DB reader completion time, and
eventual attempt-specific job start/outcome evidence. Preserve clock resolution
and uncertainty. Do not store Authorization headers, tokens or unredacted logs.
A local append-only hash chain detects accidental modification but is not an
independent third-party attestation against an administrator.

Accept a conservatively verified prospective case only when:

1. Fresh queued, null-outcome identity matches the exact attempt/SHA; any already
   observed started job makes it ineligible for a pre-start attempt prediction.
2. The existing service saved mode=shadow using the authenticated existing model
   with allowed features and strictly earlier historical outcomes.
3. A separate read-only connection saw the COMMITTED row before earliest actual
   job start for that attempt, allowing for timestamp precision/clock uncertainty.
   predicted_at must also precede start. Compare response/readback completion
   times, not request-start times alone.
4. Complete start/outcome evidence and original-field readback agree after
   reconciliation. Unknown outcomes and late/unverifiable records stay excluded.

An absence of jobs at one poll is not proof none started. Readback obtained only
after execution cannot demonstrate pre-start persistence. GitHub's status/start
timestamps and local wall clocks have finite precision and propagation delay;
if the timing margin is insufficient or clock error unknown, mark uncertain.
HTTP Date is coarse corroboration, not an exact clock-synchronization proof.
Current matched status alone cannot meet this standard because insertion could
occur after predicted_at. A second local connection establishes independent DB
readback, not independent human verification or cryptographic global timing.

## Exact implementation steps, after approval

1. Authenticate and preserve the existing trained model metadata and artifact
   (including original version, feature version, digest, creation/training
   cutoff and threshold). Stop if authentic metadata is unavailable; do not
   reconstruct dates, retrain, or substitute a test model.
2. Create a dedicated loopback observation PostgreSQL database with separate
   writer and read-only reader roles. Keep it separate from personal/deployment
   databases and disposable test fixtures. Apply existing migrations only.
3. Add a thin opt-in local runner that constructs ActionsClient, Store with an
   explicit isolated connection factory, and IntelligenceService. It calls
   predict() directly; no second feature engine/model/INSERT implementation.
   Enforce an explicit repository allowlist in this direct runner because it
   bypasses the HTTP API's authorization checks. Do not invoke app.run().
4. Add bounded, rate-aware, conditional-GET discovery and an append-only local
   ledger/cursor with restart-safe attempt identity, timeouts and a stop condition.
   A single GitHub-reading process and serialized inference are enough initially;
   avoid unbounded parallelism. Track blocked time and missed queue windows.
5. First sync approved authentic history outside the observation hot path. On
   each fresh candidate invoke the existing predictor immediately, then perform
   independent readback before further API/collection work. Capture all skips,
   errors, duplicates and unverifiable outcomes without inventing probabilities.
6. Follow pending exact attempts until completion. Reuse existing collector/Store
   reconciliation during quiet periods. Repository-wide sync is expensive and
   can delay discovery; count its calls/time. If this prevents timely capture,
   separately review a narrow attempt-scoped collector using the same persistence
   code rather than silently changing the inference engine.
7. Verify original prediction-field digest and exact outcome association via
   the reader role. Apply the stronger timing gate in a separate evidence report;
   do not silently treat all existing matched rows as independently verified.
8. Add mocked pagination/rate/304/restart/rerun tests and isolated DB evidence
   tests before enabling the runner. Run a bounded session only after separate
   approval of repository, credentials, DB, interval, duration/request budget,
   evidence destination and model version. Record zero if none qualify.

For this recommended direct-service variant, only PostgreSQL and the runner
must run locally. For the optional API variant, bind Flask explicitly to
127.0.0.1 and use local admin authorization; the app.py main entry point binds
0.0.0.0 by default, so do NOT use that entry point unchanged. Its executor can
process new tasks, with the CLI worker optional for recovery. Never expose it
publicly or enable external delivery as part of this plan.

## Verification performed and approvals

The existing late-run test lacked a SHA, so identity rejection could hide whether
the run-state gate actually worked. It now supplies a valid identity and covers
completed, in_progress, requested, waiting, pending and queued-with-known-outcome
states, asserting that no model is consulted. Existing deterministic feature/
service/client regressions are rerun. No production observer is introduced.
The main-branch 212-pass PostgreSQL/Docker checkpoint is prior
verified evidence, not a newly executed full integration suite in this task.
Targeted regression result: **53 passed, 0 failed, 0 skipped, 0 expected failures**
for test_ml_audit.py, test_ai_ml_rca.py and test_ai_collection.py. The HTTP-blocking
fixture prevents live calls. No PostgreSQL integration suite was rerun because
there is no persistence implementation change or new observer in this task.
All 68 prior preservation hashes match, including frontend/root-package work,
credentials, original RCA artifacts and saved models.

Implementation approval is needed for the runner, small HTTP transport changes,
ledger and isolated tests. Starting a real session requires explicit additional
approval of the operational parameters above. No commits, pushes, merges,
deployments, live monitoring or observation submissions were performed here.
Genuine prospective predictions recorded by this assessment: zero; prospective
metrics remain null and historical ML accuracy remains unchanged.
