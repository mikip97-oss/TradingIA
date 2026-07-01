from __future__ import annotations

from tradingia.backtesting.events import BarEvent, SignalEvent


class BuyAndHoldStrategy:
    name = "buy_and_hold"

    def __init__(self, target_percent: float = 1.0) -> None:
        self.target_percent = target_percent
        self._invested: set[str] = set()

    def on_bar(self, bar: BarEvent) -> list[SignalEvent]:
        if bar.symbol in self._invested:
            return []

        self._invested.add(bar.symbol)
        return [
            SignalEvent(
                symbol=bar.symbol,
                timestamp=bar.timestamp,
                target_percent=self.target_percent,
                reason="initial buy-and-hold allocation",
            )
        ]
