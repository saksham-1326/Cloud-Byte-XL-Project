"""Independent ground-truth RCA regression evaluation, not model self-confidence."""
import hashlib
import json
from pathlib import Path
from .rca import analyze, ANSI


def evaluate_cases(cases):
    results=[]
    for case in cases:
        report=analyze(case['jobs'])
        expected=case['expected']
        sources={f"job:{job['job_id']}:line:{number}":ANSI.sub('',line)[:2000] for job in case['jobs'] for number,line in enumerate((job.get('log_text') or '').splitlines(),1)}
        citations=all(sources.get(item['id'])==item['text'] for item in report['evidence'])
        required=set(expected.get('required_lines',[])).issubset({item['line'] for item in report['evidence']})
        text=(report['primary_cause']+' '+report['explanation']).lower()
        unsupported=not citations or any(claim.lower() in text for claim in expected.get('forbidden_claims',[]))
        results.append({'case':case['name'],'source':case['source'],'category_correct':report['category']==expected['category'],
                        'step_correct':report['failed_step']==expected['step'],'evidence_correct':citations and required,
                        'fix_correct':all(word.lower() in report['recommended_fix'].lower() for word in expected['fix_keywords']),
                        'unsupported_claims':unsupported})
    count=len(results)
    return {'engine':'evidence_rules','cases':results,'case_count':count,'real_log_cases':sum(c['source']=='real_github_log' for c in cases),
            'metrics':{field:sum(bool(r[field]) for r in results)/count if count else None for field in ['category_correct','step_correct','evidence_correct','fix_correct','unsupported_claims']},
            'limitation':'Controlled regression checks, not held-out LLM accuracy. Unsupported-claim checks cover exact citations and predefined forbidden assertions; semantic verification still requires humans.'}


def benchmark():
    fixture=Path(__file__).parents[1]/'tests'/'fixtures'/'run21_real.json'
    real=json.loads(fixture.read_text())
    cases=[{'name':'GitHub run #21','source':'real_github_log','jobs':real['jobs'],'expected':{'category':'intentional_workflow_termination','step':'Run tests','required_lines':[204,222,223],'fix_keywords':['remove','failure command'],'forbidden_claims':['pytest failed','unit tests failed']}}]
    controlled=[('Failed assertion','AssertionError: expected 1 got 2','unit_test_failure',['assertion']),('Missing dependency','ModuleNotFoundError: No module named flask','dependency_error',['dependency']),('Invalid Dockerfile','Dockerfile parse error: unknown instruction','docker_build_failure',['dockerfile']),('Incorrect command','toolxyz: command not found','ci_workflow_misconfiguration',['command']),('Missing environment','missing required environment variable APP_CONFIG','missing_environment_variable',['environment'])]
    for name,text,category,fix in controlled:
        jobs=[{'job_id':1,'payload':{'name':'controlled','steps':[{'name':name,'number':1,'conclusion':'failure','started_at':'2025-01-01T00:00:00Z','completed_at':'2025-01-01T00:00:05Z'}]},'log_text':'2025-01-01T00:00:01Z '+text}]
        cases.append({'name':name,'source':'synthetic_controlled_fixture','jobs':jobs,'expected':{'category':category,'step':name,'required_lines':[1],'fix_keywords':fix}})
    result=evaluate_cases(cases)
    result['source_sha256']=hashlib.sha256(Path(__file__).with_name('rca.py').read_bytes()).hexdigest()
    result['fixture_sha256']=hashlib.sha256(fixture.read_bytes()).hexdigest()
    output=Path(__file__).parents[1]/'reports'/'rca_regression.json';output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    print(json.dumps(benchmark(),indent=2))
