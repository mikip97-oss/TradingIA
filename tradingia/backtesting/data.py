from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pandas as pd

from tradingia.backtesting.events import BarEvent


REQUIRED_COLUMNS = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}


@dataclass
class PandasBarFeed:
    bars: pd.DataFrame

    def __post_init__(self) -> None:
        missing = REQUIRED_COLUMNS.difference(self.bars.columns)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"Bar feed is missing required columns: {names}")

        self.bars = self.bars.copy()
        self.bars["timestamp"] = pd.to_datetime(self.bars["timestamp"])
        self.bars = self.bars.sort_values(["timestamp", "symbol"]).reset_index(drop=True)

    def __iter__(self) -> Iterator[BarEvent]:
        for row in self.bars.itertuples(index=False):
            yield BarEvent(
                symbol=str(row.symbol),
                timestamp=row.timestamp.to_pydatetime(),
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
