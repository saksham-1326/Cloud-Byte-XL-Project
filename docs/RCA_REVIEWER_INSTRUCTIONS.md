# Human RCA review — practical instructions

This procedure prepares real human decisions; it does not create independent verification automatically. Original source reports, evidence and worksheets remain unchanged. No PostgreSQL submission is required.

## Start with the separate packet

Open `backend/reports/ai_verification_20261123/reviewer_packet/EVIDENCE_AND_RESPONSES.md`. It contains four real runs (#13, #21, #23, #27), eight saved response IDs, original preserved log excerpts, saved step metadata and actual saved diagnosis fields. It omits assistant verdicts/automated scores. Earlier input prompts are not fully retained; later saved excerpts from the same run are identified explicitly. #21 additionally has `backend/tests/fixtures/run21_real.json`; most other full logs are unavailable here. Do not treat the excerpts as an independent full-log collection.

Use a copy of `worksheet_blank.json` with a distinct filename such as `reviewer_A.json`; do not overwrite the original `backend/reports/independent_review/human_worksheet.json`. Fill your own provenance copy from `reviewer_provenance_blank.json`. No credential, full legal name or other sensitive identifier is needed; a stable reviewer label is enough.

Record whether you are the project author, helped produce the reports, or already saw the ChatGPT-assisted suggestions. A human review by the project author is useful but is not automatically independent. An independent reviewer should assess evidence before reading the existing guide's suggested decisions. This packet is not fully blinded: source/session names remain visible. Do not claim authenticated reviewer identity from a typed identifier alone.

## Review each response separately

1. Read the command/log context and actual step outcomes first. Identify what is proven, what is missing and which operation first failed. Do not use the AI diagnosis as ground truth.
2. Read the saved response for that exact report ID/run/attempt. Each earlier/improved report needs its own row; two responses for one run are not two independent pipeline failures.
3. Follow every cited ID into the quoted source text. Check the claim it is meant to support, not just whether the identifier exists. A command shown in a script does not independently establish its exit result; `PASSED` inside a callback JSON body is not proof a test/build ran successfully.
4. Check whether a secondary error is actually another failed step, a handled cleanup message, or an unsupported assertion. A missing-container message can coexist with successful cleanup metadata. Avoid treating a later callback failure as the primary cause if an earlier operation already failed.
5. Judge the recommended fix. A sensible investigation plan may be appropriate; an asserted exact server-side cause needs evidence. Do not require a guessed explanation for unknown HTTP 404 origin. Keep #13's compiler result unresolved if the saved material does not independently establish it.
6. Enter your own criterion judgments, overall decision and notes. Do not copy the assistant's accept/reject suggestions by default.

## Worksheet fields

Use JSON booleans `true` / `false` or `null`, not strings. Null means unanswered/unresolved and does not count as either correct or incorrect.

| Field | Question |
| --- | --- |
| `primary_cause_correct` | Is the claimed primary cause supported by the actual first failure evidence? |
| `category_correct` | Is the failure category appropriate to that cause? |
| `step_correct` | Is the named failed step supported by the saved step outcomes? |
| `evidence_correct` | Do the cited lines support the material claims, beyond valid IDs? |
| `fix_correct` | Is the recommendation appropriate and bounded by available evidence? |
| `unsupported_claims` | **True means a problem:** at least one material unsupported claim exists. False means none found after assessment; null means unresolved. |
| `secondary_errors_correct` | Are secondary error/cleanup claims and omissions handled correctly? Use `secondary_error_notes` to explain. |

Choose `decision: "accept"`, `"reject"` or `"uncertain"` independently of the booleans; do not derive all criteria automatically from the verdict. Use `comment` for cited explanations and `corrected_ground_truth` only for your evidence-supported correction. Retain original report ID, source, session, run ID and attempt.

When you personally finish assessing a row, set `review_source: "human"`, provide your reviewer identifier, and set `completed: true`. A completed assessment can still have an uncertain decision and unresolved criterion values. Do not mark an untouched row complete. The assistant must not set these on your behalf.

## Calculate after actual review

The existing offline calculator accepts completed human rows, excludes unresolved criteria from their own denominators and separates source sessions. It does not authenticate independence. The added secondary-error fields are qualitative supplementary judgments; the existing calculator does not report a secondary-error accuracy score. Do not invent that score.

From the repository root, replacing the filename with your completed copy:

```powershell
.\backend\venv\Scripts\python.exe -c "import json; from backend.ai_intelligence.review_metrics import calculate; p='backend/reports/ai_verification_20261123/reviewer_packet/reviewer_A.json'; print(json.dumps(calculate(json.load(open(p, encoding='utf-8'))), indent=2))"
```

Do not call the boolean-only human verification API for uncertain/incomplete material. Keep separate reviewers' files; adjudicate duplicate report IDs before combining them. The calculator deliberately rejects duplicate completed IDs. Preserve disagreements rather than silently choosing favorable values.

Currently there are **zero completed independent reviews**, no human correctness percentages and no independent accuracy claim. Existing 3 accept / 3 reject / 2 uncertain proposals remain separately labeled ChatGPT-assisted. Even eight completed reports would cover only four shared workflows, so results must remain small-sample descriptive measurements. Additional original logs/server evidence and genuinely independent cases are needed for stronger claims.
