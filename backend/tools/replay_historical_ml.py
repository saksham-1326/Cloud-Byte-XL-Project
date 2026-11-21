"""Replay saved historical probabilities, not a fresh fit or prospective test.

No database writes, provider calls or artifact deserialization. The saved
evaluation must come from this repository's existing historical experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sklearn.dummy import DummyClassifier

from backend.ai_intelligence.ml import metrics


def replay(saved):
    rows = saved['backtest']
    ids = [(r['run_id'], r['attempt']) for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate workflow attempts in historical test set.')
    labels = [r['label'] for r in rows]
    predicted = metrics(labels, [r['probability'] for r in rows], saved['threshold'])
    # Recover aggregate split class counts from saved confusion matrices.
    # This does not recover missing training IDs, features or raw run records.
    val_matrix = saved['comparisons']['dummy']['validation']['confusion_matrix']
    validation_counts = [sum(row) for row in val_matrix]
    test_counts = [labels.count(v) for v in (0, 1)]
    train_counts = [saved['class_distribution'][key] - validation_counts[v] - test_counts[v]
                    for v, key in enumerate(('success', 'failure'))]
    if min(train_counts) < 0 or sum(train_counts) != saved['split_sizes']['train']:
        raise ValueError('Saved split class counts are inconsistent.')
    training_labels = [0] * train_counts[0] + [1] * train_counts[1]
    dummy = DummyClassifier(strategy='prior').fit([[0]] * len(training_labels), training_labels)
    baseline = metrics(labels, dummy.predict_proba([[0]] * len(labels))[:, 1],
                       saved['comparisons']['dummy']['threshold'])
    fields = ['n', 'accuracy', 'precision', 'recall', 'f1', 'confusion_matrix', 'pr_auc']
    matches = all(predicted[k] == saved['test'][k] for k in fields)
    baseline_matches = all(baseline[k] == saved['comparisons']['dummy']['test'][k] for k in fields)
    return dict(evaluation_type='historical_saved_prediction_replay_not_fresh_training_or_prospective',
                historical_evaluation_date=saved['evaluation_date'], dataset_size=saved['dataset_size'],
                split_sizes=saved['split_sizes'],
                split_class_counts=dict(train=dict(zip(('success', 'failure'), train_counts)),
                                        validation=dict(zip(('success', 'failure'), validation_counts)),
                                        test=dict(zip(('success', 'failure'), test_counts))),
                selected_model=saved['selected_model'], threshold=saved['threshold'],
                selected_metrics=predicted, dummy_metrics=baseline,
                saved_selected_metrics_match=matches, saved_dummy_metrics_match=baseline_matches,
                false_negatives=[dict(run_id=r['run_id'], probability=r['probability'])
                                 for r in rows if r['label'] == 1 and r['probability'] < saved['threshold']],
                limitation='Only saved test probabilities are replayed. Dummy prior is fitted from '
                           'recovered aggregate training class counts, not fabricated executions. '
                           'Raw training records/snapshots are unavailable; fitting, chronological '
                           'split membership and original feature availability cannot be fully reproduced.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('backend/reports/model_evaluation.json'))
    parser.add_argument('--output', type=Path, default=Path('backend/reports/historical_ml_replay.json'))
    args = parser.parse_args()
    content = args.input.read_bytes()
    result = replay(json.loads(content))
    result['input_sha256'] = hashlib.sha256(content).hexdigest()
    if args.input.resolve() == args.output.resolve():
        raise ValueError('Output must not overwrite the source evaluation.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
