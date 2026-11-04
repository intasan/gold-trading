CREATE TABLE IF NOT EXISTS observations (
 source TEXT NOT NULL,
 series TEXT NOT NULL,
 frequency TEXT NOT NULL,
 observed_at TEXT NOT NULL,
 value DOUBLE PRECISION NOT NULL CHECK (value > 0),
 unit TEXT NOT NULL,
 retrieved_at TEXT NOT NULL,
 raw_sha256 TEXT NOT NULL,
 PRIMARY KEY (source, series, frequency, observed_at)
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
 id TEXT PRIMARY KEY,
 started_at TEXT NOT NULL,
 finished_at TEXT NOT NULL,
 status TEXT NOT NULL,
 details_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_runs (
 run_id TEXT NOT NULL REFERENCES pipeline_runs(id),
 source TEXT NOT NULL,
 status TEXT NOT NULL,
 extracted_rows INTEGER NOT NULL,
 inserted_rows INTEGER NOT NULL,
 existing_rows INTEGER NOT NULL,
 error TEXT,
 provenance_json TEXT NOT NULL,
 PRIMARY KEY (run_id, source)
);
CREATE TABLE IF NOT EXISTS model_runs (
 id TEXT PRIMARY KEY,
 created_at TEXT NOT NULL,
 status TEXT NOT NULL,
 result_json TEXT NOT NULL
);
