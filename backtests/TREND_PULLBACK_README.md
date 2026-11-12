# BTCUSDT Trend Pullback v1

Implemented: 1h EMA50/200 + ADX14>25 and DI direction; 5m EMA20 and EMA50 pullback variants, 3-prior-bar EMA touch, signal closes beyond EMA20 and prior bar high/low, next-bar open entry; stop behind 4-bar extreme plus 0.2 ATR14; 2R target; 48-bar timeout; 1% risk with unlevered notional cap; 0.1% commission and 0.05% slippage **per side**. Conservative stop-first OHLC ordering. Uses only completed 1h bars as of each 5m bar close.

Run with a verified contiguous BTCUSDT 5m CSV (UTC columns time,open,high,low,close,volume):

```bash
pip install pandas numpy
python -m backtests.trend_pullback --csv data/btc_5m.csv
```

Results in `reports/trend_pullback/`: EMA20/EMA50 JSON summaries, yearly results, trade logs and equity curves.

**Not yet a historical result:** this repository does not contain verified multi-year 5m market data; no real-data backtest has been completed. Do not interpret synthetic unit tests as evidence of profitability. For multi-year data, obtain 5m CSV from a permitted exchange/data provider and rerun.

Limitations: shorts are hypothetical on spot BTC data (funding/borrow omitted); stop/target on same candle assumes stop first; spread and market impact not separately modelled; indicator warm-up is ~2500 5m bars; yearly B&H is first-to-last close per year and strategy marks equity each candle. Benchmark on same start date after warmup before drawing performance conclusions. A further audit should verify actual order fill assumptions, funding, parameter stability, train/test separation, and no lookahead.
