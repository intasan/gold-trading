# Runtime acceptance — 4 November 2026

## Verified execution

Integration workflow: https://github.com/intasan/gold-trading/actions/runs/41788294519
Scheduled refresh first execution: https://github.com/intasan/gold-trading/actions/runs/41788601769

- Docker builds: pipeline/dashboard Python 3.12 images and Apache Airflow 2.10.5 Python 3.12 image passed on a GitHub-hosted Ubuntu runner.
- PostgreSQL 16.15: real recorded 2,406 rows loaded twice; second replay inserted 0, retained 2,406. Reopen and actual PostgreSQL container restart retained all rows.
- Actual provider extraction into PostgreSQL passed for World Bank, Gold API XAU/XAG and Frankfurter.
- Read-only API returned HTTP 200, pipeline success and 2,412 rows after fresh ingestion.
- Actual Airflow DAG CLI execution completed extract_validate_load, evaluate_if_sufficient_history and export_snapshot successfully. This is real task execution through `airflow dags test`, not a syntax-only test.
- Airflow metadata is isolated SQLite in the test container; business observations use PostgreSQL. There is no permanently hosted Airflow web UI or scheduler service.
- Daily automation is GitHub Actions cron 06:17 UTC / 13:17 Asia/Bangkok. It creates ephemeral Docker services, seeds PostgreSQL from committed real observations, runs the DAG, validates all-source success and exports back to Git. Each run rebuilds the analytical database; it is not a persistent production PostgreSQL deployment.
- First automated-path run collected new data, committed it and requested the existing GitHub Pages rebuild successfully. Cron configuration is enabled; future trigger timing has not yet been observed. GitHub scheduled jobs may be delayed.
- Exports dated 4 November 2026 include 802 World Bank monthly observations per metal through October 2026; total 2,412 observations across separately labeled frequencies.

## Evidence

Raw integration artifact files: `evidence/runtime/`. Full API-downloaded job log: `evidence/docker-postgres-airflow-job.log`. Previous failed run 41787911442 is retained on GitHub: API readiness probe raced startup; retry-all-errors and strict Bash pipefail corrected the test harness. No failed test is presented as a success.

## Model acceptance

Initial HGB MAE on the refreshed export: 138.14 vs naive 135.47 USD/troy oz (November 2023–October 2026). No point forecast is published. Broader pre-holdout model selection is recorded in `evidence/model-research.json`; candidate configurations are selected by validation MAE before inspecting the final 36 months. The historical holdout has been examined previously, so this is reused retrospective evidence, not an untouched prospective test. Passing predictive quality cannot be guaranteed by repeatedly tuning a known test set.

## Image provenance

All JPEGs were captured from real browser-rendered pages on 4 November 2026. dashboard-desktop.jpg is the earlier recorded export; dashboard-history.jpg, dashboard-model.jpg and dashboard-pipeline.jpg show the dated export visible at capture time. runtime-integration-actions.jpg shows the real successful GitHub Actions run. None is an Airflow UI or database GUI capture. Raw PostgreSQL and task logs are supplied separately to avoid implying unavailable UI evidence.

The refreshed-data candidate comparison again selected the naive baseline; all 15 alternatives failed to outperform it during pre-holdout validation. The full 16-configuration result includes its input CSV hash. Current dashboard captures (*-current.jpg) show the 4 November export and do not replace the earlier dated captures.
