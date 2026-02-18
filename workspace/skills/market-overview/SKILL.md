---
name: market-overview
description: World market overview with graphical tables showing global indices, commodities, crypto, forex, portfolio tracking, stock details, dividends, earnings, and financials.
metadata:
  openclaw:
    emoji: "🌍"
    requires:
      bins: ["uv"]
---

# Market Overview

Comprehensive world market overview with rich graphical tables, portfolio tracking, and individual stock analysis.

## When to Activate

Activate when the user asks about:
- World markets, global markets, market overview
- Stock market today, market prices
- How are markets doing
- Index prices (S&P 500, Dow, NASDAQ, Nikkei, Sensex, etc.)
- Portfolio performance, my stocks
- Stock details, dividends, earnings, financials, cashflow
- Top movers, gainers, losers

## Script Location

```
skills/market-overview/market_overview.py
```

## Views

### Default (Detail View) — All world markets
```bash
uv run --script skills/market-overview/market_overview.py
```

### Summary — Key indices only
```bash
uv run --script skills/market-overview/market_overview.py -s
```

### Portfolio — Personal stock holdings
```bash
uv run --script skills/market-overview/market_overview.py -p
```

### Skip stock movers section
```bash
uv run --script skills/market-overview/market_overview.py --no-movers
```

## Stock Analysis

### Detailed stock info (price, valuation, analyst targets)
```bash
uv run --script skills/market-overview/market_overview.py -t TSLA
uv run --script skills/market-overview/market_overview.py --stock NVDA
```

### Dividend history
```bash
uv run --script skills/market-overview/market_overview.py -d AAPL
uv run --script skills/market-overview/market_overview.py --dividends V
```

### Earnings dates and EPS
```bash
uv run --script skills/market-overview/market_overview.py -e TSLA
uv run --script skills/market-overview/market_overview.py --earnings GOOGL
```

### Income statement (yearly / quarterly)
```bash
uv run --script skills/market-overview/market_overview.py -f NVDA
uv run --script skills/market-overview/market_overview.py --financials NVDA -q
```

### Cashflow statement (yearly / quarterly)
```bash
uv run --script skills/market-overview/market_overview.py -c MSFT
uv run --script skills/market-overview/market_overview.py --cashflow MSFT -q
```

## What Each View Shows

### Market Views (default / summary / portfolio)
- Current price with color-coded change indicators
- 1-day change with trend arrows
- Historical changes: 1W, 1M, 3M, 6M, 1Y, 2Y, 5Y
- Top gainers and losers summary
- Regional stock movers (US, Singapore, India)

### Detail View Markets
- **US Markets**: S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX
- **European Markets**: FTSE 100, DAX, CAC 40, Euro Stoxx 50
- **Asian Markets**: Nikkei, Hang Seng, Shanghai, STI, Sensex, Nifty, KOSPI, TAIEX
- **Commodities & Crypto**: Gold, Silver, Crude Oil, Brent, Bitcoin, Ethereum
- **Currencies**: USD/EUR, USD/GBP, USD/JPY, USD/CNY, USD/INR, USD/SGD, USD/MYR, SGD/INR, SGD/MYR

### Portfolio Stocks
Tesla, NVIDIA, Visa, Microsoft, Meta, Google, Amazon, AMD, Broadcom, Apple

### Stock Detail (`-t`)
- Price info: current, open, day range, 52-week range, volume
- Company info: sector, industry, market cap, enterprise value
- Valuation: P/E (trailing & forward), PEG, P/B, P/S, EPS, beta, margins
- Dividends: rate, yield
- Analyst: target prices (low/mean/high), recommendation, upside/downside

### Dividends (`-d`)
- Annual dividend rate and yield
- Total dividend history
- Last 12 payment dates and amounts

### Earnings (`-e`)
- Upcoming and past earnings dates
- EPS estimate vs reported
- Surprise percentage

### Financials (`-f`)
- Total Revenue, Gross Profit, Operating Income, Net Income
- EBITDA, Basic EPS, Diluted EPS
- Up to 4 periods (yearly or quarterly with `-q`)

### Cashflow (`-c`)
- Operating, Investing, Financing cash flows
- Free Cash Flow, Capital Expenditure, End Cash Position
- Up to 4 periods (yearly or quarterly with `-q`)

## Daily Email Report

A daily HTML email with Market Summary + Portfolio is sent at 8:00 AM SGT to configured recipients via:
```
skills/market-overview/daily_email.py
```

Scheduled via OpenClaw cron (`openclaw cron list` to verify).

## CLI Reference

```
usage: market_overview.py [-h] [-s] [-p] [--no-movers] [-t SYMBOL] [-d SYMBOL]
                          [-e SYMBOL] [-f SYMBOL] [-c SYMBOL] [-q]

Options:
  -h, --help            Show help
  -s, --summary         Summary view (key indices only)
  -p, --portfolio       Portfolio view (your stocks)
  --no-movers           Skip stock movers section
  -t, --stock SYMBOL    Detailed stock info
  -d, --dividends SYMBOL  Dividend history
  -e, --earnings SYMBOL   Earnings dates and EPS
  -f, --financials SYMBOL Income statement
  -c, --cashflow SYMBOL   Cashflow statement
  -q, --quarterly       Quarterly data (for -f and -c)
```
