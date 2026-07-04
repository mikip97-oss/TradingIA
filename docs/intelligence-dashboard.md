# Intelligence Dashboard

Das Intelligence Dashboard erweitert die bestehende PySide6-App um den Modus `Top Chancen heute`. Die GUI wurde nicht neu geschrieben; der neue Modus nutzt die vorhandene Tabellen-, Detail- und Chartstruktur.

## Ziel

Das Dashboard verbindet vorhandene Komponenten:

- Intelligence Pipeline
- Daytrading Scanner
- Catalyst Scanner
- News Intelligence Engine
- Master Decision Engine

Es entwickelt keine neuen Trading-Algorithmen, sondern zeigt die finale Rangliste der bereits berechneten Scores.

## Anzeige

Die linke Tabelle zeigt:

- Rang
- Aktie
- FinalScore
- Empfehlung

Beim Anklicken einer Aktie zeigt das rechte Analysefeld:

- TradeScore, falls vorhanden
- DayTradeScore
- CatalystScore
- NewsScore
- KI %, falls vorhanden
- Marktregime, falls vorhanden
- wichtigste Gruende
- News Headline, Quelle und Veroeffentlichungszeit, falls Nachrichten vorhanden sind

## Fallback

Wenn kein `FINNHUB_API_KEY` vorhanden ist, laeuft das Dashboard trotzdem. Die Pipeline bewertet dann die technischen Scores und setzt den NewsScore konservativ auf 0 mit neutralem Sentiment.

## Chart

Die bestehende Chartansicht wird unveraendert weiterverwendet. Beim Anklicken einer Aktie wird wie bisher der Kursverlauf geladen.


## Sprint 18 Hinweis

Das Dashboard nutzt nun auch `TodayUpScore` und `OverextensionPenalty` aus der Intelligence Pipeline. Dadurch werden Vortages-Gewinner ohne heutige Fortsetzung nicht mehr automatisch hoch priorisiert.
