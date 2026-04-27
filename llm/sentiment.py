from __future__ import annotations

import yfinance as yf

from config.settings import settings

_finbert = None


def get_sentiment_pipeline():
    global _finbert
    if _finbert is None:
        from transformers import pipeline

        import os

        local_model = os.path.expanduser("~/.cache/huggingface/finbert")
        model_path = local_model if os.path.isdir(local_model) else "ProsusAI/finbert"
        _finbert = pipeline("text-classification", model=model_path)
    return _finbert


def get_news_headlines(symbol: str) -> list[str]:
    suffix = symbol.upper().strip()
    if not suffix.endswith(".NS"):
        suffix += ".NS"
    try:
        news = yf.Ticker(suffix).news
        if not news:
            return []
        return [item.get("title", "") for item in news[:10] if item.get("title")]
    except Exception:
        return []


def analyse_sentiment(headlines: list[str]) -> list[dict]:
    if not settings.FINBERT_ENABLED or not headlines:
        return []
    pipe = get_sentiment_pipeline()
    results = pipe(headlines, truncation=True, max_length=512)
    return [
        {"headline": h, "label": r["label"], "score": r["score"]}
        for h, r in zip(headlines, results)
    ]
