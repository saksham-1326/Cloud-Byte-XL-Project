import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8');
const ai = readFileSync(new URL('../src/AIIntelligence.jsx', import.meta.url), 'utf8');

test('repository scan overlay has usable cancel and Escape actions', () => {
  assert.match(app, /Cancel scan and go back/);
  assert.match(app, /aria-label="Cancel repository analysis"/);
  assert.match(app, /event\.key === "Escape"/);
  assert.match(app, /analysisRequest\.current\?\.abort\(\)/);
});

test('GitHub scan is bounded and leaves the overlay on error, success or cancel', () => {
  assert.match(app, /timeoutMs:75000/);
  assert.match(app, /setAnalyzing\(false\)/);
  assert.match(app, /analysisRequest\.current=null;/);
  assert.match(app, /setConnectionError\(error\.message/);
  assert.match(app, /Repository analysis returned incomplete evidence/);
});

test('failed re-analysis preserves previously selected repository data', () => {
  const catchStart = app.indexOf('} catch (error) {', app.indexOf('const handleConnect ='));
  const finallyStart = app.indexOf('} finally {', catchStart);
  const failure = app.slice(catchStart, finallyStart);
  assert.ok(catchStart > 0 && finallyStart > catchStart);
  assert.doesNotMatch(failure, /setRepoConnected\(false\)/);
});

test('AI historical evidence remains accessible without running a new source scan', () => {
  assert.match(app, /page === "intelligence" && \(!repoConnected \|\| !REPO\.url\)/);
  assert.match(app, /AIIntelligence repository="saksham-1326\/Cloud-Byte-XL-Project"/);
  assert.match(ai, /timeoutMs:60000/);
});
