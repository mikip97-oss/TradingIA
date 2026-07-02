# Strategy Lab

Das Strategy Lab ist die Research-Schicht fuer austauschbare Handelsstrategien in TradingIA 2.0. Es nutzt dieselbe Event-Driven-Backtesting-Engine fuer alle Strategien, damit Ergebnisse vergleichbar bleiben.

## Ziel

TradingIA soll nicht nur einzelne Scanner-Signale anzeigen, sondern Strategien reproduzierbar testen, vergleichen und spaeter im Walk-forward-Prozess validieren koennen. Das Strategy Lab ist dafuer der modulare Einstiegspunkt.

## Architektur

Alle Strategien implementieren dieselbe Schnittstelle:

```python
def on_bar(self, bar: BarEvent) -> list[SignalEvent]:
    ...
```

Eine Strategie empfaengt pro Marktereignis einen `BarEvent` und gibt null, ein oder mehrere `SignalEvent`-Objekte zurueck. Die Backtesting-Engine uebersetzt diese Signale in Orders, simulierte Ausfuehrungen, Kosten, Portfolio-Positionen und Performance-Kennzahlen.

## Enthaltene Strategien

- `BuyAndHoldStrategy`: Einstieg beim ersten Bar eines Symbols.
- `EMACrossoverStrategy`: Long-Signal, wenn die kurze EMA ueber die lange EMA steigt; Exit bei Rueckkreuzung.
- `RSIReversionStrategy`: Mean-Reversion-Einstieg bei ueberverkauftem RSI; Exit bei Erholung.
- `BreakoutStrategy`: Long-Signal, wenn der Schlusskurs ueber das vorherige Lookback-Hoch ausbricht.

## Nutzung

```python
from tradingia.backtesting.engine import BacktestEngine
from tradingia.research.strategy_lab import StrategyLab
from tradingia.strategies.registry import default_strategy_specs

lab = StrategyLab(BacktestEngine(initial_cash=10000))
results = lab.run(bars, default_strategy_specs())
leaderboard = lab.leaderboard(results)
```

`bars` ist ein pandas DataFrame mit den Spalten `symbol`, `timestamp`, `open`, `high`, `low`, `close` und `volume`.

## Leaderboard

Das Strategy Lab erzeugt ein sortiertes Leaderboard, damit mehrere Strategien auf demselben Datensatz direkt vergleichbar sind. Die Ausgabe enthaelt bewusst nur die wichtigsten Research-Kennzahlen:

- Strategie-Name
- Ending Equity
- Return %
- Max Drawdown %
- Anzahl Trades

Sortiert wird zuerst nach `Return %`, danach nach `Max Drawdown %` und `Ending Equity`. Dadurch steht die staerkste Strategie im getesteten Zeitraum oben, ohne die Backtesting-Engine oder bestehende GUI-/Scanner-Module zu veraendern.

## Rueckwaertskompatibilitaet

Die bestehende GUI und der Scanner werden nicht veraendert. Das Strategy Lab liegt als neue Research-Schicht unter `tradingia/` und kann unabhaengig getestet und erweitert werden.

## Naechster Schritt

Als naechster PR-grosser Schritt sollte die Marktdaten-Schicht `tradingia.data` eingefuehrt werden. Dann koennen Scanner, Backtester und Strategy Lab dieselbe validierte Datenquelle verwenden.
