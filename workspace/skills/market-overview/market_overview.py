# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance", "rich"]
# ///
"""World Market Overview - fetches global index prices and displays a rich table."""

import sys
import yfinance as yf
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

WORLD_INDICES = {
    "US Markets": {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000",
        "^VIX": "VIX (Fear Index)",
    },
    "European Markets": {
        "^FTSE": "FTSE 100 (UK)",
        "^GDAXI": "DAX (Germany)",
        "^FCHI": "CAC 40 (France)",
        "^STOXX50E": "Euro Stoxx 50",
    },
    "Asian Markets": {
        "^N225": "Nikkei 225 (Japan)",
        "^HSI": "Hang Seng (HK)",
        "000001.SS": "Shanghai Composite",
        "^STI": "STI (Singapore)",
        "^BSESN": "Sensex (India)",
        "^NSEI": "Nifty 50 (India)",
        "^KS11": "KOSPI (Korea)",
        "^TWII": "TAIEX (Taiwan)",
    },
    "Commodities & Crypto": {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "Crude Oil (WTI)",
        "BZ=F": "Brent Crude",
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
    },
    "Currencies (vs USD)": {
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD",
        "USDJPY=X": "USD/JPY",
        "USDCNY=X": "USD/CNY",
        "USDINR=X": "USD/INR",
        "USDSGD=X": "USD/SGD",
    },
}


def get_change_style(change_pct: float) -> str:
    if change_pct > 0:
        return "bold green"
    elif change_pct < 0:
        return "bold red"
    return "white"


def get_change_arrow(change_pct: float) -> str:
    if change_pct > 1.5:
        return " [bold green]▲▲[/]"
    elif change_pct > 0:
        return " [green]▲[/]"
    elif change_pct < -1.5:
        return " [bold red]▼▼[/]"
    elif change_pct < 0:
        return " [red]▼[/]"
    return " [white]━[/]"


def spark_bar(change_pct: float, width: int = 10) -> str:
    """Create a visual bar showing magnitude of change."""
    clamped = max(min(change_pct, 5), -5)
    blocks = int(abs(clamped) / 5 * width)
    if blocks == 0 and change_pct != 0:
        blocks = 1
    if change_pct > 0:
        return f"[green]{'█' * blocks}{'░' * (width - blocks)}[/]"
    elif change_pct < 0:
        return f"[red]{'█' * blocks}{'░' * (width - blocks)}[/]"
    return f"[dim]{'░' * width}[/]"


def fetch_market_data():
    """Fetch all market data."""
    all_tickers = []
    for section in WORLD_INDICES.values():
        all_tickers.extend(section.keys())

    tickers_str = " ".join(all_tickers)
    data = yf.Tickers(tickers_str)
    results = {}

    for ticker_symbol in all_tickers:
        try:
            t = data.tickers[ticker_symbol]
            info = t.fast_info
            price = info.last_price
            prev_close = info.previous_close
            if price and prev_close and prev_close != 0:
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                results[ticker_symbol] = {
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "prev_close": prev_close,
                }
        except Exception:
            results[ticker_symbol] = None

    return results


def render_table(results: dict):
    """Render a rich table with market data."""
    console = Console()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    console.print()
    console.print(
        Panel(
            f"[bold white]World Markets Overview[/]  |  {now}",
            border_style="blue",
            expand=False,
        )
    )
    console.print()

    for section_name, tickers in WORLD_INDICES.items():
        table = Table(
            title=f"[bold cyan]{section_name}[/]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white on dark_blue",
            border_style="blue",
            pad_edge=True,
            expand=False,
        )

        table.add_column("Market", style="bold white", min_width=22)
        table.add_column("Price", justify="right", min_width=12)
        table.add_column("Change", justify="right", min_width=10)
        table.add_column("% Change", justify="right", min_width=10)
        table.add_column("Trend", justify="center", min_width=12)
        table.add_column("Visual", min_width=12)

        for symbol, name in tickers.items():
            data = results.get(symbol)
            if data is None:
                table.add_row(name, "[dim]N/A[/]", "-", "-", "-", "-")
                continue

            price_str = f"{data['price']:,.2f}"
            change_str = f"{data['change']:+,.2f}"
            pct_str = f"{data['change_pct']:+.2f}%"
            style = get_change_style(data["change_pct"])
            arrow = get_change_arrow(data["change_pct"])
            bar = spark_bar(data["change_pct"])

            table.add_row(
                name,
                f"[{style}]{price_str}[/]",
                f"[{style}]{change_str}[/]",
                f"[{style}]{pct_str}[/]",
                arrow,
                bar,
            )

        console.print(table)
        console.print()

    # Summary
    gainers = []
    losers = []
    for section_tickers in WORLD_INDICES.values():
        for symbol, name in section_tickers.items():
            data = results.get(symbol)
            if data:
                if data["change_pct"] > 0:
                    gainers.append((name, data["change_pct"]))
                elif data["change_pct"] < 0:
                    losers.append((name, data["change_pct"]))

    gainers.sort(key=lambda x: x[1], reverse=True)
    losers.sort(key=lambda x: x[1])

    summary_table = Table(
        title="[bold yellow]Top Movers[/]",
        box=box.ROUNDED,
        border_style="yellow",
        expand=False,
    )
    summary_table.add_column("Top Gainers", style="green", min_width=30)
    summary_table.add_column("Top Losers", style="red", min_width=30)

    for i in range(min(5, max(len(gainers), len(losers)))):
        g = f"{gainers[i][0]}: +{gainers[i][1]:.2f}%" if i < len(gainers) else ""
        l = f"{losers[i][0]}: {losers[i][1]:.2f}%" if i < len(losers) else ""
        summary_table.add_row(g, l)

    console.print(summary_table)
    console.print()


def main():
    console = Console()
    console.print("[bold blue]Fetching world market data...[/]")
    results = fetch_market_data()
    render_table(results)


if __name__ == "__main__":
    main()
