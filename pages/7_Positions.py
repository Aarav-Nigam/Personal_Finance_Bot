from __future__ import annotations

import streamlit as st

from ui.styles import inject_css, metric_card, section_header, status_badge

inject_css()

section_header("Positions & Orders", icon="📊")

if not st.session_state.get("kite_connected"):
    st.info("Connect Kite to view positions and orders. Run `python scripts/kite_auth.py`.")
    st.stop()

from analytics.account import get_positions_summary, load_orders, load_positions  # noqa: E402
from data.kite_client import KiteAuthError  # noqa: E402
from utils.formatters import fmt_inr  # noqa: E402

tab_pos, tab_orders = st.tabs(["Active Positions", "Order Book"])

# ---------------------------------------------------------------------------
# Positions tab
# ---------------------------------------------------------------------------
with tab_pos:
    try:
        positions = load_positions()
        df_net = positions["net"]

        if df_net.empty:
            st.info("No positions found for today.")
        else:
            summary = get_positions_summary(df_net)

            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card(
                    "Unrealised P&L",
                    fmt_inr(summary["total_unrealised"]),
                    delta_value=summary["total_unrealised"],
                )
            with c2:
                metric_card(
                    "Realised P&L",
                    fmt_inr(summary["total_realised"]),
                    delta_value=summary["total_realised"],
                )
            with c3:
                metric_card(
                    "M2M",
                    fmt_inr(summary["total_m2m"]),
                    delta_value=summary["total_m2m"],
                )

            st.divider()

            show_all = st.toggle("Show closed positions", value=False)
            display = df_net if show_all else df_net[df_net["quantity"] != 0]

            if display.empty:
                st.info("No open positions. Toggle above to see closed positions.")
            else:
                cols_to_show = [
                    c
                    for c in [
                        "tradingsymbol",
                        "exchange",
                        "product",
                        "quantity",
                        "average_price",
                        "last_price",
                        "unrealised",
                        "realised",
                        "m2m",
                        "day_buy_quantity",
                        "day_sell_quantity",
                    ]
                    if c in display.columns
                ]
                col_config = {
                    "tradingsymbol": st.column_config.TextColumn("Symbol"),
                    "exchange": st.column_config.TextColumn("Exchange"),
                    "product": st.column_config.TextColumn("Product"),
                    "quantity": st.column_config.NumberColumn("Qty", format="%d"),
                    "average_price": st.column_config.NumberColumn("Avg Price", format="%.2f"),
                    "last_price": st.column_config.NumberColumn("LTP", format="%.2f"),
                    "unrealised": st.column_config.NumberColumn("Unrealised", format="%.2f"),
                    "realised": st.column_config.NumberColumn("Realised", format="%.2f"),
                    "m2m": st.column_config.NumberColumn("M2M", format="%.2f"),
                    "day_buy_quantity": st.column_config.NumberColumn("Day Buy Qty", format="%d"),
                    "day_sell_quantity": st.column_config.NumberColumn("Day Sell Qty", format="%d"),
                }
                st.dataframe(
                    display[cols_to_show],
                    column_config=col_config,
                    width="stretch",
                    hide_index=True,
                )
    except KiteAuthError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Failed to load positions: {e}")

# ---------------------------------------------------------------------------
# Orders tab
# ---------------------------------------------------------------------------
with tab_orders:
    try:
        orders_df = load_orders()

        if orders_df.empty:
            st.info("No orders found for today.")
        else:
            if "status" in orders_df.columns:
                status_counts = orders_df["status"].value_counts()
                badge_cols = st.columns(min(len(status_counts), 5))
                for i, (status_val, count) in enumerate(status_counts.items()):
                    badge_cols[i % len(badge_cols)].markdown(
                        f"{status_badge(status_val)} **{count}**",
                        unsafe_allow_html=True,
                    )
                st.divider()

                filter_status = st.selectbox(
                    "Filter by status",
                    ["All"] + sorted(orders_df["status"].unique().tolist()),
                )
                if filter_status != "All":
                    orders_df = orders_df[orders_df["status"] == filter_status]

            cols_to_show = [
                c
                for c in [
                    "order_id",
                    "tradingsymbol",
                    "transaction_type",
                    "quantity",
                    "average_price",
                    "status",
                    "order_timestamp",
                    "status_message",
                ]
                if c in orders_df.columns
            ]
            col_config = {
                "order_id": st.column_config.TextColumn("Order ID"),
                "tradingsymbol": st.column_config.TextColumn("Symbol"),
                "transaction_type": st.column_config.TextColumn("Type"),
                "quantity": st.column_config.NumberColumn("Qty", format="%d"),
                "average_price": st.column_config.NumberColumn("Avg Price", format="%.2f"),
                "status": st.column_config.TextColumn("Status"),
                "order_timestamp": st.column_config.TextColumn("Timestamp"),
                "status_message": st.column_config.TextColumn("Message"),
            }
            st.dataframe(
                orders_df[cols_to_show],
                column_config=col_config,
                width="stretch",
                hide_index=True,
            )
    except KiteAuthError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Failed to load orders: {e}")
