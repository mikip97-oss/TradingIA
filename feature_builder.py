import pandas as pd

from indicators import berechne_indikatoren


FEATURES = [
    "veraenderung",
    "rsi",
    "ema20",
    "ema50",
    "ema200",
    "macd",
    "macd_signal",
    "atr",
    "volumen_faktor",
    "adx",
    "cci",
    "stoch_k",
    "stoch_d",
    "roc",
    "mfi",
    "abstand_ema20",
    "abstand_ema50",
    "abstand_ema200",
    "abstand_52w_high",
    "abstand_52w_low",
    "volatilitaet_20",
]


def baue_features(data, index=None):
    if index is not None:
        teil = data.iloc[:index].copy()
    else:
        teil = data.copy()

    if len(teil) < 220:
        return None

    close = teil["Close"].squeeze()
    volume = teil["Volume"].squeeze()

    letzter_preis = float(close.iloc[-1])
    preis_gestern = float(close.iloc[-2])

    veraenderung = ((letzter_preis - preis_gestern) / preis_gestern) * 100

    volumen_heute = float(volume.iloc[-1])
    volumen_durchschnitt = float(volume.iloc[-21:-1].mean())

    if volumen_durchschnitt == 0:
        return None

    indikatoren = berechne_indikatoren(teil)

    daten = {
        "veraenderung": veraenderung,
        "rsi": indikatoren["RSI"],
        "ema20": indikatoren["EMA20"],
        "ema50": indikatoren["EMA50"],
        "ema200": indikatoren["EMA200"],
        "macd": indikatoren["MACD"],
        "macd_signal": indikatoren["MACD_SIGNAL"],
        "atr": indikatoren["ATR"],
        "volumen_faktor": volumen_heute / volumen_durchschnitt,
        "adx": indikatoren["ADX"],
        "cci": indikatoren["CCI"],
        "stoch_k": indikatoren["STOCH_K"],
        "stoch_d": indikatoren["STOCH_D"],
        "roc": indikatoren["ROC"],
        "mfi": indikatoren["MFI"],
        "abstand_ema20": indikatoren["ABSTAND_EMA20"],
        "abstand_ema50": indikatoren["ABSTAND_EMA50"],
        "abstand_ema200": indikatoren["ABSTAND_EMA200"],
        "abstand_52w_high": indikatoren["ABSTAND_52W_HIGH"],
        "abstand_52w_low": indikatoren["ABSTAND_52W_LOW"],
        "volatilitaet_20": indikatoren["VOLATILITAET_20"],
    }

    return daten


def features_als_dataframe(feature_dict):
    return pd.DataFrame([feature_dict])[FEATURES]