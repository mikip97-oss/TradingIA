# High-Speed Scanner

Dieser MVP-Speed-Schritt fuehrt paralleles Scannen fuer TradingIA ein. Ziel ist direkter Nutzen: mehr Aktien schneller scannen, ohne eine grosse Architekturumstellung.

## Was neu ist

- Die bestehende Scanner-Logik wurde in `scan_ticker(ticker)` extrahiert.
- `scan_market()` verarbeitet Ticker parallel mit `ThreadPoolExecutor`.
- Die maximale Anzahl paralleler Worker ist ueber `SCANNER_MAX_WORKERS` in `config.py` einstellbar.
- Einzelne Ticker-Fehler werden abgefangen und brechen den Gesamtscan nicht ab.
- `get_aktien_liste()` behaelt die bestehende Scanner-Logik bei.
- `TOP_ANZAHL = 50` kann bis zu 50 Top-Ergebnisse anzeigen.

## Nutzung

```python
from scanner import scan_market

df = scan_market()
print(df)
```

Fuer Tests oder gezielte Scans kann eine Tickerliste uebergeben werden:

```python
df = scan_market(max_workers=4, tickers=["AAPL", "MSFT", "NVDA"])
```

## Rueckwaertskompatibilitaet

Die Einstiegspunkte `get_aktien_liste()` und `scan_market()` bleiben erhalten. Bestehende Spalten und Bewertungslogik bleiben erhalten. Die GUI kann weiterhin `scan_market()` importieren. In diesem Sprint wurden GUI-Dateien nicht veraendert.

## Grenzen

Die Beschleunigung nutzt bewusst nur die Python-Standardbibliothek. Es gibt noch kein Caching, keine persistenten Marktdaten und keine professionelle Rate-Limit-Steuerung. Das ist ein MVP-Speed-Schritt, kein vollstaendiger Daten-Service.
