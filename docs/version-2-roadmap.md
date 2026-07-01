# TradingIA Version 2.0 Roadmap

TradingIA 2.0 will evolve from a desktop scanner into a professional quantitative research platform. The existing GUI and scanner stay usable while new research, backtesting, data, risk, and execution services are introduced behind modular interfaces.

## Target Architecture

- `tradingia.backtesting`: event-driven simulation, transaction costs, portfolio accounting, fills, and metrics.
- `tradingia.research`: walk-forward validation, experiment orchestration, model evaluation, and reporting.
- `tradingia.data`: historical/intraday data providers, local storage, calendars, and data quality checks.
- `tradingia.features`: reusable feature pipelines shared by scanner, models, and backtests.
- `tradingia.strategies`: deterministic strategy interfaces and ML-backed signal adapters.
- `tradingia.risk`: portfolio constraints, exposure limits, kill switches, and sizing models.
- `tradingia.execution`: broker adapters for paper/live trading after research validation.
- Existing GUI/scanner modules remain as compatibility entry points during migration.

## Increment 1: Event-Driven Backtesting Foundation

This first change adds a modular event-driven backtest engine without replacing the current scanner or GUI.

Included:

- Bar, signal, order, and fill events.
- A pandas-backed bar feed for deterministic tests and research notebooks.
- Portfolio accounting with cash, positions, mark-to-market equity, and trade records.
- Simulated market execution with commission and slippage.
- Basic performance metrics: ending equity, total return, and max drawdown.
- Walk-forward split generation and a runner that trains/constructs a strategy on each training window, then backtests only the following test window.
- Unit tests for costs, equity tracking, and walk-forward windows.

Next increments:

1. Add a `tradingia.data` service and migrate Yahoo downloads behind a provider interface.
2. Convert the existing technical feature builder into a reusable feature pipeline.
3. Add a strategy adapter that lets the existing scanner score logic run inside the event-driven engine.
4. Replace `backtest.py` and `ki_backtest.py` with compatibility wrappers around the new engine.
5. Add model walk-forward training, probability calibration, and threshold reports.
6. Add realistic intraday costs, spread assumptions, liquidity limits, and market calendar support.
## Increment 2: Strategy Lab

Dieser Schritt fuehrt eine modulare Strategie-Schicht ein. Mehrere Strategien koennen jetzt dieselbe Event-Driven-Backtesting-Engine nutzen und direkt miteinander verglichen werden.

Enthalten:

- Einheitliche Strategie-Schnittstelle mit `on_bar(bar) -> list[SignalEvent]`.
- Austauschbare Strategien fuer Buy & Hold, EMA-Crossover, RSI-Reversion und Breakout.
- Strategy Lab zur Ausfuehrung mehrerer Strategien auf demselben Datensatz.
- Leaderboard mit Trades, Endkapital, Gesamtrendite und maximalem Drawdown.
- Tests und deutsche Dokumentation fuer den neuen Research-Baustein.

