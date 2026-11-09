# BTCUSDT 24-candle forecast lab

## Architecture

Binance public SPOT REST /api/v3/klines (BTCUSDT 5m) -> validation of fully closed contiguous candles -> empirical bootstrap forecast -> SQLite immutable per-candle forecast -> future actual candle ingestion -> out-of-sample scoring -> Streamlit/Plotly read-only dashboard.

**Status:** initial implementation committed; not yet executed or validated in this environment. This is a research prototype, not a trading system or proven prediction model. No API keys, trading functions, or real orders.

## Run locally

Requires Python 3.10+ and network access to the public Binance Spot endpoint from your location.

```bash
git clone https://github.com/evgenyurbanmds-web/Strategy-.git
cd Strategy-
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
streamlit run dashboard.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501). While the dashboard tab is open, Streamlit refreshes roughly every 60 seconds. **For unattended 24/7 operation, run a separate scheduler/worker**: a Streamlit tab is not a durable data collector. If Binance.com is inaccessible in your jurisdiction, do not bypass restrictions; choose a permitted data source and adapt the fetcher.

## Forecast definition

- 5-minute SPOT candles, 24 future candles (2 hours).
- Uses up to the last 1000 candles; the most recent candle must be closed.
- Computes historical log returns and independently resamples 24 returns per simulated path.
- Fixed random seed, 2000 paths. P10, P50, P90 calculated per horizon.
- This bootstrap assumes iid returns and does not model market regimes, volatility clustering, market microstructure, or future information. Its probability bands are **not calibrated**.
- Forecasts are keyed by the origin candle and saved once (INSERT OR IGNORE), so revisiting the dashboard does not silently revise predictions.

## Evaluation

For each forecast made at candle open timestamp t, compare step k with actual *closed* candle at t + k*300000 ms, k=1..24. Metrics: median absolute error, 80% interval coverage, direction vs origin price. The 24th step is scored only after two hours. Historical candles used to initialize the model are **not** retroactively represented as live forecasts. Scores from overlapping horizons are correlated.

## Next engineering milestones

1. Add a standalone scheduled collector/worker, reconnect/retry/backoff, outage monitoring, and DB backup.
2. Add a permitted alternative price feed, plus reconciliation with Binance Perpetual if the target market is futures.
3. Walk-forward backtest and naive benchmarks (unchanged-price, drift, volatility-scaled bootstrap).
4. Properly calibrated intervals and non-overlapping evaluation cohorts; directional probability calibration.
5. Only then evaluate pretrained Kronos or other time-series models with frozen test periods and latency/cost accounting.
6. Optional Telegram notifications after false-signal and outage controls. No real order execution.

## Safety

Do not store API keys in this repository. This GitHub repository is currently public. Local `data/` contains observations and forecasts and is ignored by Git; keep it local or use secure storage. This system provides no financial performance guarantee.
