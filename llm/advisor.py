from __future__ import annotations

import json
from collections.abc import Generator

import pandas as pd

from llm.client import chat, chat_stream, chat_tool_turn_stream
from llm.prompts import ADVISOR_SYSTEM_PROMPT, ADVISOR_TOOLS_INSTRUCTION
from llm.tools import PORTFOLIO_TOOLS, TOOL_SCHEMAS, execute_tool, get_tool_display

MAX_TOOL_ROUNDS = 5


def _get_tools(holdings_df: pd.DataFrame | None) -> list[dict]:
    if holdings_df is not None and not holdings_df.empty:
        return TOOL_SCHEMAS
    return [t for t in TOOL_SCHEMAS if t["function"]["name"] not in PORTFOLIO_TOOLS]


def _build_system_prompt(has_portfolio: bool) -> str:
    parts = [ADVISOR_SYSTEM_PROMPT, ADVISOR_TOOLS_INSTRUCTION]
    if not has_portfolio:
        parts.append(
            "\nNote: No portfolio is connected. You can still use market data, "
            "fundamentals, signals, and news tools."
        )
    return "\n".join(parts)


def get_advice_stream_with_tools(
    user_message: str,
    holdings_df: pd.DataFrame | None = None,
    conversation_history: list[dict] | None = None,
) -> Generator[dict, None, None]:
    context = {"holdings_df": holdings_df}
    has_portfolio = holdings_df is not None and not holdings_df.empty
    tools = _get_tools(holdings_df)

    messages: list[dict] = [{"role": "system", "content": _build_system_prompt(has_portfolio)}]
    for msg in conversation_history or []:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    full_text = ""

    for _ in range(MAX_TOOL_ROUNDS):
        turn_type = None
        tool_calls_this_turn: list[dict] = []

        for event in chat_tool_turn_stream(messages, tools):
            if event["type"] == "text_delta":
                if turn_type is None:
                    turn_type = "text"
                full_text += event["content"]
                yield event

            elif event["type"] == "tool_call":
                if turn_type is None:
                    turn_type = "tools"
                tool_calls_this_turn.append(event)

        if turn_type == "tools":
            assistant_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in tool_calls_this_turn
                ],
            }
            messages.append(assistant_msg)

            for tc in tool_calls_this_turn:
                display = get_tool_display(tc["name"], tc["arguments"])
                yield {"type": "tool_call", "name": tc["name"], "display": display}

                result = execute_tool(tc["name"], tc["arguments"], context)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    }
                )
                yield {"type": "tool_result", "name": tc["name"]}

            continue

        if turn_type == "text":
            yield {"type": "done", "full_text": full_text}
            return

        break

    if not full_text:
        full_text = "I was unable to complete the analysis. Please try again."
    yield {"type": "done", "full_text": full_text}


# Legacy non-tool versions kept for backward compatibility


def _build_messages(
    user_message: str,
    holdings_df: pd.DataFrame | None,
    conversation_history: list[dict],
) -> list[dict]:
    from llm.prompts import build_market_context, build_portfolio_context

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
