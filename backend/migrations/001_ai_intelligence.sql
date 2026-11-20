CREATE TABLE IF NOT EXISTS ai_runs (
 repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL CHECK(attempt>0),
 workflow_id bigint NOT NULL, commit_sha text NOT NULL, created_at timestamptz NOT NULL,
 started_at timestamptz, completed_at timestamptz, status text NOT NULL, conclusion text,
 payload jsonb NOT NULL, synced_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(repository,run_id,attempt)
);
CREATE INDEX IF NOT EXISTS ai_runs_history ON ai_runs(repository,workflow_id,created_at);
CREATE INDEX IF NOT EXISTS ai_runs_commit ON ai_runs(repository,commit_sha);
CREATE TABLE IF NOT EXISTS ai_jobs (
 repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL, job_id bigint NOT NULL,
 payload jsonb NOT NULL, log_text text, log_status text NOT NULL, log_reference text NOT NULL,
 PRIMARY KEY(repository,run_id,attempt,job_id),
 FOREIGN KEY(repository,run_id,attempt) REFERENCES ai_runs ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS ai_steps (
 repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL, job_id bigint NOT NULL,
 step_number integer NOT NULL, payload jsonb NOT NULL,
 PRIMARY KEY(repository,run_id,attempt,job_id,step_number),
 FOREIGN KEY(repository,run_id,attempt,job_id) REFERENCES ai_jobs ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS ai_snapshots (
 repository text NOT NULL, commit_sha text NOT NULL, workflow_path text NOT NULL,
 payload jsonb NOT NULL, fetched_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(repository,commit_sha,workflow_path)
);
CREATE TABLE IF NOT EXISTS ai_features (
 repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL,
 prediction_time timestamptz NOT NULL, payload jsonb NOT NULL, provenance jsonb NOT NULL,
 PRIMARY KEY(repository,run_id,attempt),
 FOREIGN KEY(repository,run_id,attempt) REFERENCES ai_runs ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS ai_models (
 version uuid PRIMARY KEY, repository text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL, trained_through timestamptz, artifact_path text, artifact_sha256 text,
 metrics jsonb NOT NULL, feature_names jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS ai_models_latest ON ai_models(repository,created_at DESC);
CREATE TABLE IF NOT EXISTS ai_predictions (
 id uuid PRIMARY KEY, repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL,
 model_version uuid NOT NULL REFERENCES ai_models(version), predicted_at timestamptz NOT NULL,
 feature_snapshot jsonb NOT NULL, probability double precision NOT NULL CHECK(probability>=0 AND probability<=1),
 threshold double precision NOT NULL CHECK(threshold>=0 AND threshold<=1), predicted_class integer NOT NULL,
 mode text NOT NULL CHECK(mode IN ('shadow','backtest')), verification_status text NOT NULL DEFAULT 'pending',
 UNIQUE(repository,run_id,attempt,mode),
 FOREIGN KEY(repository,run_id,attempt) REFERENCES ai_runs ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS ai_outcomes (
 repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL,
 conclusion text NOT NULL, label integer, observed_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(repository,run_id,attempt), FOREIGN KEY(repository,run_id,attempt) REFERENCES ai_runs ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS ai_rca_reports (
 id uuid PRIMARY KEY, repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), model_version text NOT NULL, report jsonb NOT NULL,
 verification_status text NOT NULL DEFAULT 'unverified', review jsonb,
 FOREIGN KEY(repository,run_id,attempt) REFERENCES ai_runs ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ai_rca_run ON ai_rca_reports(repository,run_id,attempt,created_at DESC);
CREATE TABLE IF NOT EXISTS ai_tasks (
 id uuid PRIMARY KEY, repository text NOT NULL, kind text NOT NULL,
 status text NOT NULL DEFAULT 'queued', payload jsonb NOT NULL, result jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ai_tasks_one_active ON ai_tasks(repository,kind) WHERE status IN ('queued','running');
