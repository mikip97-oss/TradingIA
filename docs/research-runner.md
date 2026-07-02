# Research Runner

Der Research Runner ist ein ausfuehrbarer Einstiegspunkt fuer TradingIA-Research-Experimente. Er veraendert weder GUI noch `scanner.py` noch die Backtesting Engine.

## Ziel

Mit einem einzigen Startpunkt sollen Beispieldaten erzeugt, mehrere Strategien getestet, EMA-Parameter-Kombinationen optimiert, Leaderboards ausgegeben und HTML-/CSV-Reports exportiert werden.

## Start

```bash
python research_runner.py
```

Der Runner erzeugt deterministische Beispieldaten. Es werden keine externen Marktdaten geladen und keine API-Schluessel benoetigt.

## Ablauf

1. Beispieldaten werden mit `generate_sample_bars()` erzeugt.
2. Das Strategy Lab testet mehrere Standardstrategien.
3. Die Market Regime Engine kann dabei passende Strategien auswaehlen.
4. Der Parameter Optimizer testet mehrere EMA-Crossover-Kombinationen.
5. Zwei Leaderboards werden ausgegeben.
6. Das Research Dashboard exportiert fuer jedes Ergebnis CSV-Dateien und einen HTML-Report.

## Exporte

Standardordner:

```text
reports/research_runner/
```

Jeder Report enthaelt:

- `metrics.csv`
- `equity_curve.csv`
- `drawdown.csv`
- `trades.csv`
- `report.html`

## Rueckwaertskompatibilitaet

Der Runner ist nur ein neuer Einstiegspunkt. Bestehende Module bleiben unveraendert. Alle Backtests laufen weiterhin ueber die vorhandene Event-Driven-Backtesting-Engine.
