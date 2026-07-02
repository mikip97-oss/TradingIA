from datetime import datetime, timedelta

import pandas as pd

from tradingia.backtesting.engine import BacktestEngine
from tradingia.regime import MarketRegimeEngine
from tradingia.research.strategy_lab import StrategyLab
from tradingia.strategies.breakout import BreakoutStrategy
from tradingia.strategies.buy_and_hold import BuyAndHoldStrategy
from tradingia.strategies.ema_crossover import EMACrossoverStrategy
from tradingia.strategies.registry import StrategySpec, default_strategy_specs
from tradingia.strategies.rsi_reversion import RSIReversionStrategy


def make_bars(prices):
    start = datetime(2024, 1, 1, 9, 30)
    rows = []
    for index, price in enumerate(prices):
        rows.append(
            {
                "symbol": "AAPL",
                "timestamp": start + timedelta(days=index),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1_000_000,
            }
        )
    return pd.DataFrame(rows)


def test_strategy_lab_runs_multiple_interchangeable_strategies():
    bars = make_bars([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111])
    lab = StrategyLab(BacktestEngine(initial_cash=10_000))

    results = lab.run(
        bars,
        [
            StrategySpec("buy_and_hold", BuyAndHoldStrategy, {"target_percent": 0.5}),
            StrategySpec("ema_crossover", EMACrossoverStrategy, {"short_window": 3, "long_window": 5, "target_percent": 0.5}),
            StrategySpec("breakout", BreakoutStrategy, {"lookback": 3, "target_percent": 0.5}),
        ],
    )
    leaderboard = lab.leaderboard(results)

    assert len(results) == 3
    assert list(leaderboard.columns) == [
        "Strategie-Name",
        "Regime",
        "Ending Equity",
        "Return %",
        "Max Drawdown %",
        "Anzahl Trades",
    ]
    assert set(leaderboard["Strategie-Name"]) == {"buy_and_hold", "ema_crossover", "breakout"}
    assert all("ending_equity" in result.result.metrics for result in results)


def test_default_strategy_specs_create_fresh_strategy_instances():
    specs = default_strategy_specs()

    first_instances = [spec.create() for spec in specs]
    second_instances = [spec.create() for spec in specs]

    assert [spec.name for spec in specs] == ["buy_and_hold", "ema_crossover", "rsi_reversion", "breakout"]
    assert all(first is not second for first, second in zip(first_instances, second_instances))


def test_rsi_reversion_uses_same_strategy_interface():
    bars = make_bars([100, 98, 96, 94, 92, 90, 93, 96, 99, 102])
    strategy = RSIReversionStrategy(window=3, oversold=35, exit_rsi=55, target_percent=0.5)

    signals = []
    from tradingia.backtesting.data import PandasBarFeed

    for bar in PandasBarFeed(bars):
        signals.extend(strategy.on_bar(bar))

    assert signals
    assert all(signal.symbol == "AAPL" for signal in signals)

def test_strategy_lab_leaderboard_sorts_by_return_descending():
    bars = make_bars([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
    lab = StrategyLab(BacktestEngine(initial_cash=10_000))

    results = lab.run(
        bars,
        [
            StrategySpec("small_allocation", BuyAndHoldStrategy, {"target_percent": 0.25}),
            StrategySpec("large_allocation", BuyAndHoldStrategy, {"target_percent": 0.75}),
        ],
    )

    leaderboard = lab.leaderboard(results)

    assert leaderboard.iloc[0]["Strategie-Name"] == "large_allocation"
    assert leaderboard.iloc[0]["Return %"] >= leaderboard.iloc[1]["Return %"]
    assert leaderboard.iloc[0]["Anzahl Trades"] == 1


def test_strategy_lab_empty_leaderboard_has_stable_columns():
    lab = StrategyLab(BacktestEngine(initial_cash=10_000))

    leaderboard = lab.leaderboard([])

    assert leaderboard.empty
    assert list(leaderboard.columns) == [
        "Strategie-Name",
        "Regime",
        "Ending Equity",
        "Return %",
        "Max Drawdown %",
        "Anzahl Trades",
    ]

def test_strategy_lab_selects_strategies_for_detected_bull_regime():
    bars = make_bars([100 + index * 0.9 for index in range(90)])
    lab = StrategyLab(BacktestEngine(initial_cash=10_000))
    regime_engine = MarketRegimeEngine(fast_ema_window=5, slow_ema_window=15, trend_adx_threshold=15)

    results = lab.run(bars, default_strategy_specs(), regime_engine=regime_engine)
    leaderboard = lab.leaderboard(results)

    assert set(leaderboard["Strategie-Name"]) == {"buy_and_hold", "ema_crossover", "breakout"}
    assert set(leaderboard["Regime"]) == {"bull"}
    assert "rsi_reversion" not in set(leaderboard["Strategie-Name"])


def test_strategy_lab_runs_all_strategies_when_no_regime_engine_is_provided():
    bars = make_bars([100, 101, 102, 103, 104, 105])
    lab = StrategyLab(BacktestEngine(initial_cash=10_000))

    results = lab.run(
        bars,
        [
            StrategySpec("buy_and_hold", BuyAndHoldStrategy, {"target_percent": 0.5}),
            StrategySpec("breakout", BreakoutStrategy, {"lookback": 2, "target_percent": 0.5}),
        ],
    )
    leaderboard = lab.leaderboard(results)

    assert set(leaderboard["Strategie-Name"]) == {"buy_and_hold", "breakout"}
    assert set(leaderboard["Regime"]) == {"unknown"}

def test_strategy_lab_uses_sideways_selection_for_mixed_symbol_regimes():
    bull = make_bars([100 + index * 0.9 for index in range(90)])
    bear = make_bars([180 - index * 0.9 for index in range(90)])
    bear["symbol"] = "MSFT"
    bars = pd.concat([bull, bear], ignore_index=True)
    lab = StrategyLab(BacktestEngine(initial_cash=10_000))
    regime_engine = MarketRegimeEngine(fast_ema_window=5, slow_ema_window=15, trend_adx_threshold=15)

    results = lab.run(bars, default_strategy_specs(), regime_engine=regime_engine)
    leaderboard = lab.leaderboard(results)

    assert set(leaderboard["Regime"]) == {"sideways"}
    assert set(leaderboard["Strategie-Name"]) == {"rsi_reversion", "breakout"}

