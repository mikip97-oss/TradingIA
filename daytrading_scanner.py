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


FALLBACK_DAYTRADING_TICKERS = [
    "NVDA", "TSLA", "AMD", "AAPL", "MSFT",
    "META", "AMZN", "GOOGL", "COIN", "MSTR",
    "PLTR", "HOOD", "SOFI", "RIVN", "SMCI",
]

DAYTRADING_COLUMNS = [
    "Aktie",
    "DayTradeScore",
    "Empfehlung",
    "Einstieg",
    "Stop-Loss",
    "Ziel",
    "Heute %",
    "RSI",
    "Volumen-Faktor",
    "ADX",
    "ROC",
    "Gründe",
]


def get_daytrading_tickers() -> list[str]:
    if lade_standard_universum is None:
        return FALLBACK_DAYTRADING_TICKERS

    try:
        tickers = lade_standard_universum()
    except Exception as error:
        print(f"Daytrading-Universum konnte nicht geladen werden: {error}")
        return FALLBACK_DAYTRADING_TICKERS

    return tickers or FALLBACK_DAYTRADING_TICKERS


def scan_daytrading_market(
    tickers: list[str] | None = None,
    max_workers: int | None = None,
    top_anzahl: int | None = None,
) -> pd.DataFrame:
    universe = tickers if tickers is not None else get_daytrading_tickers()
    workers = _resolve_max_workers(max_workers, len(universe))
    rows = []

    print(f"Scanne {len(universe)} Aktien fuer Daytrading-Setups mit {workers} Workern...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(scan_daytrading_ticker, ticker): ticker for ticker in universe}

        for future in as_completed(futures):
            ticker = futures[future]
            try:
                result = future.result()
            except Exception as error:
                print(f"Daytrading-Fehler bei {ticker}: {error}")
                continue

            if result is not None:
                rows.append(result)

    if not rows:
        return pd.DataFrame(columns=DAYTRADING_COLUMNS)

    limit = TOP_ANZAHL if top_anzahl is None else top_anzahl
    return (
        pd.DataFrame(rows, columns=DAYTRADING_COLUMNS)
        .sort_values(by="DayTradeScore", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def scan_daytrading_ticker(ticker: str) -> dict[str, float | str] | None:
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

    metrics = calculate_daytrading_metrics(data)
    score, recommendation, reasons = score_daytrading_setup(metrics)
    entry = metrics["last_price"]
    atr = metrics["atr"]

    return {
        "Aktie": ticker,
        "DayTradeScore": round(score, 1),
        "Empfehlung": recommendation,
        "Einstieg": round(entry, 2),
        "Stop-Loss": round(entry - (atr * 1.2), 2),
        "Ziel": round(entry + (atr * 2.0), 2),
        "Heute %": round(metrics["today_change_pct"], 2),
        "RSI": round(metrics["rsi"], 1),
        "Volumen-Faktor": round(metrics["volume_factor"], 2),
        "ADX": round(metrics["adx"], 1),
        "ROC": round(metrics["roc"], 2),
        "Gründe": ", ".join(reasons),
    }


def calculate_daytrading_metrics(data: pd.DataFrame) -> dict[str, float]:
    close = data["Close"].squeeze()
    high = data["High"].squeeze()
    low = data["Low"].squeeze()
    open_ = data["Open"].squeeze()
    volume = data["Volume"].squeeze()

    last_price = float(close.iloc[-1])
    session_open = float(open_.iloc[0])
    previous_close = float(data.attrs.get("previous_close", close.iloc[0]))
    today_high = float(high.max())
    today_low = float(low.min())

    today_change_pct = ((last_price - session_open) / session_open) * 100 if session_open else 0.0
    gap_pct = ((float(open_.iloc[0]) - previous_close) / previous_close) * 100 if previous_close else 0.0
    high_range = max(today_high - today_low, 0.01)
    distance_to_high_pct = ((today_high - last_price) / today_high) * 100 if today_high else 0.0
    close_position_in_range = ((last_price - today_low) / high_range) * 100
    relative_move_pct = abs(today_change_pct) / max(_intraday_volatility(close), 0.01)

    return {
        "last_price": last_price,
        "today_change_pct": today_change_pct,
        "gap_pct": gap_pct,
        "volume_factor": _volume_factor(volume),
        "rsi": _rsi(close),
        "adx": _adx(high, low, close),
        "roc": _roc(close),
        "distance_to_high_pct": distance_to_high_pct,
        "close_position_in_range": close_position_in_range,
        "relative_move_pct": relative_move_pct,
        "atr": _atr(high, low, close),
    }


def score_daytrading_setup(metrics: dict[str, float]) -> tuple[float, str, list[str]]:
    score = 0.0
    reasons: list[str] = []

    today_change = metrics["today_change_pct"]
    volume_factor = metrics["volume_factor"]
    gap = metrics["gap_pct"]
    rsi = metrics["rsi"]
    adx = metrics["adx"]
    roc = metrics["roc"]
    distance_to_high = metrics["distance_to_high_pct"]
    close_position = metrics["close_position_in_range"]
    relative_move = metrics["relative_move_pct"]

    if today_change > 0:
        score += 10
        reasons.append("positive Tagesbewegung")
    if today_change >= 1.5:
        score += 12
        reasons.append("starke Intraday-Bewegung")
    if today_change >= 3.0:
        score += 8
        reasons.append("sehr starkes Momentum")

    if volume_factor >= 1.5:
        score += 18
        reasons.append("deutlich hoeheres Volumen")
    elif volume_factor >= 1.0:
        score += 10
        reasons.append("Volumen ueber Durchschnitt")

    if gap >= 1.0:
        score += 8
        reasons.append("Gap-Up oder starke Eröffnung")
    elif gap <= -2.0:
        score -= 8
        reasons.append("schwaches Gap-Down")

    if 45 <= rsi <= 72:
        score += 12
        reasons.append("RSI im handelbaren Momentum-Bereich")
    elif rsi > 80:
        score -= 8
        reasons.append("RSI kurzfristig ueberhitzt")
    elif rsi < 35:
        score -= 6
        reasons.append("RSI schwach")

    if adx >= 25:
        score += 12
        reasons.append("starker kurzfristiger Trend")
    elif adx >= 18:
        score += 6
        reasons.append("brauchbare Trendstaerke")

    if roc >= 1.0:
        score += 10
        reasons.append("positiver ROC")
    elif roc < -1.0:
        score -= 8
        reasons.append("negativer ROC")

    if distance_to_high <= 0.5 or close_position >= 85:
        score += 14
        reasons.append("nahe am Tageshoch")
    elif close_position >= 70:
        score += 7
        reasons.append("oberer Tagesbereich")

    if relative_move >= 1.5:
        score += 8
        reasons.append("starke relative Bewegung")

    score = max(0.0, min(score, 100.0))
    return score, _recommendation(score), reasons


def _recommendation(score: float) -> str:
    if score >= 80:
        return "🟢 Sehr stark"
    if score >= 70:
        return "🟢 Trade-Kandidat"
    if score >= 60:
        return "🟡 Beobachten"
    return "🔴 Kein Daytrade"


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


def _rsi(close: pd.Series, window: int = 14) -> float:
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(window).mean()
    losses = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gains / losses.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    value = rsi.iloc[-1]
    return float(value) if pd.notna(value) else 50.0


def _roc(close: pd.Series, window: int = 6) -> float:
    if len(close) <= window:
        return 0.0
    previous = float(close.iloc[-window - 1])
    return ((float(close.iloc[-1]) - previous) / previous) * 100 if previous else 0.0


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> float:
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    value = true_range.rolling(window).mean().iloc[-1]
    return float(value) if pd.notna(value) and value > 0 else max(float(close.iloc[-1]) * 0.005, 0.01)


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> float:
    previous_high = high.shift(1)
    previous_low = low.shift(1)
    up_move = high - previous_high
    down_move = previous_low - low
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    true_range = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_sum = true_range.rolling(window).sum()
    plus_di = 100 * plus_dm.rolling(window).sum() / atr_sum
    minus_di = 100 * minus_dm.rolling(window).sum() / atr_sum
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)) * 100
    value = dx.rolling(window).mean().iloc[-1]
    return float(value) if pd.notna(value) else 0.0


def _intraday_volatility(close: pd.Series, window: int = 20) -> float:
    value = close.pct_change().rolling(window).std().iloc[-1] * 100
    return float(value) if pd.notna(value) else 0.0
if __name__ == "__main__":
    df = scan_daytrading_market()

    if df.empty:
        print("Keine Daytrading-Kandidaten gefunden.")
    else:
        print("\nTop Daytrading-Kandidaten:\n")
        print(df.to_string(index=False))