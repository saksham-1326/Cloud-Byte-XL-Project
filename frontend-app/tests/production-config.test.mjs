import test from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const cwd = fileURLToPath(new URL('../', import.meta.url))
for (const target of ['', 'http://localhost:5000', 'https://backend.example.invalid/api']) {
  test(`production build rejects unsafe or missing API origin: ${target || 'missing'}`, () => {
    const result = spawnSync(process.execPath, ['node_modules/vite/bin/vite.js', 'build'], {
      cwd, env: { ...process.env, VITE_API_BASE_URL: target }, encoding: 'utf8', timeout: 30000,
    })
    assert.equal(result.error, undefined)
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /Production build requires VITE_API_BASE_URL/)
  })
}
