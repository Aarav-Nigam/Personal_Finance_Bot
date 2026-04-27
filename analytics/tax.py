from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

TAX_RATES = {
    "2024-25": {"ltcg_rate": 0.125, "stcg_rate": 0.20, "ltcg_exempt": 125000},
    "2023-24": {"ltcg_rate": 0.10, "stcg_rate": 0.15, "ltcg_exempt": 100000},
}


@dataclass
class TaxLot:
    symbol: str
    buy_date: date
    sell_date: date
    qty: int
    buy_price: float
    sell_price: float


@dataclass
class TaxSummary:
    total_stcg: float
    total_ltcg: float
    ltcg_exempt: float
    ltcg_taxable: float
    stcg_tax: float
    ltcg_tax: float
    total_tax: float
    fy: str


def classify_lots(lots: list[TaxLot], fy: str) -> pd.DataFrame:
    rows = []
    for lot in lots:
        holding_days = (lot.sell_date - lot.buy_date).days
        gain_loss = (lot.sell_price - lot.buy_price) * lot.qty
        lot_type = "LTCG" if holding_days > 365 else "STCG"
        rows.append(
            {
                "symbol": lot.symbol,
                "buy_date": lot.buy_date,
                "sell_date": lot.sell_date,
                "qty": lot.qty,
                "buy_price": lot.buy_price,
                "sell_price": lot.sell_price,
                "holding_days": holding_days,
                "gain_loss": gain_loss,
                "type": lot_type,
            }
        )
    return pd.DataFrame(rows)


def compute_tax(classified_df: pd.DataFrame, fy: str) -> TaxSummary:
    rates = TAX_RATES.get(fy, TAX_RATES["2024-25"])

    stcg_df = classified_df[classified_df["type"] == "STCG"]
    ltcg_df = classified_df[classified_df["type"] == "LTCG"]

    total_stcg = stcg_df["gain_loss"].sum() if not stcg_df.empty else 0.0
    total_ltcg = ltcg_df["gain_loss"].sum() if not ltcg_df.empty else 0.0

    ltcg_exempt = rates["ltcg_exempt"]
    ltcg_taxable = max(0, total_ltcg - ltcg_exempt)

    stcg_tax = max(0, total_stcg) * rates["stcg_rate"]
    ltcg_tax = ltcg_taxable * rates["ltcg_rate"]

    return TaxSummary(
        total_stcg=total_stcg,
        total_ltcg=total_ltcg,
        ltcg_exempt=ltcg_exempt,
        ltcg_taxable=ltcg_taxable,
        stcg_tax=stcg_tax,
        ltcg_tax=ltcg_tax,
        total_tax=stcg_tax + ltcg_tax,
        fy=fy,
    )


def suggest_tax_harvesting(holdings_df: pd.DataFrame) -> pd.DataFrame:
    if holdings_df.empty:
        return pd.DataFrame()
    df = holdings_df.copy()
    if "pnl" not in df.columns:
        df["pnl"] = (df["last_price"] - df["average_price"]) * df["quantity"]
    losses = df[df["pnl"] < -500].copy()
    if losses.empty:
        return pd.DataFrame()
    losses["unrealised_loss"] = losses["pnl"].abs()
    rates = TAX_RATES["2024-25"]
    losses["potential_tax_saving"] = losses["unrealised_loss"] * rates["stcg_rate"]
    return (
        losses[["tradingsymbol", "unrealised_loss", "potential_tax_saving"]]
        .sort_values("unrealised_loss", ascending=False)
        .reset_index(drop=True)
    )
