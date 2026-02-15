# /// script
# requires-python = ">=3.11"
# dependencies = ["feedparser", "rich", "httpx", "trafilatura"]
# ///
"""World News Aggregator - fetches top news from RSS feeds across categories."""

import argparse
import sys
import time
from datetime import datetime, timezone

import feedparser
import httpx
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# RSS feed sources organised by category
# ---------------------------------------------------------------------------
NEWS_SOURCES: dict[str, dict[str, str]] = {
    "Stock Market": {
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
        "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    },
    "Technology": {
        "TechCrunch": "https://techcrunch.com/feed/",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Hacker News": "https://hnrss.org/frontpage",
    },
    "Science": {
        "Nature": "https://www.nature.com/nature.rss",
        "Science Daily": "https://www.sciencedaily.com/rss/all.xml",
        "Phys.org": "https://phys.org/rss-feed/",
        "New Scientist": "https://www.newscientist.com/section/news/feed/",
    },
    "General": {
        "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "Reuters Top": "https://feeds.reuters.com/reuters/topNews",
        "AP News": "https://rsshub.app/apnews/topics/apf-topnews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    },
}

# Category aliases for CLI --category flag
CATEGORY_ALIASES: dict[str, str] = {
    "stock-market": "Stock Market",
    "stock": "Stock Market",
    "market": "Stock Market",
    "finance": "Stock Market",
    "business": "Stock Market",
    "technology": "Technology",
    "tech": "Technology",
    "science": "Science",
    "general": "General",
    "world": "General",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def time_ago(published_parsed) -> str:
    """Return a human-friendly 'time ago' string."""
    if not published_parsed:
        return "recently"
    try:
        pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - pub_dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        elif seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        else:
            d = seconds // 86400
            return f"{d}d ago"
    except Exception:
        return "recently"


def clean_summary(raw: str, max_len: int = 120) -> str:
    """Strip HTML tags and truncate to max_len."""
    import re

    text = re.sub(r"<[^>]+>", "", raw or "")
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 1].rsplit(" ", 1)[0] + "..."
    return text


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def fetch_feeds(
    categories: list[str] | None = None,
    max_per_source: int = 5,
) -> dict[str, list[dict]]:
    """Fetch RSS feeds and return structured article data per category."""

    selected = {k: v for k, v in NEWS_SOURCES.items() if categories is None or k in categories}
    results: dict[str, list[dict]] = {}
    client = httpx.Client(timeout=10, follow_redirects=True)

    for category, sources in selected.items():
        articles: list[dict] = []
        for source_name, url in sources.items():
            try:
                resp = client.get(url)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:max_per_source]:
                    articles.append(
                        {
                            "title": entry.get("title", "No title"),
                            "link": entry.get("link", ""),
                            "summary": clean_summary(entry.get("summary", entry.get("description", ""))),
                            "source": source_name,
                            "published": entry.get("published_parsed"),
                            "time_ago": time_ago(entry.get("published_parsed")),
                        }
                    )
            except Exception:
                # Skip sources that fail — don't break the whole run
                pass

        # Sort by recency (most recent first), deduplicate by title
        seen_titles: set[str] = set()
        unique: list[dict] = []
        for a in articles:
            title_lower = a["title"].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique.append(a)

        # Sort: items with parsed times first (newest first), then "recently" items
        def sort_key(a):
            if a["published"]:
                return (0, -time.mktime(a["published"]))
            return (1, 0)

        unique.sort(key=sort_key)
        results[category] = unique

    client.close()
    return results


# ---------------------------------------------------------------------------
# Deep-dive: fetch full article text
# ---------------------------------------------------------------------------
def deep_dive(article: dict) -> str:
    """Fetch the full article and extract readable text."""
    import trafilatura

    url = article["link"]
    if not url:
        return "No URL available for this article."
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return f"Could not fetch article. Visit directly: {url}"
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not text:
            return f"Could not extract article text. Visit directly: {url}"
        return text
    except Exception as e:
        return f"Error fetching article: {e}\nVisit directly: {url}"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render_headlines(all_news: dict[str, list[dict]], max_per_category: int = 5):
    """Render rich tables for each news category."""
    console = Console()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    console.print()
    console.print(
        Panel(
            f"[bold white]World News Headlines[/]  |  {now}",
            border_style="bright_magenta",
            expand=False,
        )
    )
    console.print()

    global_index = 1

    for category, articles in all_news.items():
        table = Table(
            title=f"[bold cyan]{category}[/]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white on dark_blue",
            border_style="blue",
            pad_edge=True,
            expand=False,
        )

        table.add_column("#", style="bold yellow", min_width=3, justify="right")
        table.add_column("Headline", style="bold white", min_width=40, max_width=60)
        table.add_column("Source", style="cyan", min_width=16)
        table.add_column("When", justify="right", min_width=8)
        table.add_column("Summary", style="dim white", min_width=30, max_width=50)

        display_articles = articles[:max_per_category]
        for article in display_articles:
            title = article["title"]
            if len(title) > 60:
                title = title[:57] + "..."

            table.add_row(
                str(global_index),
                title,
                article["source"],
                article["time_ago"],
                article["summary"],
            )
            global_index += 1

        console.print(table)
        console.print()

    # Tip
    console.print(
        Panel(
            "[bold green]Tip:[/] Deep-dive into any article:\n"
            "  uv run --script skills/world-news/world_news.py --detail [bold yellow]<number>[/]",
            border_style="green",
            expand=False,
        )
    )
    console.print()


def render_detail(all_news: dict[str, list[dict]], detail_index: int, max_per_category: int = 5):
    """Render a detailed view of a specific article."""
    console = Console()

    # Flatten articles in display order
    flat: list[dict] = []
    for articles in all_news.values():
        flat.extend(articles[:max_per_category])

    if detail_index < 1 or detail_index > len(flat):
        console.print(f"[bold red]Invalid article number {detail_index}. Choose between 1 and {len(flat)}.[/]")
        return

    article = flat[detail_index - 1]

    console.print()
    console.print(
        Panel(
            f"[bold white]{article['title']}[/]\n"
            f"[cyan]{article['source']}[/]  |  {article['time_ago']}  |  [link={article['link']}]{article['link']}[/link]",
            title="[bold yellow]Deep Dive[/]",
            border_style="yellow",
            expand=False,
        )
    )
    console.print()
    console.print("[dim]Fetching full article...[/]")

    full_text = deep_dive(article)

    console.print()
    console.print(
        Panel(
            full_text,
            title="[bold white]Full Article[/]",
            border_style="bright_magenta",
            expand=True,
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="World News Headlines")
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter by category: stock-market, technology, science, general",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of headlines per category (default: 5)",
    )
    parser.add_argument(
        "--detail",
        type=int,
        default=None,
        help="Deep-dive into article by its number",
    )
    args = parser.parse_args()

    console = Console()

    # Resolve category
    categories = None
    if args.category:
        resolved = CATEGORY_ALIASES.get(args.category.lower())
        if not resolved:
            console.print(f"[bold red]Unknown category '{args.category}'[/]")
            console.print(f"[dim]Available: {', '.join(CATEGORY_ALIASES.keys())}[/]")
            sys.exit(1)
        categories = [resolved]

    console.print("[bold bright_magenta]Fetching world news...[/]")
    all_news = fetch_feeds(categories=categories, max_per_source=args.count)

    if args.detail is not None:
        render_detail(all_news, args.detail, max_per_category=args.count)
    else:
        render_headlines(all_news, max_per_category=args.count)


if __name__ == "__main__":
    main()
