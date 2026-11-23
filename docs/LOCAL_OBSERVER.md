# Local GitHub Actions observer

Implemented for offline verification on 2026-11-22. **No live session has been
started.** This is experimental observation tooling, not production-ready ML or
proof of external event delivery. Main's earlier 212-test result remains a
historical checkpoint, not a new prospective score.

## Architecture and boundaries

`python -m backend.tools.observe_actions` is a thin opt-in runner. It uses the
existing ActionsClient API shape, IntelligenceService.predict, existing Store
prediction insertion and a new metadata-only collector.synchronize_attempt
adapter calling the existing transactional save_run. No second model, feature
engine, prediction table or model training path is introduced. No migrations
or dependencies are added. Existing HTTP APIs/workers remain unchanged.

The runner does not import backend.app, load .env, bind Flask, dispatch workflows,
enable callbacks or call a Gemini/OpenAI provider. It uses outbound HTTPS GETs
only and explicit loopback PostgreSQL connections. It cannot discover a personal
database from the normal application's default configuration. The API/task
worker is not needed for this direct-service runner.

Only the `--run` flag starts observation. `--dry-run` validates configuration
locally without creating a ledger, opening database/network connections or
submitting predictions. It does not establish credential permissions, authentic
model provenance or actual clock accuracy. No live mode is approved in this task.

## Prerequisites

1. A repository-limited credential with Actions read and Contents read. Reads
   include exact run attempts/jobs plus commit files and workflow configuration.
   Do not use a publishing token unnecessarily. The runner never sends GitHub
   mutations; it stops on permission/authentication failures. Public metadata may
   permit unauthenticated reads, but this runner deliberately requires a token.
2. A dedicated primary PostgreSQL observation database on loopback, separate
   from development/deployment databases and disposable integration test data.
   CLI database names must start with `cloud_bytexl_observation_`; role names
   must start with `cloud_bytexl_observer_`. Writer and reader must be distinct
   users on the same explicitly named host, port and database. Service files,
   implicit/default database selection, remote hosts and extra DSN options are
   rejected. Replicas are rejected. Existing migrations must be applied by an
   administrator before running; the observer does not migrate or provision.
  An explicit loopback hostaddr also blocks redirection by inherited PGHOSTADDR
  settings. Database name, current role and primary-server state are checked.
3. Authenticated original model registry metadata, original artifact/version,
   current feature version, original threshold/training cutoff and expected
   artifact SHA-256. Pin an existing version and digest explicitly. The normal
   model path/hash validation still runs. Missing/wrong models fail closed;
   there is no fallback, retraining or replacement. Import authentic pre-outcome
   history through a separately reviewed preparation step. An empty history can
   change features; the observer does not silently reconstruct historical data.
4. Local evidence storage under ignored backend/reports/observations, sufficient
   disk space for fsync, and a single writer per ledger. Never store credentials
   in commands, URLs, ledger data, Git commits or screenshots.

Suggested least-privilege grants, applied by an administrator to a dedicated
observation DB only (substitute role names; do not run against personal data):

```sql
GRANT USAGE ON SCHEMA public TO cloud_bytexl_observer_writer, cloud_bytexl_observer_reader;
GRANT SELECT ON ai_models,ai_runs,ai_jobs,ai_steps,ai_predictions,ai_outcomes,ai_shadow_events
  TO cloud_bytexl_observer_writer;
GRANT INSERT,UPDATE ON ai_runs,ai_jobs,ai_steps,ai_outcomes,ai_shadow_events
  TO cloud_bytexl_observer_writer;
GRANT INSERT ON ai_predictions TO cloud_bytexl_observer_writer;
GRANT UPDATE(verification_status) ON ai_predictions TO cloud_bytexl_observer_writer;
GRANT SELECT ON ai_runs,ai_models,ai_predictions,ai_outcomes TO cloud_bytexl_observer_reader;
```

Also grant CONNECT to that dedicated database. Neither observer role should own
the tables or be a superuser; do not grant writer UPDATE on original prediction
fields. Do not grant INSERT/UPDATE on ai_models, review tables or task tables.
Reader connections independently enforce read-only transactions. Tests use
disposable roles and temporary test models; those are not live observations.

## Safe configuration example

Replace placeholders using approved credentials/model metadata. Secrets are read
only from process environment; the runner intentionally does not load .env.
Do not paste real values into checked-in files or shell commands being recorded.
Use the local approved secret-loading method instead of literal secrets below.

```powershell
$env:GITHUB_TOKEN='<read-only-token>'
$env:OBSERVER_WRITER_DSN='host=127.0.0.1 port=55440 dbname=cloud_bytexl_observation_session user=cloud_bytexl_observer_writer password=<writer-password>'
$env:OBSERVER_READER_DSN='host=127.0.0.1 port=55440 dbname=cloud_bytexl_observation_session user=cloud_bytexl_observer_reader password=<reader-password>'
$observerArgs=@(
  '--repository','saksham-1326/cloud-byte-xl-project',
  '--allow-repository','saksham-1326/cloud-byte-xl-project',
  '--model-version','<original-model-UUID>',
  '--model-sha256','<original-64-character-lowercase-digest>',
  '--ledger','backend/reports/observations/approved-session.jsonl',
  '--interval','15','--duration-seconds','900',
  '--max-requests','300','--max-polls','60'
)
backend/venv/Scripts/python.exe -m backend.tools.observe_actions --dry-run @observerArgs
```

Wrong placeholders are rejected, not silently replaced. Do not point the runner
at the disposable regression database. The example's observation DB is not
created by this task. Default bounds are 15 seconds, 900 seconds total, 300
reserved HTTP requests and 60 total polls; minimum interval is five seconds.

Only after separate session approval, the start command is the same invocation
with `--run` in place of `--dry-run`. Ctrl+C/SIGTERM requests shutdown: no new
requests/inserts are initiated after cancellation is noticed; an in-flight
socket operation can take up to its timeout to return. Any already committed
prediction is preserved and independently read back where execution permits.
Shutdown fsyncs a safe status event and closes the idle service executor/ledger.
No server window or background daemon is started automatically.

## Rate limits, retries and actual request accounting

The counter includes discovery pages, exact attempt/job reads, service rechecks,
commit/workflow snapshot pages and retries. Conditional requests count against
the local request budget even if GitHub does not charge their primary quota.
A reservation is fsynced before issuing the GET; a crash/cancellation between
reservation and network I/O can conservatively overcount, never renew budget.
Rate-limit response headers and request IDs are retained without authentication
headers. Shared credential use means header quota deltas cannot be attributed
solely to this observer.

The 240/hour estimate describes only a single 15-second discovery GET. One new
candidate normally adds at least two precheck GETs, two service run checks,
commit pagination and workflow contents; completion adds exact attempt/job
reads and scoped reconciliation rereads. It is not a fixed 240-call workload.

The shared GET client enforces time/request bounds, a 5 MB response limit,
timeouts, cancellation, bounded retries and positive jitter. It handles 304
only for discovery; exact attempt checks never use cached state. Following
pagination is restricted to the same GitHub origin/repository; incomplete or
capped results fail closed. Binary logs and redirects are not needed/allowed.
Retry-After/reset headers are respected; secondary rate limits wait at least
a minute. A deadline/budget can stop before a retry, never shorten a server's
delay and retry early. Network/5xx errors have bounded exponential backoff.
Provider X-Poll-Interval is honored per resource. Rate cooldowns survive both
retry exhaustion and restarts; the next poll cannot bypass a prior Retry-After.
Authentication and permission errors do not spin or retry indefinitely.

Typical authenticated PAT primary quota is 5,000/hour, but credential types,
shared usage and secondary limits differ. Follow the returned headers, not an
assumed remaining quota. The observer performs no live rate-limit probe during
dry-run. References: [GitHub rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
and [conditional requests](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#use-conditional-requests).

## Discovery, reruns, restart and outcomes

Discovery filters queued status, not original creation time. A rerun on an old
run ID is a new repository/run_id/run_attempt key. Every candidate gets an exact
attempt read and paginated job-state precheck; service.predict rereads state
again. Missing/mismatched repository, identity, SHA or job association cannot
request an accepted prediction. A known started job precludes new inference;
an empty job list is only partial evidence, never proof of pre-start timing.

The existing service only supports queued, null-outcome runs. requested, waiting,
pending and in_progress states are skipped. An old rerun whose original created_at
precedes the pinned model training cutoff is also conservatively skipped by the
existing service guard. The observer does not manufacture a newer creation date
or relax that model cutoff. Duplicate results, separate concurrent observers
and process restarts reuse the existing unique shadow index.

Each ledger has an OS file lock, append-only JSONL with SHA-256 chaining, and
fsync on every record. Startup rejects partial/corrupt chains instead of
truncating/repairing original evidence. Recovery restores pending exact attempts
and the FIRST independent readback; it cannot invent an earlier receipt after
a crash. The original session deadline, poll count and request reservations are
retained. Config/model/database fingerprint changes cannot silently resume the
same session. Separate observers must use separate ledgers.

Completion is followed only for previously seen/pending exact attempts, using
the new metadata-only scoped collector and existing transactional save_run.
No logs, full-history collection or model updates occur on this path. A fresh
read-only connection verifies the outcome and compares the original prediction
digest (ID/model/probability/threshold/class/features/time). Changed fields or
wrong associations are excluded/unverifiable, not overwritten.

Bounds can expire before a long workflow completes. Pending attempts remain in
the ledger; an expired session does not automatically renew itself. A separately
approved follow-up/evidence reconciliation is required. Do not create a new
late readback and claim it was the missing pre-start receipt. Late/finished
executions cannot be backfilled as new prospective predictions.

## Timing evidence and eligibility

The ledger records session profile and kind, repository/run/attempt, sanitized
GitHub run/jobs/timestamps, UTC observer times, HTTP result/rate metadata,
prediction request/result, original model/digest and feature snapshot references,
original probability, independent readback, outcome reconciliation and final
inclusion/exclusion reason. Independent readback uses a fresh connection under
the separate SELECT-only role. `database_commit_at` is explicitly null: neither
the schema nor a query can reconstruct an original transaction commit time.
Independent visibility completion is a conservative persistence upper bound.

No clock error is assumed zero. Without supplied valid clock evidence, all
otherwise valid outcomes are unverifiable. To allow qualification, supply:

```text
--clock-uncertainty-seconds <conservative-bound>
--clock-evidence-ref <approved-local-clock-evidence.json>
```

That JSON must contain measured_at and valid_until (timezone-aware ISO times),
numeric max_error_seconds and a nonempty method. It must cover the entire
session and the configured bound must not understate it. The ledger pins its
digest, method and validity; expired evidence cannot qualify an outcome.
These checks validate an operator-supplied measurement, not the truth of a
fabricated measurement. Approve its source independently; no external clock
probe is made automatically. Local ledger hashes are not third-party signatures.

Qualification requires BOTH original predicted_at and independent readback
completion, plus clock error and at least one second of GitHub timestamp
precision margin, to precede the earliest actual executed-job start for the
EXACT attempt. All non-skipped jobs need consistent start/completion metadata.
Known success/failure outcome and unchanged pinned prediction provenance are
also required. Missing, future/inconsistent, ambiguous or late evidence remains
unverifiable/excluded. Store matched status alone is insufficient.

The label is `eligible_prestart` evidence, never human verification or measured
production accuracy. Controlled tests use session_kind=controlled_test; their
eligible fixtures are not real prospective results. No accuracy is automatically
calculated. Real performance remains unknown until approved natural observations
exist in a distinct evidence set.

## Offline verification and approval boundary

Tests mock every GitHub response and use disposable PostgreSQL 17. They cover
queued/running/completed/short-window runs, old reruns, duplicate/concurrent
observers, restart, pinned model/SHA/repository guards, readback failure, clock
uncertainty, incomplete job timing, early starts, rollback, immutable predictions,
rate/permission/outage/pagination/cache behavior, redaction, offline dry-run and
graceful shutdown. Temporary controlled model fixtures are not replacements for
the saved trained model. Full-suite results are reported in README/the task report.

Final complete backend run: **278 passed, 0 failed, 0 skipped, 0 expected failures**;
68 joblib/NumPy deprecation warnings. New observer coverage comprises **35 offline
tests and 26 PostgreSQL tests**. Least-privilege writer grants were exercised:
prediction/outcome flow succeeds while model/probability updates are denied.
Actual CLI configuration-only dry-run was exercised with placeholder inputs.
No live GitHub request or real prediction was submitted. The disposable server
is stopped after verification; no observation database/roles are provisioned.

Before a real session: approve the implementation and its isolated tests, then
approve the exact repository, read-only GitHub credential source, authenticated
model metadata/digest, dedicated DB roles, clock evidence, ledger location,
interval, duration and total request budget. Provision/authenticate those inputs
separately, run configuration-only dry-run, then explicitly authorize --run.
No commit, push, deployment, public webhook, workflow trigger or live monitoring
is part of this implementation task.
