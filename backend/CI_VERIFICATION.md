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

## Durable callback development

External delivery is disabled in the current development workflow. The sender
also defaults to disabled. The full backend suite includes authenticated
sender/Flask/PostgreSQL verification over isolated loopback, including a separate
Flask process restart. See `backend/DURABLE_CI_CALLBACKS.md` for the new versioned
endpoint, registration, receipt migration, transaction guarantees, and limitations.
The legacy callback endpoint remains compatible but is not used for durable
acknowledgment. Do not configure a public callback URL or expose the local server.

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
