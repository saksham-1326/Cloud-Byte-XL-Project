# Isolated shadow lifecycle verification

Verified 2026-11-21 on branch codex/independent-rca-review. No commit, push,
merge, production/development database connection, paid API call or live Gemini
call was made. Existing trained model artifacts were not retrained or replaced.

## Split correctness fix

Previously temporal_split purged training completion times only when validation
survived the other purges. If validation became empty, training could include
outcomes completed after the first test prediction time. Current training
already refused to fit empty validation, but the helper invariant was wrong.

The cutoff is now the earliest creation time among surviving validation/test
partitions. Training rows completing at or after that time are removed. Empty
input stays safe; insufficient partitions still return insufficient_data from
training. Existing validation-to-test purging is preserved. The original strict
expected-failure regression now passes with its assertion unchanged. Added a
boundary regression for completion exactly at the cutoff. Feature tests continue
to exclude target logs, outcomes and completed duration and unavailable history.
Feature semantics are unchanged, so the feature version remains unchanged.

## Persistence and race fixes

- The service rejects missing commit SHA or inconsistent requested run/attempt
  before feature collection. Its final recheck also validates the returned run ID.
- Run upserts reject mismatched commit SHA and stale transitions from completed
  to noncompleted. Rejected updates return before writing jobs or outcomes.
- Prediction insertion selects only a persisted queued, outcome-free run with
  matching SHA, exact repository/run/attempt and a model belonging to that
  repository. It locks the run row through insertion, coordinating with outcome
  updates so completion cannot overlook an uncommitted prediction.
- Concurrent duplicates use the existing unique shadow index and ON CONFLICT
  DO NOTHING. Original probability, timestamp, model, features, threshold and
  class are never updated by outcome reconciliation or duplicate insertion.
- If a final GitHub recheck is stale but the database already holds completed
  state, insertion is skipped. No record is falsely reported as already_predicted
  unless the original shadow row actually exists.
- Timing reconciliation remains necessary: GitHub can start after the last
  state check. A prediction at/after the observed job start is invalid_timing;
  absent start evidence remains unverifiable_timing. Neither contributes to
  prospective evaluation. These changes do not claim an atomic cross-service
  GitHub/PostgreSQL transaction or database-wide administrator immutability.

No schema/migration, Flask route contract, Gemini provider or callback code was
changed. Existing isolated callback persistence and restart tests passed.

## Disposable database and test setup

A new PostgreSQL 17 cluster was initialized at the ignored local path
backend/reports/shadow_pg_check/data-isolated and bound only to 127.0.0.1:55439.
The port was checked unused first. initdb created a dedicated test-only role
cloud_bytexl_ci; createdb created cloud_bytexl_ci_test. SCRAM authentication used
the existing public isolated test password, not a personal credential. No .env
database configuration was loaded. Startup and loopback test execution required
sandbox network permission. Docker was unavailable; native PostgreSQL was used.
An initial sandboxed initdb attempt stalled and was cancelled; only the new
isolated cluster was started. Stop the cluster with pg_ctl after testing.
The disposable server was stopped successfully after all verification runs.

Reproduction, using a NEW cluster and a free loopback port 55439:

```powershell
# Initialize/start an isolated PostgreSQL cluster before running this block.
# Never point these tests at an existing personal or production database.
$env:AI_TEST_DATABASE='1'
$env:DB_HOST='127.0.0.1'
$env:DB_PORT='55439'
$env:DB_NAME='cloud_bytexl_ci_test'
$env:DB_USER='cloud_bytexl_ci'
$env:DB_PASSWORD='isolated-ci-only'
$env:PYTHON_DOTENV_DISABLED='1'
backend/venv/Scripts/python.exe -m pytest backend/tests -q
```

conftest additionally validates the opt-in database name, role and loopback host
and blocks unmocked urllib HTTP calls. Individual tests use unique synthetic
repositories or disposable schemas and clean up their rows. Review API regression
tests exercise only synthetic isolated records, not real RCA reports or reviewers.
The real human worksheet and assisted recommendation files are not changed.

## What the lifecycle tests establish

test_shadow_postgresql.py uses a controlled GitHub client with real PostgreSQL,
real Store/IntelligenceService and a temporary test-only sklearn model artifact.
It verifies queued eligibility, SHA-checked pre-outcome features, probability and
metadata persistence, separately recorded completion, correct outcome joins,
duplicates, repeated attempts, concurrent requests, rollback after database
constraint errors and immutability of original prediction fields. A deliberate
transaction overlap verifies completion reconciles a prediction after waiting
for its transaction. Late, completed and missing-timing cases are excluded.

These simulated workflow executions are deterministic test inputs, not new
historical cases, prospective production predictions or accuracy measurements.
The current trained application model is not replaced by the temporary test model.

A separate read-only GitHub listing returned 35 runs and zero currently queued
runs. No workflow was dispatched and no artificial failure was created. Thus a
genuine newly queued-to-completed GitHub lifecycle could not be observed in this
session. Do not describe isolated verification as real prospective accuracy.

## Test results and remaining work

Complete backend suite: **212 passed, 0 failed, 0 skipped, 0 expected failures**.
ML-specific regression suite: **32 passed**. Existing RCA regression suite:
**68 passed**. Focused PostgreSQL/shadow/callback suite: **60 passed, 0 failed,
0 skipped**.
Full-suite warnings: 30 joblib/NumPy deprecation warnings from temporary model
serialization; no test failures. All original 17 database-dependent checks ran
instead of skipping. Historical model performance remains unchanged: 27 eligible
runs, six test rows, both actual failures missed. No accuracy improvement is claimed.

Next, observe a naturally occurring queued workflow using the existing trained
model and an approved isolated database populated with authentic, versioned model
metadata and pre-outcome history. Preserve the prediction, collect its actual
completion, and check timing before including it in any prospective metrics.
Event/worker delivery coverage, clock skew, model calibration, small-sample
uncertainty and the 500-row evaluation retrieval limit remain open limitations.
