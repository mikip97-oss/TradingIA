from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


FALLBACK_AKTIEN = [
    "NVDA", "AMD", "TSLA", "PLTR", "SOFI",
    "COIN", "MSTR", "AAPL", "MSFT", "MU",
    "META", "GOOGL", "AMZN", "AVGO", "HOOD",
    "RIVN", "SMCI", "NFLX", "SHOP", "UBER",
]

SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"


def normalize_yahoo_ticker(ticker: str) -> str:
    return ticker.strip().upper().replace(".", "-")


def deduplicate_tickers(tickers: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for ticker in tickers:
        normalized = normalize_yahoo_ticker(str(ticker))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)

    return result


def lade_sp500_ticker() -> list[str]:
    tables = pd.read_html(SP500_URL)
    sp500 = tables[0]
    return deduplicate_tickers(sp500["Symbol"].tolist())


def lade_nasdaq100_ticker() -> list[str]:
    tables = pd.read_html(NASDAQ100_URL)

    for table in tables:
        for column in ["Ticker", "Symbol"]:
            if column in table.columns:
                tickers = table[column].dropna().astype(str).tolist()
                if tickers:
                    return deduplicate_tickers(tickers)

    raise ValueError("Nasdaq-100 ticker table not found")


def lade_fallback_ticker() -> list[str]:
    return deduplicate_tickers(FALLBACK_AKTIEN)


def lade_grosses_universum(
    include_sp500: bool = True,
    include_nasdaq100: bool = True,
    include_fallback: bool = True,
) -> list[str]:
    tickers: list[str] = []

    if include_sp500:
        try:
            tickers.extend(lade_sp500_ticker())
        except Exception as error:
            print(f"S&P-500-Universum konnte nicht geladen werden: {error}")

    if include_nasdaq100:
        try:
            tickers.extend(lade_nasdaq100_ticker())
        except Exception as error:
            print(f"Nasdaq-100-Universum konnte nicht geladen werden: {error}")

    if include_fallback:
        tickers.extend(lade_fallback_ticker())

    return deduplicate_tickers(tickers)


def lade_standard_universum(use_large_universe: bool = True) -> list[str]:
    if use_large_universe:
        universe = lade_grosses_universum()
        if universe:
            return universe

    return lade_fallback_ticker()
