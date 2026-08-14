from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from datetime import datetime

app = Flask(__name__)
CORS(app)


# ============================================================
# PostgreSQL connection
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "bytexl",
    "user": "postgres",
    "password": "132611"
}


def get_db_connection():
    return psycopg.connect(**DB_CONFIG)


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
# Home
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "message": "Cloud-ByteXL Backend is running"
    })


# ============================================================
# Database connection test
# ============================================================

@app.route("/api/database/test", methods=["GET"])
def database_test():
    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database();")
            database_name = cursor.fetchone()[0]

        connection.close()

        return jsonify({
            "status": "SUCCESS",
            "message": "PostgreSQL connection successful",
            "database": database_name
        }), 200

    except Exception as error:
        print("Database connection error:", error)

        return jsonify({
            "status": "FAILED",
            "message": "Could not connect to PostgreSQL",
            "error": str(error)
        }), 500


# ============================================================
# GitHub Webhook
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_webhook

    data = request.get_json(silent=True) or {}

    # GitHub event
    event = request.headers.get("X-GitHub-Event", "Unknown")

    # Repository
    repository = data.get("repository", {})

    repo_name = repository.get("name", "Unknown")

    repo_url = repository.get(
        "html_url",
        ""
    )

    # Branch
    ref = data.get("ref", "Unknown")

    branch = ref

    if ref.startswith("refs/heads/"):
        branch = ref.replace("refs/heads/", "")

    # Pusher
    pusher = data.get("pusher", {})

    pusher_name = pusher.get(
        "name",
        "Unknown"
    )

    # Commits
    commits = data.get("commits", [])

    # Store latest webhook in memory
    latest_webhook = {
        "event": event,
        "repository": repo_name,
        "branch": branch,
        "pusher": pusher_name,
        "commits": commits
    }

    print("\n========== GITHUB WEBHOOK ==========")
    print("Event:", event)
    print("Repository:", repo_name)
    print("Branch:", branch)
    print("Pusher:", pusher_name)
    print("Number of commits:", len(commits))

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
                        (username, email)
                    VALUES
                        (%s, %s)
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
                        (user_id, name, url, branch)
                    VALUES
                        (%s, %s, %s, %s)
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

                    # ------------------------------------------------
                    # 4. Store deployment log
                    # ------------------------------------------------

                    commit_message = commit.get(
                        "message",
                        "No commit message"
                    )

                    log_message = (
                        f"GitHub {event} received. "
                        f"Repository: {repo_name}. "
                        f"Branch: {branch}. "
                        f"Pusher: {pusher_name}. "
                        f"Commit: {commit_id}. "
                        f"Message: {commit_message}"
                    )

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
                            log_message,
                            "INFO"
                        )
                    )

                    print(
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
                        f"GitHub {event} event received for {repo_name}",
                        "INFO"
                    )
                )

                print(
                    "Deployment saved:",
                    deployment_id
                )

        connection.commit()

        print("Database records saved successfully.")

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Database webhook error:",
            error
        )

    finally:

        if connection:
            connection.close()

    # ========================================================
    # Print webhook information
    # ========================================================

    for commit in commits:

        print(
            "Commit:",
            commit.get("id")
        )

        print(
            "Message:",
            commit.get("message")
        )

        print(
            "Author:",
            commit.get(
                "author",
                {}
            ).get(
                "name"
            )
        )

        print(
            "Added:",
            commit.get(
                "added",
                []
            )
        )

        print(
            "Modified:",
            commit.get(
                "modified",
                []
            )
        )

        print(
            "Removed:",
            commit.get(
                "removed",
                []
            )
        )

    print(
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

@app.route("/api/github/latest", methods=["GET"])
def get_latest_webhook():

    return jsonify(
        latest_webhook
    )


# ============================================================
# Receive CI/CD status
# ============================================================

@app.route("/api/ci/status", methods=["POST"])
def update_ci_status():

    global latest_ci

    data = request.get_json(
        silent=True
    ) or {}

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

    print(
        "\n========== CI/CD STATUS =========="
    )

    print(
        "Workflow:",
        latest_ci["workflow"]
    )

    print(
        "Overall Status:",
        latest_ci["status"]
    )

    print(
        "Build:",
        latest_ci["build"]
    )

    print(
        "Tests:",
        latest_ci["tests"]
    )

    print(
        "Docker:",
        latest_ci["docker"]
    )

    print(
        "==================================\n"
    )

    return jsonify({
        "message": "CI/CD status updated successfully",
        "ci": latest_ci
    }), 200


# ============================================================
# Get latest CI/CD status
# ============================================================

@app.route("/api/ci/status", methods=["GET"])
def get_ci_status():

    return jsonify(
        latest_ci
    )


# ============================================================
# Get database statistics
# ============================================================

@app.route("/api/database/stats", methods=["GET"])
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

        print(
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
# Run Flask application
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )