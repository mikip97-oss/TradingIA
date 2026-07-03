import pandas as pd

import catalyst_scanner as scanner


def make_intraday_data(bars=90):
    index = pd.date_range("2024-01-02 09:30", periods=bars, freq="5min")
    close = pd.Series([100 + i * 0.09 for i in range(bars)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.04,
            "High": close + 0.25,
            "Low": close - 0.25,
            "Close": close,
            "Volume": [1_000_000 + i * 25_000 for i in range(bars)],
        },
        index=index,
    )


def test_score_catalyst_setup_identifies_strong_catalysts():
    score, recommendation, reasons = scanner.score_catalyst_setup(
        {
            "today_change_pct": 5.2,
            "volume_factor": 2.3,
            "gap_pct": 2.1,
            "roc": 2.4,
            "distance_to_high_pct": 0.2,
            "close_position_in_range": 94.0,
            "volatility_factor": 1.9,
        }
    )

    assert score >= 80
    assert recommendation == "🟢 Sehr starker Catalyst"
    assert "außergewöhnlich hohes Volumen" in reasons
    assert "nahe am Tageshoch" in reasons


def test_score_catalyst_setup_penalizes_negative_reactions():
    score, recommendation, reasons = scanner.score_catalyst_setup(
        {
            "today_change_pct": -4.0,
            "volume_factor": 0.8,
            "gap_pct": -2.5,
            "roc": -2.0,
            "distance_to_high_pct": 8.0,
            "close_position_in_range": 20.0,
            "volatility_factor": 0.8,
        }
    )

    assert score < 60
    assert recommendation == "🔴 Kein Catalyst"
    assert "starke negative Marktreaktion" in reasons


def test_scan_catalyst_ticker_returns_required_columns(monkeypatch):
    monkeypatch.setattr(scanner.yf, "download", lambda *args, **kwargs: make_intraday_data())

    result = scanner.scan_catalyst_ticker("AAPL")

    assert result is not None
    assert list(result.keys()) == scanner.CATALYST_COLUMNS
    assert result["Aktie"] == "AAPL"
    assert 0 <= result["CatalystScore"] <= 100


def test_scan_catalyst_market_continues_when_ticker_fails(monkeypatch):
    def fake_scan_ticker(ticker):
        if ticker == "BROKEN":
            raise RuntimeError("Daten fehlen")
        return {
            "Aktie": ticker,
            "CatalystScore": 82 if ticker == "AAPL" else 65,
            "Empfehlung": "🟢 Sehr starker Catalyst",
            "Heute %": 4.0,
            "Volumen-Faktor": 2.0,
            "ROC": 2.0,
            "Gründe": "Test",
        }

    monkeypatch.setattr(scanner, "scan_catalyst_ticker", fake_scan_ticker)

    result = scanner.scan_catalyst_market(tickers=["MSFT", "BROKEN", "AAPL"], max_workers=2)

    assert list(result["Aktie"]) == ["AAPL", "MSFT"]


def test_scan_catalyst_market_returns_empty_dataframe_with_stable_columns(monkeypatch):
    monkeypatch.setattr(scanner, "scan_catalyst_ticker", lambda ticker: None)

    result = scanner.scan_catalyst_market(tickers=["AAPL"], max_workers=1)

    assert result.empty
    assert list(result.columns) == scanner.CATALYST_COLUMNS
