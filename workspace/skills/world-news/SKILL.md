---
name: world-news
description: Top world news aggregator across Stock Market, Technology, Science, and General categories with short summaries and deep-dive option.
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: ["uv"]
---

# World News

Get top news headlines from around the world across multiple categories.

## When to Activate

Activate when the user asks about:
- World news, top news, latest news, headlines
- Tech news, technology news
- Science news, scientific discoveries
- Stock market news, financial news, business news
- What's happening in the world

## Usage

Show top headlines (default 5 per category):
```bash
uv run --script skills/world-news/world_news.py
```

Show more headlines per category:
```bash
uv run --script skills/world-news/world_news.py --count 10
```

Show only specific categories:
```bash
uv run --script skills/world-news/world_news.py --category technology
uv run --script skills/world-news/world_news.py --category stock-market
uv run --script skills/world-news/world_news.py --category science
uv run --script skills/world-news/world_news.py --category general
```

Deep dive into a specific article (by number shown in the table):
```bash
uv run --script skills/world-news/world_news.py --detail 3
```

## What It Shows

- **Stock Market**: Reuters Business, CNBC, MarketWatch, Bloomberg
- **Technology**: TechCrunch, Ars Technica, The Verge, Hacker News
- **Science**: Nature, Science Daily, Phys.org, New Scientist
- **General**: BBC World, Reuters, AP News, Al Jazeera

Each entry shows: headline, source, time ago, and a short summary.

Deep dive mode fetches the full article text and provides an extended summary.
