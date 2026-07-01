from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.trend import EMAIndicator, MACD, ADXIndicator, CCIIndicator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator


def berechne_indikatoren(data):
    close = data["Close"].squeeze()
    high = data["High"].squeeze()
    low = data["Low"].squeeze()
    volume = data["Volume"].squeeze()

    letzter_preis = close.iloc[-1]

    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]

    ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
    ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close, window=200).ema_indicator().iloc[-1]

    macd_obj = MACD(close)
    macd = macd_obj.macd().iloc[-1]
    macd_signal = macd_obj.macd_signal().iloc[-1]

    atr = AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]

    window_52w = min(252, len(close))
    high_52w = close.rolling(window_52w).max().iloc[-1]
    low_52w = close.rolling(window_52w).min().iloc[-1]

    volumen_durchschnitt = volume.iloc[-21:-1].mean()
    volumen_faktor = volume.iloc[-1] / volumen_durchschnitt if volumen_durchschnitt != 0 else 0

    adx = ADXIndicator(high, low, close, window=14).adx().iloc[-1]
    cci = CCIIndicator(high, low, close, window=20).cci().iloc[-1]

    stoch = StochasticOscillator(high, low, close, window=14, smooth_window=3)
    stoch_k = stoch.stoch().iloc[-1]
    stoch_d = stoch.stoch_signal().iloc[-1]

    roc = ROCIndicator(close, window=10).roc().iloc[-1]

    bollinger = BollingerBands(close, window=20, window_dev=2)
    bb_high = bollinger.bollinger_hband().iloc[-1]
    bb_low = bollinger.bollinger_lband().iloc[-1]
    bb_middle = bollinger.bollinger_mavg().iloc[-1]

    obv = OnBalanceVolumeIndicator(close, volume).on_balance_volume().iloc[-1]
    mfi = MFIIndicator(high, low, close, volume, window=14).money_flow_index().iloc[-1]

    abstand_ema20 = ((letzter_preis - ema20) / ema20) * 100
    abstand_ema50 = ((letzter_preis - ema50) / ema50) * 100
    abstand_ema200 = ((letzter_preis - ema200) / ema200) * 100
    abstand_52w_high = ((high_52w - letzter_preis) / high_52w) * 100
    abstand_52w_low = ((letzter_preis - low_52w) / low_52w) * 100

    volatilitaet_20 = close.pct_change().rolling(20).std().iloc[-1] * 100

    return {
        "RSI": float(rsi),
        "EMA20": float(ema20),
        "EMA50": float(ema50),
        "EMA200": float(ema200),
        "MACD": float(macd),
        "MACD_SIGNAL": float(macd_signal),
        "ATR": float(atr),
        "52W_HIGH": float(high_52w),
        "52W_LOW": float(low_52w),
        "VOLUMEN_FAKTOR": float(volumen_faktor),
        "ADX": float(adx),
        "CCI": float(cci),
        "STOCH_K": float(stoch_k),
        "STOCH_D": float(stoch_d),
        "ROC": float(roc),
        "BB_HIGH": float(bb_high),
        "BB_LOW": float(bb_low),
        "BB_MIDDLE": float(bb_middle),
        "OBV": float(obv),
        "MFI": float(mfi),
        "ABSTAND_EMA20": float(abstand_ema20),
        "ABSTAND_EMA50": float(abstand_ema50),
        "ABSTAND_EMA200": float(abstand_ema200),
        "ABSTAND_52W_HIGH": float(abstand_52w_high),
        "ABSTAND_52W_LOW": float(abstand_52w_low),
        "VOLATILITAET_20": float(volatilitaet_20),
    }