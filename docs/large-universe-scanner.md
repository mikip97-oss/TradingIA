# Großer Aktien-Scanner

Dieser MVP-Speed-Schritt erweitert die Universe-Logik fuer TradingIA. Ziel ist, schnell deutlich mehr Aktien scannen zu koennen, ohne die bestehende GUI oder `scanner.py` zu veraendern.

## Enthalten

- S&P-500-Ticker laden
- Nasdaq-100-Ticker laden
- Yahoo-kompatible Ticker-Normalisierung, zum Beispiel `BRK.B` zu `BRK-B`
- Duplikate entfernen
- bestehende Fallback-Liste behalten
- robust weiterlaufen, wenn eine Quelle nicht erreichbar ist

## Wichtige Funktionen

- `lade_sp500_ticker()`
- `lade_nasdaq100_ticker()`
- `lade_fallback_ticker()`
- `lade_grosses_universum()`
- `lade_standard_universum()`

## Konfiguration

`TOP_ANZAHL` ist auf `50` gesetzt. Damit kann der Scanner mehr Top-Kandidaten anzeigen, sofern der bestehende Scanner diese Konfiguration nutzt.

`NUTZE_GROSSES_UNIVERSUM = True` aktiviert das große Universum als Standard fuer neue Scanner-Integrationen.

## Rueckwaertskompatibilitaet

Die Legacy-Funktion `lade_sp500_ticker()` bleibt erhalten. Die GUI und `scanner.py` wurden in diesem Schritt nicht veraendert.

## Naechster sinnvoller Schritt

Wenn die lokale Legacy-`scanner.py` verfuegbar ist, sollte `get_aktien_liste()` minimal auf `lade_standard_universum()` umgestellt werden. Danach kann optional eine kleine Parallelisierung der Ticker-Downloads ergaenzt werden.
