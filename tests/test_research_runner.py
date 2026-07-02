from datetime import datetime

import pandas as pd

from research_runner import build_ema_parameter_grid, generate_sample_bars, run_research


def test_generate_sample_bars_returns_required_columns():
    bars = generate_sample_bars(symbol="MSFT", days=20)

    assert list(bars.columns) == ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    assert len(bars) == 20
    assert set(bars["symbol"]) == {"MSFT"}
    assert pd.api.types.is_datetime64_any_dtype(pd.to_datetime(bars["timestamp"]))


def test_build_ema_parameter_grid_returns_only_valid_combinations():
    grid = build_ema_parameter_grid()

    assert grid
    assert all(parameters["short_window"] < parameters["long_window"] for parameters in grid)
    assert all("target_percent" in parameters for parameters in grid)


def test_run_research_builds_leaderboards_and_exports_reports(tmp_path):
    result = run_research(output_dir=tmp_path, generated_at=datetime(2024, 1, 10, 12, 0, 0))

    assert not result.strategy_leaderboard.empty
    assert not result.optimizer_leaderboard.empty
    assert list(result.optimizer_leaderboard.columns) == [
        "Strategie-Name",
        "Parameter",
        "Ending Equity",
        "Return %",
        "Max Drawdown %",
        "Anzahl Trades",
    ]
    assert result.reports
    assert all(report.output_paths["html_report"].exists() for report in result.reports)
    assert all(report.output_paths["metrics_csv"].exists() for report in result.reports)
