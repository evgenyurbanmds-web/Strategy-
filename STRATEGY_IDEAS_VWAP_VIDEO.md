# Codex research handoff — VWAP video hypotheses

Source: user-uploaded screen recording `ScreenRecording_11-05-2026 01-48-04_1.mp4` (~2m43s). The video is an educational TradingView chart walkthrough, apparently XAUUSD on a short intraday timeframe. This document distinguishes observations from proposed, testable BTCUSDT rules. It is **not** a transcription and does **not** assert the presenter has a proven edge.

## 1. What is observable in the video

- TradingView chart with a blue central reference line and green shaded/deviation regions. The explanation refers to VWAP, trending moves, retracements, and misleading moves across the reference line.
- A rising-price example: price advances away from the reference, pulls back, then continues; risk/reward boxes are illustrated.
- A later example shows a sharp move against the trend / a possible false breakout and discussion of avoiding a premature directional reversal.
- Video illustrations are selective; no full trade log, consistent executable entry/exit rules, out-of-sample tests, verified win rate, or transaction-cost analysis are supplied.
- Exact VWAP anchoring/session reset, band calculation, thresholds, trade entry timestamp, stop/target placement, and whether alerts are executable are not reliably established from the recording. **Do not present any invented numeric values as the creator's settings.**

## 2. Research objective

Determine whether VWAP-based pullback or false-breakout signals add net risk-adjusted return to the existing BTCUSDT research. BTC trades 24/7; do not assume XAUUSD session logic transfers unchanged. Test as independent strategies and as filters/entry timing improvements to the existing 4h long-only baseline.

## 3. Hypothesis A — trend-following VWAP pullback

**Researcher-defined rules, not rules verified from the video:**

1. Determine trend from information available at the previous closed bar, e.g. EMA20 > EMA50, close > SMA200, optional ADX14 > 20. Test a small preregistered grid, not a huge unconstrained search.
2. Calculate volume-weighted average price using completed candles and a clearly specified reset: UTC day, UTC week, and optionally anchored rolling lookback. BTCUSDT exchange candle volume is base-asset volume; verify consistent units.
3. Define pullback as price moving from above VWAP into a small volatility-normalized band around VWAP (for example ±0.25 or ±0.5 ATR), with a subsequent completed-candle close back above VWAP.
4. Enter long no earlier than the **next** candle open after confirmation. No same-candle hindsight fills.
5. Compare stop definitions: below the prior confirmed swing low, or fixed 2–3 ATR; compare fixed R multiple exits versus ATR trailing stop. Avoid intrabar sequencing assumptions; use 1m candles if necessary for stops.
6. Mirror short setups in a separate experiment; do not mix with spot long-only baseline without declaring the ability to short and associated borrowing/funding costs.

## 4. Hypothesis B — VWAP false breakout / reclaim

**Researcher-defined rules:**

1. Establish an uptrend before the candidate event.
2. Detect a completed candle closing below VWAP by a minimum volatility-normalized distance, followed within N completed candles by a close back above VWAP (N = 1–3 is an initial research range).
3. Confirm that the larger trend has not invalidated (e.g. previous daily SMA200 and 4h trend filter remain positive).
4. Enter at next candle open following reclaim; stop below the event low or by ATR; exits as in Hypothesis A.
5. Compare against control entries triggered by ordinary VWAP crosses, and against randomly sampled trend-following entries matched for market regime.

## 5. Hypothesis C — use VWAP as a filter on existing baseline

Keep baseline trend signals and exits fixed; only allow an entry when the last completed candle is above daily or weekly VWAP, or when a recent pullback/reclaim is present. Report whether improved drawdown compensates for missed trends and reduced trade count.

## 6. Mandatory evaluation protocol

- Market: Binance BTCUSDT; initially 15m and 5m for the video-like ideas, and 4h for baseline integration. Clearly separate timeframe-specific experiments.
- Data: exchange OHLCV, UTC timestamps, verified continuity, deduplication, and a documented start/end period. Do not claim five years of 5m history until downloaded and checked.
- Costs: 0.10% commission + 0.05% slippage **per side** = 0.15% entry and 0.15% exit, approximately 0.30% round-trip before compounding; run sensitivity at higher cost.
- Execution: use only completed candles; next-bar-open entry/exit; handle stop gaps and same-bar target/stop ambiguity conservatively.
- Capital: $10,000 initial, no leverage for spot baseline. If testing short positions, isolate futures/perpetual assumptions and funding.
- Report: net return, CAGR, max drawdown, trades, win rate, expectancy, profit factor, turnover, exposure, annual returns, and fees paid. Compare buy-and-hold and existing EMA20/EMA50 + SMA200 + ADX14 + ATR-stop baseline under the **same** data/cost engine.
- Validation: chronological train/validation/holdout, walk-forward, parameter stability, multiple-testing correction or reality check, bootstrap by trade/time blocks; do not choose a winner using holdout and then call it untouched.
- Test meaningful incremental edge: compare same-period signals, regime-adjusted performance, and out-of-sample net performance; reject if improvements are small relative to sampling uncertainty.
- Explicitly flag that an illustrative risk/reward drawing is **not** an observed realized P&L outcome.

## 7. Autonomous work instructions

1. Inspect the existing project and `PROJECT_BRIEF.md`, if available; preserve prior results and mark them unverified until reproducible.
2. Implement unit-tested VWAP session-reset and signal functions; include synthetic tests for UTC midnight/week boundary, missing candles, lookahead, and fee accounting.
3. Build a deterministic experiment manifest (config + data version + code commit + result file) and persistent `STATE.md` so future Codex runs can resume without rereading long chat history.
4. Run a small pilot to debug mechanics, then limited predefined grids; stop weak hypotheses early; do not over-optimize thresholds.
5. Write compact `results/vwap_video_report.md` with evidence, uncertainty, plots, and next steps. Never claim profitable strategy without independent holdout evidence.
6. No real orders, no exchange credentials, and no paid services without explicit user authorization.

## 8. Known uncertainties

- The video does not establish a single fully reproducible algorithm. VWAP reset, deviations, stop/target and trend definition are open research choices, not sourced facts.
- XAUUSD market structure and session volumes differ from BTCUSDT; transferring a visual setup is a hypothesis.
- Video examples are vulnerable to selection bias. All conclusions must come from reproducible data, not visual plausibility.
