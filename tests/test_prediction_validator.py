import json

import pandas as pd

from tradingia.validation import evaluate_recommendations, save_daily_recommendations


def test_save_daily_recommendations_writes_expected_csv(tmp_path):
    recommendations = pd.DataFrame(
        [
            {
                "Aktie": "AAPL",
                "TodayUpScore": 85,
                "FinalScore": 91,
                "Empfehlung": "Top Chance",
                "Einstieg": 100.0,
                "DayTradeScore": 88,
                "CatalystScore": 82,
                "NewsScore": 76,
            }
        ]
    )

    file_path = save_daily_recommendations(recommendations, tmp_path, recommendation_date="2026-07-04")

    saved = pd.read_csv(file_path)
    assert file_path.name == "recommendations_2026-07-04.csv"
    assert list(saved.columns) == ["Datum", "Aktie", "TodayUpScore", "FinalScore", "Empfehlung", "Einstiegskurs", "Teil-Scores"]
    assert saved.iloc[0]["Datum"] == "2026-07-04"
    assert saved.iloc[0]["Aktie"] == "AAPL"
    assert saved.iloc[0]["Einstiegskurs"] == 100.0
    partial_scores = json.loads(saved.iloc[0]["Teil-Scores"])
    assert partial_scores["DayTradeScore"] == 88.0
    assert partial_scores["NewsScore"] == 76.0


def test_evaluate_recommendations_calculates_performance_and_hits(tmp_path):
    recommendations = pd.DataFrame(
        [
            {"Aktie": "AAPL", "TodayUpScore": 85, "FinalScore": 90, "Empfehlung": "Top Chance", "Einstieg": 100.0},
            {"Aktie": "MSFT", "TodayUpScore": 60, "FinalScore": 72, "Empfehlung": "Beobachten", "Einstieg": 200.0},
        ]
    )
    file_path = save_daily_recommendations(recommendations, tmp_path, recommendation_date="2026-07-04")
    prices = pd.DataFrame(
        [
            {"Datum": "2026-07-05", "Aktie": "AAPL", "Close": 104.0},
            {"Datum": "2026-07-05", "Aktie": "MSFT", "Close": 196.0},
        ]
    )

    evaluated, metrics = evaluate_recommendations(file_path, prices, horizon_days=1)

    assert len(evaluated) == 2
    assert evaluated.loc[evaluated["Aktie"] == "AAPL", "Performance %"].iloc[0] == 4.0
    assert bool(evaluated.loc[evaluated["Aktie"] == "AAPL", "Treffer"].iloc[0]) is True
    assert evaluated.loc[evaluated["Aktie"] == "MSFT", "Performance %"].iloc[0] == -2.0
    assert metrics.total_recommendations == 2
    assert metrics.hit_rate == 0.5
    assert metrics.average_return_pct == 1.0
    assert metrics.average_gain_pct == 4.0
    assert metrics.average_loss_pct == -2.0
    assert metrics.best_score_threshold == 90.0


def test_evaluate_recommendations_handles_missing_future_price(tmp_path):
    recommendations = pd.DataFrame(
        [{"Aktie": "AAPL", "TodayUpScore": 85, "FinalScore": 90, "Empfehlung": "Top Chance", "Einstieg": 100.0}]
    )
    file_path = save_daily_recommendations(recommendations, tmp_path, recommendation_date="2026-07-04")
    prices = pd.DataFrame(columns=["Datum", "Aktie", "Close"])

    evaluated, metrics = evaluate_recommendations(file_path, prices)

    assert pd.isna(evaluated.iloc[0]["Performance %"])
    assert metrics.total_recommendations == 0
    assert metrics.best_score_threshold is None


def test_evaluate_recommendations_can_load_multiple_files(tmp_path):
    first = pd.DataFrame([{"Aktie": "AAPL", "TodayUpScore": 80, "FinalScore": 85, "Empfehlung": "Sehr interessant", "Einstieg": 100.0}])
    second = pd.DataFrame([{"Aktie": "NVDA", "TodayUpScore": 90, "FinalScore": 95, "Empfehlung": "Top Chance", "Einstieg": 50.0}])
    first_path = save_daily_recommendations(first, tmp_path, recommendation_date="2026-07-04")
    second_path = save_daily_recommendations(second, tmp_path, recommendation_date="2026-07-05")
    prices = pd.DataFrame(
        [
            {"Datum": "2026-07-05", "Aktie": "AAPL", "Close": 101.0},
            {"Datum": "2026-07-06", "Aktie": "NVDA", "Close": 55.0},
        ]
    )

    evaluated, metrics = evaluate_recommendations([first_path, second_path], prices)

    assert set(evaluated["Aktie"]) == {"AAPL", "NVDA"}
    assert metrics.total_recommendations == 2
    assert metrics.hit_rate == 1.0
