ALTER TABLE ai_features ADD COLUMN IF NOT EXISTS feature_version text NOT NULL DEFAULT 'prequeue-v1';
ALTER TABLE ai_features DROP CONSTRAINT IF EXISTS ai_features_pkey;
ALTER TABLE ai_features ADD PRIMARY KEY(repository,run_id,attempt,feature_version);
ALTER TABLE ai_predictions ADD CONSTRAINT ai_prediction_class_binary CHECK(predicted_class IN (0,1));
