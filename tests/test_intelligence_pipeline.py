import pandas as pd

from tradingia.intelligence import IntelligencePipeline, filter_relevant_news
from tradingia.news import MockNewsProvider, NewsIntelligenceEngine, NewsItem


def _daytrading_scanner(tickers, max_workers=None, top_anzahl=None):
    return pd.DataFrame(
        [
            {"Aktie": "AAPL", "DayTradeScore": 82},
            {"Aktie": "MSFT", "DayTradeScore": 62},
        ]
    )


def _catalyst_scanner(tickers, max_workers=None, top_anzahl=None):
    return pd.DataFrame(
        [
            {"Aktie": "AAPL", "CatalystScore": 86},
            {"Aktie": "MSFT", "CatalystScore": 40},
        ]
    )


def test_intelligence_pipeline_combines_scores_and_sorts_by_final_score():
    news_engine = NewsIntelligenceEngine(
        MockNewsProvider(
            {
                "AAPL": [
                    {
                        "headline": "Apple beats earnings expectations",
                        "summary": "AAPL raises guidance after major partnership deal",
                    }
                ],
                "MSFT": [
                    {
                        "headline": "Microsoft faces investigation",
                        "summary": "MSFT analyst downgrade follows weak demand",
                    }
                ],
            }
        )
    )
    pipeline = IntelligencePipeline(
        daytrading_scanner=_daytrading_scanner,
        catalyst_scanner=_catalyst_scanner,
        news_engine=news_engine,
        company_names={"AAPL": "Apple", "MSFT": "Microsoft"},
    )

    result = pipeline.run(["MSFT", "AAPL"])

    assert list(result.columns) == [
        "Aktie",
        "FinalScore",
        "Empfehlung",
        "DayTradeScore",
        "CatalystScore",
        "NewsScore",
        "Sentiment",
        "wichtigste Gründe",
    ]
    assert list(result["Aktie"])[0] == "AAPL"
    assert result.loc[result["Aktie"] == "AAPL", "DayTradeScore"].iloc[0] == 82
    assert result.loc[result["Aktie"] == "AAPL", "CatalystScore"].iloc[0] == 86
    assert result.loc[result["Aktie"] == "AAPL", "NewsScore"].iloc[0] > 70
    assert result.loc[result["Aktie"] == "AAPL", "Sentiment"].iloc[0] == "positive"


def test_intelligence_pipeline_runs_without_news_api_key_or_news_items():
    pipeline = IntelligencePipeline(
        daytrading_scanner=_daytrading_scanner,
        catalyst_scanner=_catalyst_scanner,
        news_engine=NewsIntelligenceEngine(MockNewsProvider()),
    )

    result = pipeline.run(["AAPL"])

    assert len(result) == 1
    assert result.iloc[0]["Aktie"] == "AAPL"
    assert result.iloc[0]["NewsScore"] == 0.0
    assert result.iloc[0]["Sentiment"] == "neutral"


def test_intelligence_pipeline_isolates_scanner_errors():
    def broken_scanner(tickers, max_workers=None, top_anzahl=None):
        raise RuntimeError("scanner down")

    pipeline = IntelligencePipeline(
        daytrading_scanner=broken_scanner,
        catalyst_scanner=_catalyst_scanner,
        news_engine=NewsIntelligenceEngine(MockNewsProvider()),
    )

    result = pipeline.run(["AAPL"])

    assert len(result) == 1
    assert result.iloc[0]["DayTradeScore"] == ""
    assert result.iloc[0]["CatalystScore"] == 86


def test_intelligence_pipeline_isolates_news_errors_per_ticker():
    class BrokenProvider:
        name = "broken"

        def get_news(self, ticker, limit=20):
            raise RuntimeError("news down")

    pipeline = IntelligencePipeline(
        daytrading_scanner=_daytrading_scanner,
        catalyst_scanner=_catalyst_scanner,
        news_engine=NewsIntelligenceEngine(BrokenProvider()),
    )

    result = pipeline.run(["AAPL"])

    assert result.iloc[0]["NewsScore"] == 0.0
    assert result.iloc[0]["Sentiment"] == "neutral"
    assert "News-Fehler" in result.iloc[0]["wichtigste Gründe"]


def test_filter_relevant_news_prefers_ticker_or_company_name():
    relevant_by_ticker = NewsItem(ticker="AAPL", headline="AAPL beats earnings")
    relevant_by_company = NewsItem(ticker="AAPL", headline="Apple announces major deal")
    irrelevant = NewsItem(ticker="AAPL", headline="Market update mentions no company")

    filtered = filter_relevant_news([relevant_by_ticker, relevant_by_company, irrelevant], "AAPL", "Apple Inc")

    assert filtered == [relevant_by_ticker, relevant_by_company]


def test_intelligence_pipeline_deduplicates_tickers():
    calls = []

    def day_scanner(tickers, max_workers=None, top_anzahl=None):
        calls.append(tickers)
        return pd.DataFrame([{"Aktie": "AAPL", "DayTradeScore": 80}])

    pipeline = IntelligencePipeline(
        daytrading_scanner=day_scanner,
        catalyst_scanner=lambda tickers, max_workers=None, top_anzahl=None: pd.DataFrame(),
        news_engine=NewsIntelligenceEngine(MockNewsProvider()),
    )

    result = pipeline.run(["aapl", "AAPL", " "])

    assert calls == [["AAPL"]]
    assert len(result) == 1
