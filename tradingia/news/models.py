from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NewsSentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass(frozen=True)
class NewsItem:
    ticker: str
    headline: str
    source: str = "unknown"
    published_at: datetime | None = None
    summary: str = ""

    @property
    def text(self) -> str:
        return f"{self.headline} {self.summary}".strip()


@dataclass(frozen=True)
class NewsScoreResult:
    ticker: str
    news_score: float
    sentiment: NewsSentiment
    news_count: int
    reasons: list[str] = field(default_factory=list)

    def as_row(self) -> dict[str, float | int | str]:
        return {
            "Aktie": self.ticker,
            "NewsScore": round(self.news_score, 1),
            "Sentiment": self.sentiment.value,
            "Anzahl News": self.news_count,
            "wichtigste Gründe": ", ".join(self.reasons),
        }
