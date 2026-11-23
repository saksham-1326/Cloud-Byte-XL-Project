# Cloud-ByteXL submission and demonstration package

Prepared November 23, 2026, for the November 26 deadline. This guide uses the
existing React/Vite application and authentic local PostgreSQL demo. It does not
start observation, train a model, call Gemini or submit human reviews.

## What is ready

The current browser rehearsal completed public repository analysis, showed its
expected PostgreSQL catalog-save warning, navigated to AI Intelligence and
displayed 27 unique historical runs / 28 attempts, experimental model metrics,
stored backtests and original RCA. Changing the failed attempt to #21 displayed
its saved diagnosis and cited log lines. Zero timing-matched shadow rows and
zero manual reviews were visible. Loading and empty-state text were observed.

Desktop 1440×1000, tablet 768×1024 and mobile 400×900 views rendered without
page-wide horizontal overflow. Mobile navigation opened/closed and the history
table scrolled horizontally to its later columns. No console errors were captured
in this session. These are focused checks, not comprehensive accessibility or
every-error-state certification. Citation evidence is inline: there are no
separate citation jump-links. External workflow links need internet access.

Seven local GET endpoints returned HTTP 200/SUCCESS: overview, runs, predictions,
models, rca, evaluation and outcomes under `/api/ai/v1/`, using
`?repository=saksham-1326/cloud-byte-xl-project`. All nine demo table hashes match
the approved authentic import. The SELECT-only role and both model artifacts
were verified. The demo has 12 historical backtests, 28 outcomes, 21 unverified
RCA reports, two original models and zero human-review submissions.

Current relevant offline regressions: **109 passed, 1 skipped**. The skip is
the explicitly opted-in PostgreSQL delivery-contract test; this invocation did
not enable destructive database tests. Frontend: **12 passed, 0 skipped**; lint
and production build passed. The build reports a nonblocking bundle-size warning
(JavaScript approximately 671 kB before gzip). Prior full hosted checkpoint of
285 backend passes and PostgreSQL/Docker verification remains historical evidence,
not a new full-suite result from this rehearsal.

## Exact launch instructions

Keep already running services. Check them before starting duplicates:

```powershell
Set-Location C:\Project\Cloud-ByteXL
& 'C:\Program Files\PostgreSQL\17\bin\pg_isready.exe' -h 127.0.0.1 -p 55439
(Invoke-WebRequest 'http://127.0.0.1:5173' -TimeoutSec 5).StatusCode
$r = Invoke-RestMethod 'http://127.0.0.1:5000/api/ai/v1/overview?repository=saksham-1326/cloud-byte-xl-project'
$r.status
$r.data.run_count
$r.data.attempt_count
```

Expected: accepting PostgreSQL connections, frontend 200, SUCCESS, 27 and 28.
If the existing isolated cluster is stopped, start it; never initialize, reset,
re-provision or migrate an existing source/demo database:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe' `
  -D 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\data-isolated' `
  -o '-h 127.0.0.1 -p 55439' `
  -l 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\acceptance-pg.log' -w start
```

Terminal A, only if Flask is stopped:

```powershell
Set-Location C:\Project\Cloud-ByteXL
.\backend\venv\Scripts\python.exe backend\reports\demo_provisioning\run_demo.py
```

The guarded launcher must confirm `cloud_bytexl_demo_20261123`, loopback port
55439 and the SELECT-only reader before serving. It uses protected local config,
disables dotenv loading/provider secrets/callbacks and denies AI mutations.
Do not substitute a plain Flask command or show the config during screen sharing.

Terminal B, only if Vite is stopped:

```powershell
Set-Location C:\Project\Cloud-ByteXL\frontend-app
$env:VITE_API_BASE_URL='http://127.0.0.1:5000'
$env:VITE_ENABLE_MODEL_TRAINING='false'
$env:VITE_ENABLE_LIVE_PREDICTIONS='false'
$env:VITE_ENABLE_PROVIDER_CALLS='false'
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `http://127.0.0.1:5173`. Do not run observer workers. Avoid Sync, Train,
Predict, Analyze failure and Submit review controls. Refresh intelligence is a
read-only saved-data refresh. Guarded backend denial is intentional if a disabled
operation is accidentally requested.

Stop only services you started: Ctrl+C in their Flask/Vite terminals. Leave the
shared PostgreSQL cluster running if any other local service uses it. After all
dependents are stopped, an operator may stop this isolated cluster with:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe' `
  -D 'C:\Project\Cloud-ByteXL\backend\reports\shadow_pg_check\data-isolated' -m fast -w stop
```

No credentials belong in launch commands, slides, screenshots or Git. This
machine's ignored guarded launcher/config and authentic demo data are required;
a clean clone alone does not reproduce the populated demo. See
[AUTHENTIC_DEMO.md](AUTHENTIC_DEMO.md) for provenance and setup safeguards.

## Seven-minute screen-by-screen script

| Time | Screen/action | What to say |
|---|---|---|
| 0:00–0:40 | Title and problem | Developers need a single place to inspect repository configuration, historical pipeline outcomes and evidence behind automated diagnoses. |
| 0:40–1:15 | Architecture | React/Vite calls Flask; Flask reads GitHub repository evidence and PostgreSQL history. Existing scikit-learn artifacts supply experimental prediction results; saved Gemini/evidence-rule reports are separate from new provider calls. |
| 1:15–2:00 | Connect repository → Overview | Enter `https://github.com/saksham-1326/Cloud-Byte-XL-Project`. Wait for real analysis. Show source/configuration findings and explain heuristic findings require review; test placeholders can trigger credential heuristics. |
| 2:00–2:30 | Overview warning → AI Intelligence | Explain that optional repository catalog persistence is unavailable in this SELECT-only AI demo. The visible warning does not mean the historical AI records are mock data. |
| 2:30–3:10 | Workflow execution history | Show 27 runs / 28 attempts. Run #27 has distinct failed first and successful second attempts. Opening a GitHub run link requires internet; local history does not. |
| 3:10–4:00 | Model evaluation → backtest table | Historical split: 16 train / 5 validation / 6 test. Logistic accuracy 50%, failure recall 0%; both actual test failures were missed. Dummy accuracy was 66.7%, failure recall 0%. Twelve saved rows span two model versions, not twelve independent held-out test cases. |
| 4:00–5:00 | RCA selector → #21 | Show original diagnosis, `exit 1`, the pytest pass line and process exit code. Citation IDs map to the displayed original snippets. Do not run new analysis or mark a review. |
| 5:00–5:30 | RCA #23 or #27 | Show observed HTTP 404 and curl exit 22. The exact server-side cause is unresolved. For #13, do not assert an independently proven compiler outcome. |
| 5:30–6:10 | Model registry and review metrics | Show persisted model identities, historical timestamps, unverified RCA and zero manual reviews. Explain immutable prediction fields, separate outcomes, exact attempts and read-only credentials. |
| 6:10–7:00 | Limitations and future work | No verified prospective predictions or independent human RCA accuracy. Timing gate remains closed. Future work is independent review, stronger timing evidence and more representative data—not an invented accuracy improvement. |

## Ten-slide speaking outline

1. Problem: fragmented repository/pipeline debugging and unsupported diagnosis risks.
2. Architecture: React/Vite → Flask → GitHub metadata and PostgreSQL; saved model
   artifacts and RCA evidence remain distinct components.
3. Repository analysis: source/configuration findings, transparent heuristic scoring.
4. GitHub Actions integration: preserved run/attempt identity, CI and durable
   callback implementation; live callbacks are disabled for the demo.
5. ML method: pre-outcome features, chronological split and experimental model.
6. Actual results: six historical test cases, 50% accuracy, zero failure recall;
   compare Dummy, disclose sample size and deliberately induced historical cases.
7. RCA: original saved diagnosis alongside cited logs and unsupported-claim limits.
8. Persistence/security: PostgreSQL, immutable prediction values, separate outcomes,
   read-only demo, isolated testing and credential exclusions.
9. Evaluation integrity: controlled regressions versus genuine independent review;
   no prospective or human-accuracy claim.
10. Limitations/future work: representative data, completed independent review,
    prospective timing proof, operational configuration and portable provisioning.

## Outage fallback and authentic evidence

New repository analysis requires GitHub connectivity. New Gemini output is not
part of this demo and requires separate approval. Saved AI data, API reads, model
artifacts, local screenshots and reviewer documents work without paid services.
An already connected/loaded browser view can continue locally; a fresh browser
may still need repository analysis before reaching AI Intelligence. Do not
promise a fully offline first-time UI journey.

If GitHub is unavailable, stop retrying and switch to the local overview API and
preserved evidence packet. Explicitly announce an API/document fallback. Current
browser captures are local ignored artifacts under
`backend/reports/final_submission_20261123/`: `desktop-ai.png`, `tablet-ai.png`,
`tablet-rca.png`, `mobile-ai.png`, `mobile-table.png`. They show genuine saved
records, not newly generated AI predictions. Existing screenshots under
`frontend-app/artifacts/` remain untouched. Never show private config/export files.

Use historical hosted CI evidence to explain Docker verification; do not claim
a local Docker pass. Neither CI checks nor rule fixtures establish general AI
accuracy. If local PostgreSQL is unavailable, use screenshots and source evidence
and clearly state that current persistence is not being demonstrated live.

## Reviewer handoff

Give an independent reviewer only [INDEPENDENT_REVIEW_HANDOFF.md](INDEPENDENT_REVIEW_HANDOFF.md)
and its three listed packet/template files. Do not give them the assistant
recommendations or existing answer-bearing review guides before assessment.
Both eight-row worksheets remain blank; the demo database has zero submitted
reviews. No independent human correctness percentage can be claimed.

## Technical questions and short answers

**Is the ML model accurate?** It is experimental. Historical accuracy was 50% on
six test cases, with zero failure recall; no prospective accuracy is established.

**Why is Dummy better on accuracy?** Most test outcomes were success. Predicting
success can score well while missing every failure, so recall/confusion counts
and the small denominator must accompany accuracy.

**Is RCA verified?** Reports preserve original diagnoses and citations. Citation
resolution and controlled rule tests do not prove semantic correctness. No
independent human review has been completed.

**What does a citation prove?** It identifies the source snippet. A reviewer must
still judge whether it supports the particular claim.

**Are the records authentic?** The demo is an approved read-only copy. Original
IDs, attempts, timestamps and model identities are preserved; nine table hashes
match its import receipt. Historical intentional test failures are not new
prospective evidence.

**Why is PostgreSQL saving unavailable?** The optional repository catalog uses a
legacy schema unavailable to this SELECT-only AI demo; historical AI GETs work.
We do not hide the warning or grant writes to make the presentation look better.

**Does the observer work?** Implementation, dry-run and controlled lifecycle
tests exist. No genuine prospective prediction is verified; the timing gate is
NO-GO. External timestamping is only a future proposal.

**Which token is used?** The prepared observer launcher uses `backend/.env` when
no process override exists. Byte-XL identity/restrictions remain unresolved until
the operator confirms that stored credential is the configured token. The demo
launcher clears inherited GitHub/provider secrets; this does not block saved data.

**Is it production-ready?** No. Sample size, failure recall, independent review,
prospective evidence and operational portability remain limitations.

## November 25–26 checklist

- Rehearse the seven-minute flow on the actual presentation machine and display.
- Verify the seven GETs, demo identity and disabled mutation behavior; keep private
  local setup securely available and never reset databases for rehearsal.
- Keep screenshots and reviewer packet locally available before testing outages.
- Retain the save warning and accurately describe heuristic findings.
- State zero prospective predictions and zero independent human reviews.
- Keep original models, source/demo databases, frontend and Figma assets intact.
- Obtain approval before any Git publication; no commit/push/merge is part of this
  preparation. Do not enable callbacks, observers, retraining or paid providers.
