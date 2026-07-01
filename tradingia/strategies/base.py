from __future__ import annotations

from typing import Protocol

from tradingia.backtesting.events import BarEvent, SignalEvent


class Strategy(Protocol):
    name: str

    def on_bar(self, bar: BarEvent) -> list[SignalEvent]:
        """Return zero or more target-allocation signals for the latest market bar."""
