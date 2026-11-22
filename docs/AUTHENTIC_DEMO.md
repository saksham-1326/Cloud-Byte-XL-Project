# Approved authentic historical demo

The approved local copy is complete. This supersedes the empty-database status in the earlier delivery/acceptance snapshots. No browser acceptance is claimed.

## Database identity and safeguards

| Purpose | Target | Access |
| --- | --- | --- |
| Original application | Existing localhost PostgreSQL, port 5432 | Source connections enforced read-only; never migrated |
| Authentic demo | `127.0.0.1:55439`, database `cloud_bytexl_demo_20261123` | Separate generated credentials; Flask role `cloud_bytexl_demo_reader_20261123`, SELECT only, default transactions read-only |
| Destructive regression tests | Separate `cloud_bytexl_ci_test` | Never run tests against the populated demo |

The isolated server listens only on `127.0.0.1`. Demo database PUBLIC access was revoked; reader role has no superuser/create-role/create-database privileges. Private configuration and export are in ignored `backend/reports/demo_provisioning/`, whose Windows ACL is restricted to the current user and SYSTEM. Passwords are never printed. Do not publish or screenshot configuration/export contents. Existing source .env and model files were not modified.

## Verified imported data

| Table | Rows |
| --- | ---: |
| `ai_runs` | 28 attempts, representing 27 unique runs |
| `ai_jobs` | 28 |
| `ai_steps` | 407 |
| `ai_snapshots` | 27 |
| `ai_features` | 54 |
| `ai_models` | 2 |
| `ai_predictions` | 12 |
| `ai_outcomes` | 28 |
| `ai_rca_reports` | 21 |

One repeatable-read, read-only source transaction supplied explicit columns/values. Records were scanned for configured secret literals, common token/private-key/JWT/credential-URL patterns, authorization values and credential fields before export/import. No findings required redaction; no approved-scope records were omitted. This is a bounded scan, not a guarantee against every possible secret format. Users, deployment tables, tasks, human-review submissions and other unrelated records were excluded by design.

All nine destination table hashes match canonical source row hashes through an independent connection using the new reader credentials. This comparison includes UUIDs, run attempts, commit SHAs, feature/probability values, prediction timestamps, full RCA JSON/citations and review states. Canonical timestamps normalize UTC for comparison without changing stored instants. A fresh read-only source connection confirmed matching table hashes and unchanged original migration receipts after the copy. No source SQL writes occurred.

Original receipts 001–004 remain unchanged and match repository checksums. Official migrations 001–005 were applied only to the new database; all five destination receipts/checksums were verified. Callback tables are empty and callbacks remain disabled. No legacy users/repositories/deployment schema was fabricated.

Both original model artifacts pass `ml.load_model` identity/path/SHA-256 checks. The compatible experimental model remains `55ef22a1-2f30-47f2-95d8-bf12efaf6463`; the other original model is preserved but lacks the current feature-version metadata. No model was trained/replaced and no metadata was invented.

All 12 predictions remain `backtest` / `historical_backtest`, with unchanged timestamps/probabilities and matching model/run/attempt/outcome relationships. There are zero shadow predictions and zero prospective results. All 21 RCA reports remain unverified; `ai_rca_reviews` is empty. Eight original legacy review JSON values explicitly say `agent_log_comparison_not_human_verification`; they were preserved unchanged, not converted into human submissions. The offline human worksheet remains unanswered.

## Application and API checks

Flask was restarted only from the prior acceptance process, using the dedicated demo credentials. Its local launcher validates target identity, SELECT-only access and model digests **before** importing/starting the application. It disables .env loading and clears inherited PG routing/provider/GitHub secrets in that process. It sets provider none, callbacks off, and an explicit repository allowlist. It blocks mutating AI requests before worker execution; no sync, training, predictions, provider generation or review submissions can run through this launcher.

Seven GET endpoints returned HTTP 200 / SUCCESS:

- `/api/ai/v1/overview`
- `/api/ai/v1/runs`
- `/api/ai/v1/predictions`
- `/api/ai/v1/models`
- `/api/ai/v1/rca`
- `/api/ai/v1/evaluation`
- `/api/ai/v1/outcomes`

Use `?repository=saksham-1326/cloud-byte-xl-project`. Overview returns 27 unique runs / 28 attempts, 21 reports, 12 backtests, the authentic compatible model, zero evaluated live rows, null live metrics and zero human reviews. Across 21 reports, all **78 primary citation references resolve to evidence items in their original report**. Exact report hashes match the source. This does not establish that the evidence semantically supports each AI claim, nor prove browser hyperlinks work. Five mutation-denial probes returned 403 before service execution. Vite returned HTTP 200.

These are real local API/database verification checks, not a full regression rerun or browser acceptance. Prior regression checkpoint: 285 backend passes / 12 frontend contract passes. No application source or frontend was changed for this copy; generated local provisioning/launcher utilities and documentation were added.

## Exact Windows startup

The existing services currently run at `http://127.0.0.1:5000` and `http://127.0.0.1:5173`. Leave them running; do not start duplicates. The dedicated database belongs to the already running isolated PostgreSQL cluster. If that cluster is stopped, restart it without modifying databases:

```powershell
Set-Location C:\Project\Cloud-ByteXL
& 'C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe' `
  -D 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\data-isolated' `
  -o '-h 127.0.0.1 -p 55439' `
  -l 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\acceptance-pg.log' -w start
```

Terminal A, if Flask is stopped:

```powershell
Set-Location C:\Project\Cloud-ByteXL
.\backend\venv\Scripts\python.exe backend\reports\demo_provisioning\run_demo.py
```

This reads the protected local configuration without printing it and refuses any target other than the approved demo identity. Do not use the plain Flask CLI without explicit DB settings, and do not rerun `prepare_demo.py`: provisioning intentionally refuses an existing database/config rather than overwriting it. The local launcher/config/export are ignored artifacts, not a portable committed installer. Back them up securely if this machine is moved; a fresh-machine import needs explicit destination review.

Terminal B, if Vite is stopped:

```powershell
Set-Location C:\Project\Cloud-ByteXL\frontend-app
$env:VITE_API_BASE_URL='http://127.0.0.1:5000'
$env:VITE_ENABLE_MODEL_TRAINING='false'
$env:VITE_ENABLE_LIVE_PREDICTIONS='false'
$env:VITE_ENABLE_PROVIDER_CALLS='false'
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Read-only smoke check, without printing evidence or secrets:

```powershell
$r = Invoke-RestMethod 'http://127.0.0.1:5000/api/ai/v1/overview?repository=saksham-1326/cloud-byte-xl-project'
$r.status                # SUCCESS
$r.data.run_count        # 27
$r.data.attempt_count    # 28
$r.data.reports.Count    # 21
$r.data.predictions.Count # 12
(Invoke-WebRequest http://127.0.0.1:5173 -TimeoutSec 5).StatusCode # 200
```

## Manual demonstration still required

Follow the screenshot checklist in [FINAL_DEMO_ACCEPTANCE.md](FINAL_DEMO_ACCEPTANCE.md). Open the frontend yourself; repository analysis uses read-only public GitHub retrieval and may warn that legacy catalog persistence is unavailable in this AI-only, SELECT-only demo. That warning is expected and must remain visible. It is separate from the now-populated PostgreSQL-backed AI history.

Open AI Intelligence → actual attempt history → historical model/backtest table → failed run #21/#23/#27 → original RCA diagnosis, evidence IDs/log text and unverified status. Do not click mutation controls: they intentionally return a read-only-demo error. Do not submit a human review. Verify navigation/loading/error states, console/network results and desktop/tablet/mobile screenshots manually; automation remains blocked by the earlier URL-safety limitation.

Historical logistic accuracy remains 50% on six test runs with failure recall 0%; no prospective accuracy exists. Keep #13 compiler uncertainty and exact HTTP 404 server-side causes unresolved. If GitHub is unavailable, use the already-preserved review guide/package and saved historical replay as explicitly labeled documents, not simulated new AI output.

Subsequent manual acceptance reported by the user: desktop AI historical views, mobile 400px navigation/table scrolling and tablet 768px RCA/table interactions passed, including historical ML/RCA/citation rendering. See [FINAL_RELEASE_REVIEW.md](FINAL_RELEASE_REVIEW.md) for the remaining demo rehearsal checklist and safe shutdown steps. Local Docker remains unavailable. Database population and API integrity are complete. The data-copy task made no commit/push, deployment, live observation or Gemini call; the later release commits and publication approval are recorded in the release review.
