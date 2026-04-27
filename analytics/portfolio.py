from __future__ import annotations

from datetime import date

import pandas as pd

from data.kite_client import get_holdings as _kite_holdings
from data.kite_client import get_orders as _kite_orders
from utils.calculations import xirr


def load_holdings() -> pd.DataFrame:
    return _kite_holdings()


def load_orders() -> pd.DataFrame:
    return _kite_orders()


def compute_pnl(holdings_df: pd.DataFrame) -> pd.DataFrame:
    df = holdings_df.copy()
    df["invested_value"] = df["quantity"] * df["average_price"]
    df["current_value"] = df["quantity"] * df["last_price"]
    df["pnl"] = df["current_value"] - df["invested_value"]
    df["pnl_pct"] = df["pnl"] / df["invested_value"].replace(0, float("nan"))
    return df


def compute_xirr(orders_df: pd.DataFrame, current_portfolio_value: float) -> float | None:
    if orders_df.empty or current_portfolio_value <= 0:
        return None
    dates = pd.to_datetime(orders_df["order_timestamp"]).dt.date.tolist()
    amounts = []
    for _, row in orders_df.iterrows():
        if row.get("transaction_type") == "BUY":
            amounts.append(-abs(row["average_price"] * row["filled_quantity"]))
        else:
            amounts.append(abs(row["average_price"] * row["filled_quantity"]))
    dates.append(date.today())
    amounts.append(current_portfolio_value)
    return xirr(dates, amounts)


def get_allocation(holdings_df: pd.DataFrame) -> dict:
    if holdings_df.empty:
        return {"instrument_type": {}}
    if "instrument_type" in holdings_df.columns:
        df = holdings_df.copy()
        df["value"] = df["quantity"] * df["last_price"]
        total = df["value"].sum()
        if total == 0:
            return {"instrument_type": {}}
        breakdown = df.groupby("instrument_type")["value"].sum() / total
        return {"instrument_type": breakdown.to_dict()}
    return {"instrument_type": {}}


def get_portfolio_summary(holdings_df: pd.DataFrame) -> dict:
    df = compute_pnl(holdings_df)
    total_invested = df["invested_value"].sum()
    total_current = df["current_value"].sum()
    total_pnl = df["pnl"].sum()
    total_pnl_pct = total_pnl / total_invested if total_invested > 0 else 0.0
    sorted_by_pnl = df.sort_values("pnl_pct", ascending=False)
    return {
        "total_invested": total_invested,
        "total_current_value": total_current,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "num_holdings": len(df),
        "top_gainers": sorted_by_pnl.head(5),
        "top_losers": sorted_by_pnl.tail(5).iloc[::-1],
    }


def compare_to_nifty(portfolio_xirr: float | None, start_date: date) -> dict | None:
    from data.market_data import get_nifty_ohlcv
    from utils.calculations import cagr

    if portfolio_xirr is None:
        return None

    days = (date.today() - start_date).days
    if days < 30:
        return None

    if days > 365 * 3:
        period = "5y"
    elif days > 365:
        period = "2y"
    else:
        period = "1y"

    nifty_df = get_nifty_ohlcv(period=period)
    if nifty_df.empty or len(nifty_df) < 2:
        return None

    nifty_df["date_parsed"] = pd.to_datetime(nifty_df["date"])
    after_start = nifty_df[nifty_df["date_parsed"] >= pd.Timestamp(start_date)]
    if after_start.empty:
        after_start = nifty_df

    start_val = float(after_start.iloc[0]["close"])
    end_val = float(nifty_df.iloc[-1]["close"])
    years = days / 365.25
    nifty_cagr = cagr(start_val, end_val, years)

    return {
        "nifty_cagr": nifty_cagr,
        "portfolio_xirr": portfolio_xirr,
        "alpha": portfolio_xirr - nifty_cagr,
        "period_days": days,
    }


def get_sector_allocation(holdings_df: pd.DataFrame) -> dict:
    from analytics.fundamentals import get_fundamentals

    if holdings_df.empty:
        return {}

    sectors: dict[str, float] = {}
    total_value = 0.0

    for _, row in holdings_df.iterrows():
        sym = str(row.get("tradingsymbol", ""))
        qty = float(row.get("quantity", 0))
        price = float(row.get("last_price", 0))
        value = qty * price
        total_value += value

        try:
            fundies = get_fundamentals(sym)
            sector = fundies.get("sector") or "Unknown"
        except Exception:
            sector = "Unknown"

        sectors[sector] = sectors.get(sector, 0.0) + value

    if total_value <= 0:
        return {}
    return {k: v / total_value for k, v in sectors.items()}


def get_market_status() -> dict:
    from datetime import datetime, timedelta, timezone

    from data.market_data import get_nifty_ohlcv

    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    weekday = now.weekday()
    hour_min = now.hour * 60 + now.minute

    if weekday < 5 and 555 <= hour_min <= 930:
        status = "Open"
    elif weekday < 5 and 540 <= hour_min < 555:
        status = "Pre-Open"
    else:
        status = "Closed"

    nifty_df = get_nifty_ohlcv(period="5d")
    nifty_level = None
    nifty_change_pct = None
    if not nifty_df.empty and len(nifty_df) >= 2:
        nifty_level = float(nifty_df.iloc[-1]["close"])
        prev_close = float(nifty_df.iloc[-2]["close"])
        if prev_close > 0:
            nifty_change_pct = (nifty_level - prev_close) / prev_close

    return {
        "status": status,
        "nifty_level": nifty_level,
        "nifty_change_pct": nifty_change_pct,
    }
