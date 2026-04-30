from __future__ import annotations

import logging
from dataclasses import dataclass, field

from analytics.fundamentals import get_fundamentals
from analytics.technicals import add_all_indicators
from data.market_data import get_analyst_recs, get_nifty_ohlcv, get_ohlcv

logger = logging.getLogger(__name__)

CATEGORY_WEIGHTS = {
    "momentum": 0.20,
    "trend": 0.20,
    "volume": 0.15,
    "fundamentals": 0.20,
    "sentiment": 0.15,
    "context": 0.10,
}


@dataclass
class SignalResult:
    score: float = 0.0
    label: str = "Hold"
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    sub_scores: dict = field(default_factory=dict)
    technical_score: int = 0
    fundamental_modifier: int = 0


def _score_to_label(score: float) -> str:
    if score >= 8:
        return "Strong Buy"
    if score >= 4:
        return "Buy"
    if score >= -3:
        return "Hold"
    if score >= -7:
        return "Sell"
    return "Strong Sell"


def _valid(val) -> bool:
    return val is not None and val == val


def _score_momentum(df) -> tuple[float, list[str], bool]:
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None
    score = 0.0
    reasons = []
    has_data = False

    # RSI (symmetric)
    if "rsi14" in df.columns and _valid(last.get("rsi14")):
        has_data = True
        rsi = last["rsi14"]
        if rsi < 30:
            score += 3
            reasons.append(f"RSI strongly oversold ({rsi:.0f})")
        elif rsi < 40:
            score += 1
            reasons.append(f"RSI oversold zone ({rsi:.0f})")
        elif rsi > 70:
            score -= 3
            reasons.append(f"RSI overbought ({rsi:.0f})")
        elif rsi > 60:
            score -= 1
            reasons.append(f"RSI approaching overbought ({rsi:.0f})")

    # MACD crossover
    if prev is not None and "macd" in df.columns and "macd_signal" in df.columns:
        if all(
            _valid(x)
            for x in [
                prev.get("macd"),
                prev.get("macd_signal"),
                last.get("macd"),
                last.get("macd_signal"),
            ]
        ):
            has_data = True
            if prev["macd"] < prev["macd_signal"] and last["macd"] > last["macd_signal"]:
                score += 2
                reasons.append("MACD bullish crossover")
            elif prev["macd"] > prev["macd_signal"] and last["macd"] < last["macd_signal"]:
                score -= 2
                reasons.append("MACD bearish crossover")

    # MACD histogram slope (3-bar trend)
    if "macd_hist" in df.columns and len(df) >= 4:
        hist_vals = df["macd_hist"].iloc[-4:].tolist()
        if all(_valid(v) for v in hist_vals):
            has_data = True
            if hist_vals[-1] > hist_vals[-2] > hist_vals[-3]:
                score += 1
                reasons.append("MACD histogram rising")
            elif hist_vals[-1] < hist_vals[-2] < hist_vals[-3]:
                score -= 1
                reasons.append("MACD histogram falling")

    # Stochastic
    if "stoch_k" in df.columns and "stoch_d" in df.columns and prev is not None:
        if all(
            _valid(x)
            for x in [
                last.get("stoch_k"),
                last.get("stoch_d"),
                prev.get("stoch_k"),
                prev.get("stoch_d"),
            ]
        ):
            has_data = True
            if (
                last["stoch_k"] < 20
                and prev["stoch_k"] < prev["stoch_d"]
                and last["stoch_k"] > last["stoch_d"]
            ):
                score += 2
                reasons.append("Stochastic oversold cross-up")
            elif (
                last["stoch_k"] > 80
                and prev["stoch_k"] > prev["stoch_d"]
                and last["stoch_k"] < last["stoch_d"]
            ):
                score -= 2
                reasons.append("Stochastic overbought cross-down")

    return (max(-10, min(10, score)), reasons, has_data)


def _score_trend(df) -> tuple[float, list[str], bool]:
    last = df.iloc[-1]
    score = 0.0
    reasons = []
    has_data = False

    # EMA alignment
    ema20 = last.get("ema20") if "ema20" in df.columns else None
    ema50 = last.get("ema50") if "ema50" in df.columns else None
    ema200 = last.get("ema200") if "ema200" in df.columns else None

    if all(_valid(x) for x in [ema20, ema50, ema200]):
        has_data = True
        if ema20 > ema50 > ema200:
            score += 3
            reasons.append("Strong uptrend (EMA20 > EMA50 > EMA200)")
        elif ema20 < ema50 < ema200:
            score -= 3
            reasons.append("Strong downtrend (EMA20 < EMA50 < EMA200)")
        elif ema20 > ema200:
            score += 1
        elif ema20 < ema200:
            score -= 1

    # Price vs EMA200
    if _valid(ema200) and _valid(last.get("close")):
        has_data = True
        if last["close"] > ema200:
            score += 1
        else:
            score -= 1

    # ADX with direction
    if "adx" in df.columns and "dmp" in df.columns and "dmn" in df.columns:
        adx = last.get("adx")
        dmp = last.get("dmp")
        dmn = last.get("dmn")
        if all(_valid(x) for x in [adx, dmp, dmn]):
            has_data = True
            if adx > 25:
                if dmp > dmn:
                    score += 2
                    reasons.append(f"Strong bullish trend (ADX {adx:.0f}, +DI > -DI)")
                else:
                    score -= 2
                    reasons.append(f"Strong bearish trend (ADX {adx:.0f}, -DI > +DI)")

    # Bollinger position
    if all(c in df.columns for c in ["bb_upper", "bb_lower", "bb_mid"]):
        bbu = last.get("bb_upper")
        bbl = last.get("bb_lower")
        bbm = last.get("bb_mid")
        close = last.get("close")
        if all(_valid(x) for x in [bbu, bbl, bbm, close]):
            has_data = True
            if close >= bbu:
                score -= 2
                reasons.append("Price at upper Bollinger Band (overextended)")
            elif close <= bbl:
                score += 2
                reasons.append("Price at lower Bollinger Band (potential bounce)")
            elif close < bbm:
                score += 1

    return (max(-10, min(10, score)), reasons, has_data)


def _score_volume(df) -> tuple[float, list[str], bool]:
    last = df.iloc[-1]
    score = 0.0
    reasons = []
    has_data = False

    if "volume" not in df.columns or not _valid(last.get("volume")):
        return (0, [], False)

    # Volume ratio vs 20-day average
    if len(df) >= 20:
        vol_20_avg = df["volume"].iloc[-20:].mean()
        if vol_20_avg > 0:
            has_data = True
            vol_ratio = last["volume"] / vol_20_avg
            close = last.get("close")
            prev_close = df.iloc[-2].get("close") if len(df) >= 2 else None
            if _valid(close) and _valid(prev_close):
                is_up_day = close > prev_close
                if vol_ratio > 1.5:
                    if is_up_day:
                        score += 3
                        reasons.append(f"High volume on up-day ({vol_ratio:.1f}x avg)")
                    else:
                        score -= 3
                        reasons.append(f"High volume on down-day ({vol_ratio:.1f}x avg)")
                elif vol_ratio < 0.5:
                    reasons.append("Very low volume — low conviction")

    # OBV trend (5-day slope)
    if "obv" in df.columns and len(df) >= 6:
        obv_recent = df["obv"].iloc[-5:]
        if obv_recent.notna().all():
            has_data = True
            obv_slope = obv_recent.iloc[-1] - obv_recent.iloc[0]
            if obv_slope > 0:
                score += 2
                reasons.append("OBV rising (accumulation)")
            elif obv_slope < 0:
                score -= 2
                reasons.append("OBV falling (distribution)")

    # MFI
    if "mfi" in df.columns and _valid(last.get("mfi")):
        has_data = True
        mfi = last["mfi"]
        if mfi < 20:
            score += 2
            reasons.append(f"MFI oversold ({mfi:.0f})")
        elif mfi > 80:
            score -= 2
            reasons.append(f"MFI overbought ({mfi:.0f})")

    return (max(-10, min(10, score)), reasons, has_data)


def _score_fundamentals(fund: dict) -> tuple[float, list[str], bool]:
    score = 0.0
    reasons = []
    valid_count = 0

    pe = fund.get("pe")
    if _valid(pe):
        valid_count += 1
        if pe < 15:
            score += 2
            reasons.append(f"Attractively valued (PE {pe:.1f})")
        elif pe < 25:
            score += 1
        elif pe > 60:
            score -= 2
            reasons.append(f"Very expensive (PE {pe:.0f})")
        elif pe > 40:
            score -= 1
            reasons.append(f"Expensive valuation (PE {pe:.0f})")

    # Forward PE improvement
    forward_pe = fund.get("forward_pe")
    if _valid(pe) and _valid(forward_pe) and pe > 0:
        valid_count += 1
        if forward_pe < pe * 0.85:
            score += 1
            reasons.append("Earnings growth expected (forward PE improving)")
        elif forward_pe > pe * 1.15:
            score -= 1

    # ROE
    roe = fund.get("roe")
    if _valid(roe):
        valid_count += 1
        if roe > 0.20:
            score += 2
            reasons.append(f"Excellent ROE ({roe * 100:.0f}%)")
        elif roe > 0.15:
            score += 1
        elif roe < 0.10:
            score -= 1

    # Debt/Equity
    de = fund.get("debt_equity")
    if _valid(de):
        valid_count += 1
        if de is not None and de < 50:
            score += 1
        elif de is not None and de > 150:
            score -= 1
            reasons.append(f"High debt (D/E {de:.0f}%)")

    # Revenue growth
    rev_growth = fund.get("revenue_growth_yoy")
    if _valid(rev_growth):
        valid_count += 1
        if rev_growth > 0.15:
            score += 1
            reasons.append(f"Strong revenue growth ({rev_growth * 100:.0f}% YoY)")
        elif rev_growth < 0:
            score -= 1
            reasons.append("Revenue declining")

    # Promoter holding
    promoter = fund.get("promoter_holding_pct")
    if _valid(promoter):
        valid_count += 1
        if promoter > 60:
            score += 1
        elif promoter < 30:
            score -= 1
            reasons.append(f"Low promoter holding ({promoter:.0f}%)")

    # PEG ratio (growth-adjusted valuation)
    peg = fund.get("peg_ratio")
    if _valid(peg):
        valid_count += 1
        if 0 < peg < 1:
            score += 2
            reasons.append(f"Undervalued on growth basis (PEG {peg:.2f})")
        elif peg < 1.5:
            score += 1
        elif peg > 3:
            score -= 1
            reasons.append(f"Expensive on growth basis (PEG {peg:.1f})")

    # Free cash flow yield
    fcf = fund.get("free_cashflow")
    if _valid(fcf):
        valid_count += 1
        mcap = fund.get("market_cap")
        if _valid(mcap) and mcap > 0:
            fcf_yield = fcf / mcap
            if fcf_yield > 0.05:
                score += 1
                reasons.append(f"Strong free cash flow yield ({fcf_yield * 100:.1f}%)")
            elif fcf < 0:
                score -= 1
                reasons.append("Negative free cash flow")

    # Profit margin quality
    margin = fund.get("profit_margins")
    if _valid(margin):
        valid_count += 1
        if margin > 0.20:
            score += 1
            reasons.append(f"High profit margins ({margin * 100:.0f}%)")
        elif margin < 0.05:
            score -= 1

    # Earnings growth
    eg = fund.get("earnings_growth")
    if _valid(eg):
        valid_count += 1
        if eg > 0.20:
            score += 1
            reasons.append(f"Strong earnings growth ({eg * 100:.0f}%)")
        elif eg < -0.10:
            score -= 1
            reasons.append(f"Earnings declining ({eg * 100:.0f}%)")

    has_data = valid_count >= 2
    return (max(-10, min(10, score)), reasons, has_data)


def _score_sentiment(symbol: str, fund: dict | None = None) -> tuple[float, list[str], bool]:
    score = 0.0
    reasons = []
    has_data = False

    # News sentiment via FinBERT
    try:
        from config.settings import settings

        if settings.FINBERT_ENABLED:
            from llm.sentiment import analyse_sentiment, get_news_headlines

            headlines = get_news_headlines(symbol)
            if headlines:
                sentiments = analyse_sentiment(headlines)
                if sentiments:
                    has_data = True
                    pos = sum(1 for s in sentiments if s["label"] == "positive")
                    neg = sum(1 for s in sentiments if s["label"] == "negative")
                    total = len(sentiments)
                    pos_ratio = pos / total
                    neg_ratio = neg / total
                    if pos_ratio > 0.8:
                        score += 4
                        reasons.append(f"Very positive news sentiment ({pos}/{total} positive)")
                    elif pos_ratio > 0.6:
                        score += 2
                        reasons.append(f"Positive news sentiment ({pos}/{total} positive)")
                    elif neg_ratio > 0.8:
                        score -= 4
                        reasons.append(f"Very negative news sentiment ({neg}/{total} negative)")
                    elif neg_ratio > 0.6:
                        score -= 2
                        reasons.append(f"Negative news sentiment ({neg}/{total} negative)")
    except Exception:
        pass

    # Analyst recommendations
    try:
        recs = get_analyst_recs(symbol)
        if not recs.empty and len(recs) >= 1:
            latest = recs.iloc[-1]
            grade = None
            for col in ["To Grade", "toGrade", "grade"]:
                if col in recs.columns:
                    grade = latest.get(col)
                    break
            if grade and isinstance(grade, str):
                has_data = True
                grade_lower = grade.lower().replace(" ", "").replace("-", "")
                if "strongbuy" in grade_lower or "outperform" in grade_lower:
                    score += 4
                    reasons.append(f"Analyst: {grade}")
                elif "buy" in grade_lower or "overweight" in grade_lower:
                    score += 2
                    reasons.append(f"Analyst: {grade}")
                elif "sell" in grade_lower or "underperform" in grade_lower:
                    score -= 2
                    reasons.append(f"Analyst: {grade}")
                elif "strongsell" in grade_lower or "underweight" in grade_lower:
                    score -= 4
                    reasons.append(f"Analyst: {grade}")
    except Exception:
        pass

    # Institutional ownership & short interest
    if fund:
        inst_pct = fund.get("held_percent_institutions")
        if _valid(inst_pct):
            has_data = True
            if inst_pct > 0.60:
                score += 1
                reasons.append(f"High institutional ownership ({inst_pct * 100:.0f}%)")
            elif inst_pct < 0.10:
                score -= 1

        short_pct = fund.get("short_percent_float")
        if _valid(short_pct):
            has_data = True
            if short_pct > 0.10:
                score -= 2
                reasons.append(f"High short interest ({short_pct * 100:.1f}% of float)")
            elif short_pct > 0.05:
                score -= 1
                reasons.append(f"Elevated short interest ({short_pct * 100:.1f}%)")

    return (max(-10, min(10, score)), reasons, has_data)


def _score_context(df, fund: dict) -> tuple[float, list[str], bool]:
    last = df.iloc[-1]
    score = 0.0
    reasons = []
    has_data = False

    # 52-week position
    high_52 = fund.get("fifty_two_week_high")
    low_52 = fund.get("fifty_two_week_low")
    close = last.get("close")
    if all(_valid(x) for x in [high_52, low_52, close]) and high_52 > low_52:
        has_data = True
        position = (close - low_52) / (high_52 - low_52)
        if position < 0.20:
            score += 3
            reasons.append(f"Near 52-week low ({position * 100:.0f}% of range)")
        elif position < 0.40:
            score += 1
        elif position > 0.80:
            score -= 3
            reasons.append(f"Near 52-week high ({position * 100:.0f}% of range)")
        elif position > 0.60:
            score -= 1

    # Mean reversion vs 200-SMA
    ema200 = last.get("ema200") if "ema200" in df.columns else None
    if _valid(ema200) and _valid(close) and ema200 > 0:
        has_data = True
        deviation = (close - ema200) / ema200
        if deviation > 0.15:
            score -= 2
            reasons.append(f"Extended above 200-EMA ({deviation * 100:.0f}%)")
        elif deviation < -0.15:
            score += 2
            reasons.append(f"Depressed below 200-EMA ({deviation * 100:.0f}%)")

    # Analyst price target upside/downside
    target = fund.get("analyst_target_mean")
    if _valid(target) and _valid(close) and close > 0:
        has_data = True
        upside = (target - close) / close
        if upside > 0.20:
            score += 3
            reasons.append(f"Analyst target {upside * 100:.0f}% above CMP (₹{target:,.0f})")
        elif upside > 0.10:
            score += 1
            reasons.append(f"Analyst target {upside * 100:.0f}% above CMP")
        elif upside < -0.20:
            score -= 3
            reasons.append(f"Analyst target {abs(upside) * 100:.0f}% below CMP (₹{target:,.0f})")
        elif upside < -0.10:
            score -= 1
            reasons.append(f"Analyst target {abs(upside) * 100:.0f}% below CMP")

    # Beta awareness
    beta = fund.get("beta")
    if _valid(beta) and beta > 1.5:
        has_data = True
        reasons.append(f"High beta ({beta:.2f}) — amplified market moves")

    # Nifty trend alignment
    try:
        nifty_df = get_nifty_ohlcv(period="3mo")
        if not nifty_df.empty and len(nifty_df) >= 20:
            has_data = True
            import pandas_ta as ta

            nifty_ema20 = ta.ema(nifty_df["close"], length=20)
            if nifty_ema20 is not None and len(nifty_ema20) > 0:
                nifty_last = nifty_df["close"].iloc[-1]
                nifty_ema = nifty_ema20.iloc[-1]
                if _valid(nifty_last) and _valid(nifty_ema):
                    nifty_bullish = nifty_last > nifty_ema
                    stock_bullish = _valid(last.get("ema20")) and close > last["ema20"]
                    if nifty_bullish and stock_bullish:
                        score += 1
                        reasons.append("Aligned with bullish market trend")
                    elif not nifty_bullish and not stock_bullish:
                        score -= 1
                        reasons.append("Aligned with bearish market trend")
    except Exception:
        pass

    return (max(-10, min(10, score)), reasons, has_data)


def compute_signal(symbol: str) -> SignalResult:
    df = get_ohlcv(symbol, period="1y")
    if df.empty or len(df) < 30:
        return SignalResult(reasons=["Insufficient data"])

    df = add_all_indicators(df)
    fund = get_fundamentals(symbol)

    sub_scores = {}
    all_reasons = []
    valid_categories = 0
    weighted_sum = 0.0

    scorers = [
        ("momentum", lambda: _score_momentum(df)),
        ("trend", lambda: _score_trend(df)),
        ("volume", lambda: _score_volume(df)),
        ("fundamentals", lambda: _score_fundamentals(fund)),
        ("sentiment", lambda: _score_sentiment(symbol, fund)),
        ("context", lambda: _score_context(df, fund)),
    ]

    for category, scorer in scorers:
        try:
            cat_score, cat_reasons, has_data = scorer()
        except Exception as e:
            logger.warning("Signal scoring error (%s) for %s: %s", category, symbol, e)
            cat_score, cat_reasons, has_data = 0, [], False

        sub_scores[category] = cat_score
        all_reasons.extend(cat_reasons)
        if has_data:
            valid_categories += 1
            weighted_sum += cat_score * CATEGORY_WEIGHTS[category]

    # Normalize: the weighted sum uses weights that sum to 1.0,
    # but each sub-score is on -10/+10. So weighted_sum is already on -10/+10 scale.
    final_score = max(-10.0, min(10.0, weighted_sum / sum(CATEGORY_WEIGHTS.values())))
    confidence = valid_categories / len(CATEGORY_WEIGHTS)

    label = _score_to_label(final_score)

    # Backward compat: approximate the old fields
    tech_score = int(sub_scores.get("momentum", 0) + sub_scores.get("trend", 0))
    fund_mod = int(sub_scores.get("fundamentals", 0))

    # Auto-store for backtesting
    try:
        current_price = float(df.iloc[-1]["close"]) if not df.empty else None
        if current_price:
            from analytics.backtest import store_signal

            store_signal(symbol, final_score, label, round(confidence, 2), current_price)
    except Exception:
        pass

    return SignalResult(
        score=round(final_score, 1),
        label=label,
        confidence=round(confidence, 2),
        reasons=all_reasons,
        sub_scores=sub_scores,
        technical_score=tech_score,
        fundamental_modifier=fund_mod,
    )


def compute_signal_with_cost_basis(
    symbol: str, buy_price: float, current_price: float
) -> SignalResult:
    result = compute_signal(symbol)

    if buy_price <= 0:
        return result

    unrealized_pct = (current_price - buy_price) / buy_price
    cost_adj = 0.0
    cost_reasons = []

    if unrealized_pct > 0.50:
        cost_adj = -2
        cost_reasons.append(
            f"Up {unrealized_pct * 100:.0f}% from cost — consider profit booking or trailing SL"
        )
    elif unrealized_pct > 0.30:
        cost_adj = -1
        cost_reasons.append(f"Up {unrealized_pct * 100:.0f}% — partial profit booking opportunity")
    elif unrealized_pct < -0.40:
        cost_adj = -1
        cost_reasons.append(
            f"Down {abs(unrealized_pct) * 100:.0f}% — review fundamentals, consider cutting"
        )
    elif unrealized_pct < -0.20:
        cost_adj = 0.5
        cost_reasons.append(f"Down {abs(unrealized_pct) * 100:.0f}% — mean reversion potential")

    adjusted_score = max(-10.0, min(10.0, result.score + cost_adj))
    new_label = _score_to_label(adjusted_score)

    return SignalResult(
        score=round(adjusted_score, 1),
        label=new_label,
        confidence=result.confidence,
        reasons=result.reasons + cost_reasons,
        sub_scores=result.sub_scores,
        technical_score=result.technical_score,
        fundamental_modifier=result.fundamental_modifier,
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
