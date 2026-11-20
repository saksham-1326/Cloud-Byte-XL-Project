CREATE TABLE IF NOT EXISTS ai_rca_reviews (
 report_id uuid NOT NULL REFERENCES ai_rca_reports(id) ON DELETE CASCADE,
 reviewer text NOT NULL CHECK(length(reviewer)>0 AND length(reviewer)<=80),
 reviewed_at timestamptz NOT NULL DEFAULT now(), review jsonb NOT NULL,
 PRIMARY KEY(report_id,reviewer)
);
