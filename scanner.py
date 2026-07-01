import yfinance as yf
import pandas as pd

from config import TOP_ANZAHL, DATEN_ZEITRAUM, DATEN_INTERVAL, MIN_DATENPUNKTE, NUTZE_SP500
from universe import lade_sp500_ticker
from candles import erkenne_candles
from ai.ai_predict import ki_vorhersage
from feature_builder import baue_features
from risk import berechne_position
from trade_engine import bewerte_trade


FALLBACK_AKTIEN = [
    "NVDA", "AMD", "TSLA", "PLTR", "SOFI",
    "COIN", "MSTR", "AAPL", "MSFT", "MU",
    "META", "GOOGL", "AMZN", "AVGO", "HOOD",
    "RIVN", "SMCI", "NFLX", "SHOP", "UBER"
]


def get_aktien_liste():
    if NUTZE_SP500:
        print("Lade S&P-500-Aktien...")
        return lade_sp500_ticker()

    return FALLBACK_AKTIEN


def scan_market():
    resultate = []
    aktien = get_aktien_liste()

    print(f"Scanne {len(aktien)} Aktien...")

    for ticker in aktien:
        try:
            data = yf.download(
                ticker,
                period=DATEN_ZEITRAUM,
                interval=DATEN_INTERVAL,
                progress=False,
                auto_adjust=True
            )

            if len(data) < max(MIN_DATENPUNKTE, 220):
                continue

            close = data["Close"].squeeze()
            letzter_preis = float(close.iloc[-1])

            feature_dict = baue_features(data)
            if feature_dict is None:
                continue

            candles = erkenne_candles(data)
            candle_muster = candles["Muster"]
            candle_score = candles["CandleScore"]

            ki_prozent = ki_vorhersage(feature_dict)

            atr = feature_dict["atr"]
            stop_loss = letzter_preis - (atr * 1.5)
            ziel = letzter_preis + (atr * 3)

            risiko = letzter_preis - stop_loss
            chance = ziel - letzter_preis
            chance_risiko = chance / risiko if risiko > 0 else 0

            trade_score, empfehlung, trade_gruende = bewerte_trade(
                ki=ki_prozent,
                adx=feature_dict["adx"],
                volumen=feature_dict["volumen_faktor"],
                chance_risiko=chance_risiko,
                abstand_52w_high=feature_dict["abstand_52w_high"],
                rsi=feature_dict["rsi"],
                candle_score=candle_score
            )

            position = berechne_position(
                einstieg=letzter_preis,
                stop_loss=stop_loss,
                kontostand=10000,
                risiko_pro_trade=0.02
            )

            resultate.append({
                "Aktie": ticker,
                "TradeScore": trade_score,
                "KI %": round(ki_prozent, 1),
                "Empfehlung": empfehlung,
                "Muster": candle_muster,
                "Gründe": ", ".join(trade_gruende),
                "Einstieg": round(letzter_preis, 2),
                "Stop-Loss": round(stop_loss, 2),
                "Ziel": round(ziel, 2),
                "Chance/Risiko": round(chance_risiko, 2),
                "Positionsgröße $": position["Positionsgröße $"],
                "Aktien": position["Aktien"],
                "Max Risiko $": position["Max Risiko $"],
                "Heute %": round(feature_dict["veraenderung"], 2),
                "RSI": round(feature_dict["rsi"], 1),
                "Volumen-Faktor": round(feature_dict["volumen_faktor"], 2),
                "52W Abstand %": round(feature_dict["abstand_52w_high"], 2),
                "ADX": round(feature_dict["adx"], 1),
                "MFI": round(feature_dict["mfi"], 1),
                "ROC": round(feature_dict["roc"], 2),
            })

        except Exception as e:
            print(f"Fehler bei {ticker}: {e}")

    df = pd.DataFrame(resultate)

    if df.empty:
        return df

    return df.sort_values(by="TradeScore", ascending=False).head(TOP_ANZAHL)