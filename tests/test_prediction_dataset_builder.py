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
        assert normalized.loc[0, column] == ""


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
