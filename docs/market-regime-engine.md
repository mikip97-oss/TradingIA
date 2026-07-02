# Market Regime Engine

Die Market Regime Engine ist eine eigenstaendige Research-Komponente fuer TradingIA 2.0. Sie erkennt, ob sich ein Markt aktuell eher in einem Bull-, Bear- oder Sideways-Regime befindet.

## Ziel

Strategien sollen nicht selbst entscheiden muessen, welches Marktumfeld vorliegt. Diese Verantwortung liegt in einer separaten Komponente, damit das Strategy Lab spaeter Regime als Filter, Kontext oder Vergleichsdimension nutzen kann.

## Verwendete Indikatoren

- EMA-Struktur: schnelle EMA gegen langsame EMA
- EMA-Steigung: Richtung des langsameren Trends
- ADX: Trendstaerke
- ATR: aktuelle Handelsspanne und Risiko-Kontext
- Volatilitaet: prozentuale Schwankung ueber ein Rolling Window

## Regime

- `bull`: schnelle EMA ueber langsamer EMA, steigende langsame EMA und ausreichend starker ADX
- `bear`: schnelle EMA unter langsamer EMA, fallende langsame EMA und ausreichend starker ADX
- `sideways`: schwacher ADX, enger EMA-Abstand oder gemischte Signale

## Nutzung

```python
from tradingia.regime import MarketRegimeEngine

engine = MarketRegimeEngine()
snapshot = engine.classify(bars)

print(snapshot.regime)
print(snapshot.reason)
```

`bars` ist ein pandas DataFrame mit mindestens diesen Spalten: `symbol`, `timestamp`, `high`, `low` und `close`.

## Rueckwaertskompatibilitaet

Die bestehende GUI, `scanner.py`, die Backtesting Engine und bestehende Strategien werden nicht veraendert. Die Engine liegt isoliert unter `tradingia/regime` und kann spaeter vom Strategy Lab eingebunden werden.
