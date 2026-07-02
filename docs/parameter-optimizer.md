# Parameter Optimizer

Der Parameter Optimizer ist eine eigenstaendige Research-Komponente fuer das Strategy Lab. Er testet mehrere Parameter-Kombinationen einer Strategie gegen dieselbe Event-Driven-Backtesting-Engine und erzeugt daraus ein sortiertes Leaderboard.

## Ziel

Strategien sollen nicht nur mit einer festen Konfiguration bewertet werden. Fuer professionelle Research-Arbeit muessen Parameterbereiche systematisch getestet und vergleichbar gemacht werden, zum Beispiel verschiedene EMA-Fenster fuer eine EMA-Crossover-Strategie.

## Beispiel

```python
from tradingia.backtesting.engine import BacktestEngine
from tradingia.research.optimizer import ParameterOptimizer, build_parameter_grid
from tradingia.strategies.ema_crossover import EMACrossoverStrategy

optimizer = ParameterOptimizer(BacktestEngine(initial_cash=10000))
grid = build_parameter_grid({
    "short_window": [5, 8, 12],
    "long_window": [20, 26, 50],
    "target_percent": [1.0],
})

results = optimizer.run(
    bars,
    strategy_name="ema_crossover",
    strategy_class=EMACrossoverStrategy,
    parameter_grid=grid,
)
leaderboard = optimizer.leaderboard(results)
```

## Leaderboard

Das Leaderboard enthaelt:

- Strategie-Name
- Parameter
- Ending Equity
- Return %
- Max Drawdown %
- Anzahl Trades

Sortiert wird zuerst nach `Return %`, danach nach `Max Drawdown %` und `Ending Equity`, jeweils absteigend.

## Rueckwaertskompatibilitaet

Der Optimizer veraendert weder GUI noch `scanner.py` noch die Backtesting Engine. Jede Parameter-Kombination erzeugt eine frische Strategieinstanz und laeuft ueber die vorhandene Engine.

## Aktuelle Grenzen

Der Optimizer fuehrt aktuell eine einfache Grid Search aus. Er prueft keine statistische Robustheit, keine Walk-forward-Stabilitaet und keine Overfitting-Risiken. Diese Punkte gehoeren in spaetere Research-Sprints.
