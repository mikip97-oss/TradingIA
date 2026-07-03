import pandas as pd

from tradingia.data import YahooFinanceProvider, empty_ohlcv_frame
from tradingia.data.base import OHLCV_COLUMNS


def make_history_frame():
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    return pd.DataFrame(
        {
            "Open": [100, 101, 102],
            "High": [101, 102, 103],
            "Low": [99, 100, 101],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1_000_000, 1_100_000, 1_200_000],
            "Ignored": [1, 2, 3],
        },
        index=index,
    )


def test_empty_ohlcv_frame_has_stable_columns():
    frame = empty_ohlcv_frame()

    assert frame.empty
    assert list(frame.columns) == OHLCV_COLUMNS


def test_yahoo_provider_returns_normalized_history(monkeypatch):
    provider = YahooFinanceProvider()
    monkeypatch.setattr("tradingia.data.yahoo.yf.download", lambda *args, **kwargs: make_history_frame())

    result = provider.get_history("AAPL", period="1mo", interval="1d")

    assert list(result.columns) == OHLCV_COLUMNS
    assert len(result) == 3
    assert provider.last_error is None


def test_yahoo_provider_returns_empty_frame_on_download_error(monkeypatch):
    provider = YahooFinanceProvider()

    def broken_download(*args, **kwargs):
        raise RuntimeError("HTTP Error 403 Forbidden")

    monkeypatch.setattr("tradingia.data.yahoo.yf.download", broken_download)

    result = provider.get_history("MSFT", period="1mo", interval="1d")

    assert result.empty
    assert list(result.columns) == OHLCV_COLUMNS
    assert provider.last_error is not None
    assert "403" in str(provider.last_error)


def test_yahoo_provider_returns_empty_frame_when_required_columns_are_missing(monkeypatch):
    provider = YahooFinanceProvider()
    monkeypatch.setattr("tradingia.data.yahoo.yf.download", lambda *args, **kwargs: pd.DataFrame({"Close": [100]}))

    result = provider.get_history("NVDA", period="1mo", interval="1d")

    assert result.empty
    assert provider.last_error is not None
    assert "missing columns" in str(provider.last_error)
