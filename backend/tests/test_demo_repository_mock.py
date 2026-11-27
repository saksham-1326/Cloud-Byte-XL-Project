"""Mocked hosted read-only repository routing; no external calls or DB writes."""
from flask import Flask, jsonify, request

from backend.hosting import register_public_demo, validate_environment


DEMO = "saksham-1326/cloud-byte-xl-project"


def create_mock_app():
    app = Flask(__name__)
    register_public_demo(app, lambda: None, {DEMO})

    @app.post("/api/github/repository")
    def analyze():
        return jsonify(
            status="SUCCESS",
            repository={
                "fullName":"saksham-1326/Cloud-Byte-XL-Project",
                "url":"https://github.com/saksham-1326/Cloud-Byte-XL-Project",
            },
            analysis={"overall":75,"issues":[]},
            files=[],
            databaseWarning="Public demo analysis is read-only; this repository was not saved to PostgreSQL.",
        )

    @app.post("/api/ai/v1/train")
    def training():
        raise AssertionError("Public visitor must never initiate training")

    return app


def test_exact_public_demo_repository_authorized_without_write():
    client=create_mock_app().test_client()
    for url in [
        "https://github.com/saksham-1326/Cloud-Byte-XL-Project",
        "https://github.com/SAKSHAM-1326/CLOUD-BYTE-XL-PROJECT",
    ]:
        response=client.post("/api/github/repository",json={"url":url})
        assert response.status_code==200
        assert response.json["status"]=="SUCCESS"
        assert "read-only" in response.json["databaseWarning"]


def test_other_repositories_refused_and_malformed_urls_refused():
    client=create_mock_app().test_client()
    for url in ["https://github.com/other/repo","https://github.com/other/Cloud-Byte-XL-Project"]:
        resp=client.post("/api/github/repository",json={"url":url})
        assert resp.status_code==403
        assert resp.json["message"]=="Repository is not allowlisted."
    for url in ["http://github.com/saksham-1326/Cloud-Byte-XL-Project",
                "https://github.com/saksham-1326/Cloud-Byte-XL-Project?secret=x",
                "https://example.com/saksham-1326/Cloud-Byte-XL-Project"]:
        assert client.post("/api/github/repository",json={"url":url}).status_code==400


def test_public_mutations_remain_blocked_after_allowlist_fix():
    client=create_mock_app().test_client()
    resp=client.post("/api/ai/v1/train",json={"repository":DEMO})
    assert resp.status_code==403
    assert resp.json["status"]=="FAILED"


def test_deployed_expected_allowlist_normalizes_exact_repo():
    config={
        "PUBLIC_DEMO_MODE":"1",
        "RCA_PROVIDER":"none",
        "CI_CALLBACK_ENABLED":"0",
        "FLASK_DEBUG":"0",
        "CORS_ORIGINS":"https://cloud-bytexl.vercel.app",
        "AI_ALLOWED_REPOSITORIES":DEMO,
        "DATABASE_URL":"postgresql://reader:test-password@db.example.invalid/neondb?sslmode=require",
    }
    assert validate_environment(config)=={DEMO}
