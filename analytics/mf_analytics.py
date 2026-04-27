from __future__ import annotations

from datetime import date

import pandas as pd

from data.mf_client import get_fund_nav
from utils.calculations import xirr


def compute_sip_xirr(payments: list[tuple[date, float]], current_value: float) -> float | None:
    if not payments or current_value <= 0:
        return None
    dates = [p[0] for p in payments]
    amounts = [-abs(p[1]) for p in payments]
    dates.append(date.today())
    amounts.append(current_value)
    return xirr(dates, amounts)


def _compute_return(nav_df: pd.DataFrame, years: int) -> float | None:
    if nav_df.empty or len(nav_df) < 2:
        return None
    latest = nav_df.iloc[-1]
    target_date = date(latest["date"].year - years, latest["date"].month, latest["date"].day)
    past = nav_df[nav_df["date"] <= target_date]
    if past.empty:
        return None
    start_nav = float(past.iloc[-1]["nav"])
    end_nav = float(latest["nav"])
    if start_nav <= 0:
        return None
    return (end_nav / start_nav) ** (1.0 / years) - 1


def get_category_returns(category: str, top_n: int = 10) -> pd.DataFrame:
    from data.mf_client import list_all_funds

    all_funds = list_all_funds()
    matched = [f for f in all_funds if category.lower() in f.get("schemeName", "").lower()][:50]

    rows = []
    for fund in matched[:top_n]:
        code = fund["schemeCode"]
        nav_df = get_fund_nav(code)
        if nav_df.empty:
            continue
        rows.append(
            {
                "scheme_name": fund["schemeName"],
                "scheme_code": code,
                "1y_return": _compute_return(nav_df, 1),
                "3y_return": _compute_return(nav_df, 3),
                "5y_return": _compute_return(nav_df, 5),
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values("3y_return", ascending=False, na_position="last")
    return df.head(top_n).reset_index(drop=True)


def compare_funds(scheme_codes: list[int]) -> pd.DataFrame:
    frames = {}
    for code in scheme_codes:
        nav_df = get_fund_nav(code)
        if nav_df.empty:
            continue
        nav_df = nav_df.set_index("date")
        base = float(nav_df.iloc[0]["nav"])
        if base > 0:
            frames[str(code)] = (nav_df["nav"] / base) * 100

    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames)
