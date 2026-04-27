from __future__ import annotations

import pandas as pd

from utils.formatters import fmt_inr, fmt_pct

ADVISOR_SYSTEM_PROMPT = """\
You are a knowledgeable Indian personal finance advisor. You analyze stock portfolios, \
mutual funds, and tax implications for Indian investors. You provide actionable insights \
based on the user's actual portfolio data.

Key guidelines:
- All values are in INR
- Reference Indian tax rules (LTCG/STCG as per latest budget)
- Consider NSE/BSE listed securities
- Suggest diversification across asset classes
- Be specific with numbers from the portfolio data provided

Disclaimer: This is not SEBI-registered financial advice. Consult a certified financial \
planner before making investment decisions.\
"""


def build_portfolio_context(
    holdings_df: pd.DataFrame,
    xirr: float | None = None,
    allocation: dict | None = None,
) -> str:
    if holdings_df is None or holdings_df.empty:
        return "No portfolio data available."

    total_invested = (holdings_df["quantity"] * holdings_df["average_price"]).sum()
    total_current = (holdings_df["quantity"] * holdings_df["last_price"]).sum()
    total_pnl = total_current - total_invested
    pnl_pct = total_pnl / total_invested if total_invested > 0 else 0

    lines = [
        f"Portfolio: {len(holdings_df)} holdings",
        f"Total Invested: {fmt_inr(total_invested)}",
        f"Current Value: {fmt_inr(total_current)}",
        f"P&L: {fmt_inr(total_pnl)} ({fmt_pct(pnl_pct)})",
    ]

    if xirr is not None:
        lines.append(f"XIRR: {fmt_pct(xirr)}")

    top = holdings_df.copy()
    top["value"] = top["quantity"] * top["last_price"]
    top = top.nlargest(5, "value")
    lines.append("\nTop 5 holdings by value:")
    for _, row in top.iterrows():
        lines.append(f"  {row['tradingsymbol']}: {fmt_inr(row['value'])}")

    if allocation:
        inst = allocation.get("instrument_type", {})
        if inst:
            lines.append("\nAllocation:")
            for k, v in inst.items():
                lines.append(f"  {k}: {v * 100:.1f}%")

    return "\n".join(lines)


def build_market_context() -> str:
    try:
        from data.market_data import get_ohlcv

        df = get_ohlcv("^NSEI", period="5d")
        if not df.empty and len(df) >= 2:
            last = float(df.iloc[-1]["close"])
            prev = float(df.iloc[-2]["close"])
            change = (last - prev) / prev
            return f"Nifty 50: {last:,.0f} ({change * 100:+.2f}% today)"
    except Exception:
        pass
    return ""
