import test from "node:test";
import assert from "node:assert/strict";
import { requestJson } from "../src/api.js";
import { emptyReview, percent, fixed, date, reviewPayload, shadowRecord, guardStatus } from "../src/aiContract.js";
import * as repository from "../src/repositoryData.js";

test("missing/nonfinite metrics stay unavailable while real zero remains zero", () => {
  assert.equal(percent(0), "0.0%");
  for (const value of [null, undefined, NaN, Infinity, "0.5"]) assert.equal(percent(value), "Unavailable");
  assert.equal(fixed(null), "Unavailable");
  assert.equal(date("invalid-date"), "Unavailable");
});

test("unanswered criteria and an identity alone cannot submit a human review", () => {
  assert.equal(reviewPayload(emptyReview(), "reviewer", true), null);
  const review = Object.fromEntries(Object.keys(emptyReview()).map(key => [key, "true"]));
  assert.equal(reviewPayload(review, "reviewer", false), null);
  assert.equal(reviewPayload(review, "", true), null);
  review.unsupported_claims = "false";
  const payload = reviewPayload(review, " reviewer ", true);
  assert.equal(payload.unsupported_claims, false);
  assert.equal(payload.category_correct, true);
  assert.equal(payload.reviewer, "reviewer");
});

test("backtests and invalid/unverifiable timing rows never become displayed shadow candidates", () => {
  const rows = [
    { mode: "backtest", verification_status: "historical_backtest" },
    { mode: "shadow", verification_status: "invalid_timing" },
    { mode: "shadow", verification_status: "unverifiable_timing" },
  ];
  assert.equal(shadowRecord(rows), undefined);
  const matched = { mode: "shadow", verification_status: "matched" };
  assert.equal(shadowRecord([...rows, matched]), matched);
});

test("later automated rejection is visible even when the original model guard passed", () => {
  assert.equal(guardStatus({ validation: { status: "passed" }, live_validation: { final_guard: { status: "rejected" } } }), "rejected");
  assert.equal(guardStatus({}), "not evaluated");
});

test("switching repositories clears findings and scores when analysis is unavailable", () => {
  repository.publishRepositoryData({ repository: { fullName: "fixture/first", url: "https://github.com/fixture/first" },
    files: [], analysis: { overall: 90, issues: [{ id: "old" }], severityCounts: { critical: 1, high: 0, medium: 0, low: 0 },
      architecture: { provider: "Old provider", detected: { cloudResources: ["old"] } } } });
  assert.equal(repository.ISSUES.length, 1);
  repository.publishRepositoryData({ repository: { fullName: "fixture/second", analysisCommitSha: "a".repeat(40) }, files: [] });
  assert.deepEqual(repository.ISSUES, []);
  assert.deepEqual(repository.ANALYSIS_HISTORY, []);
  assert.equal(repository.HEALTH.overall, null);
  assert.equal(repository.SECURITY.score, null);
  assert.deepEqual(repository.ARCH.services, []);
  assert.equal(repository.REPO.analysisCommitSha, "a".repeat(40));
});

test("successful JSON and zero-valued persisted metrics survive the fetch boundary", async t => {
  t.mock.method(globalThis, "fetch", async () => Response.json({ status: "SUCCESS", data: { test: { recall: 0 } } }));
  assert.equal((await requestJson("http://localhost/fixture")).data.test.recall, 0);
});

test("provider/API errors are surfaced, never replaced by a successful model response", async t => {
  t.mock.method(globalThis, "fetch", async () => Response.json({ status: "FAILED", message: "Provider unavailable" }, { status: 503 }));
  await assert.rejects(requestJson("http://localhost/fixture"), /Provider unavailable/);
});

test("HTML proxy errors do not leak their body or become a JSON parse crash", async t => {
  t.mock.method(globalThis, "fetch", async () => new Response("private HTML", { status: 502, headers: { "content-type": "text/html" } }));
  await assert.rejects(requestJson("http://localhost/fixture"), error => /non-JSON/.test(error.message) && !error.message.includes("private HTML"));
});

test("a JSON array or missing success status cannot appear as a successful analysis", async t => {
  const mock = t.mock.method(globalThis, "fetch", async () => Response.json([]));
  await assert.rejects(requestJson("http://localhost/fixture"), /invalid response contract/);
  mock.mock.mockImplementation(async () => Response.json({}));
  await assert.rejects(requestJson("http://localhost/fixture"), /supported status/);
});

test("network failure gives a local backend startup message", async t => {
  t.mock.method(globalThis, "fetch", async () => { throw new TypeError("network details"); });
  await assert.rejects(requestJson("http://localhost/fixture"), /Cannot reach the backend/);
});

test("timeouts abort the request and explain that the backend task might still run", async t => {
  t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
  }));
  await assert.rejects(requestJson("http://localhost/fixture", { timeoutMs: 5 }), /timed out/);
});

test("repository-change cancellation remains distinguishable from a network error", async t => {
  const controller = new AbortController(); controller.abort();
  t.mock.method(globalThis, "fetch", async () => { throw new DOMException("aborted", "AbortError"); });
  await assert.rejects(requestJson("http://localhost/fixture", { signal: controller.signal }), { name: "AbortError" });
});
