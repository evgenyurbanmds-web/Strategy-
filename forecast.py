"""Reproducible, non-trading 24-candle probabilistic baseline.

Uses Binance public spot klines and empirical bootstrap of past log returns.
Not a trained AI model and not a reliable prediction of market direction.
"""
import datetime as dt
import json
import os
import sqlite3
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

API = "https://api.binance.com/api/v3/klines"
INTERVAL = "5m"
STEP_MS = 300_000
HORIZON = 24
DB = Path(os.environ.get("FORECAST_DB", "data/forecasts.sqlite3"))
SEED = 20261109


def fetch_closed_candles(limit=1000, now_ms=None):
    """Get only CLOSED Binance BTCUSDT spot candles, in ascending order."""
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    response = requests.get(
        API, params={"symbol": "BTCUSDT", "interval": INTERVAL, "limit": limit},
        timeout=15,
    )
    response.raise_for_status()
    raw = response.json()
    if not isinstance(raw, list) or not raw:
        raise ValueError("Unexpected or empty Binance response")
    rows = [
        (int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]),
         float(k[5]), int(k[6]))
        for k in raw if int(k[6]) < now_ms
    ]
    frame = pd.DataFrame(rows, columns=["open_ms", "open", "high", "low", "close", "volume", "close_ms"])
    if frame.empty or frame["open_ms"].duplicated().any():
        raise ValueError("No closed candles or duplicate timestamps")
    frame = frame.sort_values("open_ms").reset_index(drop=True)
    if not (frame["open_ms"].diff().dropna() == STEP_MS).all():
        raise ValueError("Missing or irregular 5-minute candles")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("Invalid price")
    return frame


def make_forecast(frame, horizon=HORIZON, paths=2000, seed=SEED):
    """Empirical iid-return bootstrap. Quantiles are heuristic, NOT calibrated."""
    if len(frame) < 200 or horizon < 1 or paths < 100:
        raise ValueError("Insufficient history or invalid forecast parameters")
    close = frame["close"].to_numpy(dtype=float)
    returns = np.diff(np.log(close))
    # Exclude nonfinite returns, but never silently accept data gaps (checked on fetch).
    if not np.isfinite(returns).all():
        raise ValueError("Nonfinite log returns")
    rng = np.random.default_rng(seed)
    sampled = rng.choice(returns, size=(paths, horizon), replace=True)
    simulated = close[-1] * np.exp(np.cumsum(sampled, axis=1))
    quantiles = np.quantile(simulated, [0.1, 0.5, 0.9], axis=0)
    return {
        "origin_ms": int(frame.iloc[-1]["open_ms"]),
        "origin_close_ms": int(frame.iloc[-1]["close_ms"]),
        "origin_price": float(close[-1]),
        "horizon": horizon,
        "interval": INTERVAL,
        "model": "empirical_iid_bootstrap_v1",
        "seed": seed,
        "p10": quantiles[0].tolist(),
        "p50": quantiles[1].tolist(),
        "p90": quantiles[2].tolist(),
    }


def connect_db(path=DB):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS forecasts (
        origin_ms INTEGER PRIMARY KEY,
        origin_price REAL NOT NULL,
        horizon INTEGER NOT NULL,
        interval TEXT NOT NULL,
        model TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_utc TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS actuals (
        open_ms INTEGER PRIMARY KEY,
        close REAL NOT NULL
    )""")
    conn.commit()
    return conn


def save_observations(conn, frame):
    conn.executemany(
        "INSERT OR IGNORE INTO actuals(open_ms,close) VALUES (?,?)",
        [(int(r.open_ms), float(r.close)) for r in frame.itertuples(index=False)]
    )
    conn.commit()


def save_forecast(conn, forecast):
    conn.execute(
        """INSERT OR IGNORE INTO forecasts
        (origin_ms,origin_price,horizon,interval,model,payload,created_utc)
        VALUES (?,?,?,?,?,?,?)""",
        (forecast["origin_ms"], forecast["origin_price"], forecast["horizon"],
         forecast["interval"], forecast["model"], json.dumps(forecast),
         dt.datetime.now(dt.timezone.utc).isoformat()),
    )
    conn.commit()


def evaluate(conn):
    """Score each forecast step only once its corresponding CLOSED candle exists.

    For a forecast made on candle origin_ms, step k corresponds to
    open_ms=origin_ms + k*STEP_MS, k=1..24.
    """
    results = []
    for (payload,) in conn.execute("SELECT payload FROM forecasts ORDER BY origin_ms"):
        f = json.loads(payload)
        for k in range(1, f["horizon"] + 1):
            target_ms = f["origin_ms"] + k * STEP_MS
            actual = conn.execute("SELECT close FROM actuals WHERE open_ms=?", (target_ms,)).fetchone()
            if actual is None:
                continue
            price = float(actual[0])
            mid = float(f["p50"][k - 1])
            lo, hi = float(f["p10"][k - 1]), float(f["p90"][k - 1])
            results.append({
                "origin_ms": f["origin_ms"], "step": k, "actual": price,
                "p50": mid, "abs_error": abs(price - mid),
                "covered_80": lo <= price <= hi,
                "direction_correct": (mid > f["origin_price"]) == (price > f["origin_price"]),
            })
    return pd.DataFrame(results)


def refresh():
    frame = fetch_closed_candles()
    conn = connect_db()
    try:
        save_observations(conn, frame)
        f = make_forecast(frame)
        save_forecast(conn, f)
        return frame, f, evaluate(conn)
    finally:
        conn.close()
