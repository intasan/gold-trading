# Data sources and provenance

## 1. World Bank Pink Sheet

- Official landing page: https://www.worldbank.org/en/research/commodity-markets
- Download inspected from its Monthly prices link: https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx
- Dataset catalogue/license: https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections — Public / CC BY 4.0. Attribution: World Bank, Commodity Price Data (The Pink Sheet). This project extracts and reformats selected columns; it is not endorsed by the World Bank.
- Parsed `Monthly Prices`: find Gold/Silver header row; verify `($/troy oz)` for Gold, Silver and Platinum. Accept rows labeled YYYYMmm; no interpolation of missing values.
- Observed workbook release label: Updated on November 03, 2026. Coverage inspected: January 1960–October 2026. Treat this as the source response observed, not a promise of up-to-date market prices.
- `observed_at=YYYY-MM-01` denotes the **monthly period**, not a first-day price or exact publication timestamp.

## 2. Gold API

- Documentation: https://gold-api.com/docs ; endpoint details/frequency/units: https://gold-api.com/faqs ; provider terms: https://gold-api.com/terms
- GET `https://api.gold-api.com/price/XAU` and `/price/XAG`. USD per troy ounce, spot quotes, provider `updatedAt` retained in UTC. Retrieved time is recorded separately.
- No API key used. Current price calls are cached at least 30 seconds; this project makes one request per symbol per refresh, with bounded retry. Historical endpoints require a key and are **not** used.
- Service availability/accuracy and provider terms still apply. Only the timestamped returned values are recorded; no tick history or market execution quality is inferred.

## 3. Frankfurter

- Documentation: https://frankfurter.dev/
- GET `https://api.frankfurter.dev/v2/rate/USD/THB`. Check base USD, quote THB, ISO reference date and positive finite rate.
- Reference rate is **THB per USD**, not USD per THB, not a retail FX quote and not a Thai gold-buy/sell price. Default blended provider rates are not relabeled as an exclusively Bank of Thailand rate.
- No API key used. Daily reference dates can precede retrieval dates.

## Raw and normalized evidence

`data/raw/` is a local ignored cache of complete provider responses with URL, HTTP status, UTC retrieved time and SHA-256. A successful parser never invents missing prices. `data/published/observations.csv` contains the actual selected observations, units, source timestamps, retrieval times and raw response hashes so the exact model input can be replayed without contacting a mutable provider URL.

The original XLSX binary is not committed. Exact analysis is reproduced from the committed normalized real observations. A later provider download may have a different hash or revised values. There is no claim of a historic point-in-time source vintage.

Gold/Silver/Platinum historical columns use one source. Spot quotes use another source and frequency. No numeric equality or cross-source interchangeability is asserted. The source column and frequency are part of the primary key.
