from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.engine import BacktestEngine, BacktestResult
from tradingia.strategies.registry import StrategySpec


LEADERBOARD_COLUMNS = [
    "Strategie-Name",
    "Ending Equity",
    "Return %",
    "Max Drawdown %",
    "Anzahl Trades",
]


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

    def leaderboard_row(self) -> dict[str, float | str | int]:
        return {
            "Strategie-Name": self.strategy_name,
            "Ending Equity": self.result.metrics.get("ending_equity", 0.0),
            "Return %": self.result.metrics.get("total_return_pct", 0.0),
            "Max Drawdown %": self.result.metrics.get("max_drawdown_pct", 0.0),
            "Anzahl Trades": len(self.result.trades),
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
        rows = [result.leaderboard_row() for result in results]
        if not rows:
            return pd.DataFrame(columns=LEADERBOARD_COLUMNS)

        leaderboard = pd.DataFrame(rows, columns=LEADERBOARD_COLUMNS)
        return leaderboard.sort_values(
            by=["Return %", "Max Drawdown %", "Ending Equity"],
            ascending=[False, False, False],
        ).reset_index(drop=True)
