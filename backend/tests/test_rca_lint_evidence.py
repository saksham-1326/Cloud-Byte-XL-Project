"""Regression from public Actions run 45795104375, attempt 1 (Lint frontend)."""
import pytest

from backend.ai_intelligence.rca import analyze, extract_evidence, grounded_diagnosis, validate_diagnosis
from backend.tests.test_ai_ml_rca import job_case

LINT_LOG = """1094:10  error  'analyzeStep' is assigned a value but never used  no-unused-vars
✖ 1 problem (1 error, 0 warnings)
Process completed with exit code 1."""


def test_actual_eslint_coordinates_and_totals_are_not_pytest_counts():
    evidence = extract_evidence(job_case(LINT_LOG))
    assert evidence['facts']['pytest_summaries'] == []
    assert len(evidence['facts']['lint_errors']) == 1
    report = analyze(job_case(LINT_LOG))
    assert report['category'] == 'lint_failure'
    assert report['evidence_refs']
    assert 'lint rule' in report['recommended_fix']


def test_echoed_exit_does_not_override_observed_lint_diagnostic():
    assert analyze(job_case('exit 1\n' + LINT_LOG))['category'] == 'lint_failure'


def test_cited_lint_errors_cannot_support_a_provider_test_failure_claim():
    evidence = extract_evidence(job_case(LINT_LOG))
    report = grounded_diagnosis(evidence)
    report.update(category='insufficient_evidence', uncertainty='high', explanation='Unit tests failed.')
    with pytest.raises(ValueError, match='unsupported test failure'):
        validate_diagnosis(report, evidence, grounded_diagnosis(evidence))


def test_genuine_pytest_error_summary_remains_a_test_failure():
    assert analyze(job_case('1 error in 0.20s\nProcess completed with exit code 1.'))['category'] == 'unit_test_failure'
