from __future__ import annotations

from tradingia.trend.models import TrendClassification, TrendInput, TrendResult


class TrendFilterEngine:
    def score(self, data: TrendInput) -> TrendResult:
        if not _has_trend_data(data):
            return TrendResult(score=50.0, classification=TrendClassification.SIDEWAYS, has_trend_data=False)

        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []

        if _gt(data.ema20, data.ema50):
            score += 12
            reasons.append("EMA20 ueber EMA50")
        else:
            risks.append("EMA20 unter EMA50")

        if _gt(data.ema50, data.ema200):
            score += 14
            reasons.append("EMA50 ueber EMA200")
        else:
            risks.append("EMA50 nicht ueber EMA200")

        if _positive(data.ema20_slope):
            score += 10
            reasons.append("EMA20 steigt")
        elif _negative(data.ema20_slope):
            risks.append("EMA20 faellt")

        if _positive(data.ema50_slope):
            score += 12
            reasons.append("EMA50 steigt")
        elif _negative(data.ema50_slope):
            risks.append("EMA50 faellt")

        if _positive(data.ema200_slope):
            score += 10
            reasons.append("EMA200 steigt")
        elif _negative(data.ema200_slope):
            risks.append("EMA200 faellt")

        if _gt(data.close, data.ema20):
            score += 8
            reasons.append("Kurs ueber EMA20")
        else:
            risks.append("Kurs unter EMA20")

        if _gt(data.close, data.ema50):
            score += 10
            reasons.append("Kurs ueber EMA50")
        else:
            risks.append("Kurs unter EMA50")

        if _gt(data.close, data.ema200):
            score += 12
            reasons.append("Kurs ueber EMA200")
        else:
            risks.append("Kurs unter EMA200")

        if data.adx is not None and data.adx >= 25:
            score += 8
            reasons.append("ADX bestaetigt Trend")
        elif data.adx is not None and data.adx >= 18:
            score += 4
            reasons.append("ADX zeigt brauchbare Trendstaerke")

        if data.higher_highs is True:
            score += 6
            reasons.append("hoehere Hochs")
        elif data.higher_highs is False:
            risks.append("keine hoeheren Hochs")
        if data.higher_lows is True:
            score += 6
            reasons.append("hoehere Tiefs")
        elif data.higher_lows is False:
            risks.append("keine hoeheren Tiefs")

        score = _clamp(score)
        cap = _trend_cap(data, score)
        classification = _classification(score, cap)
        if classification == TrendClassification.STRONG_DOWNTREND and cap is None:
            cap = 65.0
        return TrendResult(score=round(score, 4), classification=classification, final_score_cap=cap, reasons=_unique(reasons), risk_reasons=_unique(risks), has_trend_data=True)


def score_trend(data: TrendInput) -> TrendResult:
    return TrendFilterEngine().score(data)


def _trend_cap(data: TrendInput, score: float) -> float | None:
    weak_downtrend = _lt(data.ema20, data.ema50) and _negative(data.ema50_slope) and _lt(data.close, data.ema50)
    if weak_downtrend and _lt(data.ema50, data.ema200):
        return 55.0
    if weak_downtrend:
        return 65.0
    if score < 25 and _lt(data.close, data.ema50):
        return 65.0
    return None


def _classification(score: float, cap: float | None) -> TrendClassification:
    if cap is not None and cap <= 55:
        return TrendClassification.STRONG_DOWNTREND
    if cap is not None and cap <= 65:
        return TrendClassification.WEAK_DOWNTREND
    if score >= 80:
        return TrendClassification.STRONG_UPTREND
    if score >= 62:
        return TrendClassification.UPTREND
    if score >= 40:
        return TrendClassification.SIDEWAYS
    if score >= 25:
        return TrendClassification.WEAK_DOWNTREND
    return TrendClassification.STRONG_DOWNTREND


def _has_trend_data(data: TrendInput) -> bool:
    return any(value is not None for value in [data.close, data.ema20, data.ema50, data.ema200, data.ema20_slope, data.ema50_slope, data.ema200_slope, data.adx])


def _gt(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and left > right


def _lt(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and left < right


def _positive(value: float | None) -> bool:
    return value is not None and value > 0


def _negative(value: float | None) -> bool:
    return value is not None and value < 0


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 100.0))


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result[:10]
