-- Legacy deployments/repositories are owned by the existing application.
-- Registration and delivery lock and validate those rows explicitly. No legacy
-- schema is created or changed by this additive migration.
CREATE TABLE IF NOT EXISTS ci_callback_executions (
 repository text NOT NULL,
 run_id bigint NOT NULL CHECK(run_id>0),
 deployment_id bigint NOT NULL UNIQUE,
 commit_sha text NOT NULL CHECK(commit_sha ~ '^[0-9a-f]{40}$'),
 current_attempt integer NOT NULL CHECK(current_attempt>0),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(repository,run_id),
 UNIQUE(repository,run_id,deployment_id,commit_sha)
);
CREATE TABLE IF NOT EXISTS ci_callback_receipts (
 id uuid PRIMARY KEY,
 delivery_id uuid NOT NULL UNIQUE,
 repository text NOT NULL,
 run_id bigint NOT NULL,
 attempt integer NOT NULL CHECK(attempt>0),
 deployment_id bigint NOT NULL,
 commit_sha text NOT NULL CHECK(commit_sha ~ '^[0-9a-f]{40}$'),
 payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 payload jsonb NOT NULL,
 persisted_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(repository,run_id,attempt),
 FOREIGN KEY(repository,run_id,deployment_id,commit_sha)
 REFERENCES ci_callback_executions(repository,run_id,deployment_id,commit_sha)
);
