from datetime import datetime

import pandas as pd

from tradingia.ml_dataset import PREDICTION_DATASET_COLUMNS, TARGET_COLUMNS, append_prediction_dataset, normalize_prediction_rows


def test_normalize_prediction_rows_creates_expected_columns():
    scan_results = pd.DataFrame(
        [
            {
                "Aktie": "aapl",
                "Einstieg": 210.5,
                "FinalScore": 84,
                "TodayUpScore": 72,
                "TrendScore": 88,
                "DayTradeScore": 69,
                "CatalystScore": 61,
                "NewsScore": 75,
                "TradeScore": 55,
                "KI %": 63,
                "RSI": 58,
                "ADX": 27,
                "ROC": 2.4,
                "Volumen-Faktor": 1.8,
                "Empfehlung": "Beobachten",
            }
        ]
    )

    normalized = normalize_prediction_rows(scan_results, timestamp=datetime(2026, 7, 4, 10, 30, 5))

    assert list(normalized.columns) == PREDICTION_DATASET_COLUMNS
    assert normalized.loc[0, "Datum"] == "2026-07-04"
    assert normalized.loc[0, "Uhrzeit"] == "10:30:05"
    assert normalized.loc[0, "Aktie"] == "AAPL"
    assert normalized.loc[0, "Einstiegskurs"] == 210.5
    assert normalized.loc[0, "MomentumConfirmationScore"] == 72.0
    assert normalized.loc[0, "Empfehlung"] == "Beobachten"
    for column in TARGET_COLUMNS:
        assert pd.isna(normalized.loc[0, column])


def test_append_prediction_dataset_writes_csv_and_deduplicates(tmp_path):
    dataset_path = tmp_path / "data" / "prediction_dataset.csv"
    scan_results = pd.DataFrame([{"Aktie": "MSFT", "FinalScore": 78, "Empfehlung": "Beobachten"}])

    append_prediction_dataset(scan_results, dataset_path, timestamp="2026-07-04 11:00:00")
    combined = append_prediction_dataset(scan_results, dataset_path, timestamp="2026-07-04 11:00:00")

    saved = pd.read_csv(dataset_path)
    assert len(combined) == 1
    assert len(saved) == 1
    assert saved.loc[0, "Aktie"] == "MSFT"


def test_append_prediction_dataset_allows_same_ticker_at_different_times(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"
    scan_results = pd.DataFrame([{"Aktie": "NVDA", "FinalScore": 91}])

    append_prediction_dataset(scan_results, dataset_path, timestamp="2026-07-04 09:35:00")
    combined = append_prediction_dataset(scan_results, dataset_path, timestamp="2026-07-04 09:36:00")

    assert len(combined) == 2
    assert set(combined["Uhrzeit"]) == {"09:35:00", "09:36:00"}


def test_append_prediction_dataset_adds_new_rows_to_existing_file(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"

    append_prediction_dataset(pd.DataFrame([{"Aktie": "AAPL", "FinalScore": 80}]), dataset_path, timestamp="2026-07-04 09:30:00")
    combined = append_prediction_dataset(pd.DataFrame([{"Aktie": "TSLA", "FinalScore": 70}]), dataset_path, timestamp="2026-07-04 09:30:00")

    assert list(combined["Aktie"]) == ["AAPL", "TSLA"]


def test_normalize_prediction_rows_uses_nan_for_missing_numeric_values():
    normalized = normalize_prediction_rows(
        pd.DataFrame([{"Aktie": "AAPL", "FinalScore": 80, "Empfehlung": "Kein Trade"}]),
        timestamp="2026-07-04 10:30:00",
    )

    assert pd.isna(normalized.loc[0, "Einstiegskurs"])
    assert pd.isna(normalized.loc[0, "RSI"])
    assert pd.isna(normalized.loc[0, "ADX"])
    assert pd.isna(normalized.loc[0, "ROC"])
    assert pd.isna(normalized.loc[0, "Volumen-Faktor"])
    assert normalized.loc[0, "FinalScore"] == 80.0
    assert normalized.loc[0, "Empfehlung"] == "Kein Trade"


def test_append_prediction_dataset_keeps_numeric_scores_and_existing_fields(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"
    scan_results = pd.DataFrame(
        [
            {
                "Aktie": "AAPL",
                "Einstiegskurs": 210.25,
                "FinalScore": 88,
                "TodayUpScore": 74,
                "TrendScore": 69,
                "MomentumConfirmationScore": 74,
                "DayTradeScore": 71,
                "CatalystScore": 65,
                "NewsScore": 55,
                "TradeScore": 62,
                "KI %": 58,
                "RSI": 61.5,
                "ADX": 24.0,
                "ROC": 1.7,
                "Volumen-Faktor": 1.45,
                "Empfehlung": "Kein Trade",
            }
        ]
    )

    combined = append_prediction_dataset(scan_results, dataset_path, timestamp="2026-07-04 10:30:00")
    saved = pd.read_csv(dataset_path)

    assert combined.loc[0, "Einstiegskurs"] == 210.25
    assert saved.loc[0, "Einstiegskurs"] == 210.25
    assert saved.loc[0, "TradeScore"] == 62.0
    assert saved.loc[0, "KI %"] == 58.0
    assert saved.loc[0, "RSI"] == 61.5
    assert saved.loc[0, "ADX"] == 24.0
    assert saved.loc[0, "ROC"] == 1.7
    assert saved.loc[0, "Volumen-Faktor"] == 1.45
    assert saved.loc[0, "Empfehlung"] == "Kein Trade"
