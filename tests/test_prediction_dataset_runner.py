from pathlib import Path

import pandas as pd

import label_prediction_dataset as runner


def test_count_open_label_rows_counts_rows_with_missing_labels():
    frame = pd.DataFrame(
        [
            {
                "Return_1h": 1.0,
                "Return_2h": 2.0,
                "Return_EOD": 3.0,
                "Treffer_1h": 1,
                "Treffer_2h": 1,
                "Treffer_EOD": 1,
            },
            {
                "Return_1h": 1.0,
                "Return_2h": pd.NA,
                "Return_EOD": 3.0,
                "Treffer_1h": 1,
                "Treffer_2h": pd.NA,
                "Treffer_EOD": 1,
            },
        ]
    )

    assert runner.count_open_label_rows(frame) == 1


def test_runner_handles_missing_dataset_without_traceback(tmp_path, capsys):
    missing_path = tmp_path / "missing.csv"

    exit_code = runner.main(["--dataset-path", str(missing_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Prediction-Dataset nicht gefunden" in output
    assert str(missing_path) in output


def test_runner_prints_labeling_summary(monkeypatch, tmp_path, capsys):
    dataset_path = tmp_path / "prediction_dataset.csv"
    dataset_path.write_text("Aktie\nAAPL\n", encoding="utf-8")

    class Summary:
        rows_total = 2
        rows_updated = 1

    labeled = pd.DataFrame(
        [
            {
                "Return_1h": 1.0,
                "Return_2h": 2.0,
                "Return_EOD": 3.0,
                "Treffer_1h": 1,
                "Treffer_2h": 1,
                "Treffer_EOD": 1,
            },
            {
                "Return_1h": pd.NA,
                "Return_2h": pd.NA,
                "Return_EOD": pd.NA,
                "Treffer_1h": pd.NA,
                "Treffer_2h": pd.NA,
                "Treffer_EOD": pd.NA,
            },
        ]
    )
    monkeypatch.setattr(runner, "label_prediction_dataset", lambda path: (labeled, Summary()))

    exit_code = runner.main(["--dataset-path", str(dataset_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Geladene Zeilen: 2" in output
    assert "Neu gelabelte Zeilen: 1" in output
    assert "Weiterhin offene Zeilen: 1" in output
    assert f"Speicherpfad: {dataset_path}" in output


def test_runner_returns_error_when_labeler_fails(monkeypatch, tmp_path, capsys):
    dataset_path = tmp_path / "prediction_dataset.csv"
    dataset_path.write_text("Aktie\nAAPL\n", encoding="utf-8")

    def broken_labeler(path):
        raise RuntimeError("kaputte Daten")

    monkeypatch.setattr(runner, "label_prediction_dataset", broken_labeler)

    exit_code = runner.main(["--dataset-path", str(dataset_path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Prediction-Dataset konnte nicht gelabelt werden" in output
    assert "kaputte Daten" in output
