# Cloud-ByteXL Frontend — Mission Control UI

This is the user-provided **Cloud-ByteXL-Frontend-UI.zip** React 19 + Vite 8 frontend integrated into the existing Cloud-ByteXL repository. It replaces the previous frontend UI only, keeping Flask, Render, Neon PostgreSQL, the existing inference/quality guards and repository-analysis APIs unchanged. The interactive landing page and Mission Control workspace come from the uploaded design.

## Run locally

```bash
cd frontend-app
npm ci
npm run dev
```

Set `VITE_API_BASE_URL` to the existing Flask origin, e.g. `http://127.0.0.1:5000`. For production Vercel this must be `https://cloud-bytexl-api.onrender.com` (no `/api` suffix). `npm test`, `npm run lint` and `npm run build` are required before deployment.

## Production security and limitations

The public hosted demo is **read-only**. Set `VITE_ENABLE_ADMIN_ACTIONS=false`, `VITE_ENABLE_MODEL_TRAINING=false`, `VITE_ENABLE_LIVE_PREDICTIONS=false`, and `VITE_ENABLE_PROVIDER_CALLS=false`. Backend AI worker and GitHub synchronization operate behind a separate restricted server-side Neon role. The frontend only reads persisted results and can request safe repository analysis. Live training, mutations, Gemini provider calls and unvalidated predictions are **not** activated by cosmetic buttons. No secrets go into `VITE_` variables or frontend source.

The AI Intelligence screen shows actual stored model history, chronological holdout, observed RCA evidence and quality gate. The rolling replay is retrospective rather than independent real-time proof. Do not claim high prospective failure prediction accuracy unless supported by new evaluation. Docker/Kubernetes/cloud actions that lack a live backend integration must be presented as informational, not as deployed infrastructure controls.

Hosting remains Vercel Hobby frontend + Render Free backend + Neon Free PostgreSQL; paid upgrades are not authorized.

## Unified mission-control interface (November 2026)

The entire application shares the same visual language as the new Cloud-ByteXL mission-control design: cyan and violet accents, midnight glass panels, a common workspace identity/banner, consistent page breadcrumbs, navigation, responsive cards, repository analysis, AI Intelligence and report workspaces. The shared theme is implemented in `src/mission-theme.css` and imported **after** the earlier component styles in `src/main.jsx`; its components are rendered across the existing page switch in `src/App.jsx`, not restricted to the Architecture/landing view. No backend, database, GitHub authorization, read-only policies, prediction release gates or evaluation data are modified by this UI styling task.

### Repository scan recovery and separate AI access

Repository analysis on the hosted Free instance has a bounded 75-second
frontend timeout, elapsed-time indicator, a Cancel and go back control, and
Escape-key cancellation. A failed refresh keeps the last analyzed repository;
invalid/incomplete responses are not accepted as successful evidence.
The backend inspects at most 48 prioritized GitHub text files per synchronous
request with individual five-second source timeouts. Coverage may be partial
and must not be presented as exhaustive.

The AI Intelligence navigation route is available before connecting a
repository; it shows previously stored evidence for the approved
`saksham-1326/Cloud-Byte-XL-Project` in Neon without rerunning analysis.
The initial AI overview allows up to 60 seconds for Render Free startup.
The hosted AI workspace remains read-only, historical predictions are
experimental, and independently verified prospective performance is not yet
established.

### Public demo read-only storage notice

After a successful repository assessment the frontend renders a small, dismissible **informational** banner explaining that results are available in the current workspace but public visitors cannot save the repository record into PostgreSQL. This expected security restriction is no longer treated as a red error. Genuine repository scan failures still appear separately as errors. The deployment remains read-only; no database, authorization or hosting policy changes were made.
