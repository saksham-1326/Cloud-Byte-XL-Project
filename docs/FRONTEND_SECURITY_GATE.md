# Frontend security gate — November 23, 2026

Scope: the existing `frontend-app` npm package and lockfile. No root Node files, UI source, AI engines, authentic records or model artifacts were changed. No `--force`, audit suppression, peer-dependency override or major React/Vite/Tailwind upgrade was used. The fix is local pending publication approval; the GitHub PR does not yet contain it.

## Audit results

| Audit | Before | After clean installation |
| --- | --- | --- |
| Full `npm audit` | 8 affected packages: 4 high, 4 moderate | **0 vulnerabilities**, all severities zero |
| `npm audit --omit=dev` | **0 vulnerabilities** | **0 vulnerabilities** |

The eight counts are affected packages, not eight distinct advisory IDs. ESLint and config-array are reported through their vulnerable minimatch dependency; brace-expansion and Vite each have multiple advisories. All eight affected installed packages had `dev: true` in the original lockfile. Production dependency constraints and all existing production locked versions remain unchanged. Audit absence is a point-in-time advisory result, not a general security certification.

## Finding-by-finding assessment

All rows below are **development-only** in this project. The installed-before versions and paths were checked against `package-lock.json` and `npm ls --all`.

| Package / installed before | Severity / directness | Advisory IDs | Patched version available / installed fix | Actual path and exposure |
| --- | --- | --- | --- | --- |
| `@eslint/config-array` 0.23.5 | Moderate; transitive | Inherits minimatch [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249) | Parent fix 0.23.6 / **0.23.6** | ESLint configuration/glob matching is invoked by lint. Configured patterns are repository-owned; arbitrary repository URLs/logs entered in the UI are not passed to this matcher. Attacker-controlled lint/config input could increase build/CI resource risk. |
| `brace-expansion` 5.0.9 | High; transitive | [GHSA-q2hr-2g5m-vwhr](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr), [GHSA-qhr7-859c-m2p7](https://github.com/advisories/GHSA-qhr7-859c-m2p7), [GHSA-6j4f-fj2g-mc7p](https://github.com/advisories/GHSA-6j4f-fj2g-mc7p) | Individual fixes 5.0.12, 5.0.11, 5.0.10; 5.0.12 covers all three / **5.0.13** | ESLint → minimatch → brace expansion. Deep/malicious glob patterns can exhaust CPU/stack. Normal checked-in globs are small; no application request endpoint accepts glob input for ESLint. Linting untrusted changes remains a tooling context. |
| `eslint` 10.8.1 | Moderate; direct dev dependency | Inherits minimatch [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249) | Compatible published parent fix **10.15.0**, now installed | Actual `npm run lint` entry point. Earlier 10.14.1 was not published in the queried registry; 10.15.0 declares patched minimatch/config-array ranges and supports existing Node 22. No application API calls ESLint. |
| `minimatch` 10.2.6 | Moderate; transitive | [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249) | Minimum 11.0.1 / **11.0.9** | Globparts amplification requires attacker-controlled patterns and the advisory's optimization behavior. ESLint/config-array actually import it; the project does not expose that functionality to GitHub-analysis request input. This is a reachable tool dependency, not proof of an exploitable browser endpoint. |
| `postcss-selector-parser` 6.1.4 | Moderate; transitive | [GHSA-rj75-hqrm-r3gf](https://github.com/advisories/GHSA-rj75-hqrm-r3gf) | 6.1.5 on the existing major (also 7.1.6 on major 7) / **6.1.6** | Tailwind/postcss-nested parse repository CSS during build. Extremely long attacker-supplied selectors cause quadratic work. Current CSS is trusted build input; fetched GitHub files are displayed, not compiled as CSS. No request-time selector parsing service is configured. |
| `source-map-js` 1.2.1 | High; transitive | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) | 1.2.2 / **1.2.4** | PostCSS source-map processing can encounter build inputs; malicious indexed maps with extreme section offsets can block the event loop. No uploaded/remote source-map processing endpoint is implemented. Malicious build sources are the relevant potential exposure, not ordinary UI log viewing. |
| `vite` 8.2.1 | High aggregate; direct dev dependency | Six advisories listed below | **8.2.4** on the same 8.2 minor, now installed | The local demo actually runs Vite on Windows. Editor-launch/dev-server paths are relevant; loopback reduces network exposure but is not sufficient grounds to dismiss browser-to-localhost attacks. Normal static production assets do not run the Vite server. |
| `zod` 4.4.3 | High; transitive | [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) | 4.6.6 / **4.6.7** | React Hooks ESLint plugin and zod-validation-error use Zod during lint. Oversized arrays/collections can allocate excessive validation issues. Application source does not import Zod or offer a Zod validation endpoint; practical input here is lint/compiler/plugin configuration, not remote RCA response JSON. |

Exposure statements are code/configuration-based assessments, not exploit demonstrations. No malicious payload or artificial failing workflow was introduced.

### Vite advisories and actual configuration

All six advisories affecting installed 8.2.1 have a same-minor Vite 8.2.4 fix:

1. [GHSA-698v-4r3x-3vcv](https://github.com/advisories/GHSA-698v-4r3x-3vcv), moderate: Windows `%` escaping in launch-editor can enable command injection with the required attacker-controlled filename/environment conditions.
2. [GHSA-r825-w8mm-5pxw](https://github.com/advisories/GHSA-r825-w8mm-5pxw), moderate: specially formed file paths can be interpreted as editor CLI options for affected editors. The developer-server/editor path exists; the project does not require open-in-editor for its demonstration.
3. [GHSA-587h-7wmj-h5pm](https://github.com/advisories/GHSA-587h-7wmj-h5pm), high: Windows path handling bypasses a filename existence check; in combination with escaping flaws, attacker-controlled editor paths can lead to command execution. This is relevant to the Windows demo toolchain and was fixed rather than waived.
4. [GHSA-9jrq-w75r-8gcw](https://github.com/advisories/GHSA-9jrq-w75r-8gcw), low: cross-origin script execution through custom HTML-transform middleware. This app uses normal SPA mode with the React plugin, not custom `transformIndexHtml` middleware or `middlewareMode`; the documented exploit configuration is not present.
5. [GHSA-rq7h-c2jc-7f22](https://github.com/advisories/GHSA-rq7h-c2jc-7f22), moderate: non-Windows filesystem allow-list bypass under crafted project/system path collisions. The demo is Windows; Linux CI builds assets rather than exposing a dev server. The affected class remains fixed in the selected version.
6. [GHSA-vfpm-58rq-9qcg](https://github.com/advisories/GHSA-vfpm-58rq-9qcg), moderate: specially requested Wasm paths can disclose four bytes from outside the intended filesystem boundary. Keep Vite bound to loopback; do not treat that restriction alone as eliminating all local-client attack paths.

## Compatibility and exact changes

Direct development dependencies are pinned to `vite: 8.2.4` and `eslint: 10.15.0` to preserve the tested security floor. Existing Node 22 satisfies both engines; existing `@vitejs/plugin-react` 6.0.5 accepts Vite `^8.0.0`. React/ReactDOM, Tailwind and all production package versions are unchanged.

The transitive minimatch upgrade is major **10 → 11**, and ESLint cache internals also change major versions. These were selected by compatible ESLint 10.15.0's declared dependencies, not forcibly overridden in an incompatible parent. The application does not import those internal APIs. `npm ls`, lint, existing tests and build verify the resolved integration. Vite's declared Rolldown `~1.2.x` resolves to 1.2.19, with matching Windows and Linux native optional entries preserved; Lightning CSS's Linux native entry remains present. No unsupported major upgrade or peer-dependency bypass was used.

The larger lockfile diff includes resolved compatible internal packages and optional platform metadata; generated reports retain before/after versions under ignored `backend/reports/security_gate/`. No source/lockfile evidence was silently deleted to hide findings. No `audit-level`, omit flag or suppression was used to manufacture the clean **full** audit; `--omit=dev` was a separate production-only comparison.

## Verification and release decision

- Fresh `npm ci`: passed, reports zero vulnerabilities.
- Frontend contract tests: **12 passed, 0 failed, 0 skipped**.
- Frontend lint: passed with ESLint 10.15.0.
- Frontend production build: passed with Vite 8.2.4; existing approximately 671 kB JS bundle warning remains.
- Relevant Flask/frontend API contracts on the disposable test DB: **7 passed**, zero failures/skips. The complete 285-test GitHub checkpoint predates this dependency fix; it is not claimed as a new run on the local fix.
- Fresh full and production-only audits both report **0 vulnerabilities**. No known finding from the original eight remains in the patched dependency graph.

Reasonable release assessment: the patched state is suitable for the intended isolated, loopback-only academic demonstration, subject to normal regression verification. This is not production-security approval. Keep the SELECT-only authentic demo role, disabled live AI actions and private credentials/model/data exclusions unchanged.

**Do not merge the old remote PR head on the assumption it contains these fixes.** The focused security commit is local only. Before merging PR #6, obtain approval to push this commit, verify the fresh GitHub backend/frontend jobs (especially Ubuntu clean install/native build), and obtain separate merge approval. No further dependency security repair is currently indicated by these audit results. Future advisories must be reassessed; do not expose Vite publicly or process untrusted build/plugin configuration as part of the demo.
