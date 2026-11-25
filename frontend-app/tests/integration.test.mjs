import test from 'node:test';
import assert from 'node:assert/strict';
import {configurationPaths,filePaths,sourceLink,matchingReports,evidenceAnchor,navigationMatches,exportRepository,validateRepositoryResponse,validateIntelligenceResponse} from '../src/integration.js';
test('detected configuration comes only from actual paths, not prototype examples',()=>{
  const paths=filePaths(['src/main.py',{path:'Dockerfile'},'Dockerfile',{path:'k8s/deployment.yaml'}]);
  assert.deepEqual(configurationPaths(paths,'Docker'),['Dockerfile']);assert.deepEqual(configurationPaths(paths,'Kubernetes'),['k8s/deployment.yaml']);assert.deepEqual(configurationPaths([],'Docker'),[]);
});
test('source links pin the analyzed SHA and encode refs and paths',()=>{
  const repo={url:'https://github.com/fixture/project',branch:'feature/x',analysisCommitSha:'a'.repeat(40)};
  assert.equal(sourceLink(repo,'src/a b.py',7),`https://github.com/fixture/project/blob/${'a'.repeat(40)}/src/a%20b.py#L7`);
  assert.equal(sourceLink({...repo,analysisCommitSha:''},'README.md'), 'https://github.com/fixture/project/blob/feature%2Fx/README.md');
});
test('RCA selection never joins another attempt or substitutes a report',()=>{
  const reports=[{id:'one',run_id:9,attempt:1},{id:'two',run_id:9,attempt:2},{id:'other',run_id:10,attempt:1}];
  assert.deepEqual(matchingReports(reports,{run_id:9,attempt:2}),[reports[1]]);assert.deepEqual(matchingReports(reports,{run_id:9,attempt:3}),[]);
});
test('citation anchors do not collide between reports or duplicate evidence IDs',()=>{
  assert.notEqual(evidenceAnchor('r1','job:1',0),evidenceAnchor('r2','job:1',0));assert.notEqual(evidenceAnchor('r1','job:1',0),evidenceAnchor('r1','job:1',1));
});
test('palette filters actual destinations rather than ignoring typed text',()=>{
  const routes=[{label:'Repository',hint:'Source files'},{label:'AI Intelligence',hint:'Root causes'}];assert.deepEqual(navigationMatches(routes,'root'),[routes[1]]);assert.deepEqual(navigationMatches(routes,'unknown'),[]);
});
test('report exports require analysis and exclude admin/component state',()=>{
  assert.throws(()=>exportRepository({repository:{name:'x'}}),/Complete/);
  const output=exportRepository({repository:{name:'fixture',analysisCommitSha:'a'},analysis:{overall:0,issues:[]},adminToken:'do-not-export',headers:{authorization:'do-not-export'}});
  assert.equal(output.health.overall,0);assert.equal(output.provenance.runtimeTelemetry,false);assert.ok(!JSON.stringify(output).includes('do-not-export'));
});
test('incomplete repository responses cannot become connected state',()=>{
  assert.throws(()=>validateRepositoryResponse({status:'SUCCESS',repository:{name:'missing-url'}}),/incomplete/);assert.throws(()=>validateRepositoryResponse({status:'FAILED'}),/incomplete/);
});
test('invalid list contracts and attempt identities surface errors instead of crashing views',()=>{
  assert.throws(()=>validateRepositoryResponse({status:'SUCCESS',repository:{name:'x',url:'https://github.com/o/r'},files:{}}),/invalid/);
  const data={repository:'o/r',runs:[],reports:[],predictions:[],model_versions:[]};
  assert.equal(validateIntelligenceResponse(data,'o/r'),data);
  assert.throws(()=>validateIntelligenceResponse(data,'other/repo'),/different/);
  assert.throws(()=>validateIntelligenceResponse({...data,runs:{}},'o/r'),/invalid/);
  assert.throws(()=>validateIntelligenceResponse({...data,runs:[{run_id:1,attempt:0}]},'o/r'),/identity/);
});
test('GitHub canonical repository casing matches the normalized API identity without accepting another repository',()=>{
  const data={repository:'saksham-1326/cloud-byte-xl-project',runs:[],reports:[],predictions:[],model_versions:[]};
  assert.equal(validateIntelligenceResponse(data,'saksham-1326/Cloud-Byte-XL-Project'),data);
  assert.equal(data.repository,'saksham-1326/cloud-byte-xl-project');
  assert.throws(()=>validateIntelligenceResponse(data,'saksham-1326/different-project'),/different repository/);
});
