import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const app=readFileSync(new URL('../src/App.jsx',import.meta.url),'utf8');
const theme=readFileSync(new URL('../src/mission-theme.css',import.meta.url),'utf8');

test('public database warning is informational, not a connection error',()=>{
  assert.match(app,/setDatabaseNotice\(Boolean\(data\.databaseWarning\)\)/);
  assert.doesNotMatch(app,/if\(data\.databaseWarning\)setConnectionError/);
  assert.match(app,/role="status" aria-label="Repository storage mode"/);
  assert.match(app,/Read-only analysis/);
  assert.match(app,/Saving this repository to the database is disabled for public visitors/);
});

test('informational notice can be dismissed and is confined to overview',()=>{
  assert.match(app,/repoConnected && databaseNotice && page === "overview"/);
  assert.match(app,/aria-label="Dismiss storage information"/);
  assert.match(app,/onClick=\{\(\) => setDatabaseNotice\(false\)\}/);
});

test('real connection errors remain alerts while read-only mode has its own styling',()=>{
  assert.match(app,/connectionError && <div className="ai-alert error" role="alert"/);
  assert.match(theme,/\.repository-storage-notice \{/);
  assert.match(theme,/\.repository-storage-notice__close:focus-visible/);
  assert.match(theme,/@media\(max-width:639px\)/);
});
