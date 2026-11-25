# Figma frontend replacement: preparation and integration plan

Prepared November 24, 2026. **Planning only: frontend replacement has not started.**
No archive scripts, installs, plugins, builds or deployment helpers were executed.

## 1. Isolated working environment

- Branch: `feature/figma-frontend-replacement`.
- Worktree: `C:/Users/Saksham Sharma/.codex/worktrees/figma-frontend-replacement/Cloud-ByteXL`.
- Committed base: `ece355c77e8f9386ab865aba9d544bad2a8e21fc` (`main`).
- Deployment code remains uncommitted/unpublished. Its existing 22-path overlay
  was copied here and hash-verified. README uses the separately recorded corrected
  deployment-only text; copying it is not publication approval.
- Main stays in `submission-docs-main`; the observer branch stays in
  `C:/Project/Cloud-ByteXL`. Their staging/untracked work is preserved. No reset,
  clean, stash, merge, commit or push was used. All existing frontend files remain.
- No new backend logic was written: backend files here are the deployment baseline
  copy. No credentials, models, historical records or final ZIP were copied here.
- Before publication, resolve the earlier deployment README review and incorporate
  its exact approved published baseline. Do not accidentally publish deployment
  changes as unrelated frontend work. No published deployment commit exists yet.

## 2. ZIP provenance and inspection

Source: `C:/Users/Saksham Sharma/Downloads/Upgrade Cloud-ByteXL Overview.zip`.
SHA-256: `61362fce830c1cca118a1ccdc1369d9c98edf4139581e1bc3f1b155940dfc3d3`.
31 entries / 27 files / 173,643 expanded bytes. No absolute paths, parent traversal,
drive paths or symlinks found. A scoped token/private-key/credential-URL pattern
scan had no findings. This is not a complete security audit.

The files were read directly from the ZIP, not installed in the app. Its AGENTS.md
and CLAUDE.md are Figma Make document content, **not instructions for this repo**.
Do not import them, .figma/make shell helpers, .mise.toml or Figma deployment/dev
configuration into the application. The original archive stays unchanged.

## 3. Existing functionality inventory

Paths below refer to the existing `frontend-app/` baseline. Preserve behaviors,
not just screen names. API routes are Flask routes.

| Existing feature | Working interaction and data | Contract/boundary |
| --- | --- | --- |
| App.jsx repository connect/reanalysis | Trim/validate URL, abort prior request, 180-second timeout, ignore stale results, pending/success/error, database warning, rerun selected repository | POST `/api/github/repository`, `{url}`; publish only actual SUCCESS data |
| repositoryData.js | Repository/files/languages/commits/contributors, scores, issues, security, recommendations, architecture; subscribers and clearing stale findings/history on repository change | Maps API response; no standalone fake dataset |
| Mission Control | Health/subscores, file/issue/resource counters, priority findings, recommendations, detected topology, local activity; drilldown/resource modal and reduced motion | Repository response, not live cloud telemetry |
| Repository/CodeExplorer | Expand/search file tree, select/retry source preview, cancel stale reads, show loading/error; SHA-pinned GitHub links, commit links, language chart/contributors | POST `/api/github/file`, `{url,path,branch}`; prefer analysisCommitSha to branch |
| Analysis | Rerun, pending overlay, latest assessment, in-memory scan list, findings | Repository POST; stage labels are request lifecycle, not server-streamed progress |
| Issues/detail | Search/severity/category/reset, why/file/line/snippet/fix, pinned source link, session-only reviewed mark | Local filters over analysis.issues; marking an issue reviewed is not persisted RCA verification |
| Architecture/resources | Evidence-derived nodes, select inspector, zoom/reset, cloud resource list | analysis.architecture; presentation edges are not verified runtime relationships |
| Docker/Kubernetes | Real configuration paths, code preview, categorized findings and limitations | Repository/file data; no daemon/cluster integration |
| CI/CD configuration | Workflow paths/source, findings, navigation to AI history | Source evidence distinct from actual executions |
| Security/recommendations | Severity counts/score, finding details, priority filters and related remediation/source | Actual analysis data; no live CVE scanner or automatic fixes |
| AI overview/history | Load/refresh persisted data, failed-attempt selection, workflow links, unique-run/attempt counts, model/provider status/errors | GET `/api/ai/v1/overview?repository=...` |
| AI metrics/predictions/models | Historical metrics, splits/classes/confusion matrix/threshold, original timestamps/version, backtests/shadow rows/model registry | Overview fields; matched shadow rows are not independent prospective proof |
| RCA/evidence | Run+attempt association, report ID, category/job/step/cause/fix/confidence/uncertainty, guard status, primary/secondary evidence ID/job/line/text | Stored reports and inline evidence; no separate citation endpoint |
| Explicit local administration | Sync, flagged training/prediction/provider actions, task polling, optional in-memory admin token, reviewer criteria/acknowledgement | POST `/api/ai/v1/{sync,train,predictions,rca}`; GET `/tasks/:id`; POST `/rca/:id/verify` under same prefix |
| Reports | Preview/toggle, JSON Blob download/object-URL cleanup, browser print/save PDF | Client-side data; no server report-generation endpoint |
| Shared UI | Sidebar/mobile navigation, issue/resource/connect modals, notification/profile menus, toasts, external links | Local state, not a new account/auth service |
| api.js | Production HTTPS base guard, response/status/JSON validation, timeout/cancel/errors | One shared client; VITE settings never contain secrets |
| aiContract.js | Null vs zero/date formatting, blank/uncertain review fields, explicit valid review payload, shadow filtering, later guard rejection precedence | Preserve existing tested semantics |

Other existing read routes: `/api/ai/v1/{runs,predictions,models,rca,evaluation,outcomes}`
and `/api/github/repository/latest`. App does not currently restore from latest
on startup. Its DB fallback restores a catalog entry, **not a complete analysis**.
Any new restoration UI must label partial data and offer reanalysis without making
up scores. Full analysis snapshots/history are not stored by this repository
workflow: the existing scan list is in memory. Preserve real local catalog saving
without promising complete persistence.

Hosted read-only mode deliberately skips catalog persistence, returning a visible
save warning. AI mutations/tasks/sync/webhooks/review submission are denied.
Some legacy buttons can still attempt denied actions; the replacement should
hide/disable hosted mutations. Server denial remains authoritative. Do not change
the backend to enable UI controls.

## 4. Figma component inventory

The export has one 1,600-line App.tsx and a 2,954-line index.css. App.tsx imports
only React and contains **zero network calls**.

| ZIP App.tsx component/lines | Purpose/current behavior |
| --- | --- |
| Icon / 152; definitions above | Inline SVG icon set |
| PageId/destinations/pageTitle / 171-329 | 12 state-based destinations, grouped Observe/Protect/Operate/Intelligence |
| StatusTag / 331; EmptySignal / 346 | Reusable status/empty visuals |
| Panel / 368; PanelHeader / 384 | Shared card/toolbar primitives |
| TopologyCanvas / 413 | Decorative unresolved graph/core; generic inspector callback |
| OverviewPage / 492 | Empty Mission Control topology/health/delivery/risk/activity/AI surfaces |
| RepositoryPage / 642 | Example tree names, empty editor/language/commit panels |
| AnalysisPage / 719 | Five static stage descriptions, waiting state and empty history |
| IssuesPage / 772 | Empty findings/detail; filter buttons lack handlers |
| SecurityPage / 815 | Decorative radar and unavailable severity/control states |
| RecommendationsPage / 864 | Empty priority lanes, unwired toolbar |
| ArchitecturePage / 899 | Empty graph/inspector, unwired Group-by control |
| CicdPage / 940 | Empty runs, hardcoded pipeline stages, unavailable logs; selector/search unwired |
| ConfigPage / 1000 | Docker/Kubernetes example filenames and placeholder source |
| ReportsPage / 1061 | Empty report/type selector, disabled export |
| AiPage / 1132 | Empty prediction/RCA/review panels; **hardcoded performance bars at line 1170** |
| Dock / 1208; CommandBar / 1288 | Click navigation/menu works; connect/analyze/branch open drawers, not an API |
| PageContent / 1344; App / 1368 | Screen switch, Ctrl/Cmd+K palette, Escape closes overlays, scroll reset |
| Palette / 1450; drawers / 1498 | Click destinations work; input does not filter and advertised arrow/Enter behavior lacks handlers; GitHub/GitLab/Bitbucket connect disabled, no URL form; chat disabled; inspector generic |

52 button tags and 27 onClick attributes do not mean 27 working business features.
CSS defines 1250/900/700/470px breakpoints, bottom mobile dock, responsive grids,
scroll containers and reduced-motion override. These are static observations,
not browser acceptance. Test clipping, focus trapping/return, drawer inertness,
keyboard navigation, contrast and chart alternatives. Google Fonts is external;
system-font fallback must work offline.

Do not present live topology, verified findings/controls, dependency vulnerability
coverage, AI synthesis, syntax-aware editing or performance-over-time without
supporting data. Static stages/filenames are not detected results. Replace the
six invented metric bars with unavailable state or real labeled historical data.

## 5. API/data adapter rules

- Repository response: status, repository (analysisCommitSha), files/fileCount,
  languages, contributors, commits, analysis and optional databaseWarning.
  Analysis: overall/status/subscores/metrics/issues/severityCounts/security/
  recommendations/architecture. Missing metrics stay unavailable, never guessed.
- File response: status/content/path/sha/branch/size/url. Encode refs/paths and
  render content as text, never executable HTML.
- Overview data: repository/run_count/attempt_count/runs/model/model_versions/
  predictions/reports/evaluation/rca_provider/shadow_events. Encode repository query.
- Run and outcome association uses repository + run_id + attempt, never position
  or run ID alone. Outcomes can be fetched through the existing outcomes GET.
- Report association uses report ID plus run/attempt. Preserve original claims,
  primary/secondary evidence, uncertainty, guard and human status separately.
  Evidence fields are id/job_id/line/text. Inline evidence already exists; stable
  local citation anchors can be added, with explicit unresolved-reference state.
- Keep original model versions/timestamps/splits and distinct backtest/shadow/
  matched/independently verified categories. API does not expose an independent
  observer-proof count: do not infer one. Known project checkpoint is zero verified
  prospective predictions; zero independent human RCA reviews. Show zero recall
  as zero and absent metrics as unavailable.
- No frontend jobs/log-stream endpoint exists. Run metadata/RCA excerpts do not
  establish complete execution timelines/logs. Use original excerpts and official
  GitHub run links; never draw standard stages as completed actual steps.

## 6. Screen-to-API integration matrix

Common acceptance for every row: real data only; pending/error/empty/stale states;
repository changes cancel or ignore old requests; keyboard and responsive access;
no hosted write requests. Figma components supply presentation, never truth data.

| Figma screen/component | Existing feature + API | Data/interaction mapping | Loading/error/empty states | Unsupported features + acceptance |
| --- | --- | --- | --- | --- |
| Mission Control / OverviewPage | Existing overview; repository POST + AI overview GET for historical summaries | Health/subscores/counts/issues/recommendations/architecture; cards drill into same records | No source -> connect; pending analysis labeled; AI error must not erase good repository results | No live infrastructure/fake activity/default resources; assert exact response counts and same finding drilldown |
| Repository / RepositoryPage | Existing explorer; repository POST, file POST; optional latest GET | Real tree/languages/contributors/commits, expand/search/select/retry file, pinned SHA links; clearly partial restoration | Per-file pending/error/empty; cancel source changes; absent analysis unavailable | No editor/save/GitLab/Bitbucket/OAuth; stale file/repository responses cannot replace current selection |
| Analysis / AnalysisPage | Existing request lifecycle; repository POST | Rerun, results, findings/session-only scan list, request pending/completed/failed | Keep last good result with stale label on refresh error; surface databaseWarning | No stage stream, full dependency CVE scanner or LLM synthesis; test real local save vs hosted warning |
| Issues / IssuesPage + detail | Existing filters/modal; repository result, optional file POST | Search/severity/category/reset, title/why/path/line/snippet/fix, source links, session reviewed marks | Unscanned != no matching filters; reset selected finding on repository change | No persisted assignment/completion/GitHub issue creation/fix; test filters, source ref and no RCA verification side effect |
| Security / SecurityPage | Existing security; analysis.security/issues | Actual score/severity counts, related finding/remediation navigation | Unscanned/no findings/API failure distinct; missing score not 0 | Radar decorative unless actual data; no runtime threats/CVE feed/verified control score; zero/null and escaped snippets tested |
| Recommendations / RecommendationsPage | Existing priority filter; analysis.recommendations | Lanes from actual severity, related issue navigation, snippets | Empty and filtered-empty distinct | No persisted Completed lane/drag-drop/applied remediation; verify lane mapping and missing related issue |
| Architecture / ArchitecturePage/TopologyCanvas | Existing graph/zoom/inspector/resource modal; analysis.architecture | Detected labels/resources/evidence, node selection, zoom/reset, evidence-bound edges | Empty/unresolved for missing config | No live health or runtime dependency proof/deploy actions; counts and inspected evidence agree with response |
| CI/CD / CicdPage | Existing config page + AI history; overview or runs/outcomes GET, file POST | Workflow config separate from attempts; run filter/select, attempt-aware outcome, GitHub link, associated RCA | No config/no history/no selection/read error distinct | No fabricated standard stages/full-log search/durations without evidence; test reruns/pending outcomes/history vs config |
| Docker / ConfigPage Docker | Existing InfraFindingsPage; repository/file POST | Real Dockerfile/Compose/.dockerignore paths, preview and category findings | No matching files and preview failure explicit | No daemon/image/build/start/stop; example filenames never become detected records |
| Kubernetes / ConfigPage Kubernetes | Existing InfraFindingsPage; repository/file POST | Real manifests/Helm paths, YAML, category findings/source | Same file states and honest missing manifest | No cluster/pod health/apply/restart; test source selection and absence of operational claims |
| Reports / ReportsPage | Existing preview/JSON/print; client-side selected repository/AI data | Executive/technical/security are projections, not server jobs; preview/toggle/JSON/print, optional labeled historical AI appendix | Disable export without actual snapshot; partial data explicitly unavailable | No server PDF service/saved report catalog; verify export repository/SHA/provenance, exclude credentials/admin state |
| AI Intelligence / AiPage | Existing AIIntelligence; overview and optional granular GETs | Attempts, experimental metrics/splits/confusion matrix, backtests, model registry, failed-attempt/report selector, causes/fix/guard/inline evidence | Independent model/history/report unavailable + loading/error/retry | Remove fake bars/obsolete Not implemented when stored history exists; no matched->prospective inference; test null/zero recall/attempt association/later guard rejection |
| RCA detail / root-cause-panel | Existing LogEvidence/RCA section; overview reports or RCA GET | Report/evidence ID, job/line/quote, primary/secondary, fix/uncertainty; stable local scroll/focus anchors | Missing reference -> unresolved, no guessed match; missing evidence stays missing | No hosted generation/review POST, no human-approved badge from guard; test escaping, duplicate IDs across reports and selection reset |
| Global Dock/CommandBar/palette/drawers | Existing navigation/connect + Figma shell; explicit repository POST | All 12 destinations; URL form, analyze/close/retry, functional search and keyboard navigation; branch display only | Prevent duplicates, accessible errors/focus return; explain disabled actions | No GitLab/Bitbucket/chat/account auth/branch writes; test bottom dock reachability, Escape/focus trap/arrows/Enter/inert drawer/reduced motion |

## 7. Proposed architecture: one existing frontend

This directory tree is a plan, not files created. Split the export into typed
presentation/features and shared data hooks. Preserve the current entry until
parity gates pass; do not create another package/root/Vercel frontend project.

```text
frontend-app/
  src/main.tsx                         # eventual single-entry cutover
  src/App.tsx                          # shell/page selection
  src/types/api.ts                     # DTOs and explicit nullable fields
  src/api.js                           # retain shared client initially
  src/aiContract.js                    # retain pure tested contracts initially
  src/repositoryData.js                # retain store until parity proven
  src/state/RepositoryProvider.tsx
  src/hooks/useRepositoryAnalysis.ts
  src/hooks/useRepositoryFile.ts
  src/hooks/useIntelligence.ts
  src/components/layout/{AppShell,Dock,CommandBar,CommandPalette,ContextDrawer}.tsx
  src/components/ui/{Icon,Panel,PanelHeader,StatusTag,EmptyState,ErrorState}.tsx
  src/components/data/{ResponsiveTable,MetricCard,CodeEvidence,TopologyCanvas}.tsx
  src/features/overview/OverviewPage.tsx
  src/features/repository/RepositoryPage.tsx
  src/features/analysis/AnalysisPage.tsx
  src/features/issues/{IssuesPage,FindingDetail}.tsx
  src/features/security/SecurityPage.tsx
  src/features/recommendations/RecommendationsPage.tsx
  src/features/architecture/ArchitecturePage.tsx
  src/features/cicd/CicdPage.tsx
  src/features/config/ConfigPage.tsx
  src/features/reports/ReportsPage.tsx
  src/features/ai/{AIIntelligencePage,HistoricalPredictions,ModelEvaluation,RcaDetail,CitationEvidence}.tsx
  src/styles/{index,tokens,layout,components,print}.css
  src/vite-env.d.ts
  tsconfig.json
  vite.config.ts                       # eventual rename, HTTPS guard retained
```

Retain App.jsx/AIIntelligence.jsx and existing CSS until all replacement pages
pass acceptance. New modules can be implemented without mounting a second app;
cut over the one index.html entry only after integration. Local rollback restores
that entry/import graph. No legacy deletion before parity, no public prototype
route or production toggle. Original committed UI plus deployment overlay hashes
remain available; preserve uncommitted baseline changes too.

Use React state/context plus the existing external-store subscription initially.
Introduce strict TS DTOs/hooks with allowJs enabled for legacy imports; do not
turn checkJs on across all existing modules or refactor globals unnecessarily.
Keep null distinct from zero; avoid unchecked `as any` coercion. Hooks own request
cancellation/pending/error/stale state and run/attempt identity. No new browser
GitHub/provider client or credential store. No router package is needed for the
current state-based navigation unless URL-based routes become an explicit need.

Hosted UI policy: production builds are read-only regardless of prototype
controls. All existing VITE_ENABLE_* flags remain false. Hide admin-token entry,
review-submit/sync/generate/train/predict in the public build and send no mutation
on mounting/refreshing history. Repository/file POSTs are read-only server-
allowlisted exceptions. Preserve explicit local administration contracts without
enabling/calling them during migration. The backend route gate remains authority.

## 8. CSS and dependency migration

No dependencies were installed/upgraded/removed. Keep npm and the frontend npm
lock, not the ZIP pnpm lock. Existing security-reviewed versions are newer than
several ZIP resolutions; copying its package.json would cause regressions.

| Package/config | Existing | ZIP lock/export | Plan |
| --- | --- | --- | --- |
| React/DOM | ^19.2.8 | 19.2.4 | Keep reviewed existing versions, no downgrade |
| Vite | 8.2.4 | 8.0.5 | Keep 8.2.4 and production API-origin checks |
| React Vite plugin | ^6.0.4 | 6.0.1 | Keep current compatible installation |
| Tailwind | ^3.4.17 + PostCSS | 4.2.2 + @tailwindcss/vite 4.2.2 | Deliberate major migration: inspect utilities/reset/tokens, audit/pin a matching reviewed v4/plugin pair; export version is a baseline, not automatic security advice |
| TypeScript | No direct compiler | 5.9.3 | Add reviewed compatible compiler and tsc --noEmit, not just Vite transpilation |
| @types/node | No direct entry | 22.19.17 | Add reviewed Node 22 types if needed by TS config |
| React type packages | ^19.2.17 / ^19.2.3 | Older versions | Keep compatible current types |
| ESLint | 10.15.0, JS/JSX flat config | No lint script | Preserve rules; add compatible typescript-eslint and TSX file coverage |
| Lucide/Recharts | Existing working consumers | No export imports | Keep while used; reuse real-data charts and accessible tables; remove only after consumer proof |
| Autoprefixer/PostCSS | Tailwind 3 pipeline | Vite Tailwind plugin | Retire old Tailwind PostCSS hook at v4 switch; remove packages only after checking consumers |
| oxfmt/.figma helpers | Not used | Formatting plus large Figma Vite helper module | Do not import by default; not needed for this application's deployment |

Port font/contrast tokens and needed shadow/keyframes into Tailwind v4 theme CSS.
Use one reset/pipeline, scope collision-prone shell/global selectors and do not
load every old/new stylesheet together. Keep fallback fonts offline. Old rollback
modules may remain without their CSS being loaded. Preserve existing API-origin
validation, Vercel root/dist/fallback, false feature flags and no VITE secrets.
Do not copy Figma custom-script/analytics injection, dev kit, error replay,
linked-package source maps, preview host/port or FIGMA_PUBLIC_URL machinery.

Planning references: [Tailwind upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
(v4 browser baseline Safari 16.4+, Chrome 111+, Firefox 128+ and changed reset/utilities),
[Tailwind Vite integration](https://tailwindcss.com/docs/installation/using-vite),
[Vite TypeScript](https://vite.dev/guide/features.html#typescript) (transpilation
is not type checking), [typescript-eslint supported versions](https://typescript-eslint.io/users/dependency-versions/)
(currently includes ESLint 10). Recheck exact versions/peer ranges and npm audits
at implementation time. No automatic major upgrade is approved by this report.

## 9. File lifecycle plan

- Add the planned TSX/type/hook/style files, TS/env declarations and adapter/
  component/browser tests. This plan is the only newly authored nonignored file.
- Later modify frontend package.json/npm lock, ESLint config, Vite config (rename
  JS to TS when ready), index.html/entry, CI frontend typecheck and README alongside
  implementation. Change frontend env example only for a justified public setting.
- Preserve frontend-app/vercel.json SPA/root/output behavior and API HTTPS guard;
  any change needs deployment-contract tests. Do not alter root package files.
- Retain api.js/aiContract.js/repositoryData.js initially; future TS conversion must
  preserve meaningful contract coverage, not weaken tests to fit implementation.
- Eventually retire old App.jsx/main.jsx/AIIntelligence.jsx and index.css/
  overview.css/platform.css/ai.css after parity. Remove App.css only after unused-
  import proof. Retire Tailwind 3/PostCSS config only once nothing needs them.
  This is not an instruction to delete any file now.
- Do not import archive AGENTS/CLAUDE, .figma executables, pnpm lock or downgraded
  dependency pins. The PNG favicon can be a reviewed static asset later.
- Backend/migrations/configuration, observer, models, original/demo/observation
  databases, authentic records and the frozen submission package are out of scope.

## 10. Test and acceptance strategy

1. Preserve 12 existing contract tests plus three production-config tests. Extend
   identified gaps: null/zero, malformed responses, cancellation/stale data,
   repository switch, partial restoration, warning semantics and source SHA links.
2. Typed adapter tests use explicitly labeled controlled fixtures, never demo
   records presented as real. Test repository/run/attempt/outcome joins, multiple
   reports, evidence identity, rejected guards, missing citations, primary versus
   secondary observations, historical labels and no fabricated prospective count.
3. Add component interaction coverage after compatible test-dependency review
   (for example React Testing Library/DOM runner). Preserve Node tests. Exercise
   connect/filter/file retry/modal/run/report selectors/export/print, not just
   snapshots matching the implementation.
4. Browser acceptance when a reviewed browser tool is available: real API fixtures
   or an explicitly approved isolated target; no private DB writes/live monitoring.
   Test 1440/1250/1024/900/768/700/470/400/320px, long paths/log lines, table scroll,
   bottom navigation/drawers, no clipped actions/page overflow. Verify keyboard
   focus/trap/return, palette keys, Escape, screen-reader labels, contrast,
   reduced motion and offline fonts. CSS inspection is not a browser PASS.
5. Production checks: valid HTTPS API build, missing/local/path-bearing origins
   rejected, SPA refresh, expected CORS/403, no forbidden UI mutation requests,
   no secrets in exports/bundles, all three feature flags false.
6. Run frontend tests, TS typecheck, lint, build, full/production npm audits and
   Linux npm-ci checks on the changed lockfile. Preserve existing backend/PG/
   Gunicorn CI. Run relevant backend contract regressions if integration changes;
   do not repeat historical model evaluation or retrain.
7. Compare imported screens with the source Figma design. Correct misleading
   labels/data to reflect evidence; no arbitrary visual redesign.
8. Cut over the single entry only after supported-feature parity. Reverify
   model/evidence/submission hashes and unrelated Git state. Remove legacy code
   only after acceptance and retain a recoverable baseline.

Fresh verification in this preparation: **12 existing frontend contract tests
passed; 0 failed/skipped** against the unchanged source baseline. ZIP static
path/size/symlink and secret-pattern checks passed. All 22 copied baseline paths
were verified, with the separately documented README correction. No Figma code
was installed, run or rendered. The prior 15 frontend / 297 backend results are
deployment-preparation checkpoints, not replacement-UI acceptance. No new browser,
Tailwind 4, TypeScript or Figma production-build success is claimed.

## 11. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Disconnected placeholder UI replaces real features | Bind typed adapters/hooks before active cutover; retain old UI until parity |
| Tailwind 3->4 reset/global/utility collisions | Explicit compatibility review, one pipeline and scoped theme/styles |
| Older export pins undo security fixes | Preserve current React/Vite/plugin, use npm lock, audit additions |
| Decorative bars/stages/filenames look authentic | Real data or unavailable state; label static evidence versus runtime telemetry |
| Wrong run/attempt/report or stale request shown | Identity-keyed selectors and cancellation/reset tests |
| Public controls attempt writes | Read-only production UI plus unchanged authoritative backend gate |
| Human/prospective claims inferred from guards or matches | Preserve null/zero/guard distinctions; independent verification is separate |
| Responsive clipping/focus/accessibility | Test all relevant breakpoints and long-content/keyboard cases |
| Unpublished deployment baseline | Resolve separate README publication review before publishing frontend work |
| Deadline pressure | Keep working UI until new screens pass parity; one-entry rollback available |

## 12. Exact implementation sequence and readiness

1. Obtain explicit implementation approval. Reverify ZIP/base hashes and keep old
   frontend intact. No approval to publish/deploy is implied.
2. Review/pin TS/Tailwind/compiler/lint dependencies. Change only frontend manifests,
   configs, necessary CI typecheck and README; keep npm, one frontend and existing
   HTTPS guard. Do not install Figma helpers. Prove TS/CSS compatibility first.
3. Extract visual shell/primitives; implement accessible dock/palette/drawers and
   responsive layout without dummy business data. Keep active entry unchanged.
4. Preserve/wrap shared client/contracts/store with typed DTOs/hooks. Implement
   repository URL analysis/source preview first, with warning/cancel/retry behavior.
5. Bind Mission Control, Analysis, Issues, Security, Recommendations, Architecture,
   Docker/Kubernetes to actual repository evidence. No runtime integration claims.
6. Bind CI history/AI reads to existing APIs; migrate metrics/model registry/backtests
   and full RCA/citation inspection. Keep hosted write features disabled.
7. Bind Reports to actual selected data and JSON/print behavior with explicit
   historical/partial-data labels. No invented server-side reporting service.
8. Complete API/component/browser/responsive/security checks, then switch only the
   existing frontend entry to the replacement. Update README with actual behavior.
9. Review parity, preservation and rollback before retiring legacy files. Commit,
   push, merge and deploy each remain outside this task's authorization.

**Decision:** safe to begin implementation after explicit approval, in this
prepared branch. No backend rewrite is required. Toolchain compatibility and UI
parity still need proof during implementation. The separate deployment README
publication gate remains unresolved. Frontend replacement has not started.
