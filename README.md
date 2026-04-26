# PersonalFinanceBot

> An open-source, free, AI-powered portfolio management tool for Indian stocks and mutual funds — built with Streamlit, Zerodha Kite Connect, and local/free LLMs.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-red)
![Free](https://img.shields.io/badge/cost-100%25%20free-brightgreen)

---

## Overview

PersonalFinanceBot connects to your Zerodha portfolio via the Kite Connect API (or a CSV export), enriches that data with live market prices and technical/fundamental indicators, and surfaces everything through a clean multi-page Streamlit dashboard. An AI Advisor tab lets you chat with your portfolio using Google Gemini, Groq (Llama), or a completely offline Ollama model — no paid subscriptions required.

**This project is intentionally free-first:** every API used either has a generous free tier or runs entirely offline.

---

## Features

### Portfolio Management
- Live portfolio sync via Kite Connect API (Zerodha personal tier)
- CSV fallback — import holdings exported from Zerodha, Groww, or Kuvera
- Real-time P&L and unrealized gains/losses per holding
- Portfolio XIRR calculated and compared against Nifty 50 benchmark
- Sector-wise and asset-class allocation pie charts
- Average buy price and cost basis tracking
- Top 5 gainers and losers at a glance

### Stock Analysis
- Interactive price chart with configurable date range
- Technical indicator overlays: EMA 20 / 50 / 200, Bollinger Bands
- Subplots: RSI (14), MACD (12, 26, 9)
- Fundamental scorecard: P/E ratio, forward P/E, EV/EBITDA, ROE, ROCE, Debt/Equity, Promoter holding %, EPS TTM
- 52-week high/low proximity gauge
- NSE live quote (open, high, low, volume, circuit limits)
- Analyst consensus summary (from Yahoo Finance)

### Mutual Fund Tracking
- NAV history chart for any AMFI-registered fund (via MFAPI.in — free, no auth)
- SIP XIRR calculator: enter installment dates + amounts + current value, get true annualised return
- Fund search by name or AMC
- Category comparison: top funds by 1Y / 3Y / 5Y returns
- Expense ratio and AUM information

### Buy / Sell Signals
- 10-point scored signal engine combining technical and fundamental analysis
- Per-stock signal card: score, category (Strong Buy / Buy / Hold / Sell / Strong Sell), reason breakdown
- Watchlist management — track any NSE ticker, not just your holdings
- RSI screener: all watched stocks sorted by RSI value
- MACD crossover detection (bullish / bearish crossover within the last 3 candles)
- EMA200 trend filter: flag stocks trading below their 200-day moving average

### Tax Calculator (India FY 2024-25)
- Classify each lot as LTCG (> 1 year) or STCG (≤ 1 year)
- LTCG on equity: 12.5% above ₹1.25 lakh annual exemption (Budget 2024)
- STCG on equity: 20% flat (Budget 2024)
- Debt mutual fund: taxed at income slab rate regardless of holding period (post-April 2023)
- Tax-loss harvesting suggestions: shows unrealised losses in your portfolio that could offset booked gains
- Export-ready summary table

### AI Portfolio Advisor
- Chat interface with full portfolio context injected as system prompt
- Supports three free LLM backends (selectable from a dropdown in the UI):
  - **Google Gemini 2.0 Flash** — 15 requests/min, 1,500 requests/day free via Google AI Studio
  - **Groq (Llama 3.3 70B)** — fast cloud inference, free tier
  - **Ollama (local)** — completely offline, supports Qwen2.5, Llama3.3, Mistral, and others
- FinBERT sentiment analysis on the last 10 news headlines for any stock (local HuggingFace model, ~500 MB one-time download)
- Pre-built query buttons: "Suggest rebalancing", "What should I sell?", "Best SIP for 5 years", "Explain my XIRR"
- Conversation history preserved for the session

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Streamlit UI                               │
│  1_Portfolio │ 2_Stocks │ 3_MutualFunds │ 4_Signals │ 5_Tax │ 6_AI  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
     ┌───────▼───────┐  ┌──────▼──────┐  ┌──────▼────────┐
     │  analytics/   │  │    llm/     │  │    data/      │
     │               │  │             │  │               │
     │ portfolio.py  │  │ client.py   │  │ kite_client   │
     │ technicals.py │  │ advisor.py  │  │ market_data   │
     │ fundamentals  │  │ prompts.py  │  │ mf_client     │
     │ signals.py    │  └──────┬──────┘  │ nse_client    │
     │ mf_analytics  │         │         │ cache.py      │
     │ tax.py        │         │         └──────┬────────┘
     └───────────────┘         │                │
                               │                │
             ┌─────────────────┘                │
             │                                  │
   ┌─────────▼──────────────┐      ┌────────────▼───────────────────┐
   │     Free LLM Backends  │      │       External APIs (Free)     │
   │                        │      │                                │
   │ • Gemini 2.0 Flash     │      │ • Kite Connect (Zerodha)       │
   │   (Google AI Studio)   │      │   holdings, positions, orders  │
   │ • Ollama (local)       │      │                                │
   │   qwen2.5 / llama3.3   │      │ • yfinance (Yahoo Finance)     │
   │ • Groq free tier       │      │   prices, OHLCV, fundamentals  │
   │   llama-3.3-70b        │      │                                │
   │ • FinBERT (HF local)   │      │ • MFAPI.in (AMFI data)         │
   │   financial sentiment  │      │   NAV history, fund list       │
   └────────────────────────┘      │                                │
                                   │ • nsepython (NSE scraper)      │
                                   │   live quotes, option chain    │
                                   └────────────────────────────────┘
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| `streamlit` | Multi-page web UI |
| `plotly` | Interactive candlestick, line, and pie charts |
| `kiteconnect` | Zerodha Kite Connect SDK — portfolio data |
| `yfinance` | Yahoo Finance — historical prices, fundamentals |
| `nsepython` | NSE India live quotes and option chain (unofficial) |
| `requests` | HTTP calls to MFAPI.in |
| `pandas` | Data manipulation and analysis |
| `numpy` | Numerical calculations |
| `pandas-ta` | Technical indicators (RSI, MACD, EMA, BBands) |
| `pyxirr` | XIRR / IRR calculation for SIP returns |
| `litellm` | Unified LLM client (Gemini, Ollama, Groq) |
| `transformers` | HuggingFace FinBERT for sentiment analysis |
| `torch` | PyTorch backend for FinBERT inference |
| `python-dotenv` | Load `.env` file into environment |

---

## Prerequisites

- **Python 3.10 or higher**
- A **Zerodha account** for Kite Connect API access (or export a holdings CSV from any broker)
- At least **one LLM backend** for the AI Advisor:
  - [Google AI Studio](https://aistudio.google.com) — free, get a `GOOGLE_API_KEY`
  - [Groq](https://console.groq.com) — free tier, get a `GROQ_API_KEY`
  - [Ollama](https://ollama.com) — local, install and pull a model (e.g. `ollama pull qwen2.5`)
- Git

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/PersonalFinanceBot.git
cd PersonalFinanceBot
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Installing `torch` for FinBERT pulls ~2 GB. If you don't want the AI Advisor's sentiment feature, comment out `transformers` and `torch` in `requirements.txt` and set `FINBERT_ENABLED=false` in your `.env`.

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your keys (see Environment Variables section below)
```

### 5. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values you need. Every variable is optional except at least one LLM key for the AI Advisor.

```bash
# ─────────────────────────────────────────────────────────────────────
# Kite Connect (Zerodha)
# Required for live portfolio sync. Leave blank to use CSV import.
# ─────────────────────────────────────────────────────────────────────
KITE_API_KEY=             # From kite.trade developer console
KITE_API_SECRET=          # From kite.trade developer console
KITE_ACCESS_TOKEN=        # Generated daily via scripts/kite_auth.py

# ─────────────────────────────────────────────────────────────────────
# LLM Backends (at least one required for AI Advisor)
# ─────────────────────────────────────────────────────────────────────
GOOGLE_API_KEY=           # Google AI Studio — free tier (15 RPM / 1500 RPD)
GROQ_API_KEY=             # Groq Cloud — free tier, ultra-fast inference
OLLAMA_BASE_URL=http://localhost:11434    # Ollama local server URL

# Default LLM provider when the app starts
# Options: gemini | groq | ollama
LLM_PROVIDER=gemini

# Default model name (LiteLLM format)
# Gemini: gemini/gemini-2.0-flash-exp
# Groq:   groq/llama-3.3-70b-versatile
# Ollama: ollama/qwen2.5
LLM_MODEL=gemini/gemini-2.0-flash-exp

# ─────────────────────────────────────────────────────────────────────
# FinBERT Sentiment (optional — ~500 MB first-time download)
# ─────────────────────────────────────────────────────────────────────
FINBERT_ENABLED=true      # Set to false to disable sentiment analysis

# ─────────────────────────────────────────────────────────────────────
# Cache settings
# ─────────────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS=300     # How long to cache market data (seconds). Default 5 min.
CACHE_DIR=.cache          # Directory for JSON cache files
```

---

## Kite Connect Authentication

Kite Connect access tokens expire every day at 6:00 AM IST. You need to refresh the token each trading day before using live portfolio data.

### One-time setup

1. Log in to [kite.trade](https://kite.trade) and create a new app under **Developer Console**
2. Set redirect URL to `http://localhost:8080`
3. Copy your **API Key** and **API Secret** into `.env`

### Daily token refresh

Run this script each morning (or whenever the app shows "Invalid access token"):

```bash
python scripts/kite_auth.py
```

The script will:
1. Open the Kite login URL in your browser
2. Ask you to paste the full redirect URL after login (it contains the `request_token`)
3. Exchange the request token for an access token
4. Automatically write `KITE_ACCESS_TOKEN=...` into your `.env` file

### Automating the refresh (optional)

Add a cron job to run the script at 8:30 AM IST daily. Since the token exchange requires a browser login, you will still need to complete the login step manually — the script just handles the API exchange automatically after you paste the URL.

---

## CSV Import (No Kite API Required)

If you don't have Kite Connect API access, you can import a static holdings CSV. The app detects the absence of `KITE_ACCESS_TOKEN` and shows a file uploader.

### Supported CSV formats

**Zerodha Console export** (Holdings → Download as CSV):
```
Instrument,Quantity,Avg. cost,LTP,Cur. val,P&L,Net chg.,Day chg.
RELIANCE,10,2450.00,2510.50,25105.00,605.00,2.47%,0.82%
```

**Generic format** (fallback — the app auto-detects column names):
| Required columns | Optional columns |
|---|---|
| `symbol` (NSE ticker) | `exchange` (defaults to NSE) |
| `quantity` | `isin` |
| `avg_cost` (average buy price) | `product` (CNC / MIS) |

**Groww / Kuvera exports** are also auto-detected by column name matching.

---

## App Pages

### 1. Portfolio Overview
The landing page. Shows your complete holdings table with current price, P&L, P&L%, invested value, and current value. Sector allocation pie chart on the right. Cards at the top display:
- Total invested amount
- Current portfolio value
- Unrealised P&L (absolute + %)
- Portfolio XIRR vs Nifty 50 XIRR for the same period

Use the date range slider to see portfolio value over time.

### 2. Stock Analysis
Search any NSE ticker (e.g., `RELIANCE`, `TCS`, `INFY`) to get a full analysis page:

**Price chart** — Candlestick OHLCV with selectable overlays: EMA20, EMA50, EMA200, Bollinger Bands (20, 2).

**Signal card** — Buy / Hold / Sell score from 0–10 with a breakdown of which conditions contributed (see Signal Methodology below).

**Fundamentals table:**
| Metric | Source |
|---|---|
| P/E (TTM) | Yahoo Finance |
| Forward P/E | Yahoo Finance |
| EV/EBITDA | Yahoo Finance |
| Price/Book | Yahoo Finance |
| ROE | Yahoo Finance |
| ROCE | Derived from yfinance financials |
| Debt/Equity | Yahoo Finance |
| Promoter holding % | NSE via nsepython |
| EPS (TTM) | Yahoo Finance |
| Revenue growth (YoY) | Yahoo Finance financials |

**News + sentiment** — 5 latest headlines with FinBERT sentiment label (Positive / Neutral / Negative) and score.

### 3. Mutual Funds
- **NAV History** — search any AMFI fund name, view NAV chart for 1M / 3M / 6M / 1Y / 3Y / 5Y
- **SIP XIRR Calculator** — enter a list of (date, amount) SIP payments and your current NAV, get annualised XIRR
- **Fund Search** — search by AMC or fund name, see snapshot (AUM, expense ratio, category, fund manager)
- **Category Leaderboard** — top 10 funds by 3Y return in a chosen category (Large Cap, ELSS, Flexi Cap, etc.)

### 4. Signals Dashboard
Master screener across your watchlist. Each row shows:
- Ticker, current price, 1D change %
- Technical score (0–10) and the top triggering conditions
- Signal badge: **Strong Buy** (≥8) / **Buy** (6–7) / **Hold** (4–5) / **Sell** (2–3) / **Strong Sell** (0–1)
- RSI value with colour coding
- MACD crossover status

Add/remove tickers to your watchlist from this page. The watchlist persists in `watchlist.json`.

### 5. Tax Calculator
**Equity LTCG/STCG calculator:**
1. Enter each lot: ticker, buy date, buy price, sell date, sell price, quantity
2. The app classifies the lot and calculates tax
3. Summary card shows total STCG, total LTCG, exempt LTCG (up to ₹1.25L), and net tax due

**Tax-loss harvesting:**
Scans your current unrealised losses and shows which holdings you could sell to offset booked gains, ranked by loss amount.

**FY selector** — supports FY 2023-24 and FY 2024-25 (different LTCG/STCG rates apply).

### 6. AI Portfolio Advisor
Chat interface powered by your chosen LLM. The system prompt is automatically populated with:
- Your current holdings, quantities, average costs, current P&L
- Portfolio XIRR and allocation summary
- Market context (Nifty 50 level, top sector performance for the day)

Pre-built queries (click to send):
- "Suggest portfolio rebalancing"
- "Which stocks should I consider selling?"
- "Analyse my sector exposure"
- "Recommend SIP funds for a 5-year horizon"
- "Explain my portfolio XIRR vs benchmark"
- "What is my tax situation this FY?"

LLM provider dropdown lets you switch between Gemini, Groq, and Ollama mid-session.

---

## Signal Methodology

The signal engine in `analytics/signals.py` computes a score from 0 to 10 for each stock. The score is the sum of technical signals only; fundamentals act as a modifier. A buy is triggered at score ≥ 6, a sell at score ≤ 3.

### Technical Score (0–10)

| Condition | Points |
|---|---|
| RSI (14) < 40 — oversold territory | +2 |
| MACD line crosses above signal line (last 3 candles) — bullish crossover | +2 |
| Current price above EMA 200 — long-term uptrend intact | +2 |
| Current price below EMA 20 — short-term dip in an uptrend | +2 |
| Current price touches or dips below Bollinger lower band (20, 2) | +2 |

### Fundamental Modifier (adjusts score by ±2)

| Condition | Modifier |
|---|---|
| P/E ratio < 30 AND ROE > 15% AND Debt/Equity < 1 | +2 (fundamentally healthy) |
| P/E ratio > 50 OR Debt/Equity > 3 OR EPS declining YoY | −2 (fundamentally stretched) |

### Signal Thresholds

| Score | Signal |
|---|---|
| 9–10 | Strong Buy |
| 7–8 | Buy |
| 4–6 | Hold |
| 2–3 | Sell |
| 0–1 | Strong Sell |

> **Important:** These signals are informational tools, not financial advice. Always do your own research before making investment decisions.

---

## Tax Calculator Methodology

### Equity and Equity Mutual Funds

| Holding period | Tax treatment (FY 2024-25) |
|---|---|
| ≤ 1 year (STCG) | 20% flat on gains |
| > 1 year (LTCG) | 12.5% on gains above ₹1,25,000 annual exemption |

The ₹1.25L LTCG exemption applies per financial year across all equity sales. The exemption is applied first to the oldest lots (FIFO by default).

### Debt Mutual Funds (post-April 2023)

All gains from debt mutual funds are taxed at your income slab rate regardless of holding period. No indexation benefit applies for units purchased after 1 April 2023.

### Dividend Income

Dividends received from stocks and mutual funds are added to your total income and taxed at your applicable slab rate. Track them separately; they are not computed in this tool.

### Tax-Loss Harvesting Logic

The tool scans unrealised losses ≥ ₹500 in your holdings and pairs them with booked LTCG/STCG to show how much tax you could save by booking those losses before the financial year ends.

---

## AI Advisor — LLM Setup

### Option 1: Google Gemini (Recommended for most users)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key** → Create API key
3. Add to `.env`: `GOOGLE_API_KEY=your-key`
4. Set: `LLM_PROVIDER=gemini` and `LLM_MODEL=gemini/gemini-2.0-flash-exp`

Free tier limits: 15 requests/minute, 1,500 requests/day, 1 million tokens/minute.

### Option 2: Groq (Ultra-fast, free tier)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up and create an API key
3. Add to `.env`: `GROQ_API_KEY=your-key`
4. Set: `LLM_PROVIDER=groq` and `LLM_MODEL=groq/llama-3.3-70b-versatile`

Free tier limits: 6,000 requests/day, 500K tokens/day on the 70B model.

### Option 3: Ollama (Fully offline, no API key)

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model:
   ```bash
   ollama pull qwen2.5       # Good all-round (4.7 GB)
   # or
   ollama pull llama3.3      # Meta Llama 3.3 (42 GB — needs 64 GB RAM)
   # or
   ollama pull mistral       # Mistral 7B (4.1 GB — fast on CPU)
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```
4. Set: `LLM_PROVIDER=ollama`, `LLM_MODEL=ollama/qwen2.5`, `OLLAMA_BASE_URL=http://localhost:11434`

### FinBERT Sentiment

FinBERT (`ProsusAI/finbert`) is downloaded automatically from HuggingFace on first use (~500 MB). It runs locally with no API key. To disable it:

```bash
FINBERT_ENABLED=false
```

---

## Extending the Project

### Adding a new data source

1. Create a new file in `data/` (e.g., `data/screener_client.py`)
2. Implement a function that returns a `pandas.DataFrame` or plain dict
3. Add a `cache.py` TTL wrapper around expensive HTTP calls
4. Import and use it from the relevant `analytics/` module

### Adding a new technical indicator

1. Open `analytics/technicals.py`
2. Add a function that takes a `pd.DataFrame` with `close` / `high` / `low` / `volume` columns
3. Use `pandas_ta` where possible: `df.ta.your_indicator()`
4. Return the DataFrame with the new column appended
5. Wire the new indicator into `analytics/signals.py` if it should affect the score

### Adding a new Streamlit page

1. Create `pages/7_YourPage.py` (the number prefix controls the sidebar order)
2. Add `st.set_page_config(page_title="...", page_icon="...")` at the top
3. Import from `data/`, `analytics/`, or `llm/` as needed
4. The page will automatically appear in the sidebar

### Adding a new LLM provider

LiteLLM supports 100+ providers. To add one:

1. Set the provider's API key as an environment variable
2. In `llm/client.py`, add the provider to the `SUPPORTED_PROVIDERS` dict with its LiteLLM model string format
3. Add the provider name to the dropdown list in `pages/6_AI_Advisor.py`

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository and create a feature branch (`git checkout -b feature/my-feature`)
2. Keep commits small and focused
3. Run `ruff check .` and `ruff format .` before committing (both are in `requirements.txt`)
4. Open a pull request with a clear description of what changed and why

### Reporting issues

Open a GitHub Issue with:
- Your Python version and OS
- The full error traceback
- Which data source or page the error occurred on

---

## Disclaimer

This tool is for **informational and educational purposes only**. It does not constitute financial advice. The buy/sell signals are generated by algorithmic rules and should not be the sole basis for investment decisions. Always consult a SEBI-registered investment advisor before making financial decisions.

Past performance data shown in this tool is sourced from third-party APIs and may be inaccurate or delayed. The maintainers of this project are not responsible for any financial losses.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Free to use, modify, and distribute. Attribution appreciated but not required.
