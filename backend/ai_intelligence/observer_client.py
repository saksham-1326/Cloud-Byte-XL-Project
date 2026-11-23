"""Budgeted GET-only observer transport; inference still uses ActionsClient APIs."""
import json
import math
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from .github import ActionsClient, repository_name
from .observation import ObservationError, aware, positive, utc
from .collector import validate_attempt


SAFE_HEADERS = ('ETag', 'Last-Modified', 'Date', 'Link', 'X-GitHub-Request-Id',
                'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset',
                'X-RateLimit-Used', 'X-RateLimit-Resource', 'Retry-After', 'X-Poll-Interval')


class ObserverClient(ActionsClient):
    """Shared budget covers discovery, retries AND all service/snapshot GETs.

    HTTP redirects and binary/log downloads are not needed by this observer.
    Conditional caching is restricted to discovery. Exact attempt reads always
    use a new unconditional GET and never reuse a queued response from cache.
    """
    def __init__(self, repo, token, ledger, budget=300, duration=900, stop=None,
                 opener=None, now=utc, monotonic=time.monotonic, wait=None,
                 jitter=None, retries=3, timeout=10):
        if not isinstance(token, str) or not token.strip():
            raise ObservationError('github_authentication_required')
        super().__init__(token=token, opener=opener)
        self.repo = repository_name(repo)
        self.ledger = ledger
        self.budget = positive(budget, 'request_budget')
        self.duration = positive(duration, 'duration')
        self.stop = stop if stop is not None else threading.Event()
        self.now = now
        self.monotonic = monotonic
        self.waiter = wait or self.stop.wait
        self.jitter = jitter or (lambda: random.uniform(0, 1))
        self.retries = positive(retries, 'retry_count')
        self.timeout = positive(timeout, 'network_timeout')
        self.cache = {}
        self.requests = sum(r['event'] == 'http_request' for r in ledger.records)
        self.retry_at=0
        self.poll_after={}
        for record in ledger.records:
            if record['event']=='http_backoff' and record['data'].get('retry_at'):
                self.retry_at=max(self.retry_at,aware(record['data']['retry_at']).timestamp())
            if record['event']=='http_response':
                self.remember_poll(record['data']['path'],record['data'].get('headers',{}),aware(record['at']).timestamp())
        sessions = [r for r in ledger.records if r['event'] == 'session']
        start = aware(sessions[0]['at']) if sessions else aware(now())
        # Restarts cannot silently renew the session's time or request budget.
        self.wall_deadline = start.timestamp()+duration
        self.deadline = monotonic()+max(0, self.wall_deadline-aware(now()).timestamp())

    def time_guard(self):
        if self.stop.is_set():
            raise ObservationError('cancelled')
        if self.monotonic() >= self.deadline or aware(self.now()).timestamp() >= self.wall_deadline:
            raise ObservationError('duration_exhausted')

    def guard(self):
        self.time_guard()
        if self.requests >= self.budget:
            raise ObservationError('request_budget_exhausted')

    def pause(self, seconds):
        remaining = min(self.deadline-self.monotonic(), self.wall_deadline-aware(self.now()).timestamp())
        if remaining <= 0:
            raise ObservationError('duration_exhausted')
        interrupted = self.waiter(min(seconds, remaining))
        if interrupted or self.stop.is_set():
            raise ObservationError('cancelled')
        self.guard()

    @staticmethod
    def headers(headers):
        return {key: headers.get(key) for key in SAFE_HEADERS if headers.get(key) is not None}

    def remember_poll(self,path,headers,at=None):
        if 'X-Poll-Interval' not in headers:
            return
        try:
            seconds=float(headers['X-Poll-Interval'])
            if not math.isfinite(seconds) or seconds<0:
                raise ValueError()
        except (ValueError,TypeError):
            raise ObservationError('invalid_poll_interval') from None
        self.poll_after[path]=max(self.poll_after.get(path,0),
                                  (at if at is not None else aware(self.now()).timestamp())+seconds)

    def _delay(self, headers, attempt, rate=False):
        delay = max(1, 2**attempt)
        if rate:
            delay = 60*(2**attempt)
        try:
            if headers.get('Retry-After') is not None:
                delay = max(delay, float(headers['Retry-After']))
            if headers.get('X-RateLimit-Remaining') == '0' and headers.get('X-RateLimit-Reset'):
                delay = max(delay, float(headers['X-RateLimit-Reset'])-aware(self.now()).timestamp())
        except (ValueError, TypeError):
            delay = max(delay, 60)
        return delay + max(0, self.jitter())

    def request(self, path, binary=False, conditional=False):
        if binary or not path.startswith(f'/repos/{self.repo}/') or '..' in path or '://' in path:
            raise ObservationError('observer_path_rejected')
        for attempt in range(int(self.retries)):
            self.guard()
            cooldown=max(self.retry_at,self.poll_after.get(path,0))-aware(self.now()).timestamp()
            if cooldown>0:
                self.pause(cooldown)
            headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Cloud-ByteXL-Observer',
                       'X-GitHub-Api-Version': '2022-11-28', 'Authorization': 'Bearer '+self.token}
            if conditional and path in self.cache:
                tag = self.cache[path][1].get('ETag')
                if tag:
                    headers['If-None-Match'] = tag
            self.requests += 1
            self.ledger.append('http_request', path=path, request_number=self.requests,
                               conditional=conditional, retry_index=attempt)
            try:
                remaining = min(self.deadline-self.monotonic(), self.wall_deadline-aware(self.now()).timestamp())
                if remaining<=0:
                    raise ObservationError('duration_exhausted')
                request = urllib.request.Request('https://api.github.com'+path, headers=headers, method='GET')
                with self.opener.open(request, timeout=max(.01, min(self.timeout, remaining))) as response:
                    chunks=[];size=0
                    read=getattr(response,'read1',response.read)
                    while True:
                        self.time_guard()
                        chunk=read(min(65536,5_000_001-size))
                        if not chunk:
                            break
                        chunks.append(chunk);size+=len(chunk)
                        if size>5_000_000:
                            raise ObservationError('response_size_exceeded')
                    body=b''.join(chunks)
                    safe = self.headers(response.headers)
                    if len(body) > 5_000_000:
                        raise ObservationError('response_size_exceeded')
                    try:
                        data = json.loads(body)
                    except (ValueError, UnicodeError):
                        raise ObservationError('invalid_github_json') from None
                self.ledger.append('http_response', path=path, status=200, headers=safe, cached=False)
                self.remember_poll(path,safe)
                if conditional:
                    self.cache[path] = (data, safe)
                return data, safe
            except urllib.error.HTTPError as error:
                safe = self.headers(error.headers)
                self.ledger.append('http_response', path=path, status=error.code, headers=safe,
                                   cached=error.code == 304)
                self.remember_poll(path,safe)
                if error.code == 304 and conditional and path in self.cache:
                    data, old = self.cache[path]
                    self.remember_poll(path,{**old,**safe})
                    return data, {**old, **safe, 'Observer-Cached': True}
                if error.code in (401, 404):
                    raise ObservationError('github_auth_or_resource_unavailable') from None
                rate = error.code == 429 or (error.code == 403 and
                       (safe.get('X-RateLimit-Remaining') == '0' or 'Retry-After' in safe))
                if error.code == 403 and not rate:
                    body = error.read(2000).lower()
                    rate = b'rate limit' in body or b'abuse' in body
                    if not rate:
                        raise ObservationError('github_permission_denied') from None
                retryable = rate or error.code in (500, 502, 503, 504)
                if not retryable:
                    raise ObservationError('github_http_error') from None
                code = 'github_rate_limited' if rate else 'github_unavailable'
                delay = self._delay(safe, attempt, rate)
            except (urllib.error.URLError, TimeoutError, OSError):
                code, delay = 'github_network_unavailable', self._delay({}, attempt)
                self.ledger.append('http_error', path=path, code=code)
            self.retry_at=aware(self.now()).timestamp()+delay
            self.ledger.append('http_backoff', reason=code, seconds=delay,
                               retry_at=datetime_from_epoch(self.retry_at))
            if attempt+1 >= self.retries:
                raise ObservationError(code)
            self.pause(delay)
        raise ObservationError('github_unavailable')

    def run(self, repo, run_id, attempt=None):
        if repository_name(repo)!=self.repo or attempt is None:
            raise ObservationError('exact_allowlisted_attempt_required')
        result=super().run(repo,run_id,attempt)
        try:
            validate_attempt(repo,run_id,attempt,result,[])
        except (ValueError,TypeError):
            raise ObservationError('github_identity_mismatch') from None
        return result

    def discover(self):
        path = f'/repos/{self.repo}/actions/runs?status=queued&per_page=100'
        found, seen = [], set()
        while path:
            if path in seen or len(seen) >= 50:
                raise ObservationError('discovery_pagination_incomplete')
            seen.add(path)
            data, headers = self.request(path, conditional=True)
            if not isinstance(data, dict) or not isinstance(data.get('workflow_runs'), list):
                raise ObservationError('invalid_discovery_response')
            found.extend(data['workflow_runs'])
            links = re.findall(r'<([^>]+)>;\s*rel="next"', headers.get('Link', ''))
            if not links:
                # Filtered Actions searches can cap at 1,000 results.
                if data.get('total_count', 0) > len(found):
                    raise ObservationError('discovery_pagination_incomplete')
                break
            target = urllib.parse.urlsplit(links[0])
            if target.scheme != 'https' or target.netloc != 'api.github.com' or target.path != f'/repos/{self.repo}/actions/runs':
                raise ObservationError('untrusted_pagination_link')
            path = target.path + ('?'+target.query if target.query else '')
        return found


def datetime_from_epoch(value):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(value,timezone.utc).isoformat()
