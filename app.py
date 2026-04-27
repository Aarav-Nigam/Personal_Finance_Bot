import io

import pandas as pd
import streamlit as st

from config.settings import settings

st.set_page_config(
    page_title="PersonalFinanceBot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "holdings_df" not in st.session_state:
    st.session_state.holdings_df = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = settings.LLM_PROVIDER
if "kite_connected" not in st.session_state:
    st.session_state.kite_connected = False

st.sidebar.title("PersonalFinanceBot")
st.sidebar.caption("v0.1.0 — Free & Open Source")


def _parse_csv(uploaded_file) -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
    cols_lower = {c: c.lower().strip() for c in raw.columns}
    raw = raw.rename(columns=cols_lower)

    col_map = {}
    for c in raw.columns:
        if "instrument" in c or "symbol" in c or "trading" in c:
            col_map["tradingsymbol"] = c
        elif c in ("qty", "quantity"):
            col_map["quantity"] = c
        elif "avg" in c and ("cost" in c or "price" in c):
            col_map["average_price"] = c
        elif c in ("ltp", "last_price", "cur. val"):
            col_map["last_price"] = c

    df = pd.DataFrame()
    df["tradingsymbol"] = raw[col_map.get("tradingsymbol", raw.columns[0])].astype(str)
    df["quantity"] = pd.to_numeric(raw[col_map.get("quantity", raw.columns[1])], errors="coerce")
    df["average_price"] = pd.to_numeric(
        raw[col_map.get("average_price", raw.columns[2])], errors="coerce"
    )
    if "last_price" in col_map:
        df["last_price"] = pd.to_numeric(raw[col_map["last_price"]], errors="coerce")
    else:
        df["last_price"] = df["average_price"]
    return df.dropna(subset=["quantity", "average_price"])


if st.session_state.holdings_df is None:
    try:
        from analytics.portfolio import load_holdings

        df = load_holdings()
        if not df.empty:
            st.session_state.holdings_df = df
            st.session_state.kite_connected = True
    except Exception:
        st.session_state.kite_connected = False

if not st.session_state.kite_connected:
    st.sidebar.warning("Kite not connected. Upload a CSV or run `python scripts/kite_auth.py`.")
    uploaded = st.sidebar.file_uploader("Upload holdings CSV", type=["csv"])
    if uploaded is not None:
        st.session_state.holdings_df = _parse_csv(uploaded)
else:
    st.sidebar.success("Connected to Kite")

from ui.styles import inject_css, metric_card, section_header  # noqa: E402

inject_css()

# ---------------------------------------------------------------------------
# Welcome banner
# ---------------------------------------------------------------------------
if st.session_state.kite_connected:
    try:
        from analytics.account import load_profile

        profile = load_profile()
        user_name = profile.get("user_name", "Investor")
        st.title(f"Welcome, {user_name}")
    except Exception:
        st.title("PersonalFinanceBot")
else:
    st.title("PersonalFinanceBot")

# ---------------------------------------------------------------------------
# Portfolio snapshot
# ---------------------------------------------------------------------------
holdings_df = st.session_state.get("holdings_df")

if holdings_df is not None and not holdings_df.empty:
    from analytics.portfolio import (
        compute_pnl,
        compute_xirr,
        get_market_status,
        get_portfolio_summary,
        load_orders,
    )
    from utils.formatters import fmt_inr, fmt_pct

    summary = get_portfolio_summary(holdings_df)
    df_pnl = compute_pnl(holdings_df)

    section_header("Portfolio Snapshot", icon="briefcase")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            "Total Value",
            fmt_inr(summary["total_current_value"]),
            icon="wallet",
        )
    with c2:
        day_pnl = float(df_pnl["day_change"].sum()) if "day_change" in df_pnl.columns else None
        if day_pnl is not None:
            metric_card(
                "Day P&L",
                fmt_inr(day_pnl),
                delta=fmt_pct(day_pnl / summary["total_current_value"])
                if summary["total_current_value"]
                else None,
                delta_value=day_pnl,
                icon="chart_increasing" if day_pnl >= 0 else "chart_decreasing",
            )
        else:
            metric_card("Day P&L", "N/A", icon="chart_increasing")
    with c3:
        metric_card(
            "Overall P&L",
            fmt_inr(summary["total_pnl"]),
            delta=fmt_pct(summary["total_pnl_pct"]),
            delta_value=summary["total_pnl"],
        )
    with c4:
        xirr_val = None
        try:
            orders = load_orders()
            xirr_val = compute_xirr(orders, summary["total_current_value"])
        except Exception:
            pass
        metric_card(
            "Portfolio XIRR",
            fmt_pct(xirr_val) if xirr_val is not None else "N/A",
            icon="target",
        )

    # ---------------------------------------------------------------------------
    # Market pulse
    # ---------------------------------------------------------------------------
    section_header("Market Pulse", icon="globe_showing_Asia-Australia")

    mkt = get_market_status()
    m1, m2, m3 = st.columns(3)
    with m1:
        nifty_str = f"{mkt['nifty_level']:,.0f}" if mkt["nifty_level"] else "N/A"
        metric_card(
            "Nifty 50",
            nifty_str,
            delta=fmt_pct(mkt["nifty_change_pct"]) if mkt["nifty_change_pct"] is not None else None,
            delta_value=mkt["nifty_change_pct"],
        )
    with m2:
        status = mkt["status"]
        color = "#00C853" if status == "Open" else "#FF9800" if status == "Pre-Open" else "#9E9E9E"
        st.markdown(
            f"""
            <div class="pfb-card pfb-card-neutral">
                <div class="card-label">Market Status</div>
                <div class="card-value" style="color:{color}">{status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        if st.session_state.kite_connected:
            try:
                from analytics.account import get_margin_summary

                margins = get_margin_summary()
                metric_card("Available Cash", fmt_inr(margins["cash"]), icon="money_bag")
            except Exception:
                metric_card("Available Cash", "N/A", icon="money_bag")
        else:
            metric_card("Available Cash", "Connect Kite", icon="money_bag")

    # ---------------------------------------------------------------------------
    # Top movers
    # ---------------------------------------------------------------------------
    section_header("Top Movers", icon="fire")
    g_col, l_col = st.columns(2)
    gainers = summary["top_gainers"].head(3)
    losers = summary["top_losers"].head(3)

    with g_col:
        st.markdown("**Top Gainers**")
        for _, row in gainers.iterrows():
            pct = row["pnl_pct"]
            color = "#00C853"
            st.markdown(
                f'<span style="font-weight:600">{row["tradingsymbol"]}</span> '
                f'<span style="color:{color};font-weight:600">{pct * 100:+.1f}%</span>',
                unsafe_allow_html=True,
            )
    with l_col:
        st.markdown("**Top Losers**")
        for _, row in losers.iterrows():
            pct = row["pnl_pct"]
            color = "#FF1744"
            st.markdown(
                f'<span style="font-weight:600">{row["tradingsymbol"]}</span> '
                f'<span style="color:{color};font-weight:600">{pct * 100:+.1f}%</span>',
                unsafe_allow_html=True,
            )

else:
    st.info("Connect Kite or upload a CSV from the sidebar to see your dashboard.")

# ---------------------------------------------------------------------------
# Quick links
# ---------------------------------------------------------------------------
st.divider()
section_header("Quick Links")
ql1, ql2, ql3, ql4 = st.columns(4)
ql1.page_link("pages/1_Portfolio.py", label="Portfolio", icon=":material/account_balance:")
ql2.page_link("pages/2_Stocks.py", label="Stock Analysis", icon=":material/candlestick_chart:")
ql3.page_link("pages/3_Mutual_Funds.py", label="Mutual Funds", icon=":material/trending_up:")
ql4.page_link("pages/4_Signals.py", label="Signals", icon=":material/notifications:")
ql5, ql6, ql7, ql8 = st.columns(4)
ql5.page_link("pages/5_Tax.py", label="Tax Calculator", icon=":material/receipt_long:")
ql6.page_link("pages/6_AI_Advisor.py", label="AI Advisor", icon=":material/smart_toy:")
ql7.page_link("pages/7_Positions.py", label="Positions & Orders", icon=":material/swap_vert:")
ql8.page_link("pages/8_Account.py", label="Account", icon=":material/person:")
