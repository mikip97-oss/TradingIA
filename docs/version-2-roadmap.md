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
## Sprint 3: Market Regime Engine

Dieser Schritt fuehrt eine eigenstaendige Market-Regime-Komponente ein. Sie erkennt Bull-, Bear- und Sideways-Maerkte anhand von EMA-Struktur, ADX, ATR und Volatilitaet. Die Komponente bleibt unabhaengig von Strategien, GUI, Scanner und Backtesting Engine, damit das Strategy Lab spaeter Regime als Kontext oder Filter nutzen kann.
## Sprint 4: Regime-Aware Strategy Selection

Dieser Schritt integriert die Market Regime Engine optional in das Strategy Lab. Das Lab kann je nach erkanntem Regime passende Strategien auswaehlen und das erkannte Regime im Leaderboard anzeigen. Ohne Regime Engine bleibt das bisherige Verhalten unveraendert.
## Sprint 5: Research Dashboard

Dieser Schritt fuehrt eine eigenstaendige Research-Auswertung fuer Backtest-Ergebnisse ein. Das Dashboard erzeugt Equity Curve, Drawdown, zentrale Performance-Kennzahlen, CSV-Exporte und einen HTML-Report mit Datum und Uhrzeit. Bestehende GUI-, Scanner- und Backtesting-Module bleiben unveraendert.
## Sprint 6: Parameter Optimizer

Dieser Schritt fuehrt einen modularen Grid-Search-Optimizer fuer Strategieparameter ein. Mehrere Parameter-Kombinationen einer Strategie koennen ueber dieselbe Event-Driven-Backtesting-Engine getestet und als Leaderboard verglichen werden. Bestehende GUI-, Scanner- und Backtesting-Module bleiben unveraendert.
## Sprint 7: Research Runner

Dieser Schritt fuehrt mit `research_runner.py` einen ausfuehrbaren Einstiegspunkt fuer Research-Experimente ein. Der Runner erzeugt Beispieldaten, startet Strategy-Lab- und Parameter-Optimizer-Laeufe, gibt Leaderboards aus und exportiert Reports ueber das Research Dashboard. Bestehende GUI-, Scanner- und Backtesting-Module bleiben unveraendert.
## MVP-Speed-Modus: Großer Aktien-Scanner

Dieser Schritt erweitert die Universe-Logik fuer einen groesseren Scanner. S&P 500 und Nasdaq 100 koennen geladen, normalisiert und dedupliziert werden. Die Fallback-Liste bleibt erhalten, und `TOP_ANZAHL` kann 50 Kandidaten anzeigen. GUI und `scanner.py` bleiben in diesem Schritt unveraendert.
## Sprint 8: High-Speed Scanner

Dieser Sprint fuehrt paralleles Scannen mit `ThreadPoolExecutor` ein. Die bestehende Scanner-Logik wird in `scan_ticker(ticker)` gekapselt, Tickerfehler werden isoliert verarbeitet und die Parallelitaet kann mit `SCANNER_MAX_WORKERS` konfiguriert werden. Ziel ist schneller MVP-Nutzen ohne GUI oder Backtesting-Module umzubauen.

