# PersonalFinanceBot

> A free, open-source, AI-powered portfolio dashboard for Indian investors — built with Streamlit, Zerodha Kite Connect, and free LLMs. Features a decision engine with risk analytics, actionable targets, rebalancing suggestions, and signal backtesting.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-red)
![Free](https://img.shields.io/badge/cost-100%25%20free-brightgreen)

---

## What Is This?

PersonalFinanceBot connects to your Zerodha portfolio via Kite Connect (or a CSV export), pulls in live market data from free APIs (yfinance, MFAPI.in, nsepython), and displays everything through a polished dark-themed Streamlit dashboard. Nine pages cover your portfolio, individual stock analysis, mutual funds, buy/sell signals, tax calculation, risk analysis, live positions & orders, account/margin details, and an AI chat advisor with 11 tools — all at zero cost.

---

## Table of Contents

1. [Features](#features)
2. [Screenshots](#screenshots)
3. [Prerequisites](#prerequisites)
4. [Installation — Step by Step](#installation--step-by-step)
5. [Setting Up Kite Connect (Zerodha)](#setting-up-kite-connect-zerodha)
6. [Setting Up an LLM (AI Advisor)](#setting-up-an-llm-ai-advisor)
7. [Environment Variables Reference](#environment-variables-reference)
8. [Daily Usage](#daily-usage)
9. [Using Without Kite (CSV Import)](#using-without-kite-csv-import)
10. [App Pages Guide](#app-pages-guide)
11. [Stopping the App](#stopping-the-app)
12. [Troubleshooting](#troubleshooting)
13. [Architecture](#architecture)
14. [Project Structure](#project-structure)
15. [Signal Methodology](#signal-methodology)
16. [Risk Metrics Methodology](#risk-metrics-methodology)
17. [Tax Calculator Methodology](#tax-calculator-methodology)
18. [Extending the Project](#extending-the-project)
19. [Contributing](#contributing)
20. [Disclaimer](#disclaimer)
21. [License](#license)

---

## Features

| Category | Highlights |
|---|---|
| **Home Dashboard** | Styled hero banner with live/offline status, portfolio snapshot (value, day P&L, overall P&L, XIRR), market pulse (Nifty 50 level, market status, available cash), top movers, quick links |
| **Portfolio** | Live holdings sync, P&L per stock, day change tracking, XIRR vs Nifty 50 benchmark, sector allocation pie, instrument-type breakdown |
| **Stock Analysis** | Candlestick chart with EMA/BBands overlays, RSI + MACD subplots, fundamental scorecard, 52-week range, analyst consensus, actionable targets (stop-loss, price target, S/R levels, position sizing), FinBERT news sentiment |
| **Mutual Funds** | NAV history chart, SIP XIRR calculator, fund search, category leaderboard (1Y/3Y/5Y), fund comparison overlay |
| **Signals** | -10 to +10 scored signal engine across 6 categories (momentum, trend, volume, fundamentals, sentiment, context), watchlist with actionable targets, portfolio rebalancing suggestions, signal accuracy backtesting |
| **Risk Analysis** | Portfolio beta, Sharpe ratio, annualized volatility, max drawdown, VaR 95%, concentration alerts (HHI, stock/sector limits), correlation heatmap, Nifty Sharpe comparison |
| **Tax Calculator** | LTCG/STCG classification (FY 2023-24 & 2024-25), LTCG exemption, tax-loss harvesting suggestions |
| **Positions & Orders** | Live open positions with unrealised/realised/M2M P&L, full order book with status filtering |
| **Account** | Profile details, funds overview (cash, collateral, intraday payin), margin utilization gauge, detailed breakdown |
| **AI Advisor** | Chat with your portfolio using Gemini, Groq, or Ollama — LLM fetches data on-demand via 11 tools (including risk metrics, targets, rebalancing), tool calls shown live in UI |
| **Rebalancing** | Equal-weight or signal-weighted target allocation, drift detection, specific Add/Trim/Hold actions with share counts |
| **Backtesting** | Signals auto-stored to SQLite, accuracy tracking per label (avg return, win rate), signal history per stock |
| **Dark Mode** | Full dark theme as default — dark backgrounds, styled cards, Plotly charts, and CSS all tuned for dark mode |
| **Grouped Navigation** | Sidebar pages organized into sections (Analysis, Tools, Account) with proper labels and icons |

---

## Screenshots

*Coming soon — run the app to see the dashboard in action.*

---

## Prerequisites

Before you begin, make sure you have:

| Requirement | Why | How to Get It |
|---|---|---|
| **Python 3.10+** | Runtime | [python.org](https://www.python.org/downloads/) or `brew install python` on macOS |
| **Git** | Clone the repo | [git-scm.com](https://git-scm.com/) or `brew install git` |
| **Zerodha account** (optional) | Live portfolio data via Kite Connect | [zerodha.com](https://zerodha.com/) — or skip and use CSV import |
| **At least one LLM API key** (optional) | AI Advisor chat feature | See [Setting Up an LLM](#setting-up-an-llm-ai-advisor) |

---

## Installation — Step by Step

### 1. Clone the repository

```bash
git clone https://github.com/Aarav-Nigam/Personal_Finance_Bot.git
cd Personal_Finance_Bot
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

You'll need to activate this virtual environment every time you open a new terminal session to use the bot.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note on FinBERT:** Installing `torch` and `transformers` pulls ~2 GB for the FinBERT sentiment model. If you don't need news sentiment analysis on the Stocks page, set `FINBERT_ENABLED=false` in your `.env` and you can skip those packages.

### 4. Create your `.env` file

```bash
cp env.template .env
```

Open `.env` in any text editor and fill in your keys. See [Environment Variables Reference](#environment-variables-reference) for details on each variable.

### 5. Start the app

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**. If it doesn't, open that URL in your browser manually.

---

## Setting Up Kite Connect (Zerodha)

Kite Connect gives you live holdings, positions, orders, margins, and profile data from your Zerodha account. It's free on the personal tier (no ₹2000/month charge — that's only for placing orders via API).

### One-time setup

1. Go to [kite.trade](https://kite.trade) and log in with your Zerodha credentials
2. Navigate to **My Apps** in the developer console
3. Click **Create New App** (choose "Connect" type)
4. Set the **Redirect URL** to: `http://127.0.0.1:8080`
5. Note down your **API Key** and **API Secret**
6. Add them to your `.env` file:
   ```
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   ```
7. **Whitelist your IP:** In the developer console, add your public IP address (find it at [whatismyip.com](https://whatismyip.com)). Kite rejects API calls from non-whitelisted IPs.

### Daily token refresh

Kite access tokens **expire every day at 6:00 AM IST**. Each trading day, before using the app with live data, run:

```bash
python scripts/kite_auth.py
```

This will:
1. Open the Kite login page in your browser
2. You log in with your Zerodha credentials and complete 2FA
3. After login, your browser redirects to `http://127.0.0.1:8080?request_token=...&status=success`
4. Copy the **full URL** from your browser's address bar
5. Paste it into the terminal when prompted
6. The script exchanges the token and saves `KITE_ACCESS_TOKEN` in your `.env` automatically

```
$ python scripts/kite_auth.py

Opening Kite login in browser...
https://kite.zerodha.com/connect/login?api_key=xxx&v=3

After logging in, paste the full redirect URL here: http://127.0.0.1:8080?request_token=abc123&status=success

Access token saved to .env (...abc123)
Token expires at 6:00 AM IST tomorrow. Re-run this script daily.
```

After refreshing the token, start (or restart) the Streamlit app and all Kite-dependent features will work.

---

## Setting Up an LLM (AI Advisor)

The AI Advisor page lets you chat about your portfolio with an LLM. The LLM uses tool-calling to fetch only the data it needs on demand (portfolio summary, fundamentals, signals, news, etc.) rather than loading everything upfront. You need at least one provider configured. All three are free.

### Option 1: Google Gemini (Recommended)

Best balance of quality and speed. Free tier is generous.

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key** and create one
3. Add to `.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   LLM_PROVIDER=gemini
   LLM_MODEL=gemini/gemini-2.5-flash
   ```

Free tier: 15 requests/minute, 1,500 requests/day.

### Option 2: Groq (Ultra-fast inference)

Groq runs Llama 3.3 70B on custom hardware — responses come back almost instantly.

1. Go to [console.groq.com](https://console.groq.com) and sign up
2. Create an API key
3. Add to `.env`:
   ```
   GROQ_API_KEY=your_key_here
   LLM_PROVIDER=groq
   LLM_MODEL=groq/llama-3.3-70b-versatile
   ```

Free tier: 6,000 requests/day, 500K tokens/day.

> **Note:** Groq may not work on corporate networks with SSL-intercepting proxies (e.g., Zscaler). If you get SSL or 403 errors, try from a home network.

### Option 3: Ollama (Fully offline, no API key)

Everything runs on your machine. No data leaves your computer.

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model:
   ```bash
   ollama pull qwen2.5       # Good all-round, 4.7 GB
   ollama pull mistral        # Mistral 7B, 4.1 GB — fast on CPU
   ollama pull llama3.3       # Llama 3.3 70B, 42 GB — needs 64 GB RAM
   ```
3. Ollama serves automatically after pulling. If not, start it:
   ```bash
   ollama serve
   ```
4. Add to `.env`:
   ```
   LLM_PROVIDER=ollama
   LLM_MODEL=ollama/qwen2.5
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Switching LLM providers at runtime

You don't need to restart the app to switch providers. On the **AI Advisor** page, use the provider dropdown in the sidebar to switch between Gemini, Groq, and Ollama mid-session. The `.env` values are just the defaults.

---

## Environment Variables Reference

Copy `env.template` to `.env` and fill in the values. Every variable has a sensible default or is optional.

| Variable | Required? | Default | Description |
|---|---|---|---|
| `KITE_API_KEY` | For live data | — | Zerodha developer console API key |
| `KITE_API_SECRET` | For live data | — | Zerodha developer console API secret |
| `KITE_ACCESS_TOKEN` | For live data | — | Auto-set by `scripts/kite_auth.py` daily |
| `GOOGLE_API_KEY` | For Gemini AI | — | Google AI Studio API key |
| `GROQ_API_KEY` | For Groq AI | — | Groq Cloud API key |
| `OLLAMA_BASE_URL` | For Ollama AI | `http://localhost:11434` | Ollama server URL |
| `LLM_PROVIDER` | No | `gemini` | Default AI provider: `gemini`, `groq`, or `ollama` |
| `LLM_MODEL` | No | `gemini/gemini-2.5-flash` | Default model in LiteLLM format |
| `FINBERT_ENABLED` | No | `true` | Set `false` to skip FinBERT sentiment (~500 MB download) |
| `CACHE_TTL_SECONDS` | No | `300` | How long to cache market data (seconds) |
| `CACHE_DIR` | No | `.cache` | Directory for JSON cache files |

---

## Daily Usage

Here's the workflow for using the bot each trading day:

### Morning startup

```bash
# 1. Open a terminal and navigate to the project
cd ~/Documents/Personal\ Projects/Personal_Finance_Bot

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Refresh your Kite access token (expires daily at 6 AM IST)
python scripts/kite_auth.py
# → Log in via browser, paste the redirect URL when prompted

# 4. Start the app
streamlit run app.py
# → Opens at http://localhost:8501
```

### What you can do

- **Home page** — Quick glance at portfolio value, day P&L, market status, top movers
- **Portfolio** — Deep dive into holdings, allocation, P&L breakdown, XIRR vs Nifty
- **Stocks** — Search any NSE ticker for chart + technicals + fundamentals + signal + actionable targets
- **Mutual Funds** — Look up any fund's NAV history, calculate SIP XIRR, compare funds
- **Signals** — Check your watchlist for buy/sell signals, get rebalance suggestions, track signal accuracy
- **Risk** — Portfolio-level risk metrics: beta, Sharpe ratio, drawdown, VaR, concentration alerts, correlation heatmap
- **Tax** — Enter trade lots to calculate LTCG/STCG tax, check harvesting opportunities
- **AI Advisor** — Ask questions about your portfolio in plain English (LLM fetches data via 11 tools)
- **Positions** — View today's open positions and full order book (Kite required)
- **Account** — Check available cash, margin utilization, profile details (Kite required)

### If the token expires mid-day

If you see an error like "Invalid access token" or "TokenException", your Kite token has expired or become invalid. Just run `python scripts/kite_auth.py` again in your terminal, then refresh the browser page (Ctrl+R / Cmd+R).

### Refreshing market data

Market data is cached for 5 minutes by default (configurable via `CACHE_TTL_SECONDS`). To force a refresh:
- **Signals page:** Click the "Refresh" button
- **Other pages:** Just wait for the cache to expire, or clear it manually by deleting the `.cache/` directory

---

## Using Without Kite (CSV Import)

You don't need a Zerodha account to use the bot. If Kite isn't connected, the app shows a CSV uploader in the sidebar.

### How to export your holdings CSV

**From Zerodha Console:**
1. Go to [console.zerodha.com](https://console.zerodha.com) → Holdings
2. Click the download/export button
3. Upload the downloaded CSV into the app

**From Groww:**
1. Go to Stocks → Holdings → Download statement
2. Upload the CSV

**From any broker:**
Create a CSV with these columns (column names are auto-detected):

```csv
Symbol,Quantity,Avg Price,LTP
RELIANCE,10,2450.00,2510.50
TCS,5,3800.00,3920.00
INFY,20,1400.00,1520.30
```

The parser is flexible — it recognizes common column name variations (`instrument`, `tradingsymbol`, `qty`, `avg_cost`, `average_price`, `last_price`, `ltp`, etc.).

### What works without Kite

| Feature | Works with CSV? |
|---|---|
| Portfolio overview (value, P&L, allocation) | Yes |
| Stock analysis (chart, technicals, fundamentals, targets) | Yes |
| Mutual Funds (NAV, SIP XIRR, leaderboard) | Yes |
| Signals (watchlist screener, rebalancing) | Yes |
| Risk Analysis (beta, Sharpe, drawdown, VaR) | Yes |
| Tax calculator | Yes |
| AI Advisor | Yes (uses CSV holdings as context) |
| Positions & Orders | No (needs live Kite connection) |
| Account & Funds | No (needs live Kite connection) |
| Day P&L on home page | No (needs Kite `day_change` field) |

---

## App Pages Guide

### Home Dashboard
The landing page. Shows:
- **Hero banner** with app name, greeting (personalized from Kite profile), and live/offline status indicator
- **Portfolio snapshot** — 4 cards: total value, day P&L, overall P&L with %, portfolio XIRR
- **Market pulse** — Nifty 50 level with daily change, market open/closed status, available cash
- **Top movers** — Your top 3 gainers and top 3 losers for the day
- **Quick links** — One-click navigation to all 8 pages

### 1. Portfolio
Full holdings breakdown:
- 5 metric cards: invested value, current value, P&L, holdings count, XIRR
- Nifty 50 comparison: your XIRR vs Nifty CAGR with alpha
- Holdings table with day change column (green/red coloring)
- Sector allocation pie + instrument type pie side by side
- Top gainers and losers bar charts

### 2. Stock Analysis
Search any NSE ticker (e.g., `RELIANCE`, `TCS`, `INFY`):
- **Candlestick chart** with toggleable overlays: EMA 20/50/200, Bollinger Bands
- **RSI subplot** (14-period) with overbought/oversold zones
- **MACD subplot** with signal line and histogram
- **Signal card** — -10 to +10 score with badge (Strong Buy / Buy / Hold / Sell / Strong Sell), sub-score breakdown chart
- **Actionable targets** — ATR-based stop-loss, analyst price target, pivot support/resistance levels, position sizing (2% risk model), risk/reward ratio
- **Fundamentals scorecard** — P/E, forward P/E, EV/EBITDA, P/B, ROE, ROCE, D/E, promoter holding %, EPS, revenue growth, PEG, FCF, margins
- **52-week range** progress bar
- **Analyst consensus** from Yahoo Finance
- **News & Sentiment** — Latest 10 headlines with FinBERT sentiment labels (in expander)

### 3. Mutual Funds
Three tabs:
- **Fund Search & NAV** — Search any AMFI fund, view NAV chart for 1M to 5Y, fund details, compare multiple funds by scheme code
- **SIP XIRR Calculator** — Enter installment dates + amounts + current value, get true XIRR (results cached across tab switches)
- **Category Leaderboard** — Top 10 funds by returns in any category (Large Cap, ELSS, Flexi Cap, etc.), results persist in session state

### 4. Signals Dashboard
Three tabs:
- **Watchlist** — Summary badges at top (count per signal label). Per-ticker expander: price, 1D change, score badge, sub-score chart, plain-English reason explanations, actionable targets (stop-loss, target, support/resistance, position size)
- **Portfolio Signals** — AI-powered analysis of all holdings with specific recommendations. Rebalancing section: choose equal-weight or signal-weighted strategy, get specific Add/Trim/Hold actions with share counts and reasons
- **Signal Accuracy** — Backtesting tab showing stored signal history. Per-label accuracy (count, avg return %, win rate). Per-symbol signal history in expanders. Signals auto-stored daily to SQLite for tracking.
- **Watchlist management** in sidebar: add/remove tickers (persists to `watchlist.json`)
- Signal results cached in session state — survive tab switches without re-fetching

### 5. Tax Calculator
Two tabs:
- **Tax Lots** — Enter each trade (symbol, buy date, sell date, prices, quantity). The app classifies as STCG/LTCG, calculates tax with exemption. STCG vs LTCG donut chart. Results cached in session state.
- **Tax-Loss Harvesting** — Scans your portfolio for unrealised losses that could offset gains. Shows potential tax savings.

Supports FY 2023-24 and FY 2024-25 with different rates.

### 6. AI Advisor
Tool-calling chat interface:
- **11 tools** the LLM can call on demand: portfolio summary, holdings P&L, allocation (by type or sector), market status, stock fundamentals, stock signal, news headlines, margin summary, **risk metrics**, **actionable targets**, **rebalance suggestions**
- **Live tool status** — each tool call shows as a status line (e.g., "Analyzing portfolio risk...") before the streamed response
- **Provider dropdown** in sidebar to switch between Gemini / Groq / Ollama
- **Connection status indicator** (green/red dot)
- Pre-built query buttons: rebalancing, what to sell, sector exposure, SIP recommendations, XIRR explanation, tax situation
- Ask "what are my risk metrics?", "should I rebalance?", "what's the stop-loss for RELIANCE?" — the LLM calls the right tools automatically
- Full conversation history for the session with tool call replay in expanders

### 7. Positions & Orders
Requires Kite connection. Two tabs:
- **Active Positions** — Unrealised P&L, Realised P&L, M2M as metric cards. Positions table with quantity, avg price, LTP. Toggle to show/hide closed positions.
- **Order Book** — Status badge counts (Complete, Rejected, Pending). Full orders table with filter-by-status dropdown.

### 8. Account & Funds
Requires Kite connection:
- **Profile** — Name, email, broker, enabled exchanges and products
- **Funds overview** — 4 cards: available cash, collateral, intraday payin, opening balance
- **Margin utilization gauge** — Visual gauge showing used vs available margin
- **Detailed breakdown** — Expandable section with all equity margin components

### 9. Risk Analysis
Portfolio-level risk dashboard (requires holdings):
- **Key metrics** — 4 cards: Portfolio Beta, Sharpe Ratio, Max Drawdown %, Annualized Volatility
- **VaR & Nifty comparison** — Daily VaR at 95% confidence, Nifty 50 Sharpe ratio, your Sharpe vs Nifty (outperforming/underperforming)
- **Concentration alerts** — HHI index, top-3 weight %, warnings if any stock >25% or sector >40%
- **Correlation heatmap** — Pairwise return correlation matrix with high-correlation pair detection (>0.75)

---

## Stopping the App

### Method 1: Keyboard shortcut (recommended)

In the terminal where Streamlit is running, press:

```
Ctrl + C
```

This stops the Streamlit server cleanly.

### Method 2: Close the terminal

Simply close the terminal window. The Streamlit process will be killed.

### Method 3: Kill by port (if the process is stuck)

If the app is running but you can't find the terminal:

```bash
# Find the process using port 8501
lsof -ti:8501 | xargs kill -9

# Or if running on a different port (e.g., 8502)
lsof -ti:8502 | xargs kill -9
```

### Deactivating the virtual environment

After stopping the app, deactivate the Python virtual environment:

```bash
deactivate
```

---

## Troubleshooting

### "Invalid access token" / "TokenException"

Your Kite token has expired (they expire daily at 6 AM IST). Run:
```bash
python scripts/kite_auth.py
```
Then refresh the browser page.

### "KITE_API_KEY and KITE_API_SECRET must be set"

You haven't configured Kite credentials in `.env`. Either:
- Add your Kite API key/secret (see [Setting Up Kite Connect](#setting-up-kite-connect-zerodha))
- Or skip Kite and use CSV import instead

### "Connect Kite to view positions" / "Connect Kite to view account details"

Positions and Account pages require a live Kite connection. They don't work with CSV import.

### Streamlit command not found

The virtual environment isn't activated. Run:
```bash
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows
```

### Port 8501 already in use

Another Streamlit instance is running. Either:
- Stop it with `Ctrl+C` in its terminal
- Or kill it: `lsof -ti:8501 | xargs kill -9`
- Or run on a different port: `streamlit run app.py --server.port 8502`

### SSL certificate errors (CERTIFICATE_VERIFY_FAILED)

If you're on a corporate network with an SSL-intercepting proxy (e.g., Zscaler):
- **MFAPI.in** — Already handled (the app uses `verify=False`)
- **Groq API** — May return 403 Forbidden. Use Gemini or Ollama instead, or try from a home network.
- **FinBERT download** — Pre-download the model manually:
  ```bash
  mkdir -p ~/.cache/huggingface/finbert
  cd ~/.cache/huggingface/finbert
  for f in config.json tokenizer_config.json vocab.txt special_tokens_map.json; do
    curl -sLk -o "$f" "https://huggingface.co/ProsusAI/finbert/resolve/main/$f"
  done
  curl -sLk -o pytorch_model.bin "https://huggingface.co/ProsusAI/finbert/resolve/main/pytorch_model.bin"
  ```

### Gemini API returns 429 / "quota exhausted"

The free tier has a 15 requests/minute limit. Wait a minute and try again. If all requests fail immediately, your daily quota (1,500 requests) may be exhausted — wait until the next day.

If the model ID returns a 404 ("model not found"), Gemini model names change periodically. Check [Google AI Studio](https://aistudio.google.com) for the current model ID and update `LLM_MODEL` in `.env`.

### Signals page is slow

The signal engine calls yfinance for each ticker in your watchlist. With 20+ tickers, the first load takes 30-60 seconds. Subsequent loads are faster thanks to caching (5 min TTL). Results are also cached in session state, so switching tabs won't trigger a re-fetch. Keep your watchlist focused on tickers you actually track.

### "Fewer than 250 rows — using EMA50 as EMA200 fallback"

This is normal for recently listed stocks. The app needs ~250 trading days of data for a proper 200-day EMA. For newer stocks, it uses the 50-day EMA as a proxy.

### nsepython errors

NSE updates its website frequently, breaking the unofficial nsepython scraper. The app automatically falls back to yfinance when nsepython fails. If you see warnings about NSE quotes, they're non-critical.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               Streamlit UI                                       │
│                        (Dark theme, grouped navigation)                          │
│                                                                                  │
│  Home │ Portfolio │ Stocks │ MF │ Signals │ Tax │ AI Advisor │ Positions │ Account│
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼──────────┐  ┌─────▼──────┐  ┌─────────▼──────────┐
    │    analytics/      │  │    llm/    │  │      data/         │
    │                    │  │            │  │                    │
    │  portfolio.py      │  │ client.py  │  │  kite_client.py    │
    │  account.py        │  │ advisor.py │  │  market_data.py    │
    │  technicals.py     │  │ prompts.py │  │  mf_client.py      │
    │  fundamentals.py   │  │ tools.py   │  │  nse_client.py     │
    │  signals.py        │  │ sentiment  │  │  cache.py          │
    │  mf_analytics.py   │  └─────┬──────┘  └─────────┬──────────┘
    │  tax.py            │        │                   │
    │  risk.py           │        │                   │
    │  targets.py        │        │                   │
    │  rebalance.py      │        │                   │
    │  backtest.py       │        │                   │
    └────────────────────┘        │                   │
                                  │                   │
    ┌─────────────────────────────┘                   │
    │                                                 │
    │   ┌──────────────────────┐       ┌──────────────▼──────────────────┐
    │   │  Free LLM Backends   │       │     External APIs (All Free)   │
    │   │                      │       │                                │
    │   │  Gemini 2.5 Flash    │       │  Kite Connect (Zerodha)        │
    │   │  Groq (Llama 3.3)    │       │    holdings, positions, orders │
    │   │  Ollama (local)      │       │    margins, profile            │
    │   │  FinBERT (local)     │       │                                │
    │   └──────────────────────┘       │  yfinance (Yahoo Finance)      │
    │                                  │    prices, OHLCV, fundamentals │
    │   ┌──────────────────────┐       │                                │
    │   │     ui/              │       │  MFAPI.in (AMFI data)          │
    │   │  theme.py (dark)     │       │    NAV history, fund list      │
    │   │  styles.py           │       │                                │
    │   │  charts.py           │       │  nsepython (NSE scraper)       │
    │   └──────────────────────┘       │    live quotes                 │
    │                                  └────────────────────────────────┘
    │   ┌──────────────────────┐
    │   │     utils/           │
    │   │  calculations.py     │
    │   │  formatters.py       │
    │   └──────────────────────┘
```

### Data flow rule

Pages (`pages/`) import from `analytics/`, `llm/`, and `utils/` — never directly from `data/`. The `data/` layer handles caching and API calls; `analytics/` provides business logic on top.

### AI Advisor tool-calling flow

```
User question → LLM receives tools list → LLM calls tools (e.g. get_stock_fundamentals)
→ Tool executes (calls analytics/data layers) → Result returned to LLM → LLM responds
```

The LLM can call up to 5 rounds of tools (11 available) before generating a final text response. Tool calls are displayed live in the UI as status captions.

---

## Project Structure

```
Personal_Finance_Bot/
├── app.py                          # Entry point — navigation controller + shared setup
├── home.py                         # Home dashboard (hero banner, portfolio snapshot, market pulse)
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Ruff config
├── env.template                    # Template for environment variables
├── .env                            # Your actual keys (git-ignored)
├── .streamlit/
│   └── config.toml                 # Streamlit dark theme config
├── config/
│   └── settings.py                 # Reads .env, exposes Settings dataclass
├── data/                           # External API wrappers + cache
│   ├── cache.py                    # TTL-based JSON file cache
│   ├── kite_client.py              # Zerodha Kite Connect SDK wrapper
│   ├── market_data.py              # yfinance wrapper (OHLCV, fundamentals)
│   ├── mf_client.py                # MFAPI.in wrapper (mutual fund data)
│   └── nse_client.py               # nsepython wrapper (live NSE quotes)
├── analytics/                      # Business logic layer
│   ├── account.py                  # Margins, profile, positions, orders
│   ├── portfolio.py                # P&L, XIRR, allocation, Nifty comparison
│   ├── technicals.py               # EMA, RSI, MACD, BBands, ATR, Pivot Points
│   ├── fundamentals.py             # P/E, ROE, PEG, FCF, margins, etc.
│   ├── signals.py                  # -10 to +10 signal scoring (6 categories)
│   ├── targets.py                  # Stop-loss, price targets, position sizing
│   ├── risk.py                     # Beta, Sharpe, drawdown, VaR, concentration
│   ├── rebalance.py                # Drift detection, rebalance suggestions
│   ├── backtest.py                 # Signal storage (SQLite) + accuracy tracking
│   ├── mf_analytics.py             # SIP XIRR, category returns, fund comparison
│   └── tax.py                      # LTCG/STCG classification + tax computation
├── llm/                            # AI features
│   ├── client.py                   # LiteLLM wrapper (Gemini, Groq, Ollama) + tool-call streaming
│   ├── advisor.py                  # Tool-calling advisor loop + legacy fallback
│   ├── prompts.py                  # System prompt templates + tool instructions
│   ├── tools.py                    # 11-tool registry (schemas, executor, display names)
│   └── sentiment.py                # FinBERT news sentiment analysis
├── ui/                             # Design system (dark mode)
│   ├── theme.py                    # Dark color palette, Plotly template
│   ├── styles.py                   # CSS injection, metric cards, badges
│   ├── charts.py                   # Themed Plotly chart factories
│   └── glossary.py                 # Tooltip definitions (62 terms) + signal explanations
├── utils/
│   ├── calculations.py             # XIRR, CAGR, annualised return
│   └── formatters.py               # fmt_inr(), fmt_pct(), fmt_cr()
├── pages/                          # Streamlit pages (loaded via st.navigation)
│   ├── 1_Portfolio.py
│   ├── 2_Stocks.py
│   ├── 3_Mutual_Funds.py
│   ├── 4_Signals.py
│   ├── 5_Tax.py
│   ├── 6_AI_Advisor.py
│   ├── 7_Positions.py
│   ├── 8_Account.py
│   └── 9_Risk.py
└── scripts/
    └── kite_auth.py                # Daily Kite OAuth token refresh
```

---

## Signal Methodology

The signal engine (`analytics/signals.py`) scores each stock from -10 to +10 across 6 weighted categories. Positive = bullish, negative = bearish.

### Categories & Weights

| Category | Weight | Data Sources |
|---|---|---|
| Momentum | 25% | RSI, MACD, Stochastic, MACD Histogram |
| Trend | 20% | EMA20/50/200, ADX, Bollinger Bands |
| Volume | 15% | OBV, MFI, volume spikes |
| Fundamentals | 20% | P/E, ROE, D/E, PEG, FCF yield, profit margins, earnings growth |
| Sentiment | 10% | News sentiment (FinBERT), analyst recs, institutional ownership, short interest |
| Context | 10% | 52-week position, distance from EMA200, analyst price targets, Nifty trend |

### Enriched Fundamental Signals (Phase 2)

| Condition | Score |
|---|---|
| PEG < 1 (undervalued on growth basis) | +2 |
| PEG > 3 (expensive relative to growth) | -1 |
| FCF yield > 5% (strong free cash flow) | +1 |
| FCF < 0 (burning cash) | -1 |
| Profit margins > 20% (high quality) | +1 |
| Earnings growth > 20% | +1 |
| Earnings growth < -10% (declining) | -1 |
| Institutional ownership > 60% | +1 |
| Short interest > 10% of float | -2 |
| Analyst target > 20% above CMP | +3 |
| Analyst target > 20% below CMP | -3 |

### Signal Labels

| Score Range | Label |
|---|---|
| +7 to +10 | Strong Buy |
| +3 to +6 | Buy |
| -2 to +2 | Hold |
| -6 to -3 | Sell |
| -10 to -7 | Strong Sell |

### Actionable Targets (per stock)

When a signal is computed, the engine also generates:
- **Stop-loss** — Current price minus 2× ATR(14)
- **Target price** — Analyst consensus mean target
- **Support/Resistance** — Classic pivot points (S1, S2, R1, R2)
- **Position size** — Based on 2% portfolio risk model: `(2% × portfolio) / (entry - stop)`
- **Risk/reward ratio** — `(target - entry) / (entry - stop)`

### Signal Backtesting

Signals are automatically stored to a local SQLite database (`.cache/signals.db`) each time they're computed. The accuracy tab shows:
- Per-label performance: count, average return %, win rate (after N days)
- Per-symbol signal history timeline
- Data accumulates over time for increasingly reliable accuracy metrics

> These signals are informational tools, not financial advice. Always do your own research.

---

## Risk Metrics Methodology

The Risk Analysis page (`analytics/risk.py`) computes portfolio-level risk metrics from daily returns (1 year of history via yfinance).

| Metric | Formula | Interpretation |
|---|---|---|
| **Portfolio Beta** | Weighted average of per-stock betas from fundamentals | >1 = more volatile than market |
| **Annualized Volatility** | `std(daily returns) × √252` | Lower is more stable |
| **Sharpe Ratio** | `(annualized return - 6.5%) / annualized volatility` | >1 good, >2 excellent |
| **Max Drawdown** | Largest peak-to-trough decline in cumulative returns | Worst-case loss experience |
| **VaR 95%** | 5th percentile of daily portfolio returns | Max daily loss 95% of the time |
| **HHI** | `Σ(weight²) × 10,000` | <1500 diversified, >2500 concentrated |

### Concentration Alerts

- Single stock > 25% of portfolio → warning
- Single sector > 40% of portfolio → warning
- High correlation pairs (>0.75) flagged in heatmap

### Rebalancing Engine

Two strategies available:
- **Equal weight** — Target 1/N allocation per stock
- **Signal weighted** — Allocate more to higher-signal stocks (shifted scores normalized to weights)

Drift > 3% triggers a suggestion. Actions combine drift direction with signal direction:
- Overweight + Sell signal → "Trim X shares"
- Underweight + Buy signal → "Add X shares"
- Overweight + Buy signal → "Hold (signal positive)"

---

## Tax Calculator Methodology

### Equity and Equity Mutual Funds

| Holding Period | FY 2024-25 | FY 2023-24 |
|---|---|---|
| STCG (up to 1 year) | 20% flat | 15% flat |
| LTCG (over 1 year) | 12.5% above ₹1,25,000 | 10% above ₹1,00,000 |

### Debt Mutual Funds (post-April 2023)

All gains taxed at income slab rate. No indexation benefit.

### Tax-Loss Harvesting

The tool scans unrealised losses >= ₹500 in your holdings and shows how much tax you could save by booking those losses before the financial year ends.

---

## Extending the Project

### Adding a new data source

1. Create `data/your_source.py`
2. Wrap all HTTP calls with `cache.get()` / `cache.set()`
3. Import from an `analytics/` module (not directly from pages)
4. Add any new API key to `env.template` and `config/settings.py`

### Adding a new page

1. Create `pages/N_PageName.py` (the number controls sidebar order)
2. Import from `analytics/`, `llm/`, or `utils/`
3. Use `ui.styles.inject_css()` for consistent styling
4. Register the page in `app.py` via `st.Page()` inside `st.navigation()`

### Adding a new LLM provider

LiteLLM supports 100+ providers. To add one:
1. Set the API key in `.env` and `config/settings.py`
2. Add the provider to `SUPPORTED_PROVIDERS` in `llm/client.py`
3. Add the provider name to the dropdown in `pages/6_AI_Advisor.py`

### Adding a new AI Advisor tool

1. Add the tool schema to `TOOL_SCHEMAS` in `llm/tools.py`
2. Add a display name template to `TOOL_DISPLAY_NAMES`
3. Add the execution case to `execute_tool()`
4. If the tool needs `holdings_df`, add its name to `PORTFOLIO_TOOLS`

---

## Contributing

Contributions are welcome!

1. Fork the repo and create a feature branch (`git checkout -b feature/my-feature`)
2. Keep commits small and focused
3. Run `ruff check . && ruff format .` before committing
4. Open a pull request with a clear description

### Reporting issues

Open a GitHub Issue with:
- Python version and OS
- Full error traceback
- Which page the error occurred on

---

## Disclaimer

This tool is for **informational and educational purposes only**. It does not constitute financial advice. The buy/sell signals are generated by algorithmic rules and should not be the sole basis for investment decisions. Always consult a SEBI-registered investment advisor before making financial decisions.

Past performance data is sourced from third-party APIs and may be inaccurate or delayed. The maintainers are not responsible for any financial losses.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Free to use, modify, and distribute. Attribution appreciated but not required.
