"""Reusable strategy implementations for TradingIA research."""

from tradingia.strategies.base import Strategy
from tradingia.strategies.breakout import BreakoutStrategy
from tradingia.strategies.buy_and_hold import BuyAndHoldStrategy
from tradingia.strategies.ema_crossover import EMACrossoverStrategy
from tradingia.strategies.rsi_reversion import RSIReversionStrategy

__all__ = [
    "BreakoutStrategy",
    "BuyAndHoldStrategy",
    "EMACrossoverStrategy",
    "RSIReversionStrategy",
    "Strategy",
]
