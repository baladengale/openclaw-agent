---
name: market-intel
description: Combined market overview and tech intelligence — world indices, portfolio tracking, stock analysis, RSS news aggregation, and keyword-scored newsletters in a single binary.
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["go"]
---

# Market Intel — Combined Market Overview & Tech Intelligence

Single Go binary that merges **market-overview** (Yahoo Finance) and **tech-intel** (RSS news) into one unified skill. Produces a combined HTML report with market status first, followed by scored news articles. Supports email delivery or local HTML generation.

## Quick Start

```bash
cd skills/market-intel
make build
./market-intel                  # both: market + news (default)
./market-intel -market          # market overview only
./market-intel -news            # tech-intel news only
./market-intel --no-email       # skip email, save HTML locally
```

## Mode Flags

| Flag          | Description                              |
|---------------|------------------------------------------|
| `-market`     | Run only market overview (replaces old `market-overview` binary) |
| `-news`       | Run only tech-intel news (replaces old `tech-intel` binary) |
| *(default)*   | Run both, combined into one HTML report  |

## Email Options

| Flag            | Description                                  |
|-----------------|----------------------------------------------|
| `--no-email`    | Skip email delivery, generate HTML file locally |
| `--email-only`  | Email only, suppress terminal output         |

## Market Flags

| Flag          | Description                                |
|---------------|--------------------------------------------|
| `-s`          | Summary view (key indices only)            |
| `-p`          | Portfolio view (personal holdings)         |
| `--no-movers` | Skip top movers section                    |
| `-t SYMBOL`   | Detailed stock info (e.g. `-t NVDA`)       |
| `-d SYMBOL`   | Dividend history                           |
| `-e SYMBOL`   | Earnings dates and EPS                     |
| `-f SYMBOL`   | Income statement (`-q` for quarterly)      |
| `-c SYMBOL`   | Cashflow statement (`-q` for quarterly)    |
| `-q`          | Quarterly data (with `-f` or `-c`)         |

## Usage Examples

```bash
# Full combined report — market data + news, emailed
./market-intel

# Market overview only, no email
./market-intel -market --no-email

# News digest only, emailed
./market-intel -news

# Portfolio view with news, save HTML locally
./market-intel -p --no-email

# Summary view, email only (no terminal output)
./market-intel -s --email-only

# Stock detail (bypasses combined flow)
./market-intel -t NVDA

# Quarterly financials
./market-intel -f TSLA -q
```

## Build

```bash
cd skills/market-intel
make build          # compile for current platform
make run            # build and run
make linux          # cross-compile for Linux amd64
make darwin         # cross-compile for macOS arm64
make install        # build and sync to OpenClaw workspace
```

## Environment Variables

Loaded from `~/.openclaw/.env` if present:

| Variable                  | Description                          | Default                                  |
|---------------------------|--------------------------------------|------------------------------------------|
| `GMAIL_USER`              | Gmail sender address                 | `dengalebr@gmail.com`                    |
| `GMAIL_APP_PASSWORD`      | Gmail app password (required for email) | —                                     |
| `MARKET_INTEL_RECIPIENTS` | Comma-separated recipient list       | Falls back to `MARKET_RECIPIENTS`        |

## Data Sources

**Market Data** — Yahoo Finance (v7 batch quotes, v8 chart data, v10 quote summary)

**News Feeds** — 12 RSS sources: TechCrunch, Ars Technica, The Verge, Hacker News, Wired, CNBC (Top + World), MarketWatch, Yahoo Finance, Reuters, BBC Business, NPR Business

## Markets Tracked

- **Indices:** S&P 500, Dow, NASDAQ, Russell 2000, VIX, FTSE 100, DAX, CAC 40, Euro Stoxx 50, Nikkei 225, Hang Seng, Shanghai, STI, Sensex, Nifty 50, KOSPI, TAIEX
- **Commodities & Crypto:** Gold, Silver, WTI, Brent, Bitcoin, Ethereum
- **Currencies:** USD/EUR, USD/GBP, USD/JPY, USD/CNY, USD/INR, USD/SGD, USD/MYR, SGD/INR, SGD/MYR
- **Portfolio:** Tesla, NVIDIA, Visa, Microsoft, Meta, Google, Amazon, AMD, Broadcom, Apple
- **Movers:** 15 US + 8 Singapore + 10 India stocks

## News Scoring

Articles scored by keyword relevance (AI, Semiconductor, Acquisition, FinTech, etc.), recency bonus (+3 for < 6h), and category bonus (+2 for Markets). Title matches get 2x weight. Top 25 selected.

## Output

- **Combined mode:** Single HTML with market tables + movers on top, followed by scored news articles below
- **Market-only:** Market tables, historical data, and top movers
- **News-only:** Ranked article list with scores, keywords, and source attribution
- **Local save:** HTML file in current directory when `--no-email` is used
