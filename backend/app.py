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

        print(
            "Database connection error:",
            error
        )

        return jsonify({
            "status": "FAILED",
            "message": "Could not connect to PostgreSQL",
            "error": str(error)
        }), 500

    finally:

        if connection:
            connection.close()


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

    print(
        "\n========== GITHUB WEBHOOK =========="
    )

    print(
        "Event:",
        event
    )

    print(
        "Repository:",
        repo_name
    )

    print(
        "Branch:",
        branch
    )

    print(
        "Pusher:",
        pusher_name
    )

    print(
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

                create_deployment_log(
                    cursor,
                    deployment_id,
                    (
                        f"GitHub {event} event received "
                        f"for {repo_name}"
                    ),
                    "INFO"
                )

                print(
                    "Deployment saved:",
                    deployment_id
                )

        connection.commit()

        print(
            "Database records saved successfully."
        )

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
    # Print commit information
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

                print(
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

                print(
                    "Deployment updated:",
                    deployment_id
                )

                print(
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

                        print(
                            "Failure analysis created for "
                            "deployment:",
                            deployment_id
                        )

                    else:

                        print(
                            "Failure analysis already exists "
                            "for deployment:",
                            deployment_id
                        )

        connection.commit()

        print(
            "CI/CD database update completed."
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "CI/CD database update error:",
            error
        )

    finally:

        if connection:
            connection.close()

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

        print(
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

        print(
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

        print(
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

        print(
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


# ============================================================
# Run Flask application
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )