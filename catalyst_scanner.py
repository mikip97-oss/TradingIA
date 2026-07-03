from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

from config import TOP_ANZAHL

try:
    from config import SCANNER_MAX_WORKERS
except ImportError:
    SCANNER_MAX_WORKERS = 8

try:
    from universe import lade_standard_universum
except ImportError:
    lade_standard_universum = None


FALLBACK_CATALYST_TICKERS = [
    "NVDA", "TSLA", "AMD", "AAPL", "MSFT",
    "META", "AMZN", "GOOGL", "COIN", "MSTR",
    "PLTR", "HOOD", "SOFI", "RIVN", "SMCI",
]

CATALYST_COLUMNS = [
    "Aktie",
    "CatalystScore",
    "Empfehlung",
    "Heute %",
    "Volumen-Faktor",
    "ROC",
    "Gründe",
]


def get_catalyst_tickers() -> list[str]:
    if lade_standard_universum is None:
        return FALLBACK_CATALYST_TICKERS

    try:
        tickers = lade_standard_universum()
    except Exception as error:
        print(f"Catalyst-Universum konnte nicht geladen werden: {error}")
        return FALLBACK_CATALYST_TICKERS

    return tickers or FALLBACK_CATALYST_TICKERS


def scan_catalyst_market(
    tickers: list[str] | None = None,
    max_workers: int | None = None,
    top_anzahl: int | None = None,
) -> pd.DataFrame:
    universe = tickers if tickers is not None else get_catalyst_tickers()
    workers = _resolve_max_workers(max_workers, len(universe))
    rows = []

    print(f"Scanne {len(universe)} Aktien fuer technische Catalyst-Setups mit {workers} Workern...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(scan_catalyst_ticker, ticker): ticker for ticker in universe}

        for future in as_completed(futures):
            ticker = futures[future]
            try:
                result = future.result()
            except Exception as error:
                print(f"Catalyst-Fehler bei {ticker}: {error}")
                continue

            if result is not None:
                rows.append(result)

    if not rows:
        return pd.DataFrame(columns=CATALYST_COLUMNS)

    limit = TOP_ANZAHL if top_anzahl is None else top_anzahl
    return (
        pd.DataFrame(rows, columns=CATALYST_COLUMNS)
        .sort_values(by="CatalystScore", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def scan_catalyst_ticker(ticker: str) -> dict[str, float | str] | None:
    data = yf.download(
        ticker,
        period="5d",
        interval="5m",
        progress=False,
        auto_adjust=True,
        threads=False,
    )

    if data is None or data.empty:
        return None

    data = _prepare_intraday_data(data)
    if len(data) < 30:
        return None

    metrics = calculate_catalyst_metrics(data)
    score, recommendation, reasons = score_catalyst_setup(metrics)

    return {
        "Aktie": ticker,
        "CatalystScore": round(score, 1),
        "Empfehlung": recommendation,
        "Heute %": round(metrics["today_change_pct"], 2),
        "Volumen-Faktor": round(metrics["volume_factor"], 2),
        "ROC": round(metrics["roc"], 2),
        "Gründe": ", ".join(reasons),
    }


def calculate_catalyst_metrics(data: pd.DataFrame) -> dict[str, float]:
    close = data["Close"].squeeze()
    high = data["High"].squeeze()
    low = data["Low"].squeeze()
    open_ = data["Open"].squeeze()
    volume = data["Volume"].squeeze()

    last_price = float(close.iloc[-1])
    session_open = float(open_.iloc[0])
    previous_close = float(data.attrs.get("previous_close", session_open))
    today_high = float(high.max())
    today_low = float(low.min())
    today_range = max(today_high - today_low, 0.01)

    today_change_pct = ((last_price - session_open) / session_open) * 100 if session_open else 0.0
    gap_pct = ((session_open - previous_close) / previous_close) * 100 if previous_close else 0.0
    distance_to_high_pct = ((today_high - last_price) / today_high) * 100 if today_high else 0.0
    close_position_in_range = ((last_price - today_low) / today_range) * 100
    volatility_pct = _intraday_volatility(close)
    baseline_volatility_pct = _baseline_intraday_volatility(close)
    volatility_factor = volatility_pct / max(baseline_volatility_pct, 0.01)

    return {
        "today_change_pct": today_change_pct,
        "volume_factor": _volume_factor(volume),
        "gap_pct": gap_pct,
        "roc": _roc(close),
        "distance_to_high_pct": distance_to_high_pct,
        "close_position_in_range": close_position_in_range,
        "volatility_factor": volatility_factor,
    }


def score_catalyst_setup(metrics: dict[str, float]) -> tuple[float, str, list[str]]:
    score = 0.0
    reasons: list[str] = []

    today_change = metrics["today_change_pct"]
    volume_factor = metrics["volume_factor"]
    gap = metrics["gap_pct"]
    roc = metrics["roc"]
    distance_to_high = metrics["distance_to_high_pct"]
    close_position = metrics["close_position_in_range"]
    volatility_factor = metrics["volatility_factor"]

    if today_change >= 1.0:
        score += 16
        reasons.append("positive Tagesreaktion")
    if today_change >= 3.0:
        score += 12
        reasons.append("starke Tagesbewegung")
    if today_change >= 5.0:
        score += 8
        reasons.append("außergewöhnlich starke Bewegung")
    if today_change <= -3.0:
        score -= 12
        reasons.append("starke negative Marktreaktion")

    if volume_factor >= 2.0:
        score += 22
        reasons.append("außergewöhnlich hohes Volumen")
    elif volume_factor >= 1.5:
        score += 16
        reasons.append("deutlich erhöhtes Volumen")
    elif volume_factor >= 1.0:
        score += 8
        reasons.append("Volumen über Durchschnitt")

    if gap >= 2.0:
        score += 14
        reasons.append("starkes Gap-Up")
    elif gap >= 1.0:
        score += 8
        reasons.append("positives Gap")
    elif gap <= -2.0:
        score -= 10
        reasons.append("starkes Gap-Down")

    if roc >= 2.0:
        score += 14
        reasons.append("starker ROC")
    elif roc >= 1.0:
        score += 8
        reasons.append("positiver ROC")
    elif roc <= -1.5:
        score -= 8
        reasons.append("negativer ROC")

    if distance_to_high <= 0.5 or close_position >= 88:
        score += 16
        reasons.append("nahe am Tageshoch")
    elif close_position >= 75:
        score += 8
        reasons.append("oberer Tagesbereich")

    if volatility_factor >= 1.8:
        score += 14
        reasons.append("außergewöhnliche Volatilität")
    elif volatility_factor >= 1.3:
        score += 8
        reasons.append("erhöhte Volatilität")

    score = max(0.0, min(score, 100.0))
    return score, _recommendation(score), reasons


def _recommendation(score: float) -> str:
    if score >= 80:
        return "🟢 Sehr starker Catalyst"
    if score >= 70:
        return "🟢 Catalyst-Kandidat"
    if score >= 60:
        return "🟡 Beobachten"
    return "🔴 Kein Catalyst"


def _prepare_intraday_data(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy().dropna()
    if isinstance(prepared.columns, pd.MultiIndex):
        prepared.columns = prepared.columns.get_level_values(0)

    if not isinstance(prepared.index, pd.DatetimeIndex):
        prepared.index = pd.to_datetime(prepared.index)

    prepared = prepared.sort_index()
    latest_session = prepared.index.normalize().max()
    previous_rows = prepared[prepared.index.normalize() < latest_session]
    session = prepared[prepared.index.normalize() == latest_session].copy()

    if not previous_rows.empty:
        session.attrs["previous_close"] = float(previous_rows["Close"].squeeze().iloc[-1])
    else:
        session.attrs["previous_close"] = float(session["Open"].squeeze().iloc[0])

    return session


def _resolve_max_workers(max_workers: int | None, ticker_count: int) -> int:
    configured = SCANNER_MAX_WORKERS if max_workers is None else max_workers
    configured = max(1, int(configured))
    return min(configured, max(1, ticker_count))


def _volume_factor(volume: pd.Series, window: int = 20) -> float:
    if len(volume) <= 1:
        return 0.0
    recent_average = float(volume.iloc[-window - 1 : -1].mean()) if len(volume) > window else float(volume.iloc[:-1].mean())
    return float(volume.iloc[-1]) / recent_average if recent_average else 0.0


def _roc(close: pd.Series, window: int = 6) -> float:
    if len(close) <= window:
        return 0.0
    previous = float(close.iloc[-window - 1])
    return ((float(close.iloc[-1]) - previous) / previous) * 100 if previous else 0.0


def _intraday_volatility(close: pd.Series, window: int = 20) -> float:
    value = close.pct_change().rolling(window).std().iloc[-1] * 100
    return float(value) if pd.notna(value) else 0.0


def _baseline_intraday_volatility(close: pd.Series, window: int = 60) -> float:
    value = close.pct_change().rolling(window).std().median() * 100
    return float(value) if pd.notna(value) else 0.0
if __name__ == "__main__":
    df = scan_catalyst_market()

    if df.empty:
        print("Keine Catalyst-Kandidaten gefunden.")
    else:
        print("\nTop Catalyst-Kandidaten:\n")
        print(df.to_string(index=False))