from datetime import datetime, timedelta

import pandas as pd

from tradingia.backtesting.costs import TransactionCostModel
from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.engine import BacktestEngine
from tradingia.backtesting.strategy import BuyAndHoldStrategy
from tradingia.research.walk_forward import WalkForwardRunner, build_walk_forward_splits


def sample_bars(days=6):
    start = datetime(2024, 1, 1, 9, 30)
    rows = []
    for day in range(days):
        price = 100 + day
        rows.append(
            {
                "symbol": "AAPL",
                "timestamp": start + timedelta(days=day),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1_000_000,
            }
        )
    return pd.DataFrame(rows)


def test_event_driven_backtest_applies_costs_and_tracks_equity():
    engine = BacktestEngine(
        initial_cash=10_000,
        costs=TransactionCostModel(commission_per_share=0.01, minimum_commission=1.0, slippage_bps=10),
    )

    result = engine.run(PandasBarFeed(sample_bars()), BuyAndHoldStrategy(target_percent=0.5))

    assert len(result.trades) == 1
    assert result.trades[0]["side"] == "BUY"
    assert result.trades[0]["commission"] >= 1.0
    assert result.metrics["ending_equity"] > 10_000
    assert "max_drawdown_pct" in result.metrics


def test_walk_forward_splits_use_train_then_test_windows():
    bars = sample_bars(days=8)

    splits = build_walk_forward_splits(bars, train_size=3, test_size=2, step_size=2)

    assert len(splits) == 2
    assert splits[0].train_start == pd.Timestamp("2024-01-01")
    assert splits[0].train_end == pd.Timestamp("2024-01-03")
    assert splits[0].test_start == pd.Timestamp("2024-01-04")
    assert splits[0].test_end == pd.Timestamp("2024-01-05")


def test_walk_forward_runner_backtests_each_test_window():
    bars = sample_bars(days=8)
    runner = WalkForwardRunner(BacktestEngine(initial_cash=10_000))

    results = runner.run(
        bars,
        strategy_factory=lambda train: BuyAndHoldStrategy(target_percent=0.25),
        train_size=3,
        test_size=2,
        step_size=2,
    )

    assert len(results) == 2
    assert all(result.result.trades for result in results)
