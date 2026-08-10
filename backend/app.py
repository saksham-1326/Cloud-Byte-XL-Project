from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({
        "message": "Cloud-ByteXL Backend is running"
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    # GitHub event type
    event = request.headers.get("X-GitHub-Event")

    # Repository information
    repository = data.get("repository", {})
    repo_name = repository.get("name", "Unknown")

    # Branch information
    ref = data.get("ref", "Unknown")

    # Pusher information
    pusher = data.get("pusher", {})
    pusher_name = pusher.get("name", "Unknown")

    # Commit information
    commits = data.get("commits", [])

    print("\n========== GITHUB WEBHOOK ==========")
    print("Event:", event)
    print("Repository:", repo_name)
    print("Branch:", ref)
    print("Pusher:", pusher_name)
    print("Number of commits:", len(commits))

    for commit in commits:
        print("Commit:", commit.get("id"))
        print("Message:", commit.get("message"))
        print("Author:", commit.get("author", {}).get("name"))
        print("Added:", commit.get("added", []))
        print("Modified:", commit.get("modified", []))
        print("Removed:", commit.get("removed", []))

    print("====================================\n")

    return jsonify({
        "message": "GitHub webhook processed successfully",
        "repository": repo_name,
        "branch": ref,
        "pusher": pusher_name,
        "commits": len(commits)
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)