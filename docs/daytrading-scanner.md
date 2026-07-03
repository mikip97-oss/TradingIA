# Daytrading Scanner

Der Daytrading Scanner ist ein separater Scanner fuer kurzfristige Tages-Setups. Er veraendert weder die bestehende GUI noch `scanner.py`.

## Ziel

Der bestehende Scanner ist eher Swing-Trading-orientiert. Der Daytrading Scanner bewertet dagegen kurzfristige Setups anhand von Intraday-Kriterien. Er behauptet nicht, sichere Vorhersagen zu liefern, sondern erstellt ein technisches Chancen-Ranking.

## Kriterien

- heutige Kursveraenderung in Prozent
- Volumen-Faktor
- Gap oder starke Bewegung
- RSI
- ADX
- ROC
- Naehe zum Tageshoch
- starke relative Bewegung

## Ausgabe

Die Ausgabe ist ein pandas DataFrame mit diesen Spalten:

- Aktie
- DayTradeScore
- Empfehlung
- Einstieg
- Stop-Loss
- Ziel
- Heute %
- RSI
- Volumen-Faktor
- ADX
- ROC
- Gruende

## Empfehlungen

- ab 80: 🟢 Sehr stark
- ab 70: 🟢 Trade-Kandidat
- ab 60: 🟡 Beobachten
- darunter: 🔴 Kein Daytrade

## Nutzung

```python
from daytrading_scanner import scan_daytrading_market

df = scan_daytrading_market(tickers=["AAPL", "MSFT", "NVDA"], max_workers=4)
print(df)
```

## Hinweis

Der DayTradeScore ist ein Setup-Score, keine Garantie. Vor jedem echten Trade muessen Liquiditaet, Spread, Nachrichtenlage, Marktumfeld und Risiko geprueft werden.
