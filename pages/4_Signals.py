from __future__ import annotations

import json
import os

import streamlit as st

from analytics.signals import compute_signal
from analytics.technicals import add_all_indicators
from data.market_data import get_ohlcv
from ui.styles import inject_css, section_header, signal_badge
from ui.theme import COLORS

WATCHLIST_PATH = "watchlist.json"

inject_css()

section_header("Signal Screener", icon="bell")


def _load_watchlist() -> list[str]:
    if os.path.exists(WATCHLIST_PATH):
        with open(WATCHLIST_PATH) as f:
            return json.load(f)
    return []


def _save_watchlist(wl: list[str]):
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(wl, f)


watchlist = _load_watchlist()

with st.sidebar:
    st.subheader("Manage Watchlist")
    new_ticker = st.text_input("Add ticker").strip().upper()
    if st.button("Add") and new_ticker and new_ticker not in watchlist:
        watchlist.append(new_ticker)
        _save_watchlist(watchlist)
        st.rerun()
    if watchlist:
        remove_ticker = st.selectbox("Remove ticker", watchlist)
        if st.button("Remove"):
            watchlist.remove(remove_ticker)
            _save_watchlist(watchlist)
            st.rerun()

if not watchlist:
    st.info("Add tickers to your watchlist from the sidebar to see signals.")
    st.stop()

if st.button("Refresh Signals"):
    from data import cache

    cache.clear()
    st.rerun()

rows = []
with st.spinner("Computing signals..."):
    for sym in watchlist:
        signal = compute_signal(sym)
        df = get_ohlcv(sym, period="5d")
        current_price = float(df.iloc[-1]["close"]) if not df.empty and len(df) >= 1 else None
        day_change = None
        if not df.empty and len(df) >= 2:
            prev_close = float(df.iloc[-2]["close"])
            if prev_close > 0:
                day_change = (float(df.iloc[-1]["close"]) - prev_close) / prev_close

        df_1y = get_ohlcv(sym, period="1y")
        df_1y = add_all_indicators(df_1y)
        rsi = (
            float(df_1y.iloc[-1]["rsi14"]) if not df_1y.empty and "rsi14" in df_1y.columns else None
        )

        macd_status = "—"
        if not df_1y.empty and "macd" in df_1y.columns and len(df_1y) >= 2:
            last_m = df_1y.iloc[-1]
            prev_m = df_1y.iloc[-2]
            if last_m["macd"] == last_m["macd"] and last_m["macd_signal"] == last_m["macd_signal"]:
                if (
                    prev_m["macd"] < prev_m["macd_signal"]
                    and last_m["macd"] > last_m["macd_signal"]
                ):
                    macd_status = "Bullish Crossover"
                elif (
                    prev_m["macd"] > prev_m["macd_signal"]
                    and last_m["macd"] < last_m["macd_signal"]
                ):
                    macd_status = "Bearish Crossover"
                else:
                    macd_status = "Neutral"

        rows.append(
            {
                "symbol": sym,
                "price": current_price,
                "day_change": day_change,
                "score": signal.score,
                "label": signal.label,
                "rsi": rsi,
                "macd": macd_status,
                "reason": signal.reasons[0] if signal.reasons else "—",
            }
        )

# ---------------------------------------------------------------------------
# Summary badges
# ---------------------------------------------------------------------------
from collections import Counter  # noqa: E402

label_counts = Counter(r["label"] for r in rows)
badge_html = " ".join(
    f"{signal_badge(label)} <b>{count}</b>&nbsp;&nbsp;" for label, count in label_counts.items()
)
st.markdown(badge_html, unsafe_allow_html=True)
st.markdown("")

# ---------------------------------------------------------------------------
# Per-ticker cards
# ---------------------------------------------------------------------------
for row in rows:
    with st.container():
        c_sym, c_price, c_score, c_signal, c_rsi, c_macd, c_reason = st.columns(
            [1.5, 1.2, 0.8, 1.2, 0.8, 1.3, 2.2]
        )
        c_sym.markdown(f"**{row['symbol']}**")

        price_str = f"{row['price']:,.2f}" if row["price"] else "N/A"
        if row["day_change"] is not None:
            chg = row["day_change"] * 100
            color = COLORS["profit"] if chg >= 0 else COLORS["loss"]
            c_price.markdown(
                f'{price_str} <span style="color:{color};font-weight:600">{chg:+.2f}%</span>',
                unsafe_allow_html=True,
            )
        else:
            c_price.markdown(price_str)

        score = row["score"]
        c_score.progress(score / 10, text=f"{score}/10")

        c_signal.markdown(signal_badge(row["label"]), unsafe_allow_html=True)

        rsi = row["rsi"]
        if rsi and rsi == rsi:
            if rsi < 30:
                rsi_color = COLORS["profit"]
            elif rsi > 70:
                rsi_color = COLORS["loss"]
            else:
                rsi_color = COLORS["text"]
            c_rsi.markdown(
                f'<span style="color:{rsi_color};font-weight:600">{rsi:.0f}</span>',
                unsafe_allow_html=True,
            )
        else:
            c_rsi.markdown("N/A")

        c_macd.markdown(row["macd"])
        c_reason.caption(row["reason"])
