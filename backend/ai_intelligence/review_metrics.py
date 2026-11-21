"""Offline descriptive metrics for explicitly completed manual worksheets.

Never writes to the database or treats agent proposals as human submissions.
One adjudicated row per report; unresolved judgments remain null.
"""

FIELDS = {
    'primary_root_cause_accuracy': 'primary_cause_correct',
    'failure_category_accuracy': 'category_correct',
    'failed_step_accuracy': 'step_correct',
    'evidence_support_rate': 'evidence_correct',
    'unsupported_claim_rate': 'unsupported_claims',
    'recommended_fix_correctness': 'fix_correct',
}


def _calculate(rows):
    completed = [r for r in rows if r.get('review_source') == 'human'
                 and r.get('completed') is True]
    ids = [r['report_id'] for r in completed]
    if len(ids) != len(set(ids)):
        raise ValueError('Adjudicate duplicate report reviews before calculating metrics.')
    for row in completed:
        if row.get('decision') not in (None, 'accept', 'reject', 'uncertain'):
            raise ValueError('Decision must be accept, reject, uncertain or null.')
        for field in FIELDS.values():
            if row.get(field) is not None and type(row[field]) is not bool:
                raise ValueError(f'{field} must be boolean or null.')
    result = {}
    for metric, field in FIELDS.items():
        values = [r[field] for r in completed if type(r.get(field)) is bool]
        result[metric] = {'numerator': sum(values), 'sample_size': len(values),
                          'rate': sum(values) / len(values) if values else None}
    decisions = [r['decision'] for r in completed
                 if r.get('decision') in ('accept', 'reject')]
    rejected = decisions.count('reject')
    result['rejection_rate'] = {'numerator': rejected, 'sample_size': len(decisions),
                              'rate': rejected / len(decisions) if decisions else None}
    return {'human_reviewed_reports': len(completed), 'metrics': result,
            'distinct_workflows': len({(r.get('repository'), r.get('run_id', r.get('run_number')), r.get('attempt', 1))
                                      for r in completed if r.get('run_id', r.get('run_number')) is not None}),
            'uncertain_decisions': sum(r.get('decision') == 'uncertain' for r in completed),
            'limitation': 'Descriptive report-level rates; repeated reports share runs. '
                          'This small single-repository sample cannot establish production accuracy.'}


def calculate(rows):
    """Report pooled descriptive results and separate source sessions.

    completed means the reviewer finished assessing the available material, not
    that every criterion is resolved. Null evidence judgments are excluded from
    that metric; missing evidence is never silently assigned a pass or failure.
    """
    rows = list(rows)
    result = _calculate(rows)
    result['by_session'] = {
        source: _calculate([r for r in rows if (r.get('source') or 'unspecified') == source])
        for source in sorted({r.get('source') or 'unspecified' for r in rows})
    }
    return result
