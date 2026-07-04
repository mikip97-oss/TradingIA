from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

RECOMMENDATION_COLUMNS = [
    "Datum",
    "Aktie",
    "TodayUpScore",
    "FinalScore",
    "Empfehlung",
    "Einstiegskurs",
    "Teil-Scores",
]

PARTIAL_SCORE_COLUMNS = [
    "DayTradeScore",
    "CatalystScore",
    "NewsScore",
    "TradeScore",
    "KI %",
    "OverextensionPenalty",
]


def save_daily_recommendations(
    recommendations: pd.DataFrame,
    output_dir: str | Path,
    *,
    recommendation_date: date | datetime | str | None = None,
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    day = _normalize_date(recommendation_date)
    file_path = output_path / f"recommendations_{day}.csv"

    frame = normalize_recommendations(recommendations, day)
    frame.to_csv(file_path, index=False, encoding="utf-8")
    return file_path


def normalize_recommendations(recommendations: pd.DataFrame, recommendation_date: str) -> pd.DataFrame:
    rows = []
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)

    for _, row in recommendations.iterrows():
        row_dict = row.to_dict()
        rows.append(
            {
                "Datum": recommendation_date,
                "Aktie": str(row_dict.get("Aktie", "")).upper(),
                "TodayUpScore": _number_or_empty(row_dict.get("TodayUpScore")),
                "FinalScore": _number_or_empty(row_dict.get("FinalScore")),
                "Empfehlung": str(row_dict.get("Empfehlung", "")),
                "Einstiegskurs": _entry_price(row_dict),
                "Teil-Scores": _partial_scores(row_dict),
            }
        )

    return pd.DataFrame(rows, columns=RECOMMENDATION_COLUMNS)


def _normalize_date(value: date | datetime | str | None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _entry_price(row: dict) -> float | str:
    for column in ["Einstiegskurs", "Einstieg", "Close", "Last", "Preis"]:
        value = _number_or_empty(row.get(column))
        if value != "":
            return value
    return ""


def _partial_scores(row: dict) -> str:
    scores = {}
    for column in PARTIAL_SCORE_COLUMNS:
        value = _number_or_empty(row.get(column))
        if value != "":
            scores[column] = value
    return json.dumps(scores, ensure_ascii=False, sort_keys=True)


def _number_or_empty(value) -> float | str:
    if value in (None, ""):
        return ""
    try:
        if pd.isna(value):
            return ""
        return round(float(value), 4)
    except (TypeError, ValueError):
        return ""
