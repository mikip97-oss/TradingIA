"""News and market intelligence components for TradingIA."""

from tradingia.news.engine import NewsIntelligenceEngine
from tradingia.news.models import NewsItem, NewsScoreResult, NewsSentiment
from tradingia.news.providers import MockNewsProvider, NewsProvider

__all__ = [
    "MockNewsProvider",
    "NewsIntelligenceEngine",
    "NewsItem",
    "NewsProvider",
    "NewsScoreResult",
    "NewsSentiment",
]
