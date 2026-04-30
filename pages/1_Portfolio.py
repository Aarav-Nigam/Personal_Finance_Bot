from __future__ import annotations

import streamlit as st

from analytics.portfolio import (
    compare_to_nifty,
    compute_pnl,
    compute_xirr,
    get_allocation,
    get_portfolio_summary,
    get_sector_allocation,
    load_orders,
)
from ui.charts import pnl_bar, themed_pie
from ui.glossary import tip
from ui.styles import inject_css, metric_card, section_header
from utils.formatters import fmt_inr, fmt_pct

inject_css()

section_header("Portfolio Overview", icon="💼")

holdings_df = st.session_state.get("holdings_df")

if holdings_df is None or holdings_df.empty:
    st.info("No holdings loaded. Connect Kite or upload a CSV from the sidebar on the Home page.")
    st.stop()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_realized = st.tabs(["📊 Overview", "💰 Realized Profit"])

# ===========================================================================
# TAB 1: Overview (existing content)
# ===========================================================================
with tab_overview:
    df = compute_pnl(holdings_df)
    summary = get_portfolio_summary(holdings_df)

    # Metric cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Total Invested", fmt_inr(summary["total_invested"]), icon="💰")
    with c2:
        metric_card(
            "Current Value",
            fmt_inr(summary["total_current_value"]),
            delta_value=summary["total_pnl"],
        )
    with c3:
        metric_card(
            tip("P&L", "Total P&L"),
            fmt_inr(summary["total_pnl"]),
            delta=fmt_pct(summary["total_pnl_pct"]),
            delta_value=summary["total_pnl"],
        )
    with c4:
        metric_card("Holdings", str(summary["num_holdings"]), icon="📊")
    with c5:
        xirr_val = None
        try:
            orders = load_orders()
            xirr_val = compute_xirr(orders, summary["total_current_value"])
        except Exception:
            pass
        metric_card(
            tip("XIRR"),
            fmt_pct(xirr_val) if xirr_val is not None else "N/A",
            icon="🎯",
        )

    st.divider()

    # Nifty comparison
    if xirr_val is not None:
        try:
            import pandas as pd

            orders_df = load_orders()
            earliest = pd.to_datetime(orders_df["order_timestamp"]).min().date()
            comparison = compare_to_nifty(xirr_val, earliest)
            if comparison:
                section_header("Performance vs Nifty 50", icon="📈")
                nc1, nc2, nc3 = st.columns(3)
                with nc1:
                    metric_card(
                        tip("XIRR", "Your XIRR"),
                        fmt_pct(comparison["portfolio_xirr"]),
                        delta_value=comparison["portfolio_xirr"],
                    )
                with nc2:
                    metric_card(tip("CAGR", "Nifty CAGR"), fmt_pct(comparison["nifty_cagr"]))
                with nc3:
                    alpha = comparison["alpha"]
                    metric_card(
                        tip("Alpha"),
                        fmt_pct(alpha),
                        delta=("Outperforming" if alpha > 0 else "Underperforming"),
                        delta_value=alpha,
                    )
                st.divider()
        except Exception:
            pass

    # Holdings table
    section_header("Holdings", icon="📋")

    display_cols = ["tradingsymbol", "quantity", "average_price", "last_price"]
    display_df = df[display_cols].copy()
    display_df["invested"] = df["invested_value"]
    display_df["current_value"] = df["current_value"]
    display_df["pnl"] = df["pnl"]
    display_df["pnl_pct"] = df["pnl_pct"]

    if "day_change" in df.columns:
        display_df["day_change"] = df["day_change"]
    if "day_change_percentage" in df.columns:
        display_df["day_chg_pct"] = df["day_change_percentage"]

    col_config = {
        "tradingsymbol": st.column_config.TextColumn("Symbol"),
        "quantity": st.column_config.NumberColumn("Qty", format="%d"),
        "average_price": st.column_config.NumberColumn("Avg Cost", format="%.2f"),
        "last_price": st.column_config.NumberColumn("LTP", format="%.2f"),
        "invested": st.column_config.NumberColumn("Invested", format="%.0f"),
        "current_value": st.column_config.NumberColumn("Current", format="%.0f"),
        "pnl": st.column_config.NumberColumn("P&L", format="%.0f"),
        "pnl_pct": st.column_config.NumberColumn("P&L %", format="%.2f%%"),
    }
    if "day_change" in display_df.columns:
        col_config["day_change"] = st.column_config.NumberColumn("Day Chg", format="%.2f")
    if "day_chg_pct" in display_df.columns:
        col_config["day_chg_pct"] = st.column_config.NumberColumn("Day %", format="%.2f%%")

    st.dataframe(display_df, column_config=col_config, width="stretch", hide_index=True)

    st.divider()

    # Allocation charts
    section_header("Allocation", icon="🥧")
    left, right = st.columns(2)

    with left:
        allocation = get_allocation(holdings_df)
        inst_alloc = allocation.get("instrument_type", {})
        if inst_alloc:
            fig = themed_pie(
                list(inst_alloc.keys()), list(inst_alloc.values()), "By Instrument Type"
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Instrument type data not available.")

    with right:
        with st.spinner("Loading sector data..."):
            sector_alloc = get_sector_allocation(holdings_df)
        if sector_alloc:
            fig = themed_pie(list(sector_alloc.keys()), list(sector_alloc.values()), "By Sector")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sector data not available.")

    st.divider()

    # Top gainers / losers
    section_header("Top Movers", icon="🔥")
    g_col, l_col = st.columns(2)

    with g_col:
        gainers = summary["top_gainers"]
        if not gainers.empty:
            fig_g = pnl_bar(
                gainers["tradingsymbol"].tolist(),
                (gainers["pnl_pct"] * 100).tolist(),
                "Top 5 Gainers (%)",
            )
            fig_g.update_layout(yaxis_ticksuffix="%")
            st.plotly_chart(fig_g, width="stretch")

    with l_col:
        losers = summary["top_losers"]
        if not losers.empty:
            fig_l = pnl_bar(
                losers["tradingsymbol"].tolist(),
                (losers["pnl_pct"] * 100).tolist(),
                "Top 5 Losers (%)",
            )
            fig_l.update_layout(yaxis_ticksuffix="%")
            st.plotly_chart(fig_l, width="stretch")


# ===========================================================================
# TAB 2: Realized Profit
# ===========================================================================
with tab_realized:
    import pandas as pd

    from analytics.realized_pnl import compute_realized_pnl

    section_header("Realized Profit", icon="💰")
    st.caption(
        "Upload your Kite Console Tradebook CSV to see actual profit from completed trades. "
        "Go to Console → Orders → Tradebook → Download."
    )

    uploaded = st.file_uploader("Upload Tradebook CSV", type=["csv"], key="tradebook_upload")

    if uploaded is not None:
        try:
            raw_df = pd.read_csv(uploaded)
            result = compute_realized_pnl(raw_df)
            st.session_state.realized_pnl = result
        except Exception as e:
            st.error(f"Error parsing CSV: {e}")

    result = st.session_state.get("realized_pnl")

    if result is None:
        st.info("Upload a tradebook CSV to see your realized profit analysis.")
        st.stop()

    # Metric cards
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        metric_card(
            tip("Realized P&L", "Total Realized P&L"),
            fmt_inr(result["total_realized_pnl"]),
            delta_value=result["total_realized_pnl"],
            icon="💵",
        )
    with mc2:
        metric_card(tip("Win Rate"), f"{result['win_rate'] * 100:.0f}%", icon="🎯")
    with mc3:
        metric_card(
            tip("Holding Period", "Avg Holding"),
            f"{result['avg_holding_days']:.0f} days",
            icon="📅",
        )
    with mc4:
        metric_card("Total Trades", str(result["total_trades"]), icon="📊")

    st.divider()

    # Tax classification
    section_header("Tax Breakdown", icon="🧾")
    tc1, tc2 = st.columns(2)
    with tc1:
        stcg = result["stcg_total"]
        stcg_tax = max(0, stcg * 0.20) if stcg > 0 else 0
        metric_card(
            tip("STCG", "Short-Term CG"),
            fmt_inr(stcg),
            delta=f"Tax ~{fmt_inr(stcg_tax)}" if stcg > 0 else None,
            delta_value=stcg,
        )
    with tc2:
        ltcg = result["ltcg_total"]
        ltcg_exempt = 125000
        ltcg_taxable = max(0, ltcg - ltcg_exempt) if ltcg > 0 else 0
        ltcg_tax = ltcg_taxable * 0.125
        metric_card(
            tip("LTCG", "Long-Term CG"),
            fmt_inr(ltcg),
            delta=f"Tax ~{fmt_inr(ltcg_tax)} (after ₹1.25L exemption)" if ltcg > 0 else None,
            delta_value=ltcg,
        )

    st.divider()

    # Monthly P&L chart
    if result["monthly_pnl"]:
        section_header("Monthly Realized P&L", icon="📈")
        months = list(result["monthly_pnl"].keys())
        values = list(result["monthly_pnl"].values())
        fig = pnl_bar(months, values, "Monthly Realized P&L")
        fig.update_layout(xaxis_title="Month", yaxis_title="P&L (₹)")
        st.plotly_chart(fig, width="stretch")

    st.divider()

    # Best / Worst trades
    section_header("Highlights", icon="🏆")
    bw1, bw2 = st.columns(2)
    with bw1:
        best = result["best_trade"]
        if best:
            metric_card(
                "Best Trade",
                f"{best['symbol']} +{fmt_inr(best['pnl'])}",
                delta=f"{best['pnl_pct']:+.1f}%",
                delta_value=best["pnl"],
            )
    with bw2:
        worst = result["worst_trade"]
        if worst:
            metric_card(
                "Worst Trade",
                f"{worst['symbol']} {fmt_inr(worst['pnl'])}",
                delta=f"{worst['pnl_pct']:+.1f}%",
                delta_value=worst["pnl"],
            )

    st.divider()

    # Trades detail table
    section_header("All Trades", icon="📋")
    if result["trades"]:
        trades_df = pd.DataFrame(result["trades"])
        trades_df["buy_date"] = pd.to_datetime(trades_df["buy_date"]).dt.strftime("%Y-%m-%d")
        trades_df["sell_date"] = pd.to_datetime(trades_df["sell_date"]).dt.strftime("%Y-%m-%d")

        col_config_trades = {
            "symbol": st.column_config.TextColumn("Symbol"),
            "buy_date": st.column_config.TextColumn("Buy Date"),
            "sell_date": st.column_config.TextColumn("Sell Date"),
            "quantity": st.column_config.NumberColumn("Qty", format="%d"),
            "buy_price": st.column_config.NumberColumn("Buy ₹", format="%.2f"),
            "sell_price": st.column_config.NumberColumn("Sell ₹", format="%.2f"),
            "pnl": st.column_config.NumberColumn("P&L ₹", format="%.0f"),
            "pnl_pct": st.column_config.NumberColumn("P&L %", format="%.1f%%"),
            "holding_days": st.column_config.NumberColumn("Days", format="%d"),
            "type": st.column_config.TextColumn("Type"),
        }
        st.dataframe(
            trades_df,
            column_config=col_config_trades,
            width="stretch",
            hide_index=True,
        )

    if result.get("unmatched_sells"):
        with st.expander(f"⚠️ {len(result['unmatched_sells'])} unmatched sells"):
            st.caption(
                "These sells had no matching buy orders in the uploaded data. "
                "The buys may have occurred before the date range of your CSV."
            )
            st.dataframe(pd.DataFrame(result["unmatched_sells"]), hide_index=True)
