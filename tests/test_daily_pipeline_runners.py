import pandas as pd

import daily_intelligence_runner
import daily_labeling_runner
import performance_report


def test_daily_intelligence_runner_saves_pipeline_results(monkeypatch, tmp_path, capsys):
    dataset_path = tmp_path / "prediction_dataset.csv"
    output_dir = tmp_path / "daily"
    monkeypatch.setattr(daily_intelligence_runner, "lade_standard_universum", lambda: ["AAPL", "MSFT", "NVDA"])

    class FakePipeline:
        def run(self, tickers, max_workers=None):
            assert tickers == ["AAPL", "MSFT"]
            assert max_workers == 3
            return pd.DataFrame([{"Aktie": "AAPL", "FinalScore": 90, "Einstiegskurs": 100.0}, {"Aktie": "MSFT", "FinalScore": 70, "Einstiegskurs": 200.0}])

    monkeypatch.setattr(daily_intelligence_runner, "IntelligencePipeline", lambda: FakePipeline())
    exit_code = daily_intelligence_runner.main(["--universe-size", "2", "--max-workers", "3", "--top-candidates", "1", "--dataset-path", str(dataset_path), "--output-dir", str(output_dir)])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Gespeicherte Kandidaten: 1" in output
    saved = pd.read_csv(dataset_path)
    assert len(saved) == 1
    assert saved.loc[0, "Aktie"] == "AAPL"


def test_daily_labeling_runner_handles_missing_dataset(tmp_path, capsys):
    missing = tmp_path / "missing.csv"
    exit_code = daily_labeling_runner.main(["--dataset-path", str(missing)])
    assert exit_code == 0
    assert "Prediction-Dataset nicht gefunden" in capsys.readouterr().out


def test_daily_labeling_runner_prints_summary(monkeypatch, tmp_path, capsys):
    dataset_path = tmp_path / "prediction_dataset.csv"
    dataset_path.write_text("Aktie\nAAPL\n", encoding="utf-8")

    class Summary:
        rows_total = 3
        rows_updated = 2

    labeled = pd.DataFrame([{"Return_1h": 1.0, "Return_2h": 1.0, "Return_EOD": 1.0, "Treffer_1h": 1, "Treffer_2h": 1, "Treffer_EOD": 1}])
    monkeypatch.setattr(daily_labeling_runner, "label_prediction_dataset", lambda path: (labeled, Summary()))
    exit_code = daily_labeling_runner.main(["--dataset-path", str(dataset_path), "--output-dir", str(tmp_path)])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Geladene Zeilen: 3" in output
    assert "Neu gelabelte Zeilen: 2" in output


def test_performance_report_handles_missing_dataset(tmp_path, capsys):
    exit_code = performance_report.main(["--dataset-path", str(tmp_path / "missing.csv")])
    assert exit_code == 0
    assert "Prediction-Dataset nicht gefunden" in capsys.readouterr().out
