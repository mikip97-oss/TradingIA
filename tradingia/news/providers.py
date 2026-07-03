from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from tradingia.news.models import NewsItem


class NewsProvider(Protocol):
    name: str

    def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        """Return recent news items for a ticker."""


class MockNewsProvider:
    name = "mock_news"

    def __init__(self, news_by_ticker: dict[str, Iterable[NewsItem | dict]] | None = None) -> None:
        self.news_by_ticker = news_by_ticker or {}

    def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        raw_items = list(self.news_by_ticker.get(ticker, []))[:limit]
        return [self._coerce_item(ticker, item) for item in raw_items]

    def _coerce_item(self, ticker: str, item: NewsItem | dict) -> NewsItem:
        if isinstance(item, NewsItem):
            return item

        return NewsItem(
            ticker=str(item.get("ticker", ticker)),
            headline=str(item.get("headline", "")),
            source=str(item.get("source", self.name)),
            published_at=item.get("published_at"),
            summary=str(item.get("summary", "")),
        )
