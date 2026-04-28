from __future__ import annotations

import streamlit as st

from ui.charts import margin_gauge
from ui.styles import inject_css, metric_card, section_header, tag_pills

inject_css()

section_header("Account & Funds", icon="👤")

if not st.session_state.get("kite_connected"):
    st.info("Connect Kite to view account details. Run `python scripts/kite_auth.py`.")
    st.stop()

from analytics.account import get_margin_summary, load_margins, load_profile  # noqa: E402
from data.kite_client import KiteAuthError  # noqa: E402
from utils.formatters import fmt_inr  # noqa: E402

# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
try:
    profile = load_profile()
    section_header("Profile", icon="👤")

    p1, p2, p3 = st.columns(3)
    with p1:
        metric_card("Name", profile.get("user_name", "N/A"))
    with p2:
        metric_card("Email", profile.get("email", "N/A"))
    with p3:
        metric_card("Broker", profile.get("broker", "Zerodha"))

    exchanges = profile.get("exchanges", [])
    products = profile.get("products", [])
    if exchanges:
        st.markdown("**Exchanges:** " + tag_pills(exchanges), unsafe_allow_html=True)
    if products:
        st.markdown("**Products:** " + tag_pills(products), unsafe_allow_html=True)

    st.divider()
except KiteAuthError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.warning(f"Could not load profile: {e}")

# ---------------------------------------------------------------------------
# Funds summary
# ---------------------------------------------------------------------------
try:
    margins_summary = get_margin_summary()

    section_header("Funds Overview", icon="💰")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        metric_card("Available Cash", fmt_inr(margins_summary["cash"]), icon="💸")
    with f2:
        metric_card("Collateral", fmt_inr(margins_summary["collateral"]))
    with f3:
        metric_card("Intraday Payin", fmt_inr(margins_summary["intraday_payin"]))
    with f4:
        metric_card("Opening Balance", fmt_inr(margins_summary["opening_balance"]))

    st.divider()

    # ---------------------------------------------------------------------------
    # Margin gauge
    # ---------------------------------------------------------------------------
    section_header("Margin Utilization", icon="⏱️")
    g_col, d_col = st.columns([1, 1])

    with g_col:
        fig = margin_gauge(margins_summary["total_used"], margins_summary["total_available"])
        st.plotly_chart(fig, width="stretch")

    with d_col:
        metric_card(
            "Total Available",
            fmt_inr(margins_summary["total_available"]),
            delta_value=1,
        )
        metric_card(
            "Total Used",
            fmt_inr(margins_summary["total_used"]),
            delta_value=-1 if margins_summary["total_used"] > 0 else 0,
        )
        metric_card("Live Balance", fmt_inr(margins_summary["live_balance"]))

    st.divider()

    # ---------------------------------------------------------------------------
    # Detailed breakdown
    # ---------------------------------------------------------------------------
    with st.expander("Detailed Margin Breakdown"):
        raw = load_margins()
        equity = raw.get("equity", {})

        avail = equity.get("available", {})
        utilised = equity.get("utilised", {})

        a_col, u_col = st.columns(2)
        with a_col:
            st.markdown("**Available**")
            for k, v in avail.items():
                if isinstance(v, (int, float)):
                    st.markdown(f"- **{k}**: {fmt_inr(v)}")
        with u_col:
            st.markdown("**Utilised**")
            for k, v in utilised.items():
                if isinstance(v, (int, float)):
                    st.markdown(f"- **{k}**: {fmt_inr(v)}")

except KiteAuthError as e:
    st.error(str(e))
except Exception as e:
    st.error(f"Failed to load margin data: {e}")

# ---------------------------------------------------------------------------
# Connection info
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Kite access token expires daily at 6:00 AM IST. Refresh via `python scripts/kite_auth.py`."
)
