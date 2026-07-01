from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.engine import BacktestEngine, BacktestResult
from tradingia.strategies.registry import StrategySpec


@dataclass
class StrategyLabResult:
    strategy_name: str
    result: BacktestResult

    @property
    def metrics(self) -> dict[str, float | str | int]:
        return {
            "strategy": self.strategy_name,
            "trades": len(self.result.trades),
            **self.result.metrics,
        }


class StrategyLab:
    def __init__(self, engine: BacktestEngine) -> None:
        self.engine = engine

    def run(self, bars: pd.DataFrame, strategy_specs: list[StrategySpec]) -> list[StrategyLabResult]:
        results: list[StrategyLabResult] = []

        for spec in strategy_specs:
            strategy = spec.create()
            result = self.engine.run(PandasBarFeed(bars), strategy)
            results.append(StrategyLabResult(spec.name, result))

        return results

    def leaderboard(self, results: list[StrategyLabResult]) -> pd.DataFrame:
        rows = [result.metrics for result in results]
        if not rows:
            return pd.DataFrame(columns=["strategy", "trades", "ending_equity", "total_return_pct", "max_drawdown_pct"])

        leaderboard = pd.DataFrame(rows)
        return leaderboard.sort_values(
            by=["total_return_pct", "max_drawdown_pct"],
            ascending=[False, False],
        ).reset_index(drop=True)
