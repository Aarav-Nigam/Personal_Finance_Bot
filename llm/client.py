from __future__ import annotations

import json
from collections.abc import Generator

from litellm import completion

from config.settings import settings

SUPPORTED_PROVIDERS = {"gemini", "groq", "ollama"}


def _build_kwargs(provider: str | None = None, model: str | None = None) -> dict:
    _provider = provider or settings.LLM_PROVIDER
    _model = model or settings.LLM_MODEL
    kwargs: dict = {"model": _model}
    if _provider == "gemini":
        kwargs["api_key"] = settings.GOOGLE_API_KEY
    elif _provider == "groq":
        kwargs["api_key"] = settings.GROQ_API_KEY
    elif _provider == "ollama":
        kwargs["api_base"] = settings.OLLAMA_BASE_URL
    return kwargs


def chat(messages: list[dict], provider: str | None = None, model: str | None = None) -> str:
    kwargs = _build_kwargs(provider, model)
    kwargs["messages"] = messages
    response = completion(**kwargs)
    return response.choices[0].message.content


def chat_stream(
    messages: list[dict], provider: str | None = None, model: str | None = None
) -> Generator[str, None, None]:
    kwargs = _build_kwargs(provider, model)
    kwargs.update({"messages": messages, "stream": True})
    response = completion(**kwargs)
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def chat_tool_turn_stream(
    messages: list[dict],
    tools: list[dict],
    provider: str | None = None,
    model: str | None = None,
) -> Generator[dict, None, None]:
    kwargs = _build_kwargs(provider, model)
    kwargs.update({"messages": messages, "tools": tools, "stream": True})
    response = completion(**kwargs)

    accumulated_tool_calls: dict[int, dict] = {}

    for chunk in response:
        choice = chunk.choices[0]
        delta = choice.delta

        if delta.content:
            yield {"type": "text_delta", "content": delta.content}

        if hasattr(delta, "tool_calls") and delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx not in accumulated_tool_calls:
                    accumulated_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                if tc_delta.id:
                    accumulated_tool_calls[idx]["id"] = tc_delta.id
                if tc_delta.function and tc_delta.function.name:
                    accumulated_tool_calls[idx]["name"] = tc_delta.function.name
                if tc_delta.function and tc_delta.function.arguments:
                    accumulated_tool_calls[idx]["arguments"] += tc_delta.function.arguments

    for idx in sorted(accumulated_tool_calls):
        tc = accumulated_tool_calls[idx]
        try:
            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
        except json.JSONDecodeError:
            args = {}
        yield {
            "type": "tool_call",
            "id": tc["id"],
            "name": tc["name"],
            "arguments": args,
        }
