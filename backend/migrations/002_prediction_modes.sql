ALTER TABLE ai_predictions DROP CONSTRAINT IF EXISTS ai_predictions_repository_run_id_attempt_mode_key;
CREATE UNIQUE INDEX IF NOT EXISTS ai_prediction_shadow_unique ON ai_predictions(repository,run_id,attempt) WHERE mode='shadow';
CREATE UNIQUE INDEX IF NOT EXISTS ai_prediction_backtest_unique ON ai_predictions(repository,run_id,attempt,model_version) WHERE mode='backtest';
CREATE TABLE IF NOT EXISTS ai_shadow_events (
 repository text NOT NULL, run_id bigint NOT NULL, attempt integer NOT NULL,
 observed_at timestamptz NOT NULL DEFAULT now(), decision text NOT NULL, reason text NOT NULL,
 PRIMARY KEY(repository,run_id,attempt)
);
