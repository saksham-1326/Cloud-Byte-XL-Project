"""Offline user-requested, ChatGPT-assisted recommendations; never human reviews."""
import hashlib
import json
from pathlib import Path


DECISIONS = {13: ('reject', 'reject'), 21: ('reject', 'accept'),
             23: ('uncertain', 'accept'), 27: ('uncertain', 'accept')}
SOURCES = ('live_rca_validation.json', 'rca_reliability_validation.json')


def summarize(rows):
    """Decision statistics only: no correctness scores inferred from a verdict."""
    ids = [r['report_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate report IDs cannot be counted twice.')
    if any(r['proposed_decision'] not in ('accept', 'reject', 'uncertain') for r in rows):
        raise ValueError('Invalid proposed decision.')

    def counts(group):
        totals = {v: sum(r['proposed_decision'] == v for r in group)
                  for v in ('accept', 'reject', 'uncertain')}
        resolved = totals['accept'] + totals['reject']
        return dict(report_count=len(group), distinct_workflows=len({r['run_number'] for r in group}),
                    decision_counts=totals,
                    provisional_rejection_rate=dict(numerator=totals['reject'], sample_size=resolved,
                                                    rate=totals['reject'] / resolved if resolved else None))

    return dict(status='provisional_chatgpt_assisted_not_independent_human_verification',
                overall=counts(rows), by_session={s: counts([r for r in rows if r['source'] == s])
                                                  for s in SOURCES},
                correctness_metrics=None,
                limitation='Decision rates describe assisted recommendations, not RCA accuracy. '
                           'Uncertain decisions are excluded from the rejection denominator. '
                           'No criterion-level correctness scores were supplied. Eight reports share '
                           'four workflows and cannot establish production accuracy.')


def prepare(output):
    """Write only assisted artifacts; preserve worksheet and original sources."""
    suggestions = json.loads((output / 'suggested_decisions.json').read_text())
    rows = []
    manifest = {}
    for source in SOURCES:
        path = output.parent / source
        data = json.loads(path.read_text())
        manifest[source] = hashlib.sha256(path.read_bytes()).hexdigest()
        for number in DECISIONS:
            case = next(c for c in data['cases'] if c['run_number'] == number)
            suggestion = next(r for r in suggestions if r['report_id'] == case['report_id'])
            uncertainty = ('Compiler return status is not independently established by the saved excerpt; '
                           'no syntax diagnostic is visible.' if number == 13 else
                           'The exact server-side origin of HTTP 404 is unresolved; acceptance covers '
                           'the observed callback HTTP error and curl exit 22 only.' if number in (23, 27) else
                           'Whether exit 1 was intended as failure injection requires project context.')
            rows.append(dict(report_id=case['report_id'], run_number=number, run_id=case['run_id'],
                             attempt=case['attempt'], source=source,
                             session='earlier' if source == SOURCES[0] else 'improved',
                             proposed_decision=DECISIONS[number][SOURCES.index(source)],
                             provenance='User-requested recommendations made with ChatGPT assistance; '
                                        'not independent human verification.',
                             explanation=suggestion['explanation'], uncertainty=uncertainty,
                             human_verified=False))
    package = dict(status='proposed_assistant_assisted_evaluation',
                   source_sha256=manifest, recommendations=rows)
    (output / 'assisted_recommendations.json').write_text(json.dumps(package, indent=2))
    (output / 'provisional_assisted_metrics.json').write_text(json.dumps(summarize(rows), indent=2))


if __name__ == '__main__':
    prepare(Path(__file__).resolve().parents[1] / 'reports' / 'independent_review')
