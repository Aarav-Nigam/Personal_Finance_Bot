from __future__ import annotations

import streamlit as st

from ui.charts import correlation_heatmap
from ui.glossary import tip
from ui.styles import inject_css, metric_card, section_header

inject_css()

section_header("Risk Analysis", icon="🛡️")

holdings_df = st.session_state.get("holdings_df")

if holdings_df is None or holdings_df.empty:
    st.info(
        "No holdings loaded. Connect Kite or upload a CSV from the Home page to see risk metrics."
    )
    st.stop()

from analytics.risk import (  # noqa: E402
    concentration_risk,
    correlation_matrix,
    max_drawdown,
    nifty_sharpe,
    portfolio_beta,
    portfolio_volatility,
    sharpe_ratio,
    var_95,
)

# ---------------------------------------------------------------------------
# Compute risk metrics
# ---------------------------------------------------------------------------
with st.spinner("Computing risk metrics..."):
    from analytics.risk import compute_portfolio_returns

    returns_df, weights = compute_portfolio_returns(holdings_df)
    beta = portfolio_beta(holdings_df)
    vol = portfolio_volatility(returns_df, weights) if not returns_df.empty else None
    sharpe = sharpe_ratio(returns_df, weights) if not returns_df.empty else None
    mdd = max_drawdown(returns_df, weights) if not returns_df.empty else None
    var = var_95(returns_df, weights) if not returns_df.empty else None
    concentration = concentration_risk(holdings_df)

# ---------------------------------------------------------------------------
# Metric cards
# ---------------------------------------------------------------------------
section_header("Key Risk Metrics", icon="📊")

c1, c2, c3, c4 = st.columns(4)
with c1:
    beta_str = f"{beta:.2f}" if beta is not None else "N/A"
    metric_card(tip("Portfolio Beta", "Beta"), beta_str, icon="📈")
with c2:
    sharpe_str = f"{sharpe:.2f}" if sharpe is not None else "N/A"
    metric_card(
        tip("Sharpe Ratio", "Sharpe"),
        sharpe_str,
        delta_value=sharpe if sharpe else 0,
        icon="⚡",
    )
with c3:
    mdd_str = f"{mdd['drawdown_pct']:.1f}%" if mdd else "N/A"
    metric_card(tip("Max Drawdown"), mdd_str, icon="📉")
with c4:
    vol_str = f"{vol * 100:.1f}%" if vol else "N/A"
    metric_card("Volatility (Ann.)", vol_str, icon="🌊")

st.divider()

# ---------------------------------------------------------------------------
# VaR & Nifty comparison
# ---------------------------------------------------------------------------
v1, v2, v3 = st.columns(3)
with v1:
    var_str = f"{var:.2f}%" if var is not None else "N/A"
    metric_card(tip("VaR 95%", "Daily VaR 95%"), var_str, icon="⚠️")
with v2:
    nifty_s = nifty_sharpe()
    nifty_str = f"{nifty_s:.2f}" if nifty_s is not None else "N/A"
    metric_card("Nifty Sharpe", nifty_str, icon="🏛️")
with v3:
    if sharpe is not None and nifty_s is not None:
        diff = sharpe - nifty_s
        metric_card(
            "Sharpe vs Nifty",
            f"{diff:+.2f}",
            delta="Outperforming" if diff > 0 else "Underperforming",
            delta_value=diff,
            icon="🎯",
        )
    else:
        metric_card("Sharpe vs Nifty", "N/A", icon="🎯")

st.divider()

# ---------------------------------------------------------------------------
# Concentration alerts
# ---------------------------------------------------------------------------
section_header("Concentration Risk", icon="⚖️")

c1, c2 = st.columns(2)
with c1:
    metric_card(
        tip("HHI", "Concentration (HHI)"),
        f"{concentration['hhi']:.0f}",
        icon="📊",
    )
with c2:
    metric_card("Top 3 Weight", f"{concentration['top3_weight']:.1f}%", icon="🏆")

alerts = concentration["stock_alerts"] + concentration["sector_alerts"]
if alerts:
    for alert in alerts:
        st.warning(alert)
else:
    st.success("No concentration alerts — portfolio is well-diversified.")

st.divider()

# ---------------------------------------------------------------------------
# Correlation heatmap
# ---------------------------------------------------------------------------
if not returns_df.empty and len(returns_df.columns) >= 2:
    section_header("Correlation Matrix", icon="🔗")
    corr = correlation_matrix(returns_df)
    if not corr.empty:
        fig = correlation_heatmap(corr)
        st.plotly_chart(fig, width="stretch")

        high_corr_pairs = []
        for i in range(len(corr)):
            for j in range(i + 1, len(corr)):
                val = corr.iloc[i, j]
                if val > 0.75:
                    high_corr_pairs.append(f"{corr.index[i]} ↔ {corr.columns[j]}: {val:.2f}")
        if high_corr_pairs:
            st.caption("⚠️ Highly correlated pairs (>0.75):")
            for pair in high_corr_pairs[:5]:
                st.caption(f"  • {pair}")
