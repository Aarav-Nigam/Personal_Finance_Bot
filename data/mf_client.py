from __future__ import annotations

from datetime import datetime

import pandas as pd
import urllib3
import requests

from data import cache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.mfapi.in"
_SESSION = requests.Session()
_SESSION.verify = False


def search_fund(query: str) -> list[dict]:
    key = f"mf_search_{query.lower()}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        resp = _SESSION.get(f"{BASE_URL}/mf/search", params={"q": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    cache.set(key, data, ttl=3600)
    return data


def get_fund_nav(scheme_code: int) -> pd.DataFrame:
    key = f"mf_nav_{scheme_code}"
    cached = cache.get(key)
    if cached is not None:
        return pd.DataFrame(cached)
    try:
        resp = _SESSION.get(f"{BASE_URL}/mf/{scheme_code}", timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return pd.DataFrame()

    nav_data = raw.get("data", [])
    if not nav_data:
        return pd.DataFrame()

    rows = []
    for entry in nav_data:
        try:
            d = datetime.strptime(entry["date"], "%d-%m-%Y").date()
            rows.append({"date": d, "nav": float(entry["nav"])})
        except (ValueError, KeyError):
            continue

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    cache_df = df.copy()
    cache_df["date"] = cache_df["date"].astype(str)
    cache.set(key, cache_df.to_dict(orient="list"), ttl=300)
    return df


def list_all_funds() -> list[dict]:
    cached = cache.get("mf_all_funds")
    if cached is not None:
        return cached
    try:
        resp = _SESSION.get(f"{BASE_URL}/mf", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    cache.set("mf_all_funds", data, ttl=86400)
    return data


def get_fund_details(scheme_code: int) -> dict:
    key = f"mf_details_{scheme_code}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        resp = _SESSION.get(f"{BASE_URL}/mf/{scheme_code}", timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return {}
    meta = raw.get("meta", {})
    cache.set(key, meta, ttl=86400)
    return meta
