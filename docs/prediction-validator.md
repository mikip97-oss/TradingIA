# Prediction Validator

Der Prediction Validator speichert TradingIA-Empfehlungen und wertet spaeter aus, ob sie tatsaechlich erfolgreich waren. Das Ziel ist Validierung und Research-Feedback, nicht Live-Trading.

## Ziel

TradingIA soll nicht nur Scores berechnen, sondern messen, ob `TodayUpScore` und `FinalScore` spaeter wirklich gute Aktien identifizieren. Empfehlungen werden als CSV gespeichert und koennen nach einem frei waehlbaren Horizont mit spaeteren Kursen verglichen werden.

## Speicherung

`save_daily_recommendations` schreibt taegliche Empfehlungen als CSV. Gespeichert werden:

- Datum
- Aktie
- TodayUpScore
- FinalScore
- Empfehlung
- Einstiegskurs
- Teil-Scores als JSON

```python
from tradingia.validation import save_daily_recommendations

file_path = save_daily_recommendations(leaderboard, "validation_logs", recommendation_date="2026-07-04")
```

## Auswertung

`evaluate_recommendations` laedt eine oder mehrere gespeicherte CSV-Dateien und vergleicht sie mit spaeteren Kursdaten. Die Kursdaten werden als DataFrame uebergeben, damit die Komponente offline testbar bleibt und keine Broker- oder Order-Anbindung benoetigt.

```python
from tradingia.validation import evaluate_recommendations

evaluated, metrics = evaluate_recommendations(file_path, future_prices, horizon_days=1)
```

Die Auswertung berechnet:

- Performance %
- Treffer oder Fehlschlag
- Trefferquote
- Durchschnittliche Rendite
- Durchschnittlicher Gewinn
- Durchschnittlicher Verlust
- Beste Score-Schwelle

## Grenzen

Diese Komponente fuehrt keine echten Orders aus und verbindet sich mit keinem Broker. Sie dient ausschliesslich dazu, Empfehlungen historisch zu validieren und Score-Schwellen datenbasiert zu verbessern.
