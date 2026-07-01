"""Event-driven backtesting components for TradingIA."""

from tradingia.backtesting.engine import BacktestEngine
from tradingia.backtesting.events import BarEvent, FillEvent, OrderEvent, SignalEvent
from tradingia.backtesting.portfolio import Portfolio

__all__ = [
    "BacktestEngine",
    "BarEvent",
    "FillEvent",
    "OrderEvent",
    "Portfolio",
    "SignalEvent",
]
