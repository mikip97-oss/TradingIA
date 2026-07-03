from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecisionWeights:
    daytrade: float = 0.30
    catalyst: float = 0.25
    news: float = 0.20
    trade: float = 0.15
    ai: float = 0.10
    regime_bonus: float = 5.0
    regime_penalty: float = 8.0


@dataclass(frozen=True)
class DecisionInput:
    ticker: str
    daytrade_score: float | None = None
    catalyst_score: float | None = None
    news_score: float | None = None
    trade_score: float | None = None
    ai_percent: float | None = None
    market_regime: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionResult:
    ticker: str
    final_score: float
    recommendation: str
    reasons: list[str]
    partial_scores: dict[str, float | str | None]

    def as_row(self) -> dict[str, float | str]:
        return {
            "Aktie": self.ticker,
            "FinalScore": round(self.final_score, 1),
            "Empfehlung": self.recommendation,
            "wichtigste Gründe": ", ".join(self.reasons),
            "Teil-Scores": _format_partial_scores(self.partial_scores),
        }


def _format_partial_scores(partial_scores: dict[str, float | str | None]) -> str:
    parts = []
    for key, value in partial_scores.items():
        if value is None:
            continue
        if isinstance(value, float):
            parts.append(f"{key}={value:.1f}")
        else:
            parts.append(f"{key}={value}")
    return "; ".join(parts)
