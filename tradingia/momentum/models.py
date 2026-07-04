from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MomentumInput:
    today_pct: float | None = None
    volume_factor: float | None = None
    distance_to_high_pct: float | None = None
    roc: float | None = None
    adx: float | None = None
    rsi: float | None = None
    gap_pct: float | None = None
    previous_day_pct: float | None = None
    relative_strength_pct: float | None = None


@dataclass(frozen=True)
class MomentumResult:
    score: float
    penalty: float
    reasons: list[str] = field(default_factory=list)
    risk_reasons: list[str] = field(default_factory=list)
