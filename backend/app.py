from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Store the latest GitHub webhook information
latest_webhook = {
    "event": None,
    "repository": None,
    "branch": None,
    "pusher": None,
    "commits": []
}


@app.route("/")
def home():
    return jsonify({
        "message": "Cloud-ByteXL Backend is running"
    })


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


@app.route("/api/github/latest", methods=["GET"])
def get_latest_webhook():
    return jsonify(latest_webhook)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)