from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.engine import BacktestEngine, BacktestResult
from tradingia.regime import MarketRegime, MarketRegimeEngine
from tradingia.strategies.registry import StrategySpec


LEADERBOARD_COLUMNS = [
    "Strategie-Name",
    "Regime",
    "Ending Equity",
    "Return %",
    "Max Drawdown %",
    "Anzahl Trades",
]

DEFAULT_REGIME_STRATEGY_MAP = {
    MarketRegime.BULL: {"buy_and_hold", "ema_crossover", "breakout"},
    MarketRegime.BEAR: {"rsi_reversion"},
    MarketRegime.SIDEWAYS: {"rsi_reversion", "breakout"},
}


@dataclass
class StrategyLabResult:
    strategy_name: str
    result: BacktestResult
    regime: str = "unknown"

    @property
    def metrics(self) -> dict[str, float | str | int]:
        return {
            "strategy": self.strategy_name,
            "regime": self.regime,
            "trades": len(self.result.trades),
            **self.result.metrics,
        }

    def leaderboard_row(self) -> dict[str, float | str | int]:
        return {
            "Strategie-Name": self.strategy_name,
            "Regime": self.regime,
            "Ending Equity": self.result.metrics.get("ending_equity", 0.0),
            "Return %": self.result.metrics.get("total_return_pct", 0.0),
            "Max Drawdown %": self.result.metrics.get("max_drawdown_pct", 0.0),
            "Anzahl Trades": len(self.result.trades),
        }


class StrategyLab:
    def __init__(self, engine: BacktestEngine) -> None:
        self.engine = engine

    def run(
        self,
        bars: pd.DataFrame,
        strategy_specs: list[StrategySpec],
        regime_engine: MarketRegimeEngine | None = None,
        regime_strategy_map: dict[MarketRegime, set[str]] | None = None,
    ) -> list[StrategyLabResult]:
        regime = self._detect_regime(bars, regime_engine) if regime_engine else None
        selected_specs = self._select_strategy_specs(strategy_specs, regime, regime_strategy_map)
        regime_label = regime.value if regime else "unknown"
        results: list[StrategyLabResult] = []

        for spec in selected_specs:
            strategy = spec.create()
            result = self.engine.run(PandasBarFeed(bars), strategy)
            results.append(StrategyLabResult(spec.name, result, regime_label))

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

    def _detect_regime(self, bars: pd.DataFrame, regime_engine: MarketRegimeEngine) -> MarketRegime:
        snapshots = regime_engine.classify_many(bars)
        regimes = {snapshot.regime for snapshot in snapshots.values()}
        if len(regimes) == 1:
            return regimes.pop()

        return MarketRegime.SIDEWAYS

    def _select_strategy_specs(
        self,
        strategy_specs: list[StrategySpec],
        regime: MarketRegime | None,
        regime_strategy_map: dict[MarketRegime, set[str]] | None,
    ) -> list[StrategySpec]:
        if regime is None:
            return strategy_specs

        allowed_names = (regime_strategy_map or DEFAULT_REGIME_STRATEGY_MAP).get(regime)
        if not allowed_names:
            return strategy_specs

        return [spec for spec in strategy_specs if spec.name in allowed_names]
