"""Trend filter components for TradingIA."""

from tradingia.trend.engine import TrendFilterEngine, score_trend
from tradingia.trend.models import TrendClassification, TrendInput, TrendResult

__all__ = [
    "TrendClassification",
    "TrendFilterEngine",
    "TrendInput",
    "TrendResult",
    "score_trend",
]
