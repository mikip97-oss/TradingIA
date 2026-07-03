from __future__ import annotations

import json
import os
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import urlopen

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


class FinnhubNewsProvider:
    name = "finnhub"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://finnhub.io/api/v1/company-news",
        lookback_days: int = 7,
        timeout: float = 10.0,
        env_file: str | Path | None = None,
        urlopen_func=urlopen,
    ) -> None:
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY") or _read_env_api_key(env_file)
        self.base_url = base_url
        self.lookback_days = lookback_days
        self.timeout = timeout
        self.urlopen_func = urlopen_func
        self.last_error: str | None = None

    def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        if not self.api_key:
            self.last_error = "FINNHUB_API_KEY fehlt"
            return []

        try:
            url = self._build_url(ticker)
            with self.urlopen_func(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, list):
                self.last_error = "Unerwartete Finnhub-Antwort"
                return []
            self.last_error = None
            return [self._to_news_item(ticker, item) for item in payload[:limit] if isinstance(item, dict)]
        except Exception as exc:
            self.last_error = str(exc)
            return []

    def _build_url(self, ticker: str) -> str:
        today = datetime.now(UTC).date()
        start = today - timedelta(days=max(self.lookback_days, 1))
        query = urlencode(
            {
                "symbol": ticker,
                "from": start.isoformat(),
                "to": today.isoformat(),
                "token": self.api_key,
            }
        )
        return f"{self.base_url}?{query}"

    def _to_news_item(self, ticker: str, item: dict) -> NewsItem:
        return NewsItem(
            ticker=ticker,
            headline=str(item.get("headline", "")),
            source=str(item.get("source", self.name)),
            published_at=_timestamp_to_datetime(item.get("datetime")),
            summary=str(item.get("summary", "")),
        )


def _read_env_api_key(env_file: str | Path | None = None) -> str | None:
    path = Path(env_file) if env_file else Path.cwd() / ".env"
    if not path.exists():
        return None

    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
            continue
        key, value = cleaned.split("=", 1)
        if key.strip() == "FINNHUB_API_KEY":
            return value.strip().strip("\"'")
    return None


def _timestamp_to_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return None
