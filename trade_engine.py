def bewerte_trade(
    ki,
    adx,
    volumen,
    chance_risiko,
    abstand_52w_high,
    rsi,
    candle_score
):
    score = 0
    gruende = []

    # KI: nicht mehr zu streng
    if ki >= 70:
        score += 35
        gruende.append("KI stark")
    elif ki >= 60:
        score += 28
        gruende.append("KI positiv")
    elif ki >= 50:
        score += 20
        gruende.append("KI neutral")
    elif ki >= 40:
        score += 12
        gruende.append("KI vorsichtig")
    else:
        score += 6
        gruende.append("KI schwach")

    # Trendstärke
    if adx >= 30:
        score += 18
        gruende.append("Sehr starker Trend")
    elif adx >= 20:
        score += 14
        gruende.append("Solider Trend")
    elif adx >= 15:
        score += 8
        gruende.append("Leichter Trend")

    # Volumen
    if volumen >= 1.5:
        score += 18
        gruende.append("Stark erhöhtes Volumen")
    elif volumen >= 1.0:
        score += 10
        gruende.append("Volumen über Durchschnitt")
    elif volumen >= 0.5:
        score += 4
        gruende.append("Volumen akzeptabel")

    # Chance/Risiko
    if chance_risiko >= 2.5:
        score += 18
        gruende.append("Sehr gutes Chance/Risiko")
    elif chance_risiko >= 2.0:
        score += 15
        gruende.append("Gutes Chance/Risiko")
    elif chance_risiko >= 1.5:
        score += 8
        gruende.append("Akzeptables Chance/Risiko")

    # RSI
    if 45 <= rsi <= 70:
        score += 8
        gruende.append("RSI im gesunden Bereich")
    elif 40 <= rsi < 45:
        score += 3
        gruende.append("RSI noch akzeptabel")
    elif rsi > 75:
        score -= 8
        gruende.append("RSI überkauft")

    # 52-Wochen-Hoch
    if abstand_52w_high <= 5:
        score += 6
        gruende.append("Nahe am 52W-Hoch")
    elif abstand_52w_high <= 15:
        score += 3
        gruende.append("Relativ nahe am 52W-Hoch")

    score += candle_score
    if candle_score > 0:
        gruende.append("Positives Candlestick-Muster")
    elif candle_score < 0:
        gruende.append("Schwaches Candlestick-Muster")

    score = max(0, min(score, 100))

    if score >= 80:
        empfehlung = "🟢 Stark kaufen"
    elif score >= 70:
        empfehlung = "🟢 Kaufen"
    elif score >= 60:
        empfehlung = "🟡 Beobachten"
    elif score >= 50:
        empfehlung = "🟠 Watchlist"
    else:
        empfehlung = "🔴 Kein Trade"

    return round(score, 1), empfehlung, gruende