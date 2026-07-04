from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from catalyst_scanner import scan_catalyst_market
from daytrading_scanner import scan_daytrading_market
from tradingia.decision import DecisionInput, MasterDecisionEngine
from tradingia.momentum import MomentumInput, score_momentum_confirmation
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
    "TodayUpScore",
    "OverextensionPenalty",
    "wichtigste Gründe",
    "News Headline",
    "News Quelle",
    "News Veröffentlichungszeit",
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

        daytrading_rows = self._scan_rows(
            self.daytrading_scanner,
            normalized_tickers,
            required_score_column="DayTradeScore",
            max_workers=max_workers,
        )
        catalyst_rows = self._scan_rows(
            self.catalyst_scanner,
            normalized_tickers,
            required_score_column="CatalystScore",
            max_workers=max_workers,
        )

        rows: list[dict[str, float | str]] = []
        for ticker in normalized_tickers:
            day_row = daytrading_rows.get(ticker, {})
            catalyst_row = catalyst_rows.get(ticker, {})
            daytrade_score = _number_or_none(day_row.get("DayTradeScore"))
            catalyst_score = _number_or_none(catalyst_row.get("CatalystScore"))
            news_result, news_items = self._score_news(ticker, news_limit)
            lead_news = news_items[0] if news_items else None
            market_context = _market_context(day_row, catalyst_row)
            today_up_score, continuation_reasons = calculate_today_up_score(market_context, news_result.news_score)
            penalty, penalty_reasons = calculate_overextension_penalty(market_context, news_result.news_score)
            has_intraday_context = market_context.get("today_pct") is not None
            adjusted_daytrade_score = _adjust_score(daytrade_score, today_up_score, penalty, has_intraday_context)
            adjusted_catalyst_score = _adjust_score(catalyst_score, today_up_score, penalty, has_intraday_context)
            notes = news_result.reasons + continuation_reasons + penalty_reasons
            decision = self.decision_engine.score(
                DecisionInput(
                    ticker=ticker,
                    daytrade_score=adjusted_daytrade_score,
                    catalyst_score=adjusted_catalyst_score,
                    news_score=news_result.news_score,
                    notes=notes,
                )
            )
            final_score = max(0.0, decision.final_score - penalty)
            rows.append(
                {
                    "Aktie": ticker,
                    "FinalScore": round(final_score, 1),
                    "Empfehlung": _recommendation(final_score),
                    "DayTradeScore": _empty_if_none(adjusted_daytrade_score),
                    "CatalystScore": _empty_if_none(adjusted_catalyst_score),
                    "NewsScore": round(news_result.news_score, 1),
                    "Sentiment": news_result.sentiment.value,
                    "TodayUpScore": round(today_up_score, 1),
                    "OverextensionPenalty": round(penalty, 1),
                    "wichtigste Gründe": ", ".join(_unique_reasons(decision.reasons + penalty_reasons)),
                    "News Headline": lead_news.headline if lead_news else "",
                    "News Quelle": lead_news.source if lead_news else "",
                    "News Veröffentlichungszeit": _format_news_time(lead_news),
                }
            )

        return pd.DataFrame(rows, columns=PIPELINE_COLUMNS).sort_values(by="FinalScore", ascending=False).reset_index(drop=True)

    def _scan_rows(
        self,
        scanner: PipelineScanner,
        tickers: list[str],
        *,
        required_score_column: str,
        max_workers: int | None,
    ) -> dict[str, dict]:
        try:
            frame = scanner(tickers=tickers, max_workers=max_workers, top_anzahl=len(tickers))
        except TypeError:
            frame = scanner(tickers=tickers, max_workers=max_workers)
        except Exception:
            return {}

        if frame is None or frame.empty or "Aktie" not in frame.columns or required_score_column not in frame.columns:
            return {}

        rows: dict[str, dict] = {}
        for _, row in frame.iterrows():
            ticker = str(row.get("Aktie", "")).upper()
            if ticker:
                rows[ticker] = row.to_dict()
        return rows

    def _score_news(self, ticker: str, limit: int) -> tuple[NewsScoreResult, list[NewsItem]]:
        try:
            provider = self.news_engine.provider
            raw_news = provider.get_news(ticker, limit=limit)
            filtered_news = filter_relevant_news(raw_news, ticker, self.company_names.get(ticker.upper()))
            return score_news_items(ticker, filtered_news), filtered_news
        except Exception as exc:
            return NewsScoreResult(
                ticker=ticker,
                news_score=0.0,
                sentiment=NewsSentiment.NEUTRAL,
                news_count=0,
                reasons=[f"News-Fehler: {exc}"],
            ), []


def calculate_today_up_score(context: dict[str, float | None], news_score: float) -> tuple[float, list[str]]:
    momentum = score_momentum_confirmation(
        MomentumInput(
            today_pct=context.get("today_pct"),
            volume_factor=context.get("volume_factor"),
            distance_to_high_pct=context.get("distance_to_high_pct"),
            roc=context.get("roc"),
            adx=context.get("adx"),
            rsi=context.get("rsi"),
            gap_pct=context.get("gap_pct"),
            previous_day_pct=context.get("previous_day_pct"),
            relative_strength_pct=context.get("relative_strength_pct"),
        )
    )
    reasons = momentum.reasons + momentum.risk_reasons
    if news_score >= 70 and context.get("today_pct") is not None and context.get("today_pct") > 0:
        reasons.append("relevante News mit heutiger Kursbestaetigung")
    return momentum.score, _unique_reasons(reasons)

def calculate_overextension_penalty(context: dict[str, float | None], news_score: float) -> tuple[float, list[str]]:
    penalty = 0.0
    reasons: list[str] = []
    previous_day_pct = context.get("previous_day_pct")
    today_pct = context.get("today_pct")
    distance_to_high_pct = context.get("distance_to_high_pct")
    rsi = context.get("rsi")

    if previous_day_pct is not None and previous_day_pct >= 4 and (today_pct is None or today_pct <= 0.5):
        penalty += 25
        reasons.append("Risiko: starker Vortagesanstieg ohne heutige Fortsetzung")
    if previous_day_pct is not None and previous_day_pct >= 7 and today_pct is not None and today_pct < 0:
        penalty += 15
        reasons.append("Risiko: Gewinnmitnahme nach überdehntem Vortag")
    if distance_to_high_pct is not None and distance_to_high_pct >= 3:
        penalty += 15
        reasons.append("Risiko: weit vom Tageshoch entfernt")
    elif distance_to_high_pct is not None and distance_to_high_pct >= 1.5:
        penalty += 8
        reasons.append("Risiko: nicht mehr nahe am Tageshoch")
    if rsi is not None and rsi >= 80:
        penalty += 12
        reasons.append("Risiko: RSI sehr hoch")
    elif rsi is not None and rsi >= 75:
        penalty += 6
        reasons.append("Risiko: RSI erhöht")
    if news_score >= 70 and (today_pct is None or today_pct <= 0.5):
        penalty += 18
        reasons.append("Risiko: hohe News-Bewertung ohne starke heutige Kursreaktion")

    return min(penalty, 60.0), reasons


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


def _market_context(day_row: dict, catalyst_row: dict) -> dict[str, float | None]:
    return {
        "previous_day_pct": _first_number(day_row, catalyst_row, ["Vortag %", "Gestern %", "Previous Day %", "Vortages-Momentum"]),
        "today_pct": _first_number(day_row, catalyst_row, ["Heute %", "Today %", "Intraday %"]),
        "volume_factor": _first_number(day_row, catalyst_row, ["Volumen-Faktor", "Volume Factor"]),
        "distance_to_high_pct": _first_number(day_row, catalyst_row, ["Abstand Tageshoch %", "Distanz Tageshoch %", "DistanceToHigh %", "Distance To High %"]),
        "rsi": _first_number(day_row, catalyst_row, ["RSI"]),
        "roc": _first_number(day_row, catalyst_row, ["ROC"]),
        "adx": _first_number(day_row, catalyst_row, ["ADX"]),
        "gap_pct": _first_number(day_row, catalyst_row, ["Gap %", "Gap", "Gap-Up %", "GapPct"]),
        "relative_strength_pct": _first_number(day_row, catalyst_row, ["Relative Strength %", "RelativeStrength", "RS vs Market %"]),
    }


def _first_number(primary: dict, secondary: dict, keys: list[str]) -> float | None:
    for key in keys:
        value = _number_or_none(primary.get(key))
        if value is not None:
            return value
        value = _number_or_none(secondary.get(key))
        if value is not None:
            return value
    return None


def _adjust_score(score: float | None, today_up_score: float, penalty: float, has_intraday_context: bool) -> float | None:
    if score is None:
        return None
    if has_intraday_context and today_up_score < 40:
        score = min(score, 55.0)
    adjusted = score - penalty
    return max(0.0, min(adjusted, 100.0))


def _recommendation(final_score: float) -> str:
    if final_score >= 90:
        return "⭐⭐⭐⭐⭐ Top Chance"
    if final_score >= 80:
        return "⭐⭐⭐⭐ Sehr interessant"
    if final_score >= 70:
        return "⭐⭐⭐ Beobachten"
    return "Kein Trade"


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


def _number_or_none(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _unique_reasons(reasons: list[str]) -> list[str]:
    unique: list[str] = []
    for reason in reasons:
        if reason and reason not in unique:
            unique.append(reason)
    return unique[:10]


def _format_news_time(news_item: NewsItem | None) -> str:
    if news_item is None or news_item.published_at is None:
        return ""
    return news_item.published_at.isoformat(sep=" ", timespec="minutes")
