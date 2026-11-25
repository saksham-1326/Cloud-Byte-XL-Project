# Vercel + Render deployment preparation

Prepared November 24, 2026. No resources have been created and no deployment is
authorized by this preparation. The existing React/Vite UI is retained. The
final submission ZIP/report remain frozen. AWS, Docker Compose and Nginx are
not required for this deployment.

## Architecture and exact settings

Browser -> Vercel static React application -> HTTPS Render Flask/Gunicorn ->
dedicated managed PostgreSQL database, using a SELECT-only application role.
Repository analysis additionally makes read-only GitHub API requests.

| Render setting | Value |
| --- | --- |
| Repository | `saksham-1326/Cloud-Byte-XL-Project` |
| Branch | Approved deployment revision on `main`; resources remain uncreated |
| Root directory | Repository root, leave dashboard field empty |
| Runtime | Python 3.13.14, native Python service |
| Build | `pip install -r backend/requirements-production.txt` |
| Start | `gunicorn --config gunicorn.conf.py backend.wsgi:app` |
| Bind | `0.0.0.0:$PORT`, default 10000 |
| Concurrency | One worker, four threads; 120-second worker timeout |
| Health check | `/readyz` |
| Auto deploy | Off; explicit approved deployments only |
| Plan | Free for an academic demonstration, subject to limits below |

`render.yaml` describes these settings but importing a Blueprint would create
resources: do not import it before approval. No database is declared in it.
Gunicorn is pinned in the production requirements. Local `python backend/app.py`
remains a development entry point and must not be used to serve a public site.
Gunicorn process execution requires Linux; the new CI smoke test verifies its
binding, health and route gate without contacting a database or GitHub.

| Vercel setting | Value |
| --- | --- |
| Project root | `frontend-app` |
| Framework / Node | Vite / Node.js 22.x |
| Install | `npm ci` |
| Build | `npm run build` |
| Output | `dist` |
| SPA fallback | `frontend-app/vercel.json` rewrites application paths to `/index.html` |
| API routing | Direct HTTPS calls to Render, no localhost proxy |

Use an exact, stable Vercel production origin in backend CORS. Preview origins
are not implicitly trusted. Add an individual preview origin only after review;
never allow `*.vercel.app`. Changing a Vite environment variable requires a new
build/deployment. CI uses `https://backend.example.invalid` solely as a build
fixture; it must never be used for a real deployment.

## Environment variables (names and safe settings)

Set these in Render's server-side environment, not in Git:

| Name | Setting |
| --- | --- |
| `DATABASE_URL` | Provider TLS connection URL for dedicated SELECT-only reader; secret |
| `DB_SSLMODE` | `require` minimum; prefer provider-supported `verify-full` with its trusted CA |
| `PUBLIC_DEMO_MODE` | `1`, required by hosted entry point |
| `CORS_ORIGINS` | Exact `https://<approved-vercel-domain>`, no trailing slash |
| `AI_ALLOWED_REPOSITORIES` | `saksham-1326/cloud-byte-xl-project` |
| `RCA_PROVIDER` | `none` |
| `CI_CALLBACK_ENABLED` | `0` |
| `FLASK_DEBUG` | `0` |
| `PYTHON_DOTENV_DISABLED` | `1` |
| `PYTHON_VERSION` | `3.13.14` |
| `PORT` | Supplied by Render; do not hardcode a localhost bind |

Do not upload `.env`. `DATABASE_URL` takes precedence over legacy `DB_*` settings.
Keep `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`, `CI_STATUS_TOKEN`, `AI_ADMIN_TOKEN`,
`OPENAI_API_KEY`, `GEMINI_API_KEY` and provider model credentials unset. Public
repository analysis can use unauthenticated GitHub reads, subject to GitHub rate
limits. A token is not required for the initial public demonstration. No observer
or scheduler is launched by WSGI. Never put database-owner credentials on Render.

Set these public build-time values in Vercel for the intended environment:

```text
VITE_API_BASE_URL=https://<approved-render-service>.onrender.com
VITE_ENABLE_MODEL_TRAINING=false
VITE_ENABLE_LIVE_PREDICTIONS=false
VITE_ENABLE_PROVIDER_CALLS=false
```

No `/api` suffix. Production builds reject missing, local, HTTP or path-bearing
API origins. All `VITE_*` values are public in browser bundles: never place secrets
there. `backend/.env.example` and `frontend-app/.env.example` document local
defaults separately.

## Clean PostgreSQL initialization — no legacy dump needed

The old AI migrations assumed the five original application tables already
existed. The checked-in `backend/schema/legacy_v1.sql` now supplies schema only:
five tables, keys, sequences and relationships, with **no historical records**.
`backend.bootstrap` creates that baseline and applies existing migrations 001–005
in one transaction. It validates key columns/types/primary keys, stores a baseline
SHA-256 receipt, and reuses the existing checksummed migration receipts.

Run only against a **new, empty, dedicated hosted database**. The command requires
an explicit name matching `current_database()`. An existing nonempty database
without its bootstrap receipt is rejected. Repeating the command on its own
initialized database is safe; checksum mismatches fail. It never starts during
web import, build or startup. There are no copied private records.

After separate approval to create the database, select PostgreSQL 17 if offered
and obtain the provider's direct owner connection URL through its secure console.
Do not copy an original/demo/observation URL. From the repository root on Windows:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DB_SSLMODE = 'require'
# Secure prompts avoid putting credentials into command history.
$owner = Read-Host 'NEW hosted database owner URL' -AsSecureString
$reader = Read-Host 'NEW reader password (at least 24 characters)' -AsSecureString
try {
    $env:DATABASE_URL = [System.Net.NetworkCredential]::new('', $owner).Password
    $env:PUBLIC_READER_PASSWORD = [System.Net.NetworkCredential]::new('', $reader).Password
    # Replace only with the NEW database name selected in the provider console.
    .\.venv\Scripts\python.exe -m backend.bootstrap --confirm-database '<new-database-name>' --create-reader cloud_bytexl_public_demo
    if ($LASTEXITCODE -ne 0) { throw 'Bootstrap/reader creation failed; stop deployment.' }
} finally {
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:PUBLIC_READER_PASSWORD -ErrorAction SilentlyContinue
    $owner.Dispose()
    $reader.Dispose()
}
```

This prompts for secrets without displaying them; they necessarily exist briefly
in the child process environment. Do not record the session or print the values.
Use a provider-generated strong password. `--create-reader` requires permission
to create a role and grant SELECT. The reader is NOSUPERUSER/NOCREATEDB/NOCREATEROLE,
has SELECT on current tables, and defaults to read-only transactions. It receives
no INSERT/UPDATE/DELETE grants. Role creation is a separate transaction after
schema bootstrap. If that step fails, the schema may already be initialized;
stop and inspect rather than recreating databases. Re-run bootstrap **without**
`--create-reader` to validate its receipt. An existing reader role is rejected,
never silently rotated. Provider-specific role restrictions require an approved
equivalent SELECT-only role created in that provider's console; do not fall back
to an owner runtime URL. Future tables need explicit reader grants after review.

Configure Render's URL with that reader identity, database name and TLS settings.
`/readyz` checks read-only transactions, five AI migration receipts, the repository
table and nonprivileged/non-INSERT reader permissions. `/healthz` checks only that
the process responds. A failed readiness check returns a generic 503 with no DSN.

The disposable PostgreSQL tests cover empty initialization, repeatability, genuine
repository persistence, existing-database refusal, wrong-name refusal, checksum
mismatch, whole-bootstrap rollback and SELECT-only reader readiness. Bootstrap
does not import model metadata or artifacts and does not make a model eligible
for inference. Inference is disabled in this deployment.

## Provider choice and expected costs

Recommendation: **Neon Free PostgreSQL** for a small academic demo, in a region
near Render. Its current free offer is $0 with no time limit, 1 GB storage and
100 CU-hours per project per month. Confirm role-creation support and connectivity
before deployment. Usage limits and scale-to-zero can cause cold-start latency.
[Neon pricing](https://neon.com/pricing).

Vercel Hobby + Render Free + Neon Free can have a $0 base hosting bill within
their respective eligibility and quotas. This is not a guaranteed always-on SLA
or unconditional zero-cost promise. Check account terms and usage before enabling
resources. Render Free sleeps after 15 minutes of inactivity, shares 750 free
instance-hours per workspace/month, has ephemeral disk and can suspend on quota
exhaustion. Bandwidth/build overages can incur charges if billing is enabled;
configure spending controls. Render Free PostgreSQL expires after 30 days and
does not provide backups, so it is a less suitable persistent submission demo.
[Render free limits](https://render.com/docs/free),
[Vercel Hobby terms and quotas](https://vercel.com/docs/plans/hobby).

Paid plans are optional and require explicit approval and a current dashboard
quote. No paid plan, custom domain or upgrade is necessary for preparation.

## Approved demo data is a separate decision

A fresh database contains **zero historical runs/predictions/RCA**. The UI must
show its honest empty states. The authentic local demo (27 runs / 28 attempts,
12 historical backtests, 21 unverified reports) is not uploaded by bootstrap.

If public historical screens are required, prepare a separate, approved export:

1. Read the original through its existing read-only role. Select only the agreed
   repository's runs/attempts, outcomes, historical predictions, necessary model
   metadata and RCA/evidence relationships; no credentials, users or task payloads.
2. Produce a local record inventory, table/row hashes, source identity, collection
   time and redaction report. Review every publicly exposed JSON field: stored
   payloads can contain log text, internal paths and URLs. Do not assume the
   public route gate sanitizes historical payloads for publication.
3. Redact only approved sensitive fields. Preserve original IDs, attempts, model
   identity/digests and timestamps. Flag or omit records when redaction would
   break citations; never silently repair AI claims. Keep a separate provenance
   manifest linking original and exported hashes.
4. Obtain approval for the exact public dataset and destination **before upload**.
   Import transactionally using a temporary owner session, then verify counts,
   relationships, citations and hashes independently with the reader. Remove
   owner credentials afterward. No import utility or data dump is included here.
5. Historical backtests remain historical. No completed independent RCA reviews
   or verified prospective predictions may be invented. Do not upload model
   binaries; serving historical metadata is distinct from loading a trained model.

Until this review completes, use an empty hosted database and the unchanged
authentic local demo for historical presentation. Never point public services at
the existing private development, demo or observation databases.

## Public route and security boundary

| Allowed | Behavior |
| --- | --- |
| GET/HEAD `/`, `/healthz`, `/readyz` | Generic status, no credentials |
| GET/HEAD `/api/github/repository/latest` | Last in-memory public analysis; lost on restart |
| POST `/api/github/repository`, `/api/github/file` | Read-only GitHub access, exact allowlisted HTTPS repository |
| GET/HEAD `/api/ai/v1/{overview,runs,predictions,models,rca,evaluation,outcomes}` | Approved repository's stored history only |
| Everything else, including callbacks/webhooks/tasks/training/verification | Denied before service work |

Repository analysis returns an explicit read-only catalog-save warning. It is
not persisted in the hosted demo. Request bodies are limited to 64 KiB. Error
responses are generic for server failures; logs redact credentials and omit query
strings, bodies and authorization headers. Flask debug is off, CORS is an exact
origin list and DB sessions are read-only with bounded statement/connect timeout.
CORS is not authentication; these routes intentionally expose the approved demo
data publicly. Do not store private records in this database.

This profile is an academic read-only demonstration, not a multi-tenant platform.
There is no distributed rate limiter; public GitHub analysis can exhaust API or
hosting quotas. Keep the allowlist narrow, avoid privileged GitHub credentials,
monitor provider quotas, and suspend the service if abused. Free-tier memory,
cold starts and large analysis timeouts need a real hosted smoke test. No new
prospective timing qualification is claimed. Historical ML accuracy remains 50%
on six test runs, failure recall 0%; independent reviews/prospective results zero.

## Deployment sequence — requires approval and account authorization

1. Review local diff/tests and approve a focused commit/push. Require green
   backend/PostgreSQL, frontend and the new Linux Gunicorn smoke checks on that
   exact revision. No GitHub workflow has been triggered by this local work.
2. Authorize Render and Vercel GitHub integrations for this repository only. Do
   not add database/provider secrets to GitHub or frontend build environments.
3. Approve creation of the selected new managed database, bootstrap/reader setup
   and explicit destination identity. Obtain any provider network-access grants.
4. Reserve the Vercel project/domain without assuming preview domains are final.
   Approve the Render service creation with auto deploy off, the reader URL and
   exact Vercel CORS origin. First creation can deploy immediately: approval must
   precede it. Use no predeploy migration/build-time DB writes.
5. Confirm Render `/healthz` and `/readyz` return 200, AI history GETs show empty
   success, write routes return 403, unknown repositories fail, and unapproved
   origins receive no CORS permission. Inspect logs without exposing secrets.
6. Set Vercel's actual Render URL and all three UI flags false, then approve its
   deployment. Verify browser Network requests use Render, SPA refresh/navigation,
   repository analysis, empty AI history, and desktop/tablet/mobile views. Neither
   cloud runtime nor browser cross-origin behavior has been verified here.
7. Optionally follow the separate public-data approval procedure above. Record
   deployed SHAs, schema receipts, provider regions and smoke-test evidence.

## Rollback

Stop exposure first by suspending the Render service or disabling its public
deployment; do not reconnect a private database. Vercel can promote the previous
known-good deployment, but an old local-only frontend/API configuration is not a
valid public rollback. Render can roll back to a previously verified hosted-safe
build only (Free limits the available history). Keep auto deploy off. Schema
changes are additive/checksummed and are not automatically reversed. Never drop
or restore a database as an application rollback. For a failed bootstrap, its
schema transaction rolls back; investigate identity/receipts before retrying.
Any provider credential rotation or data restore needs separate authorization.

## Local verification commands

```powershell
# Existing isolated-PostgreSQL test harness supplies its own DB_* credentials.
# Never set AI_TEST_DATABASE=1 against a personal or hosted database.
.\.venv\Scripts\python.exe -m pytest backend/tests -q
Push-Location frontend-app
npm ci
npm test
npm run lint
$env:VITE_API_BASE_URL = 'https://backend.example.invalid' # local build fixture only
npm run build
npm audit
npm audit --omit=dev
Remove-Item Env:VITE_API_BASE_URL
Pop-Location
```

On a disposable Linux CI environment with production requirements installed:
`python -m backend.tools.check_wsgi`. This process smoke checks Gunicorn and
public-route denial, not hosted PostgreSQL availability. See the task report for
actual test results; do not count a prepared CI step as an executed cloud test.

Platform references: [Render Flask](https://render.com/docs/deploy-flask),
[Render Blueprint settings](https://render.com/docs/blueprint-spec),
[Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite).

## Recorded preparation results and file scope

- Complete backend suite: **297 passed, 0 failed, 0 skipped, 0 expected failures**
  in a new standalone PostgreSQL 17 cluster on loopback port 55442. The cluster
  and generated password file were removed after shutdown. Original/demo/
  observation databases were not used for test writes. There are 68 existing
  joblib/NumPy deprecation warnings. A final connection-timeout keyword correction
  was followed by 12 passing hosted/API regressions; these are not added to the
  full-suite total.
- Frontend: **15 passed, 0 failed/skipped**, lint passed, production build passed.
  Existing approximately 672 kB bundle warning remains nonblocking. Three new
  tests check rejected production API configurations.
- Fresh full and production-only npm audits: **0 vulnerabilities each**. No
  dependency or lockfile upgrade was made. Gunicorn 27.0.1's public wheel and
  Python compatibility metadata were verified without installing it locally.
- Production WSGI import, exact-origin CORS and blocked routes passed using the
  real Flask application test client. Vercel configuration instance validation
  passed against its public JSON schema. No Vercel/Render runtime was started;
  Linux Gunicorn process smoke and actual provider connectivity remain pending.
- Credential-pattern scan of changed/untracked candidate text found only five
  intentional fake credential-URL fixtures in tests/the Linux smoke helper;
  no real credentials or private keys were found. This is a scoped pattern scan,
  not a claim of a complete security audit.
- Frozen submission ZIP and all 34 packaged manifest entries match. Existing
  original-checkout preservation manifests (81 and 44 files, including evidence
  and saved models) have zero mismatches. No files were staged or committed.

Files changed for this preparation:

```text
.github/workflows/ci.yml
README.md
backend/.env.example
backend/ai_intelligence/api.py
backend/app.py
backend/bootstrap.py
backend/database.py
backend/hosting.py
backend/requirements-production.txt
backend/schema/legacy_v1.sql
backend/tests/test_bootstrap_postgresql.py
backend/tests/test_hosted_preparation.py
backend/tools/check_wsgi.py
backend/wsgi.py
docs/VERCEL_RENDER_DEPLOYMENT.md
frontend-app/.env.example
frontend-app/src/api.js
frontend-app/tests/production-config.test.mjs
frontend-app/vercel.json
frontend-app/vite.config.ts
gunicorn.conf.py
render.yaml
```

The pre-existing untracked `docs/DOCKER_READINESS_ASSESSMENT.md` and prior README
rehearsal content are preserved. Ignored local diagnostic reports are not commit
candidates. Public-provider accounts, repository integration grants, explicit
deployment approval, real domains/TLS database credentials and the fresh Linux
CI run are still required. Clean-database initialization is locally verified;
cloud deployment itself is unverified and has not started.


## Figma reconciliation and live deployment boundary — November 25

The frontend was published separately as b05325fef296b9990166a96ca18c65367497c500.
This deployment revision retains its React/TypeScript components and Tailwind 4
plugin. The original 22-file deployment scope now uses vite.config.ts instead of
the replaced vite.config.js; no old JSX frontend is restored. Source worktrees,
private records, model artifacts and frozen submission files remain untouched.
The public runtime uses a dedicated SELECT-only role. Before creating anything,
confirm the free plan, account owner, region, GitHub repository permissions and
exact resource names with the operator. No paid tier, provider key, observer,
training job or historical import is authorized by publication.

Local CLI credentials for Vercel, Render and Neon were not found in the checked
standard paths/environment. Browser account sessions have not been verified.
Account sign-in and resource approval remain required; GitHub publishing does
not authorize either. Current CI outcomes must be checked for each commit.


## Exact pending resource approval

Proposed resources (names subject to availability; do not silently substitute a
paid plan):

| Provider/plan | Resource | Region / access | Expected base cost |
| --- | --- | --- | --- |
| Vercel Hobby | One project `cloud-bytexl`, root `frontend-app`, static `dist` | Global CDN; public HTTPS frontend; personal non-commercial academic use only | $0 within Hobby eligibility/limits |
| Render Free | One native Python web service `cloud-bytexl-api` | Frankfurt if available; HTTPS public API; auto deploy off | $0 within confirmed workspace quotas |
| Neon Free | One NEW project `cloud-bytexl-demo`, PostgreSQL 17 database `cloud_bytexl_hosted` | Nearest mutually available EU region, preferably Frankfurt; dedicated SELECT-only `cloud_bytexl_public_demo` runtime role | $0 within Free plan quotas |

Before creating these, the operator must confirm account owners and free-plan
eligibility. Authorize repository access only to
`saksham-1326/Cloud-Byte-XL-Project`; inspect any requested provider GitHub App
permissions before granting them. Prefer an approved manual deployment when a
Git integration would automatically publish subsequent pushes. Do not authorize
organization-wide repositories, paid upgrades, a Pro trial, custom-domain
purchases or model/provider integrations. Stop if any creation screen indicates
charges or broader access.

Separate approval must include one-time schema-only bootstrap and creation of the
reader role in the NEW empty Neon database. No existing private database is an
eligible destination, and no historical records are approved for import. Keep
owner credentials only in that short-lived bootstrap session, not Render. Use
Neon's direct owner URL for bootstrap and the dedicated reader TLS URL for
runtime. Remove owner credentials from the session after verified receipts.

After resource approval: reserve the frontend domain/project without publishing,
bootstrap Neon, configure Render's reader secret plus exact frontend CORS origin,
then approve the Render release. Set the returned HTTPS API origin in Vercel and
approve its build/release. Verify /healthz, /readyz, CORS, read-only denials and
honest empty historical views before announcing the public URL. Region/domain
availability and provider permissions must be confirmed in the actual accounts;
this document does not claim those account checks have already passed.


## Reconciled publication checks — November 25

Frontend commit GitHub CI passed: backend 285 tests and both required jobs
successful, run https://github.com/saksham-1326/Cloud-Byte-XL-Project/actions/runs/45560810555.
The deployment candidate passed the full local backend suite: 297 passed,
0 failed/skipped/expected failures, 68 dependency deprecation warnings. Testing
used a brand-new PostgreSQL 17.10 loopback cluster with generated isolated
credentials, database cloud_bytexl_ci_test and independent identity verification;
it was stopped after testing. No authentic database was a test target.
Frontend: 24 contracts plus 23 React tests (47 passed), TypeScript, ESLint and
production build passed. npm audits are zero for full and production dependencies;
the dependency lockfile is unchanged from the audited frontend publication.
Linux Gunicorn execution and Docker checks are verified by GitHub CI, not claimed
as locally executed Windows checks. Deployment-revision CI must be confirmed
separately after its push. No cloud resources have been created.
