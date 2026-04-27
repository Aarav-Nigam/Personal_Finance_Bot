from __future__ import annotations

import pandas as pd

from data.kite_client import (
    get_margins as _kite_margins,
)
from data.kite_client import (
    get_orders as _kite_orders,
)
from data.kite_client import (
    get_positions as _kite_positions,
)
from data.kite_client import (
    get_profile as _kite_profile,
)


def load_profile() -> dict:
    return _kite_profile()


def load_margins() -> dict:
    return _kite_margins()


def get_margin_summary() -> dict:
    raw = load_margins()
    equity = raw.get("equity", {})
    avail = equity.get("available", {})
    utilised = equity.get("utilised", {})

    cash = avail.get("cash", 0) or 0
    collateral = avail.get("collateral", 0) or 0
    intraday_payin = avail.get("intraday_payin", 0) or 0
    opening_balance = avail.get("opening_balance", 0) or 0
    live_balance = avail.get("live_balance", 0) or 0

    total_available = cash + collateral + intraday_payin

    total_used = sum(v for v in utilised.values() if isinstance(v, (int, float))) if utilised else 0

    utilization_pct = (
        (total_used / (total_used + total_available)) if (total_used + total_available) > 0 else 0
    )

    return {
        "total_available": total_available,
        "total_used": total_used,
        "utilization_pct": utilization_pct,
        "cash": cash,
        "collateral": collateral,
        "intraday_payin": intraday_payin,
        "opening_balance": opening_balance,
        "live_balance": live_balance,
    }


def load_positions() -> dict[str, pd.DataFrame]:
    return _kite_positions()


def get_positions_summary(positions_net_df: pd.DataFrame) -> dict:
    if positions_net_df.empty:
        return {
            "total_unrealised": 0,
            "total_realised": 0,
            "total_m2m": 0,
            "count_open": 0,
            "count_closed": 0,
        }
    unrealised = (
        positions_net_df["unrealised"].sum() if "unrealised" in positions_net_df.columns else 0
    )
    realised = positions_net_df["realised"].sum() if "realised" in positions_net_df.columns else 0
    m2m = positions_net_df["m2m"].sum() if "m2m" in positions_net_df.columns else 0
    open_count = (
        int((positions_net_df["quantity"] != 0).sum())
        if "quantity" in positions_net_df.columns
        else 0
    )
    closed_count = len(positions_net_df) - open_count

    return {
        "total_unrealised": float(unrealised),
        "total_realised": float(realised),
        "total_m2m": float(m2m),
        "count_open": open_count,
        "count_closed": closed_count,
    }


def load_orders() -> pd.DataFrame:
    return _kite_orders()
