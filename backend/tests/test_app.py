from backend.app import app


def test_home():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_repository_invalid_payload_has_cors():
    client = app.test_client()
    for payload in ({"url": "invalid"}, ["invalid"], {}):
        response = client.post("/api/github/repository", json=payload,
                               headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 400
        assert response.json["status"] == "FAILED"
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_repository_preflight():
    response = app.test_client().options("/api/github/repository", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "POST" in response.headers["Access-Control-Allow-Methods"]


def test_repository_internal_failure_is_safe_json(monkeypatch):
    import importlib
    module = importlib.import_module("backend.app")

    def fail(*args):
        raise RuntimeError("private diagnostic must stay in server logs")

    monkeypatch.setattr(module, "github_request", fail)
    response = app.test_client().post("/api/github/repository",
        json={"url": "https://github.com/octocat/Hello-World"},
        headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.json["status"] == "FAILED"
    assert "private diagnostic" not in response.get_data(as_text=True)
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_analysis_does_not_write_to_broken_stdout(monkeypatch):
    import importlib
    import builtins
    module = importlib.import_module("backend.app")

    def broken_print(*args, **kwargs):
        raise OSError(22, "Invalid argument")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "print", broken_print)
        result = module.analyze_repository("/repos/octocat/Hello-World", "master", [], False, "test-sha")
    assert "overall" in result
