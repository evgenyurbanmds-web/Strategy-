"""Read-only Streamlit dashboard; no order routing or exchange credentials."""
import datetime as dt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from forecast import STEP_MS, refresh

st.set_page_config(page_title="BTC Forecast Lab", layout="wide")
st.title("BTCUSDT · 24-candle forecast lab")
st.caption("Binance SPOT BTCUSDT · 5m · empirical bootstrap baseline, not an AI trading signal")
st.warning("Experimental forecast. Bands are uncalibrated; no live trading or order placement.")
with st.sidebar:
    st.header("Controls")
    st.write("Auto-refresh approximately every 60 seconds while this tab is open.")
    st.write("Each forecast is saved once per closed 5-minute candle.")
    st.write("No API keys required.")
    if st.button("Refresh now"):
        st.cache_data.clear()

@st.fragment(run_every="60s")
def live_view():
    try:
        frame, f, scored = refresh()
    except Exception as exc:
        st.error(f"Market data unavailable: {type(exc).__name__}: {exc}")
        return
    price = f["origin_price"]
    origin = f["origin_ms"]
    st.metric("Last closed candle", f"${price:,.2f}")
    st.caption("Origin: " + dt.datetime.fromtimestamp(origin / 1000, dt.timezone.utc).isoformat())
    recent = frame.tail(100)
    times = pd.to_datetime(recent["open_ms"], unit="ms", utc=True)
    future = pd.to_datetime([origin + STEP_MS * k for k in range(1, 25)], unit="ms", utc=True)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=times, open=recent["open"], high=recent["high"],
                                 low=recent["low"], close=recent["close"], name="BTCUSDT"))
    fig.add_trace(go.Scatter(x=list(future) + list(future[::-1]),
                             y=f["p90"] + f["p10"][::-1],
                             fill="toself", fillcolor="rgba(0,200,190,0.16)",
                             line=dict(color="rgba(0,0,0,0)"), name="P10–P90"))
    fig.add_trace(go.Scatter(x=future, y=f["p50"], name="Median forecast",
                             line=dict(color="cyan", width=2)))
    fig.update_layout(template="plotly_dark", height=570, xaxis_rangeslider_visible=False,
                      yaxis_title="USDT", xaxis_title="UTC")
    st.plotly_chart(fig, use_container_width=True)
    if scored.empty:
        st.info("Accuracy will appear once future candles close. Forecasts are not backfilled.")
        return
    complete = scored[scored["step"] == 24]
    st.subheader("Observed accuracy (saved live forecasts only)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Scored forecast steps", len(scored))
    c2.metric("MAE · all scored steps", f"${scored['abs_error'].mean():,.2f}")
    c3.metric("P10–P90 coverage", f"{100*scored['covered_80'].mean():.1f}%")
    if not complete.empty:
        st.write(f"24-step MAE: ${complete['abs_error'].mean():,.2f} | "
                 f"24-step directional accuracy: {100*complete['direction_correct'].mean():.1f}% "
                 f"(n={len(complete)} origins)")
    st.caption("Overlapping forecast horizons are correlated. Coverage and direction scores are descriptive, not proof of edge.")
live_view()
