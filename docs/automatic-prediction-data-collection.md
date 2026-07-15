# Automatische Prediction-Datensammlung

Sprint 25 verbindet das bestehende Intelligence Dashboard mit dem Prediction Dataset Builder. Nach einem erfolgreichen Scan im Modus `Top Chancen heute` werden die Ergebniszeilen automatisch nach `data/prediction_dataset.csv` geschrieben.

## Verhalten

- Gespeichert wird nur der Modus `Top Chancen heute`.
- Swing-Scanner und Daytrading-Scanner schreiben keine Prediction-Daten.
- Leere Ergebnisse werden nicht gespeichert.
- Der Zeitstempel des Scans wird beim Speichern gesetzt.
- Die Deduplizierung bleibt im Dataset Builder zentral erhalten.
- Speicherfehler brechen die GUI nicht ab, sondern werden als Statusmeldung angezeigt.

## Warum das wichtig ist

TradingIA sammelt dadurch echte Intelligence-Signale im laufenden Betrieb. Der Prediction Dataset Labeler kann diese Signale spaeter mit `Return_1h`, `Return_2h`, `Return_EOD` und Treffer-Spalten anreichern. Es wird noch kein Modell trainiert und es werden keine Orders erzeugt.

## Betroffene Module

Die Integration liegt bewusst in `app.py`, weil dort bekannt ist, welcher Scanner-Modus gerade erfolgreich abgeschlossen wurde. Bestehende Scanner-Dateien bleiben unveraendert.

## Vollständigkeit der Trainingsdaten

Die Intelligence Pipeline reicht zentrale Trainingsfeatures an den Dataset Builder weiter: Einstiegskurs beziehungsweise aktueller Kurs, FinalScore, TodayUpScore, TrendScore, MomentumConfirmationScore, DayTradeScore, CatalystScore, NewsScore, TradeScore, KI %, RSI, ADX, ROC, Volumen-Faktor und Empfehlung. Fehlende numerische Werte werden als `NaN` gespeichert, nicht als leere Zeichenketten. Auch `Kein Trade`-Zeilen bleiben im Datensatz, weil sie als negative Trainingsbeispiele wichtig sind.
