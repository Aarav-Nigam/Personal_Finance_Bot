from __future__ import annotations

import logging
from dataclasses import dataclass, field

from analytics.fundamentals import get_fundamentals
from analytics.technicals import add_all_indicators
from data.market_data import get_ohlcv

logger = logging.getLogger(__name__)


@dataclass
class SignalResult:
    score: int = 5
    label: str = "Hold"
    reasons: list[str] = field(default_factory=list)
    technical_score: int = 0
    fundamental_modifier: int = 0


def _score_to_label(score: int) -> str:
    if score >= 9:
        return "Strong Buy"
    if score >= 7:
        return "Buy"
    if score >= 4:
        return "Hold"
    if score >= 2:
        return "Sell"
    return "Strong Sell"


def compute_signal(symbol: str) -> SignalResult:
    df = get_ohlcv(symbol, period="1y")
    if df.empty or len(df) < 30:
        return SignalResult(reasons=["Insufficient data"])

    df = add_all_indicators(df)
    fund = get_fundamentals(symbol)

    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    reasons: list[str] = []

    if "rsi14" in df.columns and last["rsi14"] == last["rsi14"]:
        if last["rsi14"] < 40:
            score += 2
            reasons.append(f"RSI oversold ({last['rsi14']:.0f} < 40)")

    if "macd" in df.columns and "macd_signal" in df.columns:
        if (
            prev["macd"] == prev["macd"]
            and prev["macd_signal"] == prev["macd_signal"]
            and last["macd"] == last["macd"]
            and last["macd_signal"] == last["macd_signal"]
        ):
            if prev["macd"] < prev["macd_signal"] and last["macd"] > last["macd_signal"]:
                score += 2
                reasons.append("MACD bullish crossover")

    if "ema200" in df.columns and last["ema200"] == last["ema200"]:
        if last["close"] > last["ema200"]:
            score += 2
            reasons.append("Price above EMA200 (uptrend)")

    if "ema20" in df.columns and last["ema20"] == last["ema20"]:
        if last["close"] < last["ema20"]:
            score += 2
            reasons.append("Short-term dip below EMA20")

    if "bb_lower" in df.columns and last["bb_lower"] == last["bb_lower"]:
        if last["close"] <= last["bb_lower"]:
            score += 2
            reasons.append("Touching Bollinger lower band")

    technical_score = score

    fundamental_modifier = 0
    pe = fund.get("pe")
    roe = fund.get("roe")
    if pe and roe:
        if pe < 30 and roe > 0.15:
            fundamental_modifier = 2
            reasons.append("Healthy fundamentals (low P/E, good ROE)")
        elif pe > 50:
            fundamental_modifier = -2
            reasons.append("Expensive valuation (P/E > 50)")
    score += fundamental_modifier

    score = max(0, min(10, score))
    label = _score_to_label(score)
    return SignalResult(
        score=score,
        label=label,
        reasons=reasons,
        technical_score=technical_score,
        fundamental_modifier=fundamental_modifier,
    )


def compute_signals_batch(symbols: list[str]) -> list[SignalResult]:
    results = []
    for sym in symbols:
        try:
            results.append(compute_signal(sym))
        except Exception as e:
            logger.warning("Signal error for %s: %s", sym, e)
            results.append(SignalResult(reasons=[f"Error: {e}"]))
    return results
