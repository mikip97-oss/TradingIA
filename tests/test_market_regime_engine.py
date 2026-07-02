from datetime import datetime, timedelta

import pandas as pd
import pytest

from tradingia.regime import MarketRegime, MarketRegimeEngine


def make_bars(prices, symbol="SPY"):
    start = datetime(2024, 1, 1, 9, 30)
    rows = []
    for index, price in enumerate(prices):
        rows.append(
            {
                "symbol": symbol,
                "timestamp": start + timedelta(days=index),
                "high": price + 1.5,
                "low": price - 1.5,
                "close": price,
            }
        )
    return pd.DataFrame(rows)


def test_market_regime_engine_detects_bull_market():
    prices = [100 + index * 0.9 for index in range(90)]
    engine = MarketRegimeEngine(fast_ema_window=5, slow_ema_window=15, trend_adx_threshold=15)

    snapshot = engine.classify(make_bars(prices))

    assert snapshot.regime == MarketRegime.BULL
    assert snapshot.ema_fast > snapshot.ema_slow
    assert snapshot.adx >= 15


def test_market_regime_engine_detects_bear_market():
    prices = [180 - index * 0.9 for index in range(90)]
    engine = MarketRegimeEngine(fast_ema_window=5, slow_ema_window=15, trend_adx_threshold=15)

    snapshot = engine.classify(make_bars(prices))

    assert snapshot.regime == MarketRegime.BEAR
    assert snapshot.ema_fast < snapshot.ema_slow
    assert snapshot.adx >= 15


def test_market_regime_engine_detects_sideways_market():
    prices = [100 + (index % 4 - 1.5) * 0.15 for index in range(90)]
    engine = MarketRegimeEngine(
        fast_ema_window=5,
        slow_ema_window=15,
        sideways_adx_threshold=100,
        min_ema_spread_pct=0.5,
    )

    snapshot = engine.classify(make_bars(prices))

    assert snapshot.regime == MarketRegime.SIDEWAYS
    assert abs(((snapshot.ema_fast - snapshot.ema_slow) / snapshot.ema_slow) * 100) < 0.5


def test_market_regime_engine_classifies_multiple_symbols_independently():
    bull = make_bars([100 + index for index in range(90)], symbol="BULL")
    bear = make_bars([180 - index for index in range(90)], symbol="BEAR")
    engine = MarketRegimeEngine(fast_ema_window=5, slow_ema_window=15, trend_adx_threshold=15)

    snapshots = engine.classify_many(pd.concat([bull, bear], ignore_index=True))

    assert snapshots["BULL"].regime == MarketRegime.BULL
    assert snapshots["BEAR"].regime == MarketRegime.BEAR


def test_market_regime_engine_validates_required_columns():
    engine = MarketRegimeEngine()

    with pytest.raises(ValueError, match="missing required columns"):
        engine.classify(pd.DataFrame({"symbol": ["SPY"]}))
