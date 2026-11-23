# Independent RCA review handoff

Please assess the preserved reports yourself before reading project evaluation
guides or assistant recommendations. This handoff intentionally supplies no
suggested verdicts or prior decision totals.

Open only these files initially:

- `backend/reports/ai_verification_20261123/reviewer_packet/EVIDENCE_AND_RESPONSES.md`
- `backend/reports/ai_verification_20261123/reviewer_packet/worksheet_blank.json`
- `backend/reports/ai_verification_20261123/reviewer_packet/reviewer_provenance_blank.json`

The packet has eight saved reports from four historical workflow failures. It
contains original AI diagnoses, not established ground truth. Full earlier
prompts and most complete logs are unavailable; the packet labels the available
excerpts. Session/source names remain visible, so this is not a blinded study.

Copy the worksheet and provenance template under distinct reviewer filenames.
Keep the templates unchanged. Declare prior involvement in the project or prior
exposure to assistant recommendations; a project-author assessment is not
automatically independent. Use a stable reviewer label, not sensitive personal
information. Self-reported identity is not authenticated identity.

For each report:

1. Read original logs and step metadata before the diagnosis. Distinguish the
   first demonstrated failure from later errors or successful cleanup.
2. Judge the primary cause, category, step, supporting evidence and recommended
   fix separately. A valid citation identifier does not establish claim support.
3. Record material unsupported claims and explain uncertainty or missing evidence.
4. Choose accept, reject or uncertain yourself. Leave unresolved criterion values
   `null`; do not guess. `unsupported_claims: true` means a problem was found.
5. When you personally finish a row, identify yourself, set `review_source` to
   `human` and `completed` to `true`. The assistant must not do this for you.

Return your separate files to the project author. Do not call the human-review
API during the read-only demo. Review completeness and independence must be
checked before calculating or presenting human accuracy. Eight reports still
represent only four shared workflows, not eight independent failures.

At preparation time: eight template rows, zero completed independent reviews.

## Recording decisions and calculating later

For each correctness criterion, `true` means correct, `false` means incorrect,
and `null` means uncertain/unanswered. The overall `decision` uses `accept`,
`reject` or `uncertain`; keep those distinct from the criterion booleans.

After a reviewer returns a completed copy, the project author can calculate
results offline from the repository root (replace the filename with that copy):

```powershell
Set-Location C:\Project\Cloud-ByteXL
.\backend\venv\Scripts\python.exe -c "import json; from backend.ai_intelligence.review_metrics import calculate; p='backend/reports/ai_verification_20261123/reviewer_packet/reviewer_A.json'; print(json.dumps(calculate(json.load(open(p, encoding='utf-8'))), indent=2))"
```

Only completed `review_source: "human"` rows count. Unresolved criteria are
excluded from their respective denominators; uncertain overall decisions do not
enter the accept/reject rejection-rate denominator. Earlier/improved source
sessions are reported separately. Duplicate completed report IDs require
adjudication before calculation. Secondary-error fields are qualitative and do
not produce an automatic secondary-error accuracy score. The calculator does
not authenticate reviewer identity or independence. On the untouched template,
the result is zero completed reviews and null rates, never an accuracy percentage.
