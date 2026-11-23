# Final live observation preflight — November 23, 2026

## Current submission status — supersedes earlier snapshots

The approved historical refresh is complete. Subsequent authorized UAC recovery
successfully synchronized Windows Time at 19:44:55 IST and cleared the stale-data
error. The stopped-service findings in the earlier snapshots below are historical.
Clock uncertainty qualification remains NO-GO; Byte-XL identity/restrictions still
require operator confirmation. Zero prospective predictions are verified and no
live observer session has started. External timestamping remains a proposal only.
The historical presentation and current launch instructions are in
[SUBMISSION_DEMO_PACKAGE.md](SUBMISSION_DEMO_PACKAGE.md).

## Latest follow-up: approved refresh completed

The assessment below is preserved as the original preflight. The historical
refresh was subsequently explicitly approved and **completed** on November 23.
The exact 16 attempt identities and metadata-set digest below were revalidated
against GitHub before the transaction. No discrepancy was found. The first
network attempt timed out; its bounded retry succeeded. A transaction setup
attempt failed before writes; initialization was corrected before import.

Actual dedicated observation database totals are **44 attempts / 43 unique runs,
21 jobs, 308 steps, 44 outcomes, one unchanged model, zero predictions and zero
shadow events**. Independent post-commit read-only connections verified counts
and all seven table hashes. Existing rows remained byte-equivalent under
canonical row hashing. Exact run/attempt, commit SHA, source creation timestamps,
job/step identities and outcome associations were checked. Source and demo
databases were never write targets. Import time is not a prediction timestamp.
The receipt records observation after commit, not a fabricated commit timestamp.

Local ignored evidence:
`backend/reports/observation_blockers_20261123/historical_import_receipt.json`,
`refresh_preview_records.json`, `github_read_requests.json`,
`github_permissions.json` and `clock_diagnostic_raw.json`.

**Clock: NO-GO.** Recheck still found W32Time stopped (Manual), with source/status
queries returning 0x80070426. The latest retained packet samples at 15:18:04 and
15:18:07 IST reported −0.2170188 and −0.2093108 seconds offset, RTT 41.5017 and
28.9231 milliseconds. Conditional instantaneous estimates were 0.2479168 and
0.2339500 seconds. One of three requested samples did not yield a parsed offset.
The reference reported 119.209 ns precision, which is resolution, not guaranteed
accuracy. Packet display rounding, local timestamp resolution, unbounded future
drift/clock steps and unauthenticated reference uncertainty prevent a credible
900-second bound. No error bound or valid clock file was invented. No
administrator/service/time settings were changed. The manual Windows commands
below remain the required operator step; successful service synchronization
must still be followed by justified session-wide timing evidence.

**Token: NO-GO.** Fresh authenticated repository, Actions and Contents GETs
succeeded for numeric repository ID 1319512023, but fine-grained PAT grant and
repository-selection introspection remains unavailable from those public-resource
reads. Actions read, Contents read, repository-only selection and absence of
unnecessary write grants are unverified. Stop credential work here: inspect the
existing token's GitHub settings, select only this repository, and reduce any
unnecessary grants to Actions read / Contents read / required Metadata read.
Do not create or broaden a token. No token settings were changed.

The pinned model, distinct database roles, allowlist and absent fresh ledger were
rechecked. Configuration-only dry-run passed without monitoring or predictions.
The exact session command below remains conditional on **resolved clock/token
evidence and separate live-session approval**; the refresh approval is now
satisfied. Overall recommendation remains **NO-GO**. No live observation started.

## Original preflight (superseded where noted above)

**NO-GO. No live observation started. No database refresh performed.**
This is operational evidence, not a new historical model evaluation. The existing
observer, model, frontend, source database and demo database were not changed.

## Clock evidence and required manual action

Windows Time is stopped, startup mode Manual; this computer is not domain joined.
The configured mechanism is NTP using the Windows default peer. Status/source
queries returned service-not-started (0x80070426). No service, settings or clock
changes were made.

Three read-only `w32tm` packet samples at 15:07:34–36 IST on November 23 showed
reported offsets −0.2097768, −0.2086404 and −0.2065496 seconds, with round trips
34.279, 29.989 and 29.7343 milliseconds. Root dispersion was approximately
10 milliseconds. A conditional instantaneous estimate
`abs(offset) + RTT/2 + root_dispersion + abs(root_delay)/2` is at most 0.236995
seconds in these samples. This is **not** a justified error bound for a future
900-second session: NTP was unauthenticated and future drift/time changes remain
unbounded. The observer's session bound and evidence file remain unset. These
samples must not be converted into timing verification.

Manual action is required. In an **Administrator PowerShell**, after deciding to
authorize Windows synchronization, run the following; these commands were NOT
executed by this preflight:

```powershell
Start-Service -Name W32Time
w32tm /resync /rediscover
w32tm /query /source
w32tm /query /status /verbose
w32tm /stripchart /computer:time.windows.com /samples:10 /period:1 /packetinfo
```

If resynchronization fails, stop and review configuration before changing peers,
startup settings or firewall rules. A running service alone is insufficient:
retain source, last successful synchronization, offset/error evidence and a
justified conservative bound valid through the whole proposed session. Never
invent `max_error_seconds` or `valid_until`. See Microsoft's
[Windows Time tools documentation](https://learn.microsoft.com/en-us/windows-server/networking/windows-time-service/windows-time-service-tools-and-settings).

## Repository and credential checks

Authenticated read-only repository, Actions and Contents requests succeeded.
Repository identity is `saksham-1326/Cloud-Byte-XL-Project`, numeric ID
`1319512023`, matching preserved seed metadata. The observer allowlist contains
only this repository (case normalized). The existing credential was used in
memory, without printing or copying it into receipts.

The credential has a fine-grained PAT format, but its effective Actions read,
Contents read and selected-repository restrictions are **UNVERIFIED**. This is a
public repository: HTTP 200 proves endpoint accessibility, not explicit grants.
Endpoint permission requirement headers are not token permission introspection.
No other repository was probed and no credential was created or broadened.

Manually inspect the existing fine-grained token in GitHub settings: resource
owner, expiry, **Only select repositories** containing exactly the approved
repository, Actions read and Contents read; Metadata read is automatic. Do not
paste the token or a screenshot containing it. If these restrictions cannot be
established, do not start this session. References:
[Actions runs](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs),
[Contents](https://docs.github.com/en/rest/repos/contents#get-repository-content),
[PAT settings](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## Historical refresh — preview only, approval required

Destination: **127.0.0.1:55439 / cloud_bytexl_observation_20261123**. Source and demo
databases are outside this refresh. The preview used 36 bounded GitHub GETs and
the existing collector with an in-memory, non-writing sink. It enumerated
completed runs and individual attempts, including reruns; it did not use creation
time alone to exclude older rerun identities. Exact attempt/job associations,
commit identities and completion metadata were checked. No logs were downloaded.

| Records | Before | Proposed additions | Expected after approval |
|---|---:|---:|---:|
| Run attempts | 28 | 16 | 44 |
| Unique run IDs | 27 | 16 | 43 |
| Jobs | 0 | 21 | 21 |
| Steps | 0 | 308 | 308 |
| Outcomes | 28 | 16 | 44 |
| Models | 1 | 0 | 1 |
| Predictions / shadow events | 0 / 0 | 0 / 0 | 0 / 0 |

The proposed outcomes are 15 success and one actual historical failure. Missing
job completion evidence: zero. **Imported records: zero; database writes: zero.**
The exact reviewed run IDs below all have attempt **1**:

```text
45141514112 45140690117 45139343901 45063136997
45062533137 45061353406 44879776217 44878837018
44776070330 44772706803 44769120195 44766575831
44762894885 44762028870 44755756074 44754556387
```

Reviewed sanitized metadata-set SHA-256:
`dd7f2a5cc0a5241bc013d550da8a8c447ecd99ef2368565e08385c20c7fc37b4`.
Local ignored receipts are in
`backend/reports/final_observation_preflight_20261123/`: `refresh_preview.json`,
`refresh_preview_records.json` and `github_read_requests.json` retain exact
identities, source requests, observation timestamps and metadata digests.

After explicit approval of this destination and exact scope, reuse
`synchronize_attempt` and `Store.save_run` in one observation-only transaction.
Check the reviewed base hashes first; stop on changed metadata, commit identity,
unexpected existing keys or nonzero predictions. Import only the reviewed new
attempts, retain provenance, independently verify counts and relationships, then
commit. Roll back on mismatch. Never overwrite existing seed rows, source/demo
records, model records or predictions. Import outcome observation time means the
time history was collected, not a fabricated historical prediction/commit time.
All imported history is excluded from prospective metrics.

## Database, model, independent readback and ledger

Distinct writer and read-only roles were verified through separate PostgreSQL
backend connections:

- `cloud_bytexl_observer_writer_20261123`
- `cloud_bytexl_observer_reader_20261123`

Both preflight connections were forced read-only. The writer's intended grants
allow prediction insertion and verification-status updates, but not probability,
prediction-time or model-field updates. The reader cannot insert predictions.
The existing exact-repository/run/attempt readback query executes successfully;
it returns no prediction because none exists. Actual live persistence remains
unobserved. No database commit timestamp was fabricated.

The registry model and original artifact load successfully with matching digest:

```text
model: 55ef22a1-2f30-47f2-95d8-bf12efaf6463
SHA-256: 075d37741200bb9aaf8939fd92ee621d5fe445a11842359ba443c3ad348660a7
feature version: prequeue-v2-utc-standardized
threshold: 0.5
```

Fresh session ledger:
`backend/reports/observations/prospective_20261123_final.jsonl`.
It does not exist and was not opened. The existing separate controlled ledger's
hash chain/restart check passed without mutation; that record is controlled-test
evidence, not a prospective observation.

## Exact session profile and repeatable configuration check

| Setting | Value |
|---|---|
| Repository / sole allowlist entry | saksham-1326/Cloud-Byte-XL-Project |
| Interval | 15 seconds |
| Maximum duration | 900 seconds |
| Maximum GET requests | 300 |
| Maximum polls | 60 |
| Database / roles / model / ledger | Exact identities above |
| Clock bound / clock evidence | Unresolved / absent |
| Prospective predictions | Zero |

Copyable safe configuration-only check (no network, DB connection, ledger or
prediction):

```powershell
Set-Location C:\Project\Cloud-ByteXL
.\backend\venv\Scripts\python.exe backend\reports\final_observation_preflight_20261123\dry_run_current_profile.py
```

Actual result: `mode=offline_configuration_dry_run`, `valid=true`,
`network_access=false`, `database_access=false`, `prediction_submitted=false`.
The CLI explicitly warns that this check does not verify permissions, model
registry, artifact or clock evidence. Separate checks above supply only the
evidence actually established.

Offline observer regressions: **35 passed, 0 failed, 0 skipped**. No production
source changed, and no historical model evaluation was repeated. Preservation
manifests matched all 81 and 44 checked files, including saved artifacts,
preserved evidence, frontend files and pre-existing local work. The changed
README and this guide contain no configured credential values. The seven
observation tables matched their before/after preview hashes. No source/demo
database writes were attempted. The index remains unstaged; no commit was made.

## Commands for a subsequently approved session

**Do not execute now.** First approve and complete the exact refresh, verify the
existing token restrictions, resolve clock evidence, and explicitly approve one
live session. The placeholders below deliberately prevent an unapproved start.
Use the existing protected DSNs; never echo the private configuration. Set
`GITHUB_TOKEN` securely from the existing approved source if absent, never put a
literal token in commands or shell history.

Reviewed clock JSON must contain actual `measured_at`, `valid_until`,
`max_error_seconds` and nonempty `method` values, with timezone-aware timestamps.
No valid clock JSON has been generated by this task.

```powershell
Set-Location C:\Project\Cloud-ByteXL
$clockEvidence = Read-Host 'Absolute path to reviewed, valid clock evidence JSON'
$boundText = Read-Host 'Approved whole-session clock error bound in seconds'
$approval = Read-Host 'Only after explicit session approval, type APPROVED'
if ($approval -cne 'APPROVED') { throw 'NO-GO: live session not approved' }
if (!(Test-Path -LiteralPath $clockEvidence -PathType Leaf)) { throw 'Missing clock evidence' }
$bound = [double]::Parse($boundText, [Globalization.CultureInfo]::InvariantCulture)
if ($bound -lt 0 -or [double]::IsNaN($bound) -or [double]::IsInfinity($bound)) { throw 'Invalid bound' }
$private = Get-Content -Raw backend\reports\ai_verification_20261123\observer_private_config.json | ConvertFrom-Json
$env:OBSERVER_WRITER_DSN = $private.writer_dsn
$env:OBSERVER_READER_DSN = $private.reader_dsn
if (!$env:GITHUB_TOKEN) {
  $secure = Read-Host 'Existing approved GitHub token' -AsSecureString
  $env:GITHUB_TOKEN = [pscredential]::new('GitHub', $secure).GetNetworkCredential().Password
}
$session = Get-Content -Raw backend\reports\final_observation_preflight_20261123\session_preflight.json | ConvertFrom-Json
$observerArgs = @($session.args_without_mode_or_credentials) + @('--clock-uncertainty-seconds', $boundText, '--clock-evidence-ref', $clockEvidence)
# Recheck refresh completion and token review before this final command.
.\backend\venv\Scripts\python.exe -m backend.tools.observe_actions --run @observerArgs
```

Before execution, confirm the ledger remains absent and the public profile still
matches this review. The existing CLI checks clock evidence freshness and coverage
of the duration. Typing APPROVED is only a guard against accidental execution;
it does not establish clock accuracy, permission scope or refresh approval.
Keep protected credential files local. Do not enable a webhook or start Flask:
the independent CLI uses PostgreSQL directly. Stop at configured bounds. A run
that starts before verifiable prediction persistence must not count as verified
pre-start prediction; late/uncertain events remain excluded. A database read
timestamp is not an independently proven commit timestamp.

## Decision

**NO-GO** pending (1) defensible whole-session clock evidence, (2) confirmation of
the existing token's grants and selected-repository restriction, (3) explicit
approval and independently checked execution of the historical refresh, and
(4) separate approval to start the bounded session. Zero prospective predictions
and zero independent human RCA reviews remain the truthful state.
