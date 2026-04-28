from __future__ import annotations

import json
from dataclasses import asdict

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_summary",
            "description": (
                "Get overall portfolio summary: total invested, current value, P&L, "
                "number of holdings, top 5 gainers and losers. Call when user asks about "
                "their portfolio overview or performance."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_holdings_pnl",
            "description": (
                "Get per-holding P&L breakdown. Optionally filter to a specific stock. "
                "Returns tradingsymbol, quantity, avg price, LTP, invested value, "
                "current value, P&L, P&L%. Omit symbol to get all holdings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol to filter (e.g. 'RELIANCE'). Omit for all.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_allocation",
            "description": (
                "Get portfolio allocation breakdown by instrument type or sector. "
                "Returns percentage weights."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "by": {
                        "type": "string",
                        "enum": ["instrument_type", "sector"],
                        "description": "Breakdown dimension. Default: instrument_type.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_status",
            "description": (
                "Get current market status (Open/Closed/Pre-Open), Nifty 50 level, "
                "and daily change percentage."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_fundamentals",
            "description": (
                "Get fundamental data for a stock: PE, forward PE, EV/EBITDA, PB, ROE, "
                "ROCE, debt/equity, EPS, revenue growth, market cap, sector, industry, "
                "52-week high/low, dividend yield."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE trading symbol (e.g. 'RELIANCE', 'TCS').",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_signal",
            "description": (
                "Compute buy/sell/hold signal (0-10 score) for a stock based on "
                "technical indicators (RSI, MACD, EMA, Bollinger Bands) and "
                "fundamental modifiers (PE, ROE). Returns score, label, and reasons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE trading symbol (e.g. 'INFY').",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": (
                "Get recent news headlines for a stock (up to 10). "
                "Use this to provide timely, news-aware advice."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE trading symbol (e.g. 'HDFCBANK').",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_margin_summary",
            "description": (
                "Get account margin/funds summary: available cash, collateral, "
                "intraday payin, opening balance, total available, total used, "
                "utilization percentage."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

PORTFOLIO_TOOLS = {
    "get_portfolio_summary",
    "get_holdings_pnl",
    "get_allocation",
    "get_margin_summary",
}

TOOL_DISPLAY_NAMES = {
    "get_portfolio_summary": "Fetching portfolio summary",
    "get_holdings_pnl": "Looking up holdings P&L",
    "get_allocation": "Checking allocation breakdown",
    "get_market_status": "Checking market status",
    "get_stock_fundamentals": "Fetching fundamentals for {symbol}",
    "get_stock_signal": "Computing signal for {symbol}",
    "get_news": "Getting news for {symbol}",
    "get_margin_summary": "Checking margin & funds",
}


def get_tool_display(name: str, args: dict) -> str:
    template = TOOL_DISPLAY_NAMES.get(name, f"Calling {name}")
    try:
        return template.format(**args)
    except KeyError:
        return template


def execute_tool(name: str, args: dict, context: dict) -> str:
    try:
        result = _dispatch(name, args, context)
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result, default=str)


def _dispatch(name: str, args: dict, context: dict):
    holdings_df = context.get("holdings_df")

    if name == "get_portfolio_summary":
        from analytics.portfolio import get_portfolio_summary

        raw = get_portfolio_summary(holdings_df)
        cols = ["tradingsymbol", "pnl", "pnl_pct"]
        raw["top_gainers"] = raw["top_gainers"][cols].to_dict(orient="records")
        raw["top_losers"] = raw["top_losers"][cols].to_dict(orient="records")
        return raw

    if name == "get_holdings_pnl":
        from analytics.portfolio import compute_pnl

        df = compute_pnl(holdings_df)
        symbol = args.get("symbol")
        if symbol:
            df = df[df["tradingsymbol"].str.upper() == symbol.upper()]
        elif len(df) > 20:
            df = df.nlargest(20, "current_value")
        out_cols = [
            "tradingsymbol", "quantity", "average_price", "last_price",
            "invested_value", "current_value", "pnl", "pnl_pct",
        ]
        return df[[c for c in out_cols if c in df.columns]].to_dict(orient="records")

    if name == "get_allocation":
        by = args.get("by", "instrument_type")
        if by == "sector":
            from analytics.portfolio import get_sector_allocation

            return get_sector_allocation(holdings_df)
        from analytics.portfolio import get_allocation

        return get_allocation(holdings_df)

    if name == "get_market_status":
        from analytics.portfolio import get_market_status

        return get_market_status()

    if name == "get_stock_fundamentals":
        from analytics.fundamentals import get_fundamentals

        return get_fundamentals(args["symbol"])

    if name == "get_stock_signal":
        from analytics.signals import compute_signal

        return asdict(compute_signal(args["symbol"]))

    if name == "get_news":
        from llm.sentiment import get_news_headlines

        return get_news_headlines(args["symbol"])

    if name == "get_margin_summary":
        from analytics.account import get_margin_summary

        return get_margin_summary()

    return {"error": f"Unknown tool: {name}"}
