"""Real Flask contracts; GitHub/provider transport is offline and fixture-labeled."""
import base64
import importlib
import os
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from backend.app import app, get_db_connection
from backend.ai_intelligence.migrations import migrate
from backend.ai_intelligence.store import Store
from backend.ai_intelligence.ml import FEATURE_VERSION


def test_repository_response_matches_dashboard_contract_and_discloses_failed_database_save(monkeypatch):
    module=importlib.import_module('backend.app')
    sha='a'*40
    responses={
        '/repos/fixture/repository':dict(id=1,name='repository',full_name='fixture/repository',
            html_url='https://github.com/fixture/repository',default_branch='main',owner={'login':'fixture'}),
        '/repos/fixture/repository/commits/main':{'sha':sha},
        '/repos/fixture/repository/languages':{'Python':1},
        f'/repos/fixture/repository/git/trees/{sha}?recursive=1':{'tree':[],'truncated':False},
        '/repos/fixture/repository/commits?per_page=10':[],
        '/repos/fixture/repository/contributors?per_page=10':[],
    }
    monkeypatch.setattr(module,'github_request',lambda path:responses[path])
    def no_legacy_database(_repository):raise RuntimeError('private fixture detail')
    monkeypatch.setattr(module,'save_github_repository',no_legacy_database)
    result=app.test_client().post('/api/github/repository',json={'url':'https://github.com/fixture/repository'})
    assert result.status_code==200 and result.json['status']=='SUCCESS'
    assert result.json['repository']['analysisCommitSha']==sha
    assert all(key in result.json for key in ['files','commits','contributors','languages','analysis'])
    assert 'PostgreSQL' in result.json['databaseWarning']
    assert 'private fixture detail' not in result.get_data(as_text=True)


@pytest.mark.parametrize('payload', [[], {'url':'https://github.com/fixture/repository','path':42},
                                    {'url':'https://github.com/fixture/repository','path':' '},
                                    {'url':'https://github.com/fixture/repository','path':'app.py','branch':[] }])
def test_file_preview_invalid_contract_is_400_not_500(payload):
    result=app.test_client().post('/api/github/file',json=payload)
    assert result.status_code==400 and result.json['status']=='FAILED'


def test_file_preview_honors_exact_analysis_sha(monkeypatch):
    module=importlib.import_module('backend.app');calls=[];sha='b'*40
    def github(path):
        calls.append(path)
        return {'default_branch':'main'} if path=='/repos/fixture/repository' else {
            'type':'file','content':base64.b64encode(b'# Controlled source contract fixture').decode()}
    monkeypatch.setattr(module,'github_request',github)
    result=app.test_client().post('/api/github/file',json={
        'url':'https://github.com/fixture/repository','path':'app.py','branch':sha})
    assert result.status_code==200
    assert calls[-1].endswith('app.py?ref='+sha)
    assert 'Controlled source contract fixture' in result.json['content']


@pytest.mark.skipif(os.getenv('AI_TEST_DATABASE')!='1',reason='Isolated PostgreSQL opt-in required')
def test_ai_overview_runs_and_rca_match_frontend_contract_from_postgresql(monkeypatch):
    migrate(get_db_connection)
    store=Store(get_db_connection);repo='delivery-fixture/'+uuid.uuid4().hex
    now=datetime.now(timezone.utc);version=str(uuid.uuid4())
    monkeypatch.setenv('RCA_PROVIDER','none');monkeypatch.setenv('AI_ALLOWED_REPOSITORIES',repo)
    monkeypatch.delenv('AI_ADMIN_TOKEN',raising=False)
    try:
        run=dict(id=1,run_attempt=1,run_number=1,workflow_id=1,head_sha='c'*40,
                 created_at=(now-timedelta(minutes=2)).isoformat(),run_started_at=(now-timedelta(minutes=1)).isoformat(),
                 status='completed',conclusion='failure',name='Controlled API contract fixture',
                 html_url='https://github.com/'+repo+'/actions/runs/1')
        store.save_run(repo,run,[dict(id=2,name='test',status='completed',conclusion='failure',
            started_at=(now-timedelta(minutes=1)).isoformat(),completed_at=now.isoformat(),steps=[])])
        store.model(repo,version,{'status':'insufficient_data','feature_version':FEATURE_VERSION,
            'dataset_size':1,'reason':'Controlled contract fixture: no fitted model'})
        report=store.save_report(repo,1,1,dict(model_version='rules-v1',engine='evidence_rules',
            category='insufficient_evidence',primary_cause='Controlled fixture: no diagnostic logs',
            uncertainty='high',evidence=[],recommended_fix='Retrieve original job logs.'))
        client=app.test_client()
        response=client.get('/api/ai/v1/overview',query_string={'repository':repo})
        assert response.status_code==200
        data=response.json['data']
        assert data['run_count']==1 and data['attempt_count']==1
        assert data['runs'][0]['run_id']==1 and data['runs'][0]['attempt']==1
        assert data['model']['status']=='insufficient_data'
        assert data['predictions']==[] and data['evaluation']['live_metrics'] is None
        assert data['reports'][0]['id']==report and data['reports'][0]['verification_status']=='unverified'
        assert data['reports'][0]['report']['engine']=='evidence_rules'
        assert data['rca_provider']['provider']=='none'
        assert client.get('/api/ai/v1/runs',query_string={'repository':repo}).json['data'][0]['run_id']==1
        assert client.get('/api/ai/v1/rca',query_string={'repository':repo}).json['data'][0]['id']==report
    finally:
        store.query('DELETE FROM ai_runs WHERE repository=%s',(repo,))
        store.query('DELETE FROM ai_models WHERE repository=%s',(repo,))
