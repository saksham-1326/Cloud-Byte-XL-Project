# Figma browser acceptance — November 25, 2026

**Final frontend acceptance: PASS (local browser scope).**

## Genuine browser evidence

Playwright 1.58.2 used installed Chrome 157.0.8103.79 with its sandbox enabled
and a fresh headless profile. The actual production build connected to real
local Flask through an inert HTTPS test-origin forwarder. This verifies the
application locally, not deployed TLS, Vercel/Render hosting or production CORS.

The earlier production-build session passed all 12 destinations at 1440, 1024,
768 and 390px: historical CI/AI views, RCA citation focus, JSON export, print,
loading/empty/error states and read-only controls. No JavaScript page errors,
unexpected positive-path console errors, page overflow or overlapping cards were
observed. Earlier genuine source successes at 1440/1024px remain preserved.

## Completed tablet/mobile source checks

At 10:06:02 IST, after the advertised reset, one unauthenticated GitHub quota
probe returned core limit 60, remaining 60, used 0. No Byte-XL or other credential
was loaded. The next advertised reset was 11:06:02 IST. These are measured
pre-test values, not a promise about subsequent shared quota availability.

Only two source-preview API calls were then made. The existing Flask endpoint
uses two GitHub GETs per preview (repository metadata and file contents), so
these checks required four upstream GitHub GETs, without credential substitution:

| Viewport | File | API response | Result |
| --- | --- | --- | --- |
| 768px tablet | README.md | HTTP 200 | PASS |
| 390px mobile | README.md | HTTP 200 | PASS |

At each width, folder expansion/collapse, file filtering and root-file selection
worked. The filename and SHA-pinned GitHub link were correct; displayed content
matched the actual Flask response exactly. The source pane scrolled vertically
(18,443px content, 480px visible). Document width matched viewport width and the
file tree/source panels did not overlap. No console or JavaScript errors were
recorded. Loading was observed while delivery of the genuine response was briefly
delayed by the harness; its content was not replaced with a fixture.

Earlier real rate-limit errors displayed a message and explicit Retry control.
Isolated offline checks also confirmed controlled upstream 403/429 handling with
no automatic retries. A genuine live 429 response was not observed. The existing
API does not propagate GitHub quota headers or supply a reset countdown.

## Actual data and integrity

Fresh read-only analysis returned 115 files at repository commit
`ece355c77e8f9386ab865aba9d544bad2a8e21fc`; the final source tests reused that
actual in-memory analysis without repeating analysis or database writes.
Authentic demo history contains 27 unique runs, 28 attempts, 12 historical
backtests, 21 unverified RCA reports and two original models. Historical accuracy
remains 50% on six test runs, failure recall 0%, zero independent human reviews
and zero verified prospective predictions.

The prior before/after snapshots matched counts and canonical row hashes across
all 11 demo tables; both artifact digests matched original model metadata.
Preserved evidence, non-frontend implementation baseline and finalized submission
ZIP checks passed. No database migration, training, provider call or live
observation was started.

## Fixes and regressions

The prior browser pass fixed case-insensitive GitHub repository identity matching,
overlapping report buttons, title wrapping, paper contrast, footer layout and
print background. This final source pass required **no application fixes**.

The existing checkpoint remains 24 Node contracts plus 23 React tests: **47 passed,
zero failures/skips**; TypeScript, lint and production build passed. Full and
production npm audits reported zero findings. Tests/build were not repeated
merely for this evidence/documentation update.

## Evidence and publication boundary

Ignored local evidence: `.migration-baseline/browser-verification-20261125/`.
`final-browser-results.json` preserves the earlier whole-app pass and then-current
quota blocker; `pending-source-results.json` closes that blocker with both genuine
HTTP 200 results. `latest-quota.json` records actual quota recovery. The earlier
NO-GO files are retained unchanged as historical evidence, not silently rewritten.

New screenshots: `screenshots/768-source-preview-success-final.png` and
`screenshots/390-source-preview-success-final.png`. Earlier desktop/laptop success
captures and all 36 earlier screenshots remain intact. Source output is authentic
historical repository content, not a claim of current live model performance.

No exhaustive accessibility audit, deployed browser test or new prospective ML
result is implied. Publication requires approval and separation from the existing
22-file deployment patch; see ../docs/FIGMA_PUBLICATION_REVIEW.md. No commit, push,
merge, deployment or finalized submission-package change occurred.


## Frontend-only publication clarification

The final publication was prepared directly against main, excluding the separate
22-file deployment patch. The production API-origin enforcement, Vercel SPA
configuration and fresh PostgreSQL bootstrap remain unpublished deployment work.
The earlier browser/47-test results describe the combined local worktree; the
clean frontend publication suite contains 21 contracts plus 23 React tests (44).
Default-off feature flags and production-hidden administration remain intact.
No backend code, database, model artifact or generated browser evidence is included.
