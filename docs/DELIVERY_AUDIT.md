# November 22 delivery audit and November 23–25 completion plan

This describes the uncommitted `codex/local-actions-observer` working tree, not a published release. Deadline: November 26, 2026, Asia/Kolkata. No deployment, live observation, model training, paid provider call, review submission or Git operation publishing changes was performed.

## Completed in this task

- Preserved 61 existing frontend/root files before editing, in ignored `backend/reports/delivery_20261122/preserved-ui.zip` with `preserved-ui-sha256.json`.
- Reused the existing application and observer. Added no alternate frontend, model or observer.
- Added bounded JSON API requests, cancellation, clear network/timeout/non-JSON errors and configurable public API origin.
- Repository switches clear stale scores/history; unknown values remain unavailable. Analysis shows database-save warnings and uses the actual analyzed commit for source previews.
- Displayed persisted workflow attempts and separated historical scores, stored shadow rows, automated RCA guards and manual review state. A matched database row is not independent prospective proof.
- Removed default-positive review answers: every boolean answer, reviewer name and report-specific acknowledgment is required. The API remains self-reported manual review, not authenticated independent verification. No review was submitted.
- Default-disabled model training, queued prediction and configured-provider generation in the UI. Flags are interface safeguards, not authorization controls. Backend authentication still applies.
- Fixed `/api/github/file` malformed body/path/reference handling to return JSON 400 responses rather than unexpected 500s. Added seven Flask contracts, including real isolated PostgreSQL reads.
- Added twelve dependency-free frontend contracts. Preserved existing layouts, screenshots, root packages and model artifacts.

## Verification

| Check | Result |
| --- | --- |
| Complete backend, disposable PostgreSQL 17 on loopback | **285 passed; 0 failed; 0 skipped; 0 expected failures** |
| Observer coverage within complete suite | 61 tests: 35 offline, 26 PostgreSQL |
| Backend additions in this task | 7 Flask/API contracts; GitHub responses mocked, database reads real |
| Frontend `npm test` | **12 passed, 0 failed** |
| Frontend `npm run lint` | Passed |
| Frontend `npm run build` | Passed; main JS approximately 672 kB, Vite chunk-size warning |
| Backend warnings | 68 joblib/NumPy deprecation warnings; no suppressed failures |
| Current Docker smoke | Blocked: Docker Desktop Linux daemon pipe unavailable |
| Current browser visual/end-to-end check | Blocked: browser tool timed out reaching local Vite port 5178 |
| Genuine prospective observations | **Zero**; no prospective accuracy measurement |

Earlier main-branch Docker/212-test verification is historical and does not replace the blocked current Docker check. Existing screenshots are prior artifacts, not fresh visual acceptance of these changes. Passing API contracts do not prove live GitHub delivery or a complete browser journey.

## Frontend/backend integration matrix

Paths below are relative to the repository. Severity concerns the final demonstration.

| Feature / component | Endpoint / source | Current implementation | Missing work | Severity / recommended fix |
| --- | --- | --- | --- | --- |
| Repository input, `App.jsx` | POST `/api/github/repository` | Real bounded GitHub collection and source analysis; cancellation/error handling added | Confirm intended read-only GitHub authentication and a real repository walkthrough | Critical: verify supported URL, successful response and analyzed SHA |
| Overview/analysis, `App.jsx`, `repositoryData.js` | Repository response `analysis` | Source-derived heuristics; no fabricated ML score; stale data cleared | Browser acceptance after repository switch | Important: verify unavailable scores, errors and actual loading completion |
| Source preview, `App.jsx` | POST `/api/github/file` | Uses analysis commit SHA; malformed input now JSON 400 | Browser open/close and large-file behavior | Important: compare displayed source with pinned GitHub revision |
| CI/CD, `CICDPage` | Source configuration; link to AI view | Repository workflow declarations, not a live stage simulator | No live deployment telemetry endpoint | Important: retain explicit source-only scope; use actual history table |
| Actions history, `AIIntelligence.jsx` | GET `/api/ai/v1/overview`; POST `/sync`; GET `/tasks/:id` | Persisted runs/attempts shown; explicit asynchronous sync | Approved initial population and authenticated repository access | Critical: show actual attempt/outcome; never substitute sample history |
| Model results, `AIIntelligence.jsx` | Overview model/metrics | Historical test metrics and baseline when present; unavailable otherwise | Authentic compatible model metadata in intended demo DB | Critical: preserve original artifact/hash; no retraining or invented metadata |
| Prediction display, `AIIntelligence.jsx`, `aiContract.js` | Overview predictions; POST `/predictions` | Stored shadow rows only; timing disclaimer; new prediction disabled by default | Approved genuine observation with timing ledger | Critical for prospective claims, not required to honestly demo unavailable state |
| RCA, `AIIntelligence.jsx` | Overview reports; POST `/rca`; tasks | Actual saved rules/model report, evidence IDs/text, guard and review status | Populate/read original reports through authorized existing records; verify browser rendering | Critical: check report/run/attempt association; never label rules as Gemini |
| Gemini explanations | Saved `llm_grounded` report; configured provider | Optional backend provider; frontend does not fabricate fallback | Free quota/authentication not verified; provider calls default-disabled | Important: demonstrate saved report or explicit unavailable/error state |
| Evidence citations, `LogEvidence` | Report `log_evidence` | Full IDs and log text visible; guard rejection shown separately | Human assessment of semantic support | Important: valid IDs alone do not prove a diagnosis |
| Review form, `AIIntelligence.jsx` | POST `/rca/:id/verify` | Blank choices, explicit acknowledgment, submit lock | API only supports five boolean checks; no accept/reject/uncertain decision field | Important: keep assisted judgments and unresolved decisions in offline tooling; do not auto-submit |
| PostgreSQL results | AI Store/overview; repository catalog save | AI persistence integration tested; catalog-save failure exposed | Fresh legacy schema bootstrap absent; authorized demo DB required | Critical: AI migrations do not install original application tables |
| Loading/errors, `api.js`, `App.jsx`, AI view | Request/task state | Finite request timeout, abort, honest errors; task polling limited to 3 min | Worker task may continue after UI timeout; refresh before retry | Important: avoid duplicate actions after timeout |
| Navigation/responsiveness | `App.jsx` page state; CSS media queries | Existing sidebar/layout retained; no React Router | Fresh desktop/tablet/mobile visual acceptance | Important: test widths 1440, 1024, 768, 390; back/deep-link support optional |
| Reports/export | Source-analysis export and print | Real source analysis only | AI evidence is not automatically included in source export | Important: explain scope; view AI evidence in AI page |
| Chat/deployment/runtime | Planned chat; inferred architecture/configuration | Chat is not connected; cloud/Kubernetes state not observed | Live runtime/chat service absent | Optional: keep clearly planned; exclude from required demo |
| Session analysis history/profile affordances | Browser state/local UI | Not a PostgreSQL audit trail or authentication system | Persistent user/account workflow unverified | Optional: do not present as secure multi-user platform |

## Observer release readiness

Reviewed the completed observer and its offline verification receipt. No new release-critical observer defect was established in this task; it was not rewritten. Existing tests cover budgets/rate cooldown, restart ledger integrity, isolated credentials, reruns, independent readers, clock bounds, immutable predictions and outcome matching.

Operational blockers remain: GitHub authentication not exercised; dedicated writer/reader database roles not provisioned for a real session; original compatible model metadata/artifact and pinned UUID/digest needed; independently justified clock-bound evidence needed. No scheduler starts this automatically. The CLI must explicitly run locally, with PostgreSQL available; Flask is unnecessary for observation. Queued windows can be missed, including some reruns. Old reruns may fail the existing model cutoff guard. Unknown timing stays excluded. A session ending before outcome reconciliation needs an approved follow-up.

Proposed observer commit scope, after approval and final patch review:

- `backend/ai_intelligence/{observation,observer,observer_client}.py`
- `backend/ai_intelligence/collector.py` attempt-validation/synchronization additions only
- `backend/tools/observe_actions.py`
- `backend/tests/{test_observer_offline,test_observer_postgresql}.py`
- `backend/tests/test_ai_ml_rca.py` valid-identity eligibility regression only
- `docs/{LOCAL_OBSERVER,LOCAL_OBSERVATION_ASSESSMENT,PROSPECTIVE_PREDICTION_PLAN}.md`
- Observer-specific README hunks only

Prepare a separate delivery integration scope: `backend/app.py` file-preview validation, `backend/tests/test_delivery_contracts.py`, the inspected existing frontend edits, new frontend helper/contracts/env example, this guide and delivery README hunks. The frontend currently contains substantial preexisting uncommitted work: review its complete patch with the user before staging. Do not indiscriminately include all frontend files or root Node/Tailwind files. README spans both scopes and needs explicit hunk review. Exclude reports, backups, screenshots, .env, model binaries and all unrelated files.

PR plan: approve exact patches → focused local commits → isolated regressions and credential/artifact scan → approval to push and open PR targeting main → CI/PG/Docker verification → separate merge approval. No commit or publication occurred here. Live monitoring needs its own approval even after code merge.

## Figma mapping and minimal design work

Both exported ZIP references exist in `C:\Users\Saksham Sharma\Downloads`:

- `AI DevOps Mission Control.zip`, SHA-256 `f5b144303bf3413cb7a1d5981e44c4e4e27cc3ec8ea6c3e2a6c67fffbb7a6d45`
- `Upgrade Cloud-ByteXL Overview.zip`, SHA-256 `61362fce830c1cca118a1ccdc1369d9c98edf4139581e1bc3f1b155940dfc3d3`

Each is a 31-entry React/TypeScript Vite design export; `src/App.tsx` has no fetch calls. They are visual references, not completed backend integrations. No editable `.fig` file was found; it is not needed to apply these exported references. No required ZIP was missing. Neither ZIP was extracted over the application or executed.

| Design element | Existing destination | Minimum action |
| --- | --- | --- |
| Mission Control sidebar/status cards | `App.jsx`, `platform.css` | Preserve navigation/state; inspect wrapping and consistent spacing |
| Overview hero/metrics | `App.jsx`, `overview.css`, `repositoryData.js` | Keep actual source-derived values and unavailable states |
| Prediction/RCA panels | `AIIntelligence.jsx`, `ai.css` | Retain historical labels and visible evidence; align form spacing |
| Empty/error/loading/mobile states | `api.js`, existing JSX/CSS | Verify all breakpoints and keyboard focus; no new page shell |

Only small review-control styles were added now. Full fresh visual acceptance remains outstanding; existing media queries and successful builds do not establish responsive correctness.

## November 23–25 execution checklist

| Date / priority | Exact task and files | Dependencies | Completion evidence | Code changes? |
| --- | --- | --- | --- | --- |
| Nov 23 / critical | Review observer patches/scope above; prepare focused PR | User commit/push approvals | Reviewed diff, no generated/private files; CI after approved publication | Only verified defects if found |
| Nov 23 / critical | Configure intended demo PostgreSQL, authentic stored history/RCA and original model; `docs/LOCAL_OBSERVER.md`, AI CLI/Store | Approved separate demo DB and provenance; no personal DB reuse | Independent readback with real run/attempt/model IDs; no invented observations | Configuration first; reviewed import path only if needed |
| Nov 23 / critical | Walk repository → overview → AI history → saved RCA; `App.jsx`, `AIIntelligence.jsx`, `repositoryData.js` | Backend/frontend running on permitted origins; read-only GitHub access approval | Correct SHA, actual metadata/evidence, visible DB warning/error, repo switch clears old state | Small contract fixes only if demonstrated |
| Nov 23 / important | Decide whether legacy catalog persistence is required | Original authoritative schema unavailable in migrations | Either reviewed bootstrap from real schema or explicit source-analysis-only catalog limitation | Needed only if full legacy persistence required; never guess DDL |
| Nov 24 / important | Minimal ZIP-guided polish; `platform.css`, `overview.css`, `ai.css`, existing JSX | Actual-data journey working | Desktop/tablet/mobile screenshots at 1440/1024/768/390, keyboard/modal/table checks | Small spacing/wrapping fixes |
| Nov 24 / important | Check saved Gemini vs rules, guard rejection, unavailable metrics, timeout/permission errors | Authorized original reports and configured local API | No mislabeled AI, no preselected review, no fake progress/result | Only demonstrated UI defects |
| Nov 24 / conditional | Bounded genuine observer session | Separate live approval, valid clock proof/authentic model and dedicated DB roles | Ledger + independent readback before earliest job start; zero if no eligible run | Existing CLI, no new observer |
| Nov 25 / critical | Freeze and run full PG suite/frontend contracts/lint/build; smoke Docker | Isolated PG17; Docker Desktop daemon available | Exact totals, startup/health/cleanup evidence, no live provider calls | Fix actual failures only |
| Nov 25 / critical | Rehearse walkthrough and README/runbook; secret/artifact review | Intended demo environment and fresh browser check | Reproducible startup, labeled limitations, no private files in proposed commits | Documentation/correctness only |
| Nov 25 / optional | Reduce >500 kB JS warning; URL routing/deep links | Core acceptance complete | Build still passes, navigation preserved | Defer if delivery risk |

Do not make successful live prediction capture a prerequisite for an honest demonstration: zero independently verified observations is an acceptable disclosed result. Do not fabricate/fail workflows to fill that gap. Chat, new deployment telemetry, model replacement and major redesign are outside this deadline's core scope.

## Reproducible local setup and environment checklist

Run from the repository root in PowerShell. Use the existing environment if installed; never overwrite local .env files. The commands below prepare software and migrations, not live observation. Installing dependencies requires normal package-registry access.

```powershell
python -m venv backend/venv
.\backend\venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm --prefix frontend-app ci
```

Provision a **separate, explicitly approved local demo database** with PostgreSQL 17 and a dedicated application role. Set the following in the backend process environment; values are intentionally omitted:

| Variables | Requirement |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Explicit isolated/local demo connection; never point tests at personal/production DB |
| `PYTHON_DOTENV_DISABLED=1` | Prevent unintended backend/.env loading when using explicit configuration |
| `RCA_PROVIDER=none`, `CI_CALLBACK_ENABLED=0` | Safe initial demo: no live provider or external callback |
| `GITHUB_TOKEN` | Server-side read-only access when authorized; Actions/Contents read as needed; never a VITE variable |
| `AI_ALLOWED_REPOSITORIES` | Exact intended owner/repository identities |
| `AI_ADMIN_TOKEN` | Optional local AI administrator secret; enter only in in-memory administrator field; never in frontend files |
| `CORS_ORIGINS` | Match exact loopback UI origin; default ports 5173–5175 supported |
| `VITE_API_BASE_URL` | Public API origin, normally `http://127.0.0.1:5000` |
| Three `VITE_ENABLE_*` variables in frontend example | Leave false; do not retrain, generate live prediction or call configured provider |

`frontend-app/.env.example` contains only public configuration. Copy it to `.env.local` only if that destination does not already exist. Vite variables are embedded in browser code: never put database, GitHub or provider credentials there. Vite flags need a restart/rebuild; they do not enforce backend authorization.

```powershell
.\backend\venv\Scripts\python.exe -m backend.ai_intelligence.cli migrate
.\backend\venv\Scripts\python.exe -m flask --app backend.app run --host 127.0.0.1 --port 5000 --no-reload --no-debugger
# Separate terminal:
npm --prefix frontend-app run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Migrations install AI/callback tables, **not** the original users/repositories/deployments schema. Do not claim a complete fresh legacy installer. Repository analysis can succeed while catalog persistence fails; the UI now exposes that warning. Do not import saved model binaries without their authentic database metadata/feature version; never create fictitious training records to make the panel look ready. No automatic training command is part of this procedure.

## Demonstration walkthrough

1. Start the explicitly configured local database/backend/frontend. Confirm no unintended provider/callback/observer is running.
2. Enter the approved GitHub repository. Explain that source security/health checks are heuristics. Show analyzed SHA, actual files, warnings and source preview.
3. Open AI Intelligence. Read stored Actions attempts from PostgreSQL. If absent, show the empty state; request approval before live history synchronization. Repository analysis does not synchronously create a prediction and later RCA.
4. Show saved experimental historical metrics: 27 eligible runs, 16 training/5 validation/6 test; logistic accuracy 50%, failure recall 0%; dummy accuracy 66.7%, failure recall 0%. Both test failures were missed. These are prior historical results, not newly measured prospective accuracy. If model metadata is unavailable, show unavailable instead.
5. Select an actual failed run/attempt, show the saved report's engine/provider, diagnosis, evidence and guard status. Explain missing evidence and uncertainty; an accepted citation ID does not establish semantic support. Gemini quota/configuration errors must stay errors, never fabricated fallback prose.
6. Explain assisted RCA recommendations separately: 3 accept, 3 reject, 2 uncertain. Human worksheet remains unanswered; no independent human verification was performed. Do not submit the review form as part of automation.
7. Show zero genuine prospective predictions. A future approved local observer can save predictions and reconcile separate outcomes; only independently established pre-start records enter prospective evaluation.
8. Export/print source analysis if needed; clarify that this export is not the complete AI report/evidence ledger. Planned chat and inferred runtime architecture are not live services.

## Final acceptance and security checklist

- [ ] Fresh browser walkthrough with actual authorized DB contents; screenshots at four widths, loading, empty, errors, keyboard and repository switch.
- [ ] Docker daemon available; rerun existing CI-equivalent Docker build/start/health/cleanup without enabling external callbacks.
- [ ] Full backend `pytest backend/tests -q` with `AI_TEST_DATABASE=1` and explicit disposable PostgreSQL 17 connection variables. Never reuse demo/personal data for destructive tests.
- [x] Current full backend, frontend contracts/lint/build passed as recorded above.
- [ ] Original model/report provenance and application DB configuration approved for demo.
- [ ] Exact staged scopes reviewed; credentials, screenshots, backups, generated reports and binaries excluded; README hunks assigned correctly.
- [ ] Separate authorization before commits/push/PR/merge, and separate authorization before any live observer session.

Security posture: frontend contains no provider/GitHub/DB credentials; administrator input stays in memory. Rendered log text uses React text escaping. No ZIP code executed. Observer uses explicit allowlisting, scoped outbound GETs, bounded execution and separate database roles. Test fixtures are controlled evidence, not real prospective results. Historical RCA sources, assisted recommendations, blank worksheet and saved model artifacts remain separate and must retain their original hashes.
