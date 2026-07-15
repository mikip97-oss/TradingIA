# Automatische Datenpipeline und Performance Center

Dieses Paket verbindet die bisherige Intelligence Pipeline, den Prediction Dataset Builder, den Dataset Labeler und ein neues Performance Center. Es werden keine echten Orders erzeugt, keine Broker angebunden und keine neue Trading-Strategie eingefuehrt.

## Daily Intelligence Runner

Startet den taeglichen Top-Chancen-Scan und speichert die Ergebnisse in `data/prediction_dataset.csv`.

```powershell
python daily_intelligence_runner.py --universe-size 100 --max-workers 8 --top-candidates 50 --dataset-path data/prediction_dataset.csv --output-dir reports/daily
```

Konfigurierbar sind Universumsgroesse, maximale Worker, Anzahl gespeicherter Kandidaten, Dataset-Pfad und Ausgabeordner. API-Keys werden nicht hart codiert.

## Daily Labeling Runner

Labelt offene Dataset-Zeilen zum Tagesabschluss. Wenn fuer einzelne Aktien noch keine ausreichenden Kursdaten verfuegbar sind, bleiben diese Zeilen offen; die Verarbeitung laeuft weiter.

```powershell
python daily_labeling_runner.py --dataset-path data/prediction_dataset.csv --output-dir reports/daily
```

## Logging

Beide Tages-Runner schreiben nach:

```text
logs/daily_pipeline.log
```

Geloggte Informationen umfassen Startzeit, Endstatus, Laufzeit, verarbeitete Aktien, Fehler sowie gespeicherte oder gelabelte Zeilen.

## Performance Center

Erstellt CSV- und HTML-Reports aus dem Prediction Dataset.

```powershell
python performance_report.py --dataset-path data/prediction_dataset.csv --output-dir reports/performance
```

Exporte:

- `reports/performance/summary.csv`
- `reports/performance/score_buckets.csv`
- `reports/performance/factor_analysis.csv`
- `reports/performance/report.html`

Das Performance Center berechnet Gesamtmetriken, Score-Buckets, Faktoranalyse, beste/schlechteste Aktien, Wochentage, Uhrzeiten und Score-Schwellen. Mindestens 20 gelabelte Zeilen werden verlangt, bevor Aussagen als belastbar markiert werden.

## Windows-Aufgabenplanung

1. Windows-Aufgabenplanung oeffnen.
2. Neue Aufgabe erstellen.
3. Trigger fuer den Intelligence Runner z. B. werktags kurz nach Marktstart oder in gewuenschten Intervallen setzen.
4. Aktion: `python` starten.
5. Argumente: `daily_intelligence_runner.py --universe-size 100 --max-workers 8 --top-candidates 50`.
6. Starten in: Projektordner von TradingIA.
7. Zweite Aufgabe fuer den Tagesabschluss anlegen.
8. Aktion: `python`.
9. Argumente: `daily_labeling_runner.py --dataset-path data/prediction_dataset.csv`.
10. Starten in: Projektordner von TradingIA.

Es ist keine externe Scheduling-Bibliothek erforderlich.
