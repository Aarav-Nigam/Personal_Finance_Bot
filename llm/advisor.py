from __future__ import annotations

from collections.abc import Generator

import pandas as pd

from llm.client import chat, chat_stream
from llm.prompts import ADVISOR_SYSTEM_PROMPT, build_market_context, build_portfolio_context


def _build_messages(
    user_message: str,
    holdings_df: pd.DataFrame | None,
    conversation_history: list[dict],
) -> list[dict]:
    context_parts = [ADVISOR_SYSTEM_PROMPT]

    portfolio_ctx = build_portfolio_context(holdings_df) if holdings_df is not None else ""
    if portfolio_ctx:
        context_parts.append(f"\n\nUser's Portfolio:\n{portfolio_ctx}")

    market_ctx = build_market_context()
    if market_ctx:
        context_parts.append(f"\n\nMarket: {market_ctx}")

    messages = [{"role": "system", "content": "\n".join(context_parts)}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    return messages


def get_advice(
    user_message: str,
    holdings_df: pd.DataFrame | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    messages = _build_messages(user_message, holdings_df, conversation_history or [])
    return chat(messages)


def get_advice_stream(
    user_message: str,
    holdings_df: pd.DataFrame | None = None,
    conversation_history: list[dict] | None = None,
) -> Generator[str, None, None]:
    messages = _build_messages(user_message, holdings_df, conversation_history or [])
    yield from chat_stream(messages)
