# Prediction Dataset Labeler

Sprint 24 ergaenzt den bestehenden Prediction Dataset Builder um einen separaten Labeler unter `tradingia/ml_dataset/labeler.py`.

## Zweck

Der Builder speichert Signale zum Zeitpunkt eines Intelligence-Scans. Der Labeler ergaenzt diese Signale spaeter mit den tatsaechlichen Kursentwicklungen. Dadurch entsteht schrittweise ein Trainings- und Validierungsdatensatz, ohne echte Orders, Broker-Anbindung oder ML-Bibliotheken zu verwenden.

## Datenquelle

Der Labeler nutzt ausschliesslich die bestehende DataProvider-Schicht. Standardmaessig wird `YahooFinanceProvider` verwendet. Fuer Tests oder spaetere Anbieter kann jeder Provider eingesetzt werden, der `get_history(ticker, period, interval)` bereitstellt.

## Nutzung

```python
from tradingia.ml_dataset import label_prediction_dataset

labeled_dataset, summary = label_prediction_dataset("data/prediction_dataset.csv")
```

Optional kann ein eigener Provider uebergeben werden:

```python
labeled_dataset, summary = label_prediction_dataset(
    "data/prediction_dataset.csv",
    data_provider=my_provider,
)
```

## Berechnete Labels

- `Return_1h`
- `Return_2h`
- `Return_EOD`
- `Treffer_1h`
- `Treffer_2h`
- `Treffer_EOD`

Ein Treffer ist definiert als `Return > 0 %`.

## Schutz bestehender Labels

Bereits gefuellte Label-Felder werden nicht ueberschrieben. Der Labeler aktualisiert nur leere Felder. Dadurch koennen manuell korrigierte oder bereits validierte Werte erhalten bleiben.

## Auswirkungen

GUI, `scanner.py`, `daytrading_scanner.py` und `catalyst_scanner.py` bleiben unveraendert. Die Komponente arbeitet nur auf dem gespeicherten CSV-Datensatz und ueber die vorhandene DataProvider-Schnittstelle.
