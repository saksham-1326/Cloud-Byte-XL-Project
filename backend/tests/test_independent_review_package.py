import json
from pathlib import Path

from backend.tools import prepare_independent_review as builder


def test_rebuild_preserves_answers_and_source_evidence(tmp_path, monkeypatch):
    inputs = json.loads((Path(__file__).parent / 'fixtures/independent_review_inputs.json').read_text())['files']
    root = tmp_path / 'backend'
    output = root / 'reports' / 'independent_review'
    output.mkdir(parents=True)
    sources = {}
    for name in ['live_rca_validation.json', 'rca_reliability_validation.json']:
        sources[name] = json.dumps(inputs[name]).encode()
        (root / 'reports' / name).write_bytes(sources[name])
    ground = json.dumps(inputs['proposed_ground_truth.json']).encode()
    (output / 'proposed_ground_truth.json').write_bytes(ground)
    monkeypatch.setattr(builder, '__file__', str(root / 'tools' / 'prepare_independent_review.py'))
    builder.main()
    path = output / 'human_worksheet.json'
    rows = json.loads(path.read_text())
    assert len(rows) == 8
    assert all(r['decision'] is None and r['completed'] is False for r in rows)
    assert all(r['source'] and r['run_id'] and r['evidence_file'] for r in rows)
    assert len(json.loads((output / 'suggested_decisions.json').read_text())) == 8
    rows[0].update(comment='My unfinished note', decision='uncertain')
    path.write_text(json.dumps(rows))
    builder.main()
    assert json.loads(path.read_text()) == rows
    metrics = json.loads((output / 'metrics.json').read_text())
    assert metrics['human_reviewed_reports'] == 0
    assert len(metrics['by_session']) == 2
    assert all(m['rate'] is None for m in metrics['metrics'].values())
    guide = (output / 'REVIEW_GUIDE.md').read_text(encoding='utf-8')
    assert '"name": "Cleanup Docker container", "number": 12, "conclusion": "success"' in guide
    for row in rows:
        assert row['report_id'] in guide
    assert (output / 'proposed_ground_truth.json').read_bytes() == ground
    for name, original in sources.items():
        assert (root / 'reports' / name).read_bytes() == original
