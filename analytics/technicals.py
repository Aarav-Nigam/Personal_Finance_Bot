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

    return df
