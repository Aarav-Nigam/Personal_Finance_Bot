from __future__ import annotations

import pandas as pd


def compute_ideal_allocation(
    holdings_df: pd.DataFrame,
    strategy: str = "equal_weight",
    signals: dict[str, float] | None = None,
) -> dict[str, float]:
    """Return target weight per symbol."""
    symbols = holdings_df["tradingsymbol"].tolist()
    n = len(symbols)
    if n == 0:
        return {}

    if strategy == "signal_weighted" and signals:
        shifted = {s: max(signals.get(s, 0) + 11, 1) for s in symbols}
        total = sum(shifted.values())
        return {s: v / total for s, v in shifted.items()}

    return {s: 1.0 / n for s in symbols}


def compute_drift(
    holdings_df: pd.DataFrame,
    target_allocation: dict[str, float],
) -> list[dict]:
    """Per-stock drift from target allocation."""
    total_value = (holdings_df["last_price"] * holdings_df["quantity"]).sum()
    if total_value <= 0:
        return []

    results = []
    for _, row in holdings_df.iterrows():
        sym = row["tradingsymbol"]
        current_weight = (row["last_price"] * row["quantity"]) / total_value
        target_weight = target_allocation.get(sym, 0)
        drift = current_weight - target_weight

        if drift > 0.03:
            status = "Overweight"
        elif drift < -0.03:
            status = "Underweight"
        else:
            status = "On Target"

        results.append(
            {
                "symbol": sym,
                "current_weight": round(current_weight * 100, 1),
                "target_weight": round(target_weight * 100, 1),
                "drift_pct": round(drift * 100, 1),
                "status": status,
            }
        )
    return results


def suggest_rebalance(
    holdings_df: pd.DataFrame,
    signals: dict[str, float] | None = None,
    strategy: str = "equal_weight",
) -> list[dict]:
    """Generate specific rebalance actions with share counts."""
    target = compute_ideal_allocation(holdings_df, strategy=strategy, signals=signals)
    drift_list = compute_drift(holdings_df, target)

    total_value = (holdings_df["last_price"] * holdings_df["quantity"]).sum()
    if total_value <= 0:
        return []

    prices = dict(zip(holdings_df["tradingsymbol"], holdings_df["last_price"]))
    signal_labels = {}
    if signals:
        for sym, score in signals.items():
            if score >= 4:
                signal_labels[sym] = "Buy"
            elif score <= -4:
                signal_labels[sym] = "Sell"
            else:
                signal_labels[sym] = "Hold"

    suggestions = []
    for item in drift_list:
        sym = item["symbol"]
        drift = item["drift_pct"]
        status = item["status"]
        price = prices.get(sym, 0)
        signal_label = signal_labels.get(sym, "Hold")

        if price <= 0:
            continue

        if status == "On Target":
            action = "Hold"
            shares = 0
            reason = "Allocation on target"
        elif status == "Overweight":
            if signal_label == "Buy":
                action = "Hold"
                shares = 0
                reason = f"Overweight +{drift:.1f}% but signal is bullish"
            else:
                value_to_trim = (item["drift_pct"] / 100) * total_value
                shares = max(1, int(value_to_trim / price))
                action = "Trim"
                reason = f"Overweight +{drift:.1f}%"
                if signal_label == "Sell":
                    reason += " & signal is bearish"
        else:
            if signal_label == "Sell":
                action = "Hold"
                shares = 0
                reason = f"Underweight {drift:.1f}% but signal is bearish"
            else:
                value_to_add = (abs(item["drift_pct"]) / 100) * total_value
                shares = max(1, int(value_to_add / price))
                action = "Add"
                reason = f"Underweight {drift:.1f}%"
                if signal_label == "Buy":
                    reason += " & signal is bullish"

        suggestions.append(
            {
                "symbol": sym,
                "action": action,
                "shares": shares,
                "value": round(shares * price, 0) if shares > 0 else 0,
                "reason": reason,
                "current_weight": item["current_weight"],
                "target_weight": item["target_weight"],
                "signal": signal_label,
            }
        )

    return sorted(suggestions, key=lambda x: abs(x.get("value", 0)), reverse=True)
