from __future__ import annotations

from dataclasses import dataclass, field

from tradingia.backtesting.events import BarEvent, SignalEvent


@dataclass
class BreakoutStrategy:
    lookback: int = 20
    target_percent: float = 1.0
    exit_on_breakdown: bool = True
    name: str = "breakout"
    _highs: dict[str, list[float]] = field(default_factory=dict)
    _lows: dict[str, list[float]] = field(default_factory=dict)
    _is_long: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.lookback <= 1:
            raise ValueError("lookback must be greater than one")

    def on_bar(self, bar: BarEvent) -> list[SignalEvent]:
        highs = self._highs.setdefault(bar.symbol, [])
        lows = self._lows.setdefault(bar.symbol, [])

        previous_highs = highs[-self.lookback :]
        previous_lows = lows[-self.lookback :]
        highs.append(bar.high)
        lows.append(bar.low)

        if len(previous_highs) < self.lookback:
            return []

        breakout_level = max(previous_highs)
        breakdown_level = min(previous_lows)
        is_long = self._is_long.get(bar.symbol, False)

        if bar.close > breakout_level and not is_long:
            self._is_long[bar.symbol] = True
            return [SignalEvent(bar.symbol, bar.timestamp, self.target_percent, "close broke above lookback high")]

        if self.exit_on_breakdown and bar.close < breakdown_level and is_long:
            self._is_long[bar.symbol] = False
            return [SignalEvent(bar.symbol, bar.timestamp, 0.0, "close broke below lookback low")]

        return []
