from __future__ import annotations

from datetime import date

from pyxirr import xirr as _pyxirr_xirr


def xirr(dates: list[date], amounts: list[float]) -> float | None:
    result = _pyxirr_xirr(dates, amounts)
    if result is None or result != result:  # NaN check
        return None
    return float(result)


def cagr(start_value: float, end_value: float, years: float) -> float:
    if years <= 0 or start_value <= 0:
        return 0.0
    return (end_value / start_value) ** (1 / years) - 1


def annualised_return(total_return_pct: float, days: int) -> float:
    if days <= 0:
        return 0.0
    return (1 + total_return_pct) ** (365 / days) - 1
