# Final project verification — November 27, 2026

## Decision

**PARTIAL — the core academic prototype has been demonstrated locally and in production, but an unconditional final sign-off is withheld.** Both environments completed genuine repository scans, all 12 pages were exercised in real Chrome at all four requested widths, and JSON/browser PDF exports worked. This branch corrects report omissions, stale landing-page claims, and a reproduced RCA classification defect. These fixes are not yet deployed. Production retains some incorrect, explicitly unverified historical RCA reports; no records were overwritten. Failure prediction remains experimental and fails its release gate. Zero prospective predictions were verified.

This document distinguishes direct browser observations, live API/database reads, controlled local mutations and automated fixtures. A successful UI render is not an AI accuracy result. No paid resources, billing changes, production retraining, production data mutations, workflow triggers or deployment were performed by this verification.

## Revision and preservation

| Check | Status | Evidence |
| --- | --- | --- |
| GitHub main | PASS | `git ls-remote` and fetch returned `84999c4878be53df67c0023e61d9bacf52f3c81a`. Genuine scans resolved the same SHA. |
| Initial checkout | PASS, preserved | Original branch `codex/local-actions-observer`, HEAD `4ee51db4a8cd2d105e5b8344881394cc41093aac`, contained staged documentation and untracked frontend/root files. Its original branch and working-tree changes were preserved. |
| Isolated finalisation | PASS | Managed worktree `C:\Users\Saksham Sharma\.codex\worktrees\final-live-verification\Cloud-ByteXL`, branch `codex/final-live-verification`, based on current main. No user changes were copied into the fix branch. |
| Vercel | PASS | Production deployment `dpl_5UKdBUwyyxdd8dKirnrDJuTf2RHL`, READY, commit `84999c4`; actual bundle uses `https://cloud-bytexl-api.onrender.com`. |
| Render | PASS, different revision | Service `srv-dc3a1ebrjlhs73f9ggg0`, live deploy `dep-dc4kigcs6fmc73dttcdg`, commit `8e2f2499dc4e0ec39efc9b6abdea7847e65ae66c`; free plan; auto-deploy off. |
| Existing deployment compatibility | PASS | Between `8e2f249` and `84999c4`, the backend diff adds a mock routing test; no backend runtime implementation changed. Real frontend/backend scans, source previews and AI reads succeeded together. Equal commit IDs are not required for these compatible runtime versions. No unnecessary corrective deployment was made. |
| Proposed release | PENDING | New frontend and RCA fixes require PR review and an approved release. No merge or production deployment was attempted. |

## Environment and execution

- Windows, PowerShell; Python **3.13.14** from the existing `backend/venv`; Node **22.20.0**, npm **10.9.3**. `pip check` reported no broken requirements. Latest-main `npm ci` succeeded with zero reported vulnerabilities; no application dependency upgrade was made.
- Latest-main Flask and Vite were actually started and used at `http://127.0.0.1:5000` and `http://127.0.0.1:5173`. Initial listening-port inspection through CIM was denied; successful binds and HTTP requests subsequently verified the ports. Flask is the development server locally; this is not a production WSGI claim.
- Disposable **PostgreSQL 17.10** cluster bound only to `127.0.0.1:55441`, stored under ignored verification output. Separate databases: `cloud_bytexl_ci_test` for mutation regressions and `cloud_bytexl_live_verification` for browser/source/RCA work. Both were created empty; no original database was a write target.
- Legacy schema bootstrap plus all **five AI migrations** succeeded. Actual repository persistence and RCA readback succeeded in the browser database. Database-test endpoint returned HTTP 200 there.
- Existing environment files were not edited. Configured GitHub/Gemini credential presence was checked by name only; credential values were kept in memory. Local tests initially used anonymous GitHub reads; after a later scan failure, the existing GitHub credential was used for local verification. Providers stayed off in the Flask server.
- A local administrator frontend profile was used only for the isolated RCA submit/poll/persist retest. Training, prospective inference and provider buttons remained separately disabled. Production restrictions were unchanged.
- Neon project `floral-dream-59785344`, production branch `br-rapid-meadow-biuawmyr`, reports PostgreSQL **18** and ready state. Read-only SQL verified five migrations, 78 stored attempts, 77 snapshots, 11 jobs with logs, 15 RCA reports and zero shadow predictions. Thirteen model records had artifact path/digest receipts at that later snapshot; the hosted background service can add evaluations independently of this verification.

## Automated checks

| Check | Result | Scope and limitations |
| --- | --- | --- |
| Baseline latest-main backend, PostgreSQL enabled | PASS: **317 passed**, zero skipped | Actual disposable PostgreSQL, migrations, transactional persistence, callback authentication/idempotency/restarts, ML persistence/guards and offline API/provider fixtures. 68 existing NumPy/joblib deprecation warnings. |
| Initial older-checkout backend | 220 passed / 65 skipped | Recorded only to explain the revision mismatch; not used as latest-main acceptance. |
| Latest-main backend without integration flag | 247 passed / 70 skipped | Superseded for acceptance by the database-enabled run. |
| New lint RCA and existing reliability checks | PASS: **71 passed** | Includes the genuine ESLint regression, preserving real pytest errors and rejecting unsupported test-failure claims. |
| Final full backend after RCA fix | PASS: **321 passed**, zero skipped | Complete PostgreSQL-enabled suite; 68 existing NumPy/joblib deprecation warnings; 365.31 seconds. |
| Frontend after report fixes | PASS: **37 passed**, zero failed/skipped | Original 35 plus two report-evidence regressions. Most original checks are contract/source/mock checks, not browser tests. |
| ESLint | PASS | Latest modified frontend. |
| Vite production build | PASS | Approximately 699 kB JS / 205 kB gzip; existing >500 kB chunk warning remains. |
| npm production dependency audit | PASS | Zero reported vulnerabilities; not a complete security guarantee. |
| Docker execution | NOT TESTED | Docker executable unavailable on this host. Existing Dockerfile also has a static non-root-user finding. |
| Local Gunicorn execution | NOT APPLICABLE on Windows | Gunicorn was not installed in this environment. Render is configured to start `gunicorn --config gunicorn.conf.py backend.wsgi:app`; production HTTP checks are separate evidence of its deployed service. |

## Real browser verification

The visible in-app browser was tried first. Production POST scanning stalled after successful OPTIONS requests and returned its bounded timeout; cancellation worked. No corresponding POST appeared in the sampled Render application logs. Native-app browser recovery failed. This is an observed tooling/transport limitation, not proof of a Render cold-start fault. Independent **headed Google Chrome through Playwright**, with clean temporary contexts, then completed the real production flow without mocked HTTP responses.

Observed scan durations: **8.29 s local**, **44.474 s production** on the first independent Chrome passes; later passes **7.086 s local** and **6.38 s production** including UI completion. The fixed local export recorded **5.73 s** for its request interval, excluding later rendering. These are individual observations, not averages, percentiles or a cold-start benchmark. Render was not deliberately suspended or restarted.

| Page / flow | Local | Production | Directly exercised |
| --- | --- | --- | --- |
| Landing / workspace entry | PASS | PASS | X-Ray toggle, pipeline node selection, workspace entry and transitions. Illustrative RCA example remains labeled illustrative. |
| Overview | PASS | PASS | Genuine scan summary: exact SHA, 145 files, five languages, score 80, two static findings. Read-only storage notice in production. |
| Repository | PASS | PASS | Genuine metadata, main branch, ten recent commits, contributor/language data; Dockerfile source preview from exact SHA; file search and empty search. No separate branch-enumeration control exists. |
| Analysis | PASS | PASS | Completed assessment and scan history; real loading overlay, cancellation and successful retry. Fixed request duration on local branch. |
| Issues | PASS | PASS | Severity filter, zero-result state, reset, finding modal, local-session Reviewed state. This is not persisted human RCA verification. |
| Security | PASS | PASS | Actual severity distribution and finding inventory; charts rendered; shared finding modal. Static heuristic evidence, not comprehensive security coverage. |
| Recommendations | PASS | PASS | Severity filter and zero-result state; suggested fixes tied to actual findings. No automatic source edits. |
| Architecture | PASS | PASS | Node inspector, zoom to 125%, reset to 100%; topology is configuration evidence. |
| CI/CD | PASS | PASS | Workflow source/inspection, explicit lack of deployment telemetry, navigation to separately persisted AI history. |
| Docker | PASS, static only | PASS, static only | Actual Dockerfile inspection/finding; explicitly says container telemetry unavailable. No live Docker management. |
| Kubernetes | PASS, empty state | PASS, empty state | No matching manifests; explicitly says cluster status/workload counts unavailable. No live cluster control. |
| AI Intelligence | PASS for evidence display | PASS for evidence display | Accessible before any source scan; refresh/loading, actual stored attempts/model metrics, release gate, disabled prospective controls, failed-attempt selection and supporting citations. Accuracy is assessed separately below. |
| Reports | PASS | PASS, old omissions remain | Preview show/hide, JSON download/content inspection and real Chromium print-media PDF output. Fixed local JSON includes inventory/languages/duration. Native OS print-dialog completion was not tested. |
| Invalid URL / non-allowlisted repo | PASS | PASS | Clear frontend validation; production API rejects malformed URLs with 400 and non-allowlisted repos with 403. |
| Inaccessible repository | PARTIAL | NOT APPLICABLE beyond allowlist | Local backend gives a sanitized not-found/private-access explanation for a nonexistent repository. No real private repository or private token permissions were probed. |
| Failed refresh preservation | PASS | Automated coverage + cancellation | Actual local browser offline mode caused a genuine fetch failure; prior 145-file results remained. Escape cancelled the next scan. No mocked successful analysis was substituted. |
| Notifications/profile and external links | PARTIAL | PARTIAL | Controls/targets were inspected; no external account/profile mutation or exhaustive external-link audit was performed. |

All **12 pages × four widths (1440, 1024, 768, 390) × two environments** were navigated. No horizontal document overflow was measured. Overview, AI, issues and report screenshots were captured at the requested sizes; source panes/tables can scroll internally. Sidebar mobile opening and navigation worked. Early transition screenshots were not accepted as steady-state layout evidence; later captures finished animations and verified sidebar/main geometry. No unexpected JavaScript exceptions were captured in the successful complete browser passes. Aborted requests during React StrictMode cleanup/cancellation are expected and distinguished from failures.

## AI prediction: actual evidence, not an accuracy claim

Snapshot model **`70a321ae-a67a-4b99-a9c4-7965f24a061a`**, selected **Random Forest**, threshold **0.2**, feature version `prequeue-v2-utc-standardized`. Dataset **77 first-attempt labeled histories: 62 success / 15 failure**. Chronological split **46 train / 15 validation / 16 test**; test contains 13 successes and three failures. Selection/threshold tuning uses validation, with exact-SHA snapshots, train-only preprocessing, completed-prior-outcome and same-commit exclusions. Code and regression checks cover these safeguards; all historical rows were not independently re-collected/retrained in this audit.

| Historical test comparator | Accuracy | Precision | Recall | F1 | Brier | ROC-AUC | PR-AUC | Confusion matrix TN,FP / FN,TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dummy | 0.8125 | 0 | 0 | 0 | 0.153592 | 0.500000 | 0.187500 | `[[13,0],[3,0]]` |
| Logistic | 0.7500 | 0 | 0 | 0 | 0.196639 | 0.410256 | 0.238384 | `[[12,1],[3,0]]` |
| Selected Random Forest | 0.6250 | 0 | 0 | 0 | 0.155881 | 0.512821 | 0.240909 | `[[10,3],[3,0]]` |

Stored expanding-window **logistic** replay: 67 eligible cases (54 successes, 13 failures), accuracy **0.626866**, precision **0.2**, recall **0.307692**, F1 **0.242424**, Brier **0.243605**, matrix `[[38,16],[9,4]]`. Historical base-rate Brier **0.161069**. This replay is not evidence for the selected Random Forest family and is not prospective validation.

Release gate correctly reports **`insufficient_evidence`**: held-out failure recall/precision below policy and no comparable walk-forward result for the selected family. The UI exposes the reasons and unavailable live prediction. **Zero shadow predictions / zero timing-matched prospective outcomes**, so prospective accuracy, precision, recall and F1 are **NOT VERIFIED**. No gate was bypassed, labels synthesized, test interval selected for favorable scores, threshold tuned against test outcomes, or historical model evaluation overwritten. Historical test windows have been examined before; they are not a newly untouched validation set.

Model registry/snapshot persistence was checked by read-only production queries, and actual model save/load/digest guards by isolated regressions. Production model artifact bytes were not downloaded and rehashed: **PARTIAL** for independent verification of the deployed artifact itself. No model retraining was performed against production.

## RCA: live validation and discovered defect

1. **Run `45972234793`, attempt 1**: authentic GitHub job metadata and one failed-job log were fetched with the existing read credential, redacted by the application, and stored only locally. Evidence rules returned `insufficient_evidence` for `Run frontend contract tests` and persisted it. This conservative result is not a successful exact-cause identification.
2. After explicit user approval, **one** call to configured `gemini-3.5-flash-lite` used that redacted evidence. It returned an accepted `llm_grounded` `insufficient_evidence` report with two source citations; independent local readback verified persistence. No provider retry, billing change or production write. Automated guard acceptance is not human review or measured accuracy. The call preceded the new lint fix and was not repeated afterward.
3. **Run `45795104375`, attempt 1**: fresh genuine logs reproduced a bug. The failed step is `Lint frontend`; cited output says `'analyzeStep' is assigned a value but never used  no-unused-vars`, then `1 problem (1 error, 0 warnings)`. The old extractor incorrectly interpreted source column `10` and the linter total as pytest error counts, producing `unit_test_failure`.
4. The fix separates explicit lint diagnostics into **`lint_failure`**, excludes linter coordinates/totals from pytest counts, prevents an echoed exit from overriding lint evidence, and rejects provider test-failure claims unsupported by citations. The real local browser submitted the diagnosis, polled its asynchronous task, displayed `Category: lint failure` and `no-unused-vars` citations, and independently read back the new persisted rules report. The previous `unit_test_failure` report remained intact. No human review was fabricated.

Redaction checks are bounded, not a guarantee that arbitrary logs can never contain secrets. Original-evidence citations and primary/secondary separation have automated coverage. Zero independent human RCA reviewer submissions were established. Broad model diagnostic accuracy remains **NOT VERIFIED**. Production's old lint-as-test reports remain known incorrect, unverified historical records pending an explicitly reviewed remediation; this branch does not silently rewrite them.

## Bugs fixed and scope

| Bug | Root cause | Smallest change | Verification |
| --- | --- | --- | --- |
| Scan duration always unavailable | Repository store hardcoded `analysisDuration` to an em dash | Measure successful request with `performance.now()`; preserve unavailable for missing/invalid duration | Two functional report regressions and actual downloaded local JSON |
| Export omits dashboard inventory/languages | Inline export object did not include the source inventory | Shared report builder retains original keys and adds files, count, languages and static-inspection boundary | Real JSON download parsed; 145 actual files and matching score/findings |
| Stale test count presented as current | Landing page hardcoded “174 TESTS PASS” | Neutral pytest/CI label, no hardcoded live test count; generic PostgreSQL header avoids conflicting local/hosted versions | Browser landing interactions, frontend suite, lint/build |
| Lint failure called a unit-test failure | Generic numeric-error parsing accepted ESLint coordinates/problem total | Explicit cited `lint_failure`, exclude lint totals, enforce support for test-failure claims | Genuine historical-log reproduction, four new regressions, existing reliability checks and local browser retest |

Modified implementation: `frontend-app/src/App.jsx`, `repositoryData.js`, `MissionControlLanding.jsx`; `backend/ai_intelligence/rca.py`, `rca_facts.py`. Added regressions: `frontend-app/tests/report-evidence.test.mjs`, `backend/tests/test_rca_lint_evidence.py`. Updated root/frontend READMEs and `backend/AI_INTELLIGENCE.md`. This report and compact sanitized evidence are additive. Mission Control styling and layouts are preserved; no infrastructure/provider/model rewrite.

## Security, performance and operational limits

- Production `/healthz` and `/readyz`: HTTP 200. Readiness checks read-only DB/schema/role properties; the private database-test route correctly returns 403 publicly. Local `/healthz` and `/readyz` return 404 because those are hosted-profile routes; local `/` and database-test are the intended checks.
- Exact Vercel origin receives CORS permission; an unapproved origin receives no allow-origin header. API URL verified in the actual deployed JS bundle. CORS is not authentication.
- Live production mutation probing of `/api/ai/v1/train` was **NOT TESTED**: automatic approval review rejected the proposed negative probe because it could enqueue training. The safe alternative was isolated PostgreSQL regression coverage and inspection of disabled production controls. No bypass or production security change.
- Callback authentication, transaction safety, duplicate receipts, outcome reconciliation, restart persistence and ML artifact controls: **PASS through controlled automated tests**, not live external callback delivery. No real external callbacks were enabled.
- Source scan inspects at most 48 prioritized files and approximately 1.5 MB; 145 inventory entries do not mean every file was fully analyzed. Six metadata API requests plus bounded raw-content reads can still hit anonymous limits with repeated demonstrations. Use the existing credential securely; never put it in frontend variables. No throughput/load test or memory profiling was performed.
- The apparent hardcoded-credential finding in `backend/tests/test_ai_collection.py` is a heuristic hit on a controlled redaction-test fixture, not proof of a real leaked key. No environment credentials were committed. Existing Dockerfile non-root-user finding remains. No dependency/service upgrade was used to disguise findings.
- Vite warns about the ~699 kB JS chunk. It builds successfully; bundle splitting is deferred to avoid an unrelated late architectural change. Docker execution, real cluster control, prospective prediction and exhaustive browser-native print-dialog behavior remain outside verified claims.

## Evidence and reproducibility

Portable sanitized metrics, browser matrices, receipts and screenshot/PDF hashes: [verification/2026-11-27/summary.json](verification/2026-11-27/summary.json). This contains no credential values or raw failure-log bodies.

Dedicated local evidence directory (ignored, not committed):

`C:\Project\Cloud-ByteXL\backend\reports\final_verification_20261127\`

Key files:

- `browser-results.json`, `interaction-results.json`, `production-responsive-results.json`, `recovery-responsive-results.json`: genuine Chrome results and page text.
- `local-viewport-{1440,1024,768,390}.png`, `production-viewport-{1440,1024,768,390}.png`: steady-state overview screenshots; `{environment}-{AI-Intelligence,Issues,Reports}-{width}.png`: page-specific captures.
- `local-report.json`, `production-report.json`, `local-report.pdf`, `production-report.pdf`: actual downloaded JSON and browser print output. Production exports still show the pre-fix schema.
- `live_rca_result.json`, `live_rca_result_45795104375.json`, `gemini_approved_result.json`: separate rules/provider observations; `rca-postfix-browser-result.json` and `local-corrected-lint-rca.png`: corrected flow evidence when completed.
- `backend-tests-final.txt`, `frontend-tests-final.txt`, `http_probes.json`, `security-probes.json`: local test/API evidence. Raw responses and private operational database files remain ignored. Logs are not copied into the PR.
- Verification scripts in that directory use real browser/API calls. Mocked responses used by unit tests remain explicitly separate. Local admin/GitHub configuration is read in memory; rerunning a provider check requires renewed scope discipline and is not part of routine test reproduction.

## Submission boundary

The demonstrated scope is a **repository-analysis and evidence-inspection prototype with experimental prediction**. It is suitable for a bounded academic walkthrough when these limits are stated. Do not claim dependable failure prediction, independently validated RCA accuracy, live infrastructure management or an already deployed fix. Final regression and local readback passed. Before unconditional final sign-off: review the PR, approve any production release separately, verify the deployed fixes, and decide how to present the preserved incorrect historical lint diagnoses. The production data should not be rewritten simply to improve the demonstration.
