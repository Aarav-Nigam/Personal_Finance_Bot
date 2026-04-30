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
                "Compute buy/sell/hold signal (-10 to +10 score) for a stock based on "
                "6 weighted categories: momentum, trend, volume, fundamentals, sentiment, "
                "and market context. Positive = bullish, negative = bearish. "
                "Returns score, label, confidence, sub-scores, and reasons."
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
    {
        "type": "function",
        "function": {
            "name": "get_risk_metrics",
            "description": (
                "Get portfolio risk metrics: weighted beta, Sharpe ratio, "
                "annualized volatility, max drawdown, VaR 95%, concentration risk "
                "(HHI, top-3 weight, alerts), and Nifty Sharpe for comparison."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_actionable_targets",
            "description": (
                "Get actionable trading targets for a stock: ATR-based stop-loss, "
                "analyst price target (mean/high/low), pivot support/resistance levels, "
                "position size (2% risk model), and risk/reward ratio."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE trading symbol (e.g. 'RELIANCE').",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rebalance_suggestions",
            "description": (
                "Get portfolio rebalancing suggestions: shows drift from target allocation, "
                "recommends specific Add/Trim/Hold actions with share counts based on "
                "signals and drift. Strategy: 'equal_weight' or 'signal_weighted'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "enum": ["equal_weight", "signal_weighted"],
                        "description": "Allocation strategy. Default: signal_weighted.",
                    },
                },
                "required": [],
            },
        },
    },
]

PORTFOLIO_TOOLS = {
    "get_portfolio_summary",
    "get_holdings_pnl",
    "get_allocation",
    "get_margin_summary",
    "get_risk_metrics",
    "get_rebalance_suggestions",
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
    "get_risk_metrics": "Analyzing portfolio risk",
    "get_actionable_targets": "Computing targets for {symbol}",
    "get_rebalance_suggestions": "Generating rebalance plan",
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
            "tradingsymbol",
            "quantity",
            "average_price",
            "last_price",
            "invested_value",
            "current_value",
            "pnl",
            "pnl_pct",
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

    if name == "get_risk_metrics":
        from analytics.risk import (
            compute_portfolio_returns,
            concentration_risk,
            max_drawdown,
            nifty_sharpe,
            portfolio_beta,
            portfolio_volatility,
            sharpe_ratio,
            var_95,
        )

        beta = portfolio_beta(holdings_df)
        returns_df, weights = compute_portfolio_returns(holdings_df)
        vol = portfolio_volatility(returns_df, weights) if not returns_df.empty else None
        sharpe_val = sharpe_ratio(returns_df, weights) if not returns_df.empty else None
        mdd = max_drawdown(returns_df, weights) if not returns_df.empty else None
        var_val = var_95(returns_df, weights) if not returns_df.empty else None
        concentration = concentration_risk(holdings_df)
        nifty_s = nifty_sharpe()
        return {
            "portfolio_beta": beta,
            "annualized_volatility": vol,
            "sharpe_ratio": sharpe_val,
            "max_drawdown": mdd,
            "var_95_pct": var_val,
            "concentration": concentration,
            "nifty_sharpe": nifty_s,
        }

    if name == "get_actionable_targets":
        from analytics.targets import compute_actionable_targets

        portfolio_value = None
        if holdings_df is not None and not holdings_df.empty:
            portfolio_value = float((holdings_df["last_price"] * holdings_df["quantity"]).sum())
        return compute_actionable_targets(args["symbol"], portfolio_value=portfolio_value)

    if name == "get_rebalance_suggestions":
        from analytics.rebalance import suggest_rebalance

        strategy = args.get("strategy", "signal_weighted")
        suggestions = suggest_rebalance(holdings_df, strategy=strategy)
        return suggestions

    return {"error": f"Unknown tool: {name}"}
