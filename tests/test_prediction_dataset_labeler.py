import pandas as pd

from tradingia.ml_dataset import append_prediction_dataset, label_prediction_dataset


class FakeDataProvider:
    name = "fake"

    def __init__(self, histories):
        self.histories = histories
        self.calls = []

    def get_history(self, ticker, period, interval):
        self.calls.append((ticker, period, interval))
        return self.histories.get(ticker, pd.DataFrame())


def _history():
    index = pd.to_datetime(
        [
            "2026-07-04 09:30:00",
            "2026-07-04 10:30:00",
            "2026-07-04 11:30:00",
            "2026-07-04 15:59:00",
        ]
    )
    return pd.DataFrame(
        {
            "Open": [100, 101, 102, 103],
            "High": [101, 103, 104, 106],
            "Low": [99, 100, 101, 102],
            "Close": [100, 102, 101, 105],
            "Volume": [1000, 1200, 1300, 1500],
        },
        index=index,
    )


def test_label_prediction_dataset_fills_missing_returns_and_hits(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"
    append_prediction_dataset(
        pd.DataFrame([{"Aktie": "AAPL", "Einstiegskurs": 100.0, "FinalScore": 80}]),
        dataset_path,
        timestamp="2026-07-04 09:30:00",
    )
    provider = FakeDataProvider({"AAPL": _history()})

    labeled, summary = label_prediction_dataset(dataset_path, data_provider=provider)

    assert summary.rows_total == 1
    assert summary.rows_with_open_labels == 1
    assert summary.rows_updated == 1
    assert labeled.loc[0, "Return_1h"] == 2.0
    assert labeled.loc[0, "Return_2h"] == 1.0
    assert labeled.loc[0, "Return_EOD"] == 5.0
    assert labeled.loc[0, "Treffer_1h"] == 1
    assert labeled.loc[0, "Treffer_2h"] == 1
    assert labeled.loc[0, "Treffer_EOD"] == 1
    assert provider.calls == [("AAPL", "5d", "1m")]


def test_label_prediction_dataset_does_not_overwrite_existing_labels(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"
    frame = pd.DataFrame(
        [
            {
                "Datum": "2026-07-04",
                "Uhrzeit": "09:30:00",
                "Aktie": "AAPL",
                "Einstiegskurs": 100.0,
                "Return_1h": 9.9,
                "Return_2h": "",
                "Return_EOD": "",
                "Treffer_1h": 1,
                "Treffer_2h": "",
                "Treffer_EOD": "",
            }
        ]
    )
    frame.to_csv(dataset_path, index=False)
    provider = FakeDataProvider({"AAPL": _history()})

    labeled, summary = label_prediction_dataset(dataset_path, data_provider=provider)

    assert summary.rows_updated == 1
    assert labeled.loc[0, "Return_1h"] == 9.9
    assert labeled.loc[0, "Treffer_1h"] == 1
    assert labeled.loc[0, "Return_2h"] == 1.0
    assert labeled.loc[0, "Return_EOD"] == 5.0


def test_label_prediction_dataset_uses_first_close_when_entry_price_is_missing(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"
    frame = pd.DataFrame([{"Datum": "2026-07-04", "Uhrzeit": "09:30:00", "Aktie": "AAPL"}])
    frame.to_csv(dataset_path, index=False)

    labeled, _ = label_prediction_dataset(dataset_path, data_provider=FakeDataProvider({"AAPL": _history()}))

    assert labeled.loc[0, "Return_1h"] == 2.0
    assert labeled.loc[0, "Treffer_1h"] == 1


def test_label_prediction_dataset_handles_missing_dataset(tmp_path):
    dataset_path = tmp_path / "missing.csv"

    labeled, summary = label_prediction_dataset(dataset_path, data_provider=FakeDataProvider({}))

    assert labeled.empty
    assert summary.rows_total == 0
    assert summary.rows_updated == 0
