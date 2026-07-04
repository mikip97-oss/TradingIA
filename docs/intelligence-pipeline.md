# Intelligence Pipeline

Die Intelligence Pipeline ist die zentrale Orchestrierung fuer die aktuellen TradingIA-Scores. Sie veraendert weder GUI noch bestehende Scanner, sondern sammelt deren Ergebnisse ein und erzeugt mit der Master Decision Engine eine finale Rangliste.

## Ziel

Pro Aktie werden folgende Signale zusammengefuehrt:

- DayTradeScore aus dem Daytrading Scanner
- CatalystScore aus dem Catalyst Scanner
- NewsScore und Sentiment aus der News Intelligence Engine
- FinalScore und Empfehlung aus der Master Decision Engine

## Ablauf

1. Eine Ticker-Liste wird normalisiert und dedupliziert.
2. Der Daytrading Scanner wird fuer dieselben Ticker ausgefuehrt.
3. Der Catalyst Scanner wird fuer dieselben Ticker ausgefuehrt.
4. Die News Intelligence Engine laedt Nachrichten, standardmaessig ueber `FinnhubNewsProvider`.
5. Nachrichten werden nur bewertet, wenn Headline oder Summary den Ticker oder einen bekannten Firmennamen enthalten.
6. Die Master Decision Engine erzeugt den finalen Score.
7. Die Ausgabe wird nach `FinalScore` absteigend sortiert.

## Fallback ohne Finnhub API-Key

Wenn `FINNHUB_API_KEY` nicht gesetzt ist, liefert der Finnhub Provider eine leere Nachrichtenliste. Die Pipeline laeuft trotzdem weiter und setzt `NewsScore` auf 0 mit neutralem Sentiment. Es wird keine kostenpflichtige API erzwungen.

## Ausgabe

Die Pipeline liefert ein DataFrame mit:

- Aktie
- FinalScore
- Empfehlung
- DayTradeScore
- CatalystScore
- NewsScore
- Sentiment
- TodayUpScore
- OverextensionPenalty
- wichtigste Gruende
- News Headline, falls vorhanden
- News Quelle, falls vorhanden
- News Veroeffentlichungszeit, falls vorhanden

## Beispiel

```python
from tradingia.intelligence import IntelligencePipeline

pipeline = IntelligencePipeline(company_names={"AAPL": "Apple", "MSFT": "Microsoft"})
leaderboard = pipeline.run(["AAPL", "MSFT", "NVDA"])
print(leaderboard)
```

## Robustheit

Fehler in einem Scanner oder beim Laden einzelner News werden abgefangen. Die Pipeline erzeugt weiterhin eine Rangliste fuer die uebrigen verfuegbaren Signale. Dadurch bleibt sie fuer Research-Laeufe und spaetere GUI-Integration geeignet.


## Sprint 18: Vortages-Momentum und Overextension

Die Pipeline unterscheidet bewusst zwischen Vortages-Momentum und heutiger Intraday-Staerke. Ein starker Kursanstieg am Vortag erhoeht den Score nicht automatisch. Er wird nur als Risiko-Kontext genutzt, weil nach starken Bewegungen haeufig Gewinnmitnahmen folgen koennen.

### TodayUpScore

Der TodayUpScore belohnt nur bestaetigtes Fortsetzungs-Momentum:

- heutige positive Kursreaktion
- erhoehtes heutiges Volumen
- Naehe zum Tageshoch
- positiver ROC
- relevante News, wenn der Kurs heute ebenfalls positiv reagiert

### Overextension-/Pullback-Abzug

Die Pipeline reduziert den Score, wenn ein Setup ueberdehnt oder nicht bestaetigt wirkt:

- starker Vortagesanstieg, aber heute schwache oder negative Bewegung
- Aktie ist weit vom Tageshoch entfernt
- RSI ist sehr hoch
- NewsScore ist hoch, aber die heutige Kursreaktion bleibt schwach

Dadurch sollen Aktien nicht nur deshalb als Top-Kandidaten erscheinen, weil sie gestern stark gestiegen sind. Die finale Rangliste bevorzugt echte heutige Fortsetzung statt nachlaufendes Vortages-Momentum.


## Sprint 20: Momentum Confirmation Engine

Der TodayUpScore wird nun ueber die neue `MomentumConfirmationEngine` berechnet. Dadurch zaehlen nur heutige Signale wie Performance, Volumen, Naehe zum Tageshoch, ROC, ADX, RSI und gehaltene Gap-Ups. Vortagesbewegungen werden nicht belohnt, sondern nur als Risiko fuer Gewinnmitnahmen und Overextension verwendet.
