# Cloud-ByteXL — UI and hosted AI functional audit

**Date:** 2026-11-27. **Environment:** Vercel Hobby, Render Free, Neon Free.
**Scope:** Existing 12-route React workspace and the public read-only Flask API.

## Root cause and correction

The screenshot showed `Repository is not allowlisted`. The **public backend**
intentionally authorizes only `saksham-1326/cloud-byte-xl-project`, while the
Connect modal offered any repository without validating that restriction.
This generated a real Flask 403 and left the dashboard disconnected.

Corrective actions:
- Synchronized Render's `AI_ALLOWED_REPOSITORIES` to precisely
  `saksham-1326/cloud-byte-xl-project` (existing Free service).
- Pre-populate Connect Repository with the approved GitHub URL and validate
  it on the client; retain independent server-side enforcement.
- Accept harmless URL variants (case and `.git`) but reject other repos
  with explicit explanation **before** a network call.
- Replaced inert Profile/Team settings/Sign out menu buttons with an honest
  explanation (there is no public-demo login), a working GitHub source link,
  and a working Close menu action.

## Coverage matrix

| Function/route | Simulated tests | Live-production certainty |
|---|---|---|
| Connect repository | Allowed URL, forbidden URL, malformed URL, 403, success JSON | Render allowlist updated and Free service LIVE; public POST/browser still needs manual observation |
| Overview | Navigation, scan response contract, read-only notice | Rendered by Vercel; interactive browser acceptance not independently established |
| Repository | Route contract, cached repository result bindings | Requires successful production scan |
| Analysis | Route contract, 75s timeout/cancel, recovery | Backend source inspection bounded; production scan not independently timed |
| Issues | Navigation, issue review and modal wiring | No independent click-through |
| Security | Navigation, response-derived findings | No independent click-through |
| Recommendations | Navigation, repository findings | No independent click-through |
| Architecture | Navigation and existing source-derived mapping | No independent click-through |
| Docker | Navigation and static repository configuration inspection | **No remote Docker daemon control** |
| Kubernetes | Navigation and static configuration inspection | **No live cluster connection** |
| CI/CD | Navigation and saved GitHub Actions evidence | Historical data exists in Neon; no continuous monitoring SLA on Render Free |
| AI Intelligence | Mock overview, stored metrics, read-only gate, loading/error contracts | Historical models, predictions, RCA data verified in Neon; **0 verified prospective shadow predictions** |
| Reports | Export action and response-contract checks | Browser download acceptance not independently established |
| Profile and notifications | Inert profile buttons removed; legitimate UI actions wired | No authenticated account system in public demo |

## Regression checks

- Node's `node --test tests/*.test.mjs` covers the mocked API:
  success, HTTP 403, blocked mutation, network failure, invalid/non-JSON
  response, and historical intelligence. Also tests all 12 navigation
  destinations, recovery/cancel, visual read-only notice and honest demo
  account actions.
- Pytest `backend/tests/test_demo_repository_mock.py` covers the Flask
  allowlist, uppercase/canonical identity, invalid repositories, blocked
  AI writes and expected TLS configuration. No live GitHub or Neon writes.
- CI also runs frontend ESLint/Vite build and complete backend, Gunicorn,
  Postgres and Docker smoke tests.

**Limitations:** Mock pass does *not* certify every action in a real browser,
nor does it certify AI accuracy or an online LLM. The exposed public website
deliberately blocks paid provider calls and AI training mutations. The
historical predictor fails its evidence-based release gate and must not be
advertised as reliable for predicting future failures.

## Safe acceptance steps

1. Open `https://cloud-bytexl.vercel.app`, hard-refresh, select
   **Connect Repository**, use the prefilled approved URL and start analysis.
2. Confirm the Overview loads without the allowlist error and that navigation,
   file previews, findings and the JSON report work with the actual result.
3. Open AI Intelligence independently. Confirm historical record counts,
   release-gate explanation, RCA evidence and read-only behavior.
4. Check an unapproved repository is rejected with a helpful message. It must
   **not** bypass the backend restriction.
5. For any failure, use the specific browser network response and Render log;
   don't substitute a mocked PASS for proof of production success.
