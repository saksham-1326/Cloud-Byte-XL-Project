import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8');
const entry = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');
const styles = readFileSync(new URL('../src/mission-theme.css', import.meta.url), 'utf8');

test('mission-control design system is globally mounted after base page CSS', () => {
  assert.match(entry, /import ['"]\.\/platform\.css['"]/);
  assert.match(entry, /import ['"]\.\/mission-theme\.css['"]/);
  assert.ok(entry.indexOf('mission-theme.css') > entry.indexOf('platform.css'));
  for (const selector of ['.workspace-sidebar', '.workspace-navbar', '.workspace-content', '.glass-panel', '.platform-page', '.ai-workspace', '.page-stats']) {
    assert.ok(styles.includes(selector), `${selector} missing from shared theme`);
  }
});

test('all 12 pages are present in a common workspace and keep their functional routing', () => {
  const pages = ['overview', 'repository', 'analysis', 'issues', 'architecture', 'kubernetes', 'docker', 'cicd', 'security', 'recommendations', 'intelligence', 'reports'];
  for (const page of pages) {
    assert.match(app, new RegExp(`case ["']${page}["']:`), `${page} must stay routed`);
  }
  assert.match(app, /workspace-identity/);
  assert.match(app, /workspace-route/);
  assert.match(app, /<AIIntelligence/);
  assert.match(app, /publishRepositoryData\(data\)/);
  assert.match(app, /requestJson\(`\$\{API_BASE\}\/api\/github\/repository`/);
});

test('shared visual system does not introduce hidden controls or override read-only AI restrictions', () => {
  assert.doesNotMatch(styles, /pointer-events:\s*none\s*!important/);
  assert.match(styles, /focus-visible/);
  assert.match(styles, /prefers-reduced-motion/);
  assert.match(styles, /max-width:639px/);
});