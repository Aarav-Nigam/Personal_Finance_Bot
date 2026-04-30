from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta

import pandas as pd

from config.settings import settings

DB_PATH = os.path.join(settings.CACHE_DIR, "signals.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            score REAL NOT NULL,
            label TEXT NOT NULL,
            confidence REAL,
            price_at_signal REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, symbol)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_date ON signals(date)")
    conn.commit()
    return conn


def store_signal(symbol: str, score: float, label: str, confidence: float, price: float) -> None:
    """Store one signal record. Uses INSERT OR REPLACE for re-runs on same day."""
    conn = _get_conn()
    today = date.today().isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO signals (date, symbol, score, label, confidence, price_at_signal) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (today, symbol.upper(), round(score, 1), label, round(confidence, 2), round(price, 2)),
    )
    conn.commit()
    conn.close()


def get_signal_history(symbol: str | None = None, days: int = 90) -> pd.DataFrame:
    """Retrieve stored signals, optionally filtered by symbol."""
    conn = _get_conn()
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    if symbol:
        df = pd.read_sql_query(
            "SELECT date, symbol, score, label, confidence, price_at_signal "
            "FROM signals WHERE symbol = ? AND date >= ? ORDER BY date DESC",
            conn,
            params=(symbol.upper(), cutoff),
        )
    else:
        df = pd.read_sql_query(
            "SELECT date, symbol, score, label, confidence, price_at_signal "
            "FROM signals WHERE date >= ? ORDER BY date DESC",
            conn,
            params=(cutoff,),
        )
    conn.close()
    return df


def compute_accuracy(days_forward: int = 30) -> pd.DataFrame:
    """For each label, compute avg return N days later and win rate."""
    from data.market_data import get_ohlcv

    conn = _get_conn()
    cutoff = (date.today() - timedelta(days=days_forward + 7)).isoformat()
    signals_df = pd.read_sql_query(
        "SELECT date, symbol, score, label, price_at_signal "
        "FROM signals WHERE date <= ? ORDER BY date",
        conn,
        params=(cutoff,),
    )
    conn.close()

    if signals_df.empty:
        return pd.DataFrame()

    results = []
    for _, row in signals_df.iterrows():
        signal_date = pd.to_datetime(row["date"]).date()
        target_date = signal_date + timedelta(days=days_forward)
        price_at_signal = row["price_at_signal"]

        if not price_at_signal or price_at_signal <= 0:
            continue

        df = get_ohlcv(row["symbol"], period="6mo")
        if df.empty:
            continue

        df["date_col"] = pd.to_datetime(df["date"]).dt.date
        future_rows = df[df["date_col"] >= target_date]
        if future_rows.empty:
            continue

        future_price = float(future_rows.iloc[0]["close"])
        ret = (future_price - price_at_signal) / price_at_signal

        is_buy = row["score"] > 0
        is_win = (ret > 0 and is_buy) or (ret < 0 and not is_buy)

        results.append(
            {
                "label": row["label"],
                "return_pct": ret * 100,
                "win": is_win,
            }
        )

    if not results:
        return pd.DataFrame()

    results_df = pd.DataFrame(results)
    accuracy = (
        results_df.groupby("label")
        .agg(
            count=("return_pct", "count"),
            avg_return_pct=("return_pct", "mean"),
            win_rate=("win", "mean"),
        )
        .round(2)
        .reset_index()
    )
    return accuracy


def get_total_signals_count() -> int:
    """Quick count of total stored signals."""
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    conn.close()
    return count
