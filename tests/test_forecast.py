import sqlite3
import numpy as np
import pandas as pd
from forecast import STEP_MS, make_forecast, connect_db, save_forecast, save_observations, evaluate

def candles(n=250):
    prices = 100 * np.exp(np.cumsum(np.full(n, 0.0001)))
    return pd.DataFrame({
        "open_ms": np.arange(n) * STEP_MS, "close_ms": np.arange(n) * STEP_MS + STEP_MS - 1,
        "open": prices, "high": prices*1.01, "low": prices*.99,
        "close": prices, "volume": np.ones(n)
    })

def test_forecast_deterministic_and_monotone():
    a = make_forecast(candles(), paths=200, seed=42)
    b = make_forecast(candles(), paths=200, seed=42)
    assert a == b
    assert len(a["p50"]) == 24
    assert all(lo <= mid <= hi for lo, mid, hi in zip(a["p10"], a["p50"], a["p90"]))

def test_scoring_uses_future_candles_only(tmp_path):
    frame = candles(250)
    conn = connect_db(tmp_path / "test.db")
    try:
        f = make_forecast(frame, paths=200)
        save_observations(conn, frame)
        save_forecast(conn, f)
        assert evaluate(conn).empty
        future = candles(275).tail(25)
        save_observations(conn, future)
        scores = evaluate(conn)
        assert len(scores) == 24
        assert set(scores["step"]) == set(range(1, 25))
    finally:
        conn.close()
