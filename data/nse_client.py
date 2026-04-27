from __future__ import annotations

from data import cache


def get_quote(symbol: str) -> dict:
    key = f"nse_quote_{symbol.upper()}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        from nsepython import nse_quote

        raw = nse_quote(symbol.upper())
        info = raw.get("priceInfo", {})
        result = {
            "last_price": info.get("lastPrice"),
            "open": info.get("open"),
            "high": info.get("intraDayHighLow", {}).get("max"),
            "low": info.get("intraDayHighLow", {}).get("min"),
            "close": info.get("previousClose"),
            "change": info.get("change"),
            "pct_change": info.get("pChange"),
            "upper_circuit": info.get("upperCP"),
            "lower_circuit": info.get("lowerCP"),
        }
    except Exception:
        from data.market_data import get_ohlcv

        df = get_ohlcv(symbol, period="5d")
        if df.empty:
            return {}
        last = df.iloc[-1]
        result = {"last_price": float(last.get("close", 0))}
    cache.set(key, result, ttl=60)
    return result


def get_option_chain(symbol: str) -> dict:
    key = f"nse_oc_{symbol.upper()}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        from nsepython import option_chain

        data = option_chain(symbol.upper())
        cache.set(key, data, ttl=60)
        return data
    except Exception:
        return {}
