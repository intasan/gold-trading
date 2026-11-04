# Model card — monthly gold research

## Actual evaluation

- Model: HistGradientBoostingRegressor on log returns, scikit-learn 1.8.0. Fixed parameters, no holdout tuning.
- Dataset: World Bank Gold/Silver/Platinum monthly averages, current workbook vintage. Feature construction starts January 2000.
- Eligible complete feature rows: 308. Initial training rows before holdout: 272.
- Evaluation: Expanding-window, one-observation-ahead; fixed hyperparameters; no random split. 36 held-out monthly predictions from 2023-10-01 through 2026-09-01. For each period, fit only on earlier feature rows. Earlier actual test observations become available to subsequent expanding-window fits, matching the explicitly retrospective one-step setup.
- Target: log(gold monthly average / previous monthly average), converted back to price for evaluation.
- Features: return_1, return_3, return_6, return_12, mean_ratio_3, mean_ratio_12, volatility_6, silver_return_1, platinum_return_1. All shifted to prior observations. No current-period metal value, spot quote or FX rate is used as a feature.

| Metric | Candidate | Naive last-observed price |
|---|---:|---:|
| MAE (USD/troy oz) | 133.60021960 | 129.52777778 |
| RMSE (USD/troy oz) | 180.93078538 | 175.08418610 |
| MAPE (%) | 3.72944110 | 3.65742206 |

**Outcome: not promoted.** The candidate has higher MAE than the naive baseline in this run. The exported forecast is null, and the dashboard explicitly states that the forecast is withheld. No profit or investment-performance claim follows from these errors.

## Readiness gate

At least 180 initial training feature rows plus 36 holdout rows; positive actual prices and complete consecutive monthly feature rows. Missing periods are not interpolated. If history is insufficient or gapped, status becomes not_ready with a reason. A runtime evaluation error is failed, not a hidden fallback success.

## Reproducibility

Run replay into a clean DB, then model. Input normalized observations: data/published/observations.csv; evaluation detail: evidence/model-evaluation.json. Input SHA-256: 51119174a00f1c63d68c26fb1ad2e80028ac0381dd717481c8f0526aacc8f200. Exact floating-point results may vary slightly across numerical-library/platform versions. No pickle/joblib model download is executed.

## Limits

- This is a **monthly-average** model, not an intraday or daily spot-price forecast.
- Current-vintage historical data can contain revisions. The experiment does not reconstruct publication-time availability or real-time historical vintages. It is not a tradable point-in-time backtest.
- Monthly observations are released after the observation period; publication latency is not modeled. Any future research estimate refers to the next unpublished monthly observation, not necessarily a future calendar month.
- Fixed model choice/thresholds were specified before reading holdout errors in this implementation; this is a single candidate, not an exhaustive model comparison. No selection of a better-looking score after seeing this holdout.
- No fees, positions, transactions, P&L, prediction intervals or live deployment validation.
- Keep collecting timestamped raw source vintages, improve baselines and use a separate future evaluation period before making stronger claims.
