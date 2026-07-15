from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from tradingia.data import DataProvider, YahooFinanceProvider
from tradingia.ml_dataset.builder import DEFAULT_DATASET_PATH, PREDICTION_DATASET_COLUMNS

RETURN_COLUMNS = ["Return_1h", "Return_2h", "Return_EOD"]
HIT_COLUMNS = ["Treffer_1h", "Treffer_2h", "Treffer_EOD"]
LABEL_COLUMNS = RETURN_COLUMNS + HIT_COLUMNS

NUMERIC_DATASET_COLUMNS = [
    "Einstiegskurs",
    "FinalScore",
    "TodayUpScore",
    "TrendScore",
    "MomentumConfirmationScore",
    "DayTradeScore",
    "CatalystScore",
    "NewsScore",
    "TradeScore",
    "KI %",
    "RSI",
    "ADX",
    "ROC",
    "Volumen-Faktor",
    "Return_1h",
    "Return_2h",
    "Return_EOD",
]


@dataclass(frozen=True)
class LabelingSummary:
    rows_total: int
    rows_with_open_labels: int
    rows_updated: int


def label_prediction_dataset(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    *,
    data_provider: DataProvider | None = None,
    period: str = "5d",
    interval: str = "1m",
) -> tuple[pd.DataFrame, LabelingSummary]:
    """Fill missing return and hit labels in the prediction dataset CSV."""
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        empty = pd.DataFrame(columns=PREDICTION_DATASET_COLUMNS)
        return empty, LabelingSummary(rows_total=0, rows_with_open_labels=0, rows_updated=0)

    frame = _ensure_label_columns(pd.read_csv(dataset_path))
    provider = data_provider or YahooFinanceProvider()
    rows_with_open_labels = 0
    rows_updated = 0

    history_cache: dict[str, pd.DataFrame] = {}
    for index, row in frame.iterrows():
        if not _has_open_labels(row):
            continue

        rows_with_open_labels += 1
        ticker = str(row.get("Aktie", "")).strip().upper()
        signal_time = _signal_timestamp(row)
        if not ticker or signal_time is None:
            continue

        history = _history_for_ticker(ticker, provider, history_cache, period, interval)
        labels = calculate_labels_for_signal(row, history, signal_time)
        if not labels:
            continue

        updated = False
        for column, value in labels.items():
            if column in frame.columns and _is_empty(frame.at[index, column]):
                frame.at[index, column] = value
                updated = True

        if updated:
            rows_updated += 1

    frame = _ensure_label_columns(frame)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(dataset_path, index=False, encoding="utf-8")
    return frame, LabelingSummary(
        rows_total=len(frame),
        rows_with_open_labels=rows_with_open_labels,
        rows_updated=rows_updated,
    )


def calculate_labels_for_signal(row: pd.Series, history: pd.DataFrame, signal_time: pd.Timestamp) -> dict[str, float | int]:
    if history is None or history.empty or "Close" not in history.columns:
        return {}

    entry_price = _number_or_none(row.get("Einstiegskurs"))
    prepared_history = _prepare_history(history)
    if prepared_history.empty:
        return {}

    if entry_price is None:
        entry_price = _close_at_or_after(prepared_history, signal_time)
    if entry_price is None or entry_price <= 0:
        return {}

    labels: dict[str, float | int] = {}
    horizons = {
        "Return_1h": signal_time + pd.Timedelta(hours=1),
        "Return_2h": signal_time + pd.Timedelta(hours=2),
    }
    for column, target_time in horizons.items():
        close = _close_at_or_after(prepared_history, target_time)
        if close is not None:
            labels[column] = _return_pct(entry_price, close)

    eod_close = _eod_close(prepared_history, signal_time)
    if eod_close is not None:
        labels["Return_EOD"] = _return_pct(entry_price, eod_close)

    for return_column, hit_column in {
        "Return_1h": "Treffer_1h",
        "Return_2h": "Treffer_2h",
        "Return_EOD": "Treffer_EOD",
    }.items():
        existing_return = labels.get(return_column)
        if existing_return is None:
            existing_return = _number_or_none(row.get(return_column))
        if existing_return is not None:
            labels[hit_column] = int(existing_return > 0)

    return labels


def _ensure_label_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in PREDICTION_DATASET_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA if column in NUMERIC_DATASET_COLUMNS or column in HIT_COLUMNS else ""
    for column in LABEL_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    normalized = _coerce_dataset_dtypes(normalized)
    ordered_columns = list(dict.fromkeys(PREDICTION_DATASET_COLUMNS + LABEL_COLUMNS))
    return normalized[ordered_columns]


def _coerce_dataset_dtypes(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in NUMERIC_DATASET_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    for column in HIT_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce").astype("Int64")
    return normalized


def _has_open_labels(row: pd.Series) -> bool:
    return any(_is_empty(row.get(column)) for column in LABEL_COLUMNS)


def _history_for_ticker(
    ticker: str,
    provider: DataProvider,
    cache: dict[str, pd.DataFrame],
    period: str,
    interval: str,
) -> pd.DataFrame:
    if ticker not in cache:
        cache[ticker] = provider.get_history(ticker, period=period, interval=interval)
    return cache[ticker]


def _signal_timestamp(row: pd.Series) -> pd.Timestamp | None:
    date = str(row.get("Datum", "")).strip()
    time = str(row.get("Uhrzeit", "")).strip()
    if not date or not time:
        return None
    timestamp = pd.to_datetime(f"{date} {time}", errors="coerce")
    if pd.isna(timestamp):
        return None
    return pd.Timestamp(timestamp)


def _prepare_history(history: pd.DataFrame) -> pd.DataFrame:
    prepared = history.copy()
    if not isinstance(prepared.index, pd.DatetimeIndex):
        prepared.index = pd.to_datetime(prepared.index, errors="coerce")
    prepared = prepared[prepared.index.notna()]
    if getattr(prepared.index, "tz", None) is not None:
        prepared.index = prepared.index.tz_convert(None)
    prepared = prepared.sort_index()
    return prepared.dropna(subset=["Close"])


def _close_at_or_after(history: pd.DataFrame, timestamp: pd.Timestamp) -> float | None:
    matching = history.loc[history.index >= timestamp]
    if matching.empty:
        return None
    return _number_or_none(matching.iloc[0]["Close"])


def _eod_close(history: pd.DataFrame, signal_time: pd.Timestamp) -> float | None:
    same_day = history.loc[history.index.date == signal_time.date()]
    same_day = same_day.loc[same_day.index >= signal_time]
    if same_day.empty:
        return None
    return _number_or_none(same_day.iloc[-1]["Close"])


def _return_pct(entry_price: float, exit_price: float) -> float:
    return round(((exit_price - entry_price) / entry_price) * 100, 4)


def _number_or_none(value: Any) -> float | None:
    if _is_empty(value):
        return None
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return None
    return float(number)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        return False
    return str(value).strip() == ""
