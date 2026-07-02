from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

from config import DATEN_INTERVAL, DATEN_ZEITRAUM, MIN_DATENPUNKTE, NUTZE_SP500, TOP_ANZAHL

try:
    from config import SCANNER_MAX_WORKERS
except ImportError:
    SCANNER_MAX_WORKERS = 8

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


def scan_market(tickers=None, max_workers=None):
    resultate = []
    aktien = tickers if tickers is not None else get_aktien_liste()
    workers = _resolve_max_workers(max_workers=max_workers, ticker_count=len(aktien))

    print(f"Scanne {len(aktien)} Aktien mit {workers} Workern...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(scan_ticker, ticker): ticker for ticker in aktien}

        for future in as_completed(futures):
            ticker = futures[future]
            try:
                result = future.result()
            except Exception as e:
                print(f"Fehler bei {ticker}: {e}")
                continue

            if result is not None:
                resultate.append(result)

    df = pd.DataFrame(resultate)

    if df.empty:
        return df

    return df.sort_values(by="TradeScore", ascending=False).head(TOP_ANZAHL)


def scan_ticker(ticker):
    data = yf.download(
        ticker,
        period=DATEN_ZEITRAUM,
        interval=DATEN_INTERVAL,
        progress=False,
        auto_adjust=True
    )

    if len(data) < max(MIN_DATENPUNKTE, 220):
        return None

    close = data["Close"].squeeze()
    letzter_preis = float(close.iloc[-1])

    feature_dict = baue_features(data)
    if feature_dict is None:
        return None

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

    return {
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
    }


def _resolve_max_workers(max_workers=None, ticker_count=0):
    configured = SCANNER_MAX_WORKERS if max_workers is None else max_workers
    configured = max(1, int(configured))
    return min(configured, max(1, ticker_count))
