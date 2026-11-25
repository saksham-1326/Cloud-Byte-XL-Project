# Figma frontend replacement — local review

The single React/Vite application now starts at `src/main.tsx` and `src/App.tsx`.
Figma's reviewed SVG primitives, navigation metadata and visual stylesheet were
adapted from `Upgrade Cloud-ByteXL Overview.zip` (SHA-256
`61362fce830c1cca118a1ccdc1369d9c98edf4139581e1bc3f1b155940dfc3d3`). Its scripts,
instructions, pnpm lockfile, injected plugins and older dependency pins were not
installed. No second frontend, backend rewrite, deployment or database change.

## Implemented screens and contracts

| Screens | Existing data / supported behavior |
| --- | --- |
| Mission Control | Actual repository score/findings/resources and historical summary; no simulated activity |
| Repository | Metadata/languages/contributors/commits, searchable/expandable files, SHA-pinned source previews |
| Analysis | Explicit repository POST, cancellation/stale-result protection, save warning, session-only history |
| Issues / Security | Search/category/severity, original finding details/snippets/fixes and pinned source links |
| Recommendations | Actual priority lanes/filter and related findings; no automatic fixes |
| Architecture | Detected source classifications/resources/evidence, selection/zoom/reset; not runtime relationships |
| CI/CD | Stored run/attempt metadata, workflow filter, associated outcome/RCA and official GitHub links |
| Docker / Kubernetes | Detected configuration files/previews/findings; operations and telemetry unavailable |
| Reports | Actual-data JSON export, selectable preview and browser print/save PDF |
| AI Intelligence | Historical metrics/confusion matrix/backtests/model versions, attempt/report selection, original RCA uncertainty and inline evidence focus |

Repository/file reads reuse `/api/github/repository` and `/api/github/file` POSTs.
AI history uses `/api/ai/v1/overview`; restoration explicitly calls repository
`/latest`. A restored catalog is not a restored analysis. Missing metrics stay
unavailable, real zeros remain zero. Citation IDs are report-specific; unresolved
references are shown rather than guessed. Guards and human status remain separate.

The API client, AI contract helpers and repository transformations are retained.
Pure integration helpers add validated boundaries, source links, filters,
attempt/report association and an allowlisted report-export payload. Hooks own
request state. Controlled test fixtures are not authentic historical records.

## Hosted safety and unsupported features

Production omits administrative token entry, sync, review-submit, train, predict
and provider-generation controls. All three existing `VITE_ENABLE_*` flags remain
false. Backend read-only safeguards remain unchanged and authoritative. No action
is automatically submitted to generate predictions, train models or call providers.
Explicit local administration remains available separately, with disabled-by-
default feature flags and no stored credentials in browser persistence.

No chat service, GitLab/Bitbucket authentication, Docker daemon, Kubernetes cluster,
complete dependency CVE scanning, live infrastructure telemetry, complete job-log
stream or server PDF service is claimed. Pipeline stages and performance-over-time
bars were not invented. Historical backtests are not prospective verification;
manual criteria remain blank until a deliberate local reviewer supplies them.

## Dependencies and build

- React/DOM retain the existing reviewed versions; Vite remains 8.2.4 and ESLint
  10.15.0. The npm lock was updated with normal npm commands, not replaced by pnpm.
- Tailwind 4.2.2 and its matching Vite plugin replace the old v3 PostCSS pipeline.
  TypeScript 5.9.3 and compatible TS linting/component-test tools were added after
  peer-range checks. Existing JSX rules remain for retained JavaScript helpers.
- Recharts was removed after its only consumers (old UI) were retired. Actual
  language percentages now use accessible meters; metric history is tabular.
  Direct Autoprefixer/PostCSS dependencies were removed with the unused v3 hook;
  Vite may still depend on PostCSS transitively. Lucide remains required by the
  retained repository contract module.
- Hosting should explicitly configure an HTTPS `VITE_API_BASE_URL`. Enforcement
  and Vercel SPA routing belong to the separate deployment patch. Typechecking
  is part of this frontend build.

```powershell
# From repository root. No frontend environment value may contain a secret.
npm ci --prefix frontend-app
npm test --prefix frontend-app
npm run lint --prefix frontend-app
$env:VITE_API_BASE_URL = 'https://backend.example.invalid' # build fixture only
npm run build --prefix frontend-app
Remove-Item Env:VITE_API_BASE_URL
# Local development; choose only an independently verified safe backend target.
$env:VITE_API_BASE_URL = 'http://127.0.0.1:5000'
npm run dev --prefix frontend-app -- --host 127.0.0.1 --port 5180 --strictPort
```

Replace the fixture with the real approved Render origin before any production
deployment. Never aim repository-analysis POST at an unknown/private DB backend.
Local saving is intentional; hosted mode skips it with a visible warning.

## Cleanup and recovery

Before editing, 29 frontend baseline files were saved in ignored
`.migration-baseline/frontend-before-figma.zip` with SHA-256 entries in
`.migration-baseline/manifest.json`. It contains no `.env`, database or model.
This recoverable local snapshot must not be committed with deployment code.

After automated checks passed, unimported legacy App.jsx, AIIntelligence.jsx,
main.jsx, App.css, index.css, overview.css, platform.css, ai.css and Tailwind 3
configuration were removed. Old vite.config.js and postcss.config.js were also
superseded. The active entry imports no legacy screen/style. Original source
worktrees remain untouched. For rollback, inspect the snapshot/manifest and
restore only the frontend paths after preserving any subsequent work; do not
reset or clean the repository. The separate 22-file deployment baseline and its
README publication correction remain uncommitted and independently reviewable.

## Verification and manual acceptance

See `.migration-baseline/FINAL_VERIFICATION.json` for exact final test totals and
the file delta against the captured frontend baseline. Snapshot/log/result files
are ignored, not release inputs. Root README documents the replacement in the
same implementation task.

November 25 browser verification supersedes the earlier activation limitation.
Playwright with installed sandboxed Chrome exercised all four requested widths
and all 12 destinations using actual Flask responses and authentic read-only
history. Responsive checks passed. After the unauthenticated GitHub quota recovered,
tablet/mobile source checks also passed; local frontend acceptance is PASS. See
[BROWSER_ACCEPTANCE.md](BROWSER_ACCEPTANCE.md) for evidence, fixes and limitations.
The current regression total is 24 Node contracts plus 23 React tests.

Manual checklist, using the actual replacement preview and an approved read-only
demo backend (or clearly labeled controlled fixtures):

1. Open each viewport above at 100% browser zoom. Capture Mission Control and
   navigation. Verify no overlapping health/risk cards, clipped labels, unexpected
   page overflow or unreachable bottom dock actions. Table-local scrolling is
   intentional. Check all 12 destinations and long file/evidence text.
2. Submit the approved repository URL, observe pending/success/error and read-only
   save warning. Change sources rapidly; no old response should replace the new
   selection. Restore catalog only if desired; scores must not be invented.
3. Search/expand/select files, retry errors, inspect actual source and SHA links.
   Filter findings/recommendations, open details, close/reopen the session-reviewed
   mark. Check actual languages and configuration lists, not example filenames.
4. Select CI reruns and RCA responses. Verify run ID + attempt association,
   original diagnosis/uncertainty/guard, quotations/job/line, citation scroll/focus
   and unresolved-reference labels. Confirm zero recall stays zero and absent
   metrics stay unavailable. No prospective/human-verification claim is inferred.
5. Export JSON and print preview: only actual selected repository results, no
   credentials/admin state. Check read-only production controls are absent.
6. Exercise palette typing/arrows/Enter/Escape, focus trapping/return, navigation,
   reduced motion and offline fonts. Test 404/500/offline/empty responses.
7. Inspect Console and Network. Requests must target the intended Flask origin;
   no unintended mutation/provider call, console error or failed asset load.

Capture screenshots locally outside tracked release inputs, labeled by viewport,
screen and whether authentic data or controlled fixtures were used. No live
monitoring, models, source/demo/observation DBs or frozen submission files may be
changed to complete visual acceptance.

## Exact replacement file delta (deployment baseline excluded)

### Added

```text
frontend-app/MIGRATION.md
frontend-app/src/App.tsx
frontend-app/src/components/CodeExplorer.tsx
frontend-app/src/components/DataUI.tsx
frontend-app/src/components/Icon.tsx
frontend-app/src/components/Modal.tsx
frontend-app/src/components/Navigation.tsx
frontend-app/src/components/Primitives.tsx
frontend-app/src/features/Findings.tsx
frontend-app/src/features/Intelligence.tsx
frontend-app/src/features/Overview.tsx
frontend-app/src/features/Rca.tsx
frontend-app/src/features/Reports.tsx
frontend-app/src/features/Repository.tsx
frontend-app/src/features/Topology.tsx
frontend-app/src/hooks/Workspace.tsx
frontend-app/src/hooks/useIntelligence.ts
frontend-app/src/hooks/useRepository.ts
frontend-app/src/integration.js
frontend-app/src/main.tsx
frontend-app/src/navigation.ts
frontend-app/src/styles/figma.css
frontend-app/src/styles/integration.css
frontend-app/src/types.ts
frontend-app/src/vite-env.d.ts
frontend-app/tests/app.test.tsx
frontend-app/tests/integration.test.mjs
frontend-app/tests/setup.ts
frontend-app/tsconfig.json
frontend-app/vite.config.ts
frontend-app/vitest.config.ts
```

### Modified

```text
frontend-app/.gitignore
frontend-app/eslint.config.js
frontend-app/index.html
frontend-app/package-lock.json
frontend-app/package.json
frontend-app/src/api.js
frontend-app/tests/contracts.test.mjs
```

### Removed

```text
frontend-app/postcss.config.js
frontend-app/src/AIIntelligence.jsx
frontend-app/src/App.css
frontend-app/src/App.jsx
frontend-app/src/ai.css
frontend-app/src/index.css
frontend-app/src/main.jsx
frontend-app/src/overview.css
frontend-app/src/platform.css
frontend-app/tailwind.config.js
frontend-app/vite.config.js
```

Root README.md was updated separately as explicitly required. Existing uncommitted deployment files are not additional frontend implementation changes.


## Frontend-only publication clarification

The final publication was prepared directly against main, excluding the separate
22-file deployment patch. The production API-origin enforcement, Vercel SPA
configuration and fresh PostgreSQL bootstrap remain unpublished deployment work.
The earlier browser/47-test results describe the combined local worktree; the
clean frontend publication suite contains 21 contracts plus 23 React tests (44).
Default-off feature flags and production-hidden administration remain intact.
No backend code, database, model artifact or generated browser evidence is included.
