from __future__ import annotations

import streamlit as st

from ui.styles import inject_css, metric_card, section_header

inject_css()

# ---------------------------------------------------------------------------
# Welcome banner
# ---------------------------------------------------------------------------
_greeting = "Welcome back"
_user_name = ""
if st.session_state.kite_connected:
    try:
        from analytics.account import load_profile

        profile = load_profile()
        _user_name = profile.get("user_name", "")
    except Exception:
        pass

_name_html = f", {_user_name}" if _user_name else ""
_status_dot = (
    '<span style="color:#00E676">&#9679;</span> Live'
    if st.session_state.kite_connected
    else '<span style="color:#9E9E9E">&#9679;</span> Offline'
)
st.markdown(
    f"""
    <div style="
        background: linear-gradient(135deg, #1A1D23 0%, #0E1117 100%);
        border: 1px solid #2D3139;
        border-radius: 14px;
        padding: 32px 36px 24px;
        margin-bottom: 24px;
    ">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="font-size:2.2rem; font-weight:700; color:#E0E0E0; line-height:1.2;">
                    📊 PersonalFinanceBot
                </div>
                <div style="font-size:1.1rem; color:#9E9E9E; margin-top:6px;">
                    {_greeting}{_name_html} &mdash; your portfolio command center
                </div>
            </div>
            <div style="
                background: #0E1117;
                border: 1px solid #2D3139;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 0.85rem;
                color: #9E9E9E;
            ">
                {_status_dot} &nbsp;&bull;&nbsp; v0.1.0
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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

    section_header("Portfolio Snapshot", icon="💼")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            "Total Value",
            fmt_inr(summary["total_current_value"]),
            icon="👛",
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
                icon="📈" if day_pnl >= 0 else "📉",
            )
        else:
            metric_card("Day P&L", "N/A", icon="📈")
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
            icon="🎯",
        )

    # ---------------------------------------------------------------------------
    # Market pulse
    # ---------------------------------------------------------------------------
    section_header("Market Pulse", icon="🌏")

    mkt = get_market_status()
    m1, m2, m3 = st.columns(3)
    with m1:
        nifty_str = f"{mkt['nifty_level']:,.0f}" if mkt["nifty_level"] else "N/A"
        metric_card(
            "Nifty 50",
            nifty_str,
            delta=fmt_pct(mkt["nifty_change_pct"])
            if mkt["nifty_change_pct"] is not None
            else None,
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
                metric_card("Available Cash", fmt_inr(margins["cash"]), icon="💰")
            except Exception:
                metric_card("Available Cash", "N/A", icon="💰")
        else:
            metric_card("Available Cash", "Connect Kite", icon="💰")

    # ---------------------------------------------------------------------------
    # Top movers
    # ---------------------------------------------------------------------------
    section_header("Top Movers", icon="🔥")
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
