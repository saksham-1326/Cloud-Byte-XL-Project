# Durable CI callbacks

This implementation is local-only pending review. External callback delivery is
removed from the workflow and the sender defaults to disabled. No tunnel, public
URL, hosted service, provider call, or production database is required.

## Endpoints and authentication

- `POST /api/ci/v1/status`: mandatory `Authorization: Bearer <token>` using
  `CI_STATUS_TOKEN`, plus an explicit `CI_ALLOWED_REPOSITORIES` allowlist.
- `GET /api/ci/v1/receipts/<uuid>?repository=owner/repo`: same authentication and
  repository authorization; reads PostgreSQL rather than process memory.
- Missing token configuration returns 503; missing/wrong credentials return 401;
  a non-allowlisted repository returns 403. Authentication precedes database use.
- JSON objects must contain the exact required fields, positive integer run ID
  and attempt, full lowercase SHA, UUID delivery ID, bounded workflow name, and
  supported pipeline/stage statuses. Bodies are limited to 16 KiB.

Required payload fields: `repository`, `run_id`, `attempt`, `commit_sha`,
`delivery_id`, `workflow`, `status`, `build`, `tests`, and `docker`.
Pipeline states are SUCCESS, FAILURE, CANCELLED. Successful pipelines require all
three stages PASSED. Stage states also include FAILED, SKIPPED, CANCELLED, and the
legacy FAILED_OR_SKIPPED value.

## Explicit association

A callback cannot create its own association or choose a deployment ID. A trusted
local operator registers an already-created legacy deployment:

```powershell
backend/venv/Scripts/python.exe -m backend.ai_intelligence.cli migrate
backend/venv/Scripts/python.exe -m backend.tools.register_ci_execution --repository owner/repo --run-id 123 --attempt 1 --commit-sha <full-sha> --deployment-id 456
```

The registration function locks and checks the exact deployment's repository URL
and commit, stores its run binding, and refuses rebinding or attempt regression.
Each deployment has one bound run. Register a newer attempt explicitly before
accepting its callback. Run IDs are not verified against GitHub by this local
administration function: the operator must obtain the exact IDs from trusted
workflow metadata. The callback token is a shared repository-allowlisted
credential, not GitHub OIDC identity verification.

## Migration 005 and transaction semantics

`005_ci_callbacks.sql` adds:

- `ci_callback_executions`: repository/run primary key, unique deployment ID,
  commit SHA, current attempt, and timestamps.
- `ci_callback_receipts`: receipt UUID, globally unique delivery UUID, unique
  repository/run/attempt, exact deployment and commit, canonical payload hash,
  original validated payload, and persisted timestamp.
- A composite foreign key ensures a receipt matches its registered execution,
  deployment ID, and commit. Legacy tables are not created/altered by this
  migration. Their association is checked while their rows are locked on every
  delivery; there is no new foreign key to the separately managed legacy schema.

All deployment changes and receipt creation happen in one PostgreSQL transaction.
Per-delivery advisory locks serialize replays; execution row locks serialize
competing results and attempt registration. Lock/statement timeouts bound waits.
A successful response is constructed only after commit completes and includes
`persisted: true`, receipt ID, delivery ID, execution identity, deployment ID,
payload hash, and duplicate flag. FAILURE maps to the existing FAILED deployment
status. No globally latest deployment lookup is used by the new endpoint.

An identical delivery replay returns the same receipt without applying another
update. Changed payloads reusing a delivery ID return 409. Another delivery ID for
an already-finalized attempt returns 409. Unregistered runs return 404; a wrong
commit, unregistered newer attempt, or stale attempt returns 409. An old exact
replay may acknowledge its original receipt after a rerun; it never overwrites the
newer deployment result.

Database/commit errors return a safe 503 with `persisted: false`, meaning the
request is **not acknowledged**, not proof that an ambiguous network failure
could never have committed. Retry the same delivery ID to resolve uncertainty.
The sender validates the exact execution identity, receipt UUID, persisted boolean,
and payload digest; an arbitrary HTTP 200 is not sufficient. It uses stable UUIDv5
delivery IDs derived from repository/run/attempt, rejects redirects and embedded
credentials, uses normal HTTPS validation and no ambient proxies, bounds response
size, and never logs authentication or response bodies. No automatic retries are
introduced.

## Isolated verification

Run the complete suite with `AI_TEST_DATABASE=1`, `PYTHON_DOTENV_DISABLED=1`, and
DB_HOST=127.0.0.1, DB_NAME=cloud_bytexl_ci_test, DB_USER=cloud_bytexl_ci against a
**disposable** PostgreSQL server. The reviewed CI already supplies these settings.
Do not point tests at a development or production database.

```powershell
backend/venv/Scripts/python.exe -m pytest backend/tests/ -q
backend/venv/Scripts/python.exe -m pytest backend/tests/test_ci_durable.py::test_real_sender_http_database_readback_and_process_restart -s -q
```

Each callback database fixture creates a unique schema, migrates it twice, and
creates only the minimal legacy repositories/deployments contract inside that
schema. It removes its own schema afterward. HTTP verification starts a separate
Flask subprocess on an ephemeral literal 127.0.0.1 port with an ephemeral token,
invokes the actual sender subprocess, queries PostgreSQL through a separate
connection, terminates Flask, starts a new Flask subprocess, reads the receipt,
and replays the sender. Deployment 11 becomes SUCCESS; unrelated deployment 12
stays RECEIVED; exactly one receipt survives restart and replay.

The test-only HTTP exception requires CI_CALLBACK_TEST_LOOPBACK=1, disabled dotenv,
explicit database-test opt-in, the dedicated test database/role, and a literal
127.0.0.1 database and callback hostname. It cannot authorize public HTTP URLs.
It is set only in the isolated test subprocess environment. HTTPS/TLS delivery to
a persistent remote service is deliberately not tested or enabled.

## Compatibility and limitations

AI tables, providers, ML functionality, Gemini configuration, and frontend files
are unchanged. Existing `/api/ci/status` behavior is preserved for compatibility;
its legacy latest-deployment and nonpersistent acknowledgment semantics do not
apply to the new v1 endpoint, and it must not be used for durable delivery. The
legacy in-memory dashboard status is not automatically populated by v1 receipts.
No automatic registration from GitHub webhooks or public hosting is introduced.
Runtime credentials and URL settings are not provisioned by this change.

PR #1 was merged normally as 83d2fc4b0f957af47d68ea2b1ca316c9c0a2a2c5. Its
post-merge GitHub run 44755756074 passed all 121 existing tests and Docker checks;
its external callback skipped because configuration was absent. New callback
changes are uncommitted on codex/durable-ci-callbacks and have not run on GitHub.

## Final local checkpoint — 2026-11-20

- Complete backend regression with PostgreSQL enabled: **172 passed in 18.39s**.
- Separate real HTTP/sender/process-restart verification: **1 passed in 9.09s**.
- Actual independent SQL readback after restart and sender replay: receipt count
  **1**; deployment rows **(11, SUCCESS), (12, RECEIVED)**; same receipt UUID
  readable from the restarted Flask process; persisted acknowledgment true;
  initial and replay sender exit codes both 0.
- Wrong run/commit/attempt, changed-payload replay, concurrent duplicate and
  conflicting requests, unauthorized requests, deleted deployments, transaction
  failure, and deferred commit-time failure are covered by PostgreSQL tests.
- The SQL migration was applied through the CLI and fixture migrations were
  applied twice to verify idempotency and checksum tracking.
- `pip check`, Python compileall, YAML parsing, and official actionlint passed.
  Actionlint's optional shellcheck/pyflakes integrations were disabled.
- Credential-pattern/local-secret scans found no secret values in changed files.
- Test schemas and the disposable PostgreSQL server/data are removed after tests.
  New callback changes remain unstaged/uncommitted; no new branch push performed.

## Final review and commit-preparation checkpoint — 2026-11-20

- Full backend suite: **174 passed in 34.54s**.
- Separate populated-database upgrade and HTTP/restart checks: **2 passed in
  13.17s**. SQL readback again showed one receipt, deployment 11 SUCCESS,
  deployment 12 RECEIVED, and the same receipt after Flask restart and replay.
- The upgrade test first applies only migrations 001–004, seeds AI run/model and
  legacy deployment data, then applies 005 twice. All seeded rows and the first
  four migration checksums remain unchanged, and durable delivery works afterward.
- Review closed one malformed-input gap: unpaired Unicode surrogates in workflow
  names now return a validation error before PostgreSQL access.
- Dependency checks, Python compilation, YAML assertions, and official actionlint
  passed. The workflow includes the complete suite and no external sender step.
- All per-test callback schemas were removed; the disposable cluster is stopped
  and removed after validation. No production/development database is used.
- Remaining boundaries are unchanged: shared-token local administration, explicit
  run registration, preserved legacy endpoint, and no remote HTTPS verification.
