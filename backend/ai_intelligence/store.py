"""Parameterized persistence. Logs and snapshots have already been redacted."""
import uuid
from datetime import datetime, timezone
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value,str) and value else value


def label(conclusion):
    return {"success":0,"failure":1}.get(conclusion)


class Store:
    def __init__(self, connect):
        self.connect = connect

    def query(self, sql, args=(), one=False):
        with self.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql,args)
                if cursor.description:
                    return cursor.fetchone() if one else cursor.fetchall()

    def runs(self, repo):
        return self.query("SELECT * FROM ai_runs WHERE repository=%s ORDER BY created_at,run_id,attempt", (repo,))

    def run(self, repo, run_id, attempt):
        return self.query("SELECT * FROM ai_runs WHERE repository=%s AND run_id=%s AND attempt=%s",(repo,run_id,attempt),True)

    def save_run(self, repo, run, jobs):
        attempt=run.get("run_attempt",1)
        completion=max((j.get("completed_at") for j in jobs if j.get("completed_at")),default=None) if run["status"]=="completed" else None
        # Allowlist GitHub fields; exclude actor credentials and unnecessary metadata.
        payload={k:run.get(k) for k in ("id","run_attempt","run_number","name","workflow_id","head_sha","head_branch","event","created_at","run_started_at","updated_at","status","conclusion","path","html_url","display_title","repository_id")}
        payload["completed_at"]=completion
        start=timestamp(run.get("run_started_at"))
        payload["duration_seconds"] = max(0,(timestamp(completion)-start).total_seconds()) if completion and start else None
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO ai_runs(repository,run_id,attempt,workflow_id,commit_sha,created_at,started_at,completed_at,status,conclusion,payload)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(repository,run_id,attempt) DO UPDATE SET
                    started_at=excluded.started_at,completed_at=excluded.completed_at,status=excluded.status,conclusion=excluded.conclusion,payload=excluded.payload,synced_at=now()
                    WHERE ai_runs.commit_sha=excluded.commit_sha AND NOT (ai_runs.status='completed' AND excluded.status<>'completed') RETURNING commit_sha""",
                    (repo,run["id"],attempt,run["workflow_id"],run["head_sha"],timestamp(run["created_at"]),start,timestamp(completion),run["status"],run.get("conclusion"),Jsonb(payload)))
                if not cur.fetchone():
                    return  # Stale state or inconsistent SHA: do not write jobs/outcomes.
                for job in jobs:
                    text=job.get("log_text")
                    body={k:job.get(k) for k in ("id","name","status","conclusion","started_at","completed_at","steps")}
                    cur.execute("""INSERT INTO ai_jobs(repository,run_id,attempt,job_id,payload,log_text,log_status,log_reference) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(repository,run_id,attempt,job_id) DO UPDATE SET payload=excluded.payload,
                        log_text=COALESCE(excluded.log_text,ai_jobs.log_text),log_status=CASE WHEN excluded.log_text IS NULL AND ai_jobs.log_text IS NOT NULL THEN ai_jobs.log_status ELSE excluded.log_status END""",
                        (repo,run["id"],attempt,job["id"],Jsonb(body),text,job.get("log_status","not_fetched"),f"github:actions/jobs/{job['id']}/logs"))
                    for step in job.get("steps",[]):
                        cur.execute("""INSERT INTO ai_steps VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(repository,run_id,attempt,job_id,step_number) DO UPDATE SET payload=excluded.payload""",(repo,run["id"],attempt,job["id"],step["number"],Jsonb(step)))
                if run["status"]=="completed" and run.get("conclusion"):
                    cur.execute("""INSERT INTO ai_outcomes(repository,run_id,attempt,conclusion,label) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(repository,run_id,attempt) DO UPDATE SET conclusion=excluded.conclusion,label=excluded.label,observed_at=now()""",(repo,run["id"],attempt,run["conclusion"],label(run["conclusion"])))
                    actual_start=min((timestamp(j["started_at"]) for j in jobs if j.get("started_at")),default=start)
                    cur.execute("""UPDATE ai_predictions SET verification_status=CASE
                        WHEN %s::integer IS NULL THEN 'excluded_outcome'
                        WHEN %s::timestamptz IS NULL THEN 'unverifiable_timing'
                        WHEN predicted_at >= %s::timestamptz THEN 'invalid_timing'
                        ELSE 'matched' END WHERE repository=%s AND run_id=%s AND attempt=%s AND mode='shadow'""",
                        (label(run["conclusion"]),actual_start,actual_start,repo,run["id"],attempt))

    def jobs(self, repo, run_id, attempt):
        return self.query("SELECT * FROM ai_jobs WHERE repository=%s AND run_id=%s AND attempt=%s ORDER BY (payload->>'started_at'),job_id",(repo,run_id,attempt))

    def snapshot(self, repo, sha, path):
        row=self.query("SELECT payload FROM ai_snapshots WHERE repository=%s AND commit_sha=%s AND workflow_path=%s",(repo,sha,path),True)
        return row["payload"] if row else None

    def save_snapshot(self, repo, snapshot):
        self.query("INSERT INTO ai_snapshots(repository,commit_sha,workflow_path,payload) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",(repo,snapshot["sha"],snapshot["workflow_path"],Jsonb(snapshot)))

    def features(self, repo, run, values, provenance, at):
        self.query("""INSERT INTO ai_features(repository,run_id,attempt,prediction_time,payload,provenance,feature_version) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",(repo,run["run_id"],run["attempt"],at,Jsonb(values),Jsonb(provenance),provenance['feature_version']))

    def models(self, repo):
        return self.query("SELECT * FROM ai_models WHERE repository=%s ORDER BY created_at DESC",(repo,))

    def model(self, repo, version, result, artifact=None, digest=None):
        self.query("INSERT INTO ai_models(version,repository,status,trained_through,artifact_path,artifact_sha256,metrics,feature_names) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(version,repo,result["status"],result.get("trained_through"),artifact,digest,Jsonb(result),Jsonb(result.get("feature_names",[]))))

    def reports(self, repo):
        return self.query("SELECT * FROM ai_rca_reports WHERE repository=%s ORDER BY created_at DESC LIMIT 100",(repo,))

    def save_report(self, repo, run_id, attempt, report):
        report_id=str(uuid.uuid4())
        self.query("INSERT INTO ai_rca_reports(id,repository,run_id,attempt,model_version,report) VALUES(%s,%s,%s,%s,%s,%s)",(report_id,repo,run_id,attempt,report["model_version"],Jsonb(report)))
        return report_id

    def predictions(self, repo):
        return self.query("""SELECT p.*,o.conclusion actual_conclusion,o.label actual_label,(p.predicted_class=o.label) correct
            FROM ai_predictions p LEFT JOIN ai_outcomes o USING(repository,run_id,attempt) WHERE p.repository=%s ORDER BY predicted_at DESC LIMIT 500""",(repo,))

    def predict(self, repo, run, version, values, probability, threshold, at):
        return self.query("""INSERT INTO ai_predictions(id,repository,run_id,attempt,model_version,predicted_at,feature_snapshot,probability,threshold,predicted_class,mode)
            SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'shadow'
            FROM ai_runs r JOIN ai_models m ON m.version=%s AND m.repository=r.repository
            WHERE r.repository=%s AND r.run_id=%s AND r.attempt=%s
              AND r.commit_sha=%s AND r.status='queued' AND r.conclusion IS NULL
            FOR UPDATE OF r
            ON CONFLICT DO NOTHING RETURNING id""",
            (str(uuid.uuid4()),repo,run["id"],run.get("run_attempt",1),version,at,Jsonb(values),probability,threshold,int(probability>=threshold),
             version,repo,run["id"],run.get("run_attempt",1),run['head_sha']),True)

    def enqueue(self, repo, kind, payload):
        task_id=str(uuid.uuid4())
        row=self.query("""INSERT INTO ai_tasks(id,repository,kind,payload) VALUES(%s,%s,%s,%s) ON CONFLICT(repository,kind) WHERE status IN ('queued','running') DO NOTHING RETURNING id""",(task_id,repo,kind,Jsonb(payload)),True)
        if row:
            return str(row["id"])
        return str(self.query("SELECT id FROM ai_tasks WHERE repository=%s AND kind=%s AND status IN ('queued','running')",(repo,kind),True)["id"])
