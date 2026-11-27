# AI Intelligence: setup, demonstration, and verification

## Final live verification — 2026-11-27

A genuine failed `Lint frontend` step exposed an evidence-rule defect: ESLint source coordinates and its `1 problem (1 error, 0 warnings)` summary were counted as pytest errors. New analyses classify explicit linter diagnostics as `lint_failure`, preserve the diagnostic citations, and recommend correcting the cited lint rule. Lint evidence cannot support a provider claim that unit tests failed. Regression tests use the redacted public diagnostic from Actions run `45795104375`, attempt 1. Existing database reports and historical evaluations are preserved; previously stored `unit_test_failure` reports for this lint pattern remain historical, incorrect diagnoses until separately reviewed. The exact provider call performed before this fix is not re-counted as a post-fix provider test. See [final verification](../docs/FINAL_PROJECT_VERIFICATION.md).

## RCA reliability improvements — 2026-11-15

This checkpoint supersedes the earlier Gemini accuracy results below. Four
**fresh** generation calls to the existing configured `gemini-3.5-flash-lite`
returned four structured responses, with no provider, quota, authentication or
parsing errors. No old answer was reused as a new live response, and no model,
provider, billing, React/Figma or ML-prediction changes were made.

The extractor now records source-linked command-script echoes, observed process
exit codes, explicit exit commands, pytest summaries, compiler/import diagnostics,
HTTP errors, Docker errors and shell context. Echoed commands do not prove every
command executed. Timestamps and command frames separate primary evidence from
earlier unrelated or later cleanup/status-reporting errors. Subsequent failing
callbacks are secondary evidence; sequential failures no longer inflate the
`parallel_failures` field. Other failed jobs remain separately disclosed.

The existing category strings/API routes are preserved. The taxonomy now has
explicit diagnostic requirements: compiler/import command names and nonzero
aggregate exit codes are not compiler/dependency errors. Passing pytest plus an
unconditional nonzero exit is intentional workflow termination when no earlier
causal diagnostic exists. `insufficient_evidence` is the backward-compatible
unknown category and requires high uncertainty. Truncated or potentially tolerated
diagnostics produce an unknown result instead of an asserted unique cause.

Gemini and OpenAI share generic category/grounding instructions and a stricter
provider schema requiring failed job/step and separate secondary citations and
explanation. No expected run diagnoses or previously generated answers are sent.
Legacy response fields remain supported. Local guards check real and relevant
primary/secondary citations, metadata, category indicators, compiler/dependency
assertions, passing-test contradictions, exit/HTTP codes and test counts. Guards
reject unsupported output; they do not replace its category with ground truth.
These are bounded pattern constraints, not proof of arbitrary semantic entailment.

Before generation, expectations were frozen in
`backend/reports/rca_reliability_ground_truth.json`. #21 uses the user's independently
verified ground truth; the other cases use prior direct review of stored real logs
by the agent. These are previously examined cases, not a held-out accuracy dataset.

| Run | Fresh category and diagnosis | Independent agent assessment |
| --- | --- | --- |
| #21 | intentional_workflow_termination: pytest passed, then explicit exit 1. | Cause/category/fix correct; missing-container cleanup correctly secondary. |
| #13 | intentional_workflow_termination: explicit exit 1, no compiler diagnostic. | Primary cause/category/fix correct. Secondary statement that cleanup **step** failed is false: GitHub records success. Final guard rejects this output. |
| #23 | network_service_failure: callback HTTP 404, curl exit 22. | Primary and subsequent failed FAILURE-status callback correctly separated. |
| #27 | network_service_failure: callback HTTP 404, curl exit 22. | Primary and subsequent failed FAILURE-status callback correctly separated. |

Primary cause narratives and categories improved from 3/4 and 2/4 respectively
to **4/4 each** on these same four cases. Step identification, proposed primary
fixes and primary evidence passed for all four. Secondary accuracy and full rubric
success are **3/4**, with one unsupported secondary claim. Every primary and
secondary citation was resolved against the original normalized/redacted logs.
The cleanup-step metadata guard was added after independent review and applied
**offline to the same four raw responses**. There was no additional live call or
replacement answer. All original categories and narratives are retained.

PostgreSQL stores the original responses, input evidence, agent rubric judgments,
frozen expected outcomes, and final guard verdicts separately. All four reports
remain `unverified` by humans. #13 is operationally rejected by the final guard;
that verdict is separate from its human-verification status. Human reviewer
identity/agreement and production generalization are not claimed.

Artifacts:

- `backend/reports/rca_reliability_validation.json`: fresh call audit, original
  responses, source evidence, assessments and final guard verdicts.
- `backend/reports/rca_reliability_ground_truth.json`: pre-call expectations.
- `backend/reports/rca_reliability_assessments.json`: explicit agent judgments.
- `backend/tests/fixtures/gemini_reliability_responses.json`: four new responses
  for offline regression. The earlier response fixture remains separate.

Reproduce fresh inference only when wanted (this consumes project quota):

```powershell
backend/venv/Scripts/python.exe -m backend.tools.validate_live_rca --output-name rca_reliability_validation.json --run-numbers 21 13 23 27
```

The tool archives an existing output before a fresh evaluation, fingerprints the
instructions/schema/input and never retries provider/quota failures. `--resume`
cannot mix different prompt versions. Rubric review still follows generation.

Full backend regression with `AI_TEST_DATABASE=1`: **111 passed**, including
PostgreSQL, new extraction/grounding tests and offline replay of the old and new
responses. Regression tests make no live Gemini calls. Remaining limits include
the small, previously examined sample, bounded pattern/negation checks, absence
of human review, incomplete cross-job causal analysis and unknown server-side
reasons for HTTP 404. ML failure-prediction work remains deferred.

## Gemini live RCA validation — 2026-11-15

Gemini support is implemented alongside OpenAI; backend routes and response
contracts are preserved. `.env` is loaded by the existing backend loader, and
Gemini uses `GEMINI_API_KEY`, `RCA_PROVIDER=gemini`, and explicit `RCA_MODEL`.
The key is sent only in an HTTP header. No billing settings, tools, paid-only
models, automatic provider fallback, or automatic retry are used. HTTP 429 stops
validation. The reviewed free-tier model list is deliberately conservative.
`gemini-2.5-flash` is blocked from 2026-12-01 to avoid Google's announced
automatic routing after that cutoff.

Live results: **4 successful generation responses from gemini-3.5-flash-lite**.
The initial user-selected `gemini-2.5-flash` and subsequently authorized
`gemini-2.5-flash-lite` each returned HTTP 404 on generation, despite successful
metadata checks. Flash-Lite's error specifically says the model is unavailable
to new users. The user explicitly authorized both model changes. Session totals:
6 generation attempts (4 successes, 2 HTTP 404 errors), 3 successful metadata
checks, no quota/authentication/parsing errors. Model metadata does not expose
project billing tier or remaining free quota; generation success establishes
current access, not an independently authenticated billing status.

Run #21 was the first generation request for each selected model. Prompts contained
only redacted extracted evidence and generic instructions/schema, never known
diagnoses or local rule categories. No output was coached or retried to improve
its grade. The same model checkpoint resumed after #21's category rejection
without another call for that case.

| Run | Actual Gemini diagnosis | Agent comparison |
| --- | --- | --- |
| #21 | Pytest passed; subsequent explicit `exit 1` caused failure. Fix: remove it. Category: `unit_test_failure`. | Narrative/fix correct; category wrong and rejected by existing guard. |
| #13 | Claimed py_compile failed and advised fixing syntax. | Wrong: explicit `exit 1` appears in the failed frame, with no syntax diagnostic. Category rejected; syntax claim unsupported. |
| #23 | Status-update POST received HTTP 404; curl --fail exited 22. | Cause, citations, and diagnostic fix supported. Underlying server-side reason remains unknown. |
| #27 | Status-update POST received HTTP 404; curl exited 22. | Cause, citations, and diagnostic fix supported. Underlying server-side reason remains unknown. |

Direct log comparison: cause narrative 3/4, category 2/4, failed-step name 4/4,
recommended fix 3/4, evidence support 3/4. Citation IDs resolve to real primary
logs in all 4 responses. Two responses contain unsupported classification/cause
claims. The model omitted secondary errors in all four narratives. The existing
extractor retains Docker cleanup errors for #21/#13, but omits subsequent failed
status-update calls for #23/#27 and calls multiple failed steps `parallel_failures`
even when sequential. Step fields and secondary_errors in application reports
are deterministic extraction, not independently model-generated structured fields.

These are **agent assessments**, not human verification or production accuracy.
Only #21 uses the user's supplied independently verified ground truth; other
cases were compared directly with stored real logs by the agent. Raw model
responses, guard failures, rubric judgments, ground-truth provenance, and source
evidence are stored separately in PostgreSQL. All AI reports remain `unverified`;
no human reviewer identity or agreement was fabricated. Four assessments were
read back and all cited evidence IDs checked against the original primary logs.
#4/#8 were skipped for model calls because their logs are expired.

Artifacts:

- `backend/reports/live_rca_validation.json`: current complete evaluation audit.
- `backend/reports/gemini_flash_access_failure.json`: first model's HTTP 404.
- `backend/reports/gemini_flash_lite_access_failure.json`: second model's HTTP 404.
- `backend/tests/fixtures/gemini_live_rca_cases.json`: four actual model responses
  for offline guard regression; replaying them makes no API calls.

Final backend regression with `AI_TEST_DATABASE=1`: **75 passed**. This includes
PostgreSQL persistence, Gemini error/secret handling, blind outbound requests,
provider selection, and replay of all four real responses through existing guards.

The live exercise is evaluated **with failures**, not certified as accurate RCA.
No more model calls were made after the four evaluated responses. Further quality
improvements and independent human review remain necessary. ML prediction
verification, React changes, and Figma integration remain deferred.

## Live RCA checkpoint — 2026-11-14

Live RCA validation remains **blocked**, not complete: the loaded configuration
has no `OPENAI_API_KEY`, `RCA_MODEL`, or `RCA_PROVIDER=openai`. Actual LLM calls:
**0**; model: **none**. No ML failure-prediction verification was undertaken.

The provider input now contains only extracted log evidence, with no rule-based
diagnosis or known expected category. Local citation/category checks still run
after generation. Failed-command context (including curl and py_compile) is
preserved. Tests verify the actual outbound request excludes the rule diagnosis
and that provider failures propagate rather than becoming apparent AI successes.

PostgreSQL contains cached real failed-job logs for #13, #21, #23, and #27.
Logs for #4 and #8 are marked expired. Inspection independently confirms:

- #21: `Run tests`; explicit `exit 1` at line 204, `1 passed` at 222,
  exit code 1 at 223; missing Docker container at 273 is later cleanup.
- #13: `Check Python syntax`; py_compile command at 178–179, explicit
  `exit 1` at 180 and exit code 1 at 190; no syntax diagnostic in that frame.
- #23 and #27: `Update CI status - SUCCESS`; curl POST to CI_STATUS_URL,
  HTTP 404 at lines 419 and 435 respectively, then exit code 22.
  The underlying reason for HTTP 404 is unproven. Later failure-status updates
  also fail; they must not replace the earliest failing step as the primary cause.

`backend/reports/live_rca_validation.json` records configuration and per-case
blockers. Six new reports/checkpoints were saved and read back in PostgreSQL;
their engine is explicitly `evidence_rules` and verification remains `unverified`.
Review criteria are null because no live diagnosis exists to grade. These are
preflight records, not measured LLM accuracy or completed AI verification.

After configuring the provider in backend/.env, run:

```powershell
backend/venv/Scripts/python.exe -m backend.tools.validate_live_rca
```

The tool invokes #21 first, records structured provider results and attempted
calls, stores accepted reports, and stops on a provider/validation error. A live
execution still requires independent review of step, primary cause, citations,
fix, and unsupported claims before declaring this phase complete. It uses cached
real logs and does not refresh GitHub history, train models, or predict failures.

Validation: full backend suite with `AI_TEST_DATABASE=1`: **54 passed**.
Frontend/Figma files were not modified during this checkpoint.

## Backend-first phase checkpoint — 2026-11-11

Implementation order is Actions history/log collection, real-log RCA, ML prediction,
actual-outcome verification, independently verified RCA evaluation, Flask/PostgreSQL
integration, then automated tests/documentation. Validate one phase before advancing.
Preserve the current frontend; Figma ZIP integration and redesign are deferred until
backend AI functionality has been verified.

Inspection found existing implementations for all seven areas below; their presence
does not establish live AI accuracy or production readiness. This checkpoint addresses
the earliest discovered incomplete behavior in phase 1:

- Completed attempts with empty cached jobs or unfinished cached jobs are retried.
- An empty jobs response for a completed attempt emits a warning and remains retryable.
  This can also occur for a legitimate jobless workflow, so no missing cause is inferred.
- Unfinished jobs have `pending` log status rather than a success-log status.
- Complete cached attempts still skip repeat collection.

Validation: `backend/venv/Scripts/python.exe -m pytest backend/tests -q` passed
45 tests with 2 PostgreSQL tests skipped before the added regression cases. After
the changes, running the full suite with `AI_TEST_DATABASE=1` passed **51 tests**,
including PostgreSQL persistence/outcome/reviewer tests and the real-log run #21
regression. The initial sandboxed database attempt failed on local socket permissions;
the permitted retry passed. The root `.venv` lacks AI dependencies; use `backend/venv`.
Collection retry tests use mocked GitHub responses; this checkpoint did not download
fresh remote logs, generate new predictions, retrain models, or measure new accuracy.

Next phase: validate real-log RCA/provider behavior. Run #21 remains the initial real
regression case. Live LLM output, genuine future shadow predictions and their eventual
outcomes, and independently authenticated human ground truth remain unverified. The
small historical dataset cannot support production prediction claims. CI currently
installs only a dependency subset and runs the legacy test file; full AI CI coverage
remains outstanding. No frontend files were changed in this checkpoint.

This extends the existing Flask app and React shell. It does not change any remote repository, workflow, or infrastructure. All mutations are confined to the application's own PostgreSQL tables and local model artifacts.

## Run the existing application

From the project root in PowerShell:

```powershell
backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/venv/Scripts/python.exe -m backend.ai_intelligence.cli migrate
backend/venv/Scripts/python.exe backend/app.py
# In another terminal:
npm run dev --prefix frontend-app
```

The backend uses `backend/.env` regardless of the current directory. Keep actual secrets there or in the process environment; never put GitHub/LLM/database credentials in React. `backend/.env.example` lists the new settings without secret values. The pre-existing database password was moved, with explicit approval, from the source fallback into the ignored local backend environment file. DB_PASSWORD must now be configured; no password fallback remains in source. Do not copy an empty example DB password over a working setup.

Connect `https://github.com/saksham-1326/Cloud-Byte-XL-Project` through the existing repository dialog, then choose **AI Intelligence**. Click **Sync Actions history**, then **Train experimental model**. Both are persisted background tasks, not synchronous training requests. The UI polls their status. The separate AI administrator field is only for `AI_ADMIN_TOKEN`, never for a GitHub or provider key.

The CI workflow installs `backend/requirements.txt` and runs the complete backend suite with an isolated PostgreSQL 17 service. AI tests use mocks and saved fixtures; no live provider calls are required. See `backend/CI_VERIFICATION.md` for database isolation and optional authenticated callback configuration. No controlled failed Actions runs are created by this implementation.

## GitHub history and storage

- GitHub token needs repository metadata/contents and Actions read access. Public metadata may work without a token, but downloading logs can require Actions read permission.
- Pagination follows GitHub's `Link` signal, with a bounded page limit that reports truncation as an error. Rate limits return a retryable task error; no indefinite sleeps occupy request workers.
- Unique key: `(repository, run_id, attempt)`. A rerun is an additional attempt, not an additional independent training run.
- Jobs and steps use normalized foreign keys; outcomes, SHA snapshots, feature versions, predictions, model versions, RCA reports and worker tasks have separate tables.
- Sync skips complete persisted attempts with complete snapshots, retries partial snapshots/deferred log errors, and preserves immutable cached data. Missing/expired/inaccessible logs are explicit. Successful-job logs are referenced but not downloaded by default; failed-job logs are bounded to 5 MB and redacted before storage.
- Historical commit diffs and workflow configurations are fetched using each run's exact commit SHA, not current main. Commit diffs are head-commit diffs, not a reconstructed multi-commit PR diff.
- Four transactional, checksum-tracked migrations add isolated `ai_*` tables/indexes. Migrations are explicit; the application does not silently migrate during an API request.
- Logs are untrusted. The collector redacts configured secret values, common credential assignments, token patterns, private-key blocks, bearer headers, credential-bearing HTTP URLs, and JWTs. Redaction is defensive best effort, not a proof that every possible arbitrary secret representation can be identified. Do not deliberately print secrets in CI.

Manual CLI equivalents:

```powershell
backend/venv/Scripts/python.exe -m backend.ai_intelligence.cli sync --repository saksham-1326/cloud-byte-xl-project
backend/venv/Scripts/python.exe -m backend.ai_intelligence.cli train --repository saksham-1326/cloud-byte-xl-project
backend/venv/Scripts/python.exe -m backend.ai_intelligence.cli rca --repository saksham-1326/cloud-byte-xl-project --run-id 32446985157 --attempt 1
```

## Prediction definition and leakage controls

Live prediction time is **while GitHub still reports the exact run attempt as queued**, before observing its outcome. The server fetches the current run itself; clients cannot submit labels, feature vectors, commands, or fetch URLs. After feature collection/inference, it rechecks the run and rejects it if it started, completed, changed SHA, or changed attempt. Database outcome matching further checks the persisted prediction timestamp against actual job start time; late or unprovable timing is excluded from live evaluation.

Features (`prequeue-v2-utc-standardized`): changed-file count, commit additions/deletions, dependency/Docker/workflow file change indicators, historical workflow configuration availability/line count, preceding same-workflow failure rate and streak, preceding completed duration statistics, trigger, workflow identity, UTC queued hour and weekday. Historical feature snapshots are versioned. Each model artifact has a SHA-256 digest and is loaded only from the server-owned UUID-named artifact directory. Feature-version mismatches are rejected.

Never included: target conclusion/status/duration/logs/failed jobs or contemporary security scores. History uses only earlier completed outcomes and excludes target/same-commit siblings. Previous attempts of an earlier run count only once (latest attempt known before cutoff). Training excludes rerun attempts; same-commit groups are purged across chronological 60/20/20 partitions, with training/validation outcome availability checked at later prediction boundaries.

Labels: success=0, failure=1. Cancelled/skipped/timed_out/action_required/other conclusions are excluded. The policy is intentional: a timeout is not silently relabeled as a test failure.

Compare DummyClassifier, scaled Logistic Regression and a small Random Forest. Fit preprocessing only on the train partition, select model and threshold using validation F1 (0.5 if validation lacks both classes), then report every comparator on the untouched test interval. Report precision, recall, F1, accuracy, confusion matrix, average-precision PR-AUC, ROC-AUC when defined, Brier score and descriptive calibration bins. Small data is not probability-calibrated; single-class AUCs are null, not fabricated. If independent sample/class requirements fail, persist **insufficient_data** and produce no probability.

The live audit reports latest run conclusions of 22 successes / 5 failures. There are 28 attempts for 27 unique runs because one failed first attempt was rerun successfully. Training deliberately uses first attempts: 21 successes / 6 failures. These are different observation units, not duplicated training samples.

All fitted models remain **experimental**. The historical repository contains deliberately induced failures and too few independent executions for production claims. The dashboard keeps historical backtests and genuine live shadow predictions separate. Backtests are produced now from as-of historical features; their `predicted_at` is the actual backtest generation time, with historical feature time stored separately. Older feature versions stay in the registry but are not used for new-version inference.

## Shadow mode / future outcomes

For automatic operation, configure a GitHub repository webhook manually:

- URL: `<your-backend>/api/ai/v1/webhook`
- Content type: application/json
- Events: Workflow runs (`requested`, `completed`)
- Secret: the backend's `GITHUB_WEBHOOK_SECRET`
- Set `AI_ALLOWED_REPOSITORIES` to the repository full name.

Only HMAC-verified, allowlisted events are accepted. The payload's status is never trusted for inference: the service fetches GitHub again. Requested events attempt prediction before syncing other history; completed events synchronize real outcomes and update evaluation. The service never changes CI behavior. Some rerun/fast-start events do not provide a usable queued window; those events are honestly skipped/audited. Strict pre-execution prediction cannot be guaranteed for every fast workflow. For reliable organization-wide queued event coverage, a GitHub App/check orchestration integration is future work.

Tasks are durable in PostgreSQL, claimed atomically, heartbeated, and run through a bounded executor. To recover queued tasks after a restart or reclaim leases older than 15 minutes:

```powershell
backend/venv/Scripts/python.exe -m backend.ai_intelligence.cli worker
```

This worker does not trigger Actions runs. Existing pending tasks resume; configure your process supervisor for long-term operation. The application currently has local-admin authorization, not a multi-user tenant identity model. Without `AI_ADMIN_TOKEN`, only direct loopback requests with a trusted local Origin/Host are allowed. Remote AI administration requires the token and a repository allowlist. Keep the backend behind appropriate network/HTTPS access controls if exposed.

## Root-cause analysis

Run #21 ID is `32446985157`, attempt 1, job `96668290338`. GitHub calls its failed step **Run tests**, but the retrieved logs show:

- Line 204: explicit `exit 1` command.
- Line 222: `1 passed`.
- Line 223: process exited with code 1.
- Line 273: nonexistent Docker container during later cleanup.

The primary diagnosis must be **intentional_workflow_termination**. The Docker observation is secondary. The extractor narrows to the failed command frame, preserves normalized original line numbers, distinguishes cleanup, and returns insufficient evidence when logs cannot establish a cause. Parallel failures are disclosed; one report covers the earliest relevant failed step, not a guaranteed complete causal graph.

Provider modes:

- `RCA_PROVIDER=none`: deterministic evidence-rule diagnostics, clearly labeled `evidence_rules`/`rules-v1`. This is useful and testable but is **not an LLM call**.
- `RCA_PROVIDER=openai`, `OPENAI_API_KEY`, `RCA_MODEL`: OpenAI Responses API with strict JSON Schema. Choose an available Structured Outputs model in your account; no outdated model name is hardcoded. Bounded redacted evidence is sent as untrusted data, with no tools. Output is schema-validated; citations must reference supplied primary evidence; outputs contradicting detected passing tests / intentional termination are rejected. Provider failures remain errors rather than silently claimed AI successes.
- `RCA_PROVIDER=gemini`, `GEMINI_API_KEY`, `RCA_MODEL`: native Gemini Developer
  API with JSON Schema output, the same local guard checks, bounded responses,
  safe redacted errors, and no automatic retry/fallback. Current project validation
  used explicitly authorized `gemini-3.5-flash-lite`; inspect the latest checkpoint above.

No provider credential was available during implementation, so live LLM generation remains **unverified**. Report uncertainty is not used to measure accuracy. Human verification uses independent category/step/citation/fix/unsupported-claim criteria. Reviewer identities are self-reported in this local-admin application. Distinct reviewer IDs can submit separate rubric reviews; pairwise exact agreement is measured over the five boolean judgments within each report. Agreement remains unavailable until at least two reviewers assess the same report. It does not authenticate reviewer identity or prove independence. Mixed pass/fail reviews mark a report disputed.

## Tests and measured reports

```powershell
backend/venv/Scripts/python.exe -m pytest backend/tests -q
$env:AI_TEST_DATABASE='1'
backend/venv/Scripts/python.exe -m pytest backend/tests -q
backend/venv/Scripts/python.exe -m backend.ai_intelligence.evaluate
backend/venv/Scripts/python.exe backend/tools/verify_ai.py
npm run lint --prefix frontend-app
npm run build --prefix frontend-app
```

DB tests use a unique temporary repository and remove only their own fixtures. External APIs are mocked for deterministic tests; the live integration script calls the actual running local Flask server, GitHub, and PostgreSQL. It does not create a workflow execution or modify GitHub content.

- `backend/ai_audit.json`: original live GitHub history audit.
- `backend/reports/model_evaluation.json`: final measured model comparison and chronological backtest, including feature/split provenance.
- `backend/reports/run21_rca.json`: persisted real-log RCA.
- `backend/reports/rca_regression.json`: one real-log case and five independently specified synthetic controlled fixtures. This measures evidence rules, not LLM quality; exact citation/forbidden-assertion checks are not comprehensive semantic grading.
- `backend/reports/live_api_verification.json`: actual HTTP sync/train/RCA/rejection outcomes.

A trained test F1 on six held-out runs is not evidence of generalization. No real future queued run was created solely for this task, so live prediction/outcome matching is covered by deterministic race/persistence tests, while real live evaluation remains empty until future events arrive.

## API map

All routes are under `/api/ai/v1` and preserve existing API contracts:

- GET `overview`, `runs`, `models`, `predictions`, `outcomes`, `evaluation`, `rca` (query `repository=owner/repo`).
- POST `sync`, `train` with `{repository}` returns HTTP 202 and a durable `task_id`.
- POST `predictions`, `rca` with `{repository,run_id,attempt}` returns 202.
- GET `tasks/<uuid>?repository=...` returns task status and bounded results.
- POST `rca/<uuid>/verify` requires repository, a reviewer identifier, and all five boolean review criteria.
- POST `webhook` requires GitHub HMAC and an allowlisted repository.

Changed existing files: `backend/app.py` (blueprint registration and approved removal of the password fallback), `backend/requirements.txt`, `.gitignore`, `frontend-app/src/App.jsx`. Added: `backend/ai_intelligence/{github,collector,migrations,store,rca,ml,service,api,cli,evaluate,reviews}.py`, four SQL migrations, collection/ML/RCA/API/storage tests and a redacted real fixture, audit/integration tools, reports, `.env.example`, this guide, `frontend-app/src/AIIntelligence.jsx` and `ai.css`. Local model artifacts are ignored by Git.

## Primary API references

- [GitHub Actions workflow runs](https://docs.github.com/en/rest/actions/workflow-runs)
- [GitHub Actions workflow jobs and logs](https://docs.github.com/en/rest/actions/workflow-jobs)
- [OpenAI Structured Outputs / Responses](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
- [scikit-learn chronological evaluation guidance](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split)
