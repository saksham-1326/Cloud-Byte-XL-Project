"""Gemini contract checks; no live requests or credentials in tests."""
import io
import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from backend.ai_intelligence.rca import (
    GeminiProvider, OpenAIProvider, ProviderError, configured_provider,
    provider_configuration, analyze, extract_evidence, grounded_diagnosis,
    validate_diagnosis,
)
from backend.tests.test_ai_ml_rca import job_case


@pytest.fixture
def gemini(monkeypatch):
    monkeypatch.setenv('RCA_PROVIDER','gemini')
    monkeypatch.setenv('RCA_MODEL','gemini-2.5-flash')
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key')
    return GeminiProvider()


def mock_response(monkeypatch,body,requests):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return json.dumps(body).encode()
    def send(request,timeout):
        requests.append(request)
        return Response()
    monkeypatch.setattr(urllib.request,'urlopen',send)


def test_gemini_blind_request_and_valid_result(gemini,monkeypatch):
    evidence=extract_evidence(job_case('exit 1\n1 passed'))
    diagnosis=grounded_diagnosis(evidence)
    requests=[]
    mock_response(monkeypatch,{'modelVersion':'actual-model-version','responseId':'response-1',
                              'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(diagnosis)}]}}]},requests)
    assert gemini.generate(evidence,{'primary_cause':'EXPECTED_CAUSE_SENTINEL'})==diagnosis
    request=requests[0]
    payload=json.loads(request.data)
    assert json.loads(payload['contents'][0]['parts'][0]['text'])=={'evidence':evidence}
    assert 'EXPECTED_CAUSE_SENTINEL' not in request.data.decode()
    assert 'private-test-key' not in request.full_url
    assert request.get_header('X-goog-api-key')=='private-test-key'
    assert 'tools' not in payload
    assert payload['generationConfig']['candidateCount']==1
    assert gemini.last_metadata['model_version']=='actual-model-version'


@pytest.mark.parametrize('status,code',[(429,'quota_exhausted'),(400,'invalid_request'),(401,'authentication'),
                                      (403,'permission'),(404,'model_unavailable'),(503,'http_error')])
def test_gemini_errors_are_safe_no_retry_or_fallback(gemini,monkeypatch,status,code):
    calls=[]
    def fail(request,timeout):
        calls.append(request)
        raise urllib.error.HTTPError(request.full_url,status,'private-test-key',{},io.BytesIO(b'private-test-key'))
    monkeypatch.setattr(urllib.request,'urlopen',fail)
    with pytest.raises(ProviderError) as caught:
        analyze(job_case('exit 1\n1 passed'),gemini)
    assert caught.value.code==code
    assert 'private-test-key' not in str(caught.value)
    assert len(calls)==1


@pytest.mark.parametrize('body,code',[
    ({},'incomplete_output'),
    ({'candidates':[{'finishReason':'MAX_TOKENS'}]},'incomplete_output'),
    ({'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'not json'}]}}]},'parsing'),
])
def test_gemini_missing_truncated_or_invalid_output_rejected(gemini,monkeypatch,body,code):
    mock_response(monkeypatch,body,[])
    with pytest.raises(ProviderError) as caught:gemini.generate({}, {})
    assert caught.value.code==code


@pytest.mark.parametrize('model',['your_free_tier_model_id','paid-model','../../other-host'])
def test_unreviewed_models_do_not_make_requests(gemini,monkeypatch,model):
    monkeypatch.setenv('RCA_MODEL',model)
    monkeypatch.setattr(urllib.request,'urlopen',lambda *a,**k:pytest.fail('Unexpected request'))
    assert not provider_configuration()['configured']
    with pytest.raises(ProviderError):configured_provider()


def test_provider_selection_preserves_openai_and_rejects_unknown(gemini,monkeypatch):
    assert isinstance(configured_provider(),GeminiProvider)
    monkeypatch.setenv('RCA_PROVIDER','openai')
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    assert isinstance(configured_provider(),OpenAIProvider)
    monkeypatch.setenv('RCA_PROVIDER','none')
    assert configured_provider() is None
    monkeypatch.setenv('RCA_PROVIDER','typo')
    with pytest.raises(ProviderError):configured_provider()


def test_model_metadata_does_not_claim_free_quota(gemini,monkeypatch):
    mock_response(monkeypatch,{'name':'models/gemini-2.5-flash','supportedGenerationMethods':['generateContent']},[])
    result=gemini.check_model()
    assert result['free_quota']=='unconfirmed_until_generation'
    assert result['billing_tier']=='not_exposed_by_model_metadata'


def test_error_details_are_redacted(gemini,monkeypatch):
    def fail(request,timeout):
        body=json.dumps({'error':{'status':'NOT_FOUND','message':'Rejected private-test-key'}}).encode()
        raise urllib.error.HTTPError(request.full_url,404,'Not found',{},io.BytesIO(body))
    monkeypatch.setattr(urllib.request,'urlopen',fail)
    with pytest.raises(ProviderError) as caught:gemini.check_model()
    assert caught.value.details['provider_status']=='NOT_FOUND'
    assert 'private-test-key' not in json.dumps(caught.value.details)


def test_gemini_35_uses_minimal_thinking(gemini,monkeypatch):
    monkeypatch.setenv('RCA_MODEL','gemini-3.5-flash-lite')
    evidence=extract_evidence(job_case('exit 1\n1 passed'))
    diagnosis=grounded_diagnosis(evidence)
    requests=[]
    mock_response(monkeypatch,{'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(diagnosis)}]}}]},requests)
    report=analyze(job_case('exit 1\n1 passed'),gemini)
    assert report['engine']=='llm_grounded'
    assert report['verification_status']=='unverified'
    assert report['model_version']=='gemini-3.5-flash-lite'
    config=json.loads(requests[0].data)['generationConfig']
    assert config['thinkingConfig']=={'thinkingLevel':'minimal'}


@pytest.mark.parametrize('run_number',[21,13,23,27])
def test_actual_gemini_responses_replay_validation_guards(run_number):
    fixture=json.loads((Path(__file__).parent/'fixtures/gemini_live_rca_cases.json').read_text(encoding='utf-8'))
    case=next(row for row in fixture['cases'] if row['run_number']==run_number)
    anchor=grounded_diagnosis(case['evidence'])
    if case['accepted_by_guard']:
        assert validate_diagnosis(case['diagnosis'],case['evidence'],anchor)==case['diagnosis']
    else:
        with pytest.raises(ValueError,match='contradicts'):
            validate_diagnosis(case['diagnosis'],case['evidence'],anchor)
