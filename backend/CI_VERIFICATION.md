# CI verification and operation

The existing `.github/workflows/ci.yml` installs `backend/requirements.txt`, checks
installed dependency consistency, migrates an ephemeral PostgreSQL 17 service,
and runs `python -m pytest backend/tests/ -v` on Python 3.13.

The service owns database `cloud_bytexl_ci_test` and role `cloud_bytexl_ci` with
public, test-only credentials. No GitHub database secrets are used. Test setup
ignores `.env`, restricts database integration opt-in to this local database/role,
and blocks unmocked urllib HTTP requests. Gemini/OpenAI tests use saved fixtures
and mocks; CI has no provider keys and never invokes live validation tools.

Docker still builds the existing Dockerfile, starts Flask, and polls HTTP `/`
for up to 30 attempts. This checks container startup, not a database connection
inside the application container. Cleanup runs even after failure and cannot
replace the original failure. `.dockerignore` excludes local environments,
credentials, logs, virtual environments, and generated artifacts.

## Optional dashboard callback

1. Configure `CI_STATUS_TOKEN` in the Flask server environment first. Without
   this setting the existing local callback behavior is preserved; do not expose
   the legacy unauthenticated endpoint publicly.
2. Add the identical value as repository Actions secret `CI_STATUS_TOKEN`.
3. Add repository Actions variable `CI_STATUS_URL` as the stable HTTPS URL ending
   in `/api/ci/status`, without query parameters or embedded credentials.

No URL means a successful skip. Configured callbacks require HTTPS and a token,
reject redirects, have a 15-second timeout, and report HTTP failure codes without
printing credentials or response bodies. Notifications run only on pushes, not
PRs. Their failure is visible as a warning and does not turn passing tests into
a failed pipeline. Payload fields and the Flask response contract are retained.
The backend checks Authorization when configured; GitHub webhook routes are
unchanged. Flask's existing callback acknowledges in-memory status even when its
legacy deployment database update fails; HTTP 200 does not prove persistence.

## Review and remote execution

Review all required AI modules, migrations, fixtures, and tests currently
untracked in the working tree before approving a commit. The expanded CI needs
these files in the eventual push. No commit/push or GitHub-hosted run is performed
as part of local verification. After approval, push the complete reviewed change
and inspect the resulting Actions run, including PostgreSQL and Docker steps.

## Local verification checkpoint — 2026-11-20

- Installed the exact backend requirements (including psycopg/binary 3.2.9).
- `pip check`: passed.
- Complete backend suite with PostgreSQL integration enabled: **121 passed**.
- Database: freshly initialized PostgreSQL 17 cluster, localhost:55439, dedicated
  CI role/database; migrations succeeded. Existing development databases were
  not used. Temporary server stopped after verification.
- YAML parsed with the existing frontend development YAML parser; no runtime
  dependency added.
- Docker execution unavailable: Docker Desktop Linux engine named pipe missing.
- No live LLM calls, commits, pushes, or GitHub-hosted CI runs performed.
- Official actionlint validator: passed (workflow structure/expressions; optional
  shellcheck/pyflakes integrations disabled because they are not installed).
