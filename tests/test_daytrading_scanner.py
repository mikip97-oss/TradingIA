import pandas as pd

import daytrading_scanner as scanner


def make_intraday_data(days=1, bars=80):
    index = pd.date_range("2024-01-02 09:30", periods=bars, freq="5min")
    close = pd.Series([100 + i * 0.08 for i in range(bars)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.03,
            "High": close + 0.2,
            "Low": close - 0.2,
            "Close": close,
            "Volume": [1_000_000 + i * 20_000 for i in range(bars)],
        },
        index=index,
    )


def test_score_daytrading_setup_recommends_strong_setups():
    score, recommendation, reasons = scanner.score_daytrading_setup(
        {
            "today_change_pct": 3.2,
            "volume_factor": 1.8,
            "gap_pct": 1.2,
            "rsi": 62.0,
            "adx": 28.0,
            "roc": 1.5,
            "distance_to_high_pct": 0.2,
            "close_position_in_range": 92.0,
            "relative_move_pct": 2.0,
        }
    )

    assert score >= 80
    assert recommendation == "🟢 Sehr stark"
    assert "nahe am Tageshoch" in reasons


def test_score_daytrading_setup_does_not_overstate_weak_setups():
    score, recommendation, reasons = scanner.score_daytrading_setup(
        {
            "today_change_pct": -1.0,
            "volume_factor": 0.7,
            "gap_pct": -2.5,
            "rsi": 30.0,
            "adx": 10.0,
            "roc": -1.5,
            "distance_to_high_pct": 5.0,
            "close_position_in_range": 35.0,
            "relative_move_pct": 0.5,
        }
    )

    assert score < 60
    assert recommendation == "🔴 Kein Daytrade"
    assert "schwaches Gap-Down" in reasons


def test_scan_daytrading_ticker_returns_required_columns(monkeypatch):
    monkeypatch.setattr(scanner.yf, "download", lambda *args, **kwargs: make_intraday_data())

    result = scanner.scan_daytrading_ticker("AAPL")

    assert result is not None
    assert list(result.keys()) == scanner.DAYTRADING_COLUMNS
    assert result["Aktie"] == "AAPL"
    assert 0 <= result["DayTradeScore"] <= 100


def test_scan_daytrading_market_continues_when_ticker_fails(monkeypatch):
    def fake_scan_ticker(ticker):
        if ticker == "BROKEN":
            raise RuntimeError("Intraday-Daten fehlen")
        return {
            "Aktie": ticker,
            "DayTradeScore": 80 if ticker == "AAPL" else 65,
            "Empfehlung": "🟢 Sehr stark",
            "Einstieg": 100.0,
            "Stop-Loss": 99.0,
            "Ziel": 102.0,
            "Heute %": 2.0,
            "RSI": 60.0,
            "Volumen-Faktor": 1.5,
            "ADX": 25.0,
            "ROC": 1.2,
            "Gründe": "Test",
        }

    monkeypatch.setattr(scanner, "scan_daytrading_ticker", fake_scan_ticker)

    result = scanner.scan_daytrading_market(tickers=["MSFT", "BROKEN", "AAPL"], max_workers=2)

    assert list(result["Aktie"]) == ["AAPL", "MSFT"]


def test_scan_daytrading_market_returns_empty_dataframe_with_stable_columns(monkeypatch):
    monkeypatch.setattr(scanner, "scan_daytrading_ticker", lambda ticker: None)

    result = scanner.scan_daytrading_market(tickers=["AAPL"], max_workers=1)

    assert result.empty
    assert list(result.columns) == scanner.DAYTRADING_COLUMNS

def test_prepare_intraday_data_uses_latest_session_and_keeps_previous_close():
    index = pd.date_range("2024-01-01 09:30", periods=20, freq="5min").append(
        pd.date_range("2024-01-02 09:30", periods=20, freq="5min")
    )
    close = pd.Series([100 + i * 0.1 for i in range(40)], index=index)
    data = pd.DataFrame(
        {
            "Open": close - 0.02,
            "High": close + 0.2,
            "Low": close - 0.2,
            "Close": close,
            "Volume": 1_000_000,
        },
        index=index,
    )

    session = scanner._prepare_intraday_data(data)

    assert len(session) == 20
    assert session.index.normalize().nunique() == 1
    assert session.attrs["previous_close"] == close.iloc[19]

