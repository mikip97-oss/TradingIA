from __future__ import annotations

from tradingia.momentum.models import MomentumInput, MomentumResult


class MomentumConfirmationEngine:
    def score(self, data: MomentumInput) -> MomentumResult:
        score = 0.0
        penalty = 0.0
        reasons: list[str] = []
        risk_reasons: list[str] = []

        today = data.today_pct
        volume = data.volume_factor
        distance = data.distance_to_high_pct
        roc = data.roc
        adx = data.adx
        rsi = data.rsi
        gap = data.gap_pct
        previous = data.previous_day_pct
        relative_strength = data.relative_strength_pct

        if today is not None and today > 0:
            score += 18
            reasons.append("heutige positive Kursreaktion")
        if today is not None and today >= 1.5:
            score += 14
            reasons.append("starke heutige Performance")

        if volume is not None and volume >= 1.5 and today is not None and today > 0:
            score += 16
            reasons.append("erhoehtes Volumen bestaetigt Kaufinteresse")
        elif volume is not None and volume >= 1.0 and today is not None and today > 0:
            score += 8
            reasons.append("Volumen ueber Durchschnitt")
        if volume is not None and volume >= 1.5 and today is not None and today <= 0:
            penalty += 18
            risk_reasons.append("hohes Volumen bei fallendem Kurs")

        if distance is not None and distance <= 0.75:
            score += 18
            reasons.append("sehr nahe am Tageshoch")
        elif distance is not None and distance <= 1.5:
            score += 10
            reasons.append("nahe am Tageshoch")
        elif distance is not None and distance >= 3.0:
            penalty += 14
            risk_reasons.append("weit vom Tageshoch entfernt")

        if roc is not None and roc > 0:
            score += 12
            reasons.append("positiver Intraday-ROC")
        if roc is not None and roc >= 1.5:
            score += 8
            reasons.append("starker Intraday-ROC")
        if roc is not None and roc < 0:
            penalty += 12
            risk_reasons.append("negatives Intraday-Momentum")

        if adx is not None and adx >= 25:
            score += 10
            reasons.append("starker Intraday-Trend")
        elif adx is not None and adx >= 18:
            score += 6
            reasons.append("brauchbare Trendstaerke")

        if rsi is not None and 45 <= rsi <= 72:
            score += 8
            reasons.append("RSI im bestaetigten Momentum-Bereich")
        elif rsi is not None and rsi >= 85:
            penalty += 20
            risk_reasons.append("RSI extrem ueberdehnt")
        elif rsi is not None and rsi >= 78:
            penalty += 12
            risk_reasons.append("RSI sehr hoch")
        elif rsi is not None and rsi < 40:
            penalty += 8
            risk_reasons.append("RSI schwach")

        if gap is not None and gap >= 1.0:
            if today is not None and today > 0 and (distance is None or distance <= 1.5):
                score += 10
                reasons.append("Gap-Up wird gehalten")
            else:
                penalty += 22
                risk_reasons.append("Gap-Up wird nicht gehalten")

        if today is not None and today <= -1.0:
            penalty += 18
            risk_reasons.append("starke Intraday-Schwaeche")
        elif today is not None and today < 0:
            penalty += 10
            risk_reasons.append("Intraday-Schwaeche")

        if previous is not None and previous >= 4.0 and (today is None or today <= 0.5):
            penalty += 20
            risk_reasons.append("Gewinnmitnahme-Risiko nach starkem Vortag")
        if previous is not None and previous >= 7.0 and today is not None and today < 0:
            penalty += 12
            risk_reasons.append("overextended nach Vortagesanstieg")

        if relative_strength is not None and relative_strength > 0:
            score += 6
            reasons.append("relative Staerke gegen Markt")
        elif relative_strength is not None and relative_strength < 0:
            penalty += 6
            risk_reasons.append("relative Schwaeche gegen Markt")

        final_score = _clamp(score - penalty)
        return MomentumResult(score=round(final_score, 4), penalty=round(min(penalty, 100.0), 4), reasons=_unique(reasons), risk_reasons=_unique(risk_reasons))


def score_momentum_confirmation(data: MomentumInput) -> MomentumResult:
    return MomentumConfirmationEngine().score(data)


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 100.0))


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result[:10]
