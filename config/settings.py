from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    KITE_API_KEY: str = os.getenv("KITE_API_KEY", "")
    KITE_API_SECRET: str = os.getenv("KITE_API_SECRET", "")
    KITE_ACCESS_TOKEN: str | None = os.getenv("KITE_ACCESS_TOKEN") or None
    KITE_REDIRECT_URL: str = os.getenv("KITE_REDIRECT_URL", "http://127.0.0.1:8080")

    GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY") or None
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY") or None
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")

    FINBERT_ENABLED: bool = os.getenv("FINBERT_ENABLED", "true").lower() == "true"

    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    CACHE_DIR: str = os.getenv("CACHE_DIR", ".cache")


settings = Settings()
