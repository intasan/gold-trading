# Evidence index — new real-source implementation

- live-refresh.txt: actual provider calls, source timestamps, response hashes, inserted/existing counts and model outcome.
- database-summary.json: SQL coverage/counts from the loaded SQLite database.
- model-evaluation.json: actual 36-period expanding-window predictions and errors, including the inferior candidate result and withheld forecast.
- runtime-verification.json / .txt: real-row CSV/SQL equality, idempotent replay and persistence after reopening an isolated SQLite DB.
- unit-tests.txt: actual test stdout, including labeled fault injection on copies of recorded observations.
- api-tests.json / .txt: actual Python API with recorded real rows in an isolated test database; public endpoints work and private paths are rejected.
- Browser/desktop/mobile captures and browser QA are recorded after opening the implemented app. They are real screenshots, not generated UI images.

Historical source-audit.json describes the concept-only baseline. Do not use it as the status of the new implementation. No original Airflow execution, original PostgreSQL row count, or old ML score has been reused as a new result.
