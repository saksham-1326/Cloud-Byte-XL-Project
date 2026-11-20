"""Optional authenticated CI notification; no response bodies or secrets logged."""
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def main():
    url = os.getenv('CI_STATUS_URL', '').strip()
    if not url:
        print('CI callback not configured; notification skipped.')
        return 0
    try:
        target = urlsplit(url)
    except ValueError:
        print('::warning::Invalid CI callback URL configuration.')
        return 1
    token = os.getenv('CI_STATUS_TOKEN', '')
    if (target.scheme != 'https' or not target.hostname or target.username
            or target.password or target.fragment or target.query
            or target.path != '/api/ci/status' or not token):
        print('::warning::CI callback requires HTTPS /api/ci/status and CI_STATUS_TOKEN.')
        return 1
    passed = lambda key: 'PASSED' if os.getenv(key) == 'success' else 'FAILED_OR_SKIPPED'
    payload = dict(status='SUCCESS' if os.getenv('PIPELINE_STATUS') == 'success' else 'FAILURE',
                   build=passed('SYNTAX_OUTCOME'), tests=passed('TEST_OUTCOME'),
                   docker=passed('DOCKER_OUTCOME'), workflow='Cloud-ByteXL CI')
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=15) as response:
            if not 200 <= response.status < 300:
                print(f'::warning::CI callback returned HTTP {response.status}.')
                return 1
        print('CI status delivered to Flask.')
        return 0
    except urllib.error.HTTPError as error:
        print(f'::warning::CI callback returned HTTP {error.code}.')
    except (urllib.error.URLError, OSError, ValueError):
        print('::warning::CI callback delivery failed (network, TLS, or configuration).')
    return 1


if __name__ == '__main__':
    sys.exit(main())
