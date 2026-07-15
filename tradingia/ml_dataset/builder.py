from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_DATASET_PATH = Path("data/prediction_dataset.csv")

FEATURE_COLUMNS = [
    "Datum",
    "Uhrzeit",
    "Aktie",
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
    "Empfehlung",
]

TARGET_COLUMNS = [
    "Return_1h",
    "Return_2h",
    "Return_EOD",
    "Treffer_1h",
    "Treffer_2h",
    "Treffer_EOD",
]

PREDICTION_DATASET_COLUMNS = FEATURE_COLUMNS + TARGET_COLUMNS

_DEDUPLICATION_COLUMNS = ["Datum", "Uhrzeit", "Aktie"]

_COLUMN_ALIASES = {
    "Aktie": ["Aktie", "Ticker", "Symbol"],
    "Einstiegskurs": ["Einstiegskurs", "Einstieg", "Entry", "EntryPrice", "Close", "Kurs", "Preis", "Last"],
    "FinalScore": ["FinalScore", "Final Score"],
    "TodayUpScore": ["TodayUpScore", "Today Up Score"],
    "TrendScore": ["TrendScore", "Trend Score"],
    "MomentumConfirmationScore": ["MomentumConfirmationScore", "Momentum Confirmation Score", "MomentumScore"],
    "DayTradeScore": ["DayTradeScore", "Day Trade Score"],
    "CatalystScore": ["CatalystScore", "Catalyst Score"],
    "NewsScore": ["NewsScore", "News Score"],
    "TradeScore": ["TradeScore", "Trade Score"],
    "KI %": ["KI %", "KI%", "AI %", "AI%", "KI", "AI"],
    "RSI": ["RSI"],
    "ADX": ["ADX"],
    "ROC": ["ROC"],
    "Volumen-Faktor": ["Volumen-Faktor", "Volumen Faktor", "Volume Factor", "VolumeFactor"],
    "Empfehlung": ["Empfehlung", "Recommendation"],
}

_NUMERIC_COLUMNS = {
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
}


def normalize_prediction_rows(scan_results: pd.DataFrame, timestamp: datetime | str | None = None) -> pd.DataFrame:
    """Normalize Intelligence scan rows into the persistent prediction dataset schema."""
    scan_results = _ensure_frame(scan_results)
    current_timestamp = _normalize_timestamp(timestamp)
    rows: list[dict[str, Any]] = []

    for _, source_row in scan_results.iterrows():
        ticker = _text_value(_value(source_row, "Aktie")).upper()
        if not ticker:
            continue

        row: dict[str, Any] = {
            "Datum": current_timestamp.strftime("%Y-%m-%d"),
            "Uhrzeit": current_timestamp.strftime("%H:%M:%S"),
            "Aktie": ticker,
            "Empfehlung": _text_value(_value(source_row, "Empfehlung")),
        }

        for column in _NUMERIC_COLUMNS:
            row[column] = _number_or_empty(_value(source_row, column))

        if row["MomentumConfirmationScore"] == "":
            row["MomentumConfirmationScore"] = row["TodayUpScore"]

        for target_column in TARGET_COLUMNS:
            row[target_column] = ""

        rows.append(row)

    return pd.DataFrame(rows, columns=PREDICTION_DATASET_COLUMNS)


def append_prediction_dataset(
    scan_results: pd.DataFrame,
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    *,
    timestamp: datetime | str | None = None,
) -> pd.DataFrame:
    """Append scan rows to the prediction dataset CSV and avoid duplicate signals."""
    dataset_path = Path(dataset_path)
    new_rows = normalize_prediction_rows(scan_results, timestamp=timestamp)
    existing_rows = _read_existing_dataset(dataset_path)

    if existing_rows.empty:
        combined = new_rows
    elif new_rows.empty:
        combined = existing_rows
    else:
        combined = pd.concat([existing_rows, new_rows], ignore_index=True)

    combined = _ensure_dataset_columns(combined)
    if not combined.empty:
        combined = combined.drop_duplicates(subset=_DEDUPLICATION_COLUMNS, keep="first").reset_index(drop=True)

    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(dataset_path, index=False, encoding="utf-8")
    return combined


def _ensure_frame(scan_results: pd.DataFrame) -> pd.DataFrame:
    if scan_results is None:
        return pd.DataFrame()
    if not isinstance(scan_results, pd.DataFrame):
        raise TypeError("scan_results must be a pandas DataFrame")
    return scan_results.copy()


def _read_existing_dataset(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        return pd.DataFrame(columns=PREDICTION_DATASET_COLUMNS)
    return _ensure_dataset_columns(pd.read_csv(dataset_path))


def _ensure_dataset_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in PREDICTION_DATASET_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    return normalized[PREDICTION_DATASET_COLUMNS]


def _normalize_timestamp(timestamp: datetime | str | None) -> datetime:
    if timestamp is None:
        return datetime.now()
    if isinstance(timestamp, datetime):
        return timestamp
    parsed = pd.to_datetime(timestamp)
    if pd.isna(parsed):
        raise ValueError(f"Invalid timestamp: {timestamp}")
    return parsed.to_pydatetime()


def _value(row: pd.Series, canonical_column: str) -> Any:
    for alias in _COLUMN_ALIASES.get(canonical_column, [canonical_column]):
        if alias in row.index:
            value = row.get(alias)
            if not _is_empty(value):
                return value
    return ""


def _number_or_empty(value: Any) -> float | str:
    if _is_empty(value):
        return ""
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return ""
    return float(number)


def _text_value(value: Any) -> str:
    if _is_empty(value):
        return ""
    return str(value).strip()


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        return False
    return str(value).strip() == ""
