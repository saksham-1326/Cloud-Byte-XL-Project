import json
from pathlib import Path

import pytest

from backend.ai_intelligence.review_metrics import calculate
from backend.tools.assisted_rca_recommendations import SOURCES, prepare, summarize


def test_assisted_artifacts_preserve_sources_and_never_count_as_human(tmp_path):
    inputs = json.loads((Path(__file__).parent / 'fixtures/independent_review_inputs.json').read_text())['files']
    output = tmp_path / 'independent_review'
    output.mkdir()
    preserved = {}
    for name in SOURCES:
        path = tmp_path / name
        path.write_text(json.dumps(inputs[name]))
        preserved[path] = path.read_bytes()
    for name in ['suggested_decisions.json', 'human_worksheet.json', 'proposed_ground_truth.json']:
        path = output / name
        path.write_text(json.dumps(inputs[name]))
        preserved[path] = path.read_bytes()
    prepare(output)
    rows = json.loads((output / 'assisted_recommendations.json').read_text())['recommendations']
    assert len(rows) == 8
    assert all(not r['human_verified'] for r in rows)
    assert calculate(rows)['human_reviewed_reports'] == 0
    assert all('Compiler return status' in r['uncertainty'] for r in rows if r['run_number'] == 13)
    assert all('server-side origin' in r['uncertainty'] for r in rows if r['run_number'] in (23, 27))
    metrics = summarize(rows)
    assert metrics['overall']['decision_counts'] == {'accept': 3, 'reject': 3, 'uncertain': 2}
    assert metrics['overall']['provisional_rejection_rate'] == dict(numerator=3, sample_size=6, rate=.5)
    assert metrics['by_session'][SOURCES[0]]['decision_counts'] == dict(accept=0, reject=2, uncertain=2)
    assert metrics['by_session'][SOURCES[1]]['decision_counts'] == dict(accept=3, reject=1, uncertain=0)
    assert metrics['correctness_metrics'] is None
    for path, before in preserved.items():
        assert path.read_bytes() == before
    before = (output / 'assisted_recommendations.json').read_bytes()
    prepare(output)
    assert (output / 'assisted_recommendations.json').read_bytes() == before
    with pytest.raises(ValueError):
        summarize(rows + rows[:1])


def test_no_resolved_recommendations_produces_null_rate():
    result = summarize([dict(report_id='x', run_number=23, source=SOURCES[0],
                             proposed_decision='uncertain')])
    assert result['overall']['provisional_rejection_rate']['rate'] is None
    assert result['overall']['provisional_rejection_rate']['sample_size'] == 0
