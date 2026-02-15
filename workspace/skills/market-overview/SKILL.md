---
name: market-overview
description: World market overview with graphical tables showing global indices, commodities, crypto, and forex prices with visual trend indicators.
metadata:
  openclaw:
    emoji: "🌍"
    requires:
      bins: ["uv"]
---

# Market Overview

Get a comprehensive world market overview with rich graphical tables.

## When to Activate

Activate when the user asks about:
- World markets, global markets, market overview
- Stock market today, market prices
- How are markets doing
- Index prices (S&P 500, Dow, NASDAQ, Nikkei, Sensex, etc.)

## Usage

Run the market overview script:
```bash
uv run --script skills/market-overview/market_overview.py
```

## What It Shows

- **US Markets**: S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX
- **European Markets**: FTSE 100, DAX, CAC 40, Euro Stoxx 50
- **Asian Markets**: Nikkei, Hang Seng, Shanghai, STI, Sensex, Nifty, KOSPI, TAIEX
- **Commodities & Crypto**: Gold, Silver, Crude Oil, Brent, Bitcoin, Ethereum
- **Currencies**: EUR/USD, GBP/USD, USD/JPY, USD/CNY, USD/INR, USD/SGD
- **Top Movers**: Biggest gainers and losers summary

Each entry shows: current price, change, % change, trend arrow, and visual bar chart.

## Combine with stock-market-pro

For detailed analysis of individual stocks, use the `stock-market-pro` skill commands:
- `uv run --script scripts/yf price [TICKER]` - Get individual stock price
- `uv run --script scripts/yf pro [TICKER] [PERIOD]` - Generate candlestick chart
