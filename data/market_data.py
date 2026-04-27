from __future__ import annotations

import pandas as pd
import yfinance as yf

from data import cache


def _ensure_ns(symbol: str) -> str:
    s = symbol.upper().strip()
    if not s.endswith(".NS") and not s.startswith("^"):
        return s + ".NS"
    return s


def get_ohlcv(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    sym = _ensure_ns(symbol)
    key = f"yfinance_{sym}_{period}_{interval}"
    cached = cache.get(key)
    if cached is not None:
        return pd.DataFrame(cached)
    df = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    cache_df = df.copy()
    for col in cache_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        cache_df[col] = cache_df[col].astype(str)
    cache.set(key, cache_df.to_dict(orient="list"), ttl=300)
    return df


def get_fundamentals(symbol: str) -> dict:
    sym = _ensure_ns(symbol)
    key = f"yfinance_fundamentals_{sym}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        info = yf.Ticker(sym).info
    except Exception:
        return {}
    result = {
        "pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "debt_equity": info.get("debtToEquity"),
        "eps_ttm": info.get("trailingEps"),
        "revenue_growth_yoy": info.get("revenueGrowth"),
        "market_cap": info.get("marketCap"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "dividend_yield": info.get("dividendYield"),
    }
    cache.set(key, result, ttl=3600)
    return result


def get_analyst_recs(symbol: str) -> pd.DataFrame:
    sym = _ensure_ns(symbol)
    key = f"yfinance_recs_{sym}"
    cached = cache.get(key)
    if cached is not None:
        return pd.DataFrame(cached)
    try:
        recs = yf.Ticker(sym).recommendations
        if recs is None or recs.empty:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()
    recs = recs.reset_index()
    cache.set(key, recs.to_dict(orient="list"), ttl=86400)
    return recs


def get_nifty_ohlcv(period: str = "1y") -> pd.DataFrame:
    return get_ohlcv("^NSEI", period=period)
