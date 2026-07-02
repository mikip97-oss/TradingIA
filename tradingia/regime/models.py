from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MarketRegime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"


@dataclass(frozen=True)
class RegimeSnapshot:
    symbol: str
    timestamp: datetime
    regime: MarketRegime
    close: float
    ema_fast: float
    ema_slow: float
    adx: float
    atr: float
    volatility: float
    reason: str
