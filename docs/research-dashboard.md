# Research Dashboard

Das Research Dashboard ist eine eigenstaendige Auswertungsschicht fuer TradingIA 2.0. Es veraendert weder GUI noch `scanner.py` noch die Backtesting Engine. Es nimmt ein vorhandenes `BacktestResult` entgegen und erzeugt daraus Kennzahlen, CSV-Dateien und einen HTML-Report.

## Ziel

Backtests sollen reproduzierbar ausgewertet und archiviert werden koennen. Jede Auswertung erhaelt Datum und Uhrzeit, damit Research-Laeufe spaeter nachvollziehbar bleiben.

## Enthaltene Auswertungen

- Equity Curve
- Drawdown
- Winrate
- Profit Factor
- Sharpe Ratio
- Sortino Ratio
- Durchschnittlicher Gewinn
- Durchschnittlicher Verlust
- Anzahl Trades
- Durchschnittliche Haltedauer

## Exporte

Pro Report werden diese Dateien erzeugt:

- `metrics.csv`
- `equity_curve.csv`
- `drawdown.csv`
- `trades.csv`
- `report.html`

Der Zielordner enthaelt den Zeitstempel im Format `YYYYMMDD_HHMMSS`.

## Nutzung

```python
from tradingia.research.dashboard import ResearchDashboard

dashboard = ResearchDashboard(output_dir="reports/research")
report = dashboard.build_and_export(backtest_result, report_name="ema_crossover")

print(report.metrics)
print(report.output_paths["html_report"])
```

## Wichtige Annahme

Kennzahlen wie Winrate, Profit Factor, durchschnittlicher Gewinn, durchschnittlicher Verlust und Haltedauer werden aus geschlossenen Round-Trips rekonstruiert. Offene Positionen werden konservativ nicht als abgeschlossene Trades gezaehlt.

## Rueckwaertskompatibilitaet

Das Dashboard ist nur eine neue Research-Komponente unter `tradingia/research`. Bestehende Module bleiben unveraendert.
