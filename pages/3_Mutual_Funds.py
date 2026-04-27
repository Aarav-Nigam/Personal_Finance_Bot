from __future__ import annotations

from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from analytics.mf_analytics import compare_funds, compute_sip_xirr, get_category_returns
from data.mf_client import get_fund_details, get_fund_nav, search_fund
from ui.styles import inject_css, metric_card, section_header
from ui.theme import COLORS, apply_plotly_defaults
from utils.formatters import fmt_pct

inject_css()

section_header("Mutual Funds", icon="chart_increasing")

tab_search, tab_sip, tab_leaderboard = st.tabs(
    ["Fund Search & NAV", "SIP XIRR Calculator", "Category Leaderboard"]
)

with tab_search:
    query = st.text_input("Search fund by name or AMC").strip()
    if query:
        with st.spinner("Searching..."):
            results = search_fund(query)
        if not results:
            st.warning("No funds found.")
        else:
            options = {
                f"{r['schemeName']} ({r['schemeCode']})": r["schemeCode"] for r in results[:20]
            }
            selected = st.selectbox("Select a fund", list(options.keys()))
            if selected:
                scheme_code = options[selected]

                period_map = {
                    "1M": 30,
                    "3M": 90,
                    "6M": 180,
                    "1Y": 365,
                    "3Y": 1095,
                    "5Y": 1825,
                    "Max": None,
                }
                period = st.selectbox("Period", list(period_map.keys()), index=3)

                with st.spinner("Loading NAV data..."):
                    nav_df = get_fund_nav(scheme_code)
                    details = get_fund_details(scheme_code)

                if nav_df.empty:
                    st.error("Could not fetch NAV data.")
                else:
                    days = period_map[period]
                    if days:
                        cutoff = date.today() - timedelta(days=days)
                        plot_df = nav_df[nav_df["date"] >= cutoff]
                    else:
                        plot_df = nav_df

                    fig = px.area(
                        plot_df,
                        x="date",
                        y="nav",
                        title=f"NAV — {selected}",
                    )
                    fig.update_traces(
                        line=dict(color=COLORS["primary"], width=2),
                        fillcolor=f"{COLORS['primary']}18",
                    )
                    fig.update_layout(xaxis_title="", yaxis_title="NAV (INR)")
                    apply_plotly_defaults(fig)
                    st.plotly_chart(fig, use_container_width=True)

                    if details:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            metric_card("Fund House", details.get("fund_house", "N/A"))
                        with c2:
                            metric_card("Category", details.get("scheme_category", "N/A"))
                        with c3:
                            metric_card("Type", details.get("scheme_type", "N/A"))

    st.divider()
    with st.expander("Compare Funds"):
        st.write("Enter 2-3 scheme codes to overlay normalized NAV (base 100).")
        compare_input = st.text_input(
            "Scheme codes (comma-separated)", placeholder="119551, 120503"
        )
        if compare_input:
            codes = [int(c.strip()) for c in compare_input.split(",") if c.strip().isdigit()]
            if len(codes) >= 2:
                with st.spinner("Comparing..."):
                    comp_df = compare_funds(codes)
                if not comp_df.empty:
                    fig = px.line(
                        comp_df,
                        x="date",
                        y="nav",
                        color="scheme_code",
                        title="Fund Comparison (Base 100)",
                    )
                    apply_plotly_defaults(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Could not fetch comparison data.")
            else:
                st.info("Enter at least 2 scheme codes.")

with tab_sip:
    section_header("SIP XIRR Calculator", icon="calculator")
    st.write("Enter your SIP installments and current investment value.")

    if "sip_rows" not in st.session_state:
        st.session_state.sip_rows = [
            {"date": date.today() - timedelta(days=365), "amount": 10000.0}
        ]

    edited = st.data_editor(
        st.session_state.sip_rows,
        column_config={
            "date": st.column_config.DateColumn("Payment Date"),
            "amount": st.column_config.NumberColumn("Amount (INR)", min_value=0),
        },
        num_rows="dynamic",
        use_container_width=True,
    )
    st.session_state.sip_rows = edited

    current_value = st.number_input("Current Investment Value (INR)", min_value=0.0, value=0.0)

    if st.button("Calculate XIRR"):
        payments = [(row["date"], row["amount"]) for row in edited if row.get("amount")]
        if not payments or current_value <= 0:
            st.warning("Enter at least one payment and a positive current value.")
        else:
            result = compute_sip_xirr(payments, current_value)
            if result is not None:
                st.success(f"SIP XIRR: **{fmt_pct(result)}** annualised")
            else:
                st.error("Could not compute XIRR. Check your inputs.")

with tab_leaderboard:
    section_header("Category Leaderboard", icon="trophy")
    categories = ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "ELSS", "Debt", "Index"]
    category = st.selectbox("Category", categories)

    if st.button("Load Leaderboard"):
        with st.spinner(f"Fetching top {category} funds..."):
            lb = get_category_returns(category, top_n=10)
        if lb.empty:
            st.warning("No funds found for this category.")
        else:
            display = lb.copy()
            for col in ["1y_return", "3y_return", "5y_return"]:
                if col in display.columns:
                    display[col] = display[col].apply(
                        lambda x: fmt_pct(x) if x is not None else "N/A"
                    )
            display.columns = ["Fund Name", "Code", "1Y Return", "3Y Return", "5Y Return"]
            st.dataframe(display, use_container_width=True, hide_index=True)
