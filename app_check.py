from flask import Flask, request, jsonify
from flask_cors import CORS
# GitHub webhook test
app = Flask(__name__)
CORS(app)

# ============================================================
# Store the latest GitHub webhook information
# ============================================================

latest_webhook = {
    "event": None,
    "repository": None,
    "branch": None,
    "pusher": None,
    "commits": []
}

# ============================================================
# Store the latest CI/CD pipeline information
# ============================================================

latest_ci = {
    "status": "UNKNOWN",
    "build": "UNKNOWN",
    "tests": "UNKNOWN",
    "docker": "UNKNOWN",
    "workflow": "Cloud-ByteXL CI"
}

# ============================================================
# Home
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "message": "Cloud-ByteXL Backend is running"
    })


# ============================================================
# GitHub Webhook
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_webhook

    data = request.get_json(silent=True) or {}

    event = request.headers.get("X-GitHub-Event")

    repository = data.get("repository", {})
    repo_name = repository.get("name", "Unknown")

    ref = data.get("ref", "Unknown")

    pusher = data.get("pusher", {})
    pusher_name = pusher.get("name", "Unknown")

    commits = data.get("commits", [])

    latest_webhook = {
        "event": event,
        "repository": repo_name,
        "branch": ref,
        "pusher": pusher_name,
        "commits": commits
    }

    print("\n========== GITHUB WEBHOOK ==========")
    print("Event:", event)
    print("Repository:", repo_name)
    print("Branch:", ref)
    print("Pusher:", pusher_name)
    print("Number of commits:", len(commits))
    print("====================================\n")

    return jsonify({
        "message": "GitHub webhook processed successfully",
        "repository": repo_name,
        "branch": ref,
        "pusher": pusher_name,
        "commits": len(commits)
    }), 200


# ============================================================
# Get latest GitHub webhook
# ============================================================

@app.route("/api/github/latest", methods=["GET"])
def get_latest_webhook():
    return jsonify(latest_webhook)


# ============================================================
# Receive CI/CD status
# ============================================================

@app.route("/api/ci/status", methods=["POST"])
def update_ci_status():
    global latest_ci

    data = request.get_json(silent=True) or {}

    latest_ci = {
        "status": data.get("status", "UNKNOWN"),
        "build": data.get("build", "UNKNOWN"),
        "tests": data.get("tests", "UNKNOWN"),
        "docker": data.get("docker", "UNKNOWN"),
        "workflow": data.get(
            "workflow",
            "Cloud-ByteXL CI"
        )
    }

    print("\n========== CI/CD STATUS ==========")
    print("Workflow:", latest_ci["workflow"])
    print("Overall Status:", latest_ci["status"])
    print("Build:", latest_ci["build"])
    print("Tests:", latest_ci["tests"])
    print("Docker:", latest_ci["docker"])
    print("==================================\n")

    return jsonify({
        "message": "CI/CD status updated successfully",
        "ci": latest_ci
    }), 200


# ============================================================
# Get latest CI/CD status
# ============================================================

@app.route("/api/ci/status", methods=["GET"])
def get_ci_status():
    return jsonify(latest_ci)


# ============================================================
# Run Flask application
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )