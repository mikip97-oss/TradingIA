from datetime import datetime, timedelta

import pandas as pd

from tradingia.backtesting.engine import BacktestEngine
from tradingia.research.optimizer import ParameterOptimizer, build_parameter_grid, format_parameters
from tradingia.strategies.ema_crossover import EMACrossoverStrategy


def make_bars(prices):
    start = datetime(2024, 1, 1, 9, 30)
    rows = []
    for index, price in enumerate(prices):
        rows.append(
            {
                "symbol": "AAPL",
                "timestamp": start + timedelta(days=index),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1_000_000,
            }
        )
    return pd.DataFrame(rows)


def test_build_parameter_grid_creates_cartesian_product():
    grid = build_parameter_grid(
        {
            "short_window": [3, 5],
            "long_window": [8, 12],
            "target_percent": [0.5],
        }
    )

    assert grid == [
        {"short_window": 3, "long_window": 8, "target_percent": 0.5},
        {"short_window": 3, "long_window": 12, "target_percent": 0.5},
        {"short_window": 5, "long_window": 8, "target_percent": 0.5},
        {"short_window": 5, "long_window": 12, "target_percent": 0.5},
    ]


def test_parameter_optimizer_runs_each_combination_through_backtesting_engine():
    bars = make_bars([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111])
    optimizer = ParameterOptimizer(BacktestEngine(initial_cash=10_000))
    grid = build_parameter_grid({"short_window": [3, 4], "long_window": [6], "target_percent": [0.5]})

    results = optimizer.run(bars, "ema_crossover", EMACrossoverStrategy, grid)

    assert len(results) == 2
    assert [result.strategy_name for result in results] == ["ema_crossover", "ema_crossover"]
    assert all(result.result.metrics["ending_equity"] > 0 for result in results)
    assert all(result.parameters["long_window"] == 6 for result in results)


def test_parameter_optimizer_leaderboard_has_required_columns_and_sorted_results():
    bars = make_bars([100, 99, 101, 103, 105, 104, 106, 108, 111, 113, 112, 115])
    optimizer = ParameterOptimizer(BacktestEngine(initial_cash=10_000))
    grid = [
        {"short_window": 2, "long_window": 4, "target_percent": 0.25},
        {"short_window": 2, "long_window": 4, "target_percent": 0.75},
    ]

    leaderboard = optimizer.leaderboard(
        optimizer.run(bars, "ema_crossover", EMACrossoverStrategy, grid)
    )

    assert list(leaderboard.columns) == [
        "Strategie-Name",
        "Parameter",
        "Ending Equity",
        "Return %",
        "Max Drawdown %",
        "Anzahl Trades",
    ]
    assert leaderboard.iloc[0]["Return %"] >= leaderboard.iloc[1]["Return %"]
    assert set(leaderboard["Strategie-Name"]) == {"ema_crossover"}
    assert "short_window=2" in leaderboard.iloc[0]["Parameter"]


def test_parameter_optimizer_empty_leaderboard_is_stable():
    optimizer = ParameterOptimizer(BacktestEngine(initial_cash=10_000))

    leaderboard = optimizer.leaderboard([])

    assert leaderboard.empty
    assert list(leaderboard.columns) == [
        "Strategie-Name",
        "Parameter",
        "Ending Equity",
        "Return %",
        "Max Drawdown %",
        "Anzahl Trades",
    ]


def test_format_parameters_is_stable_and_readable():
    assert format_parameters({"long_window": 12, "short_window": 5}) == "long_window=12, short_window=5"
    assert format_parameters({}) == "{}"
