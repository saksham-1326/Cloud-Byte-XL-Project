# Prospective prediction readiness and commit review

Reviewed 2026-11-21 on codex/independent-rca-review. This is an operational plan,
not evidence of live predictions. No deployment, webhook, credential, model or
GitHub repository settings were changed. No commits have been created. Final
preparation stages only the first reviewed scope; later scopes have separate
review patches until approval permits creating the commits in sequence.

## Working-tree organization

The existing branch is already a dedicated development branch. Proposed commits
are below, for approval only. Select README hunks for each commit rather than
including its entire combined diff in the first commit. Preserve all local files.

### 1. Offline assisted RCA evaluation

Proposed title: `test(rca): add reproducible assisted evaluation tooling`.

- .gitignore: ignore generated backend/reports and backend/ai_audit.json.
- backend/ai_intelligence/review_metrics.py.
- backend/tools/prepare_independent_review.py.
- backend/tools/review_guide.py.
- backend/tools/assisted_rca_recommendations.py.
- backend/tests/test_review_metrics.py.
- backend/tests/test_independent_review_package.py.
- backend/tests/test_assisted_rca_recommendations.py.
- backend/tests/fixtures/independent_review_inputs.json.
- README: RCA review, assisted decision statistics and generated-output policy.

The fixture is an explicitly frozen regression input, not a generated review to
publish as a human result. Original report IDs and diagnosis strings are retained.
Human metrics require completed human rows and resolved boolean judgments;
assisted decisions cannot enter that calculation. Provisional decision counts
remain 3 accept, 3 reject, 2 uncertain; they are not accuracy. Session denominators
are separate. Original sources match saved hashes and the human worksheet has
zero completed rows. There are no real review API submissions in this task.

### 2. ML reliability fixes and historical replay

Proposed title: `fix(ml): enforce temporal safety and shadow prediction integrity`.

- backend/ai_intelligence/ml.py, service.py and store.py.
- backend/tests/test_ai_ml_rca.py (valid SHA in the untrained-model test fixture).
- backend/tests/test_ml_audit.py and test_shadow_postgresql.py.
- backend/tests/fixtures/historical_ml_evaluation.json.
- backend/tools/replay_historical_ml.py.
- docs/ML_PREDICTION_AUDIT.md and docs/SHADOW_VERIFICATION.md.
- README: historical ML audit, split fix and isolated verification results.

Review conclusion: target final outcomes/logs/durations stay excluded; prior
outcomes require strict pre-cutoff completion; the empty-validation split defect
is fixed. Store uses transactions, a matching repository/run/attempt/SHA/model
selection and a run-row lock during prediction insertion. Completion upserts
serialize against that lock, cannot regress to queued state, and do not rewrite
prediction fields. Duplicate requests preserve one row via the existing unique
index. Changed completion metadata with a mismatched SHA cannot write jobs or
outcomes. Attempt/repository joins are exact. These application guarantees do
not prevent a database administrator from editing prediction records.

### 3. Prospective observation procedure

Proposed title: `docs: document prospective prediction verification`.

- docs/PROSPECTIVE_PREDICTION_PLAN.md (this file).
- README: actual event mechanism, missing configuration and link to this plan.

Excluded from every proposed commit: generated backend/reports, .env and other
credentials, backend/ai_artifacts/*.joblib, backend/ai_audit.json, screenshots,
frontend-app changes/artifacts, root package.json/package-lock.json,
postcss.config.js and tailwind.config.js. These are preserved locally. Existing
frontend modifications include index.html, App.jsx, index.css, main.jsx and
frontend tailwind.config.js; additional untracked frontend files are unrelated.
No migrations, provider code, callback implementation or Flask routes changed.

## Exact event and process mechanism

1. Running `python -m backend.app` constructs the Flask app, registers the AI
   blueprint and creates IntelligenceService with a single-thread executor.
   Registration alone neither watches GitHub nor starts the durable worker.
2. POST /api/ai/v1/predictions accepts repository, run_id and attempt, persists a
   predict task, and submits it to the API process's executor. A running API
   process can therefore execute new requests without a separate worker.
3. POST /api/ai/v1/webhook validates HMAC-SHA256, requires GitHub event workflow_run
   and an allowlisted repository, and enqueues observe tasks. requested/queued
   actions request prediction followed by synchronization; completed requests
   synchronization only. in_progress is ignored by this implementation.
4. `python -m backend.ai_intelligence.cli worker` is the separately started durable
   recovery worker. It polls ai_tasks every two seconds, claims a queued task
   atomically, heartbeats, and requeues running tasks stale for 15 minutes. It
   does NOT poll GitHub for new runs. API and worker can race to claim a task;
   the conditional task-state update prevents both from executing that claim.
5. Prediction re-fetches the exact GitHub attempt and requires status queued,
   conclusion null, a SHA and valid identity. It loads the existing compatible
   experimental model, computes allowlisted features and rechecks run state.
   A completed or in-progress run is skipped, not backfilled.
6. synchronize fetches outcomes and jobs and reconciles existing predictions.
   A completion webhook can trigger it, or an administrator can request POST
   /api/ai/v1/sync or run the CLI sync command. The collector walks repository
   history, so cold sync work can delay later queued prediction tasks.

The legacy /webhook in app.py is not the dedicated AI workflow_run endpoint.
Durable CI status callbacks and .github/workflows/ci.yml do not themselves start
ML prediction. There is no built-in scheduled GitHub polling observer and the
CLI has no predict command. A bounded external observer would need to call the
existing API and keep its own observation evidence; it is not installed here.

GitHub documents workflow_run actions requested, in_progress and completed, not
queued; the handler's queued branch is not proof of actual delivery. requested
does not occur on reruns, so existing webhook handling alone cannot establish
queued coverage for repeated attempts. workflow_job is a different event and is
ignored here. Sources: [workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run)
and [webhook payloads](https://docs.github.com/en/webhooks/webhook-events-and-payloads#workflow_run).

## Observed readiness and configuration gaps

A secret-safe check of backend/.env merged with the current shell environment
found GITHUB_TOKEN present, and GITHUB_WEBHOOK_SECRET, AI_ALLOWED_REPOSITORIES
and AI_ADMIN_TOKEN absent. Token presence does not prove Actions permission.
An existing backend process could have a different environment; its configuration
and uptime were not authenticated. The GitHub repository's webhook settings and
actual delivery history were not verified or changed. Do not infer delivery from
passing mocked webhook tests. The dedicated endpoint rejects requests when its
secret is unset. Local administrator loopback access can work without an admin
token; remote access also requires an allowlist and should use the admin token.

Required before live observation: an approved dedicated observation database
(separate from the disposable test database and personal/deployment databases),
applied existing migrations, read/write application access, independent read-only
verification access, authenticated original model metadata and its existing
artifact, matching feature version/hash, completed pre-outcome history, a GitHub
Actions-capable credential, and a continuously running API/executor plus recovery
worker as appropriate. Do not invent missing model timestamps or metadata from
an evaluation summary. If the original metadata cannot be authenticated, stop
with insufficient readiness rather than silently retraining or replacing it.

Choose event delivery only after approval: either use an already approved secure
workflow_run webhook route and verify deliveries, or implement/run an approved
bounded read-only observer that submits exact eligible identities to the local
API. No public callback URL, webhook subscription, polling job or deployment
setting is created by this plan. Webhook delivery to localhost is not assumed.
The second route avoids assuming a remote webhook is already connected but is
not an existing automatic feature. Short queue windows can legitimately yield
zero predictions. Report eligible/seen/skipped coverage, not just successes.

## Reproducible genuine-observation procedure

1. Confirm the scoped commits/configuration are approved. Prepare the dedicated
   observation environment without using the disposable regression database.
   Freeze the original model version, threshold, feature version, digest and
   training cutoff. Verify the existing artifact with load_model. Snapshot
   initial prediction/outcome counts through an independent read-only connection.
   Sync authentic history before observation so cold ingestion does not consume
   the queue window. Do not invoke train or RCA/provider endpoints.
2. Start the API and, if used, the durable recovery worker with explicit approved
   environment variables. Verify DB connectivity/model readback and process
   health. Confirm clock synchronization and record UTC clock source/uncertainty.
   Keep secrets out of evidence. Do not enable public callbacks or change GitHub
   workflows as part of observation.
3. Start an append-only observation ledger outside the committed source tree.
   For each naturally observed run record repository, workflow_id, run_id,
   run_attempt, head_sha, exact status/conclusion, GitHub updated/start times,
   UTC observation time, transport/request receipt times, and the original
   redacted API response or signed-delivery metadata. Current ai_shadow_events
   overwrites the latest event and is not an append-only observation ledger.
4. Only if the fresh exact attempt is queued and outcome-free submit JSON
   {repository, run_id, attempt} to POST /api/ai/v1/predictions. Use required local
   authorization. Retain returned task_id and poll GET /api/ai/v1/tasks/<task_id>
   with the repository until completed or failed. A 202 response means queued
   task, not prediction success. Record skipped/failed/already_predicted honestly.
   Never submit completed attempts as prospective, and never relabel backtest.
5. Immediately read the exact shadow row using a NEW read-only PostgreSQL
   connection, parameterizing repository/run_id/attempt. Save its id, mode,
   predicted_at, model_version, original probability, threshold, predicted_class
   and complete feature_snapshot/provenance. Record reader UTC time and artifact
   digest. Confirm feature collection time <= predicted_at, matching SHA/attempt,
   compatible model, known training cutoff and strictly earlier prior outcomes.
   Preserve this original row as canonical JSON with a SHA-256 digest.
6. Continue observing the SAME attempt until it completes naturally. Save job
   started/completed timestamps and final run metadata. Let the authenticated
   completion event trigger sync, or request POST /sync and wait for its task.
   A skipped prediction is not a reason to manufacture a new failure. Reruns are
   separate attempts and require their own queued-time observation.
7. Independently read ai_predictions joined to ai_outcomes and ai_runs on
   repository/run_id/attempt, and ai_models on model_version plus repository.
   Confirm outcome label policy and identity. Compare every original prediction
   field/digest with step 5; only outcome/verification metadata may differ.
   Check the outcome against saved GitHub completion evidence, not just the join.
8. Apply the conservative timing rules below. Keep invalid/unverifiable cases in
   the ledger with reasons, but out of prospective accuracy denominators. Store
   reports under ignored backend/reports or another approved private evidence
   location, not in a source commit. Never send observations to human-review APIs.

Independent readback query shape (bind values; never substitute SQL strings):

```sql
SELECT p.*, o.label AS actual_label, o.conclusion AS actual_conclusion,
       r.commit_sha, r.status, r.payload AS run_payload,
       m.artifact_sha256, m.trained_through, m.created_at AS model_created_at
FROM ai_predictions p
JOIN ai_runs r USING(repository, run_id, attempt)
JOIN ai_models m ON m.version=p.model_version AND m.repository=p.repository
LEFT JOIN ai_outcomes o ON o.repository=p.repository
    AND o.run_id=p.run_id AND o.attempt=p.attempt
WHERE p.repository=%s AND p.run_id=%s AND p.attempt=%s AND p.mode='shadow';
```

Use a dedicated read-only role/transaction (default_transaction_read_only=on),
explicit observation database/host/port and statement/connect timeouts. Check
exactly one row, or record a missing/duplicate result as a verification failure.
Do not reuse the application's write connection as independent verification.

## Timing integrity and evaluation rules

The service samples predicted_at BEFORE database insertion; there is no separate
database insertion/commit timestamp column. A lock/network delay could postpone
persistence past job start even if predicted_at is earlier. Current matched
status compares the supplied prediction timestamp against job start and alone
does not prove the row was committed pre-start. This remains an operational
evidence gap, not a guarantee supplied by the 212 integration tests.

For this procedure, require the independent reader to have observed the committed
row before the earliest actual job start as well as predicted_at before start,
with adequate margin for clock uncertainty. Keep the observed queued response
and attempt identity. If readback occurs only after start, clocks are uncertain,
job-start evidence is incomplete, model provenance is missing or prediction
fields change, mark the case unverifiable for the conservative prospective
sample even if the existing API reports matched. A future auditable insert/receipt
timestamp and append-only event ledger would make this easier, but are not added
here. A DB receipt timestamp still needs clock and commit-delay analysis.

Only independently evidenced, pre-start shadow rows with exact known binary
outcomes count. Exclude historical mode, cancelled/unknown outcomes, late and
unverifiable predictions. Report counts of observed runs, eligible runs, inserted
predictions and every exclusion. Keep historical 27-run evaluation, controlled
integration tests and genuine observations in separate sections/files. Do not
combine improved/earlier RCA sessions or assisted recommendations with ML scores.
Until live evidence exists, prospective prediction count for this task is zero
and prospective metrics are null. Do not change threshold/model based on these
test cases or claim production readiness from this small repository sample.

## Verification in this review

The full backend suite was rerun using the previous disposable PostgreSQL 17
test cluster bound only to 127.0.0.1:55439, database cloud_bytexl_ci_test and role
cloud_bytexl_ci, with .env loading disabled and AI_TEST_DATABASE=1. Result:
**212 passed, 0 failed, 0 skipped, 0 expected failures**. Thirty existing
joblib/NumPy deprecation warnings occurred. Tests include chronological leakage,
concurrent prediction inserts, immutability, outcome races, Gemini RCA and durable
callback/restart coverage. No new runtime code was needed for this review.

Frontend/root-package file hashes are checked before and after this task. The
real worksheet, assisted recommendations and two original RCA source hashes
are checked without rewriting them. No genuine observation was initiated and
no deployment configuration was changed. The test server is stopped after the
rerun. Any later live session must follow the approved prerequisites above.
