# Current model card — recorded export 2026-11-04T06:56:26.299389Z

Model: HistGradientBoostingRegressor on log returns. Lagged monthly gold, silver and platinum features; expanding-window chronological evaluation. Initial training: 273 rows; holdout: 2023-11-01 through 2026-10-01 (36 months).

| Metric | Candidate | Naive |
|---|---|---|
| MAE USD/troy oz | 138.1440 | 135.4722 |
| RMSE USD/troy oz | 183.5701 | 178.6801 |
| MAPE % | 3.8215 | 3.8022 |

**Not promoted; forecast withheld.** No claim of useful predictive performance or trading profitability. Monthly averages are separate from spot quotes and FX.

Current-vintage observations have revisions and publication lags that are not reconstructed. This is retrospective evaluation, not a point-in-time trading backtest. Additional candidate comparison is recorded in evidence/model-research.json; the previously inspected holdout is disclosed as reused historical evidence. Its research gate requires at least 5% lower MAE and RMSE and winning MAE in at least two of three annual folds. Repeated tuning until a known holdout passes would not demonstrate future forecasting quality.

Earlier model card retained in docs/archive/MODEL_CARD_20261103.md. Full current predictions and parameters: data/published/snapshot.json.
