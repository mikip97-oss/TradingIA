from __future__ import annotations

import pandas as pd

from tradingia.decision.models import DecisionInput, DecisionResult, DecisionWeights


class MasterDecisionEngine:
    def __init__(self, weights: DecisionWeights | None = None) -> None:
        self.weights = weights or DecisionWeights()

    def score(self, decision_input: DecisionInput) -> DecisionResult:
        weighted_score, reasons = self._weighted_score(decision_input)
        regime_adjustment, regime_reason = self._regime_adjustment(decision_input.market_regime, decision_input)
        final_score = _clamp(weighted_score + regime_adjustment)

        if regime_reason:
            reasons.append(regime_reason)
        reasons.extend(decision_input.notes)

        return DecisionResult(
            ticker=decision_input.ticker,
            final_score=round(final_score, 4),
            recommendation=self._recommendation(final_score),
            reasons=_unique(reasons),
            partial_scores={
                "DayTradeScore": decision_input.daytrade_score,
                "CatalystScore": decision_input.catalyst_score,
                "NewsScore": decision_input.news_score,
                "TradeScore": decision_input.trade_score,
                "KI %": decision_input.ai_percent,
                "Market Regime": decision_input.market_regime,
            },
        )

    def score_many(self, inputs: list[DecisionInput]) -> pd.DataFrame:
        rows = [self.score(item).as_row() for item in inputs]
        columns = ["Aktie", "FinalScore", "Empfehlung", "wichtigste Gründe", "Teil-Scores"]
        if not rows:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(rows, columns=columns).sort_values(by="FinalScore", ascending=False).reset_index(drop=True)

    def _weighted_score(self, decision_input: DecisionInput) -> tuple[float, list[str]]:
        components = [
            ("DayTradeScore", decision_input.daytrade_score, self.weights.daytrade),
            ("CatalystScore", decision_input.catalyst_score, self.weights.catalyst),
            ("NewsScore", decision_input.news_score, self.weights.news),
            ("TradeScore", decision_input.trade_score, self.weights.trade),
            ("KI %", decision_input.ai_percent, self.weights.ai),
        ]
        available = [(name, _clamp(score), weight) for name, score, weight in components if score is not None]

        if not available:
            return 0.0, ["keine Teil-Scores vorhanden"]

        total_weight = sum(weight for _, _, weight in available)
        if total_weight <= 0:
            return 0.0, ["Gewichtung ist 0"]

        weighted_score = sum(score * weight for _, score, weight in available) / total_weight
        reasons = self._score_reasons(available)
        return weighted_score, reasons

    def _score_reasons(self, available: list[tuple[str, float, float]]) -> list[str]:
        reasons = []
        strong = [name for name, score, _ in available if score >= 80]
        weak = [name for name, score, _ in available if score < 50]

        if strong:
            reasons.append(f"starke Teil-Scores: {', '.join(strong)}")
        if weak:
            reasons.append(f"schwache Teil-Scores: {', '.join(weak)}")
        return reasons

    def _regime_adjustment(self, regime: str | None, decision_input: DecisionInput) -> tuple[float, str | None]:
        if not regime:
            return 0.0, None

        normalized = regime.lower()
        daytrade = decision_input.daytrade_score or 0.0
        catalyst = decision_input.catalyst_score or 0.0
        trade = decision_input.trade_score or 0.0

        if normalized == "bull" and max(daytrade, catalyst, trade) >= 70:
            return self.weights.regime_bonus, "Bull-Regime bestätigt Long-Setup"
        if normalized == "bear" and max(daytrade, catalyst, trade) >= 70:
            return -self.weights.regime_penalty, "Bear-Regime reduziert Long-Setup"
        if normalized == "sideways" and daytrade >= 80:
            return self.weights.regime_bonus / 2, "Sideways-Regime: nur starke Intraday-Setups bevorzugt"
        if normalized == "sideways" and daytrade < 60:
            return -self.weights.regime_penalty / 2, "Sideways-Regime ohne starkes Intraday-Setup"

        return 0.0, f"Market Regime: {regime}"

    def _recommendation(self, final_score: float) -> str:
        if final_score >= 90:
            return "⭐⭐⭐⭐⭐ Top Chance"
        if final_score >= 80:
            return "⭐⭐⭐⭐ Sehr interessant"
        if final_score >= 70:
            return "⭐⭐⭐ Beobachten"
        return "Kein Trade"


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 100.0))


def _unique(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result[:8]
