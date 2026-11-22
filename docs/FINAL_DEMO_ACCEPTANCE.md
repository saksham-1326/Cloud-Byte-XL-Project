# Final demo acceptance — November 22, 2026

Deadline: November 26. **This document records the pre-copy acceptance snapshot.** The subsequently approved isolated data copy and current startup commands are in [AUTHENTIC_DEMO.md](AUTHENTIC_DEMO.md). The original database remains unchanged; the demo is now populated and API-verified. Browser acceptance remains pending. Nothing was committed or published.

## Verified status

| Requirement | Status | Evidence / limit |
| --- | --- | --- |
| Existing Vite service | PASS | Loopback port 5173 returned HTTP 200 |
| Existing Flask and isolated DB integration | PASS | Port 5000 AI overview returned HTTP 200, zero runs/predictions/reports and null model |
| Original application DB connectivity | PASS | PostgreSQL service running; localhost:5432 IPv4/IPv6 TCP accepted; authenticated read-only SQL succeeded |
| Original model artifacts | PASS | Both load through `ml.load_model`, including UUID/path/SHA-256 guards |
| Authentic historical data availability | PASS | Original DB: 28 runs, 28 outcomes, 12 backtest predictions, 2 models, 21 unverified RCA reports, zero RCA reviews |
| Isolated demo populated with authentic data | BLOCKED | Still empty; copying into it requires approval |
| Actual prediction eligibility | BLOCKED / not attempted | No eligible queued target verified; compatible metadata exists only in original DB |
| Browser acceptance / responsive layouts | BLOCKED | Prior Computer Use URL-safety stop; manual checklist below required |
| Docker | BLOCKED | Last check: Linux daemon pipe unavailable; not repeatedly retried |
| End-to-end browser demonstration | BLOCKED | Browser checklist and approved historical-data copy outstanding |

No new code changes or regression run in this task. Prior checkpoint remains **285 backend passes** (including 61 observer tests) and **12 frontend contract passes**, lint/build passed. Those are prior results, not a fresh acceptance run. Historical ML metrics remain unchanged; genuine prospective prediction count is zero.

## Why the earlier connection timed out

The timeout was an execution-environment restriction: sandboxed network access failed; the same local connection succeeded outside the sandbox. It was not evidence of a stopped PostgreSQL service, invalid password, or absent original data.

The file `backend/.env` supplies the password; host/port/name/user are absent, so `backend.app` uses its documented defaults (`localhost`, `5432`, `bytexl`, `postgres`). The diagnostic process had no DB overrides and no PG service/host/SSL overrides. The running acceptance Flask process was deliberately started with explicit isolated DB environment settings; it does **not** expose original DB records.

Read-only original access was enforced with `default_transaction_read_only=on` and a short statement timeout, and confirmed by `SHOW transaction_read_only`. Authentication and SELECT permissions worked. The connection used no SSL on loopback. No SSL setting was weakened; remote access must follow the intended certificate/security policy. `get_db_connection` uses the five DB settings and a five-second connection timeout; libpq SSL configuration is separate (`PGSSLMODE`, etc.), not a documented `DB_SSLMODE` application option.

Original migration receipts 001–004 match checked-in checksums. There is **no receipt for 005** in the original database. Do not run the migration CLI against it to repair that during a demo. Keep durable callbacks disabled; any original-schema upgrade requires a separate reviewed approval. The original database is not disposable test infrastructure.

## Models and historical integrity

- `55ef22a1-2f30-47f2-95d8-bf12efaf6463`: experimental, artifact digest matches `075d37741200bb9aaf8939fd92ee621d5fe445a11842359ba443c3ad348660a7`, current `prequeue-v2-utc-standardized` feature metadata present.
- `5ce8fe38-7217-458d-b547-a6458efb5d88`: experimental, digest matches `325c2d412cded573c049c5b5bd49740a6d00fcdba4e0b341c56ddf636affa018`; feature-version metadata absent, so current service does not select it as compatible.

Artifact loading is not metadata installation and does not prove a new target is eligible. Prediction also requires a currently queued run with consistent SHA/attempt, permitted repository, compatible metadata, non-overlapping training cutoff, pre-outcome features and subsequent state checks. None was attempted here. Never invent metadata or run training to populate the demo.

All 12 original predictions are `backtest` / `historical_backtest`; none is a prospective shadow record. Every prediction has an associated model and exact repository/run/attempt outcome (zero missing associations). Six of these twelve stored rows match their outcomes; **this aggregate mixes historical records and must not replace the six-run selected-model evaluation** or become a new accuracy claim. The historical six-test-run logistic accuracy remains 50%, failure recall 0%; dummy accuracy 66.7%, failure recall 0%.

Saved RCA covers failed workflow numbers 4, 8, 13, 21, 23 and 27. All 21 reports remain unverified, with zero rows in `ai_rca_reviews`. The separate assisted recommendations and unanswered worksheet remain separate from those API records.

## Authentic data recovery — approval required before writes

Recommended destination: a new explicitly named dedicated demo database (for example `cloud_bytexl_demo_20261123`), not the original `bytexl` database and not the destructive regression-test database. The currently running empty test-backed UI can be used for empty-state acceptance until that is approved.

Proposed concrete scope:

1. Open one read-only, repeatable-read source transaction for repository `saksham-1326/cloud-byte-xl-project`. Export **data only** from `ai_runs`, `ai_jobs`, `ai_steps`, `ai_snapshots`, `ai_features`, `ai_models`, `ai_predictions`, `ai_outcomes`, and `ai_rca_reports`. Preserve UUIDs, attempts, SHAs, JSON feature versions/provenance, original timestamps, probabilities and backtest/verification states. Do not copy user, deployment, credential, task-queue or review tables. Do not execute queued work.
2. Write a private local export under ignored reports; record snapshot time, source identity (without credentials), table/column lists, repository filter, row counts, canonical row hashes and export SHA-256. Keep it out of Git and screenshots.
3. Inspect logs/payloads for secrets and personal data before use. Keep an access-controlled unmodified original export if authorized. If redaction is needed, generate a separate clearly labeled display copy plus redaction manifest; preserve record IDs and distinguish changed evidence hashes from source hashes. Do not silently modify source reports or claim a redacted copy is byte-identical evidence.
4. **After approval**, create the dedicated demo database/role and apply current migrations there only. Verify destination identity, schema and emptiness. Import explicit columns in dependency order: runs; jobs/steps; snapshots/features; models; predictions/outcomes; RCA reports. Use one transaction and fail on conflicts; no truncate, delete, upsert overwrite, timestamp regeneration, new IDs or disabled constraints. No original DB writes.
5. Verify exact counts/key sets, canonical hashes of unredacted values, FK associations, outcome joins, model UUID/digests, probabilities, prediction/creation timestamps and historical modes through an independent connection. Verify no shadow/pending rows or completed human reviews appeared. Artifact files remain unchanged at their verified original paths; any relocation must preserve content digest and be explicitly documented.
6. Point Flask at the approved demo database, keep `RCA_PROVIDER=none`, callbacks off and frontend action flags false. GET overview must expose authentic model metrics/runs/reports. No sync/train/predict/RCA-generation/verify POST is required to view these records.

The export/import is **proposed, not executed**. Table counts and available data were read directly, not reconstructed from screenshots. A separate recovery implementation/review is needed before executing this plan. Minimum model setup is copying the authentic compatible `ai_models` row with its original UUID/digest/metrics/timestamps into the approved demo schema, preserving its existing artifact; do not synthesize a row from filename alone.

## Windows startup commands

Existing services currently respond at `http://127.0.0.1:5173` and `http://127.0.0.1:5000`. Preserve them; do not start duplicates. These PowerShell checks are read-only:

```powershell
Set-Location C:\Project\Cloud-ByteXL
(Invoke-WebRequest http://127.0.0.1:5173 -TimeoutSec 5).StatusCode
$r = Invoke-RestMethod 'http://127.0.0.1:5000/api/ai/v1/overview?repository=saksham-1326/cloud-byte-xl-project'
$r.status
$r.data.run_count
Get-Service postgresql-x64-17
```

If the previously approved isolated cluster is stopped, its exact startup is below. Do not use this cluster for authentic demo imports while it is used for destructive regression tests:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe' `
  -D 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\data-isolated' `
  -o '-h 127.0.0.1 -p 55439' `
  -l 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\acceptance-pg.log' -w start
```

For restarting **only a stopped** acceptance backend, terminal A:

```powershell
Set-Location C:\Project\Cloud-ByteXL
$env:PYTHON_DOTENV_DISABLED='1'
$env:DB_HOST='127.0.0.1'
$env:DB_PORT='55439'
$env:DB_NAME='cloud_bytexl_ci_test'
$env:DB_USER='cloud_bytexl_ci'
$dbCredential = Get-Credential -UserName $env:DB_USER -Message 'Existing isolated database credentials'
$env:DB_PASSWORD=$dbCredential.GetNetworkCredential().Password
$env:RCA_PROVIDER='none'
$env:CI_CALLBACK_ENABLED='0'
$env:AI_ALLOWED_REPOSITORIES='saksham-1326/cloud-byte-xl-project'
# Suppress inherited provider credentials; default demo performs no provider calls.
Remove-Item Env:GEMINI_API_KEY,Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
.\backend\venv\Scripts\python.exe -m flask --app backend.app run --host 127.0.0.1 --port 5000 --no-reload --no-debugger
```

After approved demo provisioning, replace only the explicit connection settings with that dedicated demo identity. Do not omit them and accidentally fall back to the original .env. No migration/sync/train/worker/observer command belongs in ordinary demo startup. Do not paste secrets into output or screenshots.

Terminal B, if Vite is stopped:

```powershell
Set-Location C:\Project\Cloud-ByteXL\frontend-app
$env:VITE_API_BASE_URL='http://127.0.0.1:5000'
$env:VITE_ENABLE_MODEL_TRAINING='false'
$env:VITE_ENABLE_LIVE_PREDICTIONS='false'
$env:VITE_ENABLE_PROVIDER_CALLS='false'
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

No credential belongs in a VITE variable. Backend checklist: explicit five DB variables, `PYTHON_DOTENV_DISABLED`, provider none, callbacks off, exact repository allowlist; optional `AI_ADMIN_TOKEN` if configured, server-side read-only `GITHUB_TOKEN` only when needed for the authorized repository analysis. Default CORS accepts loopback 5173; if using another port, configure its exact origin on Flask. Do not disable CORS or browser security. If admin authentication is required, enter only that admin token in the in-memory administrator field, never the GitHub/provider/DB secret.

## Manual browser acceptance checklist

Use Chrome on Windows, visiting the URL yourself. Keep DevTools Console and Network open. Save screenshots in ignored `frontend-app/artifacts/final-acceptance/`; record date, viewport, database mode and pass/fail in a local note. Do not capture authorization headers, tokens, credentials, unrelated tabs or unredacted sensitive logs. No screenshot exists from this task and no box below has been marked passed automatically.

| Check | Exact action and expected result | Screenshot |
| --- | --- | --- |
| Dashboard | Open `http://127.0.0.1:5173`; dashboard renders without blank screen/error overlay; missing repository data is not fabricated | `01-dashboard-desktop.png` |
| Repository input/loading | Enter `https://github.com/saksham-1326/Cloud-Byte-XL-Project`; submit once. Loading remains until request resolves; repository analysis uses real GitHub reads, not prediction/RCA generation | `02-analysis-loading.png` |
| Repository result | Metadata, source findings and analyzed SHA render. A failed catalog save is visibly warned, not reported as durable success. Open a file preview: source reference equals analyzed SHA | `03-analysis-result.png` |
| AI navigation | Click AI Intelligence; sidebar and page change correctly. Network GET overview targets port 5000 with correct repository. No automatic train/prediction/provider POST | `04-ai-navigation.png` |
| CI history | Empty DB: explicit no-stored-attempts message. Approved populated DB: actual run number/ID, attempt, completed status/outcome correspond to stored records; no simulated stages | `05-ci-history.png` |
| Historical model | Empty DB: unavailable/not-trained state, no invented score. Populated DB: compatible model UUID/experimental historical metrics; no prospective accuracy. Backtest rows must not appear as prospective shadow probabilities | `06-historical-model.png` |
| RCA/evidence | Empty DB: no stored report. Populated DB: select failed #21/23/27; verify run/attempt, engine/provider, diagnosis, full citation IDs/text, automated guard status and unverified review state. Read cited text before accepting support | `07-rca-evidence.png` |
| Review safety | Choices initially unanswered; submit disabled without all choices/name/acknowledgment. Do not submit a review for this acceptance exercise | `08-review-unanswered.png` |
| Errors | Invalid repo URL: actionable validation error. Use DevTools Network Offline temporarily, then Refresh intelligence: clear network error, no success/fake result; restore Online and refresh. Do not trigger generation actions | `09-network-error.png` |
| Loading/pending | DevTools Slow 3G + Refresh shows loading; restore No throttling. If an authentic pre-existing pending result exists, it must say pending. Do not create a task/prediction solely for this screenshot; otherwise mark pending acceptance untested | `10-loading.png` |
| Navigation/layout | Visit overview, CI/CD, AI, security and reports; back through sidebar. No click obstruction, overlapping panels or cropped critical text. Table horizontal scrolling may be intentional | `11-navigation.png` |
| Responsive | Device toolbar: 1440×900, 1024×768, 768×1024, 390×844; refresh/check sidebar or collapsed navigation, modal, tables and RCA. No inaccessible controls or full-page accidental horizontal overflow | `12-desktop.png`, `13-tablet.png`, `14-mobile.png` |
| Console | Clear Console, repeat navigation/analysis/AI refresh. No uncaught exceptions, React render failures or failed module loads. Record actual warnings separately | `15-console.png` |
| Network | Check repository POST, source-preview POST and overview GET responses. Success must contain JSON SUCCESS; distinguish expected invalid-input/offline/permission errors from unexpected 500/CORS/mixed-content failures | `16-network.png` |

Browser acceptance passes only after these observations, not HTTP 200 alone. Mark real-data checks blocked until the approved copy exists. Do not export a HAR containing credentials. Do not click Sync, Train, Predict, Generate or Verify during the read-only historical walkthrough.

## Reliable demonstration and fallback

With approved populated demo DB: start explicit isolated services → real GitHub repository analysis → show analyzed source SHA and heuristics → AI persisted attempt history → historical model metrics with small-sample/zero-failure-recall limitation → preserved failed run #21 and cited logs → guard/unverified status → explain zero genuine prospective predictions. Prediction and eventual RCA are separate operations; no new execution or provider request is necessary.

Without data-copy approval: show the actual running empty-state UI and API (do not call it populated), then open `backend/reports/independent_review/REVIEW_GUIDE.md` and `REVIEW_PACKAGE.md` for preserved real #13/#21/#23/#27 evidence. Show `backend/reports/historical_ml_replay.json` as saved historical replay. If GitHub is unavailable, stop repository analysis at its honest error and continue with these local files; this fallback is a document demonstration, **not an offline live-application data mode**. No fallback importer or fake API exists.

Preserve run #13 compiler uncertainty and unknown exact server-side HTTP 404 causes. Assisted recommendations remain 3 accept, 3 reject, 2 uncertain; they are not independent human verification. The worksheet remains unanswered. Never generate a replacement explanation if Gemini is unavailable.

Remaining critical blockers: manual browser/responsive acceptance, approval and reviewed execution of authentic data copy, final populated-DB readback/UI check. Docker's current daemon remains an environment blocker; previous main CI run `44879776217` recorded build/start/health/cleanup and 212 passing tests, not a fresh local Docker check. Historical CI evidence: https://github.com/saksham-1326/Cloud-Byte-XL-Project/actions/runs/44879776217.
