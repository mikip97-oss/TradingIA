# Momentum Confirmation Engine

Die Momentum Confirmation Engine bewertet ausschliesslich heutige Intraday-Bestaetigung. Sie soll verhindern, dass TradingIA Aktien bevorzugt, die nur gestern stark waren, heute aber kein echtes Kaufinteresse zeigen.

## Ziel

Der `MomentumConfirmationScore` liegt zwischen 0 und 100. Er ersetzt in der Intelligence Pipeline die alte interne TodayUpScore-Berechnung. Dadurch basiert `TodayUpScore` auf einer eigenstaendigen, testbaren Momentum-Komponente.

## Positive heutige Signale

- heutige Performance %
- Intraday-Volumen relativ zum Durchschnitt
- Naehe zum Tageshoch
- positiver ROC
- ADX als Trendstaerke
- RSI im bestaetigten Momentum-Bereich
- Gap-Up nur, wenn das Gap gehalten wird
- optionale relative Staerke gegen Nasdaq oder S&P 500 als vorbereiteter Platzhalter

## Risikoabzuege

- Gewinnmitnahmen nach starkem Vortagesanstieg
- Overextension nach Vortagesbewegung
- hohes Volumen bei fallendem Kurs
- negatives Intraday-Momentum
- Gap-Fill oder starker Abverkauf nach Gap-Up
- starke Intraday-Schwaeche
- weit vom Tageshoch entfernt
- sehr hoher RSI

## Integration

Die Intelligence Pipeline nutzt `score_momentum_confirmation` in `calculate_today_up_score`. Bestehende Scanner und GUI werden nicht veraendert. Wenn einzelne Felder wie Gap oder relative Staerke noch nicht vorhanden sind, werden sie einfach ignoriert.

```python
from tradingia.momentum import MomentumInput, score_momentum_confirmation

result = score_momentum_confirmation(
    MomentumInput(today_pct=2.1, volume_factor=1.8, distance_to_high_pct=0.5, roc=1.2)
)
```

## Hinweis

Der Score ist keine Kursprognose. Er bewertet, ob eine Aktie heute aktuell Momentum bestaetigt und ob Risiken gegen eine Fortsetzung sprechen.
