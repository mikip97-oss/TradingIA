from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from catalyst_scanner import scan_catalyst_market
from daytrading_scanner import scan_daytrading_market
from tradingia.decision import DecisionInput, MasterDecisionEngine
from tradingia.news import FinnhubNewsProvider, NewsIntelligenceEngine, NewsItem, NewsScoreResult, NewsSentiment
from tradingia.news.engine import score_news_items

PipelineScanner = Callable[..., pd.DataFrame]

PIPELINE_COLUMNS = [
    "Aktie",
    "FinalScore",
    "Empfehlung",
    "DayTradeScore",
    "CatalystScore",
    "NewsScore",
    "Sentiment",
    "wichtigste Gründe",
]


class IntelligencePipeline:
    def __init__(
        self,
        *,
        daytrading_scanner: PipelineScanner = scan_daytrading_market,
        catalyst_scanner: PipelineScanner = scan_catalyst_market,
        news_engine: NewsIntelligenceEngine | None = None,
        decision_engine: MasterDecisionEngine | None = None,
        company_names: dict[str, str] | None = None,
    ) -> None:
        self.daytrading_scanner = daytrading_scanner
        self.catalyst_scanner = catalyst_scanner
        self.news_engine = news_engine or NewsIntelligenceEngine(FinnhubNewsProvider())
        self.decision_engine = decision_engine or MasterDecisionEngine()
        self.company_names = {ticker.upper(): name for ticker, name in (company_names or {}).items()}

    def run(self, tickers: list[str], *, max_workers: int | None = None, news_limit: int = 20) -> pd.DataFrame:
        normalized_tickers = _deduplicate_tickers(tickers)
        if not normalized_tickers:
            return pd.DataFrame(columns=PIPELINE_COLUMNS)

        daytrading_scores = self._scan_scores(
            self.daytrading_scanner,
            normalized_tickers,
            score_column="DayTradeScore",
            max_workers=max_workers,
        )
        catalyst_scores = self._scan_scores(
            self.catalyst_scanner,
            normalized_tickers,
            score_column="CatalystScore",
            max_workers=max_workers,
        )

        rows: list[dict[str, float | str]] = []
        for ticker in normalized_tickers:
            news_result = self._score_news(ticker, news_limit)
            decision = self.decision_engine.score(
                DecisionInput(
                    ticker=ticker,
                    daytrade_score=daytrading_scores.get(ticker),
                    catalyst_score=catalyst_scores.get(ticker),
                    news_score=news_result.news_score,
                    notes=news_result.reasons,
                )
            )
            rows.append(
                {
                    "Aktie": ticker,
                    "FinalScore": round(decision.final_score, 1),
                    "Empfehlung": decision.recommendation,
                    "DayTradeScore": _empty_if_none(daytrading_scores.get(ticker)),
                    "CatalystScore": _empty_if_none(catalyst_scores.get(ticker)),
                    "NewsScore": round(news_result.news_score, 1),
                    "Sentiment": news_result.sentiment.value,
                    "wichtigste Gründe": ", ".join(decision.reasons),
                }
            )

        return pd.DataFrame(rows, columns=PIPELINE_COLUMNS).sort_values(by="FinalScore", ascending=False).reset_index(drop=True)

    def _scan_scores(
        self,
        scanner: PipelineScanner,
        tickers: list[str],
        *,
        score_column: str,
        max_workers: int | None,
    ) -> dict[str, float]:
        try:
            frame = scanner(tickers=tickers, max_workers=max_workers, top_anzahl=len(tickers))
        except TypeError:
            frame = scanner(tickers=tickers, max_workers=max_workers)
        except Exception:
            return {}

        if frame is None or frame.empty or "Aktie" not in frame.columns or score_column not in frame.columns:
            return {}

        scores: dict[str, float] = {}
        for _, row in frame.iterrows():
            ticker = str(row.get("Aktie", "")).upper()
            value = row.get(score_column)
            if ticker and pd.notna(value):
                try:
                    scores[ticker] = float(value)
                except (TypeError, ValueError):
                    continue
        return scores

    def _score_news(self, ticker: str, limit: int) -> NewsScoreResult:
        try:
            provider = self.news_engine.provider
            raw_news = provider.get_news(ticker, limit=limit)
            filtered_news = filter_relevant_news(raw_news, ticker, self.company_names.get(ticker.upper()))
            return score_news_items(ticker, filtered_news)
        except Exception as exc:
            return NewsScoreResult(
                ticker=ticker,
                news_score=0.0,
                sentiment=NewsSentiment.NEUTRAL,
                news_count=0,
                reasons=[f"News-Fehler: {exc}"],
            )


def filter_relevant_news(news_items: list[NewsItem], ticker: str, company_name: str | None = None) -> list[NewsItem]:
    ticker_token = ticker.lower()
    company_tokens = _company_tokens(company_name)
    if not ticker_token and not company_tokens:
        return news_items

    filtered = []
    for item in news_items:
        text = item.text.lower()
        if ticker_token and ticker_token in text:
            filtered.append(item)
            continue
        if company_tokens and any(token in text for token in company_tokens):
            filtered.append(item)
    return filtered


def _company_tokens(company_name: str | None) -> list[str]:
    if not company_name:
        return []
    cleaned = company_name.lower().strip()
    if not cleaned:
        return []
    tokens = [cleaned]
    first_word = cleaned.split()[0]
    if len(first_word) >= 4:
        tokens.append(first_word)
    return list(dict.fromkeys(tokens))


def _deduplicate_tickers(tickers: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for ticker in tickers:
        normalized = str(ticker).strip().upper()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _empty_if_none(value: float | None) -> float | str:
    if value is None:
        return ""
    return round(value, 1)
