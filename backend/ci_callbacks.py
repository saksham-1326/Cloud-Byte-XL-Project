"""Authenticated, explicitly bound CI callbacks. No GitHub or LLM requests."""
import hashlib
import hmac
import json
import os
import re
import uuid
from urllib.parse import urlsplit

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge


class CallbackError(Exception):
    def __init__(self, code, message, status=409):
        self.code, self.message, self.status = code, message, status


def repository_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        raise CallbackError('invalid_payload', 'Invalid repository identity.', 400)
    return value.lower()


def validate_payload(data):
    fields = {'repository', 'run_id', 'attempt', 'commit_sha', 'delivery_id',
              'workflow', 'status', 'build', 'tests', 'docker'}
    if not isinstance(data, dict) or set(data) != fields:
        raise CallbackError('invalid_payload', 'The complete callback field set is required.', 400)
    data = dict(data)
    data['repository'] = repository_name(data['repository'])
    for field, maximum in [('run_id', 2**63-1), ('attempt', 2**31-1)]:
        if type(data[field]) is not int or not 1 <= data[field] <= maximum:
            raise CallbackError('invalid_payload', 'Run ID and attempt must be positive integers.', 400)
    if not isinstance(data['commit_sha'], str) or not re.fullmatch('[0-9a-f]{40}', data['commit_sha']):
        raise CallbackError('invalid_payload', 'A full lowercase commit SHA is required.', 400)
    try:
        if not isinstance(data['delivery_id'], str): raise ValueError()
        data['delivery_id'] = str(uuid.UUID(data['delivery_id']))
    except ValueError:
        raise CallbackError('invalid_payload', 'A UUID delivery ID is required.', 400) from None
    if not isinstance(data['workflow'], str) or not 1 <= len(data['workflow']) <= 160 or any(ord(c) < 32 for c in data['workflow']):
        raise CallbackError('invalid_payload', 'A bounded workflow name is required.', 400)
    try:
        data['workflow'].encode('utf-8')
    except UnicodeEncodeError:
        raise CallbackError('invalid_payload', 'Workflow name must contain valid Unicode.', 400) from None
    if not isinstance(data['status'], str) or data['status'] not in {'SUCCESS', 'FAILURE', 'CANCELLED'}:
        raise CallbackError('invalid_payload', 'Invalid pipeline status.', 400)
    for field in ['build', 'tests', 'docker']:
        if not isinstance(data[field], str) or data[field] not in {'PASSED', 'FAILED', 'SKIPPED', 'CANCELLED', 'FAILED_OR_SKIPPED'}:
            raise CallbackError('invalid_payload', 'Invalid stage status.', 400)
    if data['status'] == 'SUCCESS' and any(data[f] != 'PASSED' for f in ['build', 'tests', 'docker']):
        raise CallbackError('invalid_payload', 'Successful pipelines require passing stages.', 400)
    return data


def _lock(cursor, key):
    cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (key,))


def _deployment(cursor, deployment_id, repository, commit_sha):
    cursor.execute('''SELECT d.id,d.commit_id,r.url FROM deployments d
        JOIN repositories r ON r.id=d.repository_id WHERE d.id=%s FOR UPDATE OF d,r''', (deployment_id,))
    row = cursor.fetchone()
    if not row:
        raise CallbackError('deployment_not_found', 'The associated deployment does not exist.', 404)
    url = urlsplit(row['url'])
    path = url.path.strip('/')
    if path.endswith('.git'): path = path[:-4]
    if url.hostname != 'github.com' or path.lower() != repository or row['commit_id'] != commit_sha:
        raise CallbackError('association_mismatch', 'Deployment repository or commit does not match.')


def register_execution(connect, repository, run_id, attempt, commit_sha, deployment_id):
    """Trusted local administration only: binds an already-created deployment.

    No callback can create or change this association. A rerun must be registered
    explicitly before its callback is accepted. This function never changes a
    deployment's result.
    """
    data = validate_payload(dict(repository=repository, run_id=run_id, attempt=attempt,
        commit_sha=commit_sha, delivery_id=str(uuid.uuid4()), workflow='registration',
        status='SUCCESS', build='PASSED', tests='PASSED', docker='PASSED'))
    if type(deployment_id) is not int or not 1 <= deployment_id <= 2**63-1:
        raise CallbackError('invalid_payload', 'A positive deployment ID is required.', 400)
    with connect() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SET LOCAL lock_timeout='5s'")
            cursor.execute("SET LOCAL statement_timeout='10s'")
            _lock(cursor, f"ci:run:{data['repository']}:{run_id}")
            cursor.execute('SELECT * FROM ci_callback_executions WHERE repository=%s AND run_id=%s FOR UPDATE', (data['repository'], run_id))
            old = cursor.fetchone()
            if old and (old['deployment_id'] != deployment_id or old['commit_sha'] != commit_sha):
                raise CallbackError('association_mismatch', 'A run cannot be rebound to another deployment or commit.')
            if old and attempt < old['current_attempt']:
                raise CallbackError('stale_attempt', 'Cannot register an older attempt.')
            _deployment(cursor, deployment_id, data['repository'], commit_sha)
            cursor.execute('''INSERT INTO ci_callback_executions(repository,run_id,deployment_id,commit_sha,current_attempt)
                VALUES(%s,%s,%s,%s,%s) ON CONFLICT(repository,run_id) DO UPDATE
                SET current_attempt=excluded.current_attempt,updated_at=now()''',
                (data['repository'], run_id, deployment_id, commit_sha, attempt))


def persist_callback(connect, data):
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    # The response is returned only after the connection context commits. A
    # commit-time failure propagates to the endpoint and never acknowledges data.
    with connect() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SET LOCAL lock_timeout='5s'")
            cursor.execute("SET LOCAL statement_timeout='10s'")
            _lock(cursor, 'ci:delivery:' + data['delivery_id'])
            cursor.execute('SELECT * FROM ci_callback_receipts WHERE delivery_id=%s', (data['delivery_id'],))
            receipt = cursor.fetchone()
            if receipt:
                if receipt['payload_sha256'] != digest:
                    raise CallbackError('delivery_conflict', 'Delivery ID was already used for a different payload.')
                result = acknowledgment(receipt, duplicate=True)
            else:
                cursor.execute('SELECT * FROM ci_callback_executions WHERE repository=%s AND run_id=%s FOR UPDATE', (data['repository'], data['run_id']))
                execution = cursor.fetchone()
                if not execution:
                    raise CallbackError('execution_not_found', 'Workflow execution has not been explicitly registered.', 404)
                if execution['commit_sha'] != data['commit_sha']:
                    raise CallbackError('association_mismatch', 'Commit does not match the registered execution.')
                if execution['current_attempt'] != data['attempt']:
                    raise CallbackError('stale_attempt' if data['attempt'] < execution['current_attempt'] else 'unregistered_attempt', 'Only the registered current attempt can update this execution.')
                cursor.execute('SELECT id FROM ci_callback_receipts WHERE repository=%s AND run_id=%s AND attempt=%s', (data['repository'], data['run_id'], data['attempt']))
                if cursor.fetchone():
                    raise CallbackError('attempt_conflict', 'This attempt already has a terminal receipt; reuse its delivery ID.')
                _deployment(cursor, execution['deployment_id'], data['repository'], data['commit_sha'])
                cursor.execute('UPDATE deployments SET status=%s,completed_at=now() WHERE id=%s',
                    ('FAILED' if data['status'] == 'FAILURE' else data['status'], execution['deployment_id']))
                receipt_id = str(uuid.uuid4())
                cursor.execute('''INSERT INTO ci_callback_receipts(id,delivery_id,repository,run_id,attempt,deployment_id,commit_sha,payload_sha256,payload)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
                    (receipt_id, data['delivery_id'], data['repository'], data['run_id'], data['attempt'], execution['deployment_id'], data['commit_sha'], digest, Jsonb(data)))
                result = acknowledgment(cursor.fetchone(), duplicate=False)
    return result


def acknowledgment(receipt, duplicate=False):
    return dict(status='SUCCESS', persisted=True, receipt_id=str(receipt['id']),
        delivery_id=str(receipt['delivery_id']), repository=receipt['repository'],
        run_id=receipt['run_id'], attempt=receipt['attempt'], commit_sha=receipt['commit_sha'],
        deployment_id=receipt['deployment_id'], payload_sha256=receipt['payload_sha256'],
        duplicate=duplicate)


def register_ci_callbacks(app, connect):
    bp = Blueprint('ci_callbacks', __name__, url_prefix='/api/ci/v1')

    @bp.before_request
    def authenticate():
        request.max_content_length = 16384
        token = os.getenv('CI_STATUS_TOKEN', '')
        if not token:
            return jsonify(status='FAILED', code='not_configured', message='Durable callbacks are disabled until authentication is configured.'), 503
        supplied = request.headers.get('Authorization', '')
        if not hmac.compare_digest(supplied.encode(), ('Bearer ' + token).encode()):
            return jsonify(status='FAILED', code='unauthorized', message='Callback authentication required.'), 401
        if request.content_length is not None and request.content_length > 16384:
            return jsonify(status='FAILED', code='payload_too_large', message='Callback body exceeds the limit.'), 413

    @bp.errorhandler(CallbackError)
    def callback_error(error):
        return jsonify(status='FAILED', code=error.code, message=error.message), error.status

    @bp.errorhandler(RequestEntityTooLarge)
    def oversized(error):
        return jsonify(status='FAILED', code='payload_too_large', message='Callback body exceeds the limit.'), 413

    @bp.errorhandler(psycopg.Error)
    def database_error(error):
        # Log only the exception type, never SQL, connection details or payloads.
        app.logger.warning('Durable CI callback database failure (%s)', type(error).__name__)
        return jsonify(status='FAILED', code='database_unavailable', persisted=False,
                       message='Callback was not acknowledged. Retry the same delivery ID after database recovery.'), 503

    def allowed(repository):
        allowed_repositories = {r.strip().lower() for r in os.getenv('CI_ALLOWED_REPOSITORIES', '').split(',') if r.strip()}
        if repository not in allowed_repositories:
            raise CallbackError('repository_forbidden', 'Repository is not authorized for callbacks.', 403)

    @bp.post('/status')
    def status():
        if not request.is_json:
            raise CallbackError('invalid_payload', 'JSON content type is required.', 415)
        data = validate_payload(request.get_json(silent=True))
        allowed(data['repository'])
        return jsonify(persist_callback(connect, data)), 200

    @bp.get('/receipts/<receipt_id>')
    def receipt(receipt_id):
        repository = repository_name(request.args.get('repository'))
        allowed(repository)
        try: receipt_id = str(uuid.UUID(receipt_id))
        except ValueError: raise CallbackError('invalid_payload', 'Invalid receipt ID.', 400) from None
        with connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('SELECT * FROM ci_callback_receipts WHERE id=%s AND repository=%s', (receipt_id, repository))
                row = cursor.fetchone()
                if not row: raise CallbackError('receipt_not_found', 'Receipt not found.', 404)
                result = acknowledgment(row)
        return jsonify(result), 200

    app.register_blueprint(bp)
