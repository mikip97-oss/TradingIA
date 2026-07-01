from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tradingia.strategies.base import Strategy
from tradingia.strategies.breakout import BreakoutStrategy
from tradingia.strategies.buy_and_hold import BuyAndHoldStrategy
from tradingia.strategies.ema_crossover import EMACrossoverStrategy
from tradingia.strategies.rsi_reversion import RSIReversionStrategy


@dataclass(frozen=True)
class StrategySpec:
    name: str
    strategy_class: type[Strategy]
    parameters: dict[str, Any] = field(default_factory=dict)

    def create(self) -> Strategy:
        return self.strategy_class(**self.parameters)


def default_strategy_specs() -> list[StrategySpec]:
    return [
        StrategySpec("buy_and_hold", BuyAndHoldStrategy, {"target_percent": 1.0}),
        StrategySpec("ema_crossover", EMACrossoverStrategy, {"short_window": 5, "long_window": 12, "target_percent": 1.0}),
        StrategySpec("rsi_reversion", RSIReversionStrategy, {"window": 5, "oversold": 35.0, "exit_rsi": 55.0}),
        StrategySpec("breakout", BreakoutStrategy, {"lookback": 10, "target_percent": 1.0}),
    ]
