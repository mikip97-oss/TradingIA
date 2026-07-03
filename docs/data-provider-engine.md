# Data Provider Engine

Die Data Provider Engine ist eine neue modulare Datenanbieter-Schicht fuer TradingIA. Sie bereitet die Architektur darauf vor, Scanner spaeter von direkten `yfinance`-Aufrufen zu entkoppeln.

## Ziel

Yahoo Finance kann bei grossen Scans HTTP 401/403 oder leere Antworten liefern. Statt diese Fehler in jedem Scanner einzeln zu behandeln, sollen Datenanbieter kuenftig eine einheitliche Schnittstelle implementieren.

## Schnittstelle

Jeder Provider soll diese Methode anbieten:

```python
def get_history(self, ticker: str, period: str, interval: str) -> pandas.DataFrame:
    ...
```

Bei Fehlern wird ein leerer OHLCV-DataFrame zurueckgegeben, damit Apps und Scanner nicht abbrechen. Details koennen ueber `last_error` eingesehen werden.

## Erste Implementierung

- `YahooFinanceProvider`

Der Provider kapselt `yfinance.download(...)`, normalisiert die Spalten auf `Open`, `High`, `Low`, `Close`, `Volume` und gibt bei Downloadfehlern einen leeren DataFrame zurueck.

## Spaetere Erweiterungen

Die Struktur ist vorbereitet fuer weitere Anbieter wie:

- Polygon
- Finnhub
- Alpaca
- Interactive Brokers
- lokale Datenbanken oder Caches

## Rueckwaertskompatibilitaet

Bestehende Scanner wurden in diesem Sprint nicht umgestellt. Die neue Schicht ist bewusst parallel eingefuehrt, damit die Migration spaeter klein und kontrolliert erfolgen kann.
