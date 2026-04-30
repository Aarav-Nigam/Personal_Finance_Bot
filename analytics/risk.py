from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from analytics.fundamentals import get_fundamentals
from analytics.portfolio import get_sector_allocation
from data.market_data import get_nifty_ohlcv, get_ohlcv

logger = logging.getLogger(__name__)

RISK_FREE_RATE = 0.065
TRADING_DAYS = 252


def _valid(val) -> bool:
    return val is not None and val == val


def compute_portfolio_returns(
    holdings_df: pd.DataFrame, period: str = "1y"
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Fetch daily returns for each holding, weighted by allocation.
    Returns (returns_df with columns per stock, weights dict).
    """
    total_value = (holdings_df["last_price"] * holdings_df["quantity"]).sum()
    if total_value <= 0:
        return pd.DataFrame(), {}

    returns_dict: dict[str, pd.Series] = {}
    weights: dict[str, float] = {}

    for _, row in holdings_df.iterrows():
        sym = row["tradingsymbol"]
        value = row["last_price"] * row["quantity"]
        weight = value / total_value

        df = get_ohlcv(sym, period=period)
        if df.empty or len(df) < 30:
            continue

        daily_returns = df["close"].pct_change().dropna()
        returns_dict[sym] = daily_returns.reset_index(drop=True)
        weights[sym] = weight

    if not returns_dict:
        return pd.DataFrame(), {}

    returns_df = pd.DataFrame(returns_dict)
    return returns_df, weights


def portfolio_beta(holdings_df: pd.DataFrame) -> float | None:
    """Weighted average beta from fundamentals."""
    total_value = (holdings_df["last_price"] * holdings_df["quantity"]).sum()
    if total_value <= 0:
        return None

    weighted_beta = 0.0
    valid_weight = 0.0

    for _, row in holdings_df.iterrows():
        fund = get_fundamentals(row["tradingsymbol"])
        beta = fund.get("beta")
        if _valid(beta):
            weight = (row["last_price"] * row["quantity"]) / total_value
            weighted_beta += beta * weight
            valid_weight += weight

    if valid_weight < 0.5:
        return None
    return round(weighted_beta / valid_weight, 2)


def portfolio_volatility(returns_df: pd.DataFrame, weights: dict[str, float]) -> float | None:
    """Annualized portfolio volatility."""
    if returns_df.empty:
        return None

    available = [s for s in weights if s in returns_df.columns]
    if not available:
        return None

    w = np.array([weights[s] for s in available])
    w = w / w.sum()

    ret_matrix = returns_df[available].dropna()
    if len(ret_matrix) < 30:
        return None

    portfolio_daily = ret_matrix.values @ w
    vol = float(np.std(portfolio_daily) * np.sqrt(TRADING_DAYS))
    return round(vol, 4)


def sharpe_ratio(
    returns_df: pd.DataFrame, weights: dict[str, float], risk_free_rate: float = RISK_FREE_RATE
) -> float | None:
    """(Annualized return - rf) / annualized volatility."""
    if returns_df.empty:
        return None

    available = [s for s in weights if s in returns_df.columns]
    if not available:
        return None

    w = np.array([weights[s] for s in available])
    w = w / w.sum()

    ret_matrix = returns_df[available].dropna()
    if len(ret_matrix) < 30:
        return None

    portfolio_daily = ret_matrix.values @ w
    ann_return = float(np.mean(portfolio_daily) * TRADING_DAYS)
    ann_vol = float(np.std(portfolio_daily) * np.sqrt(TRADING_DAYS))

    if ann_vol == 0:
        return None
    return round((ann_return - risk_free_rate) / ann_vol, 2)


def max_drawdown(returns_df: pd.DataFrame, weights: dict[str, float]) -> dict | None:
    """Maximum peak-to-trough drawdown."""
    if returns_df.empty:
        return None

    available = [s for s in weights if s in returns_df.columns]
    if not available:
        return None

    w = np.array([weights[s] for s in available])
    w = w / w.sum()

    ret_matrix = returns_df[available].dropna()
    if len(ret_matrix) < 30:
        return None

    portfolio_daily = ret_matrix.values @ w
    cumulative = (1 + portfolio_daily).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = cumulative / running_max - 1
    max_dd = float(np.min(drawdowns))
    max_dd_idx = int(np.argmin(drawdowns))

    return {
        "drawdown_pct": round(max_dd * 100, 2),
        "worst_day_index": max_dd_idx,
    }


def var_95(returns_df: pd.DataFrame, weights: dict[str, float]) -> float | None:
    """Historical VaR at 95% confidence (5th percentile daily loss)."""
    if returns_df.empty:
        return None

    available = [s for s in weights if s in returns_df.columns]
    if not available:
        return None

    w = np.array([weights[s] for s in available])
    w = w / w.sum()

    ret_matrix = returns_df[available].dropna()
    if len(ret_matrix) < 30:
        return None

    portfolio_daily = ret_matrix.values @ w
    var = float(np.percentile(portfolio_daily, 5))
    return round(var * 100, 2)


def concentration_risk(holdings_df: pd.DataFrame) -> dict:
    """HHI, top-3 weight, single-stock and sector alerts."""
    total_value = (holdings_df["last_price"] * holdings_df["quantity"]).sum()
    if total_value <= 0:
        return {"hhi": 0, "top3_weight": 0, "stock_alerts": [], "sector_alerts": []}

    weights = []
    stock_alerts = []

    for _, row in holdings_df.iterrows():
        w = (row["last_price"] * row["quantity"]) / total_value
        weights.append(w)
        if w > 0.25:
            stock_alerts.append(
                f"{row['tradingsymbol']} is {w * 100:.0f}% of portfolio (>25% threshold)"
            )

    weights_sorted = sorted(weights, reverse=True)
    hhi = sum(w**2 for w in weights) * 10000
    top3_weight = sum(weights_sorted[:3]) if len(weights_sorted) >= 3 else sum(weights_sorted)

    # Sector concentration
    sector_alerts = []
    try:
        sector_alloc = get_sector_allocation(holdings_df)
        for sector, pct in sector_alloc.items():
            if pct > 0.40:
                sector_alerts.append(f"{sector} is {pct * 100:.0f}% of portfolio (>40% threshold)")
    except Exception:
        pass

    return {
        "hhi": round(hhi, 0),
        "top3_weight": round(top3_weight * 100, 1),
        "stock_alerts": stock_alerts,
        "sector_alerts": sector_alerts,
    }


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Pairwise correlation of daily returns."""
    if returns_df.empty or len(returns_df.columns) < 2:
        return pd.DataFrame()
    return returns_df.corr().round(2)


def nifty_sharpe(period: str = "1y") -> float | None:
    """Sharpe ratio of Nifty 50 for comparison."""
    df = get_nifty_ohlcv(period=period)
    if df.empty or len(df) < 30:
        return None
    daily_returns = df["close"].pct_change().dropna()
    ann_return = float(daily_returns.mean() * TRADING_DAYS)
    ann_vol = float(daily_returns.std() * np.sqrt(TRADING_DAYS))
    if ann_vol == 0:
        return None
    return round((ann_return - RISK_FREE_RATE) / ann_vol, 2)
