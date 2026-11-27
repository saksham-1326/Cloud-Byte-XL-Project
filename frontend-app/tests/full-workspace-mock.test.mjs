import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DEMO_REPOSITORY, DEMO_REPOSITORY_URL, normalizeRepositoryUrl, validateDemoRepository } from "../src/repoAccess.js";
import { requestJson } from "../src/api.js";

const app = readFileSync(new URL("../src/App.jsx",import.meta.url),"utf8");
const ai = readFileSync(new URL("../src/AIIntelligence.jsx",import.meta.url),"utf8");
const theme = readFileSync(new URL("../src/mission-theme.css",import.meta.url),"utf8");

test("demo repository accepts canonical and case-insensitive approved URLs",()=>{
  for(const value of [
    "https://github.com/saksham-1326/Cloud-Byte-XL-Project",
    "github.com/saksham-1326/Cloud-Byte-XL-Project",
    "https://github.com/SAKSHAM-1326/cloud-byte-xl-project/",
    "https://github.com/saksham-1326/Cloud-Byte-XL-Project.git",
  ]) assert.equal(validateDemoRepository(value),DEMO_REPOSITORY_URL);
  assert.equal(DEMO_REPOSITORY,"saksham-1326/Cloud-Byte-XL-Project");
});

test("public repository restrictions reject other repos and hostile URLs",()=>{
  for(const value of [
    "https://github.com/unapproved/repo",
    "https://evil.example/anything",
    "https://github.com.evil.example/saksham-1326/Cloud-Byte-XL-Project",
    "https://github.com/user/repo?access_token=x",
    "https://github.com/user/repo#fragment",
    "https://user:pass@github.com/user/repo",
    "http://github.com/saksham-1326/Cloud-Byte-XL-Project",
    "https://github.com/owner/repo/extra",
    "",
  ]) assert.throws(()=>validateDemoRepository(value),Error);
});

test("repository validation reports why permission denial occurred before network call",()=>{
  assert.throws(()=>validateDemoRepository("github.com/other/repo"),/only permits/);
  assert.equal(normalizeRepositoryUrl("github.com/other/repo"),"https://github.com/other/repo");
  assert.match(app,/repoUrl = validateDemoRepository\(url \|\| ""\)/);
  assert.match(app,/This public demo permits only/);
});

test("all twelve navigation destinations have a page route",()=>{
  const section=app.slice(app.indexOf("const NAV_ITEMS ="),app.indexOf("const NAV_GROUPS ="));
  const routes=[...section.matchAll(/key:\s*"([a-z]+)"/g)].map(x=>x[1]);
  assert.deepEqual(routes,["overview","repository","analysis","issues","architecture","kubernetes","docker","cicd","security","recommendations","intelligence","reports"]);
  for(const key of routes){
    if(key==="intelligence") assert.match(app,/page === "intelligence"/);
    else assert.ok(app.includes('case "'+key+'":'),key+" missing route");
  }
  assert.match(app,/onClick=\{\(\) => setPage\(key\)\}/);
});

test("scan and navigation remain recoverable, including failure, cancellation and retry",()=>{
  for(const term of ["Cancel scan and go back","timeoutMs:75000","onCancel","event.key === \"Escape\"",
    "setAnalyzing(false)","setConnectionError(error.message","publishRepositoryData(data)",
    "setRepoConnected(true)","setPage(\"overview\")"])
    assert.ok(app.includes(term),term);
});

test("AI intelligence reads stored real evidence and remains read-only in production",()=>{
  assert.match(ai,/\/overview\?repository=/);
  assert.match(ai,/timeoutMs:60000/);
  assert.match(ai,/VITE_ENABLE_MODEL_TRAINING/);
  assert.match(ai,/VITE_ENABLE_LIVE_PREDICTIONS/);
  assert.match(ai,/VITE_ENABLE_PROVIDER_CALLS/);
  assert.match(app,/page === "intelligence"/);
});

test("all visible settings and report actions stay wired, with unavailable chat disabled",()=>{
  for(const term of ["handleExport","Blob([JSON.stringify(report","onMarkReviewed",
    "onClose","onAnalyze","setShowConnectModal(true)","setMobileNavOpen",
    "AI chat is not available","onClick={() => setDatabaseNotice(false)}"])
    assert.ok(app.includes(term),term);
  assert.match(theme,/\.repository-storage-notice/);
});

test("mock backend success and read-only warning payload retain exact API contract",async t=>{
  const response={
    status:"SUCCESS",
    repository:{name:"Cloud-Byte-XL-Project",fullName:DEMO_REPOSITORY,url:DEMO_REPOSITORY_URL,branch:"main"},
    files:[{path:"README.md"}],
    analysis:{overall:76,issues:[],security:{score:78}},
    databaseWarning:"Public demo analysis is read-only; this repository was not saved to PostgreSQL.",
  };
  t.mock.method(globalThis,"fetch",async (url,opts)=>{
    assert.equal(url,"https://example.invalid/api/github/repository");
    assert.equal(opts.method,"POST");
    assert.equal(JSON.parse(opts.body).url,DEMO_REPOSITORY_URL);
    return Response.json(response);
  });
  const result=await requestJson("https://example.invalid/api/github/repository",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({url:validateDemoRepository(DEMO_REPOSITORY_URL)})
  });
  assert.equal(result.repository.fullName,DEMO_REPOSITORY);
  assert.equal(result.analysis.overall,76);
  assert.match(result.databaseWarning,/read-only/);
});

test("mock backend forbidden response displays informative error",async t=>{
  t.mock.method(globalThis,"fetch",async()=>Response.json({status:"FAILED",message:"Repository is not allowlisted."},{status:403}));
  await assert.rejects(requestJson("https://example.invalid/api/github/repository"),/Repository is not allowlisted/);
});

test("mock historical AI overview preserves model status and failed-run evidence",async t=>{
  const payload={status:"SUCCESS",data:{models:[{status:"experimental",metrics:{test:{f1:0},release_gate:{status:"insufficient_evidence",reasons:["Failure recall unverified"]}}}],runs:[{conclusion:"failure"}],rca:[{engine:"evidence_rules"}]}};
  t.mock.method(globalThis,"fetch",async()=>Response.json(payload));
  const result=await requestJson("https://example.invalid/api/ai/v1/overview?repository="+DEMO_REPOSITORY);
  assert.equal(result.data.models[0].metrics.test.f1,0);
  assert.equal(result.data.models[0].metrics.release_gate.status,"insufficient_evidence");
  assert.equal(result.data.runs[0].conclusion,"failure");
});

test("mock network outage and non-JSON Render errors never display fabricated analysis",async t=>{
  const m=t.mock.method(globalThis,"fetch",async()=>{throw new TypeError("simulated DNS failure");});
  await assert.rejects(requestJson("https://example.invalid/api/github/repository"),/Cannot reach the backend/);
  m.mock.mockImplementation(async()=>new Response("<html>Gateway Timeout</html>",{status:504,headers:{"content-type":"text/html"}}));
  await assert.rejects(requestJson("https://example.invalid/api/github/repository"),/non-JSON/);
});

test("mock read-only mutation rejected by backend",async t=>{
  t.mock.method(globalThis,"fetch",async()=>Response.json({status:"FAILED",message:"Endpoint unavailable in read-only public demo."},{status:403}));
  await assert.rejects(requestJson("https://example.invalid/api/ai/v1/train",{method:"POST",body:"{}"}),/read-only public demo/);
});
