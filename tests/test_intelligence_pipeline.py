import pandas as pd

from tradingia.intelligence import IntelligencePipeline, filter_relevant_news
from tradingia.news import MockNewsProvider, NewsIntelligenceEngine, NewsItem


def _assert_required_columns(frame, required_columns):
    normalized_columns = {_normalize_column_name(column) for column in frame.columns}
    normalized_required = {_normalize_column_name(column) for column in required_columns}
    missing = normalized_required - normalized_columns
    assert not missing, f"Fehlende Spalten: {sorted(missing)}"


def _normalize_column_name(column):
    return str(column).replace("ÃƒÂ¼", "ü").replace("Ã¼", "ü")


def _assert_numeric_between(value, lower=0, upper=100):
    number = float(value)
    assert lower <= number <= upper
    return number


def _daytrading_scanner(tickers, max_workers=None, top_anzahl=None):
    return pd.DataFrame(
        [
            {
                "Aktie": "AAPL",
                "DayTradeScore": 82,
                "Heute %": 1.8,
                "Volumen-Faktor": 1.6,
                "Abstand Tageshoch %": 0.5,
                "RSI": 65,
                "ROC": 1.2,
            },
            {
                "Aktie": "MSFT",
                "DayTradeScore": 62,
                "Heute %": -0.3,
                "Volumen-Faktor": 0.8,
                "Abstand Tageshoch %": 3.0,
                "RSI": 55,
                "ROC": -0.4,
            },
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

    _assert_required_columns(
        result,
        {
            "Aktie",
            "FinalScore",
            "Empfehlung",
            "DayTradeScore",
            "CatalystScore",
            "NewsScore",
            "TodayUpScore",
            "OverextensionPenalty",
            "Sentiment",
            "wichtigste Gründe",
        },
    )
    assert list(result["Aktie"])[0] == "AAPL"
    aapl_row = result.loc[result["Aktie"] == "AAPL"].iloc[0]
    assert _assert_numeric_between(aapl_row["DayTradeScore"]) >= 0
    assert _assert_numeric_between(aapl_row["CatalystScore"]) >= 0
    assert _assert_numeric_between(aapl_row["OverextensionPenalty"], lower=0) >= 0
    assert aapl_row["NewsScore"] > 0
    assert aapl_row["TodayUpScore"] > 0
    assert aapl_row["Sentiment"] == "positive"
    assert aapl_row["News Headline"] == "Apple beats earnings expectations"


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


def _news_engine_for_sprint18():
    return NewsIntelligenceEngine(
        MockNewsProvider(
            {
                "PULL": [{"headline": "PULL beats earnings", "summary": "PULL raises guidance after strong deal"}],
                "CONT": [{"headline": "CONT beats earnings", "summary": "CONT raises guidance after strong deal"}],
                "NEWS": [{"headline": "NEWS beats earnings", "summary": "NEWS raises guidance after major deal"}],
            }
        )
    )


def test_yesterday_strong_today_weak_gets_low_score():
    def day_scanner(tickers, max_workers=None, top_anzahl=None):
        return pd.DataFrame(
            [
                {
                    "Aktie": "PULL",
                    "DayTradeScore": 92,
                    "Vortag %": 8.0,
                    "Heute %": -0.4,
                    "Volumen-Faktor": 0.8,
                    "Abstand Tageshoch %": 4.2,
                    "RSI": 82,
                    "ROC": -0.8,
                }
            ]
        )

    def catalyst_scanner(tickers, max_workers=None, top_anzahl=None):
        return pd.DataFrame([{"Aktie": "PULL", "CatalystScore": 88}])

    pipeline = IntelligencePipeline(
        daytrading_scanner=day_scanner,
        catalyst_scanner=catalyst_scanner,
        news_engine=_news_engine_for_sprint18(),
    )

    result = pipeline.run(["PULL"])

    assert result.iloc[0]["TodayUpScore"] < 40
    assert result.iloc[0]["OverextensionPenalty"] >= 40
    assert result.iloc[0]["FinalScore"] < 70
    assert result.iloc[0]["Empfehlung"] == "Kein Trade"


def test_yesterday_up_today_continuation_gets_high_score():
    def day_scanner(tickers, max_workers=None, top_anzahl=None):
        return pd.DataFrame(
            [
                {
                    "Aktie": "CONT",
                    "DayTradeScore": 92,
                    "Vortag %": 6.0,
                    "Heute %": 2.4,
                    "Volumen-Faktor": 2.1,
                    "Abstand Tageshoch %": 0.4,
                    "RSI": 68,
                    "ROC": 1.8,
                }
            ]
        )

    def catalyst_scanner(tickers, max_workers=None, top_anzahl=None):
        return pd.DataFrame([{"Aktie": "CONT", "CatalystScore": 90}])

    pipeline = IntelligencePipeline(
        daytrading_scanner=day_scanner,
        catalyst_scanner=catalyst_scanner,
        news_engine=_news_engine_for_sprint18(),
    )

    result = pipeline.run(["CONT"])

    assert result.iloc[0]["TodayUpScore"] >= 80
    assert result.iloc[0]["OverextensionPenalty"] == 0
    assert result.iloc[0]["FinalScore"] >= 80


def test_high_news_but_weak_price_reaction_is_not_top_candidate():
    def day_scanner(tickers, max_workers=None, top_anzahl=None):
        return pd.DataFrame(
            [
                {
                    "Aktie": "NEWS",
                    "DayTradeScore": 86,
                    "Vortag %": 1.0,
                    "Heute %": 0.1,
                    "Volumen-Faktor": 0.9,
                    "Abstand Tageshoch %": 3.5,
                    "RSI": 64,
                    "ROC": -0.2,
                }
            ]
        )

    def catalyst_scanner(tickers, max_workers=None, top_anzahl=None):
        return pd.DataFrame([{"Aktie": "NEWS", "CatalystScore": 82}])

    pipeline = IntelligencePipeline(
        daytrading_scanner=day_scanner,
        catalyst_scanner=catalyst_scanner,
        news_engine=_news_engine_for_sprint18(),
    )

    result = pipeline.run(["NEWS"])

    assert result.iloc[0]["NewsScore"] > 70
    assert result.iloc[0]["TodayUpScore"] < 40
    assert result.iloc[0]["FinalScore"] < 80
    assert "Top Chance" not in result.iloc[0]["Empfehlung"]
