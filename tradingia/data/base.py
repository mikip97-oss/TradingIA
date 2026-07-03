from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass(frozen=True)
class DataProviderError(Exception):
    provider: str
    ticker: str
    message: str

    def __str__(self) -> str:
        return f"{self.provider} failed for {self.ticker}: {self.message}"


class DataProvider(Protocol):
    name: str

    def get_history(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        """Return historical OHLCV data or an empty DataFrame when data is unavailable."""


def empty_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=OHLCV_COLUMNS)
