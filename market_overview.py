# /// script
# requires-python = ">=3.11"
# dependencies = ["yfinance", "rich", "lxml"]
# ///
"""World Market Overview - fetches global index prices and displays a rich table."""

import argparse
import sys
import time
import pandas as pd
import yfinance as yf
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# =============================================================================
# VIEW CONFIGURATIONS
# =============================================================================

# DETAIL VIEW - All markets (default)
DETAIL_VIEW = {
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
    "Currencies": {
        "EURUSD=X": "USD/EUR",
        "GBPUSD=X": "USD/GBP",
        "USDJPY=X": "USD/JPY",
        "USDCNY=X": "USD/CNY",
        "USDINR=X": "USD/INR",
        "USDSGD=X": "USD/SGD",
        "USDMYR=X": "USD/MYR",
        "SGD/INR": "SGD/INR",
        "SGD/MYR": "SGD/MYR",
    },
}

# SUMMARY VIEW - Selected markets only
SUMMARY_VIEW = {
    "Key Indices": {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^HSI": "Hang Seng (HK)",
        "^STI": "STI (Singapore)",
        "^BSESN": "Sensex (India)",
        "^NSEI": "Nifty 50 (India)",
    },
    "Commodities & Crypto": {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "Crude Oil (WTI)",
        "BZ=F": "Brent Crude",
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
    },
    "Currencies": {
        "USDINR=X": "USD/INR",
        "USDSGD=X": "USD/SGD",
        "SGD/INR": "SGD/INR",
        "SGD/MYR": "SGD/MYR",
    },
}

# PORTFOLIO VIEW - Personal stock holdings
PORTFOLIO_VIEW = {
    "My Portfolio": {
        "TSLA": "Tesla",
        "NVDA": "NVIDIA",
        "V": "Visa",
        "MSFT": "Microsoft",
        "META": "Meta",
        "GOOGL": "Google",
        "AMZN": "Amazon",
        "AMD": "AMD",
        "AVGO": "Broadcom",
        "AAPL": "Apple",
    },
}

# TOP MOVERS - Individual stocks for tracking (used in all views)
TOP_MOVERS_STOCKS = {
    "US Stocks": {
        "TSLA": "Tesla",
        "NVDA": "NVIDIA",
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Google",
        "AMZN": "Amazon",
        "META": "Meta",
        "AMD": "AMD",
        "AVGO": "Broadcom",
        "V": "Visa",
        "JPM": "JPMorgan",
        "BAC": "Bank of America",
        "WMT": "Walmart",
        "DIS": "Disney",
        "NFLX": "Netflix",
    },
    "Singapore Stocks": {
        "D05.SI": "DBS Group",
        "O39.SI": "OCBC Bank",
        "U11.SI": "UOB",
        "Z74.SI": "Singtel",
        "C6L.SI": "Singapore Airlines",
        "C38U.SI": "CapitaLand",
        "G13.SI": "Genting Singapore",
        "S58.SI": "SATS",
    },
    "India Stocks": {
        "RELIANCE.NS": "Reliance",
        "TCS.NS": "TCS",
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "HINDUNILVR.NS": "Hindustan Unilever",
        "ITC.NS": "ITC",
        "SBIN.NS": "SBI",
        "BHARTIARTL.NS": "Bharti Airtel",
        "WIPRO.NS": "Wipro",
    },
}

# Tickers that need price inversion for display (show as USD/X instead of X/USD)
INVERT_TICKERS = {"EURUSD=X", "GBPUSD=X"}

# Cross rates to calculate (name: (base_ticker, quote_ticker))
# SGD/INR = USDINR / USDSGD, SGD/MYR = USDMYR / USDSGD
CROSS_RATES = {
    "SGD/INR": ("USDINR=X", "USDSGD=X"),
    "SGD/MYR": ("USDMYR=X", "USDSGD=X"),
}

# Historical periods (trading days threshold, label)
# ~252 trading days/year, using slightly lower thresholds for flexibility
HISTORICAL_PERIODS = [
    (5, "1W"),
    (21, "1M"),
    (63, "3M"),
    (126, "6M"),
    (252, "1Y"),
    (504, "2Y"),
    (1260, "5Y"),
]

# Extract labels for column headers
PERIOD_LABELS = [label for _, label in HISTORICAL_PERIODS]


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


def fetch_with_retry(tickers_list, period="10y", retries=MAX_RETRIES):
    """Fetch data with retry logic for rate limits."""
    console = Console()
    for attempt in range(retries):
        try:
            # Use yf.download for batch fetching - single API call for all tickers
            data = yf.download(
                tickers=tickers_list,
                period=period,
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            return data
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                if attempt < retries - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    console.print(f"[yellow]Rate limited. Waiting {wait_time}s before retry...[/]")
                    time.sleep(wait_time)
                else:
                    console.print(f"[red]Rate limit exceeded after {retries} retries[/]")
                    return None
            else:
                console.print(f"[red]Error fetching data: {e}[/]")
                return None
    return None


def fetch_market_data(view_config, include_top_movers=True):
    """Fetch all market data using a single 5y batch request to avoid rate limiting."""
    console = Console()

    # Collect all tickers from the view
    all_tickers = set()
    for section in view_config.values():
        all_tickers.update(section.keys())

    # Also fetch tickers needed for cross rates (if currencies are in view)
    for base, quote in CROSS_RATES.values():
        all_tickers.add(base)
        all_tickers.add(quote)

    # Add top movers stocks if enabled
    if include_top_movers:
        for region_stocks in TOP_MOVERS_STOCKS.values():
            all_tickers.update(region_stocks.keys())

    # Remove cross rate names (they're not real tickers)
    all_tickers = sorted([t for t in all_tickers if t not in CROSS_RATES])

    console.print(f"[dim]Fetching 10y data for {len(all_tickers)} tickers (single batch)...[/]")

    # Single batch fetch for 5 years of data
    data = fetch_with_retry(all_tickers, period="10y")
    if data is None or data.empty:
        console.print("[red]Failed to fetch market data[/]")
        return {}

    results = {}
    raw_data = {}  # Store raw data for cross rate calculations

    # Process each ticker
    for ticker_symbol in all_tickers:
        try:
            # Get close prices for this ticker
            if len(all_tickers) == 1:
                closes = data["Close"].dropna()
            else:
                if ticker_symbol not in data.columns.get_level_values(0):
                    continue
                closes = data[ticker_symbol]["Close"].dropna()

            if len(closes) < 2:
                continue

            price = closes.iloc[-1]
            prev_close = closes.iloc[-2]

            if not price or price == 0:
                continue

            # Store raw data for cross rates
            raw_data[ticker_symbol] = {
                "price": price,
                "prev_close": prev_close,
                "closes": closes,
            }

            # Handle inverted tickers (for display as USD/EUR instead of EUR/USD)
            invert = ticker_symbol in INVERT_TICKERS
            display_price = 1.0 / price if invert else price
            display_prev = 1.0 / prev_close if invert else prev_close

            change_pct = ((display_price - display_prev) / display_prev) * 100

            # Calculate historical changes using trading day indices
            historical_changes = {}
            num_closes = len(closes)
            for trading_days, label in HISTORICAL_PERIODS:
                if num_closes > trading_days:
                    historical_price = closes.iloc[-(trading_days + 1)]
                    if invert:
                        historical_price = 1.0 / historical_price
                    if historical_price and historical_price != 0:
                        historical_changes[label] = ((display_price - historical_price) / historical_price) * 100

            # Fetch additional info (52 week range, P/E, analyst targets)
            extra_info = {}
            try:
                ticker_obj = yf.Ticker(ticker_symbol)
                info = ticker_obj.info
                extra_info = {
                    "week52_high": info.get("fiftyTwoWeekHigh"),
                    "week52_low": info.get("fiftyTwoWeekLow"),
                    "pe_trailing": info.get("trailingPE"),
                    "pe_forward": info.get("forwardPE"),
                    "target_high": info.get("targetHighPrice"),
                    "target_mean": info.get("targetMeanPrice"),
                    "target_low": info.get("targetLowPrice"),
                    "recommendation": info.get("recommendationKey", "").upper() if info.get("recommendationKey") else None,
                }
            except Exception:
                pass

            results[ticker_symbol] = {
                "price": display_price,
                "change_pct": change_pct,
                "historical": historical_changes,
                **extra_info,
            }
        except Exception:
            pass

    # Calculate cross rates
    for name, (base_ticker, quote_ticker) in CROSS_RATES.items():
        if base_ticker in raw_data and quote_ticker in raw_data:
            try:
                base = raw_data[base_ticker]
                quote = raw_data[quote_ticker]

                # Cross rate = base / quote (e.g., SGD/INR = USDINR / USDSGD)
                price = base["price"] / quote["price"]
                prev_price = base["prev_close"] / quote["prev_close"]
                change_pct = ((price - prev_price) / prev_price) * 100

                # Calculate historical cross rates
                historical_changes = {}
                base_closes = base["closes"]
                quote_closes = quote["closes"]
                num_closes = min(len(base_closes), len(quote_closes))

                for trading_days, label in HISTORICAL_PERIODS:
                    if num_closes > trading_days:
                        base_hist = base_closes.iloc[-(trading_days + 1)]
                        quote_hist = quote_closes.iloc[-(trading_days + 1)]
                        if quote_hist and quote_hist != 0:
                            hist_cross = base_hist / quote_hist
                            if hist_cross != 0:
                                historical_changes[label] = ((price - hist_cross) / hist_cross) * 100

                results[name] = {
                    "price": price,
                    "change_pct": change_pct,
                    "historical": historical_changes,
                }
            except Exception:
                pass

    console.print(f"[dim]Successfully loaded {len(results)} tickers[/]")
    return results


def format_pct(value, show_sign=True):
    """Format percentage value with color."""
    if value is None:
        return "[dim]-[/]"
    style = get_change_style(value)
    if show_sign:
        return f"[{style}]{value:+.1f}%[/]"
    return f"[{style}]{value:.1f}%[/]"


def _get_terminal_width():
    """Get terminal width, defaulting to 120."""
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except Exception:
        return 120


def _format_rec(rec):
    """Format recommendation with color and short label."""
    if not rec:
        return "[dim]-[/]"
    rec_colors = {"BUY": "green", "STRONG_BUY": "bold green", "HOLD": "yellow", "SELL": "red", "STRONG_SELL": "bold red"}
    rec_short = {"STRONG_BUY": "S.BUY", "STRONG_SELL": "S.SELL"}.get(rec, rec)
    rec_color = rec_colors.get(rec, "white")
    return f"[{rec_color}]{rec_short}[/]"


def render_table(results: dict, view_config: dict, view_name: str, show_stock_movers: bool = True):
    """Render a rich table with market data."""
    console = Console()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    term_width = _get_terminal_width()
    # Use wide layout if terminal can fit ~150+ cols, otherwise split into two tables
    wide_mode = term_width >= 150

    console.print()
    console.print(
        Panel(
            f"[bold white]{view_name}[/]  |  {now}",
            border_style="blue",
            expand=False,
        )
    )
    console.print()

    for section_name, tickers in view_config.items():
        if wide_mode:
            # Single wide table with all columns
            table = Table(
                title=f"[bold cyan]{section_name}[/]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold white on dark_blue",
                border_style="blue",
                pad_edge=True,
                expand=False,
            )
            table.add_column("Market", style="bold white", min_width=18)
            table.add_column("Price", justify="right", min_width=9)
            table.add_column("1D", justify="right", min_width=6)
            for label in PERIOD_LABELS:
                table.add_column(label, justify="right", min_width=6)
            table.add_column("52W", justify="center", min_width=12)
            table.add_column("PE(T)", justify="right", min_width=5)
            table.add_column("PE(F)", justify="right", min_width=5)
            table.add_column("Target", justify="center", min_width=14)
            table.add_column("Rec", justify="center", min_width=8)
            table.add_column("Trend", justify="center", min_width=5)

            for symbol, name in tickers.items():
                data = results.get(symbol)
                if data is None:
                    row = [name, "[dim]N/A[/]", "-"] + ["-"] * len(PERIOD_LABELS) + ["-", "-", "-", "-", "-", "-"]
                    table.add_row(*row)
                    continue

                price_str = f"{data['price']:,.2f}"
                style = get_change_style(data["change_pct"])
                arrow = get_change_arrow(data["change_pct"])
                row = [name, f"[{style}]{price_str}[/]", format_pct(data["change_pct"])]
                historical = data.get("historical", {})
                for label in PERIOD_LABELS:
                    row.append(format_pct(historical.get(label)))

                w52_high, w52_low = data.get("week52_high"), data.get("week52_low")
                row.append(f"[dim]{w52_low:,.0f}[/]-[bold]{w52_high:,.0f}[/]" if w52_high and w52_low else "[dim]-[/]")

                pe_t, pe_f = data.get("pe_trailing"), data.get("pe_forward")
                row.append(f"{pe_t:.1f}" if pe_t else "[dim]-[/]")
                row.append(f"{pe_f:.1f}" if pe_f else "[dim]-[/]")

                t_high, t_mean, t_low = data.get("target_high"), data.get("target_mean"), data.get("target_low")
                if t_mean:
                    row.append(f"[red]{t_low:.0f}[/]-[yellow]{t_mean:.0f}[/]-[green]{t_high:.0f}[/]" if t_low and t_high else f"[yellow]{t_mean:.0f}[/]")
                else:
                    row.append("[dim]-[/]")

                row.append(_format_rec(data.get("recommendation")))
                row.append(arrow)
                table.add_row(*row)

            console.print(table)
            console.print()
        else:
            # Narrow mode: two separate tables
            # Table 1: Price + Historical changes
            # Pick periods that fit: 1D + up to 4 historical periods for narrow terminals
            if term_width < 90:
                show_periods = ["1W", "1M", "1Y", "5Y"]
            elif term_width < 100:
                show_periods = ["1W", "1M", "6M", "1Y", "5Y"]
            elif term_width < 120:
                show_periods = ["1W", "1M", "3M", "6M", "1Y", "5Y"]
            else:
                show_periods = PERIOD_LABELS

            price_table = Table(
                title=f"[bold cyan]{section_name} - Price & Changes[/]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold white on dark_blue",
                border_style="blue",
                pad_edge=True,
                expand=False,
            )
            price_table.add_column("Market", style="bold white", min_width=16)
            price_table.add_column("Price", justify="right", min_width=9)
            price_table.add_column("1D", justify="right", min_width=6)
            for label in show_periods:
                price_table.add_column(label, justify="right", min_width=6)
            price_table.add_column("", justify="center", min_width=3)

            for symbol, name in tickers.items():
                data = results.get(symbol)
                if data is None:
                    row = [name, "[dim]N/A[/]", "-"] + ["-"] * len(show_periods) + ["-"]
                    price_table.add_row(*row)
                    continue

                price_str = f"{data['price']:,.2f}"
                style = get_change_style(data["change_pct"])
                arrow = get_change_arrow(data["change_pct"])
                row = [name, f"[{style}]{price_str}[/]", format_pct(data["change_pct"])]
                historical = data.get("historical", {})
                for label in show_periods:
                    row.append(format_pct(historical.get(label)))
                row.append(arrow)
                price_table.add_row(*row)

            console.print(price_table)
            console.print()

            # Table 2: Fundamentals (52W, PE, Target, Rec)
            # Only show if any ticker in section has fundamental data
            has_fundamentals = any(
                results.get(s, {}).get("pe_trailing") or results.get(s, {}).get("target_mean") or results.get(s, {}).get("recommendation")
                for s in tickers
            )
            if has_fundamentals:
                fund_table = Table(
                    title=f"[bold cyan]{section_name} - Fundamentals[/]",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold white on dark_blue",
                    border_style="blue",
                    pad_edge=True,
                    expand=False,
                )
                fund_table.add_column("Market", style="bold white", min_width=14)
                fund_table.add_column("52W Range", justify="center", min_width=12)
                fund_table.add_column("PE(T)", justify="right", min_width=5)
                fund_table.add_column("PE(F)", justify="right", min_width=5)
                fund_table.add_column("Target(L-M-H)", justify="center", min_width=13)
                fund_table.add_column("Rec", justify="center", min_width=6)

                for symbol, name in tickers.items():
                    data = results.get(symbol)
                    if data is None:
                        fund_table.add_row(name, "-", "-", "-", "-", "-")
                        continue

                    w52_high, w52_low = data.get("week52_high"), data.get("week52_low")
                    w52_str = f"[dim]{w52_low:,.0f}[/]-[bold]{w52_high:,.0f}[/]" if w52_high and w52_low else "[dim]-[/]"

                    pe_t, pe_f = data.get("pe_trailing"), data.get("pe_forward")
                    pe_t_str = f"{pe_t:.1f}" if pe_t else "[dim]-[/]"
                    pe_f_str = f"{pe_f:.1f}" if pe_f else "[dim]-[/]"

                    t_high, t_mean, t_low = data.get("target_high"), data.get("target_mean"), data.get("target_low")
                    if t_mean:
                        target_str = f"[red]{t_low:.0f}[/]-[yellow]{t_mean:.0f}[/]-[green]{t_high:.0f}[/]" if t_low and t_high else f"[yellow]{t_mean:.0f}[/]"
                    else:
                        target_str = "[dim]-[/]"

                    fund_table.add_row(name, w52_str, pe_t_str, pe_f_str, target_str, _format_rec(data.get("recommendation")))

                console.print(fund_table)
                console.print()

    # Summary - Market/Index movers from current view
    gainers = []
    losers = []
    for section_tickers in view_config.values():
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
        title="[bold yellow]Top Movers (Indices/Markets)[/]",
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

    # Stock movers by region (US, Singapore, India)
    if show_stock_movers:
        for region_name, stocks in TOP_MOVERS_STOCKS.items():
            region_gainers = []
            region_losers = []
            for symbol, name in stocks.items():
                data = results.get(symbol)
                if data:
                    if data["change_pct"] > 0:
                        region_gainers.append((name, data["change_pct"]))
                    elif data["change_pct"] < 0:
                        region_losers.append((name, data["change_pct"]))

            region_gainers.sort(key=lambda x: x[1], reverse=True)
            region_losers.sort(key=lambda x: x[1])

            if region_gainers or region_losers:
                stock_table = Table(
                    title=f"[bold magenta]Top Stock Movers - {region_name}[/]",
                    box=box.ROUNDED,
                    border_style="magenta",
                    expand=False,
                )
                stock_table.add_column("Top Gainers", style="green", min_width=25)
                stock_table.add_column("Top Losers", style="red", min_width=25)

                for i in range(min(5, max(len(region_gainers), len(region_losers)))):
                    g = f"{region_gainers[i][0]}: +{region_gainers[i][1]:.2f}%" if i < len(region_gainers) else ""
                    l = f"{region_losers[i][0]}: {region_losers[i][1]:.2f}%" if i < len(region_losers) else ""
                    stock_table.add_row(g, l)

                console.print(stock_table)
                console.print()


def fetch_stock_details(symbol: str) -> dict:
    """Fetch comprehensive details for a single stock."""
    console = Console()
    console.print(f"[dim]Fetching details for {symbol.upper()}...[/]")

    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        if not info or info.get("regularMarketPrice") is None:
            return {"error": f"Could not fetch data for {symbol}"}

        return {
            "symbol": symbol.upper(),
            "name": info.get("longName", info.get("shortName", "N/A")),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            # Price data
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "previous_close": info.get("previousClose"),
            "open": info.get("open", info.get("regularMarketOpen")),
            "day_high": info.get("dayHigh", info.get("regularMarketDayHigh")),
            "day_low": info.get("dayLow", info.get("regularMarketDayLow")),
            "week52_high": info.get("fiftyTwoWeekHigh"),
            "week52_low": info.get("fiftyTwoWeekLow"),
            "volume": info.get("volume", info.get("regularMarketVolume")),
            "avg_volume": info.get("averageVolume"),
            # Company info
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "float_shares": info.get("floatShares"),
            # Valuation
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            # Dividends
            "dividend_rate": info.get("dividendRate"),
            "dividend_yield": info.get("dividendYield"),
            "ex_dividend_date": info.get("exDividendDate"),
            # Analyst
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_mean": info.get("targetMeanPrice"),
            "target_median": info.get("targetMedianPrice"),
            "recommendation": info.get("recommendationKey", "").upper() if info.get("recommendationKey") else None,
            "num_analysts": info.get("numberOfAnalystOpinions"),
            # Additional
            "beta": info.get("beta"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
        }
    except Exception as e:
        return {"error": str(e)}


def render_stock_details(data: dict):
    """Render detailed stock information in a rich panel."""
    console = Console()

    if "error" in data:
        console.print(f"[red]Error: {data['error']}[/]")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symbol = data["symbol"]
    name = data["name"]
    currency = data["currency"]

    # Calculate change
    current = data.get("current_price", 0)
    prev = data.get("previous_close", 0)
    change = current - prev if current and prev else 0
    change_pct = (change / prev * 100) if prev else 0
    change_style = "green" if change >= 0 else "red"
    change_arrow = "▲" if change >= 0 else "▼"

    # Header
    console.print()
    console.print(Panel(
        f"[bold white]{name}[/] ([cyan]{symbol}[/])  |  {now}",
        border_style="blue",
        expand=False,
    ))
    console.print()

    # Price Panel
    price_table = Table(box=box.ROUNDED, border_style="green", expand=False, title="[bold green]Price Information[/]")
    price_table.add_column("Metric", style="bold white", min_width=18)
    price_table.add_column("Value", justify="right", min_width=15)
    price_table.add_column("Metric", style="bold white", min_width=18)
    price_table.add_column("Value", justify="right", min_width=15)

    def fmt_price(val):
        return f"${val:,.2f}" if val else "-"

    def fmt_num(val):
        if not val:
            return "-"
        if val >= 1e12:
            return f"${val/1e12:.2f}T"
        if val >= 1e9:
            return f"${val/1e9:.2f}B"
        if val >= 1e6:
            return f"${val/1e6:.2f}M"
        return f"{val:,.0f}"

    price_table.add_row(
        "Current Price", f"[{change_style}]{fmt_price(current)}[/]",
        "Previous Close", fmt_price(prev)
    )
    price_table.add_row(
        "Change", f"[{change_style}]{change_arrow} ${abs(change):.2f} ({change_pct:+.2f}%)[/]",
        "Open", fmt_price(data.get("open"))
    )
    price_table.add_row(
        "Day Range", f"{fmt_price(data.get('day_low'))} - {fmt_price(data.get('day_high'))}",
        "52W Range", f"{fmt_price(data.get('week52_low'))} - {fmt_price(data.get('week52_high'))}"
    )
    price_table.add_row(
        "Volume", fmt_num(data.get("volume")),
        "Avg Volume", fmt_num(data.get("avg_volume"))
    )
    console.print(price_table)
    console.print()

    # Company Info
    company_table = Table(box=box.ROUNDED, border_style="cyan", expand=False, title="[bold cyan]Company Info[/]")
    company_table.add_column("Metric", style="bold white", min_width=18)
    company_table.add_column("Value", justify="right", min_width=15)
    company_table.add_column("Metric", style="bold white", min_width=18)
    company_table.add_column("Value", justify="right", min_width=15)

    company_table.add_row(
        "Sector", data.get("sector", "-"),
        "Industry", data.get("industry", "-")
    )
    company_table.add_row(
        "Market Cap", fmt_num(data.get("market_cap")),
        "Enterprise Value", fmt_num(data.get("enterprise_value"))
    )
    company_table.add_row(
        "Shares Outstanding", fmt_num(data.get("shares_outstanding")),
        "Float Shares", fmt_num(data.get("float_shares"))
    )
    console.print(company_table)
    console.print()

    # Valuation
    val_table = Table(box=box.ROUNDED, border_style="yellow", expand=False, title="[bold yellow]Valuation Metrics[/]")
    val_table.add_column("Metric", style="bold white", min_width=18)
    val_table.add_column("Value", justify="right", min_width=12)
    val_table.add_column("Metric", style="bold white", min_width=18)
    val_table.add_column("Value", justify="right", min_width=12)

    def fmt_ratio(val):
        return f"{val:.2f}" if val else "-"

    def fmt_pct(val):
        return f"{val*100:.2f}%" if val else "-"

    val_table.add_row(
        "P/E (Trailing)", fmt_ratio(data.get("pe_trailing")),
        "P/E (Forward)", fmt_ratio(data.get("pe_forward"))
    )
    val_table.add_row(
        "PEG Ratio", fmt_ratio(data.get("peg_ratio")),
        "Price/Book", fmt_ratio(data.get("price_to_book"))
    )
    val_table.add_row(
        "EPS (Trailing)", fmt_price(data.get("eps_trailing")),
        "EPS (Forward)", fmt_price(data.get("eps_forward"))
    )
    val_table.add_row(
        "Price/Sales", fmt_ratio(data.get("price_to_sales")),
        "Beta", fmt_ratio(data.get("beta"))
    )
    val_table.add_row(
        "Profit Margin", fmt_pct(data.get("profit_margin")),
        "Revenue Growth", fmt_pct(data.get("revenue_growth"))
    )
    console.print(val_table)
    console.print()

    # Dividends (if applicable)
    if data.get("dividend_yield"):
        div_table = Table(box=box.ROUNDED, border_style="magenta", expand=False, title="[bold magenta]Dividends[/]")
        div_table.add_column("Metric", style="bold white", min_width=18)
        div_table.add_column("Value", justify="right", min_width=15)

        div_table.add_row("Dividend Rate", fmt_price(data.get("dividend_rate")))
        div_table.add_row("Dividend Yield", fmt_pct(data.get("dividend_yield")))
        console.print(div_table)
        console.print()

    # Analyst Recommendations
    analyst_table = Table(box=box.ROUNDED, border_style="blue", expand=False, title="[bold blue]Analyst Recommendations[/]")
    analyst_table.add_column("Metric", style="bold white", min_width=18)
    analyst_table.add_column("Value", justify="right", min_width=15)
    analyst_table.add_column("Metric", style="bold white", min_width=18)
    analyst_table.add_column("Value", justify="right", min_width=15)

    rec = data.get("recommendation")
    rec_colors = {"BUY": "green", "STRONG_BUY": "bold green", "HOLD": "yellow", "SELL": "red", "STRONG_SELL": "bold red"}
    rec_style = rec_colors.get(rec, "white") if rec else "dim"

    analyst_table.add_row(
        "Target High", f"[green]{fmt_price(data.get('target_high'))}[/]",
        "Target Low", f"[red]{fmt_price(data.get('target_low'))}[/]"
    )
    analyst_table.add_row(
        "Target Mean", f"[yellow]{fmt_price(data.get('target_mean'))}[/]",
        "Target Median", fmt_price(data.get("target_median"))
    )
    analyst_table.add_row(
        "Recommendation", f"[{rec_style}]{rec or '-'}[/]",
        "# of Analysts", str(data.get("num_analysts", "-"))
    )

    # Upside/downside from current price
    target_mean = data.get("target_mean")
    if target_mean and current:
        upside = ((target_mean - current) / current) * 100
        upside_style = "green" if upside > 0 else "red"
        analyst_table.add_row(
            "Upside/Downside", f"[{upside_style}]{upside:+.1f}%[/]",
            "", ""
        )

    console.print(analyst_table)
    console.print()


def fetch_and_render_dividends(symbol: str):
    """Fetch and display dividend history for a stock."""
    console = Console()
    console.print(f"[dim]Fetching dividend history for {symbol.upper()}...[/]")

    try:
        ticker = yf.Ticker(symbol.upper())
        dividends = ticker.dividends
        info = ticker.info

        if dividends.empty:
            console.print(f"[yellow]No dividend history found for {symbol.upper()}[/]")
            return

        console.print()
        console.print(Panel(
            f"[bold white]Dividend History[/] - [cyan]{symbol.upper()}[/] ({info.get('longName', 'N/A')})",
            border_style="magenta",
            expand=False,
        ))
        console.print()

        # Summary info
        summary_table = Table(box=box.ROUNDED, border_style="magenta", expand=False, title="[bold magenta]Dividend Summary[/]")
        summary_table.add_column("Metric", style="bold white", min_width=20)
        summary_table.add_column("Value", justify="right", min_width=15)

        current_rate = info.get("dividendRate")
        current_yield = info.get("dividendYield")
        summary_table.add_row("Annual Dividend Rate", f"${current_rate:.2f}" if current_rate else "-")
        summary_table.add_row("Dividend Yield", f"{current_yield*100:.2f}%" if current_yield else "-")
        summary_table.add_row("Total Dividends (History)", f"${dividends.sum():.2f}")
        summary_table.add_row("Number of Payments", str(len(dividends)))
        console.print(summary_table)
        console.print()

        # Recent dividends table
        recent = dividends.tail(12).iloc[::-1]  # Last 12, most recent first
        div_table = Table(box=box.ROUNDED, border_style="green", expand=False, title="[bold green]Recent Dividends (Last 12)[/]")
        div_table.add_column("Date", style="bold white", min_width=12)
        div_table.add_column("Amount", justify="right", min_width=10)

        for date, amount in recent.items():
            div_table.add_row(date.strftime("%Y-%m-%d"), f"${amount:.4f}")

        console.print(div_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error fetching dividends: {e}[/]")


def fetch_and_render_earnings(symbol: str):
    """Fetch and display earnings dates for a stock."""
    console = Console()
    console.print(f"[dim]Fetching earnings dates for {symbol.upper()}...[/]")

    try:
        ticker = yf.Ticker(symbol.upper())
        earnings_dates = ticker.earnings_dates
        info = ticker.info

        if earnings_dates is None or earnings_dates.empty:
            console.print(f"[yellow]No earnings dates found for {symbol.upper()}[/]")
            return

        console.print()
        console.print(Panel(
            f"[bold white]Earnings Dates[/] - [cyan]{symbol.upper()}[/] ({info.get('longName', 'N/A')})",
            border_style="yellow",
            expand=False,
        ))
        console.print()

        # Earnings table
        earn_table = Table(box=box.ROUNDED, border_style="yellow", expand=False, title="[bold yellow]Earnings Calendar[/]")
        earn_table.add_column("Date", style="bold white", min_width=12)
        earn_table.add_column("EPS Estimate", justify="right", min_width=12)
        earn_table.add_column("Reported EPS", justify="right", min_width=12)
        earn_table.add_column("Surprise %", justify="right", min_width=10)

        for date, row in earnings_dates.head(12).iterrows():
            eps_est = row.get("EPS Estimate", None)
            eps_rep = row.get("Reported EPS", None)
            surprise = row.get("Surprise(%)", None)

            eps_est_str = f"${eps_est:.2f}" if eps_est and not pd.isna(eps_est) else "-"
            eps_rep_str = f"${eps_rep:.2f}" if eps_rep and not pd.isna(eps_rep) else "[dim]Pending[/]"

            if surprise and not pd.isna(surprise):
                surp_style = "green" if surprise > 0 else "red"
                surprise_str = f"[{surp_style}]{surprise:+.2f}%[/]"
            else:
                surprise_str = "-"

            earn_table.add_row(
                date.strftime("%Y-%m-%d"),
                eps_est_str,
                eps_rep_str,
                surprise_str
            )

        console.print(earn_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error fetching earnings: {e}[/]")


def fetch_and_render_financials(symbol: str, freq: str = "yearly"):
    """Fetch and display income statement for a stock."""
    console = Console()
    console.print(f"[dim]Fetching financials for {symbol.upper()} ({freq})...[/]")

    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        if freq == "quarterly":
            income = ticker.quarterly_income_stmt
        else:
            income = ticker.income_stmt

        if income is None or income.empty:
            console.print(f"[yellow]No financial data found for {symbol.upper()}[/]")
            return

        console.print()
        console.print(Panel(
            f"[bold white]Income Statement ({freq.title()})[/] - [cyan]{symbol.upper()}[/] ({info.get('longName', 'N/A')})",
            border_style="cyan",
            expand=False,
        ))
        console.print()

        def fmt_num(val):
            if pd.isna(val) or val is None:
                return "-"
            if abs(val) >= 1e9:
                return f"${val/1e9:.2f}B"
            if abs(val) >= 1e6:
                return f"${val/1e6:.2f}M"
            return f"${val:,.0f}"

        # Key metrics
        fin_table = Table(box=box.ROUNDED, border_style="cyan", expand=False)
        fin_table.add_column("Metric", style="bold white", min_width=25)

        # Add columns for each period
        for col in income.columns[:4]:
            fin_table.add_column(col.strftime("%Y-%m-%d"), justify="right", min_width=12)

        key_metrics = [
            "Total Revenue", "Gross Profit", "Operating Income", "Net Income",
            "EBITDA", "Basic EPS", "Diluted EPS"
        ]

        for metric in key_metrics:
            if metric in income.index:
                row = [metric]
                for col in income.columns[:4]:
                    row.append(fmt_num(income.loc[metric, col]))
                fin_table.add_row(*row)

        console.print(fin_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error fetching financials: {e}[/]")


def fetch_and_render_cashflow(symbol: str, freq: str = "yearly"):
    """Fetch and display cashflow statement for a stock."""
    console = Console()
    console.print(f"[dim]Fetching cashflow for {symbol.upper()} ({freq})...[/]")

    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        if freq == "quarterly":
            cashflow = ticker.quarterly_cashflow
        else:
            cashflow = ticker.cashflow

        if cashflow is None or cashflow.empty:
            console.print(f"[yellow]No cashflow data found for {symbol.upper()}[/]")
            return

        console.print()
        console.print(Panel(
            f"[bold white]Cashflow Statement ({freq.title()})[/] - [cyan]{symbol.upper()}[/] ({info.get('longName', 'N/A')})",
            border_style="blue",
            expand=False,
        ))
        console.print()

        def fmt_num(val):
            if pd.isna(val) or val is None:
                return "-"
            style = "green" if val > 0 else "red"
            if abs(val) >= 1e9:
                return f"[{style}]${val/1e9:.2f}B[/]"
            if abs(val) >= 1e6:
                return f"[{style}]${val/1e6:.2f}M[/]"
            return f"[{style}]${val:,.0f}[/]"

        cf_table = Table(box=box.ROUNDED, border_style="blue", expand=False)
        cf_table.add_column("Metric", style="bold white", min_width=30)

        for col in cashflow.columns[:4]:
            cf_table.add_column(col.strftime("%Y-%m-%d"), justify="right", min_width=12)

        key_metrics = [
            "Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow",
            "Free Cash Flow", "Capital Expenditure", "End Cash Position"
        ]

        for metric in key_metrics:
            if metric in cashflow.index:
                row = [metric]
                for col in cashflow.columns[:4]:
                    row.append(fmt_num(cashflow.loc[metric, col]))
                cf_table.add_row(*row)

        console.print(cf_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error fetching cashflow: {e}[/]")


def main():
    parser = argparse.ArgumentParser(
        description="World Market Overview - View global markets, indices, and stocks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 market_overview.py              # Default: detail view with all markets
  python3 market_overview.py --summary    # Summary: key indices only
  python3 market_overview.py --portfolio  # Portfolio: your stock holdings
  python3 market_overview.py --stock TSLA # Get detailed info for a specific stock
  python3 market_overview.py -t NVDA      # Short form for stock lookup
  python3 market_overview.py --no-movers  # Skip stock movers section
  python3 market_overview.py --dividends AAPL      # Dividend history
  python3 market_overview.py --earnings TSLA       # Earnings dates and EPS
  python3 market_overview.py --financials NVDA     # Income statement (yearly)
  python3 market_overview.py --financials NVDA -q  # Income statement (quarterly)
  python3 market_overview.py --cashflow MSFT       # Cashflow statement (yearly)
  python3 market_overview.py -c MSFT -q            # Cashflow statement (quarterly)
        """
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Show summary view with key indices only"
    )
    parser.add_argument(
        "--portfolio", "-p",
        action="store_true",
        help="Show portfolio view with your stocks"
    )
    parser.add_argument(
        "--no-movers",
        action="store_true",
        help="Skip individual stock movers section"
    )
    parser.add_argument(
        "--stock", "-t",
        type=str,
        metavar="SYMBOL",
        help="Get detailed info for a specific stock (e.g., TSLA, NVDA, AAPL)"
    )
    parser.add_argument(
        "--dividends", "-d",
        type=str,
        metavar="SYMBOL",
        help="Get dividend history for a specific stock"
    )
    parser.add_argument(
        "--earnings", "-e",
        type=str,
        metavar="SYMBOL",
        help="Get earnings dates and EPS data for a stock"
    )
    parser.add_argument(
        "--financials", "-f",
        type=str,
        metavar="SYMBOL",
        help="Get income statement for a stock"
    )
    parser.add_argument(
        "--cashflow", "-c",
        type=str,
        metavar="SYMBOL",
        help="Get cashflow statement for a stock"
    )
    parser.add_argument(
        "--quarterly", "-q",
        action="store_true",
        help="Use quarterly data instead of yearly (for --financials and --cashflow)"
    )
    args = parser.parse_args()

    console = Console()

    # Handle stock lookup mode
    if args.stock:
        data = fetch_stock_details(args.stock)
        render_stock_details(data)
        return

    # Handle dividends lookup
    if args.dividends:
        fetch_and_render_dividends(args.dividends)
        return

    # Handle earnings lookup
    if args.earnings:
        fetch_and_render_earnings(args.earnings)
        return

    # Handle financials lookup
    if args.financials:
        freq = "quarterly" if args.quarterly else "yearly"
        fetch_and_render_financials(args.financials, freq)
        return

    # Handle cashflow lookup
    if args.cashflow:
        freq = "quarterly" if args.quarterly else "yearly"
        fetch_and_render_cashflow(args.cashflow, freq)
        return

    # Select view based on arguments
    if args.portfolio:
        view_config = PORTFOLIO_VIEW
        view_name = "My Portfolio"
        show_movers = not args.no_movers
    elif args.summary:
        view_config = SUMMARY_VIEW
        view_name = "Market Summary"
        show_movers = not args.no_movers
    else:
        view_config = DETAIL_VIEW
        view_name = "World Markets Overview"
        show_movers = not args.no_movers

    console.print(f"[bold blue]Fetching market data ({view_name})...[/]")
    results = fetch_market_data(view_config, include_top_movers=show_movers)
    render_table(results, view_config, view_name, show_stock_movers=show_movers)


if __name__ == "__main__":
    main()
