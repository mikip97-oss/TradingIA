from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import product
from typing import Any

import pandas as pd

from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.engine import BacktestEngine, BacktestResult
from tradingia.strategies.registry import StrategySpec


OPTIMIZER_LEADERBOARD_COLUMNS = [
    "Strategie-Name",
    "Parameter",
    "Ending Equity",
    "Return %",
    "Max Drawdown %",
    "Anzahl Trades",
]


@dataclass
class OptimizationResult:
    strategy_name: str
    parameters: dict[str, Any]
    result: BacktestResult

    def leaderboard_row(self) -> dict[str, float | str | int]:
        return {
            "Strategie-Name": self.strategy_name,
            "Parameter": format_parameters(self.parameters),
            "Ending Equity": self.result.metrics.get("ending_equity", 0.0),
            "Return %": self.result.metrics.get("total_return_pct", 0.0),
            "Max Drawdown %": self.result.metrics.get("max_drawdown_pct", 0.0),
            "Anzahl Trades": len(self.result.trades),
        }


class ParameterOptimizer:
    def __init__(self, engine: BacktestEngine) -> None:
        self.engine = engine

    def run(
        self,
        bars: pd.DataFrame,
        strategy_name: str,
        strategy_class,
        parameter_grid: Iterable[dict[str, Any]],
    ) -> list[OptimizationResult]:
        results: list[OptimizationResult] = []

        for parameters in parameter_grid:
            spec = StrategySpec(strategy_name, strategy_class, dict(parameters))
            strategy = spec.create()
            result = self.engine.run(PandasBarFeed(bars), strategy)
            results.append(OptimizationResult(strategy_name, dict(parameters), result))

        return results

    def leaderboard(self, results: list[OptimizationResult]) -> pd.DataFrame:
        rows = [result.leaderboard_row() for result in results]
        if not rows:
            return pd.DataFrame(columns=OPTIMIZER_LEADERBOARD_COLUMNS)

        leaderboard = pd.DataFrame(rows, columns=OPTIMIZER_LEADERBOARD_COLUMNS)
        return leaderboard.sort_values(
            by=["Return %", "Max Drawdown %", "Ending Equity"],
            ascending=[False, False, False],
        ).reset_index(drop=True)


def build_parameter_grid(parameters: dict[str, Iterable[Any]]) -> list[dict[str, Any]]:
    names = list(parameters.keys())
    values = [list(parameters[name]) for name in names]

    if not names:
        return [{}]

    return [dict(zip(names, combination)) for combination in product(*values)]


def format_parameters(parameters: dict[str, Any]) -> str:
    if not parameters:
        return "{}"

    return ", ".join(f"{name}={parameters[name]}" for name in sorted(parameters))
