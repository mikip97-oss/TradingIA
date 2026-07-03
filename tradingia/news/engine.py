from __future__ import annotations

import pandas as pd

from tradingia.news.models import NewsItem, NewsScoreResult, NewsSentiment
from tradingia.news.providers import NewsProvider


POSITIVE_TERMS = {
    "beat", "beats", "strong", "surge", "surges", "record", "growth", "raises", "raised",
    "profit", "profitable", "outperform", "upgrade", "upgraded", "approval", "approved",
    "partnership", "partner", "deal", "contract", "launch", "expands", "buyback",
}

NEGATIVE_TERMS = {
    "miss", "misses", "weak", "falls", "fall", "plunge", "plunges", "downgrade",
    "downgraded", "lawsuit", "investigation", "probe", "fraud", "warning", "cuts",
    "cut", "loss", "decline", "recall", "rejected", "delay", "delayed",
}

EVENT_TERMS = {
    "earnings": {"earnings", "quarterly results", "q1", "q2", "q3", "q4", "guidance"},
    "analyst_upgrade": {"upgrade", "upgraded", "raises price target", "outperform", "buy rating"},
    "analyst_downgrade": {"downgrade", "downgraded", "cuts price target", "sell rating", "underperform"},
    "partnership_deal": {"partnership", "deal", "contract", "agreement", "collaboration"},
    "fda_approval": {"fda", "approval", "approved", "clearance", "trial success"},
    "lawsuit_investigation": {"lawsuit", "investigation", "probe", "sec", "doj", "fraud"},
}


class NewsIntelligenceEngine:
    def __init__(self, provider: NewsProvider) -> None:
        self.provider = provider

    def score_ticker(self, ticker: str, limit: int = 20) -> NewsScoreResult:
        news_items = self.provider.get_news(ticker, limit=limit)
        return score_news_items(ticker, news_items)

    def score_many(self, tickers: list[str], limit: int = 20) -> pd.DataFrame:
        rows = [self.score_ticker(ticker, limit=limit).as_row() for ticker in tickers]
        columns = ["Aktie", "NewsScore", "Sentiment", "Anzahl News", "wichtigste Gründe"]
        if not rows:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(rows, columns=columns).sort_values(by="NewsScore", ascending=False).reset_index(drop=True)


def score_news_items(ticker: str, news_items: list[NewsItem]) -> NewsScoreResult:
    if not news_items:
        return NewsScoreResult(ticker=ticker, news_score=0.0, sentiment=NewsSentiment.NEUTRAL, news_count=0, reasons=[])

    score = 50.0
    positive_hits = 0
    negative_hits = 0
    reasons: list[str] = []

    for item in news_items:
        text = item.text.lower()
        pos = _count_terms(text, POSITIVE_TERMS)
        neg = _count_terms(text, NEGATIVE_TERMS)
        positive_hits += pos
        negative_hits += neg
        score += min(pos * 4, 16)
        score -= min(neg * 5, 20)

        event_score, event_reasons = _score_events(text)
        score += event_score
        reasons.extend(event_reasons)

    if positive_hits:
        reasons.append(f"positive Begriffe: {positive_hits}")
    if negative_hits:
        reasons.append(f"negative Begriffe: {negative_hits}")

    score = max(0.0, min(score, 100.0))
    sentiment = _sentiment(score, positive_hits, negative_hits)
    return NewsScoreResult(ticker=ticker, news_score=score, sentiment=sentiment, news_count=len(news_items), reasons=_unique_reasons(reasons))


def _score_events(text: str) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if _contains_any(text, EVENT_TERMS["earnings"]):
        score += 8
        reasons.append("Earnings/Guidance")
    if _contains_any(text, EVENT_TERMS["analyst_upgrade"]):
        score += 12
        reasons.append("Analyst Upgrade")
    if _contains_any(text, EVENT_TERMS["analyst_downgrade"]):
        score -= 14
        reasons.append("Analyst Downgrade")
    if _contains_any(text, EVENT_TERMS["partnership_deal"]):
        score += 10
        reasons.append("Partnership/Deal")
    if _contains_any(text, EVENT_TERMS["fda_approval"]):
        score += 14
        reasons.append("FDA/Approval")
    if _contains_any(text, EVENT_TERMS["lawsuit_investigation"]):
        score -= 18
        reasons.append("Lawsuit/Investigation")

    return score, reasons


def _count_terms(text: str, terms: set[str]) -> int:
    return sum(1 for term in terms if term in text)


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _sentiment(score: float, positive_hits: int, negative_hits: int) -> NewsSentiment:
    if positive_hits and negative_hits:
        if abs(positive_hits - negative_hits) <= 1:
            return NewsSentiment.MIXED
    if score >= 65:
        return NewsSentiment.POSITIVE
    if score <= 40:
        return NewsSentiment.NEGATIVE
    return NewsSentiment.NEUTRAL


def _unique_reasons(reasons: list[str]) -> list[str]:
    unique: list[str] = []
    for reason in reasons:
        if reason not in unique:
            unique.append(reason)
    return unique[:8]
