import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from analytics.fundamentals import get_fundamentals
from analytics.signals import compute_signal
from analytics.technicals import add_all_indicators
from data.market_data import get_analyst_recs, get_ohlcv
from ui.glossary import tip
from ui.styles import inject_css, metric_card, section_header, signal_badge
from ui.theme import COLORS, apply_plotly_defaults
from utils.formatters import fmt_inr

inject_css()

section_header("Stock Analysis", icon="📈")

ticker = st.text_input("Enter NSE ticker (e.g., RELIANCE)").strip().upper()
if not ticker:
    st.info("Enter a ticker symbol above to begin analysis.")
    st.stop()

col_period, col_ema, col_bb = st.columns([1, 2, 1])
with col_period:
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
with col_ema:
    ema_toggles = st.multiselect("EMA Overlays", ["EMA20", "EMA50", "EMA200"], default=["EMA200"])
with col_bb:
    show_bb = st.checkbox("Bollinger Bands", value=False)

with st.spinner(f"Loading {ticker}..."):
    df = get_ohlcv(ticker, period=period)

if df.empty:
    st.error(f"No data found for {ticker}. Check the ticker symbol.")
    st.stop()

df = add_all_indicators(df)
last = df.iloc[-1]

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    row_heights=[0.6, 0.2, 0.2],
    vertical_spacing=0.03,
    subplot_titles=("Price", "RSI (14)", "MACD"),
)

fig.add_trace(
    go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="OHLC",
        showlegend=False,
        increasing_line_color=COLORS["profit"],
        decreasing_line_color=COLORS["loss"],
    ),
    row=1,
    col=1,
)

ema_map = {
    "EMA20": ("ema20", COLORS["accent"]),
    "EMA50": ("ema50", COLORS["primary"]),
    "EMA200": ("ema200", "#9C27B0"),
}
for label in ema_toggles:
    col_name, color = ema_map[label]
    if col_name in df.columns:
        fig.add_trace(
            go.Scatter(x=df["date"], y=df[col_name], name=label, line=dict(width=1, color=color)),
            row=1,
            col=1,
        )

if show_bb and "bb_upper" in df.columns:
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["bb_upper"],
            name="BB Upper",
            line=dict(width=1, dash="dot", color=COLORS["muted"]),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["bb_lower"],
            name="BB Lower",
            line=dict(width=1, dash="dot", color=COLORS["muted"]),
            fill="tonexty",
            fillcolor="rgba(158,158,158,0.1)",
        ),
        row=1,
        col=1,
    )

if "rsi14" in df.columns:
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["rsi14"], name="RSI", line=dict(color="#E91E63", width=1)),
        row=2,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["loss"], opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["profit"], opacity=0.5, row=2, col=1)

if "macd" in df.columns:
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["macd"], name="MACD", line=dict(color=COLORS["primary"], width=1)
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["macd_signal"],
            name="Signal",
            line=dict(color=COLORS["accent"], width=1),
        ),
        row=3,
        col=1,
    )
    colors = [COLORS["profit"] if v >= 0 else COLORS["loss"] for v in df["macd_hist"].fillna(0)]
    fig.add_trace(
        go.Bar(
            x=df["date"], y=df["macd_hist"], name="Histogram", marker_color=colors, showlegend=False
        ),
        row=3,
        col=1,
    )

fig.update_layout(
    height=800,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=40, b=20),
)
fig.update_yaxes(title_text="Price (INR)", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
fig.update_yaxes(title_text="MACD", row=3, col=1)
apply_plotly_defaults(fig)

st.plotly_chart(fig, width="stretch")

st.divider()

fund = get_fundamentals(ticker)

left_col, right_col = st.columns(2)

with left_col:
    section_header("Fundamentals", icon="📋")

    def _fmt_val(val, is_pct=False):
        if val is None:
            return "N/A"
        if is_pct:
            return f"{val * 100:.1f}%"
        return f"{val:.2f}"

    f1, f2 = st.columns(2)
    with f1:
        metric_card(tip("PE", "P/E (TTM)"), _fmt_val(fund.get("pe")))
        metric_card(tip("EV/EBITDA"), _fmt_val(fund.get("ev_ebitda")))
        metric_card(tip("ROE"), _fmt_val(fund.get("roe"), is_pct=True))
        metric_card(tip("Debt/Equity"), _fmt_val(fund.get("debt_equity")))
        metric_card(tip("Revenue Growth"), _fmt_val(fund.get("revenue_growth_yoy"), is_pct=True))
    with f2:
        metric_card(tip("Forward PE", "Forward P/E"), _fmt_val(fund.get("forward_pe")))
        metric_card(tip("PB", "P/B"), _fmt_val(fund.get("pb")))
        metric_card("ROCE", _fmt_val(fund.get("roce"), is_pct=True))
        metric_card("EPS (TTM)", _fmt_val(fund.get("eps_ttm")))
        metric_card(tip("Dividend Yield"), _fmt_val(fund.get("dividend_yield"), is_pct=True))

with right_col:
    section_header(tip("52-Week Range") + " ", icon="📅")
    high_52 = fund.get("fifty_two_week_high")
    low_52 = fund.get("fifty_two_week_low")
    current_price = float(last["close"])

    if high_52 and low_52 and high_52 > low_52:
        position = (current_price - low_52) / (high_52 - low_52)
        position = max(0.0, min(1.0, position))
        st.progress(position)
        c1, c2, c3 = st.columns(3)
        c1.caption(f"Low: {fmt_inr(low_52)}")
        c2.caption(f"Current: {fmt_inr(current_price)}")
        c3.caption(f"High: {fmt_inr(high_52)}")
    else:
        st.info("52-week data not available.")

    if fund.get("sector"):
        metric_card("Sector", fund["sector"])
    if fund.get("industry"):
        metric_card("Industry", fund["industry"])
    if fund.get("market_cap"):
        metric_card("Market Cap", fmt_inr(fund["market_cap"]))

with st.expander("Analyst Recommendations"):
    recs = get_analyst_recs(ticker)
    if not recs.empty:
        st.dataframe(recs.tail(10), width="stretch", hide_index=True)
    else:
        st.info("No analyst recommendations available.")

st.divider()
section_header("Signal", icon="🔔")

with st.spinner("Computing signal..."):
    signal = compute_signal(ticker)

sig_col1, sig_col2, sig_col3 = st.columns([1, 1, 2])
with sig_col1:
    metric_card(
        tip("Signal Score", "Score"),
        f"{signal.score:+.1f}",
        delta_value=signal.score,
    )
with sig_col2:
    st.markdown(signal_badge(signal.label), unsafe_allow_html=True)
    st.markdown(
        f"{tip('Confidence')}: {signal.confidence:.0%}",
        unsafe_allow_html=True,
    )
with sig_col3:
    if signal.reasons:
        for reason in signal.reasons[:5]:
            st.markdown(f"- {reason}")

if signal.sub_scores:
    from ui.charts import sub_score_bar

    fig = sub_score_bar(signal.sub_scores)
    st.plotly_chart(fig, width="stretch")

# Actionable targets
with st.expander("Actionable Targets (Stop-Loss, Price Target, Support/Resistance)"):
    from analytics.targets import compute_actionable_targets

    portfolio_value = None
    holdings_df = st.session_state.get("holdings_df")
    if holdings_df is not None and not holdings_df.empty:
        portfolio_value = float((holdings_df["last_price"] * holdings_df["quantity"]).sum())

    targets = compute_actionable_targets(ticker, portfolio_value=portfolio_value)

    if targets.get("atr"):
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            metric_card(
                tip("Stop Loss"),
                fmt_inr(targets["stop_loss_long"]),
                icon="🛑",
            )
        with t2:
            target_str = fmt_inr(targets["target_price"]) if targets["target_price"] else "N/A"
            metric_card("Target Price", target_str, icon="🎯")
        with t3:
            metric_card(
                tip("Support", "Support (S1)"),
                fmt_inr(targets["support_1"]),
                icon="🟢",
            )
        with t4:
            metric_card(
                tip("Resistance", "Resistance (R1)"),
                fmt_inr(targets["resistance_1"]),
                icon="🔴",
            )

        cap_parts = [f"ATR: {targets['atr']:.2f}"]
        if targets.get("upside_pct") is not None:
            cap_parts.append(f"Upside: {targets['upside_pct']:+.1f}%")
        if targets.get("risk_reward_ratio") is not None:
            cap_parts.append(f"Risk/Reward: {targets['risk_reward_ratio']:.1f}:1")
        if targets.get("position_size_shares") and targets["position_size_shares"] > 0:
            cap_parts.append(
                f"Position size: {targets['position_size_shares']} shares "
                f"({targets['position_size_pct']:.1f}% of portfolio)"
            )
        st.caption(" · ".join(cap_parts))
    else:
        st.info("Insufficient price data to compute targets.")

st.divider()
with st.expander("News & Sentiment"):
    from config.settings import settings as _settings

    if _settings.FINBERT_ENABLED:
        from llm.sentiment import analyse_sentiment, get_news_headlines

        headlines = get_news_headlines(ticker)
        if headlines:
            with st.spinner("Analysing sentiment..."):
                sentiments = analyse_sentiment(headlines)
            if sentiments:
                import pandas as pd

                sent_df = pd.DataFrame(sentiments)
                sent_df.columns = ["Headline", "Sentiment", "Confidence"]
                st.dataframe(sent_df, width="stretch", hide_index=True)
                pos = sum(1 for s in sentiments if s["label"] == "positive")
                st.caption(f"Overall: {pos}/{len(sentiments)} positive headlines")
            else:
                st.info("Sentiment analysis not available.")
        else:
            st.info("No recent news found.")
    else:
        st.info("FinBERT disabled. Set FINBERT_ENABLED=true in .env to enable.")
