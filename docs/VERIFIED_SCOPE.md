# Verified implementation scope — 4 November 2026 (Asia/Bangkok)

New implementation based on repository baseline `5a0872c07784fcc7e82ddaf7be6ef9fae41c4577`, backed up at `backup/before-real-pipeline-20261104`. This is not a recovery or continuation of an unprovided Airflow database/source archive.

| Capability | Result | Evidence / boundary |
|---|---|---|
| Actual network extraction | PASS | evidence/live-refresh.txt; World Bank workbook, Gold API XAU/XAG, Frankfurter USD/THB returned successful responses |
| Normalization / unit separation | PASS | source validation, frequency in primary key, monthly chart separate from spot/FX |
| SQLite load | PASS | 2,406 real observations in the recorded run; SQL coverage in evidence/database-summary.json |
| UPSERT / idempotence | PASS | Replay exact recorded rows twice in isolated SQLite: second insert count zero |
| Persistence | PASS (SQLite reopen) | Reopened isolated SQLite database retains all rows; not a VPS/container restart test |
| Partial/all-source failure handling | PASS in isolated fault-injection tests | Does not prove a real provider outage occurred; no corrupted test values published |
| Read-only Python HTTP API | PASS | tools.verify_api starts actual service against a temporary DB containing replayed real rows; status/privacy-path checks |
| Static dashboard | Browser evidence recorded separately | Reads generated JSON; prices and history are real recorded observations, not continuously live |
| ML readiness / feature engineering | PASS | 308 eligible monthly rows; all features use prior months; insufficient/gapped histories gated |
| ML evaluation | PASS as research execution | 36 expanding-window monthly holdout predictions; candidate loses to naive on MAE; forecast withheld |
| PostgreSQL adapter / Compose | NOT TESTED at runtime | Source/configuration supplied; no Docker/Postgres binaries available in this Work environment |
| Airflow DAG | NOT TESTED at runtime | Source compiled only; manual Airflow 2.10.x DAG, separate Python 3.12 venv required |
| CI / Pages deployment | See GitHub workflow result and final browser review | Do not infer a passed deployment from this source file alone |
| Physical mobile device | NOT TESTED | CSS viewport rendering is browser testing only |
| Investment or production acceptance | NOT TESTED / outside scope | No trading strategy, transactions, P&L, SLA, investor suitability or signed UAT |

## Current data and limits

Historical data returned by the official workbook ends September 2026, despite the collection date being later. The workbook says Updated on October 02, 2026. Both dates are shown so historical monthly averages are never advertised as current quotes.

Model MAE is about 133.60 USD/troy oz versus naive 129.53 in the recorded evaluation. This is a negative result, not a hidden result. The candidate is not promoted and a point forecast is not exposed. Current-vintage inputs are not a point-in-time trading backtest.

The old concept-only audit is retained in docs/archive/VERIFIED_SCOPE_20261030.md and the previous evidence/source-audit.json. They describe the earlier repository and are not current runtime results.
