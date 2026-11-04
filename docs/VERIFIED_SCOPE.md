# Verified scope — 4 November 2026

| Capability | Status | Evidence |
|---|---|---|
| Real provider ingestion | PASS | Scheduled refresh 41788601769; 2,412 recorded observations |
| SQLite | PASS | 12 unit tests and earlier API checks |
| Docker + PostgreSQL 16.15 | PASS in isolated integration | Replay idempotence, persistence after restart, fresh-source ingest and API |
| Airflow 2.10.5 DAG execution | PASS in Docker | All three tasks ran through Airflow DAG CLI test; raw logs in evidence/runtime |
| Daily automated refresh | PASS first full execution / cron enabled | 13:17 Bangkok; ephemeral services and Git-persisted export |
| GitHub Pages | PASS | Recorded export published; no Python process hosted on Pages |
| ML predictive quality | NOT PASSED | Current HGB MAE 138.14 vs naive 135.47; no forecast published |
| Physical device test | NOT TESTED | Browser viewport tests only |
| Persistent hosted Airflow/PostgreSQL | NOT DEPLOYED | Actions runtime is ephemeral; no VPS changed |
| Trading system / Production Ready | Not claimed | No orders, profit, broker integration or signed UAT |

See [Runtime acceptance](RUNTIME_ACCEPTANCE.md) and [Model card](MODEL_CARD.md). Historical evidence remains preserved and should be read with its recorded export date.
