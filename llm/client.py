from __future__ import annotations

from collections.abc import Generator

from litellm import completion

from config.settings import settings

SUPPORTED_PROVIDERS = {"gemini", "groq", "ollama"}


def chat(messages: list[dict], provider: str | None = None, model: str | None = None) -> str:
    _provider = provider or settings.LLM_PROVIDER
    _model = model or settings.LLM_MODEL

    kwargs: dict = {"model": _model, "messages": messages}

    if _provider == "gemini":
        kwargs["api_key"] = settings.GOOGLE_API_KEY
    elif _provider == "groq":
        kwargs["api_key"] = settings.GROQ_API_KEY
    elif _provider == "ollama":
        kwargs["api_base"] = settings.OLLAMA_BASE_URL

    response = completion(**kwargs)
    return response.choices[0].message.content


def chat_stream(
    messages: list[dict], provider: str | None = None, model: str | None = None
) -> Generator[str, None, None]:
    _provider = provider or settings.LLM_PROVIDER
    _model = model or settings.LLM_MODEL

    kwargs: dict = {"model": _model, "messages": messages, "stream": True}

    if _provider == "gemini":
        kwargs["api_key"] = settings.GOOGLE_API_KEY
    elif _provider == "groq":
        kwargs["api_key"] = settings.GROQ_API_KEY
    elif _provider == "ollama":
        kwargs["api_base"] = settings.OLLAMA_BASE_URL

    response = completion(**kwargs)
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content
