"""Literal CI observations with source IDs, never test-case labels or diagnoses.

Echoed scripts describe configured commands, not proof that every command ran.
Only diagnostic output establishes compiler/dependency/test errors. These bounded
pattern checks are evidence guards, not a general natural-language entailment model.
"""
import re


COMPILER = re.compile(r'\b(?:SyntaxError|IndentationError|TabError)\b|\b(?:fatal )?error:\s*(?:expected|undefined reference|cannot find symbol|.*undeclared)|\bcompilation (?:failed|terminated)\b', re.I)
DEPENDENCY = re.compile(r'ModuleNotFoundError|ImportError:\s*(?:No module named|cannot import)|No module named|Could not find a version that satisfies|No matching distribution found', re.I)
TEST_ERROR = re.compile(r'AssertionError|={2,}\s*FAILURES|\bFAILED\s+\S*test\S*', re.I)
NETWORK = re.compile(r'Connection refused|Could not resolve host|timed out|ENOTFOUND|ECONNRESET', re.I)
DOCKER_BUILD = re.compile(r'failed to solve|Dockerfile.*(?:parse|error)|docker build.*failed', re.I)
DOCKER_ERROR = re.compile(r'Error response from daemon|No such container|failed to solve|Dockerfile.*(?:parse|error)|docker.*(?:error|failed)', re.I)
HTTP = re.compile(r'(?:HTTP(?:/\d(?:\.\d)?)?(?:\s+status(?:\s+code)?)?\s*[:=]?\s*|returned error:\s*)([45]\d\d)\b', re.I)
EXIT_CODE = re.compile(r'Process completed with exit code (\d+)\b', re.I)
SUMMARY = re.compile(r'\b(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b', re.I)


def summary_counts(text):
    # "HTTP 404 error" is a status code, never 404 pytest errors.
    http_numbers={match.start(1) for match in HTTP.finditer(text)}
    return [(match[1],match[2]) for match in SUMMARY.finditer(text) if match.start() not in http_numbers]


def body(text):
    """Drop only a timestamp prefix, preserving source text elsewhere."""
    return re.sub(r'^\d{4}-\d\d-\d\dT\S+\s*', '', text).strip()


def observations(items):
    facts={key:[] for key in ('commands','exit_codes','explicit_exit_commands','pytest_summaries',
                              'compiler_errors','dependency_errors','test_errors','http_errors',
                              'docker_errors','docker_build_errors','network_errors','shells','tolerated_failure_commands')}
    script=False
    conditional_depth=0
    for item in items:
        text=body(item['text'])
        ref={'evidence_ref':item['id'],'text':text}
        if text.startswith('##[group]Run '):
            script=True
            text=text[len('##[group]Run '):]
        elif text.startswith('shell:'):
            facts['shells'].append(ref)
            script=False
        elif text.startswith('##[endgroup]'):
            script=False
        if re.match(r'(?:if\b|for\b|while\b|case\b)',text):conditional_depth+=1
        if re.match(r'(?:fi\b|done\b|esac\b)',text):conditional_depth=max(0,conditional_depth-1)
        if script or re.match(r'(?:python(?:\d(?:\.\d)?)?\s|pytest\s|curl\s|docker\s|pip\s|gcc\s|exit\s)',text):
            if text and not text.startswith(('##[','env:')):
                facts['commands'].append({**ref,'command':text,'execution_status':'script_echo_not_execution_proof'})
                if re.search(r'\|\|\s*(?:true|:)|\bset\s+\+e\b',text):facts['tolerated_failure_commands'].append(ref)
        explicit=re.fullmatch(r'exit\s+([1-9]\d*)(?:\s*#.*)?',text)
        if explicit:
            facts['explicit_exit_commands'].append({**ref,'code':int(explicit[1]),'unconditional_in_visible_script':conditional_depth==0})
        match=EXIT_CODE.search(text)
        if match:facts['exit_codes'].append({**ref,'code':int(match[1])})
        command_echo=item.get('kind')=='command_script' or bool(re.match(r'(?:echo |printf |python\S*\s|pip\s|curl\s|docker\s|gcc\s)',text))
        counts=summary_counts(text)
        if counts and not command_echo:
            facts['pytest_summaries'].append({**ref,'counts':{name.lower():int(count) for count,name in counts}})
        # Command names (e.g. py_compile, pip install) are not error diagnostics.
        for key,pattern in [('compiler_errors',COMPILER),('dependency_errors',DEPENDENCY),
                            ('test_errors',TEST_ERROR),('docker_errors',DOCKER_ERROR),
                            ('docker_build_errors',DOCKER_BUILD),('network_errors',NETWORK)]:
            if pattern.search(text) and not command_echo:facts[key].append(ref)
        match=HTTP.search(text)
        if match and not command_echo:facts['http_errors'].append({**ref,'code':int(match[1])})
    return facts


def passing_tests(facts):
    summaries=facts['pytest_summaries']
    return bool(any(item['counts'].get('passed',0)>0 for item in summaries)
                and not any(item['counts'].get('failed',0) or item['counts'].get('error',0)
                            or item['counts'].get('errors',0) for item in summaries)
                and not facts['test_errors'])


def intentional_exit(facts):
    return bool(any(item['unconditional_in_visible_script'] for item in facts['explicit_exit_commands'])
                and not any(facts[key] for key in ('compiler_errors','dependency_errors','test_errors',
                                                  'http_errors','network_errors','docker_build_errors'))
                and not any(item['counts'].get('failed',0) or item['counts'].get('errors',0)
                            for item in facts['pytest_summaries']))


def support(category,facts,text):
    """Require the cited primary content to contain the category's indicators."""
    if category!='insufficient_evidence' and ambiguous_errors(facts):return False
    requirements={
        'intentional_workflow_termination':lambda:intentional_exit(facts),
        'compilation_error':lambda:bool(facts['compiler_errors']),
        'dependency_error':lambda:bool(facts['dependency_errors']),
        'unit_test_failure':lambda:bool(facts['test_errors'] or any(
            item['counts'].get('failed',0) or item['counts'].get('error',0) or item['counts'].get('errors',0)
            for item in facts['pytest_summaries'])),
        'network_service_failure':lambda:bool(facts['http_errors'] or facts['network_errors']),
        'docker_build_failure':lambda:bool(facts['docker_build_errors']),
        'kubernetes_configuration_error':lambda:bool(re.search(r'error validating|unable to recognize.*yaml',text,re.I)),
        'ci_workflow_misconfiguration':lambda:bool(re.search(r'command not found|not recognized as.*command',text,re.I)),
        'missing_environment_variable':lambda:bool(re.search(r'missing.*environment|required.*environment|KeyError.*(?:ENV|KEY|TOKEN|DATABASE)',text,re.I)),
        'authentication_permission_failure':lambda:bool(re.search(r'401 Unauthorized|403 Forbidden|permission denied|authentication failed',text,re.I)),
        'insufficient_evidence':lambda:True,
    }
    return requirements.get(category,lambda:False)()


def ambiguous_errors(facts):
    return bool(facts['tolerated_failure_commands'] and facts['explicit_exit_commands']
                and any(facts[key] for key in ('compiler_errors','dependency_errors','test_errors','http_errors')))


def positive_claim(text,pattern):
    """Recognize a limited set of affirmative assertions, allowing explicit negation."""
    for sentence in re.split(r'[.;\n]',text):
        for match in re.finditer(pattern,sentence,re.I):
            prefix=sentence[max(0,match.start()-60):match.start()]
            if not re.search(r'\b(?:no|not|without|rather than|no evidence of)\b',prefix,re.I):
                return True
    return False


def validate_claims(result,primary,cited,secondary):
    """Reject unsupported claims even if category=unknown or citations exist."""
    facts=observations(primary)
    cited_facts=observations(cited)
    text=' '.join(result[key] for key in ('primary_cause','explanation','recommended_fix'))
    if not support(result['category'],cited_facts,'\n'.join(item['text'] for item in cited)):
        raise ValueError('RCA category is unsupported by its cited primary content.')
    compiler_claim=r'(?:compil(?:ation|er)|syntax check|py_compile).{0,45}(?:failed|error)|(?:fix|correct|resolve).{0,25}syntax errors?|syntax errors? (?:caused|in)'
    dependency_claim=r'(?:missing|uninstalled|unavailable) (?:Python |required )?(?:dependenc\w*|packages?|modules?)|(?:dependenc\w*|packages?|modules?) (?:is |are )?(?:missing|uninstalled|unavailable)|(?:install|add).{0,30}(?:missing dependenc\w*|missing modules?)'
    test_claim=r'(?:pytest|(?:unit |python )?tests?)\s+(?:(?:has|have|had|was|were)\s+)?failed|failing (?:unit )?tests?|test failures?'
    if positive_claim(text,compiler_claim) and not cited_facts['compiler_errors']:
        raise ValueError('RCA contains an unsupported compilation or syntax claim.')
    if positive_claim(text,dependency_claim) and not cited_facts['dependency_errors']:
        raise ValueError('RCA contains an unsupported dependency claim.')
    if passing_tests(facts) and positive_claim(text,test_claim):
        raise ValueError('RCA incorrectly claims that passing tests failed.')
    if any(int(code) not in {item['code'] for item in cited_facts['http_errors']} for code in HTTP.findall(text)):
        raise ValueError('RCA contains an HTTP code unsupported by the cited content.')
    known_exit_codes={item['code'] for key in ('exit_codes','explicit_exit_commands') for item in cited_facts[key]}
    if any(int(code) not in known_exit_codes for code in re.findall(r'\bexit\s+(?:code\s+)?(\d+)\b',text,re.I)):
        raise ValueError('RCA contains an exit code unsupported by the cited content.')
    known_summaries={(name,count) for item in cited_facts['pytest_summaries'] for name,count in item['counts'].items()}
    if any((name.lower(),int(count)) not in known_summaries for count,name in summary_counts(text)):
        raise ValueError('RCA contains a test summary unsupported by the cited content.')
    if result['category']=='insufficient_evidence' and result['uncertainty']!='high':
        raise ValueError('An insufficient-evidence diagnosis must declare high uncertainty.')
    if 'secondary_evidence_refs' in result:
        secondary_ids={item['id'] for item in secondary}
        if any(ref not in secondary_ids for ref in result['secondary_evidence_refs']):
            raise ValueError('RCA contains an unsupported secondary evidence citation.')
        if secondary and not result['secondary_evidence_refs']:
            raise ValueError('RCA omitted available secondary failure evidence.')
        secondary_cited=[item for item in secondary if item['id'] in result['secondary_evidence_refs']]
        secondary_text='\n'.join(item['text'] for item in secondary_cited)
        explanation=result.get('secondary_explanation','')
        if re.search(r'docker|container',explanation,re.I) and not DOCKER_ERROR.search(secondary_text):
            raise ValueError('RCA secondary Docker claim lacks supporting evidence.')
        if any(code not in HTTP.findall(secondary_text) for code in HTTP.findall(explanation)):
            raise ValueError('RCA secondary HTTP code lacks supporting evidence.')
        for key,pattern in [('compiler_errors',compiler_claim),('dependency_errors',dependency_claim)]:
            if positive_claim(explanation,pattern) and not observations(secondary_cited)[key]:
                raise ValueError('RCA secondary claim lacks explicit diagnostic evidence.')
