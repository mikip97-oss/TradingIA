from __future__ import annotations

import pandas as pd
import yfinance as yf

from tradingia.data.base import DataProviderError, empty_ohlcv_frame


class YahooFinanceProvider:
    name = "yahoo_finance"

    def __init__(self, auto_adjust: bool = True, progress: bool = False, threads: bool = False) -> None:
        self.auto_adjust = auto_adjust
        self.progress = progress
        self.threads = threads
        self.last_error: DataProviderError | None = None

    def get_history(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        self.last_error = None

        try:
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=self.progress,
                auto_adjust=self.auto_adjust,
                threads=self.threads,
            )
        except Exception as error:
            self.last_error = DataProviderError(self.name, ticker, str(error))
            return empty_ohlcv_frame()

        return self._normalize(data, ticker)

    def _normalize(self, data: pd.DataFrame | None, ticker: str) -> pd.DataFrame:
        if data is None or data.empty:
            return empty_ohlcv_frame()

        normalized = data.copy()
        if isinstance(normalized.columns, pd.MultiIndex):
            normalized.columns = normalized.columns.get_level_values(0)

        required = ["Open", "High", "Low", "Close", "Volume"]
        missing = [column for column in required if column not in normalized.columns]
        if missing:
            self.last_error = DataProviderError(self.name, ticker, f"missing columns: {', '.join(missing)}")
            return empty_ohlcv_frame()

        normalized = normalized[required].dropna(how="all")
        if normalized.empty:
            return empty_ohlcv_frame()

        return normalized
