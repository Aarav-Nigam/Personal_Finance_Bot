from __future__ import annotations

import hashlib

import pandas as pd
from kiteconnect import KiteConnect

from config.settings import settings
from data import cache

_kite: KiteConnect | None = None


class KiteAuthError(Exception):
    pass


def _get_kite() -> KiteConnect:
    global _kite
    if _kite is None:
        if not settings.KITE_ACCESS_TOKEN:
            raise KiteAuthError(
                "Kite access token not found. Run `python scripts/kite_auth.py` to authenticate."
            )
        kc = KiteConnect(api_key=settings.KITE_API_KEY)
        kc.set_access_token(settings.KITE_ACCESS_TOKEN)
        _kite = kc
    return _kite


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        if "TokenException" in type(e).__name__ or "token" in str(e).lower():
            global _kite
            _kite = None
            raise KiteAuthError(
                "Kite session expired. Run `python scripts/kite_auth.py` to refresh."
            ) from e
        raise


def get_holdings() -> pd.DataFrame:
    cached = cache.get("kite_holdings")
    if cached is not None:
        return pd.DataFrame(cached)
    kite = _get_kite()
    data = _safe_call(kite.holdings)
    df = pd.DataFrame(data)
    cache.set("kite_holdings", df.to_dict(orient="list"))
    return df


def get_positions() -> dict[str, pd.DataFrame]:
    cached_net = cache.get("kite_positions_net")
    cached_day = cache.get("kite_positions_day")
    if cached_net is not None and cached_day is not None:
        return {"net": pd.DataFrame(cached_net), "day": pd.DataFrame(cached_day)}
    kite = _get_kite()
    data = _safe_call(kite.positions)
    df_net = pd.DataFrame(data.get("net", []))
    df_day = pd.DataFrame(data.get("day", []))
    cache.set("kite_positions_net", df_net.to_dict(orient="list"))
    cache.set("kite_positions_day", df_day.to_dict(orient="list"))
    return {"net": df_net, "day": df_day}


def get_orders() -> pd.DataFrame:
    cached = cache.get("kite_orders")
    if cached is not None:
        return pd.DataFrame(cached)
    kite = _get_kite()
    data = _safe_call(kite.orders)
    df = pd.DataFrame(data)
    cache.set("kite_orders", df.to_dict(orient="list"))
    return df


def get_quote(symbols: list[str]) -> dict:
    key = "kite_quote_" + hashlib.md5("_".join(sorted(symbols)).encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached
    kite = _get_kite()
    data = _safe_call(kite.quote, symbols)
    cache.set(key, data, ttl=60)
    return data


def get_ltp(symbols: list[str]) -> dict:
    key = "kite_ltp_" + hashlib.md5("_".join(sorted(symbols)).encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached
    kite = _get_kite()
    data = _safe_call(kite.ltp, symbols)
    cache.set(key, data, ttl=60)
    return data


def get_margins() -> dict:
    cached = cache.get("kite_margins")
    if cached is not None:
        return cached
    kite = _get_kite()
    data = _safe_call(kite.margins)
    cache.set("kite_margins", data)
    return data


def get_profile() -> dict:
    cached = cache.get("kite_profile")
    if cached is not None:
        return cached
    kite = _get_kite()
    data = _safe_call(kite.profile)
    cache.set("kite_profile", data, ttl=3600)
    return data
