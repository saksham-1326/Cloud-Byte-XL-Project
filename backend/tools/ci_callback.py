"""Durable CI sender. Disabled by default; credentials never enter diagnostics."""
import json
import hashlib
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.ci_callbacks import CallbackError, validate_payload


def payload_from_environment():
    stage = lambda key: {'success': 'PASSED', 'failure': 'FAILED',
                        'cancelled': 'CANCELLED', 'skipped': 'SKIPPED'}.get(os.getenv(key), 'SKIPPED')
    repository = os.getenv('GITHUB_REPOSITORY', '').lower()
    run_id = int(os.getenv('GITHUB_RUN_ID', '0'))
    attempt = int(os.getenv('GITHUB_RUN_ATTEMPT', '0'))
    # Stable across transport retries, unique across repository/run/attempt.
    delivery_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f'cloud-bytexl-ci:{repository}:{run_id}:{attempt}'))
    status = {'success': 'SUCCESS', 'failure': 'FAILURE', 'cancelled': 'CANCELLED'}.get(os.getenv('PIPELINE_STATUS'))
    return validate_payload(dict(repository=repository, run_id=run_id, attempt=attempt,
        commit_sha=os.getenv('GITHUB_SHA', ''), delivery_id=delivery_id,
        workflow=os.getenv('GITHUB_WORKFLOW', ''), status=status,
        build=stage('SYNTAX_OUTCOME'), tests=stage('TEST_OUTCOME'), docker=stage('DOCKER_OUTCOME')))


def valid_acknowledgment(body, payload):
    if not isinstance(body, dict) or body.get('status') != 'SUCCESS' or body.get('persisted') is not True:
        return False
    if type(body.get('deployment_id')) is not int or body['deployment_id'] <= 0:
        return False
    if type(body.get('duplicate')) is not bool:
        return False
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if body.get('payload_sha256') != digest:
        return False
    try:
        if not isinstance(body.get('receipt_id'), str): return False
        uuid.UUID(body['receipt_id'])
    except ValueError:
        return False
    return all(type(body.get(key)) is type(payload[key]) and body[key] == payload[key]
        for key in ['delivery_id', 'repository', 'run_id', 'attempt', 'commit_sha'])


def main():
    if os.getenv('CI_CALLBACK_ENABLED', '0') != '1':
        print('Durable CI callback delivery disabled; notification skipped.')
        return 0
    url = os.getenv('CI_STATUS_URL', '').strip()
    token = os.getenv('CI_STATUS_TOKEN', '')
    try:
        target = urlsplit(url)
        # Explicit test-only HTTP transport is restricted to literal loopback and
        # the disposable CI database. It never enables a public HTTP callback.
        loopback_test = (os.getenv('CI_CALLBACK_TEST_LOOPBACK') == '1'
            and os.getenv('PYTHON_DOTENV_DISABLED') == '1'
            and os.getenv('AI_TEST_DATABASE') == '1'
            and os.getenv('DB_NAME') == 'cloud_bytexl_ci_test'
            and os.getenv('DB_USER') == 'cloud_bytexl_ci'
            and os.getenv('DB_HOST') == '127.0.0.1'
            and target.scheme == 'http' and target.hostname == '127.0.0.1')
        if ((target.scheme != 'https' and not loopback_test) or not target.hostname
                or target.username or target.password or target.fragment or target.query
                or target.path != '/api/ci/v1/status' or not token):
            raise ValueError()
        payload = payload_from_environment()
        request = urllib.request.Request(url, data=json.dumps(payload).encode(), method='POST',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    except (ValueError, CallbackError):
        print('::warning::Invalid durable callback URL, authentication, or execution metadata.')
        return 1

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    try:
        # Ignore ambient HTTP proxies: authenticated callbacks go only to the
        # configured destination, with normal HTTPS certificate verification.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=15) as response:
            if not 200 <= response.status < 300:
                print(f'::warning::CI callback returned HTTP {response.status}.')
                return 1
            raw = response.read(16385)
            if len(raw) > 16384 or not valid_acknowledgment(json.loads(raw), payload):
                print('::warning::Callback did not acknowledge matching persisted data.')
                return 1
        print('Durable CI callback persistence acknowledged.')
        return 0
    except urllib.error.HTTPError as error:
        print(f'::warning::CI callback returned HTTP {error.code}; persistence was not acknowledged.')
    except (urllib.error.URLError, OSError, ValueError):
        print('::warning::CI callback persistence was not acknowledged (transport or response failure).')
    return 1


if __name__ == '__main__':
    sys.exit(main())
