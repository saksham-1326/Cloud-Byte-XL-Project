# AI verification checkpoint — November 23, 2026

This is technical verification after PR #6 merged, not a new accuracy claim. No live observer, workflow trigger, provider call, deployment, production retraining/replacement, commit or push was performed. Original databases, the SELECT-only demo, pinned models and RCA evidence remain protected. Analysis outputs and private configuration live under ignored `backend/reports/ai_verification_20261123/`.

## A. Prospective prediction — prepared, not started

### Actual checks performed

| Item | Result |
| --- | --- |
| GitHub authentication | Three bounded, one-shot GET probes returned 200 for the exact repository, Actions workflow metadata and workflow contents. This was authentication validation, not polling or observer execution. |
| Credential permissions | Read access works. OAuth scopes were not returned, so repository-limited Actions/Contents-only scope is **not independently established**. Repository `permissions` describe the caller's repository relationship and do not prove this token's grants. Confirm its actual configuration before live use; never paste it into chat. |
| Model | Original `55ef22a1-2f30-47f2-95d8-bf12efaf6463`, SHA-256 `075d37741200bb9aaf8939fd92ee621d5fe445a11842359ba443c3ad348660a7`, current feature version, original training cutoff/threshold and artifact integrity verified. No model or threshold replaced. |
| Observation database | New `cloud_bytexl_observation_20261123` on `127.0.0.1:55439`, separate from original, demo and destructive test databases. Existing official migrations applied there only. |
| Roles | Distinct `cloud_bytexl_observer_writer_20261123` and `cloud_bytexl_observer_reader_20261123`; neither owns tables or has superuser/create-role/create-database privileges. Writer can insert predictions/update only verification status; cannot change original probability/time/model metrics. Reader has SELECT-only access and enforced read-only transactions. |
| Authentic seed | 28 completed attempts / 28 historical outcomes plus the single authentic pinned model copied from the read-only demo with original identities/timestamps. No historical predictions, RCA reports, tasks or reviews copied into observation DB. **Zero observation predictions**. |
| Independent connection | Existing connection factory verifies exact DB/role/primary identity. Reader query joins predictions to exact run/attempt/model/outcome without error. Privileges checked independently. |
| Ledger | Separate, explicitly `controlled_test` preflight ledger written and reopened through the existing hash-chain implementation. The intended live ledger does not exist and was not opened. This is a controlled integrity check, not prospective evidence or an external signature. |
| Existing CLI dry-run | Passed twice with actual prepared DSNs/model configuration and existing credential loaded only into the child process. CLI reported no network/DB/ledger access or prediction submission during dry-run. Separate preflight checks, not dry-run itself, established connectivity/model/permissions. |
| Time evidence | Windows Time service is **stopped**; `w32tm` returned service-not-started. No measured clock-error bound or valid-until evidence exists. This does not prove the clock is wrong, but prevents qualifying pre-start persistence claims. Clock bound remains null; no fabricated zero uncertainty. |
| Historical freshness | Seed ends **November 3, 2026**. Newer real runs must be incorporated through an approved bounded historical metadata refresh before using recent-history features for a credible session. No refresh/polling was silently started. |

The existing runner and prediction service were reused. No alternate observer or prediction engine was built. Flask is unnecessary for the runner; its writer/reader connections are separate from the read-only demo server. Private preparation directory permissions are restricted to the current Windows user and SYSTEM. No API credential is stored in the observer private configuration or receipts; DB passwords are private and never printed.

### Proposed exact session profile

- Repository/only allowlist: `saksham-1326/cloud-byte-xl-project`.
- Pinned UUID/hash as above; original threshold **0.5**, feature version `prequeue-v2-utc-standardized`.
- Interval **15 seconds**, duration **900 seconds**, at most **60 polls / 300 total reserved GETs**, including service rechecks, pagination and retries. No automatic extension after expiry.
- Dedicated DB/roles above. DSNs are loaded from the protected local `observer_private_config.json`; no default .env database fallback.
- Intended live evidence ledger: `backend/reports/observations/approved_20261123.jsonl`. Do not substitute the controlled preflight ledger or reuse a different profile's ledger.
- `--clock-uncertainty-seconds` and `--clock-evidence-ref`: **unresolved**. Measurement must have an independently justified conservative bound, timezone-aware measured/expiry times, method and validity covering the full session. Do not enable/change Windows time settings automatically as part of this task.
- Preflight API header showed 5,000 primary requests/hour, 4,907 remaining after the three probes. These were observed values, not a promise of future/shared quota. Existing runner rate headers, cooldowns and budget guards remain authoritative.

Safe repeatable check (no live option exists in this helper):

```powershell
Set-Location C:\Project\Cloud-ByteXL
.\backend\venv\Scripts\python.exe backend\reports\ai_verification_20261123\check_observer_dry_run.py
```

The helper/profile are protected local artifacts, not checked-in credentials or a portable installer. It rejects extra arguments and can only call `--dry-run`. Existing CLI `--run` is not invoked here.

### Required before approval/start

1. Verify a repository-limited Actions/Contents read credential and its actual grant settings.
2. Obtain and review clock-bound evidence covering the session. Unknown bounds would leave results unverifiable, even if the saved DB row later says matched.
3. Approve a bounded, metadata-only update of the November-3 historical seed into **only the observation DB**, reusing existing GitHub client and scoped collector. Exact request/time bounds and completeness must be approved before that refresh; do not use full-history sync with unreviewed log/provider work or silently truncated history.
4. Approve the final profile, clock-evidence digest, ledger, start time, duration and budget. Start before a naturally occurring eligible event; do not trigger a workflow as part of preparation. Queue windows may be shorter than polling, and some reruns are conservatively ineligible.
5. During the approved session, retain exact run/attempt/SHA/state, first prediction time, model/version/features/probability and first independent readback. Both prediction and independently observed persistence, plus clock/timestamp precision margin, must precede earliest executed-job start. Reconcile actual outcome separately and recheck immutable fields. No database commit timestamp is invented.

Session expiry can leave pending outcomes; separately approve follow-up reconciliation without manufacturing an earlier readback. Report zero eligible captures if that happens. **Actual genuine prospective predictions remain zero. No prospective accuracy is available.**

## B. ML accuracy — reproduced, not improved

### Authentic data and protocol

Source has **27 unique runs / 28 attempts**: 22 success attempts, 6 failure attempts. The successful rerun is excluded by the existing training policy. The eligible 27 first attempts have **21 successes / 6 failures**.

| Partition | Runs | Success | Failure |
| --- | ---: | ---: | ---: |
| Train | 16 | 13 | 3 |
| Validation | 5 | 4 | 1 |
| Previously examined historical test | 6 | 4 | 2 |

The existing `ml.train`, `features` and `temporal_split` were reused unchanged with a memory-only experiment store. Source data were read in a repeatable-read/read-only transaction. Feature/model writes were captured locally, not sent to any original/demo/observation registry. New candidate joblib output is confined to ignored `candidate_artifacts/`; it cannot replace the pinned live artifact.

Protocol was recorded before fitting: existing Dummy prior, balanced Logistic Regression and balanced Random Forest (100 trees, max depth 4, min leaf 2, seed 42). Vectorization/scaling and fitting use train only. Model/threshold selection uses validation F1 then Brier only; the existing grid is 0.2–0.8 and an additional validation-only exploration tried 0.05/0.10/0.15 plus that grid. The extra threshold was **not applied to the test interval**.

Assertions checked disjoint run/attempts, chronological completion cutoffs, target/same-commit exclusions and strictly prior completed outcomes in features. Target result, logs, completed target duration and post-run errors do not enter the current features. Historical immutable-SHA reconstruction is backtesting, not proof that features were actually collected prospectively.

### Reproduced historical test results

Confusion matrices use `[[TN, FP], [FN, TP]]`. All three use threshold 0.5 selected from validation.

| Model | Accuracy | Failure precision | Failure recall | Failure F1 | Confusion matrix | PR-AUC |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Dummy prior | 66.7% | 0* | 0 | 0 | `[[4,0],[2,0]]` | 0.3333 |
| Logistic Regression | 50.0% | 0 | 0 | 0 | `[[3,1],[2,0]]` | 0.3333 |
| Random Forest | 66.7% | 0* | 0 | 0 | `[[4,0],[2,0]]` | 0.3333 |

`*` No predicted failures: the existing calculator uses `zero_division=0`; this is not an empirically established nonzero precision estimate. Both classes exist, so PR-AUC is defined. All three score only the test failure prevalence on PR-AUC.

On the five validation runs, Logistic and Random Forest each achieved 100% accuracy/recall/F1 **on only one failure**; Dummy accuracy was 80%, failure recall/F1 zero. Logistic won the existing validation Brier tie-break (approximately 0.0551 vs RF 0.1084). The expanded validation threshold search still selects **0.5**. Perfect five-row validation did not translate into test recall.

This test interval has already been examined in earlier audits and failure diagnosis. It is **not a genuinely untouched independent test set**. Results are historical reproduction, not a new model-validation claim. No model was selected or threshold tuned using test scores; no new threshold's test accuracy was calculated. Repeated fits on the same rows do not create independent observations. Original historical result files remain unchanged.

### Why the failures were missed

- Only three training failures exist, and the actual failure mechanisms vary. Class imbalance is present, but both fitted models **already use balanced class weights**, so simply adding class weighting is not a missing fix.
- Original pinned Logistic probabilities for failed #23 and #27 were approximately **0.190669** and **6.872 × 10⁻⁴⁷**, below threshold 0.5.
- #27 has 5,002 additions / 2,157 deletions / 10 changed files; training maxima are only **171 / 46 / 3**. In the pinned Logistic model, additions and deletions contribute about **−58.12 and −38.97 log-odds**, plus changed files about −6.81. This numerical extrapolation explains the extreme low estimate; it does not imply code churn causally prevents failure.
- Some training features are constant: workflow identity, event and configuration availability. Generic churn, workflow line count, time and recent history do not directly establish whether a remote callback route will return HTTP 404. The exact server-side causes remain unknown.
- The validation set contains one failure and cannot support reliable threshold tuning, calibration or broad model selection. Lowering a threshold after seeing the test failures would be test-guided tuning; it was not done. The validation data do not support a lower threshold as an improvement here.

**Supported improvement: operational verification and clearer failure diagnosis, not better measured prediction accuracy.** Random Forest does not recover the missed failures. Current model/threshold remain pinned. Future candidate features/regularization/capping must be designed and selected on training/validation, then evaluated on new data; adding a feature because these known test failures exposed it cannot create an independent evaluation on the same six rows.

Needed data: new naturally occurring successes **and failures**, varied commits/configurations and failure mechanisms, exact attempt/SHA, pre-outcome feature snapshot and timing evidence, first job start, completion/outcome, and clear marking of historical intentional failure injections. Reserve the next independent temporal test window before using its outcomes for tuning. More successes alone do not solve the three-failure training problem; no universal sample-count guarantee is claimed. Before November 26, honest limitations are preferable to a forced probability or production-readiness claim.

Local reproducibility scripts and full metrics: `evaluate_candidates.py`, `candidate_protocol.json`, `ml_candidate_evaluation.json` under the protected ignored analysis directory. The script reuses the existing training engine and creates local historical candidates only; it performs no provider calls, original registry writes or live predictions. Rerunning it is not a new independent experiment dataset.

## C. Gemini RCA — reviewer-ready, no human results yet

Both original source hashes match the preserved manifest. Eight historical Gemini response IDs for #13/#21/#23/#27 match original PostgreSQL report/run/attempt associations. Source has **21 unverified RCA reports**, eight explicitly non-human legacy agent assessments and **zero** human-review submissions. No generation or verification API was called.

The original `REVIEW_GUIDE.md`, `REVIEW_PACKAGE.md`, `human_worksheet.json` and `assisted_recommendations.json` remain unchanged. A separate recommendation-free packet was created at:

```text
backend/reports/ai_verification_20261123/reviewer_packet/
  EVIDENCE_AND_RESPONSES.md
  worksheet_blank.json
  reviewer_provenance_blank.json
  source_manifest.json
```

All human decisions and criterion values remain empty. The copy adds empty secondary-error correctness/notes fields without changing original IDs or the original worksheet. No new automated correctness judgments were inserted. It is recommendation-free, **not** a claimed blinded study; source/session names and extractor-selected evidence are visible.

Use [RCA_REVIEWER_INSTRUCTIONS.md](RCA_REVIEWER_INSTRUCTIONS.md). Check primary cause, category, exact failed step, semantic citation support, manual fix, unsupported claims and secondary/cleanup treatment separately. Preserve compiler uncertainty in #13 and unknown server-side HTTP 404 causes in #23/#27. Valid IDs, command text and posted `PASSED` strings are not independent proof of those claims. Missing evidence permits uncertain/null judgments.

The existing calculator confirms **0 completed human reports**, all criterion sample sizes zero and rates null, separately for earlier and improved sessions. Existing assisted suggestions remain **3 accept / 3 reject / 2 uncertain** with their explicit ChatGPT-assisted provenance; that is not RCA accuracy. Do not label a project author's previously assisted review independent without documenting involvement/exposure. Real decisions must come from an actual reviewer before recalculation; none were supplied here.

## Regression and next actions

Full backend suite on separate disposable PostgreSQL: **285 passed, 0 failed, 0 skipped, 0 expected failures**, including 61 observer tests and ML/RCA/callback regressions; 68 existing joblib/NumPy deprecation warnings. No frontend changes or new provider/ML implementation were made.

Before November 26: resolve clock evidence and token scope; approve historical refresh and the bounded session; capture only genuine eligible events or report zero; have an actual reviewer complete the separate packet; calculate human metrics only afterward. Retain the existing demo and historical metrics as the fallback. No commit/push/merge or live run is authorized by this preparation task.
