from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from datetime import datetime
from urllib.parse import urlparse, quote
import urllib.request
import urllib.error
import json
import base64
import os
import re
import hmac
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from logging.handlers import RotatingFileHandler
import logging
import sys
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException


# Resolve configuration independently of the server working directory.
load_dotenv(Path(__file__).with_name(".env"), override=False)

app = Flask(__name__)
CORS(app, origins=[origin.strip() for origin in os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175",
).split(",") if origin.strip()])

# Detached Windows processes can have invalid stdout/stderr handles. Never
# let diagnostic output break an otherwise successful repository analysis.
log_handler = logging.StreamHandler(sys.stdout) if os.getenv('PUBLIC_DEMO_MODE')=='1' else RotatingFileHandler(
    Path(__file__).with_name("backend.log"), maxBytes=2_000_000,
    backupCount=2, encoding="utf-8",
)
log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
app.logger.handlers.clear()
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)
app.logger.propagate = False


def log_message(*parts):
    app.logger.info(" ".join(str(part) for part in parts))


@app.errorhandler(Exception)
def handle_api_error(error):
    if isinstance(error, HTTPException):
        return jsonify(status="FAILED", message=error.description), error.code
    app.logger.exception("Unhandled API request failure")
    return jsonify(status="FAILED", message="An internal server error occurred."), 500


# ============================================================
# PostgreSQL connection
# ============================================================

try:
    from .database import configuration as database_configuration, connect as database_connect
except ImportError:
    from database import configuration as database_configuration, connect as database_connect
DB_CONFIG = database_configuration()


def get_db_connection():
    return database_connect(DB_CONFIG,readonly=os.getenv('PUBLIC_DEMO_MODE')=='1')


# ============================================================
# GitHub REST API helpers
# ============================================================

GITHUB_API = "https://api.github.com"


def github_request(endpoint):
    """
    Read data from the GitHub REST API.

    Public repositories work without a token.
    If GITHUB_TOKEN is configured in the environment, it is used
    for authenticated requests and private repositories.
    """

    url = f"{GITHUB_API}{endpoint}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Cloud-ByteXL",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    github_token = os.getenv("GITHUB_TOKEN")

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ValueError(
                "GitHub repository or resource was not found. "
                "If this is a private repository, configure "
                "GITHUB_TOKEN."
            )

        if error.code == 403:
            raise ValueError(
                "GitHub API access was denied or the API rate "
                "limit was reached. Configure GITHUB_TOKEN "
                "for authenticated access."
            )

        try:
            error_body = error.read().decode("utf-8")
            error_json = json.loads(error_body)
            message = error_json.get(
                "message",
                f"HTTP {error.code}"
            )
        except Exception:
            message = f"HTTP {error.code}"

        raise ValueError(
            f"GitHub API error: {message}"
        )

    except urllib.error.URLError as error:
        raise ValueError(
            f"Could not connect to GitHub: {error.reason}"
        )


def parse_github_url(repo_url):
    """
    Convert a GitHub repository URL into owner and repository.

    Examples:
        https://github.com/owner/repository
        https://github.com/owner/repository.git
        github.com/owner/repository
    """

    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError(
            "GitHub repository URL is required."
        )

    repo_url = repo_url.strip()

    if not repo_url.startswith(("http://", "https://")):
        repo_url = "https://" + repo_url

    parsed = urlparse(repo_url)

    if parsed.netloc.lower() not in {
        "github.com",
        "www.github.com",
    }:
        raise ValueError(
            "Please enter a valid GitHub repository URL."
        )

    parts = [
        part
        for part in parsed.path.strip("/").split("/")
        if part
    ]

    if len(parts) != 2:
        raise ValueError(
            "GitHub URL must look like: "
            "https://github.com/owner/repository"
        )

    owner = parts[0]
    repository = parts[1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    if not owner or not repository:
        raise ValueError(
            "GitHub owner and repository name are required."
        )

    return owner, repository


def calculate_language_percentages(languages):
    """Convert GitHub language byte counts into percentages."""

    total = sum(
        value for value in languages.values()
        if isinstance(value, int)
    )

    if total == 0:
        return []

    result = []

    for name, byte_count in sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        result.append({
            "name": name,
            "bytes": byte_count,
            "pct": round(
                (byte_count / total) * 100,
                2,
            ),
        })

    return result


def save_github_repository(repository):
    """
    Store/update a repository in the existing repositories table.

    This uses the same repositories schema already used by the
    webhook integration: user_id, name, url, branch.
    """

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            # Reuse an integration user instead of creating a
            # new user for every repository connection.
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = %s
                """,
                ("github-integration",),
            )

            user_row = cursor.fetchone()

            if user_row:
                user_id = user_row[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO users
                        (username, email)
                    VALUES
                        (%s, %s)
                    RETURNING id
                    """,
                    (
                        "github-integration",
                        "github-integration@cloud-bytexl.local",
                    ),
                )

                user_id = cursor.fetchone()[0]

            repo_url = repository.get("url", "")
            repo_name = repository.get("name", "")
            branch = repository.get("branch", "main")

            cursor.execute(
                """
                SELECT id
                FROM repositories
                WHERE url = %s
                """,
                (repo_url,),
            )

            repository_row = cursor.fetchone()

            if repository_row:
                repository_id = repository_row[0]

                cursor.execute(
                    """
                    UPDATE repositories
                    SET
                        name = %s,
                        branch = %s
                    WHERE id = %s
                    """,
                    (
                        repo_name,
                        branch,
                        repository_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO repositories
                        (
                            user_id,
                            name,
                            url,
                            branch
                        )
                    VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    RETURNING id
                    """,
                    (
                        user_id,
                        repo_name,
                        repo_url,
                        branch,
                    ),
                )

                repository_id = cursor.fetchone()[0]

        connection.commit()

        return repository_id

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if connection:
            connection.close()


# ============================================================
# Latest GitHub webhook information
# ============================================================

latest_webhook = {
    "event": None,
    "repository": None,
    "branch": None,
    "pusher": None,
    "commits": []
}


# ============================================================
# Latest GitHub repository ingestion
# ============================================================

latest_github_repository = None


# ============================================================
# Latest CI/CD pipeline information
# ============================================================

latest_ci = {
    "status": "UNKNOWN",
    "build": "UNKNOWN",
    "tests": "UNKNOWN",
    "docker": "UNKNOWN",
    "workflow": "Cloud-ByteXL CI"
}


# ============================================================
# Helper: store deployment log
# ============================================================

def create_deployment_log(
    cursor,
    deployment_id,
    message,
    level="INFO"
):
    """
    Store a log entry for a deployment.

    This is the main Phase 7 log-collection helper.
    """

    cursor.execute(
        """
        INSERT INTO deployment_logs
            (
                deployment_id,
                log_message,
                log_level
            )
        VALUES
            (
                %s,
                %s,
                %s
            )
        """,
        (
            deployment_id,
            message,
            level
        )
    )



# ============================================================
# Lightweight real repository analysis
# ============================================================

def decode_github_file(file_data):
    content = file_data.get("content", "")
    if not content:
        return ""
    try:
        return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _raw_github_text(owner, repo, revision, path):
    """Read a text file directly from raw.githubusercontent.com.

    The repository tree is obtained from the GitHub API once. File contents are
    then read from the raw host so analysis can cover many files without burning
    through the unauthenticated GitHub API request quota.
    """
    encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
    encoded_revision = quote(revision, safe="")
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{encoded_revision}/{encoded_path}"
    headers = {"User-Agent": "Cloud-ByteXL", "Accept": "text/plain"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            raw = response.read(300_000)
            return raw.decode("utf-8", errors="ignore")
    except Exception as error:
        log_message("Raw GitHub file read warning:", path, error)
        return ""


def _line_number(content, pattern):
    import re
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(pattern, line, re.IGNORECASE):
            return i
    return 1



# ============================================================
# Deterministic repository/resource audit helpers
# ============================================================

def _file_extension(path):
    """Return a normalized file-type label from the repository path."""
    base = path.rsplit("/", 1)[-1].lower()
    if base.startswith(".") and base.count(".") == 1:
        return "[extensionless]"
    if "." not in base:
        return "[extensionless]"
    return "." + base.rsplit(".", 1)[-1]


def _line_number_for_match(content, start):
    return content[:start].count("\n") + 1


def build_resource_audit(paths, file_contents, tree_truncated=False):
    """Build an evidence-only audit.

    Important distinction:
    - File counts come from the complete GitHub tree returned to the analyzer.
    - A "cloud resource" is counted only when a concrete resource declaration is
      found in inspected file contents. SDK imports/references alone are NOT
      counted as resources.
    - Missing categories are explicitly represented as zero.
    """
    extension_counts = {}
    extension_files = {}
    for path in paths:
        ext = _file_extension(path)
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
        extension_files.setdefault(ext, []).append(path)

    def count_ext(*exts):
        return sum(extension_counts.get(e, 0) for e in exts)

    # Exact file categories based only on repository paths.
    file_categories = {
        "Python": count_ext(".py"),
        "JavaScript": count_ext(".js"),
        "JSX": count_ext(".jsx"),
        "TypeScript": count_ext(".ts"),
        "TSX": count_ext(".tsx"),
        "Java": count_ext(".java"),
        "C": count_ext(".c"),
        "C++": count_ext(".cpp", ".cc", ".cxx"),
        "C#": count_ext(".cs"),
        "Go": count_ext(".go"),
        "Rust": count_ext(".rs"),
        "PHP": count_ext(".php"),
        "Ruby": count_ext(".rb"),
        "HTML": count_ext(".html", ".htm"),
        "CSS": count_ext(".css"),
        "SCSS": count_ext(".scss"),
        "SQL": count_ext(".sql"),
        "JSON": count_ext(".json"),
        "YAML": count_ext(".yaml", ".yml"),
        "TOML": count_ext(".toml"),
        "XML": count_ext(".xml"),
        "Markdown": count_ext(".md", ".mdx"),
        "Terraform": count_ext(".tf", ".tfvars"),
        "Bicep": count_ext(".bicep"),
    }

    special_files = {
        "Dockerfile": [p for p in paths if p.lower().rsplit("/", 1)[-1] == "dockerfile"],
        "Docker Compose": [p for p in paths if p.lower().rsplit("/", 1)[-1] in {"docker-compose.yml", "docker-compose.yaml"}],
        "GitHub Actions": [p for p in paths if ".github/workflows/" in p.lower()],
        "Kubernetes/Helm": [p for p in paths if ("/k8s/" in p.lower() or "/kubernetes/" in p.lower() or "/helm/" in p.lower())],
        "Pulumi": [p for p in paths if p.lower().rsplit("/", 1)[-1] in {"pulumi.yaml", "pulumi.yml"}],
        "CDK": [p for p in paths if p.lower().rsplit("/", 1)[-1] == "cdk.json"],
        "CloudFormation/SAM": [p for p in paths if "cloudformation" in p.lower() or p.lower().rsplit("/", 1)[-1] in {"template.yaml", "template.yml"}],
    }

    resource_definitions = []
    resource_counts = {}
    resource_evidence_files = set()
    provider_evidence = {"AWS": [], "Azure": [], "GCP": []}
    sdk_evidence = {"AWS": [], "Azure": [], "GCP": []}

    def add_resource(provider, resource_type, path, line, source_kind):
        key = (provider, resource_type, path, line, source_kind)
        if key in {(r["provider"], r["type"], r["file"], r["line"], r["sourceKind"]) for r in resource_definitions}:
            return
        item = {
            "provider": provider,
            "type": resource_type,
            "name": resource_type,
            "file": path,
            "line": line,
            "sourceKind": source_kind,
        }
        resource_definitions.append(item)
        resource_counts[f"{provider}:{resource_type}"] = resource_counts.get(f"{provider}:{resource_type}", 0) + 1
        resource_evidence_files.add(path)

    # Terraform: only actual resource blocks are counted; provider SDK mentions
    # and variable names are never promoted to resources.
    for path, content in file_contents.items():
        lp = path.lower()
        if lp.endswith(".tf"):
            for match in re.finditer(r'(?m)^\s*resource\s+["\'](aws|azurerm|google)_([A-Za-z0-9_]+)["\']\s+["\']([^"\']+)["\']', content, re.I):
                provider = {"aws": "AWS", "azurerm": "Azure", "google": "GCP"}[match.group(1).lower()]
                add_resource(provider, match.group(2), path, _line_number_for_match(content, match.start()), "Terraform resource block")
                provider_evidence[provider].append(path)
            # Provider blocks are evidence of configured provider, not resources.
            for match in re.finditer(r'(?m)^\s*provider\s+["\'](aws|azurerm|google)["\']', content, re.I):
                provider = {"aws": "AWS", "azurerm": "Azure", "google": "GCP"}[match.group(1).lower()]
                provider_evidence[provider].append(path)

        # CloudFormation/SAM: count AWS:: types only when they occur inside
        # an explicit Resources section. Generic Type: fields elsewhere are
        # not treated as cloud resources.
        if lp.endswith((".yaml", ".yml")):
            resource_section = re.search(r'(?ms)^\s*Resources\s*:\s*\n(.*?)(?=^\S|\Z)', content)
            if resource_section:
                section_text = resource_section.group(1)
                section_start = resource_section.start(1)
                for match in re.finditer(r'(?m)^\s+Type\s*:\s*(AWS::[A-Za-z0-9:._/-]+)\s*$', section_text):
                    resource_type = match.group(1)
                    absolute = section_start + match.start()
                    add_resource("AWS", resource_type, path, _line_number_for_match(content, absolute), "CloudFormation/SAM resource")
                    provider_evidence["AWS"].append(path)
        elif lp.endswith(".json"):
            # JSON CloudFormation is counted only when a top-level Resources
            # object exists and contains concrete AWS:: Type declarations.
            try:
                parsed = json.loads(content)
                resources_obj = parsed.get("Resources") if isinstance(parsed, dict) else None
                if isinstance(resources_obj, dict):
                    for logical_id, definition in resources_obj.items():
                        if isinstance(definition, dict) and isinstance(definition.get("Type"), str) and definition["Type"].startswith("AWS::"):
                            resource_type = definition["Type"]
                            line = _line_number_for_match(content, content.find(logical_id)) if logical_id else 1
                            add_resource("AWS", resource_type, path, line, "CloudFormation/SAM resource")
                            provider_evidence["AWS"].append(path)
            except (ValueError, TypeError):
                pass

        # Azure Bicep: concrete resource declaration.
        if lp.endswith(".bicep"):
            for match in re.finditer(r"(?m)^\s*resource\s+['\"]?([A-Za-z0-9_.-]+)\s+['\"](Microsoft\.[^'\"]+)['\"]", content, re.I):
                resource_type = match.group(2).split("@", 1)[0]
                add_resource("Azure", resource_type, path, _line_number_for_match(content, match.start()), "Bicep resource declaration")
                provider_evidence["Azure"].append(path)

        # Kubernetes: each explicit apiVersion+kind document is a concrete
        # orchestration resource. This does not imply a cloud provider.
        if lp.endswith((".yaml", ".yml")):
            for match in re.finditer(r'(?ms)^\s*apiVersion\s*:\s*[^\n]+\n(?:.*\n){0,12}?\s*kind\s*:\s*([A-Za-z][A-Za-z0-9]*)\s*$', content):
                kind = match.group(1)
                if kind.lower() == "list":
                    continue
                add_resource("Kubernetes", kind, path, _line_number_for_match(content, match.start()), "Kubernetes manifest")

        # Docker Compose: count declared services, not arbitrary service-like text.
        base = lp.rsplit("/", 1)[-1]
        if base in {"docker-compose.yml", "docker-compose.yaml"}:
            in_services = False
            for i, line in enumerate(content.splitlines(), 1):
                if re.match(r"^\s*services\s*:\s*$", line, re.I):
                    in_services = True
                    continue
                if in_services:
                    if re.match(r"^\S", line) and not re.match(r"^\s*#", line):
                        in_services = False
                    m = re.match(r"^\s{2,}([A-Za-z0-9_.-]+)\s*:\s*$", line)
                    if m and in_services:
                        add_resource("Docker", f"service:{m.group(1)}", path, i, "Docker Compose service")

        # Provider SDK/import evidence is recorded separately and never counted
        # as a resource definition.
        sdk_patterns = {
            "AWS": [r'\baws-sdk\b', r'@aws-sdk/', r'\bboto3\b', r'arn:aws:', r'\bAWS::'],
            "Azure": [r'@azure/', r'azure\.identity', r'\bMicrosoft\.'],
            "GCP": [r'google-cloud-', r'@google-cloud/', r'googleapis\.com'],
        }
        for provider, patterns in sdk_patterns.items():
            if any(re.search(pattern, content, re.I) for pattern in patterns):
                sdk_evidence[provider].append(path)

    # De-duplicate evidence paths while preserving order.
    for mapping in (provider_evidence, sdk_evidence):
        for provider in mapping:
            mapping[provider] = list(dict.fromkeys(mapping[provider]))

    # A provider is detected if there is explicit provider/resource/IaC evidence.
    detected_providers = [p for p in ("AWS", "Azure", "GCP") if provider_evidence[p] or sdk_evidence[p]]
    actual_cloud_resources = [r for r in resource_definitions if r["provider"] in {"AWS", "Azure", "GCP"}]
    cloud_resources = list(dict.fromkeys([f'{r["provider"]}:{r["type"]}' for r in actual_cloud_resources]))

    infrastructure_files = {
        "Terraform": extension_files.get(".tf", []) + extension_files.get(".tfvars", []),
        "Bicep": extension_files.get(".bicep", []),
        "Dockerfile": special_files["Dockerfile"],
        "Docker Compose": special_files["Docker Compose"],
        "Kubernetes/Helm": special_files["Kubernetes/Helm"],
        "GitHub Actions": special_files["GitHub Actions"],
        "Pulumi": special_files["Pulumi"],
        "CDK": special_files["CDK"],
        "CloudFormation/SAM": special_files["CloudFormation/SAM"],
    }

    resource_audit = {
        "completeFileTree": not tree_truncated,
        "totalFiles": len(paths),
        "fileTypes": [
            {"type": name, "count": count} for name, count in file_categories.items()
        ],
        "extensions": [
            {"extension": ext, "count": extension_counts[ext]}
            for ext in sorted(extension_counts)
        ],
        "specialFiles": [
            {"type": name, "count": len(items), "files": items[:50]}
            for name, items in special_files.items()
        ],
        "infrastructureFiles": [
            {"type": name, "count": len(items), "files": items[:50]}
            for name, items in infrastructure_files.items()
        ],
        "resourceDefinitions": resource_definitions,
        "resourceCounts": [
            {"resource": name, "count": count} for name, count in sorted(resource_counts.items())
        ],
        "totalDetectedResources": len(resource_definitions),
        "cloudResourceDefinitions": actual_cloud_resources,
        "cloudResourceCount": len(actual_cloud_resources),
        "cloudResources": cloud_resources,
        "providerEvidence": [
            {"provider": p, "files": provider_evidence[p], "sdkEvidenceFiles": sdk_evidence[p]}
            for p in ("AWS", "Azure", "GCP")
        ],
        "resourceCountingRule": "Only explicit resource declarations/manifests/services are counted as resources. SDK imports, provider libraries, names, comments, and generic references are evidence only and are not counted as resources.",
        "limitations": (["The GitHub file tree was truncated; file counts are counts of the returned tree, not the full repository."] if tree_truncated else []) + (["Resource definitions are limited to file contents successfully inspected by the analyzer."] if len(resource_evidence_files) < len(paths) and not tree_truncated else []),
    }

    return resource_audit, detected_providers, cloud_resources, actual_cloud_resources, provider_evidence, sdk_evidence


def analyze_repository(repo_endpoint, default_branch, files, tree_truncated=False, commit_sha=None):
    """Perform evidence-based analysis of the connected repository.

    The analyzer deliberately distinguishes between *detected* evidence and
    assumptions. It must never invent AWS/Kubernetes/Cloud resources simply
    because the dashboard has a Cloud Architecture page.
    """
    import re

    parts = repo_endpoint.strip("/").split("/")
    owner = parts[-2] if len(parts) >= 2 else ""
    repo = parts[-1] if parts else ""

    paths = [str(item.get("path", "")) for item in files if item.get("path")]
    lower_paths = [p.lower() for p in paths]
    path_set = set(lower_paths)

    # Strict architecture detection: labels are emitted only when the
    # exact triggering file or folder exists in the GitHub file tree.
    architecture_labels = []

    def has_file(filename):
        return any(path.rsplit("/", 1)[-1] == filename for path in lower_paths)

    def has_extension(extension):
        return any(path.endswith(extension) for path in lower_paths)

    def has_folder(folder_name):
        return any(folder_name in path.split("/") for path in lower_paths)

    if has_file("dockerfile"):
        architecture_labels.append("Containerized (Docker) Deployment")

    if has_file("docker-compose.yml") or has_file("docker-compose.yaml"):
        architecture_labels.append("Multi-container Orchestration")

    if any(has_file(name) for name in {"deployment.yaml", "service.yaml", "ingress.yaml"}):
        architecture_labels.append("Kubernetes Native Manifests")

    if has_file("chart.yaml") or has_file("helmfile.yaml"):
        architecture_labels.append("Helm Charts Management")

    if has_folder("terraform") or has_extension(".tf"):
        architecture_labels.append("Infrastructure as Code (Terraform)")

    if has_file("serverless.yml"):
        architecture_labels.append("Serverless Framework")

    if has_file("cloudformation.yaml"):
        architecture_labels.append("AWS CloudFormation")

    if has_file(".gitlab-ci.yml"):
        architecture_labels.append("GitLab CI/CD")

    if any(
        path.startswith(".github/workflows/")
        and path.endswith((".yml", ".yaml"))
        for path in lower_paths
    ):
        architecture_labels.append("GitHub Actions CI/CD")

    if has_file("jenkinsfile"):
        architecture_labels.append("Jenkins Pipeline")

    if has_file("azure-pipelines.yml"):
        architecture_labels.append("Azure DevOps")

    if has_file("package.json"):
        architecture_labels.append("Node.js / NPM Ecosystem")

    if has_file("yarn.lock"):
        architecture_labels.append("Node.js / Yarn Ecosystem")

    if has_file("pom.xml"):
        architecture_labels.append("Java Maven Build")

    if has_file("build.gradle") or has_file("build.gradle.kts"):
        architecture_labels.append("Java Gradle Build")

    if (
        has_file("requirements.txt")
        or has_file("pipfile")
        or has_file("pyproject.toml")
    ):
        architecture_labels.append("Python Ecosystem")

    if has_file("cargo.toml"):
        architecture_labels.append("Rust / Cargo")

    if has_file("go.mod"):
        architecture_labels.append("Go Modules")

    if has_file("gemfile"):
        architecture_labels.append("Ruby Bundler")

    if has_file("composer.json"):
        architecture_labels.append("PHP Composer")

    if has_extension(".csproj"):
        architecture_labels.append(".NET / C# Project")

    if has_file("angular.json"):
        architecture_labels.append("Angular Frontend")

    if has_file("next.config.js"):
        architecture_labels.append("Next.js React Framework")

    if has_file("nuxt.config.js"):
        architecture_labels.append("Nuxt.js Vue Framework")

    if has_file("pubspec.yaml"):
        architecture_labels.append("Flutter / Dart")

    if has_file("podfile"):
        architecture_labels.append("iOS CocoaPods")

    if has_file(".eslintrc.js"):
        architecture_labels.append("ESLint Linting")

    if has_file("jest.config.js"):
        architecture_labels.append("Jest Testing")

    if has_file("pytest.ini"):
        architecture_labels.append("Pytest Testing")

    issues = []
    evidence = []
    file_contents = {}

    def add_issue(severity, title, category, path, line, snippet, why, impact, recommendation, related):
        issues.append({
            "id": len(issues) + 1,
            "severity": severity,
            "title": title,
            "category": category,
            "file": path,
            "line": line,
            "snippet": snippet,
            "why": why,
            "impact": impact,
            "recommendation": recommendation,
            "related": related,
        })

    def add_evidence(kind, label, detail, paths_for_evidence=None, confidence="high"):
        evidence.append({
            "kind": kind,
            "label": label,
            "detail": detail,
            "files": paths_for_evidence or [],
            "confidence": confidence,
        })

    # --------------------------------------------------------
    # Select real files for inspection. Configuration is prioritized,
    # followed by source files. Raw GitHub reads avoid API-rate-limit burn.
    # --------------------------------------------------------
    priority_names = {
        "readme.md", "dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "package.json", "requirements.txt", "pyproject.toml", "pom.xml", "go.mod",
        "cargo.toml", "gemfile", "composer.json", "serverless.yml", "serverless.yaml",
        "template.yaml", "template.yml", "cloudformation.yml", "cloudformation.yaml",
        "main.tf", "variables.tf", "providers.tf", "pulumi.yaml", "cdk.json",
    }
    priority = []
    secondary = []
    source_ext = (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".cs")
    config_ext = (".tf", ".tfvars", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".xml", ".bicep")
    for item in files:
        path = str(item.get("path", ""))
        lp = path.lower()
        base = lp.rsplit("/", 1)[-1]
        if base in priority_names or ".github/workflows/" in lp or "/k8s/" in lp or "/kubernetes/" in lp or "/helm/" in lp:
            priority.append(path)
        elif lp.endswith(config_ext) or lp.endswith(source_ext) or base.startswith(".env"):
            secondary.append(path)

    ordered = []
    for path in priority + secondary:
        if path not in ordered:
            ordered.append(path)
    # Keep analysis broad but bounded. Fetch files in parallel so one slow
    # GitHub/raw request cannot make the whole repository analysis appear
    # frozen for many minutes.
    selected = ordered[:100]
    fetched = {}

    log_message(f"Starting source analysis: {len(selected)} files selected")

    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_path = {
            executor.submit(_raw_github_text, owner, repo, commit_sha or default_branch, path): path
            for path in selected
        }
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                content = future.result()
            except Exception as error:
                log_message("Source analysis warning:", path, error)
                content = ""
            if content:
                fetched[path] = content[:300_000]

    # Preserve repository priority order and enforce the 1.5MB analysis cap.
    total_bytes = 0
    for path in selected:
        content = fetched.get(path, "")
        if not content:
            continue
        if total_bytes + len(content) > 1_500_000:
            remaining = 1_500_000 - total_bytes
            if remaining <= 0:
                break
            content = content[:remaining]
        file_contents[path] = content
        total_bytes += len(content)
        if total_bytes >= 1_500_000:
            break

    log_message(f"Source analysis complete: {len(file_contents)} files inspected, {total_bytes} bytes")

    # --------------------------------------------------------
    # Repository / project identity
    # --------------------------------------------------------
    project_types = []
    project_checks = [
        ("Python", {"requirements.txt", "pyproject.toml", "poetry.lock", "pipfile"}),
        ("Node.js", {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}),
        ("Java", {"pom.xml", "build.gradle", "build.gradle.kts"}),
        ("Go", {"go.mod", "go.sum"}),
        ("Rust", {"cargo.toml", "cargo.lock"}),
        ("Ruby", {"gemfile", "gemfile.lock"}),
        ("PHP", {"composer.json", "composer.lock"}),
        (".NET", {"*.csproj", "*.sln"}),
    ]
    for label, names in project_checks:
        if any(n in path_set for n in names) or (label == ".NET" and any(p.endswith((".csproj", ".sln")) for p in lower_paths)):
            project_types.append(label)
    if not project_types:
        project_types = ["General repository"]

    has_tests = any(
        "/test" in p or "/tests" in p or p.startswith("test") or "test_" in p.rsplit("/", 1)[-1]
        for p in lower_paths
    )
    has_readme = "readme.md" in path_set or any(p.endswith("/readme.md") for p in lower_paths)
    lockfiles = [p for p in paths if p.lower().rsplit("/", 1)[-1] in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "pipfile.lock", "cargo.lock", "go.sum", "composer.lock", "gemfile.lock"}]
    if has_tests:
        add_evidence("quality", "Tests detected", "Test files/directories were found in the repository.", [p for p in paths if "/test" in p.lower() or "/tests" in p.lower()][:8])
    else:
        add_evidence("quality", "No obvious test suite detected", "No conventional test directory or test file pattern was found in the scanned tree.", [], "medium")
    if lockfiles:
        add_evidence("quality", "Dependency lockfiles detected", "The repository pins dependency resolution through lockfiles.", lockfiles[:8])

    # --------------------------------------------------------
    # --------------------------------------------------------
    # Deterministic resource audit / cloud evidence
    # --------------------------------------------------------
    resource_audit, detected_providers, cloud_resources, actual_cloud_resources, provider_evidence, sdk_evidence = build_resource_audit(
        paths, file_contents, tree_truncated
    )

    file_type_counts = {item["type"]: item["count"] for item in resource_audit["fileTypes"]}
    has_tf = file_type_counts.get("Terraform", 0) > 0
    has_bicep = file_type_counts.get("Bicep", 0) > 0
    has_pulumi = bool(resource_audit["infrastructureFiles"][6]["count"])
    has_cdk = bool(resource_audit["infrastructureFiles"][7]["count"])
    has_cloudformation = bool(resource_audit["infrastructureFiles"][8]["count"])
    has_docker = bool(resource_audit["specialFiles"][0]["count"] or resource_audit["specialFiles"][1]["count"])
    has_k8s = bool(resource_audit["specialFiles"][3]["count"] or any(r["provider"] == "Kubernetes" for r in resource_audit["resourceDefinitions"]))
    has_workflows = bool(resource_audit["specialFiles"][2]["count"])
    has_infrastructure_as_code = bool(has_tf or has_bicep or has_pulumi or has_cdk or has_cloudformation)

    # Provider evidence is not the same thing as a cloud resource.
    cloud_resource_evidence = bool(actual_cloud_resources)

    for provider, paths_found in provider_evidence.items():
        if paths_found:
            add_evidence(
                "cloud",
                f"{provider} evidence detected",
                "Explicit provider configuration or concrete provider resource declarations were found.",
                paths_found[:10],
                "high",
            )
        elif sdk_evidence.get(provider):
            add_evidence(
                "cloud-sdk",
                f"{provider} SDK evidence detected",
                "A provider SDK/library/reference was found, but this does not prove that a cloud resource is defined in the repository.",
                sdk_evidence[provider][:10],
                "medium",
            )

    if has_tf:
        add_evidence("infrastructure", "Terraform detected", "Terraform files are present.", resource_audit["infrastructureFiles"][0]["files"][:12], "high")
    if has_bicep:
        add_evidence("infrastructure", "Azure Bicep detected", "Bicep files are present.", resource_audit["infrastructureFiles"][1]["files"][:12], "high")
    if has_pulumi:
        add_evidence("infrastructure", "Pulumi detected", "Pulumi configuration is present.", resource_audit["infrastructureFiles"][6]["files"][:8], "high")
    if has_cdk:
        add_evidence("infrastructure", "CDK configuration detected", "CDK configuration is present; resource count is not inferred from the package name alone.", resource_audit["infrastructureFiles"][7]["files"][:8], "high")
    if has_cloudformation:
        add_evidence("infrastructure", "CloudFormation/SAM detected", "CloudFormation/SAM-style files are present.", resource_audit["infrastructureFiles"][8]["files"][:8], "high")
    if has_docker:
        add_evidence("runtime", "Docker detected", "A Dockerfile or Docker Compose file is present.", resource_audit["specialFiles"][0]["files"][:10] + resource_audit["specialFiles"][1]["files"][:10], "high")
    if has_k8s:
        add_evidence("runtime", "Kubernetes/Helm evidence detected", "Kubernetes manifests or Helm/Kubernetes directories are present.", resource_audit["specialFiles"][3]["files"][:10], "high")

    if actual_cloud_resources:
        provider = actual_cloud_resources[0]["provider"] if len(set(r["provider"] for r in actual_cloud_resources)) == 1 else "Multi-cloud"
        cloud_mode = "cloud"
        architecture_title = f"{provider} cloud resource architecture"
        architecture_reason = "The architecture includes only cloud resources explicitly declared in repository evidence."
    elif detected_providers:
        provider = detected_providers[0] if len(detected_providers) == 1 else "Multiple providers evidenced"
        cloud_mode = "evidence-only"
        architecture_title = "Application with cloud evidence"
        architecture_reason = "Cloud provider references were detected, but no concrete cloud resource declaration was confirmed."
    elif has_k8s:
        provider = "Kubernetes / provider not determined"
        cloud_mode = "orchestrated"
        architecture_title = "Container orchestration architecture"
        architecture_reason = "Kubernetes/Helm artifacts were detected; no cloud provider is assumed."
    elif has_docker:
        provider = "Not detected"
        cloud_mode = "container"
        architecture_title = "Containerized application architecture"
        architecture_reason = "Docker artifacts were detected; no cloud provider or cloud resource is assumed."
    elif has_infrastructure_as_code:
        provider = "Not determined"
        cloud_mode = "iac"
        architecture_title = "Infrastructure-as-code architecture"
        architecture_reason = "Infrastructure-as-code files were detected, but no unsupported cloud architecture is inferred."
    else:
        provider = "Not detected"
        cloud_mode = "application"
        architecture_title = "Application architecture"
        architecture_reason = "Only repository evidence with confirmed files/components is described."

    # Detailed issue detection
    # --------------------------------------------------------
    for path, content in file_contents.items():
        lp = path.lower()
        lines = content.splitlines()

        # Terraform / cloud network exposure
        if lp.endswith(".tf") and "0.0.0.0/0" in content:
            line = _line_number(content, r"0\.0\.0\.0/0")
            add_issue("high", "Unrestricted IPv4 ingress detected", "Cloud Infrastructure", path, line, lines[line-1].strip() if lines else "0.0.0.0/0",
                      "The infrastructure configuration allows traffic from every IPv4 address.",
                      "Internet-exposed resources can receive unsolicited traffic and are easier to scan and attack.",
                      "Restrict ingress to the required ports and trusted CIDR ranges. If public access is intentional, document the reason and compensating controls.", "Network security")

        # Terraform wildcards
        if lp.endswith(".tf") and re.search(r'\bAction\s*[:=].*["\']\*[:"\']|actions?\s*=\s*\[[^\]]*["\']\*', content, re.I):
            line = _line_number(content, r'\*')
            add_issue("medium", "Wildcard IAM-style permission detected", "Cloud Infrastructure", path, line, lines[line-1].strip() if lines else "*",
                      "A wildcard permission may grant broader access than the application requires.",
                      "If the role is compromised, excessive permissions increase blast radius.",
                      "Scope actions and resources to the minimum permissions required by the workload.", "IAM / least privilege")

        # Docker security
        if lp.rsplit("/", 1)[-1] == "dockerfile":
            user_lines = [i for i, value in enumerate(lines, 1) if value.strip().upper().startswith("USER ")]
            root_line = next((i for i, value in enumerate(lines, 1) if value.strip().upper() == "USER ROOT"), None)
            if root_line:
                add_issue("high", "Docker image explicitly runs as root", "Docker", path, root_line, lines[root_line-1].strip(),
                          "The image explicitly switches to the root user.",
                          "A container compromise can have a larger blast radius when the application process has root privileges.",
                          "Create a dedicated non-root runtime user and switch to it before starting the application.", "Docker")
            elif not user_lines and any(line.strip().upper().startswith("FROM ") for line in lines):
                add_issue("medium", "Dockerfile does not declare a runtime user", "Docker", path, 1, "USER instruction not found",
                          "No USER instruction was detected.",
                          "The final runtime identity is not explicitly constrained by the image configuration.",
                          "Declare a dedicated non-root user for the application process.", "Docker")
            if any("latest" in line.lower() and line.strip().upper().startswith("FROM ") for line in lines):
                add_issue("low", "Docker base image uses a moving latest tag", "Docker", path, _line_number(content, r"^\s*FROM .*latest"), "FROM ...:latest",
                          "A moving image tag can change without a repository change.",
                          "Builds can become less reproducible and may unexpectedly receive breaking or vulnerable changes.",
                          "Pin the base image to a stable version or digest.", "Docker reproducibility")

        # GitHub Actions
        if ".github/workflows/" in lp:
            for i, line in enumerate(lines, 1):
                if re.search(r"uses:\s*[^\s]+@(main|master)\b", line, re.I):
                    add_issue("medium", "GitHub Action references a moving branch", "CI/CD", path, i, line.strip(),
                              "The workflow references a branch instead of a fixed action release or commit.",
                              "Upstream changes can silently alter the CI/CD supply chain.",
                              "Pin third-party actions to a release tag or commit SHA.", "GitHub Actions")
            if re.search(r"permissions:\s*\n\s*contents:\s*write|permissions:\s*write-all", content, re.I):
                add_issue("medium", "GitHub Actions workflow requests write permissions", "CI/CD", path, _line_number(content, r"permissions:"), "Workflow permissions include write access.",
                          "Broad token permissions increase the impact of a compromised workflow.",
                          "Grant only the repository permissions required by each job.", "GitHub Actions security")

        # Kubernetes
        if lp.endswith((".yaml", ".yml")) and ("apiVersion:" in content and re.search(r"kind:\s*(Deployment|StatefulSet|DaemonSet)", content, re.I)):
            if "resources:" not in content:
                add_issue("medium", "Kubernetes workload has no resource requests/limits", "Kubernetes", path, 1, "resources: not found",
                          "No CPU or memory resource configuration was detected for a workload.",
                          "Unbounded workloads can consume node resources and create noisy-neighbor failures.",
                          "Define realistic CPU/memory requests and limits for each container.", "Kubernetes")
            if re.search(r"image:\s*[^\s]+:latest\b", content, re.I):
                add_issue("low", "Kubernetes image uses the latest tag", "Kubernetes", path, _line_number(content, r"image:.*:latest"), "image: ...:latest",
                          "The deployment does not pin an immutable application image version.",
                          "A new image can be deployed without a manifest change, reducing rollout reproducibility.",
                          "Use a versioned tag or image digest.", "Kubernetes reproducibility")

        # Obvious secret-bearing filenames
        base = lp.rsplit("/", 1)[-1]
        if base in {".env", ".env.local", ".env.production", ".env.prod"}:
            add_issue("high", "Environment file is committed", "Security", path, 1, path,
                      "A live-style environment file is present in the repository tree.",
                      "Environment files frequently contain credentials, tokens, or connection strings.",
                      "Remove secrets from version control, rotate exposed credentials, and use a secret manager or CI secrets.", "Secrets")

        # Basic hard-coded secret patterns in text files
        secret_match = re.search(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|password)\s*[:=]\s*[\"'][^\"']{12,}[\"']", content)
        if secret_match and base not in {"readme.md", "readme.txt"} and "example" not in base and "sample" not in base:
            line = content[:secret_match.start()].count("\n") + 1
            add_issue("high", "Possible hard-coded credential detected", "Security", path, line, "credential-like assignment",
                      "A credential-like value appears to be assigned directly in source/configuration.",
                      "Committed credentials can be copied and abused independently of the application.",
                      "Move the value to environment/secret storage and rotate it if it is real.", "Secrets")

    # --------------------------------------------------------
    # --------------------------------------------------------
    # Grounded architecture graph — only confirmed components
    # --------------------------------------------------------
    nodes = [{"id": "github", "label": "GitHub Repository", "kind": "source", "detail": "Confirmed repository source."}]
    edges = []

    if has_workflows:
        nodes.append({"id": "actions", "label": "GitHub Actions", "kind": "cicd", "detail": "Confirmed .github/workflows files."})
        edges.append(["github", "actions"])
    if has_docker:
        nodes.append({"id": "docker", "label": "Docker", "kind": "runtime", "detail": "Confirmed Dockerfile or Docker Compose file."})
        edges.append(["actions" if has_workflows else "github", "docker"])
    if has_k8s:
        nodes.append({"id": "kubernetes", "label": "Kubernetes / Helm", "kind": "orchestration", "detail": "Confirmed Kubernetes/Helm evidence."})
        edges.append(["docker" if has_docker else ("actions" if has_workflows else "github"), "kubernetes"])

    for provider_name in detected_providers:
        pid = provider_name.lower().replace(" ", "-")
        nodes.append({
            "id": pid,
            "label": provider_name,
            "kind": "cloud-evidence",
            "detail": "Provider evidence confirmed; a cloud resource is shown only when explicitly declared.",
        })
        edges.append(["kubernetes" if has_k8s else ("docker" if has_docker else ("actions" if has_workflows else "github")), pid])

    for resource in actual_cloud_resources:
        rid = "resource-" + str(len(nodes))
        nodes.append({
            "id": rid,
            "label": f'{resource["provider"]}:{resource["type"]}',
            "kind": "cloud-resource",
            "detail": f'Explicit {resource["sourceKind"]} found in {resource["file"]}:{resource["line"]}.',
        })
        parent = resource["provider"].lower().replace(" ", "-")
        if any(n["id"] == parent for n in nodes):
            edges.append([parent, rid])
        else:
            edges.append(["github", rid])

    if not has_docker and not has_k8s and not detected_providers and not has_workflows and not actual_cloud_resources:
        nodes.append({"id": "application", "label": "Application / Source", "kind": "application", "detail": "No deployment infrastructure was confirmed in the repository evidence."})
        edges.append(["github", "application"])

    if actual_cloud_resources:
        cloud_assessment = f"{len(actual_cloud_resources)} concrete cloud resource definition(s) were confirmed in repository files."
    elif detected_providers:
        cloud_assessment = "Provider evidence was detected, but no concrete cloud resource definition was confirmed; no cloud resource is claimed."
    elif has_k8s:
        cloud_assessment = "Kubernetes evidence was detected. A specific cloud provider is not claimed."
    elif has_docker:
        cloud_assessment = "Docker evidence was detected. A cloud provider is not claimed."
    elif has_infrastructure_as_code:
        cloud_assessment = "Infrastructure-as-code files were detected. Provider-specific resources are not claimed unless explicitly declared."
    else:
        cloud_assessment = "No concrete cloud resource definition was confirmed in the repository evidence."

    architecture = {
        "mode": cloud_mode,
        "title": architecture_title,
        "provider": provider,
        "cloudRequiredEvidence": cloud_resource_evidence,
        "confidence": 100 if resource_audit["completeFileTree"] else 85,
        "reason": architecture_reason,
        "cloudAssessment": cloud_assessment,
        "architectureLabels": architecture_labels,
        "nodes": nodes,
        "edges": edges,
        "evidence": evidence,
        "resourceAudit": resource_audit,
        "detected": {
            "cloudProviders": detected_providers,
            "cloudResources": cloud_resources,
            "cloudResourceDefinitions": actual_cloud_resources,
            "terraform": has_tf,
            "bicep": has_bicep,
            "pulumi": has_pulumi,
            "cdk": has_cdk,
            "cloudFormation": has_cloudformation,
            "docker": has_docker,
            "kubernetes": has_k8s,
            "githubActions": has_workflows,
            "architectureLabels": architecture_labels,
        },
        "disclaimer": "Only confirmed repository evidence is used. Missing files/resources are reported as zero or not detected; external infrastructure is not inferred."
    }

    # Scoring — reward evidence and testability, penalize findings.
    # A clean repo can score highly, but scores are not forced to 100.
    # --------------------------------------------------------
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in issues:
        counts[issue["severity"]] += 1

    quality = 55
    if has_readme: quality += 8
    if has_tests: quality += 15
    if lockfiles: quality += 8
    if project_types != ["General repository"]: quality += 7
    if len(paths) > 10: quality += 5
    quality -= counts["critical"] * 6 + counts["high"] * 4 + counts["medium"] * 2
    quality = max(0, min(100, quality))

    security = 90
    security -= counts["critical"] * 25 + counts["high"] * 12 + counts["medium"] * 5 + counts["low"] * 2
    security = max(0, min(100, security))

    infrastructure = 70
    if cloud_resource_evidence: infrastructure += 15
    if has_docker: infrastructure += 5
    if has_k8s: infrastructure += 5
    if has_workflows: infrastructure += 3
    if not cloud_resource_evidence and not has_docker and not has_k8s: infrastructure = 80
    infrastructure -= counts["high"] * 2 + counts["medium"]
    infrastructure = max(0, min(100, infrastructure))

    cicd = 70 if has_workflows else 55
    if has_workflows: cicd += 15 if has_tests else 5
    cicd -= sum(1 for i in issues if i["category"] == "CI/CD") * 7
    cicd = max(0, min(100, cicd))

    configuration = 82
    configuration += 8 if lockfiles else 0
    configuration += 5 if has_readme else 0
    configuration -= counts["critical"] * 7 + counts["high"] * 4 + counts["medium"] * 2
    configuration = max(0, min(100, configuration))

    overall = round(quality * 0.25 + security * 0.30 + infrastructure * 0.15 + cicd * 0.15 + configuration * 0.15)
    status = "Excellent" if overall >= 90 else "Healthy" if overall >= 80 else "Good — Improvements Recommended" if overall >= 65 else "Needs Attention" if overall >= 45 else "Critical — Immediate Action Required"

    recommendations = [{
        "id": issue["id"],
        "severity": issue["severity"],
        "title": issue["recommendation"],
        "why": issue["why"],
        "action": issue["recommendation"],
        "relatedIssue": issue["id"],
    } for issue in sorted(issues, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["severity"]])[:8]]

    tech_stack = [{"name": p, "category": "Language / Runtime"} for p in project_types]
    if has_docker: tech_stack.append({"name": "Docker", "category": "Container"})
    if has_k8s: tech_stack.append({"name": "Kubernetes / Helm", "category": "Orchestration"})
    if has_tf: tech_stack.append({"name": "Terraform", "category": "Infrastructure as Code"})
    if has_workflows: tech_stack.append({"name": "GitHub Actions", "category": "CI/CD"})
    for p in detected_providers: tech_stack.append({"name": p, "category": "Cloud provider evidence"})

    return {
        "overall": overall,
        "status": status,
        "subscores": [
            {"label": "Code Quality", "value": quality, "tone": "emerald" if quality >= 80 else "amber"},
            {"label": "Security", "value": security, "tone": "emerald" if security >= 85 else "amber" if security >= 65 else "critical"},
            {"label": "Infrastructure", "value": infrastructure, "tone": "blue"},
            {"label": "CI/CD", "value": cicd, "tone": "emerald" if cicd >= 85 else "amber"},
            {"label": "Configuration", "value": configuration, "tone": "emerald" if configuration >= 85 else "amber"},
        ],
        "security": {"score": security, "findings": counts},
        "issues": issues,
        "severityCounts": counts,
        "recommendations": recommendations,
        "metrics": {
            "issues": len(issues),
            "critical": counts["critical"],
            "securityFindings": sum(counts.values()),
            "hasDocker": has_docker,
            "hasKubernetes": has_k8s,
            "hasTerraform": has_tf,
            "hasCICD": has_workflows,
            "hasCloudResources": cloud_resource_evidence,
            "cloudProviders": detected_providers,
            "cloudResourceCount": len(actual_cloud_resources),
            "cloudResources": cloud_resources,
            "resourceCount": resource_audit["totalDetectedResources"],
            "resourceAudit": resource_audit,
            "filesAnalyzed": len(file_contents),
            "filesTotal": len(paths),
            "testsDetected": has_tests,
            "projectTypes": project_types,
        },
        "architecture": architecture,
        "resourceAudit": resource_audit,
        "techStack": tech_stack,
        "analysisScope": {
            "filesInRepository": len(paths),
            "filesInspected": len(file_contents),
            "branch": default_branch,
            "commitSha": commit_sha,
            "revisionUsedForFiles": commit_sha or default_branch,
            "method": "Deterministic repository tree audit + explicit resource declarations + inspected file evidence",
            "fileTreeComplete": resource_audit["completeFileTree"],
            "zeroHallucinationPolicy": True,
        },
    }

# ============================================================
# Home
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Cloud-ByteXL Backend is running",
        "github_integration": True,
        "github_repository_endpoint": "/api/github/repository",
        "github_file_endpoint": "/api/github/file",
        "github_webhook_endpoint": "/webhook",
    })


# ============================================================
# Database connection test
# ============================================================

@app.route(
    "/api/database/test",
    methods=["GET"]
)
def database_test():

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT current_database();"
            )

            database_name = cursor.fetchone()[0]

        return jsonify({
            "status": "SUCCESS",
            "message": "PostgreSQL connection successful",
            "database": database_name
        }), 200

    except Exception as error:

        log_message(
            "Database connection error:",
            error
        )

        return jsonify({
            "status": "FAILED",
            "message": "Could not connect to PostgreSQL",
            "error": "Internal server error. See backend logs for details."
        }), 500

    finally:

        if connection:
            connection.close()


# ============================================================
# Connect and read a real GitHub repository
# ============================================================

@app.route(
    "/api/github/repository",
    methods=["POST"],
)
def connect_github_repository():
    """
    Read a real GitHub repository and return repository data
    for the React dashboard.

    Request:
        {
            "url": "https://github.com/owner/repository"
        }
    """

    global latest_github_repository

    data = request.get_json(
        silent=True
    ) or {}

    repo_url = data.get("url") if isinstance(data, dict) else None

    try:
        owner, repo = parse_github_url(repo_url)

        repo_endpoint = (
            f"/repos/{owner}/{repo}"
        )

        # --------------------------------------------------------
        # 1. Repository metadata
        # --------------------------------------------------------

        repository = github_request(
            repo_endpoint
        )

        default_branch = repository.get(
            "default_branch",
            "main",
        )

        # --------------------------------------------------------
        # 1A. Resolve the exact repository HEAD commit
        # --------------------------------------------------------
        # The analysis must be tied to a concrete commit snapshot,
        # not a moving branch name.
        commit_data = github_request(
            f"{repo_endpoint}/commits/{quote(default_branch, safe='')}"
        )

        commit_sha = commit_data.get("sha")

        if not commit_sha:
            raise ValueError(
                "GitHub did not return a commit SHA for the default branch. "
                "Analysis cannot continue without an exact repository revision."
            )

        # --------------------------------------------------------
        # 2. Languages
        # --------------------------------------------------------

        languages = github_request(
            f"{repo_endpoint}/languages"
        )

        language_data = calculate_language_percentages(
            languages
        )

        # --------------------------------------------------------
        # 3. File tree
        # --------------------------------------------------------

        encoded_commit = quote(
            commit_sha,
            safe="",
        )

        tree = github_request(
            f"{repo_endpoint}/git/trees/"
            f"{encoded_commit}?recursive=1"
        )

        files = []

        for item in tree.get("tree", []):
            if item.get("type") != "blob":
                continue

            files.append({
                "path": item.get("path"),
                "type": "file",
                "size": item.get("size", 0),
            })

        # --------------------------------------------------------
        # 4. Recent commits
        # --------------------------------------------------------

        commits = github_request(
            f"{repo_endpoint}/commits?per_page=10"
        )

        commit_data = []

        for commit in commits:
            commit_info = commit.get(
                "commit",
                {},
            )

            author_info = commit_info.get(
                "author",
                {},
            )

            commit_data.append({
                "hash": commit.get(
                    "sha",
                    "",
                )[:7],

                "sha": commit.get(
                    "sha"
                ),

                "message": commit_info.get(
                    "message",
                    "",
                ).split("\n")[0],

                "author": author_info.get(
                    "name",
                    "Unknown",
                ),

                "date": author_info.get(
                    "date"
                ),

                "url": commit.get(
                    "html_url"
                ),
            })

        # --------------------------------------------------------
        # 5. Contributors
        # --------------------------------------------------------

        contributors = github_request(
            f"{repo_endpoint}/contributors?per_page=10"
        )

        contributor_data = []

        for contributor in contributors:
            contributor_data.append({
                "name": contributor.get(
                    "login",
                    "Unknown",
                ),

                "commits": contributor.get(
                    "contributions",
                    0,
                ),

                "avatar": contributor.get(
                    "avatar_url"
                ),

                "url": contributor.get(
                    "html_url"
                ),
            })

        # --------------------------------------------------------
        # 6. Build response
        # --------------------------------------------------------

        repository_data = {
            "id": repository.get("id"),

            "name": repository.get(
                "name"
            ),

            "fullName": repository.get(
                "full_name"
            ),

            "url": repository.get(
                "html_url"
            ),

            "cloneUrl": repository.get(
                "clone_url"
            ),

            "description": repository.get(
                "description"
            ),

            "owner": repository.get(
                "owner",
                {},
            ).get(
                "login"
            ),

            "branch": default_branch,
            "analysisCommitSha": commit_sha,

            "visibility": repository.get(
                "visibility"
            ),

            "private": repository.get(
                "private",
                False,
            ),

            "stars": repository.get(
                "stargazers_count",
                0,
            ),

            "forks": repository.get(
                "forks_count",
                0,
            ),

            "openIssues": repository.get(
                "open_issues_count",
                0,
            ),

            "createdAt": repository.get(
                "created_at"
            ),

            "updatedAt": repository.get(
                "updated_at"
            ),
        }

        analysis = analyze_repository(
            repo_endpoint,
            default_branch,
            files,
            tree.get("truncated", False),
            commit_sha,
        )

        response = {
            "status": "SUCCESS",
            "repository": repository_data,
            "languages": language_data,
            "files": files,
            "fileCount": len(files),
            "treeTruncated": tree.get("truncated", False),
            "commits": commit_data,
            "contributors": contributor_data,
            "analysis": analysis,
        }

        # --------------------------------------------------------
        # 7. Persist repository in PostgreSQL
        # --------------------------------------------------------

        try:
            if os.getenv('PUBLIC_DEMO_MODE')=='1':
                response['databaseWarning']='Public demo analysis is read-only; this repository was not saved to PostgreSQL.'
            else:
                repository_id = save_github_repository(repository_data)
                response["repository"]["databaseId"] = repository_id

        except Exception as database_error:
            # GitHub ingestion remains successful even if
            # PostgreSQL is temporarily unavailable.
            log_message(
                "GitHub repository database save error:",
                database_error,
            )

            response["databaseWarning"] = (
                "Repository was read from GitHub, "
                "but could not be saved to PostgreSQL."
            )

        latest_github_repository = response

        log_message(
            "\n========== GITHUB REPOSITORY INGESTED =========="
        )

        log_message(
            "Repository:",
            repository_data["fullName"],
        )

        log_message(
            "Branch:",
            default_branch,
        )

        log_message(
            "Analysis commit:",
            commit_sha,
        )

        log_message(
            "Files:",
            len(files),
        )

        log_message(
            "Languages:",
            len(language_data),
        )

        log_message(
            "Commits:",
            len(commit_data),
        )

        log_message(
            "Contributors:",
            len(contributor_data),
        )

        log_message(
            "===============================================\n"
        )

        return jsonify(response), 200

    except ValueError as error:
        return jsonify({
            "status": "FAILED",
            "message": str(error),
        }), 400

    except Exception as error:
        app.logger.exception("GitHub repository ingestion failed")

        return jsonify({
            "status": "FAILED",
            "message": (
                "Failed to read GitHub repository."
            ),
            "error": "Internal server error. See backend logs for details.",
        }), 500


# ============================================================
# Get latest connected GitHub repository
# ============================================================

@app.route(
    "/api/github/repository/latest",
    methods=["GET"],
)
def get_latest_github_repository():
    # Fast path: use the in-memory result from the current backend process.
    if latest_github_repository is not None:
        return jsonify(latest_github_repository), 200

    # Fallback: restore the latest repository from PostgreSQL after a restart.
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name, url, branch
                FROM repositories
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()

        if not row:
            return jsonify({
                "status": "NOT_CONNECTED",
                "message": "No GitHub repository has been connected yet.",
            }), 404

        name, url, branch = row
        return jsonify({
            "status": "SUCCESS",
            "repository": {
                "name": name,
                "fullName": name,
                "url": url,
                "branch": branch or "main",
                "owner": None,
            },
            "languages": [],
            "files": [],
            "fileCount": 0,
            "commits": [],
            "contributors": [],
            "restoredFromDatabase": True,
        }), 200

    except Exception as error:
        log_message("Latest GitHub repository lookup error:", error)
        return jsonify({
            "status": "FAILED",
            "message": "Could not restore the latest GitHub repository.",
            "error": "Internal server error. See backend logs for details.",
        }), 500
    finally:
        if connection:
            connection.close()


# ============================================================
# Read a specific file from a GitHub repository
# ============================================================

@app.route(
    "/api/github/file",
    methods=["POST"],
)
def get_github_file():
    """
    Read actual file content from GitHub.

    Request:
        {
            "url": "https://github.com/owner/repository",
            "path": "Dockerfile"
        }

    This endpoint is the foundation for the later analysis
    engine because the dashboard can request real source files.
    """

    data = request.get_json(
        silent=True
    ) or {}

    repo_url = data.get("url") if isinstance(data, dict) else None
    if not isinstance(data, dict):
        return jsonify(status="FAILED", message="A JSON object is required."), 400
    file_path = data.get("path")

    if not isinstance(file_path, str) or not file_path.strip():
        return jsonify({
            "status": "FAILED",
            "message": "A nonempty file path is required.",
        }), 400

    if data.get("branch") is not None and (not isinstance(data["branch"], str) or not data["branch"].strip()):
        return jsonify(status="FAILED", message="Branch or commit reference must be a nonempty string."), 400

    try:
        owner, repo = parse_github_url(
            repo_url
        )

        repo_endpoint = (
            f"/repos/{owner}/{repo}"
        )

        repository = github_request(
            repo_endpoint
        )

        branch = data.get(
            "branch"
        ) or repository.get(
            "default_branch",
            "main",
        )

        encoded_path = quote(
            file_path.strip("/"),
            safe="/",
        )

        encoded_ref = quote(
            branch,
            safe="",
        )

        file_data = github_request(
            f"{repo_endpoint}/contents/"
            f"{encoded_path}?ref={encoded_ref}"
        )

        if file_data.get("type") != "file":
            return jsonify({
                "status": "FAILED",
                "message": (
                    "The requested GitHub path is not a file."
                ),
            }), 400

        encoded_content = file_data.get(
            "content",
            "",
        ).replace(
            "\n",
            "",
        )

        try:
            content = base64.b64decode(
                encoded_content
            ).decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            content = ""

        return jsonify({
            "status": "SUCCESS",

            "repository": repository.get(
                "full_name"
            ),

            "branch": branch,

            "path": file_data.get(
                "path"
            ),

            "size": file_data.get(
                "size",
                0,
            ),

            "sha": file_data.get(
                "sha"
            ),

            "url": file_data.get(
                "html_url"
            ),

            "content": content,
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "FAILED",
            "message": str(error),
        }), 400

    except Exception as error:
        log_message(
            "GitHub file read error:",
            error,
        )

        return jsonify({
            "status": "FAILED",
            "message": (
                "Failed to read GitHub file."
            ),
            "error": "Internal server error. See backend logs for details.",
        }), 500


# ============================================================
# GitHub Webhook
# ============================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    global latest_webhook

    data = request.get_json(
        silent=True
    ) or {}

    # --------------------------------------------------------
    # GitHub event
    # --------------------------------------------------------

    event = request.headers.get(
        "X-GitHub-Event",
        "Unknown"
    )

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    repository = data.get(
        "repository",
        {}
    )

    repo_name = repository.get(
        "name",
        "Unknown"
    )

    repo_url = repository.get(
        "html_url",
        ""
    )

    # --------------------------------------------------------
    # Branch
    # --------------------------------------------------------

    ref = data.get(
        "ref",
        "Unknown"
    )

    branch = ref

    if ref.startswith("refs/heads/"):

        branch = ref.replace(
            "refs/heads/",
            ""
        )

    # --------------------------------------------------------
    # Pusher
    # --------------------------------------------------------

    pusher = data.get(
        "pusher",
        {}
    )

    pusher_name = pusher.get(
        "name",
        "Unknown"
    )

    # --------------------------------------------------------
    # Commits
    # --------------------------------------------------------

    commits = data.get(
        "commits",
        []
    )

    # --------------------------------------------------------
    # Store latest webhook in memory
    # --------------------------------------------------------

    latest_webhook = {
        "event": event,
        "repository": repo_name,
        "branch": branch,
        "pusher": pusher_name,
        "commits": commits
    }

    log_message(
        "\n========== GITHUB WEBHOOK =========="
    )

    log_message(
        "Event:",
        event
    )

    log_message(
        "Repository:",
        repo_name
    )

    log_message(
        "Branch:",
        branch
    )

    log_message(
        "Pusher:",
        pusher_name
    )

    log_message(
        "Number of commits:",
        len(commits)
    )

    # ========================================================
    # Store information in PostgreSQL
    # ========================================================

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            # ------------------------------------------------
            # 1. Find or create integration user
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = %s
                """,
                ("github-webhook",)
            )

            user_row = cursor.fetchone()

            if user_row:

                user_id = user_row[0]

            else:

                cursor.execute(
                    """
                    INSERT INTO users
                        (
                            username,
                            email
                        )
                    VALUES
                        (
                            %s,
                            %s
                        )
                    RETURNING id
                    """,
                    (
                        "github-webhook",
                        "github-webhook@cloud-bytexl.local"
                    )
                )

                user_id = cursor.fetchone()[0]

            # ------------------------------------------------
            # 2. Find or create repository
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM repositories
                WHERE name = %s
                """,
                (repo_name,)
            )

            repository_row = cursor.fetchone()

            if repository_row:

                repository_id = repository_row[0]

                cursor.execute(
                    """
                    UPDATE repositories
                    SET
                        url = %s,
                        branch = %s
                    WHERE id = %s
                    """,
                    (
                        repo_url,
                        branch,
                        repository_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO repositories
                        (
                            user_id,
                            name,
                            url,
                            branch
                        )
                    VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    RETURNING id
                    """,
                    (
                        user_id,
                        repo_name,
                        repo_url,
                        branch
                    )
                )

                repository_id = cursor.fetchone()[0]

            # ------------------------------------------------
            # 3. Create deployment records
            # ------------------------------------------------

            if commits:

                for commit in commits:

                    commit_id = commit.get(
                        "id",
                        "Unknown"
                    )

                    cursor.execute(
                        """
                        INSERT INTO deployments
                            (
                                repository_id,
                                commit_id,
                                branch,
                                status,
                                started_at
                            )
                        VALUES
                            (
                                %s,
                                %s,
                                %s,
                                %s,
                                %s
                            )
                        RETURNING id
                        """,
                        (
                            repository_id,
                            commit_id,
                            branch,
                            "RECEIVED",
                            datetime.now()
                        )
                    )

                    deployment_id = cursor.fetchone()[0]

                    commit_message = commit.get(
                        "message",
                        "No commit message"
                    )

                    # ------------------------------------------------
                    # Phase 7 - GitHub log
                    # ------------------------------------------------

                    log_message = (
                        f"GitHub {event} received. "
                        f"Repository: {repo_name}. "
                        f"Branch: {branch}. "
                        f"Pusher: {pusher_name}. "
                        f"Commit: {commit_id}. "
                        f"Message: {commit_message}"
                    )

                    create_deployment_log(
                        cursor,
                        deployment_id,
                        log_message,
                        "INFO"
                    )

                    log_message(
                        "Deployment saved:",
                        deployment_id
                    )

            else:

                # ------------------------------------------------
                # Handle webhook with no commits
                # ------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO deployments
                        (
                            repository_id,
                            commit_id,
                            branch,
                            status,
                            started_at
                        )
                    VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    RETURNING id
                    """,
                    (
                        repository_id,
                        None,
                        branch,
                        "RECEIVED",
                        datetime.now()
                    )
                )

                deployment_id = cursor.fetchone()[0]

                create_deployment_log(
                    cursor,
                    deployment_id,
                    (
                        f"GitHub {event} event received "
                        f"for {repo_name}"
                    ),
                    "INFO"
                )

                log_message(
                    "Deployment saved:",
                    deployment_id
                )

        connection.commit()

        log_message(
            "Database records saved successfully."
        )

    except Exception as error:

        if connection:
            connection.rollback()

        log_message(
            "Database webhook error:",
            error
        )

    finally:

        if connection:
            connection.close()

    # ========================================================
    # Print commit information
    # ========================================================

    for commit in commits:

        log_message(
            "Commit:",
            commit.get("id")
        )

        log_message(
            "Message:",
            commit.get("message")
        )

        log_message(
            "Author:",
            commit.get(
                "author",
                {}
            ).get(
                "name"
            )
        )

        log_message(
            "Added:",
            commit.get(
                "added",
                []
            )
        )

        log_message(
            "Modified:",
            commit.get(
                "modified",
                []
            )
        )

        log_message(
            "Removed:",
            commit.get(
                "removed",
                []
            )
        )

    log_message(
        "====================================\n"
    )

    return jsonify({
        "message": "GitHub webhook processed successfully",
        "repository": repo_name,
        "branch": branch,
        "pusher": pusher_name,
        "commits": len(commits)
    }), 200


# ============================================================
# Get latest GitHub webhook
# ============================================================

@app.route(
    "/api/github/latest",
    methods=["GET"]
)
def get_latest_webhook():

    return jsonify(
        latest_webhook
    )


# ============================================================
# Receive CI/CD status
# ============================================================

@app.route(
    "/api/ci/status",
    methods=["POST"]
)
def update_ci_status():

    global latest_ci

    # Opt-in authentication preserves existing local clients. Configure the same
    # token on Flask and the CI sender before enabling a remote callback.
    callback_token = os.getenv("CI_STATUS_TOKEN", "")
    if callback_token and not hmac.compare_digest(
        request.headers.get("Authorization", ""), "Bearer " + callback_token
    ):
        return jsonify(status="FAILED", message="Unauthorized CI callback."), 401

    data = request.get_json(
        silent=True
    ) or {}

    # --------------------------------------------------------
    # Update in-memory CI status
    # --------------------------------------------------------

    latest_ci = {

        "status": data.get(
            "status",
            "UNKNOWN"
        ),

        "build": data.get(
            "build",
            "UNKNOWN"
        ),

        "tests": data.get(
            "tests",
            "UNKNOWN"
        ),

        "docker": data.get(
            "docker",
            "UNKNOWN"
        ),

        "workflow": data.get(
            "workflow",
            "Cloud-ByteXL CI"
        )
    }

    log_message(
        "\n========== CI/CD STATUS =========="
    )

    log_message(
        "Workflow:",
        latest_ci["workflow"]
    )

    log_message(
        "Overall Status:",
        latest_ci["status"]
    )

    log_message(
        "Build:",
        latest_ci["build"]
    )

    log_message(
        "Tests:",
        latest_ci["tests"]
    )

    log_message(
        "Docker:",
        latest_ci["docker"]
    )

    # ========================================================
    # Update latest deployment in PostgreSQL
    # ========================================================

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            # ------------------------------------------------
            # Find latest deployment
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    id
                FROM deployments
                ORDER BY id DESC
                LIMIT 1
                """
            )

            deployment_row = cursor.fetchone()

            if not deployment_row:

                log_message(
                    "No deployment found to update."
                )

            else:

                deployment_id = deployment_row[0]

                # ------------------------------------------------
                # Determine deployment status
                # ------------------------------------------------

                ci_status = str(
                    latest_ci["status"]
                ).upper()

                if ci_status == "SUCCESS":

                    deployment_status = "SUCCESS"

                elif ci_status == "FAILURE":

                    deployment_status = "FAILED"

                else:

                    deployment_status = ci_status

                # ------------------------------------------------
                # Update deployment
                # ------------------------------------------------

                cursor.execute(
                    """
                    UPDATE deployments
                    SET
                        status = %s,
                        completed_at = %s
                    WHERE id = %s
                    """,
                    (
                        deployment_status,
                        datetime.now(),
                        deployment_id
                    )
                )

                log_message(
                    "Deployment updated:",
                    deployment_id
                )

                log_message(
                    "Deployment status:",
                    deployment_status
                )

                # =================================================
                # PHASE 7 - Individual CI/CD logs
                # =================================================

                create_deployment_log(
                    cursor,
                    deployment_id,
                    (
                        f"Build stage completed with status: "
                        f"{latest_ci['build']}"
                    ),
                    (
                        "INFO"
                        if str(
                            latest_ci["build"]
                        ).upper() == "PASSED"
                        else "ERROR"
                    )
                )

                create_deployment_log(
                    cursor,
                    deployment_id,
                    (
                        f"Tests stage completed with status: "
                        f"{latest_ci['tests']}"
                    ),
                    (
                        "INFO"
                        if str(
                            latest_ci["tests"]
                        ).upper() == "PASSED"
                        else "ERROR"
                    )
                )

                create_deployment_log(
                    cursor,
                    deployment_id,
                    (
                        f"Docker stage completed with status: "
                        f"{latest_ci['docker']}"
                    ),
                    (
                        "INFO"
                        if str(
                            latest_ci["docker"]
                        ).upper() == "PASSED"
                        else "ERROR"
                    )
                )

                # ------------------------------------------------
                # Overall CI/CD log
                # ------------------------------------------------

                ci_log_message = (
                    f"CI/CD workflow "
                    f"'{latest_ci['workflow']}' "
                    f"completed with status "
                    f"{deployment_status}. "
                    f"Build: {latest_ci['build']}. "
                    f"Tests: {latest_ci['tests']}. "
                    f"Docker: {latest_ci['docker']}."
                )

                create_deployment_log(
                    cursor,
                    deployment_id,
                    ci_log_message,
                    (
                        "INFO"
                        if deployment_status == "SUCCESS"
                        else "ERROR"
                    )
                )

                # =================================================
                # Failure analysis
                # =================================================

                if deployment_status == "FAILED":

                    # ------------------------------------------------
                    # Prevent duplicate failure records
                    # ------------------------------------------------

                    cursor.execute(
                        """
                        SELECT id
                        FROM failure_analysis
                        WHERE deployment_id = %s
                        LIMIT 1
                        """,
                        (deployment_id,)
                    )

                    existing_failure = cursor.fetchone()

                    if not existing_failure:

                        failure_type = "CI/CD_FAILURE"

                        failed_parts = []

                        if str(
                            latest_ci["build"]
                        ).upper() != "PASSED":

                            failed_parts.append(
                                f"Build: {latest_ci['build']}"
                            )

                        if str(
                            latest_ci["tests"]
                        ).upper() != "PASSED":

                            failed_parts.append(
                                f"Tests: {latest_ci['tests']}"
                            )

                        if str(
                            latest_ci["docker"]
                        ).upper() != "PASSED":

                            failed_parts.append(
                                f"Docker: {latest_ci['docker']}"
                            )

                        if failed_parts:

                            error_message = (
                                "; ".join(
                                    failed_parts
                                )
                            )

                        else:

                            error_message = (
                                "CI/CD pipeline failed."
                            )

                        suggested_fix = (
                            "Review the failed CI/CD step, "
                            "check the GitHub Actions logs, "
                            "fix the failing build, tests, "
                            "or Docker configuration, "
                            "and push a new commit."
                        )

                        cursor.execute(
                            """
                            INSERT INTO failure_analysis
                                (
                                    deployment_id,
                                    failure_type,
                                    error_message,
                                    suggested_fix
                                )
                            VALUES
                                (
                                    %s,
                                    %s,
                                    %s,
                                    %s
                                )
                            """,
                            (
                                deployment_id,
                                failure_type,
                                error_message,
                                suggested_fix
                            )
                        )

                        create_deployment_log(
                            cursor,
                            deployment_id,
                            (
                                "Failure analysis created: "
                                + error_message
                            ),
                            "ERROR"
                        )

                        log_message(
                            "Failure analysis created for "
                            "deployment:",
                            deployment_id
                        )

                    else:

                        log_message(
                            "Failure analysis already exists "
                            "for deployment:",
                            deployment_id
                        )

        connection.commit()

        log_message(
            "CI/CD database update completed."
        )

    except Exception as error:

        if connection:
            connection.rollback()

        log_message(
            "CI/CD database update error:",
            error
        )

    finally:

        if connection:
            connection.close()

    log_message(
        "==================================\n"
    )

    return jsonify({
        "message": "CI/CD status updated successfully",
        "ci": latest_ci
    }), 200


# ============================================================
# Get latest CI/CD status
# ============================================================

@app.route(
    "/api/ci/status",
    methods=["GET"]
)
def get_ci_status():

    return jsonify(
        latest_ci
    )


# ============================================================
# Get database statistics
# ============================================================

@app.route(
    "/api/database/stats",
    methods=["GET"]
)
def database_stats():

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) FROM users"
            )

            users_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM repositories"
            )

            repositories_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM deployments"
            )

            deployments_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM deployment_logs"
            )

            logs_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM failure_analysis"
            )

            failures_count = cursor.fetchone()[0]

        return jsonify({

            "status": "SUCCESS",

            "users": users_count,

            "repositories": repositories_count,

            "deployments": deployments_count,

            "deployment_logs": logs_count,

            "failure_analysis": failures_count

        }), 200

    except Exception as error:

        log_message(
            "Database statistics error:",
            error
        )

        return jsonify({

            "status": "FAILED",

            "message": str(error)

        }), 500

    finally:

        if connection:
            connection.close()


# ============================================================
# Get deployment history
# ============================================================

@app.route(
    "/api/deployments",
    methods=["GET"]
)
def get_deployments():

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    d.id,
                    d.commit_id,
                    d.branch,
                    d.status,
                    d.started_at,
                    d.completed_at,
                    r.name AS repository
                FROM deployments d
                LEFT JOIN repositories r
                    ON d.repository_id = r.id
                ORDER BY d.id DESC
                """
            )

            rows = cursor.fetchall()

        deployments = []

        for row in rows:

            deployments.append({

                "id": row[0],

                "commit_id": row[1],

                "branch": row[2],

                "status": row[3],

                "started_at": (
                    row[4].isoformat()
                    if row[4]
                    else None
                ),

                "completed_at": (
                    row[5].isoformat()
                    if row[5]
                    else None
                ),

                "repository": row[6]

            })

        return jsonify({

            "status": "SUCCESS",

            "deployments": deployments

        }), 200

    except Exception as error:

        log_message(
            "Deployment history error:",
            error
        )

        return jsonify({

            "status": "FAILED",

            "message": str(error)

        }), 500

    finally:

        if connection:
            connection.close()


# ============================================================
# Get all deployment logs
# ============================================================

@app.route(
    "/api/deployment-logs",
    methods=["GET"]
)
def get_deployment_logs():

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    dl.id,
                    dl.deployment_id,
                    dl.log_message,
                    dl.log_level,
                    dl.created_at,
                    d.commit_id,
                    d.branch,
                    r.name AS repository
                FROM deployment_logs dl
                LEFT JOIN deployments d
                    ON dl.deployment_id = d.id
                LEFT JOIN repositories r
                    ON d.repository_id = r.id
                ORDER BY dl.id DESC
                """
            )

            rows = cursor.fetchall()

        logs = []

        for row in rows:

            logs.append({

                "id": row[0],

                "deployment_id": row[1],

                "log_message": row[2],

                "log_level": row[3],

                "created_at": (
                    row[4].isoformat()
                    if row[4]
                    else None
                ),

                "commit_id": row[5],

                "branch": row[6],

                "repository": row[7]

            })

        return jsonify({

            "status": "SUCCESS",

            "logs": logs,

            "count": len(logs)

        }), 200

    except Exception as error:

        log_message(
            "Deployment log history error:",
            error
        )

        return jsonify({

            "status": "FAILED",

            "message": str(error)

        }), 500

    finally:

        if connection:
            connection.close()


# ============================================================
# Get logs for a specific deployment
# ============================================================

@app.route(
    "/api/deployments/<int:deployment_id>/logs",
    methods=["GET"]
)
def get_deployment_logs_by_id(
    deployment_id
):

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    deployment_id,
                    log_message,
                    log_level,
                    created_at
                FROM deployment_logs
                WHERE deployment_id = %s
                ORDER BY id ASC
                """,
                (deployment_id,)
            )

            rows = cursor.fetchall()

        logs = []

        for row in rows:

            logs.append({

                "id": row[0],

                "deployment_id": row[1],

                "log_message": row[2],

                "log_level": row[3],

                "created_at": (
                    row[4].isoformat()
                    if row[4]
                    else None
                )

            })

        return jsonify({

            "status": "SUCCESS",

            "deployment_id": deployment_id,

            "logs": logs,

            "count": len(logs)

        }), 200

    except Exception as error:

        log_message(
            "Deployment-specific log error:",
            error
        )

        return jsonify({

            "status": "FAILED",

            "message": str(error)

        }), 500

    finally:

        if connection:
            connection.close()


# ============================================================
# Get failure analysis history
# ============================================================

@app.route(
    "/api/failures",
    methods=["GET"]
)
def get_failures():

    connection = None

    try:

        connection = get_db_connection()

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    f.id,
                    f.deployment_id,
                    f.failure_type,
                    f.error_message,
                    f.suggested_fix,
                    f.created_at
                FROM failure_analysis f
                ORDER BY f.id DESC
                """
            )

            rows = cursor.fetchall()

        failures = []

        for row in rows:

            failures.append({

                "id": row[0],

                "deployment_id": row[1],

                "failure_type": row[2],

                "error_message": row[3],

                "suggested_fix": row[4],

                "created_at": (
                    row[5].isoformat()
                    if row[5]
                    else None
                )

            })

        return jsonify({

            "status": "SUCCESS",

            "failures": failures

        }), 200

    except Exception as error:

        log_message(
            "Failure history error:",
            error
        )

        return jsonify({

            "status": "FAILED",

            "message": str(error)

        }), 500

    finally:

        if connection:
            connection.close()


# Additive AI routes: existing API contracts remain unchanged.
try:
    from .ai_intelligence.api import register_ai
except ImportError:
    from ai_intelligence.api import register_ai
register_ai(app, get_db_connection)

try:
    from .ci_callbacks import register_ci_callbacks
except ImportError:
    from ci_callbacks import register_ci_callbacks
register_ci_callbacks(app, get_db_connection)


# ============================================================
# Run Flask application
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true"}
    )
