from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TrendClassification(str, Enum):
    STRONG_UPTREND = "Strong Uptrend"
    UPTREND = "Uptrend"
    SIDEWAYS = "Seitwärts"
    WEAK_DOWNTREND = "Schwacher Abwärtstrend"
    STRONG_DOWNTREND = "Strong Downtrend"


@dataclass(frozen=True)
class TrendInput:
    close: float | None = None
    ema20: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    ema20_slope: float | None = None
    ema50_slope: float | None = None
    ema200_slope: float | None = None
    adx: float | None = None
    higher_highs: bool | None = None
    higher_lows: bool | None = None


@dataclass(frozen=True)
class TrendResult:
    score: float
    classification: TrendClassification
    final_score_cap: float | None = None
    reasons: list[str] = field(default_factory=list)
    risk_reasons: list[str] = field(default_factory=list)
    has_trend_data: bool = True
