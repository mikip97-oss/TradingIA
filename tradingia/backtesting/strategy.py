from typing import Protocol

from tradingia.backtesting.events import SignalEvent


class Strategy(Protocol):
    def on_bar(self, event) -> list[SignalEvent]:
        pass


class BuyAndHoldStrategy:
    def __init__(self, target_percent: float = 1.0):
        self.target_percent = target_percent
        self.has_bought = False

    def on_bar(self, event) -> list[SignalEvent]:
        if self.has_bought:
            return []

        self.has_bought = True

        return [
            SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                target_percent=self.target_percent,
                reason="Buy and hold",
            )
        ]