from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from analytics.tax import TaxLot, classify_lots, compute_tax, suggest_tax_harvesting
from ui.charts import themed_pie
from ui.styles import inject_css, metric_card, section_header
from utils.formatters import fmt_inr

inject_css()

section_header("Tax Calculator", icon="🧾")

fy = st.selectbox("Financial Year", ["2024-25", "2023-24"])

tab_lots, tab_harvest = st.tabs(["Tax Lot Calculator", "Tax-Loss Harvesting"])

with tab_lots:
    st.subheader("Enter your sold lots")

    if "tax_lots" not in st.session_state:
        st.session_state.tax_lots = [
            {
                "symbol": "RELIANCE",
                "buy_date": date.today() - timedelta(days=400),
                "sell_date": date.today(),
                "qty": 10,
                "buy_price": 2400.0,
                "sell_price": 2800.0,
            }
        ]

    edited = st.data_editor(
        st.session_state.tax_lots,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "buy_date": st.column_config.DateColumn("Buy Date"),
            "sell_date": st.column_config.DateColumn("Sell Date"),
            "qty": st.column_config.NumberColumn("Quantity", min_value=1),
            "buy_price": st.column_config.NumberColumn("Buy Price", min_value=0),
            "sell_price": st.column_config.NumberColumn("Sell Price", min_value=0),
        },
        num_rows="dynamic",
        width="stretch",
    )
    st.session_state.tax_lots = edited

    if st.button("Calculate Tax"):
        lots = []
        for row in edited:
            if row.get("symbol") and row.get("qty"):
                lots.append(
                    TaxLot(
                        symbol=row["symbol"],
                        buy_date=row["buy_date"],
                        sell_date=row["sell_date"],
                        qty=int(row["qty"]),
                        buy_price=float(row["buy_price"]),
                        sell_price=float(row["sell_price"]),
                    )
                )

        if not lots:
            st.warning("Enter at least one lot.")
        else:
            classified = classify_lots(lots, fy)
            summary = compute_tax(classified, fy)
            st.session_state.tax_classified = classified
            st.session_state.tax_summary = summary

    classified = st.session_state.get("tax_classified")
    summary = st.session_state.get("tax_summary")
    if classified is not None and summary is not None:
        st.subheader("Classified Lots")
        st.dataframe(classified, width="stretch", hide_index=True)

        st.divider()
        section_header("Tax Summary", icon="🧮")

        c1, c2 = st.columns(2)
        with c1:
            metric_card(
                "Total STCG",
                fmt_inr(summary.total_stcg),
                delta_value=summary.total_stcg,
            )
            metric_card(
                "Total LTCG",
                fmt_inr(summary.total_ltcg),
                delta_value=summary.total_ltcg,
            )
            metric_card("LTCG Taxable", fmt_inr(summary.ltcg_taxable))
        with c2:
            metric_card(
                "STCG Tax",
                fmt_inr(summary.stcg_tax),
                delta_value=-summary.stcg_tax if summary.stcg_tax else 0,
            )
            metric_card("LTCG Exempt", fmt_inr(summary.ltcg_exempt))
            metric_card(
                "LTCG Tax",
                fmt_inr(summary.ltcg_tax),
                delta_value=-summary.ltcg_tax if summary.ltcg_tax else 0,
            )

        st.divider()
        tc1, tc2 = st.columns([1, 1])
        with tc1:
            metric_card(
                "Total Tax Due",
                fmt_inr(summary.total_tax),
                delta_value=-summary.total_tax if summary.total_tax else 0,
                icon="🧾",
            )
        with tc2:
            if summary.total_stcg > 0 or summary.total_ltcg > 0:
                fig = themed_pie(
                    ["STCG", "LTCG"],
                    [abs(summary.total_stcg), abs(summary.total_ltcg)],
                    "STCG vs LTCG Split",
                )
                st.plotly_chart(fig, width="stretch")

with tab_harvest:
    section_header("Tax-Loss Harvesting Opportunities", icon="🌱")
    holdings_df = st.session_state.get("holdings_df")
    if holdings_df is None or holdings_df.empty:
        st.info("Load your portfolio from the Home page to see harvesting opportunities.")
    else:
        harvest = suggest_tax_harvesting(holdings_df)
        if harvest.empty:
            st.success("No significant unrealised losses to harvest.")
        else:
            total_loss = (
                harvest["unrealised_loss"].sum() if "unrealised_loss" in harvest.columns else 0
            )
            total_saving = (
                harvest["potential_tax_saving"].sum()
                if "potential_tax_saving" in harvest.columns
                else 0
            )

            s1, s2 = st.columns(2)
            with s1:
                metric_card(
                    "Total Harvestable Loss",
                    fmt_inr(abs(total_loss)),
                    delta_value=-1,
                )
            with s2:
                metric_card(
                    "Potential Tax Saving",
                    fmt_inr(total_saving),
                    delta_value=1,
                    icon="💰",
                )

            st.dataframe(harvest, width="stretch", hide_index=True)
