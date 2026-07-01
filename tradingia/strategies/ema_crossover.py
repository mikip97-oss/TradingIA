from __future__ import annotations

from dataclasses import dataclass, field

from tradingia.backtesting.events import BarEvent, SignalEvent


def _ema(previous: float | None, price: float, window: int) -> float:
    if previous is None:
        return price
    alpha = 2 / (window + 1)
    return (price * alpha) + (previous * (1 - alpha))


@dataclass
class EMACrossoverStrategy:
    short_window: int = 12
    long_window: int = 26
    target_percent: float = 1.0
    name: str = "ema_crossover"
    _short_ema: dict[str, float] = field(default_factory=dict)
    _long_ema: dict[str, float] = field(default_factory=dict)
    _is_long: dict[str, bool] = field(default_factory=dict)
    _observations: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("EMA windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be smaller than long_window")

    def on_bar(self, bar: BarEvent) -> list[SignalEvent]:
        symbol = bar.symbol
        self._observations[symbol] = self._observations.get(symbol, 0) + 1
        self._short_ema[symbol] = _ema(self._short_ema.get(symbol), bar.close, self.short_window)
        self._long_ema[symbol] = _ema(self._long_ema.get(symbol), bar.close, self.long_window)

        if self._observations[symbol] < self.long_window:
            return []

        bullish = self._short_ema[symbol] > self._long_ema[symbol]
        was_long = self._is_long.get(symbol, False)

        if bullish and not was_long:
            self._is_long[symbol] = True
            return [SignalEvent(symbol, bar.timestamp, self.target_percent, "short EMA crossed above long EMA")]

        if not bullish and was_long:
            self._is_long[symbol] = False
            return [SignalEvent(symbol, bar.timestamp, 0.0, "short EMA crossed below long EMA")]

        return []
