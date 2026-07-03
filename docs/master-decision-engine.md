# Master Decision Engine

Die Master Decision Engine kombiniert mehrere TradingIA-Scores zu einer zentralen Handelsbewertung. Sie wird noch nicht in die GUI integriert, sondern steht als neue modulare Komponente unter `tradingia/decision` bereit.

## Ziel

TradingIA hat inzwischen mehrere getrennte Signale:

- TradeScore
- DayTradeScore
- CatalystScore
- NewsScore
- KI %
- Market Regime

Die Decision Engine erzeugt daraus einen `FinalScore` von 0 bis 100.

## Gewichtung

Die Gewichtung ist konfigurierbar ueber `DecisionWeights`. Standardwerte:

- DayTradeScore: 30 %
- CatalystScore: 25 %
- NewsScore: 20 %
- TradeScore: 15 %
- KI %: 10 %

Market Regime wirkt als Bonus oder Malus. Ein Bull-Regime kann starke Long-Setups bestaetigen, ein Bear-Regime kann sie abschwaechen.

## Ausgabe

Die Ausgabe enthaelt:

- Aktie
- FinalScore
- Empfehlung
- wichtigste Gruende
- Teil-Scores

## Empfehlungen

- ab 90: ⭐⭐⭐⭐⭐ Top Chance
- ab 80: ⭐⭐⭐⭐ Sehr interessant
- ab 70: ⭐⭐⭐ Beobachten
- darunter: Kein Trade

## Hinweis

Der FinalScore ist eine zusammenfassende technische und informationsbasierte Bewertung. Er ist keine sichere Prognose und ersetzt kein Risiko-Management.
