"""Read-only, secret-safe project integration audit."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app import get_db_connection
from backend.ai_intelligence.github import ActionsClient

client = ActionsClient()
repo = 'saksham-1326/cloud-byte-xl-project'
runs = client.runs(repo)
summary = {"repository": repo, "runs": len(runs), "outcomes": {}, "run21": []}
for run in runs:
    key = run.get('conclusion') or run['status']
    summary['outcomes'][key] = summary['outcomes'].get(key, 0) + 1
    if run.get('run_number') == 21:
        jobs = client.jobs(repo, run['id'], run.get('run_attempt', 1))
        summary['run21'].append({"id": run['id'], "attempt": run.get('run_attempt',1), "title":run['display_title'], "conclusion":run['conclusion'], "jobs":[{"name":j['name'],"id":j['id'],"steps":[{"name":s['name'],"conclusion":s['conclusion'],"number":s['number']} for s in j.get('steps',[])]} for j in jobs]})
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT 1');summary['postgresql'] = cur.fetchone()[0] == 1
Path('backend/ai_audit.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
