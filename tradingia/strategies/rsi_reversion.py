from __future__ import annotations

from dataclasses import dataclass, field

from tradingia.backtesting.events import BarEvent, SignalEvent


def _calculate_rsi(closes: list[float], window: int) -> float | None:
    if len(closes) <= window:
        return None

    changes = [closes[index] - closes[index - 1] for index in range(len(closes) - window, len(closes))]
    gains = [change for change in changes if change > 0]
    losses = [-change for change in changes if change < 0]
    average_gain = sum(gains) / window
    average_loss = sum(losses) / window

    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


@dataclass
class RSIReversionStrategy:
    window: int = 14
    oversold: float = 30.0
    exit_rsi: float = 50.0
    target_percent: float = 1.0
    name: str = "rsi_reversion"
    _closes: dict[str, list[float]] = field(default_factory=dict)
    _is_long: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError("RSI window must be positive")
        if self.oversold >= self.exit_rsi:
            raise ValueError("oversold must be lower than exit_rsi")

    def on_bar(self, bar: BarEvent) -> list[SignalEvent]:
        closes = self._closes.setdefault(bar.symbol, [])
        closes.append(bar.close)
        rsi = _calculate_rsi(closes, self.window)

        if rsi is None:
            return []

        is_long = self._is_long.get(bar.symbol, False)
        if rsi <= self.oversold and not is_long:
            self._is_long[bar.symbol] = True
            return [SignalEvent(bar.symbol, bar.timestamp, self.target_percent, f"RSI reversion entry at {rsi:.2f}")]

        if rsi >= self.exit_rsi and is_long:
            self._is_long[bar.symbol] = False
            return [SignalEvent(bar.symbol, bar.timestamp, 0.0, f"RSI reversion exit at {rsi:.2f}")]

        return []
