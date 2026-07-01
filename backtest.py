import yfinance as yf
import pandas as pd

from config import DATEN_INTERVAL
from indicators import berechne_indikatoren
from performance import performance_auswerten


AKTIEN = ["AMD", "RIVN", "MU", "HOOD", "TSLA"]

BACKTEST_ZEITRAUM = "2y"
HALTEDAUER_TAGE = 5
MIN_DATENPUNKTE = 60
MIN_SCORE = 70

STARTKAPITAL = 10000
RISIKO_PRO_TRADE = 0.02


def backtest_aktie(ticker):
    data = yf.download(
        ticker,
        period=BACKTEST_ZEITRAUM,
        interval=DATEN_INTERVAL,
        progress=False,
        auto_adjust=True
    )

    if len(data) < MIN_DATENPUNKTE + HALTEDAUER_TAGE:
        return []

    close_all = data["Close"].squeeze()
    trades = []

    for i in range(MIN_DATENPUNKTE, len(data) - HALTEDAUER_TAGE):
        teil = data.iloc[:i].copy()

        close = teil["Close"].squeeze()
        volume = teil["Volume"].squeeze()

        preis = float(close.iloc[-1])
        preis_gestern = float(close.iloc[-2])
        veraenderung = ((preis - preis_gestern) / preis_gestern) * 100

        volumen_heute = float(volume.iloc[-1])
        volumen_durchschnitt = float(volume.iloc[-21:-1].mean())

        if volumen_durchschnitt == 0:
            continue

        volumen_faktor = volumen_heute / volumen_durchschnitt

        indikatoren = berechne_indikatoren(teil)

        rsi = indikatoren["RSI"]
        ema20 = indikatoren["EMA20"]
        ema50 = indikatoren["EMA50"]
        atr = indikatoren["ATR"]

        score = 0

        if veraenderung > 0:
            score += 10
        if veraenderung > 1:
            score += 10
        if veraenderung > 3:
            score += 15

        if volumen_faktor > 1:
            score += 15
        if volumen_faktor > 1.5:
            score += 10

        if preis > ema20:
            score += 15
        if ema20 > ema50:
            score += 15

        if 45 <= rsi <= 70:
            score += 10

        if score >= MIN_SCORE:
            einstieg = float(close_all.iloc[i])
            ausstieg = float(close_all.iloc[i + HALTEDAUER_TAGE])

            stop_loss = einstieg - (atr * 1.5)
            risiko_pro_aktie = einstieg - stop_loss

            if risiko_pro_aktie <= 0:
                continue

            max_verlust_dollar = STARTKAPITAL * RISIKO_PRO_TRADE
            anzahl_aktien = max_verlust_dollar / risiko_pro_aktie

            gewinn_verlust = (ausstieg - einstieg) * anzahl_aktien
            rendite_prozent = ((ausstieg - einstieg) / einstieg) * 100

            trades.append({
                "Aktie": ticker,
                "Score": score,
                "Einstieg": round(einstieg, 2),
                "Ausstieg": round(ausstieg, 2),
                "Stop-Loss": round(stop_loss, 2),
                "Aktien": round(anzahl_aktien, 2),
                "Gewinn $": round(gewinn_verlust, 2),
                "Rendite %": round(rendite_prozent, 2),
            })

    return trades


def main():
    alle_trades = []

    for aktie in AKTIEN:
        print(f"Teste {aktie}...")
        trades = backtest_aktie(aktie)
        alle_trades.extend(trades)

    if not alle_trades:
        print("Keine Trades gefunden.")
        return

    df = pd.DataFrame(alle_trades)

    gewinner = df[df["Gewinn $"] > 0]
    verlierer = df[df["Gewinn $"] <= 0]

    print("\nBacktest Ergebnis:")
    print(f"Anzahl Trades: {len(df)}")
    print(f"Gewinnquote: {round(len(gewinner) / len(df) * 100, 2)} %")
    print(f"Durchschnittlicher Trade: {round(df['Gewinn $'].mean(), 2)} $")
    print(f"Durchschnittlicher Gewinn: {round(gewinner['Gewinn $'].mean(), 2)} $")
    print(f"Durchschnittlicher Verlust: {round(verlierer['Gewinn $'].mean(), 2)} $")
    print(f"Gesamtergebnis: {round(df['Gewinn $'].sum(), 2)} $")

    performance_auswerten(df["Gewinn $"].tolist(), startkapital=STARTKAPITAL)


if __name__ == "__main__":
    main()