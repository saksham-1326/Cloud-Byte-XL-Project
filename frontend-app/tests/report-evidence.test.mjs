import test from 'node:test';
import assert from 'node:assert/strict';
import { publishRepositoryData, buildRepositoryReport } from '../src/repositoryData.js';

test('downloaded report retains the measured duration, exact revision and dashboard file inventory', () => {
  const files = [{ path: 'Dockerfile', size: 42 }, { path: 'backend/app.py', size: 100 }];
  publishRepositoryData({ repository: { fullName: 'fixture/project', analysisCommitSha: 'a'.repeat(40) },
    files, languages: [{ name: 'Python', percentage: 100 }], scanDurationMs: 8290,
    analysis: { overall: 80, issues: [], severityCounts: { critical: 0, high: 0, medium: 0, low: 0 } } });
  const report = JSON.parse(JSON.stringify(buildRepositoryReport()));
  assert.equal(report.repository.analysisDuration, '8.29s');
  assert.equal(report.repository.analysisCommitSha, 'a'.repeat(40));
  assert.equal(report.fileCount, 2);
  assert.deepEqual(report.files, files);
  assert.equal(report.health.overall, 80);
  assert.match(report.inspectionNote, /bounded source inspection/);
});

test('unknown duration stays unavailable after a new scan rather than reusing an earlier measurement', () => {
  for (const scanDurationMs of [undefined, null, -1, Infinity, '123']) {
    publishRepositoryData({ repository: { fullName: 'fixture/project' }, files: [], scanDurationMs });
    assert.equal(buildRepositoryReport().repository.analysisDuration, '—');
  }
});
