def erstelle_ki_analyse(aktie):
    name = aktie.get("Aktie", "")
    score = aktie.get("Score", 0)
    empfehlung = aktie.get("Empfehlung", "")
    rsi = aktie.get("RSI", 0)
    volumen = aktie.get("Volumen-Faktor", 0)
    heute = aktie.get("Heute %", 0)
    chance_risiko = aktie.get("Chance/Risiko", 0)
    einstieg = aktie.get("Einstieg", 0)
    stop = aktie.get("Stop-Loss", 0)
    ziel = aktie.get("Ziel", 0)
    muster = aktie.get("Muster", "Keine")

    analyse = []

    analyse.append(f"KI-Analyse für {name}")
    analyse.append("=" * 40)
    analyse.append(f"Score: {score}/100")
    analyse.append(f"Empfehlung: {empfehlung}")
    analyse.append("")

    if score >= 90:
        analyse.append("Die Aktie zeigt aktuell ein sehr starkes technisches Setup.")
    elif score >= 75:
        analyse.append("Die Aktie ist technisch interessant und sollte beobachtet werden.")
    elif score >= 60:
        analyse.append("Die Aktie zeigt erste positive Signale, ist aber noch kein klares Top-Setup.")
    else:
        analyse.append("Die Aktie ist aktuell kein bevorzugter Trade.")

    analyse.append("")

    analyse.append("Wichtige Punkte:")

    if heute > 3:
        analyse.append(f"+ Starkes Momentum heute: {heute}%")
    elif heute > 0:
        analyse.append(f"+ Positive Tagesbewegung: {heute}%")
    else:
        analyse.append(f"- Schwache Tagesbewegung: {heute}%")

    if volumen >= 1.5:
        analyse.append(f"+ Deutlich erhöhtes Volumen: {volumen}x")
    elif volumen >= 1:
        analyse.append(f"+ Volumen über Durchschnitt: {volumen}x")
    else:
        analyse.append(f"- Volumen noch unterdurchschnittlich: {volumen}x")

    if 45 <= rsi <= 70:
        analyse.append(f"+ RSI im gesunden Momentum-Bereich: {rsi}")
    elif rsi > 75:
        analyse.append(f"- RSI möglicherweise überkauft: {rsi}")
    else:
        analyse.append(f"- RSI noch nicht ideal: {rsi}")

    if muster != "Keine":
        analyse.append(f"+ Candlestick-Muster erkannt: {muster}")

    if chance_risiko >= 2:
        analyse.append(f"+ Gutes Chance/Risiko-Verhältnis: {chance_risiko}")
    else:
        analyse.append(f"- Chance/Risiko-Verhältnis eher schwach: {chance_risiko}")

    analyse.append("")
    analyse.append("Trade-Plan:")
    analyse.append(f"Einstieg: {einstieg}")
    analyse.append(f"Stop-Loss: {stop}")
    analyse.append(f"Ziel: {ziel}")

    analyse.append("")
    analyse.append("Hinweis: Das ist keine Anlageberatung. Der Bot liefert nur eine technische Einschätzung.")

    return "\n".join(analyse)