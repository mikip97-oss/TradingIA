# Dataset Labeling Runner

Sprint 26 ergaenzt eine ausfuehrbare Datei im Projektstamm: `label_prediction_dataset.py`. Damit koennen offene Zeilen in `data/prediction_dataset.csv` nachtraeglich mit Returns und Treffer-Spalten gelabelt werden.

## Nutzung

Standardpfad:

```powershell
python label_prediction_dataset.py
```

Eigener Dataset-Pfad:

```powershell
python label_prediction_dataset.py --dataset-path data/prediction_dataset.csv
```

## Ausgabe

Der Runner gibt eine kurze Zusammenfassung aus:

- Anzahl geladener Zeilen
- Anzahl neu gelabelter Zeilen
- Anzahl weiterhin offener Zeilen
- Speicherpfad

## Verhalten bei fehlenden Daten

Wenn die Dataset-Datei noch nicht existiert, erscheint eine verstaendliche Meldung und das Programm endet ohne langen Traceback. Wenn fuer einzelne Aktien noch keine ausreichenden Kursdaten verfuegbar sind, bleiben diese Zeilen offen; die uebrigen Aktien werden weiter verarbeitet.

## Grenzen

Der Runner verwendet ausschliesslich den bestehenden Dataset Labeler und die vorhandene DataProvider-Schicht. Es gibt keine Broker-Anbindung, keine Orders und kein Modelltraining. GUI und Scanner bleiben unveraendert.
