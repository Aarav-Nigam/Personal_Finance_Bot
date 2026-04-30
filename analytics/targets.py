from __future__ import annotations

from analytics.fundamentals import get_fundamentals
from analytics.technicals import add_all_indicators
from data.market_data import get_ohlcv

RISK_PER_TRADE_PCT = 0.02


def _valid(val) -> bool:
    return val is not None and val == val


def compute_actionable_targets(
    symbol: str,
    portfolio_value: float | None = None,
) -> dict:
    """Compute stop-loss, price targets, S/R levels, and position sizing."""
    df = get_ohlcv(symbol, period="1y")
    if df.empty or len(df) < 30:
        return {}

    df = add_all_indicators(df)
    last = df.iloc[-1]
    fund = get_fundamentals(symbol)

    close = last.get("close")
    if not _valid(close) or close <= 0:
        return {}

    result: dict = {"current_price": round(float(close), 2)}

    # ATR-based stop-loss (2x ATR)
    atr = last.get("atr14") if "atr14" in df.columns else None
    if _valid(atr) and atr > 0:
        result["atr"] = round(float(atr), 2)
        result["stop_loss_long"] = round(float(close - 2 * atr), 2)
        result["stop_loss_short"] = round(float(close + 2 * atr), 2)

    # Analyst price targets
    target_mean = fund.get("analyst_target_mean")
    target_high = fund.get("analyst_target_high")
    target_low = fund.get("analyst_target_low")
    if _valid(target_mean):
        result["target_price"] = round(float(target_mean), 2)
        result["upside_pct"] = round((target_mean - close) / close * 100, 1)
    if _valid(target_high):
        result["target_high"] = round(float(target_high), 2)
    if _valid(target_low):
        result["target_low"] = round(float(target_low), 2)

    # Pivot-based support / resistance
    pivot_keys = [
        ("pivot_s1", "support_1"),
        ("pivot_s2", "support_2"),
        ("pivot_r1", "resistance_1"),
        ("pivot_r2", "resistance_2"),
        ("pivot", "pivot"),
    ]
    for col_key, out_key in pivot_keys:
        val = last.get(col_key) if col_key in df.columns else None
        if _valid(val):
            result[out_key] = round(float(val), 2)

    # Position sizing (fixed-risk model: risk 2% of portfolio per trade)
    stop_loss = result.get("stop_loss_long")
    if portfolio_value and stop_loss and close > stop_loss:
        risk_per_share = close - stop_loss
        max_risk = RISK_PER_TRADE_PCT * portfolio_value
        shares = int(max_risk / risk_per_share)
        if shares >= 1:
            result["position_size_shares"] = shares
            result["position_size_value"] = round(shares * close, 0)
            result["position_size_pct"] = round(shares * close / portfolio_value * 100, 1)

    # Risk/Reward ratio
    if _valid(target_mean) and stop_loss and close > stop_loss:
        reward = target_mean - close
        risk = close - stop_loss
        if risk > 0 and reward > 0:
            result["risk_reward_ratio"] = round(reward / risk, 2)

    return result
