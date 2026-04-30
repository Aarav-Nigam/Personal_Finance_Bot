from __future__ import annotations

TERMS: dict[str, str] = {
    # Technical indicators
    "RSI": "Relative Strength Index — measures if a stock is overbought (>70) or oversold (<30). Scale 0-100.",
    "MACD": "Moving Average Convergence Divergence — shows momentum shifts. Bullish when MACD crosses above signal line.",
    "EMA": "Exponential Moving Average — weighted average of recent prices. Faster EMAs (20-day) react quicker than slower ones (200-day).",
    "EMA20": "20-day Exponential Moving Average — short-term trend indicator. Price above EMA20 = short-term bullish.",
    "EMA50": "50-day Exponential Moving Average — medium-term trend. Acts as support/resistance.",
    "EMA200": "200-day Exponential Moving Average — long-term trend indicator. Price above EMA200 = long-term uptrend.",
    "ADX": "Average Directional Index — measures trend strength (not direction). Above 25 = strong trend, below 20 = no clear trend.",
    "OBV": "On-Balance Volume — tracks cumulative buying/selling pressure. Rising OBV = accumulation (bullish).",
    "MFI": "Money Flow Index — volume-weighted RSI. Below 20 = oversold, above 80 = overbought.",
    "Stochastic": "Stochastic Oscillator — compares closing price to its range. Below 20 = oversold, above 80 = overbought.",
    "Bollinger Bands": "Price envelope around a moving average (±2 std dev). Price near lower band = potentially cheap.",
    "MACD Histogram": "Difference between MACD and signal line. Rising = strengthening momentum.",
    # Fundamentals
    "PE": "Price-to-Earnings ratio — how much you pay per ₹1 of earnings. Lower PE = cheaper stock (compare within same sector).",
    "Forward PE": "PE based on expected future earnings. Lower than trailing PE = earnings expected to grow.",
    "PB": "Price-to-Book ratio — price vs net asset value. Below 1 means stock trades below its book value.",
    "ROE": "Return on Equity — profit generated per ₹1 of shareholder equity. Above 15% is generally good.",
    "EV/EBITDA": "Enterprise Value to EBITDA — valuation metric that accounts for debt. Lower = cheaper.",
    "Debt/Equity": "Total debt divided by shareholder equity. Below 1 is healthy, above 2 is risky.",
    "Dividend Yield": "Annual dividend as % of stock price. Higher yield = more income per ₹ invested.",
    "Revenue Growth": "Year-over-year increase in company's sales. Positive growth = expanding business.",
    "Promoter Holding": "% of shares held by company founders/promoters. Higher (>50%) signals management confidence.",
    "Market Cap": "Total market value of a company (share price × total shares). Large-cap = more stable.",
    # Portfolio metrics
    "XIRR": "Extended Internal Rate of Return — your actual annualized return accounting for all buy/sell dates and amounts.",
    "CAGR": "Compound Annual Growth Rate — smoothed annual return assuming constant compounding.",
    "Alpha": "Excess return over benchmark (Nifty 50). Positive alpha = you're beating the market.",
    "P&L": "Profit & Loss — difference between current value and invested amount.",
    "Unrealized P&L": "Paper profit/loss on holdings you still own. Becomes 'realized' only when you sell.",
    "Realized P&L": "Actual profit/loss from stocks you've already sold. This is real money in/out.",
    # Tax
    "STCG": "Short-Term Capital Gains — profit from stocks held less than 12 months. Taxed at 20% (FY 2024-25).",
    "LTCG": "Long-Term Capital Gains — profit from stocks held 12+ months. Taxed at 12.5% above ₹1.25L exemption.",
    "FIFO": "First-In-First-Out — oldest shares are considered sold first (used for tax calculation).",
    # Signals
    "Signal Score": "Combined score from -10 to +10 across 6 factors. Positive = bullish, negative = bearish, 0 = neutral.",
    "Confidence": "How much data was available to compute the signal (0-100%). Higher = more reliable signal.",
    "Momentum": "Speed and direction of price movement. Combines RSI, MACD, Stochastic indicators.",
    "Trend": "Overall price direction using moving averages and ADX. Strong uptrend/downtrend or sideways.",
    "Volume": "Trading activity level. High volume confirms price moves; low volume = unreliable moves.",
    "Sentiment": "Market mood from news headlines (AI-analyzed) and analyst recommendations.",
    "Context": "Where the stock sits relative to its 52-week range, historical average, and overall market.",
    # Account
    "Margin": "Money available for trading. Includes cash + collateral from holdings.",
    "Collateral": "Value of your holdings that the broker allows as trading margin (usually 50-80% of stock value).",
    "M2M": "Mark-to-Market — daily profit/loss on open positions, settled at end of day.",
    # Risk metrics
    "PEG": "Price/Earnings-to-Growth ratio — PE divided by earnings growth rate. Below 1 = undervalued on growth basis.",
    "Beta": "How much a stock moves relative to the market. Beta 1.5 = 50% more volatile than Nifty 50.",
    "Free Cash Flow": "Cash left after all expenses and investments. Positive FCF = company generates real cash.",
    "ATR": "Average True Range — measures daily price volatility. Used to set stop-losses (typically 2x ATR below entry).",
    "Sharpe Ratio": "Risk-adjusted return: (return - risk-free rate) / volatility. Above 1 is good, above 2 is excellent.",
    "Max Drawdown": "Largest peak-to-trough decline in portfolio value. Shows worst-case loss experience.",
    "VaR 95%": "Value at Risk — the maximum daily loss you'd expect 95% of the time. 5% of days may be worse.",
    "Portfolio Beta": "Weighted average beta of all your holdings. Above 1 = portfolio is more volatile than Nifty.",
    "HHI": "Herfindahl-Hirschman Index — concentration measure. Below 1500 = diversified, above 2500 = concentrated.",
    "Stop Loss": "Price level where you exit to limit losses. Typically set at 2x ATR below your entry price.",
    "Position Size": "How many shares to buy based on risk budget (2% of portfolio per trade / distance to stop-loss).",
    "Risk/Reward": "Ratio of potential profit to potential loss. Above 2:1 means reward is twice the risk — worth taking.",
    "Support": "Price level where buyers tend to step in. Derived from pivot point calculations.",
    "Resistance": "Price level where sellers tend to step in. Stock may struggle to break above this.",
    "Pivot Point": "Key reference price = (High + Low + Close) / 3. Used to derive support/resistance levels.",
    # General
    "52-Week Range": "Highest and lowest price in the last 1 year. Shows how volatile the stock is.",
    "Win Rate": "% of your completed trades that made a profit.",
    "Holding Period": "Average number of days between buying and selling a stock.",
    "SIP": "Systematic Investment Plan — investing a fixed amount regularly (e.g., monthly) in mutual funds.",
    "NAV": "Net Asset Value — price per unit of a mutual fund.",
    "Nifty 50": "Index of top 50 Indian companies by market cap. The benchmark for Indian equity performance.",
}


def tip(term: str, label: str | None = None) -> str:
    display = label or term
    explanation = TERMS.get(term, "")
    if not explanation:
        return display
    return (
        f'<span title="{explanation}" style="border-bottom:1px dotted #9E9E9E;'
        f'cursor:help;">{display}</span>'
    )


def tip_md(term: str, label: str | None = None) -> str:
    display = label or term
    explanation = TERMS.get(term, "")
    if not explanation:
        return display
    return (
        f'<span title="{explanation}" style="border-bottom:1px dotted #9E9E9E;'
        f'cursor:help;font-weight:600;">{display}</span>'
    )


SIGNAL_EXPLANATIONS: list[tuple[str, str]] = [
    ("RSI strongly oversold", "Stock is heavily sold off — buyers may step in soon."),
    ("RSI oversold zone", "Stock is getting cheap — watch for a reversal."),
    ("RSI overbought", "Stock is overheated — buyers are exhausted, pullback likely."),
    ("RSI approaching overbought", "Stock is getting pricey — momentum may slow down."),
    ("MACD bullish crossover", "Momentum is shifting upward — a buy signal."),
    ("MACD bearish crossover", "Momentum is fading — a sell signal."),
    ("MACD histogram rising", "Bullish momentum is strengthening each day."),
    ("MACD histogram falling", "Bearish pressure is building each day."),
    ("Stochastic oversold cross-up", "Stock bounced from extreme low — strong buy signal."),
    ("Stochastic overbought cross-down", "Stock dropped from extreme high — sell signal."),
    ("Strong uptrend", "All moving averages are aligned upward — stock is in a clear rally."),
    ("Strong downtrend", "All moving averages are aligned downward — stock is in a clear decline."),
    ("Strong bullish trend", "Trend is powerful and moving up — ride the wave."),
    ("Strong bearish trend", "Trend is powerful and moving down — avoid or sell."),
    (
        "Price at upper Bollinger Band",
        "Stock has stretched too far above average — likely to cool off.",
    ),
    ("Price at lower Bollinger Band", "Stock has dipped well below average — could bounce back."),
    ("High volume on up-day", "Lots of buyers are piling in — confirms the rally is real."),
    ("High volume on down-day", "Lots of sellers are dumping — confirms the drop is real."),
    ("Very low volume", "Almost no one is trading — any price move is unreliable."),
    ("OBV rising", "Smart money is accumulating — buying pressure building quietly."),
    ("OBV falling", "Smart money is distributing — selling pressure building quietly."),
    ("MFI oversold", "Money is flowing out heavily — stock may be oversold."),
    ("MFI overbought", "Money is flowing in heavily — stock may be overbought."),
    ("Attractively valued", "Stock is cheap relative to its earnings — good entry point."),
    ("Very expensive", "Stock costs way too much for what it earns — risky to buy here."),
    ("Expensive valuation", "Stock is pricey — you're paying a premium for growth hopes."),
    ("Earnings growth expected", "Analysts expect profits to grow — future looks brighter."),
    ("Excellent ROE", "Company makes great returns on shareholder money — well managed."),
    ("High debt", "Company owes a lot — risky if earnings slow down."),
    ("Strong revenue growth", "Sales are growing fast — business is expanding."),
    ("Revenue declining", "Sales are shrinking — business may be in trouble."),
    ("Low promoter holding", "Founders own very little — less skin in the game."),
    ("Very positive news sentiment", "Almost all recent news is positive — market is optimistic."),
    ("Positive news sentiment", "More good news than bad lately."),
    ("Very negative news sentiment", "Almost all recent news is negative — market is worried."),
    ("Negative news sentiment", "More bad news than good lately."),
    ("Analyst:", "Professional analyst opinion from brokerage research."),
    (
        "Near 52-week low",
        "Stock is near its cheapest point this year — could be a bargain or a falling knife.",
    ),
    (
        "Near 52-week high",
        "Stock is near its most expensive this year — may be running out of steam.",
    ),
    (
        "overextended above 200-day avg",
        "Price has run too far above its long-term average — pullback likely.",
    ),
    (
        "oversold vs 200-day avg",
        "Price has fallen too far below its long-term average — bounce likely.",
    ),
    ("Nifty in uptrend", "The overall market is going up — tailwind for most stocks."),
    ("Nifty in downtrend", "The overall market is falling — headwind for most stocks."),
    ("Consider partial profit booking", "You've made 30%+ — locking in some gains reduces risk."),
    ("Extended gains", "You've made 50%+ — strong candidate for profit booking."),
    ("Mean reversion likely", "You're down 20% — statistically likely to recover some."),
    ("Cut losses", "You're down 40%+ — something may be fundamentally wrong, reconsider holding."),
    # Phase 2: Enriched signal explanations
    ("PEG undervalued", "Stock is cheap relative to its growth rate — good value."),
    ("PEG expensive", "You're paying a lot for the growth this company delivers."),
    (
        "Strong free cash flow",
        "Company generates real cash after all spending — financially healthy.",
    ),
    (
        "Negative free cash flow",
        "Company is burning more cash than it earns — watch the balance sheet.",
    ),
    (
        "High profit margin",
        "Company keeps a big chunk of revenue as profit — high quality business.",
    ),
    (
        "Strong earnings growth",
        "Profits are growing fast — the business is firing on all cylinders.",
    ),
    ("Declining earnings", "Profits are shrinking — the business may be losing its edge."),
    ("High institutional ownership", "Big fund houses own this stock — smart money validation."),
    ("High short interest", "Many traders are betting against this stock — bearish pressure."),
    ("Elevated short interest", "Shorts are building up — some traders expect a decline."),
    ("Analyst target", "Professional analyst price target — how far the stock could go."),
    ("upside to analyst target", "Analysts think the stock can go higher from here."),
    ("downside to analyst target", "Analysts think the stock is overpriced at current levels."),
]


def explain_signal(reason: str) -> str:
    reason_lower = reason.lower()
    for keyword, explanation in SIGNAL_EXPLANATIONS:
        if keyword.lower() in reason_lower:
            return explanation
    return ""
