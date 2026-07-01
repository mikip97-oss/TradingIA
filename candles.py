def erkenne_candles(data):
    open_ = data["Open"].squeeze()
    high = data["High"].squeeze()
    low = data["Low"].squeeze()
    close = data["Close"].squeeze()

    o1 = float(open_.iloc[-1])
    h1 = float(high.iloc[-1])
    l1 = float(low.iloc[-1])
    c1 = float(close.iloc[-1])

    o2 = float(open_.iloc[-2])
    c2 = float(close.iloc[-2])

    muster = []
    score = 0

    body = abs(c1 - o1)
    range_ = h1 - l1

    if range_ == 0:
        return {"Muster": "Keine", "CandleScore": 0}

    upper_shadow = h1 - max(o1, c1)
    lower_shadow = min(o1, c1) - l1

    # Bullish Engulfing
    if c2 < o2 and c1 > o1 and c1 > o2 and o1 < c2:
        muster.append("Bullish Engulfing")
        score += 15

    # Hammer
    if lower_shadow > body * 2 and upper_shadow < body:
        muster.append("Hammer")
        score += 10

    # Doji
    if body / range_ < 0.1:
        muster.append("Doji")
        score -= 5

    if not muster:
        muster.append("Keine")

    return {
        "Muster": ", ".join(muster),
        "CandleScore": score
    }