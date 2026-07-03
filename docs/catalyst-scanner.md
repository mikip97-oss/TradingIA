# Catalyst Scanner

Der Catalyst Scanner ist ein separater Scanner fuer technische Daytrading-Katalysatoren. Er veraendert weder GUI, `app.py` noch `scanner.py`.

## Ziel

Daytrading-Kandidaten entstehen oft durch starke Marktreaktionen, Volumen, Gaps, Momentum und ungewoehnliche Volatilitaet. Dieser Scanner bewertet solche technischen Catalyst-Faktoren ohne echte News-API.

## Faktoren

- Heute %
- Volumen-Faktor
- Gap oder starke Bewegung
- ROC
- Naehe zum Tageshoch
- aussergewoehnliche Volatilitaet

## Ausgabe

Die Ausgabe ist ein pandas DataFrame mit diesen Spalten:

- Aktie
- CatalystScore
- Empfehlung
- Heute %
- Volumen-Faktor
- ROC
- Gruende

## Hinweis

Der CatalystScore ist ein technischer Setup-Score. Er behauptet nicht, Nachrichten zu kennen oder Kursbewegungen sicher vorherzusagen. Echte News-Feeds, Sentiment und Event-Daten koennen spaeter modular ergaenzt werden.
