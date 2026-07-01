from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.engine import BacktestEngine, BacktestResult
from tradingia.backtesting.strategy import Strategy


@dataclass(frozen=True)
class WalkForwardSplit:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


@dataclass
class WalkForwardResult:
    split: WalkForwardSplit
    result: BacktestResult


def build_walk_forward_splits(
    bars: pd.DataFrame,
    train_size: int,
    test_size: int,
    step_size: int | None = None,
) -> list[WalkForwardSplit]:
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")

    step = step_size or test_size
    dates = pd.Series(pd.to_datetime(bars["timestamp"]).dt.normalize().unique()).sort_values().reset_index(drop=True)
    splits: list[WalkForwardSplit] = []

    start = 0
    while start + train_size + test_size <= len(dates):
        train_dates = dates.iloc[start : start + train_size]
        test_dates = dates.iloc[start + train_size : start + train_size + test_size]
        splits.append(
            WalkForwardSplit(
                train_start=train_dates.iloc[0],
                train_end=train_dates.iloc[-1],
                test_start=test_dates.iloc[0],
                test_end=test_dates.iloc[-1],
            )
        )
        start += step

    return splits


class WalkForwardRunner:
    def __init__(self, engine: BacktestEngine) -> None:
        self.engine = engine

    def run(
        self,
        bars: pd.DataFrame,
        strategy_factory: Callable[[pd.DataFrame], Strategy],
        train_size: int,
        test_size: int,
        step_size: int | None = None,
    ) -> list[WalkForwardResult]:
        splits = build_walk_forward_splits(bars, train_size, test_size, step_size)
        results: list[WalkForwardResult] = []
        all_bars = bars.copy()
        all_bars["timestamp"] = pd.to_datetime(all_bars["timestamp"])

        for split in splits:
            train = all_bars[
                (all_bars["timestamp"] >= split.train_start)
                & (all_bars["timestamp"] < split.train_end + pd.Timedelta(days=1))
            ]
            test = all_bars[
                (all_bars["timestamp"] >= split.test_start)
                & (all_bars["timestamp"] < split.test_end + pd.Timedelta(days=1))
            ]
            strategy = strategy_factory(train)
            result = self.engine.run(PandasBarFeed(test), strategy)
            results.append(WalkForwardResult(split, result))

        return results
