from __future__ import annotations


def _indian_grouping(n: str) -> str:
    if len(n) <= 3:
        return n
    last3 = n[-3:]
    rest = n[:-3]
    groups = []
    while rest:
        groups.append(rest[-2:])
        rest = rest[:-2]
    groups.reverse()
    return ",".join(groups) + "," + last3


def fmt_inr(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    abs_val = abs(amount)
    integer_part = int(abs_val)
    decimal_part = f"{abs_val - integer_part:.2f}"[1:]  # ".xx"
    formatted = _indian_grouping(str(integer_part))
    return f"{sign}₹{formatted}{decimal_part}"


def fmt_pct(value: float) -> str:
    pct = value * 100
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.2f}%"


def fmt_cr(amount: float) -> str:
    abs_val = abs(amount)
    sign = "-" if amount < 0 else ""
    if abs_val >= 1_00_00_000:
        return f"{sign}₹{abs_val / 1_00_00_000:.2f} Cr"
    return f"{sign}₹{abs_val / 1_00_000:.2f} L"
