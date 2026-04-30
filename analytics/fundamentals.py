from __future__ import annotations

from data.market_data import get_fundamentals as _yf_fundamentals
from data.nse_client import get_quote as _nse_quote


def get_fundamentals(symbol: str) -> dict:
    yf_data = _yf_fundamentals(symbol)

    promoter_holding_pct = None
    try:
        nse_data = _nse_quote(symbol)
        if nse_data:
            promoter_holding_pct = nse_data.get("promoter_holding_pct")
    except Exception:
        pass

    roce = None
    return {
        "pe": yf_data.get("pe"),
        "forward_pe": yf_data.get("forward_pe"),
        "ev_ebitda": yf_data.get("ev_ebitda"),
        "pb": yf_data.get("pb"),
        "roe": yf_data.get("roe"),
        "roce": roce,
        "debt_equity": yf_data.get("debt_equity"),
        "promoter_holding_pct": promoter_holding_pct,
        "eps_ttm": yf_data.get("eps_ttm"),
        "revenue_growth_yoy": yf_data.get("revenue_growth_yoy"),
        "sector": yf_data.get("sector"),
        "industry": yf_data.get("industry"),
        "market_cap": yf_data.get("market_cap"),
        "fifty_two_week_high": yf_data.get("fifty_two_week_high"),
        "fifty_two_week_low": yf_data.get("fifty_two_week_low"),
        "dividend_yield": yf_data.get("dividend_yield"),
        "analyst_target_mean": yf_data.get("analyst_target_mean"),
        "analyst_target_high": yf_data.get("analyst_target_high"),
        "analyst_target_low": yf_data.get("analyst_target_low"),
        "recommendation_key": yf_data.get("recommendation_key"),
        "num_analyst_opinions": yf_data.get("num_analyst_opinions"),
        "beta": yf_data.get("beta"),
        "profit_margins": yf_data.get("profit_margins"),
        "operating_margins": yf_data.get("operating_margins"),
        "free_cashflow": yf_data.get("free_cashflow"),
        "operating_cashflow": yf_data.get("operating_cashflow"),
        "peg_ratio": yf_data.get("peg_ratio"),
        "short_ratio": yf_data.get("short_ratio"),
        "short_percent_float": yf_data.get("short_percent_float"),
        "current_ratio": yf_data.get("current_ratio"),
        "earnings_growth": yf_data.get("earnings_growth"),
        "earnings_quarterly_growth": yf_data.get("earnings_quarterly_growth"),
        "held_percent_insiders": yf_data.get("held_percent_insiders"),
        "held_percent_institutions": yf_data.get("held_percent_institutions"),
    }
