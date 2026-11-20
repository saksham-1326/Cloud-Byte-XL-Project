"""Descriptive agreement between separately identified manual review submissions."""
from itertools import combinations

FIELDS=['category_correct','step_correct','evidence_correct','fix_correct','unsupported_claims']


def agreement(reviews):
    by_report={}
    for row in reviews:by_report.setdefault(str(row['report_id']),[]).append(row)
    agreements=0;comparisons=0;pairs=0
    for rows in by_report.values():
        for a,b in combinations(rows,2):
            if a['reviewer']==b['reviewer']:continue
            pairs+=1
            for field in FIELDS:
                comparisons+=1;agreements+=a['review'][field]==b['review'][field]
    return {'agreement':agreements/comparisons if comparisons else None,'paired_reports':sum(len(rows)>1 for rows in by_report.values()),
            'reviewer_pairs':pairs,'rubric_comparisons':comparisons,
            'method':'Pairwise exact agreement over the five independent boolean rubric judgments, within each report.',
            'identity_limitation':'Reviewer identifiers are self-reported under local administrator access; identities are not independently authenticated.'}
