import importlib
import sys
import types

import pandas as pd


def install_scanner_dependencies():
    candles = types.ModuleType("candles")
    candles.erkenne_candles = lambda data: {"Muster": "Keine", "CandleScore": 0}
    sys.modules["candles"] = candles

    feature_builder = types.ModuleType("feature_builder")
    feature_builder.baue_features = lambda data: {
        "atr": 2.0,
        "adx": 22.0,
        "volumen_faktor": 1.4,
        "abstand_52w_high": 5.0,
        "rsi": 58.0,
        "veraenderung": 1.25,
        "mfi": 62.0,
        "roc": 3.5,
    }
    sys.modules["feature_builder"] = feature_builder

    risk = types.ModuleType("risk")
    risk.berechne_position = lambda einstieg, stop_loss, kontostand, risiko_pro_trade: {
        "Positionsgröße $": 1000.0,
        "Aktien": 10.0,
        "Max Risiko $": 200.0,
    }
    sys.modules["risk"] = risk

    trade_engine = types.ModuleType("trade_engine")
    trade_engine.bewerte_trade = lambda **kwargs: (72.0, "Kaufen", ["KI positiv", "Volumen über Durchschnitt"])
    sys.modules["trade_engine"] = trade_engine

    ai_package = types.ModuleType("ai")
    ai_predict = types.ModuleType("ai.ai_predict")
    ai_predict.ki_vorhersage = lambda feature_dict: 66.6
    sys.modules["ai"] = ai_package
    sys.modules["ai.ai_predict"] = ai_predict


def import_scanner():
    install_scanner_dependencies()
    sys.modules.pop("scanner", None)
    return importlib.import_module("scanner")


def make_download_data(days=230):
    index = pd.date_range("2024-01-01", periods=days, freq="D")
    close = pd.Series([100 + i * 0.2 for i in range(days)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": [1_000_000 + i * 1_000 for i in range(days)],
        },
        index=index,
    )


def test_resolve_max_workers_caps_to_ticker_count():
    scanner = import_scanner()

    assert scanner._resolve_max_workers(max_workers=8, ticker_count=3) == 3
    assert scanner._resolve_max_workers(max_workers=0, ticker_count=3) == 1
    assert scanner._resolve_max_workers(max_workers=4, ticker_count=0) == 1


def test_scan_market_continues_when_single_ticker_fails(monkeypatch):
    scanner = import_scanner()

    def fake_scan_ticker(ticker):
        if ticker == "BROKEN":
            raise RuntimeError("Download fehlgeschlagen")
        return {"Aktie": ticker, "TradeScore": 70 if ticker == "AAPL" else 65}

    monkeypatch.setattr(scanner, "scan_ticker", fake_scan_ticker)

    result = scanner.scan_market(tickers=["AAPL", "BROKEN", "MSFT"], max_workers=2)

    assert list(result["Aktie"]) == ["AAPL", "MSFT"]


def test_scan_market_limits_to_top_anzahl(monkeypatch):
    scanner = import_scanner()
    monkeypatch.setattr(scanner, "TOP_ANZAHL", 2)
    monkeypatch.setattr(
        scanner,
        "scan_ticker",
        lambda ticker: {"Aktie": ticker, "TradeScore": {"A": 10, "B": 30, "C": 20}[ticker]},
    )

    result = scanner.scan_market(tickers=["A", "B", "C"], max_workers=2)

    assert list(result["Aktie"]) == ["B", "C"]


def test_scan_ticker_preserves_existing_scanner_columns(monkeypatch):
    scanner = import_scanner()
    monkeypatch.setattr(scanner.yf, "download", lambda *args, **kwargs: make_download_data())

    result = scanner.scan_ticker("AAPL")

    assert result == {
        "Aktie": "AAPL",
        "TradeScore": 72.0,
        "KI %": 66.6,
        "Empfehlung": "Kaufen",
        "Muster": "Keine",
        "Gründe": "KI positiv, Volumen über Durchschnitt",
        "Einstieg": 145.8,
        "Stop-Loss": 142.8,
        "Ziel": 151.8,
        "Chance/Risiko": 2.0,
        "Positionsgröße $": 1000.0,
        "Aktien": 10.0,
        "Max Risiko $": 200.0,
        "Heute %": 1.25,
        "RSI": 58.0,
        "Volumen-Faktor": 1.4,
        "52W Abstand %": 5.0,
        "ADX": 22.0,
        "MFI": 62.0,
        "ROC": 3.5,
    }


def test_get_aktien_liste_keeps_existing_fallback_behavior(monkeypatch):
    scanner = import_scanner()
    monkeypatch.setattr(scanner, "NUTZE_SP500", False)

    assert scanner.get_aktien_liste() == scanner.FALLBACK_AKTIEN
