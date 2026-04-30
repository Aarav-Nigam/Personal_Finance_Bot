from __future__ import annotations

import yfinance as yf

from config.settings import settings
from data import cache

_finbert = None


def get_sentiment_pipeline():
    global _finbert
    if _finbert is None:
        import sys
        import types
        import warnings

        warnings.filterwarnings("ignore", message=".*torchvision.*")

        if "torchvision" not in sys.modules:
            sys.modules["torchvision"] = types.ModuleType("torchvision")
            sys.modules["torchvision.transforms"] = types.ModuleType("torchvision.transforms")

        import os

        from transformers import pipeline

        local_model = os.path.expanduser("~/.cache/huggingface/finbert")
        model_path = local_model if os.path.isdir(local_model) else "ProsusAI/finbert"
        _finbert = pipeline("text-classification", model=model_path)
    return _finbert


def get_news_headlines(symbol: str) -> list[str]:
    suffix = symbol.upper().strip()
    if not suffix.endswith(".NS"):
        suffix += ".NS"

    cache_key = f"news_headlines_{suffix}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        news = yf.Ticker(suffix).news
        if not news:
            return []
        titles = []
        for item in news[:10]:
            title = item.get("title") or (item.get("content") or {}).get("title")
            if title:
                titles.append(title)
        cache.set(cache_key, titles, ttl=1800)
        return titles
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
