# Historical ML audit and prospective shadow plan

Follow-up: [isolated shadow verification](SHADOW_VERIFICATION.md) fixes the split
helper defect and records 212 passing backend tests with PostgreSQL enabled.
The original audit below records the earlier state; its expected failure and
skips have been resolved in the follow-up. Historical accuracy is unchanged,
and no genuine prospective GitHub lifecycle was observed (no queued run available).

Audit date: 2026-11-21. No model implementation changes, training, deployment,
paid calls, human verification, commits or pushes were performed.

## RCA evaluation and commit readiness

Assisted recommendations remain separate from the human worksheet: 3 accept,
3 reject, 2 uncertain across eight responses on four workflows. These are
ChatGPT-assisted proposals, not independent human verification. The worksheet
still has zero completed rows and zero decisions. Human accuracy rates remain
null. The original two RCA source files still match source_manifest.json hashes.
Run #13's compiler result and the server-side origins of #23/#27's HTTP 404
remain unresolved. No review API was called. A fresh read-only PostgreSQL
connection failed with OperationalError, so current database review state could
not be independently checked; historical readbacks indicate unverified reports.

Generated backend/reports output and backend/ai_audit.json are now ignored.
Stable test inputs are explicitly retained under backend/tests/fixtures:
independent_review_inputs.json contains the minimal historical fields used by
package tests, exact diagnosis strings, report IDs and evidence; it is not a
completed review. The tests no longer depend on local generated reports.

Proposed focused evaluation commit (not created; see final preparation scopes):

- .gitignore and the RCA README section.
- backend/ai_intelligence/review_metrics.py.
- backend/tools/prepare_independent_review.py, review_guide.py,
  assisted_rca_recommendations.py.
- backend/tests/test_review_metrics.py, test_independent_review_package.py,
  test_assisted_rca_recommendations.py, fixtures/independent_review_inputs.json.

Proposed title: `test(rca): add reproducible assisted evaluation tooling`.
Exclude all frontend, root package files, generated reports and model artifacts.
Keep the ML replay tool, audit tests, historical ML fixture, this audit and ML
README paragraph for a separate review scope. If preparing only the focused
RCA commit, select README hunks accordingly. Do not use git add . or git add -A.
Approval is still required before any commit or push. No approval is requested
to make major ML changes: this task stops at audit and planning.

## Implemented architecture

`collector.synchronize` fetches real GitHub runs and all attempts, job metadata,
failed-job logs and commit-SHA workflow snapshots. It persists them in ai_runs,
ai_jobs, ai_steps, ai_snapshots and ai_outcomes; no synchronization was invoked.
Historical collection includes observed results, but prediction features use a
separate explicit allowlist. Completion is inferred from completed job metadata.

`ml.features` uses head-commit changed-file counts, additions/deletions, dependency,
Docker and workflow-change indicators, workflow availability/line count, event,
workflow identity and UTC hour/day. It also uses prior same-workflow outcomes,
failure streak/rate and durations only for runs completed strictly before the
feature timestamp. Target run, same-commit siblings, other workflows and unknown
outcomes are excluded. History retries are deduplicated by run ID using the
latest attempt whose completion was already available. Prior durations are
legitimate history features, not the target's completed duration. No target logs,
jobs, final result, error details or completed duration enter the allowlist.

`ml.train` admits labeled first attempts with completion timestamps and matching
historical snapshots. It builds a chronological 60/20/20 split with cross-partition
commit purging and completion-time purging. A train-only DictVectorizer and
StandardScaler feed DummyClassifier(prior), balanced logistic regression and a
balanced random forest. Validation F1 selects thresholds; validation F1 then
Brier score selects the candidate. Test rows are untouched by this selection.
Insufficient samples/class diversity return insufficient_data. Experimental
artifacts are server-generated joblib files with SHA-256 checks on normal loading.

`IntelligenceService.predict` accepts only a currently queued, outcome-free run
read from GitHub. It loads a compatible experimental model, checks training
cutoff, collects features, predicts, re-reads run state and saves only if still
queued with the same SHA and attempt. It stores model version, probability,
threshold, class, feature/provenance snapshot and prediction timestamp. It does
not require an LLM. POST /api/ai/v1/predictions queues the operation; GET returns
records. POST /train queues training. Signed allowlisted workflow_run webhooks
enqueue observe tasks; completed events synchronize outcomes. The durable task
worker supports this flow, but event delivery/worker uptime have not been
demonstrated here.

Migrations 001-003 separate ai_models, ai_features, ai_predictions, ai_outcomes
and ai_shadow_events. Shadow predictions have a unique repository/run/attempt
index; inserts use ON CONFLICT DO NOTHING. Backtests are keyed separately by
model version and explicitly labeled historical_backtest. Outcome collection
updates verification_status, not the original probability, class, model version
or feature snapshot. These are application guarantees, not a database trigger
preventing an administrator from editing records. GET evaluation includes only
shadow predictions with matched timing and a known actual label; prediction
retrieval is limited to the latest 500 rows, so it is not an unlimited audit.

## Actual saved historical measurements

Source: backend/reports/model_evaluation.json, experiment dated
2026-11-11T04:34:23.468930+00:00, feature version prequeue-v2-utc-standardized.
Saved collection summary: 27 unique runs, 28 attempts. Eligible dataset: 27 first
attempts, 21 successes and 6 failures. The later attempt of run #27 was excluded.
An earlier ai_audit.json lists only 5 failures; do not silently reconcile distinct
snapshots into a new dataset. Current database inventory is unavailable.

| Partition | Runs | Success | Failure |
| --- | ---: | ---: | ---: |
| Train | 16 | 13 | 3 |
| Validation | 5 | 4 | 1 |
| Test | 6 | 4 | 2 |

Class counts are recovered from the saved overall class counts and validation/
test confusion matrices. Training run IDs/features are not available in this
file. This is not a fresh extraction or complete retraining reproduction.

| Historical test measurement | Selected logistic | Dummy prior |
| --- | ---: | ---: |
| Test runs | 6 | 6 |
| Threshold | 0.5 | 0.5 |
| Accuracy | 0.5 | 0.6666666667 |
| Precision | 0 | 0 |
| Recall | 0 | 0 |
| F1 | 0 | 0 |
| PR-AUC (average precision) | 0.3333333333 | 0.3333333333 |
| Confusion matrix [[TN, FP], [FN, TP]] | [[3, 1], [2, 0]] | [[4, 0], [2, 0]] |

Precision uses zero_division=0; no model correctly identified a failure.
Average precision is defined here because test labels contain both classes.
The random forest's saved test accuracy is also 4/6, recall/F1 zero; its
probabilities are not available in the saved backtest, so those metrics are
historical reported values, not independently replayed comparator predictions.

Reproduce the selected metrics and DummyClassifier prior baseline without
network, database writes, training or deserializing models:

```powershell
backend/venv/Scripts/python.exe -m backend.tools.replay_historical_ml
```

Output: ignored backend/reports/historical_ml_replay.json, including input hash
and explicit replay limitations. The dummy is fitted only from recovered
aggregate counts (13 success, 3 failure), producing constant probability 3/16;
no executions are fabricated or added. Regression tests use a frozen copy of
the original experiment at tests/fixtures/historical_ml_evaluation.json.

The trusted local first-party artifact 55ef22a1-2f30-47f2-95d8-bf12efaf6463.joblib
was inspected read-only and reproduced all six saved probabilities exactly.
Its SHA-256 is 075d37741200bb9aaf8939fd92ee621d5fe445a11842359ba443c3ad348660a7.
This locally computed digest is not fresh database-backed artifact authentication.
A second local joblib artifact exists but was not evaluated: its training record
could not be fetched. Neither artifact is proposed for commit.

## Why failures were missed

The two observed false negatives were #23 (run 33851582532, p=0.1906690766)
and #27 (41589239366, p=6.8721922178e-47), both below the saved 0.5 threshold.
#27's largest logistic contributions are additions -58.12, deletions -38.97,
and changed_files -6.81 log-odds. These explain the extreme model score, not
the real workflow failure. #23 has negative workflow-change and hour effects.

Inference: the tiny dataset allowed spurious correlations with commit size,
time and workflow structure. Validation contained only one failure: its perfect
F1 cannot support reliable candidate/threshold selection. The scalar workflow
features do not understand an explicit exit command, and none observes runtime
callback/tunnel health. Observed 404 failures can occur without a revealing code
change. Whether extreme #27 features are outside the original training range
requires the missing training rows; do not claim verified distribution shift.
There is no evidence that raising failure probabilities or tuning on these six
test rows would generalize. Model fitting is implemented; reliable prediction,
calibration and production readiness are not established.

## Leakage assessment and outstanding defect

Deterministic checks confirm target outcomes/durations/errors/logs do not change
features; history that completes at or after prediction time is excluded; future
retries do not replace an available earlier attempt; normal partitions purge
outcomes overlapping the next partition. Train-only preprocessing is implemented.
Snapshot SHA validation prevents using the current main branch configuration.
Head-commit diffs are not full pull-request diffs. Original snapshot availability
and historical split membership cannot be established without raw records.

Known defect, documented by a strict expected-failure regression test: if
same-commit purging removes all validation rows, temporal_split does not purge
training outcomes against first test creation time. The current train function
then refuses fitting because validation is too small, so this path does not
produce a fitted model today. The saved experiment had five validation rows.
Nevertheless, the split helper must be fixed before changing fit admission or
reusing it. Plan: choose the earliest surviving validation/test creation cutoff
and purge training completion times against it, including ties and long-running
jobs. Do not remove the expected-failure marker until the corrected invariant
passes. No ml.py change was made during this audit.

## Prospective shadow readiness and implementation plan

The core queued-run flow and immutable insert behavior exist; genuine prospective
performance is not verified. The saved live verification artifact reports zero
live predictions. Current counts cannot be queried. A manual request or signed
webhook must arrive while a run is still queued; immediate starts and serial
worker delays can cause legitimate skips. Do not fabricate delays or failures
to improve model scores or label a retrospective backtest prospective.

1. Recover read-only database connectivity. Export versioned raw run/snapshot
   inventories and original prediction metadata with hashes and secret-safe
   provenance. Reproduce the chronological fit in an isolated offline store
   with no application database writes; keep the test set frozen.
2. Fix the empty-validation split invariant with the regression test. Verify
   completion cutoffs after all purges. Keep feature/version compatibility
   explicit if semantics change; do not tune against the saved test outcomes.
3. Exercise the existing queued-run path and outcome join using an isolated
   PostgreSQL test database. Confirm duplicate events preserve the original
   probability, timestamp and features. Run the currently skipped persistence,
   callback/restart and integrity tests before claiming integration readiness.
4. Preserve the final queued-state recheck, but treat it as a best-effort check:
   a run can start after this read and before insertion. The later outcome
   reconciliation must keep predictions at/after the earliest actual job start
   invalid and out of prospective metrics. Preserve original rows and explain
   the invalidation. Require reliable actual-start evidence; missing or ambiguous
   timing must remain unverifiable. Current fallback run_started_at may be less
   precise than job starts and needs explicit validation.
5. Store feature-collection and persisted prediction times distinctly; keep the
   model version, threshold, SHA, attempt and training/selection cutoff auditable.
   Existing features use the earlier collection timestamp while predicted_at
   is recorded before database insertion. Check clock skew and persistence
   semantics; record server receipt time if stronger audit guarantees are needed.
6. Use existing signed allowlisted event delivery or an approved bounded polling
   observer; no public callback URL is introduced by this plan. Monitor delivery,
   queue delay, skipped runs and timing-invalid records. Confirm the worker is
   running and measure coverage on naturally occurring workflows.
7. Persist outcomes separately, then join exact repository/run/attempt. Evaluate
   only legitimately pre-start predictions with known binary outcomes, compare
   against a frozen dummy prior, and report sample sizes and class counts.
   Aggregate beyond the current 500-row retrieval limit for a durable audit.
8. Collect substantially more natural failures across time before reconsidering
   model complexity or calibration. Diagnose unsupported runtime failure modes
   honestly; consider only features demonstrated available at collection time.
   Prospective accuracy remains unknown until those outcomes exist.

## Validation and unchanged scope

Command: backend/venv/Scripts/python.exe -m pytest backend/tests -q

Result: 172 passed, 17 skipped, 1 expected failure. The skips require explicit
isolated PostgreSQL integration opt-in; they were not run against the application
database. External urllib calls are blocked by the test fixture. The expected
failure is the documented empty-validation split defect, not a hidden pass.
The prior 174-test CI checkpoint is historical, not a claim that this local run
executed the same integration checks. RCA-only scope is separately testable.

No Gemini provider, prediction service, ML model implementation, Flask API,
database schema, callback code or frontend was changed. All pre-existing frontend
and Figma work is outside the proposed commit. Stop here for review and approval
of the focused RCA commit and the prospective implementation plan.
