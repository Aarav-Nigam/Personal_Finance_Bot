from __future__ import annotations

import json
import os
from collections import Counter

import streamlit as st

from analytics.signals import compute_signal, compute_signal_with_cost_basis
from analytics.targets import compute_actionable_targets
from analytics.technicals import add_all_indicators
from data.market_data import get_ohlcv
from ui.charts import sub_score_bar
from ui.glossary import explain_signal, tip
from ui.styles import inject_css, metric_card, pnl_colored, section_header, signal_badge
from ui.theme import COLORS

WATCHLIST_PATH = "watchlist.json"

inject_css()

section_header("Signal Screener", icon="🔔")


def _load_watchlist() -> list[str]:
    if os.path.exists(WATCHLIST_PATH):
        with open(WATCHLIST_PATH) as f:
            return json.load(f)
    return []


def _save_watchlist(wl: list[str]):
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(wl, f)


# ---------------------------------------------------------------------------
# Sidebar: watchlist management
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_watchlist, tab_portfolio, tab_accuracy = st.tabs(
    ["📋 Watchlist Signals", "💼 Portfolio Signals", "📊 Signal Accuracy"]
)


# ===========================================================================
# TAB 1: Watchlist Signals
# ===========================================================================
with tab_watchlist:
    if not watchlist:
        st.info("Add tickers to your watchlist from the sidebar to see signals.")
        st.stop()

    def _compute_watchlist_signals(symbols: list[str]) -> list[dict]:
        rows = []
        for sym in symbols:
            signal = compute_signal(sym)
            df = get_ohlcv(sym, period="5d")
            current_price = float(df.iloc[-1]["close"]) if not df.empty else None
            day_change = None
            if not df.empty and len(df) >= 2:
                prev_close = float(df.iloc[-2]["close"])
                if prev_close > 0:
                    day_change = (float(df.iloc[-1]["close"]) - prev_close) / prev_close

            df_1y = get_ohlcv(sym, period="1y")
            df_1y = add_all_indicators(df_1y)
            rsi = (
                float(df_1y.iloc[-1]["rsi14"])
                if not df_1y.empty and "rsi14" in df_1y.columns
                else None
            )

            rows.append(
                {
                    "symbol": sym,
                    "price": current_price,
                    "day_change": day_change,
                    "score": signal.score,
                    "label": signal.label,
                    "confidence": signal.confidence,
                    "rsi": rsi,
                    "reasons": signal.reasons,
                    "sub_scores": signal.sub_scores,
                }
            )
        return rows

    if st.button("Refresh Signals", key="refresh_watchlist"):
        from data import cache

        cache.clear()
        st.session_state.pop("signal_rows", None)
        st.session_state.pop("signal_watchlist", None)
        st.rerun()

    cached_wl = st.session_state.get("signal_watchlist")
    if cached_wl != watchlist or "signal_rows" not in st.session_state:
        with st.spinner("Computing signals..."):
            rows = _compute_watchlist_signals(watchlist)
        st.session_state.signal_rows = rows
        st.session_state.signal_watchlist = list(watchlist)
    else:
        rows = st.session_state.signal_rows

    # Summary badges
    label_counts = Counter(r["label"] for r in rows)
    badge_html = " ".join(
        f"{signal_badge(label)} <b>{count}</b>&nbsp;&nbsp;" for label, count in label_counts.items()
    )
    st.markdown(badge_html, unsafe_allow_html=True)
    st.markdown("")

    # Column headers with tooltips
    hdr = st.columns([1.5, 1.5, 1.2, 1.2, 0.8, 0.8])
    hdr[0].markdown("**Symbol**")
    hdr[1].markdown("**Price**")
    hdr[2].markdown(f"**{tip('Signal Score', 'Score')}**", unsafe_allow_html=True)
    hdr[3].markdown("**Signal**")
    hdr[4].markdown(f"**{tip('RSI')}**", unsafe_allow_html=True)
    hdr[5].markdown(f"**{tip('Confidence', 'Conf')}**", unsafe_allow_html=True)

    # Per-ticker rows
    for row in rows:
        with st.container():
            c_sym, c_price, c_score, c_signal, c_rsi, c_conf = st.columns(
                [1.5, 1.5, 1.2, 1.2, 0.8, 0.8]
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
            progress_val = max(0.0, min(1.0, (score + 10) / 20))
            c_score.progress(progress_val, text=f"{score:+.1f}")

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

            c_conf.caption(f"{row['confidence']:.0%}")

        # Expander with details
        with st.expander(f"{row['symbol']} — details"):
            if row["sub_scores"]:
                st.markdown(
                    f"**{tip('Signal Score')} Breakdown** "
                    f"({tip('Confidence')}: {row['confidence']:.0%})",
                    unsafe_allow_html=True,
                )
                fig = sub_score_bar(row["sub_scores"])
                st.plotly_chart(fig, width="stretch", key=f"wl_sub_{row['symbol']}")
            if row["reasons"]:
                st.markdown("**Signals driving this score:**")
                for r in row["reasons"]:
                    expl = explain_signal(r)
                    if expl:
                        st.markdown(
                            f'- **{r}** — <span style="color:{COLORS["muted"]};">{expl}</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"- {r}")

            # Actionable targets
            targets = compute_actionable_targets(row["symbol"])
            if targets:
                st.markdown(
                    f"**{tip('Stop Loss', 'Actionable Levels')}:**",
                    unsafe_allow_html=True,
                )
                tc1, tc2, tc3, tc4 = st.columns(4)
                if "stop_loss_long" in targets:
                    tc1.metric(tip("Stop Loss", "Stop"), f"₹{targets['stop_loss_long']:,.0f}")
                if "target_price" in targets:
                    up = targets.get("upside_pct", 0)
                    tc2.metric("Target", f"₹{targets['target_price']:,.0f}", delta=f"{up:+.1f}%")
                if "support_1" in targets:
                    tc3.metric(tip("Support", "S1"), f"₹{targets['support_1']:,.0f}")
                if "resistance_1" in targets:
                    tc4.metric(tip("Resistance", "R1"), f"₹{targets['resistance_1']:,.0f}")
                rr = targets.get("risk_reward_ratio")
                if rr:
                    st.caption(f"Risk/Reward: {rr:.1f}:1")


# ===========================================================================
# TAB 2: Portfolio Signals
# ===========================================================================
with tab_portfolio:
    holdings_df = st.session_state.get("holdings_df")

    if holdings_df is None or holdings_df.empty:
        st.info(
            "No holdings loaded. Connect Kite or upload a CSV from the Home page "
            "to see portfolio signals."
        )
        st.stop()

    def _compute_portfolio_signals(hdf) -> list[dict]:
        results = []
        for _, row in hdf.iterrows():
            sym = row["tradingsymbol"]
            buy_price = float(row["average_price"])
            current_price = float(row["last_price"])
            qty = int(row["quantity"])

            signal = compute_signal_with_cost_basis(sym, buy_price, current_price)

            pnl_pct = (current_price - buy_price) / buy_price if buy_price > 0 else 0

            # News sentiment summary
            news_sentiment = ""
            try:
                from config.settings import settings

                if settings.FINBERT_ENABLED:
                    from llm.sentiment import analyse_sentiment, get_news_headlines

                    headlines = get_news_headlines(sym)
                    if headlines:
                        sentiments = analyse_sentiment(headlines)
                        if sentiments:
                            pos = sum(1 for s in sentiments if s["label"] == "positive")
                            neg = sum(1 for s in sentiments if s["label"] == "negative")
                            news_sentiment = f"{pos} positive, {neg} negative of {len(sentiments)}"
            except Exception:
                pass

            results.append(
                {
                    "symbol": sym,
                    "quantity": qty,
                    "buy_price": buy_price,
                    "current_price": current_price,
                    "pnl_pct": pnl_pct,
                    "score": signal.score,
                    "label": signal.label,
                    "confidence": signal.confidence,
                    "reasons": signal.reasons,
                    "sub_scores": signal.sub_scores,
                    "news_sentiment": news_sentiment,
                    "top_reasons": signal.reasons[:3],
                }
            )
        return sorted(results, key=lambda x: x["score"], reverse=True)

    if st.button("Refresh Portfolio Signals", key="refresh_portfolio"):
        st.session_state.pop("portfolio_signals", None)
        st.rerun()

    if "portfolio_signals" not in st.session_state:
        with st.spinner(f"Computing signals for {len(holdings_df)} holdings..."):
            portfolio_signals = _compute_portfolio_signals(holdings_df)
        st.session_state.portfolio_signals = portfolio_signals
    else:
        portfolio_signals = st.session_state.portfolio_signals

    # Summary metrics
    buy_count = sum(1 for s in portfolio_signals if s["label"] in ("Buy", "Strong Buy"))
    sell_count = sum(1 for s in portfolio_signals if s["label"] in ("Sell", "Strong Sell"))
    hold_count = sum(1 for s in portfolio_signals if s["label"] == "Hold")
    avg_score = (
        sum(s["score"] for s in portfolio_signals) / len(portfolio_signals)
        if portfolio_signals
        else 0
    )

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        metric_card("Buy Signals", str(buy_count), icon="🟢")
    with mc2:
        metric_card("Sell Signals", str(sell_count), icon="🔴")
    with mc3:
        metric_card("Hold", str(hold_count), icon="🟡")
    with mc4:
        metric_card("Avg Score", f"{avg_score:+.1f}", delta_value=avg_score, icon="📊")

    st.divider()

    # Column headers with tooltips
    ph = st.columns([1.5, 1.5, 1.0, 1.0, 1.0, 1.5])
    ph[0].markdown("**Symbol**")
    ph[1].markdown(f"**LTP / {tip('P&L')}**", unsafe_allow_html=True)
    ph[2].markdown(f"**{tip('Signal Score', 'Score')}**", unsafe_allow_html=True)
    ph[3].markdown("**Signal**")
    ph[4].markdown(f"**{tip('Confidence', 'Conf')}**", unsafe_allow_html=True)
    ph[5].markdown("**Reason**")

    # Holdings signal table
    for sig in portfolio_signals:
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1.0, 1.0, 1.0, 1.5])

            c1.markdown(f"**{sig['symbol']}**")

            pnl_val = sig["pnl_pct"] * 100
            c2.markdown(
                f"₹{sig['current_price']:,.0f} {pnl_colored(sig['pnl_pct'], f'{pnl_val:+.1f}%')}",
                unsafe_allow_html=True,
            )

            progress_val = max(0.0, min(1.0, (sig["score"] + 10) / 20))
            c3.progress(progress_val, text=f"{sig['score']:+.1f}")

            c4.markdown(signal_badge(sig["label"]), unsafe_allow_html=True)

            c5.caption(f"Conf: {sig['confidence']:.0%}")

            reason_text = sig["reasons"][0] if sig["reasons"] else "—"
            c6.caption(reason_text)

        with st.expander(f"{sig['symbol']} — analysis"):
            col_chart, col_info = st.columns([2, 1])
            with col_chart:
                if sig["sub_scores"]:
                    st.markdown(
                        f"**{tip('Signal Score')} Breakdown**",
                        unsafe_allow_html=True,
                    )
                    fig = sub_score_bar(sig["sub_scores"])
                    st.plotly_chart(fig, width="stretch", key=f"pf_sub_{sig['symbol']}")
            with col_info:
                st.markdown(f"**Cost Basis:** ₹{sig['buy_price']:,.0f}")
                st.markdown(f"**Qty:** {sig['quantity']}")
                pnl_val = sig["pnl_pct"] * 100
                st.markdown(
                    f"**{tip('Unrealized P&L')}:** "
                    f"{pnl_colored(sig['pnl_pct'], f'₹{pnl_val:+.1f}%')}",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"**{tip('Confidence')}:** {sig['confidence']:.0%}",
                    unsafe_allow_html=True,
                )
                if sig["news_sentiment"]:
                    st.markdown(
                        f"**{tip('Sentiment', 'News')}:** {sig['news_sentiment']}",
                        unsafe_allow_html=True,
                    )

            if len(sig["reasons"]) > 1:
                st.markdown("**All signals:**")
                for r in sig["reasons"]:
                    expl = explain_signal(r)
                    if expl:
                        st.markdown(
                            f'- **{r}** — <span style="color:{COLORS["muted"]};">{expl}</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"- {r}")

    # LLM Portfolio Analysis
    st.divider()
    section_header("AI Portfolio Analysis", icon="🤖")

    if st.button("Generate AI Analysis", key="llm_analysis"):
        from llm.client import chat
        from llm.prompts import build_portfolio_signals_prompt

        prompt_text = build_portfolio_signals_prompt(portfolio_signals)
        with st.spinner("Generating AI analysis..."):
            try:
                response = chat(
                    [
                        {"role": "system", "content": "You are an expert Indian equity analyst."},
                        {"role": "user", "content": prompt_text},
                    ]
                )
                st.session_state.portfolio_llm_analysis = response
            except Exception as e:
                st.error(f"LLM call failed: {e}")

    if "portfolio_llm_analysis" in st.session_state:
        st.markdown(st.session_state.portfolio_llm_analysis)

    # Rebalancing section
    st.divider()
    section_header("Rebalancing Suggestions", icon="⚖️")

    rebal_strategy = st.selectbox(
        "Strategy",
        ["equal_weight", "signal_weighted"],
        format_func=lambda x: "Equal Weight" if x == "equal_weight" else "Signal Weighted",
        key="rebal_strategy",
    )

    if st.button("Generate Rebalance Plan", key="rebal_btn"):
        from analytics.rebalance import suggest_rebalance

        signals_map = {s["symbol"]: s["score"] for s in portfolio_signals}
        suggestions = suggest_rebalance(holdings_df, signals=signals_map, strategy=rebal_strategy)
        st.session_state.rebalance_suggestions = suggestions

    if "rebalance_suggestions" in st.session_state:
        suggestions = st.session_state.rebalance_suggestions
        if not suggestions:
            st.info("Portfolio is balanced — no changes needed.")
        else:
            for sug in suggestions:
                if sug["action"] == "Hold":
                    continue
                action_color = COLORS["profit"] if sug["action"] == "Add" else COLORS["loss"]
                st.markdown(
                    f'<span style="color:{action_color};font-weight:700">{sug["action"]}</span> '
                    f"**{sug['symbol']}** — {sug['shares']} shares "
                    f"(₹{sug['value']:,.0f}) — {sug['reason']}",
                    unsafe_allow_html=True,
                )


# ===========================================================================
# TAB 3: Signal Accuracy
# ===========================================================================
with tab_accuracy:
    section_header("Signal Accuracy", icon="📊")

    from analytics.backtest import compute_accuracy, get_signal_history, get_total_signals_count

    total_signals = get_total_signals_count()

    if total_signals < 5:
        st.info(
            f"Only {total_signals} signals stored so far. Signals are automatically tracked "
            "each time you compute them. Check back after a few weeks for accuracy metrics."
        )
    else:
        days_fwd = st.selectbox("Evaluation period (days)", [7, 14, 30, 60], index=2)
        accuracy_df = compute_accuracy(days_forward=days_fwd)

        if accuracy_df.empty:
            st.info(
                "Not enough historical data yet. Need signals older than "
                f"{days_fwd} days to measure accuracy."
            )
        else:
            st.dataframe(
                accuracy_df,
                column_config={
                    "label": st.column_config.TextColumn("Signal"),
                    "count": st.column_config.NumberColumn("Count", format="%d"),
                    "avg_return_pct": st.column_config.NumberColumn(
                        "Avg Return %", format="%.1f%%"
                    ),
                    "win_rate": st.column_config.NumberColumn("Win Rate", format="%.0f%%"),
                },
                width="stretch",
                hide_index=True,
            )

    st.divider()
    with st.expander("Recent signal history"):
        history = get_signal_history(days=90)
        if history.empty:
            st.info("No signals stored yet.")
        else:
            st.dataframe(
                history,
                column_config={
                    "date": st.column_config.TextColumn("Date"),
                    "symbol": st.column_config.TextColumn("Symbol"),
                    "score": st.column_config.NumberColumn("Score", format="%.1f"),
                    "label": st.column_config.TextColumn("Signal"),
                    "confidence": st.column_config.NumberColumn("Conf", format="%.0f%%"),
                    "price_at_signal": st.column_config.NumberColumn("Price", format="%.2f"),
                },
                width="stretch",
                hide_index=True,
            )
