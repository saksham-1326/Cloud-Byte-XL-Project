"""Bounded, read-only GitHub Actions client. No user-supplied fetch URLs."""
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request


class GitHubError(RuntimeError):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def repository_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ValueError("Use a repository full name: owner/repository.")
    return value.lower()


def redact(text):
    text = str(text)
    for name, value in os.environ.items():
        if any(word in name.upper() for word in ("TOKEN", "PASSWORD", "SECRET", "API_KEY")) and len(value) >= 5:
            text = text.replace(value, "[REDACTED]")
    text = re.sub(r"(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{12,}|AKIA[A-Z0-9]{16})", "[REDACTED]", text)
    text = re.sub(r"""(?i)(["']?[\w.-]*(?:password|passwd|secret|token|api[_-]?key)[\w.-]*["']?\s*[:=]\s*)(["'])(?:\\.|(?!\2)[^\\\r\n])*\2""", r'\1"[REDACTED]"', text)
    text = re.sub(r"(?i)(authorization\s*[:=]\s*(?:bearer|basic)\s+)\S+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(\b(?:[\w.-]*(?:password|passwd|secret|token|api[_-]?key)[\w.-]*)\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]", text)
    text = re.sub(r"((?:https?|postgres(?:ql)?|mysql|redis)://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED JWT]", text)
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----", "[REDACTED PRIVATE KEY]", text)
    return text


def scrub(value):
    if isinstance(value,str):return redact(value)
    if isinstance(value,list):return [scrub(item) for item in value]
    if isinstance(value,dict):
        return {key:('[REDACTED]' if re.search(r'password|passwd|secret|token|api[_-]?key',str(key),re.I) else scrub(item)) for key,item in value.items()}
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class ActionsClient:
    def __init__(self, token=None, opener=None):
        self.token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        self.opener = opener or urllib.request.build_opener(NoRedirect())

    def request(self, path, binary=False):
        if not path.startswith("/repos/") or ".." in path or "://" in path:
            raise ValueError("Invalid GitHub API path.")
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Cloud-ByteXL-AI", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request("https://api.github.com" + path, headers=headers)
        try:
            with self.opener.open(req, timeout=25) as response:
                body = response.read(5_000_001)
                if len(body) > 5_000_000:
                    raise GitHubError("GitHub response exceeds the ingestion size limit.")
                return (body if binary else json.loads(body)), response.headers
        except urllib.error.HTTPError as error:
            if error.code in (301, 302, 307):
                if not binary:
                    raise GitHubError("Repository redirect encountered; use its canonical full name.")
                target = error.headers.get("Location", "")
                parsed = urllib.parse.urlparse(target)
                allowed = (".blob.core.windows.net", ".actions.githubusercontent.com", ".githubusercontent.com")
                if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(allowed):
                    raise GitHubError("Untrusted GitHub log redirect rejected.")
                # Deliberately omit Authorization on the signed, cross-origin log URL.
                with self.opener.open(urllib.request.Request(target), timeout=25) as response:
                    data = response.read(5_000_001)
                    if len(data) > 5_000_000:
                        raise GitHubError("Job log exceeds the 5 MB ingestion limit.")
                    return data, response.headers
            if error.code in (403, 429):
                retry = error.headers.get("Retry-After") or error.headers.get("X-RateLimit-Reset")
                raise GitHubError("GitHub rate/access limit reached. Retry later; check Actions read permissions." + (f" Retry reference: {retry}." if retry and retry.isdigit() else ""), 429)
            if error.code in (404, 410):
                raise GitHubError("GitHub resource/logs unavailable, expired, or inaccessible.", error.code)
            raise GitHubError(f"GitHub request failed (HTTP {error.code}).") from None
        except (urllib.error.URLError, TimeoutError):
            raise GitHubError("GitHub connection failed or timed out.") from None

    def get(self, path):
        return self.request(path)[0]

    def pages(self, path, key, max_pages=50):
        items = []
        for page in range(1, max_pages + 1):
            sep = "&" if "?" in path else "?"
            data, headers = self.request(f"{path}{sep}per_page=100&page={page}")
            batch = data[key] if key else data
            items.extend(batch)
            if 'rel="next"' not in headers.get("Link", ""):
                return items
        raise GitHubError("Pagination limit reached; narrow the sync window rather than silently truncating history.")

    def runs(self, repo):
        return self.pages(f"/repos/{repository_name(repo)}/actions/runs", "workflow_runs")

    def run(self, repo, run_id, attempt=None):
        suffix = f"/attempts/{int(attempt)}" if attempt else ""
        return self.get(f"/repos/{repository_name(repo)}/actions/runs/{int(run_id)}{suffix}")

    def jobs(self, repo, run_id, attempt):
        return self.pages(f"/repos/{repository_name(repo)}/actions/runs/{int(run_id)}/attempts/{int(attempt)}/jobs", "jobs")

    def job_log(self, repo, job_id):
        data, _ = self.request(f"/repos/{repository_name(repo)}/actions/jobs/{int(job_id)}/logs", binary=True)
        return redact(data.decode("utf-8", errors="replace"))

    def snapshot(self, repo, run):
        sha = run["head_sha"]
        commits = self.pages(f"/repos/{repository_name(repo)}/commits/{urllib.parse.quote(sha, safe='')}", "files")
        workflow_path = run.get("path", "").split("@")[0]
        config = None
        config_status = "unavailable"
        if workflow_path.startswith(".github/workflows/"):
            try:
                data = self.get(f"/repos/{repository_name(repo)}/contents/{urllib.parse.quote(workflow_path, safe='/')}?ref={urllib.parse.quote(sha, safe='')}")
                config = redact(base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")[:64000])
                config_status = "available"
            except GitHubError as error:
                if error.status not in (404, 410):
                    raise
        return {"sha": sha, "workflow_path": workflow_path, "workflow_config": config, "config_status": config_status,
                "files": [{"filename": item["filename"], "status": item.get("status"), "additions": item.get("additions", 0), "deletions": item.get("deletions", 0)} for item in commits],
                "commit": {"message": redact(run.get("head_commit", {}).get("message", ""))[:2000]},
                "historical_ref": sha}
