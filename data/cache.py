from __future__ import annotations

import hashlib
import json
import os
import time

from config.settings import settings


def _cache_dir() -> str:
    os.makedirs(settings.CACHE_DIR, exist_ok=True)
    return settings.CACHE_DIR


def _key_path(key: str) -> str:
    h = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(_cache_dir(), f"{h}.json")


def get(key: str):
    path = _key_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            entry = json.load(f)
    except (json.JSONDecodeError, OSError):
        invalidate(key)
        return None
    if time.time() > entry.get("expires_at", 0):
        invalidate(key)
        return None
    return entry["data"]


def set(key: str, value, ttl: int = settings.CACHE_TTL_SECONDS):
    path = _key_path(key)
    entry = {"data": value, "expires_at": time.time() + ttl}
    with open(path, "w") as f:
        json.dump(entry, f)


def invalidate(key: str):
    path = _key_path(key)
    if os.path.exists(path):
        os.remove(path)


def clear():
    d = _cache_dir()
    for fname in os.listdir(d):
        if fname.endswith(".json"):
            os.remove(os.path.join(d, fname))
