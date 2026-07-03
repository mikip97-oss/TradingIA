import pandas as pd

import universe


def test_deduplicate_tickers_normalizes_for_yahoo():
    tickers = universe.deduplicate_tickers(["brk.b", "BRK-B", " aapl ", "AAPL", ""])

    assert tickers == ["BRK-B", "AAPL"]


def test_lade_sp500_ticker_uses_symbol_column(monkeypatch):
    def fake_read_html(url):
        assert url == universe.SP500_URL
        return [pd.DataFrame({"Symbol": ["AAPL", "BRK.B", "AAPL"]})]

    monkeypatch.setattr(universe.pd, "read_html", fake_read_html)

    assert universe.lade_sp500_ticker() == ["AAPL", "BRK-B"]


def test_lade_nasdaq100_ticker_accepts_ticker_column(monkeypatch):
    def fake_read_html(url):
        assert url == universe.NASDAQ100_URL
        return [pd.DataFrame({"Company": ["Ignored"]}), pd.DataFrame({"Ticker": ["MSFT", "GOOGL", "MSFT"]})]

    monkeypatch.setattr(universe.pd, "read_html", fake_read_html)

    assert universe.lade_nasdaq100_ticker() == ["MSFT", "GOOGL"]


def test_lade_grosses_universum_removes_duplicates_and_keeps_fallback(monkeypatch):
    monkeypatch.setattr(universe, "lade_sp500_ticker", lambda: ["AAPL", "MSFT", "BRK-B"])
    monkeypatch.setattr(universe, "lade_nasdaq100_ticker", lambda: ["MSFT", "NVDA", "GOOGL"])
    monkeypatch.setattr(universe, "lade_fallback_ticker", lambda: ["NVDA", "AMD"])

    tickers = universe.lade_grosses_universum(include_backup=False)

    assert tickers == ["AAPL", "MSFT", "BRK-B", "NVDA", "GOOGL", "AMD"]


def test_lade_grosses_universum_survives_source_errors(monkeypatch):
    def broken_source():
        raise RuntimeError("Quelle nicht erreichbar")

    monkeypatch.setattr(universe, "lade_sp500_ticker", broken_source)
    monkeypatch.setattr(universe, "lade_nasdaq100_ticker", lambda: ["QQQ", "AAPL"])
    monkeypatch.setattr(universe, "lade_fallback_ticker", lambda: ["AAPL", "AMD"])

    tickers = universe.lade_grosses_universum()

    assert "QQQ" in tickers
    assert "AAPL" in tickers
    assert "AMD" in tickers
    assert len(tickers) >= universe.MIN_GROSSES_UNIVERSUM


def test_lade_standard_universum_falls_back_when_large_universe_is_empty(monkeypatch):
    monkeypatch.setattr(universe, "lade_grosses_universum", lambda: [])
    monkeypatch.setattr(universe, "lade_fallback_ticker", lambda: ["AAPL", "MSFT"])

    assert universe.lade_standard_universum(use_large_universe=True) == ["AAPL", "MSFT"]

def test_backup_us_ticker_contains_large_static_universe():
    tickers = universe.lade_backup_us_ticker()

    assert len(tickers) >= 100
    assert "AAPL" in tickers
    assert "NVDA" in tickers
    assert len(tickers) == len(set(tickers))


def test_lade_grosses_universum_uses_backup_when_online_sources_fail(monkeypatch):
    def broken_source():
        raise RuntimeError("HTTP Error 403 Forbidden")

    monkeypatch.setattr(universe, "lade_sp500_ticker", broken_source)
    monkeypatch.setattr(universe, "lade_nasdaq100_ticker", broken_source)

    tickers = universe.lade_grosses_universum()

    assert len(tickers) >= universe.MIN_GROSSES_UNIVERSUM
    assert "AAPL" in tickers
    assert "MSFT" in tickers
    assert "NVDA" in tickers


def test_lade_grosses_universum_can_disable_backup_for_precise_tests(monkeypatch):
    monkeypatch.setattr(universe, "lade_sp500_ticker", lambda: ["AAPL"])
    monkeypatch.setattr(universe, "lade_nasdaq100_ticker", lambda: ["MSFT"])
    monkeypatch.setattr(universe, "lade_fallback_ticker", lambda: ["AMD"])

    assert universe.lade_grosses_universum(include_backup=False) == ["AAPL", "MSFT", "AMD"]

