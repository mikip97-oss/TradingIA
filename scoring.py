def berechne_score(
    veraenderung,
    letzter_preis,
    ema20,
    ema50,
    ema200,
    rsi,
    macd,
    macd_signal,
    volumen_faktor,
    abstand_52w_high,
    candle_score
):
    score = 0
    gruende = []

    if veraenderung > 0:
        score += 5
        gruende.append("Positive Tagesbewegung")
    if veraenderung > 1:
        score += 10
        gruende.append("Starkes Momentum")
    if veraenderung > 3:
        score += 15
        gruende.append("Sehr starkes Tagesmomentum")

    if letzter_preis > ema20:
        score += 10
        gruende.append("Kurs über EMA20")
    if ema20 > ema50:
        score += 15
        gruende.append("EMA20 über EMA50")
    if ema50 > ema200:
        score += 15
        gruende.append("Langfristiger Aufwärtstrend")

    if 45 <= rsi <= 70:
        score += 10
        gruende.append("RSI im gesunden Bereich")
    elif rsi > 75:
        score -= 10
        gruende.append("RSI möglicherweise überkauft")

    if macd > macd_signal:
        score += 10
        gruende.append("MACD bullisch")

    if volumen_faktor > 1:
        score += 10
        gruende.append("Volumen über Durchschnitt")
    if volumen_faktor > 1.5:
        score += 10
        gruende.append("Stark erhöhtes Volumen")

    if abstand_52w_high < 10:
        score += 10
        gruende.append("Nahe am 52-Wochen-Hoch")
    if abstand_52w_high < 3:
        score += 10
        gruende.append("Sehr nahe am 52-Wochen-Hoch")

    score += candle_score

    if candle_score > 0:
        gruende.append("Positives Candlestick-Muster")
    elif candle_score < 0:
        gruende.append("Schwaches Candlestick-Muster")

    return score, gruende


def berechne_endscore(
    technik,
    ki,
    adx,
    volumen,
    candle_score
):
    score = 0

    # Technik stärker gewichten, weil KI aktuell konservativ ist
    score += technik * 0.65

    # KI als Bestätigung
    score += ki * 0.25

    # Trendstärke
    if adx > 30:
        score += 8
    elif adx > 20:
        score += 5
    elif adx > 15:
        score += 3

    # Volumen
    if volumen > 1.5:
        score += 4
    elif volumen > 1:
        score += 2

    # Candlestick
    score += candle_score

    return round(min(score, 100), 1)


def empfehlung(endscore):
    if endscore >= 80:
        return "🟢 Stark kaufen"
    elif endscore >= 70:
        return "🟢 Kaufen"
    elif endscore >= 60:
        return "🟡 Beobachten"
    elif endscore >= 50:
        return "🟠 Watchlist"
    else:
        return "🔴 Kein Trade"