"""Safe test defaults, before application imports; AI HTTP calls must be mocked."""
import os
import urllib.request

import pytest

os.environ['PYTHON_DOTENV_DISABLED'] = '1'
for key, value in {
    'DB_HOST': '127.0.0.1', 'DB_PORT': '55439',
    'DB_NAME': 'cloud_bytexl_ci_test', 'DB_USER': 'cloud_bytexl_ci',
    'DB_PASSWORD': 'isolated-ci-only', 'RCA_PROVIDER': 'none',
    'OPENAI_API_KEY': '', 'GEMINI_API_KEY': '', 'GITHUB_TOKEN': '',
    'AI_ADMIN_TOKEN': '', 'AI_ALLOWED_REPOSITORIES': '', 'CI_STATUS_TOKEN': '',
    'CI_ALLOWED_REPOSITORIES': '', 'CI_CALLBACK_ENABLED': '0',
    'CI_CALLBACK_TEST_LOOPBACK': '0',
}.items():
    os.environ.setdefault(key, value)

if os.getenv('AI_TEST_DATABASE') == '1' and (
    os.environ['DB_NAME'] != 'cloud_bytexl_ci_test'
    or os.environ['DB_USER'] != 'cloud_bytexl_ci'
    or os.environ['DB_HOST'] not in {'127.0.0.1', 'localhost'}
):
    raise pytest.UsageError('Database tests require the isolated local CI database and role.')


@pytest.fixture(autouse=True)
def no_external_http(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError('Tests must mock HTTP; live API calls are disabled.')
    monkeypatch.setattr(urllib.request, 'urlopen', blocked)
    monkeypatch.setattr(urllib.request.OpenerDirector, 'open', blocked)
