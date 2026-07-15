import pandas as pd

from tradingia.performance_center import analyze_prediction_dataset, export_performance_report, load_prediction_dataset


def _synthetic_dataset(rows=24):
    data = []
    for index in range(rows):
        score = 45 + (index % 6) * 10
        return_eod = 1.5 if score >= 70 else -0.8
        data.append(
            {
                "Datum": f"2026-07-{(index % 5) + 1:02d}",
                "Uhrzeit": f"10:{index % 60:02d}:00",
                "Aktie": "AAPL" if index % 2 == 0 else "MSFT",
                "FinalScore": score,
                "TodayUpScore": score - 5,
                "TrendScore": score - 3,
                "MomentumConfirmationScore": score - 4,
                "DayTradeScore": score - 2,
                "CatalystScore": score - 1,
                "NewsScore": score - 6,
                "TradeScore": score - 7,
                "KI %": score - 8,
                "Return_1h": return_eod / 2,
                "Return_2h": return_eod * 0.75,
                "Return_EOD": return_eod,
                "Treffer_1h": int(return_eod > 0),
                "Treffer_2h": int(return_eod > 0),
                "Treffer_EOD": int(return_eod > 0),
            }
        )
    return pd.DataFrame(data)


def test_load_prediction_dataset_handles_missing_file(tmp_path):
    frame = load_prediction_dataset(tmp_path / "missing.csv")
    assert frame.empty


def test_load_prediction_dataset_handles_empty_file(tmp_path):
    dataset_path = tmp_path / "empty.csv"
    dataset_path.write_text("", encoding="utf-8")
    frame = load_prediction_dataset(dataset_path)
    assert frame.empty


def test_performance_summary_handles_partially_unlabeled_rows():
    frame = _synthetic_dataset(5)
    frame.loc[0, "Return_EOD"] = pd.NA
    frame.loc[0, "Treffer_EOD"] = pd.NA
    analysis = analyze_prediction_dataset(frame, min_labeled_rows=20)
    assert analysis.labeled_rows == 4
    assert analysis.is_statistically_reliable is False
    assert "Nein" in str(analysis.summary.loc[analysis.summary["Kennzahl"] == "Belastbare Aussage", "Wert"].iloc[0])


def test_score_bucket_calculation_and_hit_rates_are_correct():
    frame = pd.DataFrame(
        [
            {"FinalScore": 45, "Return_EOD": -1.0, "Treffer_EOD": 0, "Return_1h": -0.5, "Return_2h": -0.7, "Treffer_1h": 0, "Treffer_2h": 0},
            {"FinalScore": 75, "Return_EOD": 2.0, "Treffer_EOD": 1, "Return_1h": 1.0, "Return_2h": 1.5, "Treffer_1h": 1, "Treffer_2h": 1},
            {"FinalScore": 92, "Return_EOD": 3.0, "Treffer_EOD": 1, "Return_1h": 1.2, "Return_2h": 2.0, "Treffer_1h": 1, "Treffer_2h": 1},
        ]
    )
    analysis = analyze_prediction_dataset(frame, min_labeled_rows=1)
    bucket_70 = analysis.score_buckets.loc[analysis.score_buckets["Score-Bucket"] == "70-79"].iloc[0]
    bucket_90 = analysis.score_buckets.loc[analysis.score_buckets["Score-Bucket"] == "90-100"].iloc[0]
    assert bucket_70["Anzahl Signale"] == 1
    assert bucket_70["Trefferquote EOD %"] == 100.0
    assert bucket_90["Durchschnittsrendite EOD %"] == 3.0


def test_factor_analysis_ranks_useful_factors():
    analysis = analyze_prediction_dataset(_synthetic_dataset(24), min_labeled_rows=20)
    assert not analysis.factor_analysis.empty
    assert set(["Faktor", "Korrelation Return_EOD", "Trefferquote hoher Faktor %"]).issubset(analysis.factor_analysis.columns)
    assert analysis.is_statistically_reliable is True


def test_performance_exports_csv_and_html(tmp_path):
    dataset_path = tmp_path / "prediction_dataset.csv"
    output_dir = tmp_path / "reports"
    _synthetic_dataset(24).to_csv(dataset_path, index=False)
    analysis = export_performance_report(dataset_path, output_dir)
    assert analysis.labeled_rows == 24
    assert (output_dir / "summary.csv").exists()
    assert (output_dir / "score_buckets.csv").exists()
    assert (output_dir / "factor_analysis.csv").exists()
    assert (output_dir / "report.html").exists()
    assert "TradingIA Performance Center" in (output_dir / "report.html").read_text(encoding="utf-8")
