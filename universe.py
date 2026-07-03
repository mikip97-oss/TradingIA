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

BACKUP_US_AKTIEN = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "AVGO", "TSLA", "COST",
    "NFLX", "AMD", "ADBE", "PEP", "CSCO", "TMUS", "INTC", "QCOM", "TXN", "AMAT",
    "INTU", "AMGN", "ISRG", "HON", "BKNG", "VRTX", "SBUX", "REGN", "ADP", "MDLZ",
    "GILD", "ADI", "LRCX", "MU", "PANW", "KLAC", "SNPS", "CDNS", "MELI", "CRWD",
    "MAR", "PYPL", "CTAS", "ORLY", "CSX", "MNST", "ABNB", "NXPI", "MRVL", "ADSK",
    "FTNT", "ROP", "CHTR", "KDP", "AEP", "PAYX", "PCAR", "ROST", "ODFL", "KHC",
    "EXC", "FAST", "EA", "XEL", "IDXX", "BKR", "CTSH", "GEHC", "DDOG", "TEAM",
    "DXCM", "ZS", "BIIB", "ON", "ILMN", "WBD", "DLTR", "TTD", "ANSS", "MDB",
    "JPM", "LLY", "V", "UNH", "XOM", "MA", "JNJ", "PG", "HD", "ABBV",
    "BAC", "KO", "MRK", "CVX", "WMT", "ORCL", "CRM", "WFC", "ACN", "MCD",
    "LIN", "ABT", "DIS", "IBM", "PM", "TMO", "GS", "NOW", "CAT", "VZ",
    "NEE", "RTX", "UBER", "PFE", "SPGI", "LOW", "ISRG", "AXP", "QCOM", "UNP",
    "MS", "TJX", "BLK", "BK", "SYK", "SCHW", "ETN", "LMT", "BSX", "C",
    "AMT", "CB", "MDT", "MMC", "ADI", "PLD", "GILD", "DE", "MU", "FI",
    "SO", "MO", "DUK", "ICE", "SHW", "WM", "CL", "PANW", "HCA", "MCO",
    "ELV", "APH", "CMG", "SNPS", "CDNS", "PH", "TT", "NKE", "MCK", "TDG",
    "EQIX", "EOG", "USB", "ITW", "AON", "MMM", "PNC", "ORLY", "APD", "GD",
    "REGN", "CME", "MSI", "CI", "ZTS", "BDX", "EMR", "SLB", "WELL", "AJG",
    "COF", "FDX", "TGT", "CSX", "NSC", "FCX", "GM", "F", "PLTR", "SOFI",
    "COIN", "MSTR", "HOOD", "RIVN", "SMCI", "SHOP", "SNOW", "NET", "TSM", "NVO",
]

MIN_GROSSES_UNIVERSUM = 100


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


def lade_backup_us_ticker() -> list[str]:
    return deduplicate_tickers(BACKUP_US_AKTIEN)


def lade_grosses_universum(
    include_sp500: bool = True,
    include_nasdaq100: bool = True,
    include_fallback: bool = True,
    include_backup: bool = True,
) -> list[str]:
    tickers: list[str] = []
    online_errors = 0

    if include_sp500:
        try:
            tickers.extend(lade_sp500_ticker())
        except Exception as error:
            online_errors += 1
            print(f"S&P-500-Universum konnte nicht geladen werden: {error}")

    if include_nasdaq100:
        try:
            tickers.extend(lade_nasdaq100_ticker())
        except Exception as error:
            online_errors += 1
            print(f"Nasdaq-100-Universum konnte nicht geladen werden: {error}")

    deduplicated = deduplicate_tickers(tickers)

    if include_backup and (online_errors > 0 or len(deduplicated) < MIN_GROSSES_UNIVERSUM):
        deduplicated = deduplicate_tickers([*deduplicated, *lade_backup_us_ticker()])

    if include_fallback:
        deduplicated = deduplicate_tickers([*deduplicated, *lade_fallback_ticker()])

    return deduplicated


def lade_standard_universum(use_large_universe: bool = True) -> list[str]:
    if use_large_universe:
        universe = lade_grosses_universum()
        if universe:
            return universe

    return lade_fallback_ticker()
