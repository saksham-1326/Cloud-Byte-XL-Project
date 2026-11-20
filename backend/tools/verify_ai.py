"""Live API integration check, safe summaries and versioned evaluation artifacts."""
from pathlib import Path
import json
import time
import urllib.request

BASE='http://127.0.0.1:5000/api/ai/v1'
REPO='saksham-1326/cloud-byte-xl-project'
OUT=Path('backend/reports');OUT.mkdir(exist_ok=True)

def request(path,body=None):
    headers={'Origin':'http://localhost:5173'}
    if body is not None:headers['Content-Type']='application/json'
    req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
    with urllib.request.urlopen(req,timeout=60) as response:
        assert response.headers.get('Access-Control-Allow-Origin')=='http://localhost:5173'
        return json.load(response)

def task(path,extra=None):
    submitted=request(path,{'repository':REPO,**(extra or {})})
    task_id=submitted['task_id']
    for _ in range(120):
        row=request(f'/tasks/{task_id}?repository={REPO}')['data']
        if row['status']=='failed':raise RuntimeError(row['result']['message'])
        if row['status']=='completed':return row['result']
        time.sleep(1)
    raise RuntimeError('Background job did not complete within the integration-check deadline.')

synchronization=task('/sync')
assert synchronization['stored_attempts']==28
training=task('/train')
(OUT/'model_evaluation.json').write_text(json.dumps(training,indent=2))
report=task('/rca',{'run_id':32446985157,'attempt':1})
assert report['report']['category']=='intentional_workflow_termination'
assert report['report']['secondary_errors'][0]['line']==273
(OUT/'run21_rca.json').write_text(json.dumps(report,indent=2))
rejected=task('/predictions',{'run_id':32446985157,'attempt':1})
assert rejected['status']=='skipped'
data=request('/overview?repository='+REPO)['data']
summary={'incremental_sync':synchronization,'unique_runs':data['run_count'],'attempts':data['attempt_count'],'model_status':training['status'],'dataset_size':training['dataset_size'],'test_metrics':training.get('test'),'rca_category':report['report']['category'],'rca_engine':report['report']['engine'],'provider_configured':data['rca_provider']['configured'],'completed_run_live_prediction':rejected['status'],'live_predictions':sum(p['mode']=='shadow' for p in data['predictions'])}
(OUT/'live_api_verification.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
