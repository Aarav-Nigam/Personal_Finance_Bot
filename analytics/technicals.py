from __future__ import annotations

import logging

import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "close" not in df.columns:
        return df

    ema200_span = 200
    if len(df) < 250:
        logger.warning("Fewer than 250 rows — using EMA50 as EMA200 fallback.")
        ema200_span = 50

    df["ema20"] = ta.ema(df["close"], length=20)
    df["ema50"] = ta.ema(df["close"], length=50)
    df["ema200"] = ta.ema(df["close"], length=ema200_span)

    df["rsi14"] = ta.rsi(df["close"], length=14)

    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        df["macd"] = macd_df["MACD_12_26_9"]
        df["macd_signal"] = macd_df["MACDs_12_26_9"]
        df["macd_hist"] = macd_df["MACDh_12_26_9"]

    bbands_df = ta.bbands(df["close"], length=20, std=2)
    if bbands_df is not None and not bbands_df.empty:
        cols = bbands_df.columns
        bbu = [c for c in cols if c.startswith("BBU_")]
        bbm = [c for c in cols if c.startswith("BBM_")]
        bbl = [c for c in cols if c.startswith("BBL_")]
        if bbu:
            df["bb_upper"] = bbands_df[bbu[0]]
        if bbm:
            df["bb_mid"] = bbands_df[bbm[0]]
        if bbl:
            df["bb_lower"] = bbands_df[bbl[0]]

    # ADX (trend strength + direction)
    if "high" in df.columns and "low" in df.columns:
        adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
        if adx_df is not None and not adx_df.empty:
            adx_cols = adx_df.columns
            adx_c = [c for c in adx_cols if c.startswith("ADX_")]
            dmp_c = [c for c in adx_cols if c.startswith("DMP_")]
            dmn_c = [c for c in adx_cols if c.startswith("DMN_")]
            if adx_c:
                df["adx"] = adx_df[adx_c[0]]
            if dmp_c:
                df["dmp"] = adx_df[dmp_c[0]]
            if dmn_c:
                df["dmn"] = adx_df[dmn_c[0]]

    # OBV (On-Balance Volume)
    if "volume" in df.columns:
        obv_series = ta.obv(df["close"], df["volume"])
        if obv_series is not None:
            df["obv"] = obv_series

    # MFI (Money Flow Index)
    if "high" in df.columns and "low" in df.columns and "volume" in df.columns:
        mfi_series = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=14)
        if mfi_series is not None:
            df["mfi"] = mfi_series

    # Stochastic Oscillator
    if "high" in df.columns and "low" in df.columns:
        stoch_df = ta.stoch(df["high"], df["low"], df["close"])
        if stoch_df is not None and not stoch_df.empty:
            stoch_cols = stoch_df.columns
            k_cols = [c for c in stoch_cols if c.startswith("STOCHk_")]
            d_cols = [c for c in stoch_cols if c.startswith("STOCHd_")]
            if k_cols:
                df["stoch_k"] = stoch_df[k_cols[0]]
            if d_cols:
                df["stoch_d"] = stoch_df[d_cols[0]]

    # ATR (Average True Range) — 14-period
    if "high" in df.columns and "low" in df.columns:
        atr_series = ta.atr(df["high"], df["low"], df["close"], length=14)
        if atr_series is not None:
            df["atr14"] = atr_series

    # Classic Pivot Points (from previous day's HLC)
    if all(c in df.columns for c in ["high", "low", "close"]) and len(df) >= 2:
        prev = df.iloc[-2]
        pivot = (prev["high"] + prev["low"] + prev["close"]) / 3
        df["pivot"] = pivot
        df["pivot_s1"] = 2 * pivot - prev["high"]
        df["pivot_s2"] = pivot - (prev["high"] - prev["low"])
        df["pivot_r1"] = 2 * pivot - prev["low"]
        df["pivot_r2"] = pivot + (prev["high"] - prev["low"])

    return df
