import yfinance as yf
import pandas as pd

from config import DATEN_INTERVAL
from feature_builder import baue_features
from ai.ai_predict import ki_vorhersage


AKTIEN = ["AMD", "TSLA", "AAPL", "NVDA", "MSFT", "MU", "HOOD", "RIVN", "AMZN", "GOOGL"]

BACKTEST_ZEITRAUM = "3y"
MIN_DATENPUNKTE = 220
HALTEDAUER_TAGE = 5
MIN_KI_PROZENT = 50


def ki_backtest_aktie(ticker):
    data = yf.download(
        ticker,
        period=BACKTEST_ZEITRAUM,
        interval=DATEN_INTERVAL,
        progress=False,
        auto_adjust=True,
    )

    if len(data) < MIN_DATENPUNKTE + HALTEDAUER_TAGE:
        return []

    close_all = data["Close"].squeeze()
    trades = []

    for i in range(MIN_DATENPUNKTE, len(data) - HALTEDAUER_TAGE):
        try:
            feature_dict = baue_features(data, index=i)

            if feature_dict is None:
                continue

            ki_prozent = ki_vorhersage(feature_dict)

            einstieg = float(close_all.iloc[i])
            ausstieg = float(close_all.iloc[i + HALTEDAUER_TAGE])
            rendite = ((ausstieg - einstieg) / einstieg) * 100

            if ki_prozent >= MIN_KI_PROZENT:
                trades.append({
                    "Aktie": ticker,
                    "KI %": round(ki_prozent, 1),
                    "Einstieg": round(einstieg, 2),
                    "Ausstieg": round(ausstieg, 2),
                    "Rendite %": round(rendite, 2),
                })

        except Exception:
            continue

    return trades


def auswertung(df, titel):
    if df.empty:
        print(f"\n{titel}: Keine Trades")
        return

    gewinner = df[df["Rendite %"] > 0]
    verlierer = df[df["Rendite %"] <= 0]

    print(f"\n{titel}")
    print("-" * 50)
    print(f"Anzahl Trades: {len(df)}")
    print(f"Gewinnquote: {round(len(gewinner) / len(df) * 100, 2)} %")
    print(f"Ø Trade: {round(df['Rendite %'].mean(), 2)} %")
    print(f"Ø Gewinn: {round(gewinner['Rendite %'].mean(), 2)} %")

    if len(verlierer) > 0:
        print(f"Ø Verlust: {round(verlierer['Rendite %'].mean(), 2)} %")
    else:
        print("Ø Verlust: keine Verlierer")

    print(f"Gesamtergebnis: {round(df['Rendite %'].sum(), 2)} %")


def main():
    alle_trades = []

    for aktie in AKTIEN:
        print(f"Teste {aktie}...")
        trades = ki_backtest_aktie(aktie)
        alle_trades.extend(trades)

    if not alle_trades:
        print("Keine KI-Trades gefunden.")
        return

    df = pd.DataFrame(alle_trades)

    auswertung(df, "Gesamter KI-Backtest")

    print("\nKI-Bereiche:")
    print("=" * 50)

    bereiche = [
        (50, 60),
        (60, 70),
        (70, 80),
        (80, 90),
        (90, 101),
    ]

    for minimum, maximum in bereiche:
        gruppe = df[(df["KI %"] >= minimum) & (df["KI %"] < maximum)]
        auswertung(gruppe, f"KI {minimum} bis {maximum - 1} %")

    print("\nBeste 10 KI-Trades:")
    print(df.sort_values(by="Rendite %", ascending=False).head(10).to_string(index=False))

    print("\nSchlechteste 10 KI-Trades:")
    print(df.sort_values(by="Rendite %", ascending=True).head(10).to_string(index=False))


if __name__ == "__main__":
    main()