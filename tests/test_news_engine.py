from datetime import datetime

from tradingia.news import MockNewsProvider, NewsIntelligenceEngine, NewsItem, NewsSentiment
from tradingia.news.engine import score_news_items


def test_mock_news_provider_returns_news_items():
    provider = MockNewsProvider(
        {
            "AAPL": [
                {"headline": "Apple announces major partnership deal", "source": "test"},
            ]
        }
    )

    news = provider.get_news("AAPL")

    assert len(news) == 1
    assert isinstance(news[0], NewsItem)
    assert news[0].ticker == "AAPL"


def test_news_score_rewards_positive_events():
    news = [
        NewsItem(
            ticker="NVDA",
            headline="Nvidia beats earnings expectations and raises guidance",
            published_at=datetime(2024, 1, 1),
        ),
        NewsItem(ticker="NVDA", headline="Analyst upgrade follows strong growth and new partnership deal"),
    ]

    result = score_news_items("NVDA", news)

    assert result.news_score > 70
    assert result.sentiment == NewsSentiment.POSITIVE
    assert result.news_count == 2
    assert "Earnings/Guidance" in result.reasons
    assert "Analyst Upgrade" in result.reasons
    assert "Partnership/Deal" in result.reasons


def test_news_score_penalizes_negative_events():
    news = [
        NewsItem(ticker="TSLA", headline="Tesla misses earnings as analyst downgrade follows weak demand"),
        NewsItem(ticker="TSLA", headline="Company faces lawsuit and investigation after safety probe"),
    ]

    result = score_news_items("TSLA", news)

    assert result.news_score < 40
    assert result.sentiment == NewsSentiment.NEGATIVE
    assert "Analyst Downgrade" in result.reasons
    assert "Lawsuit/Investigation" in result.reasons


def test_news_score_detects_fda_approval():
    news = [NewsItem(ticker="MRNA", headline="FDA approval granted after trial success")]

    result = score_news_items("MRNA", news)

    assert result.news_score > 60
    assert "FDA/Approval" in result.reasons


def test_news_engine_scores_many_as_dataframe():
    provider = MockNewsProvider(
        {
            "AAPL": [{"headline": "Apple upgraded after strong earnings beat"}],
            "MSFT": [{"headline": "Microsoft faces investigation and downgrade"}],
        }
    )
    engine = NewsIntelligenceEngine(provider)

    df = engine.score_many(["MSFT", "AAPL"])

    assert list(df.columns) == ["Aktie", "NewsScore", "Sentiment", "Anzahl News", "wichtigste Gründe"]
    assert list(df["Aktie"])[0] == "AAPL"
    assert df.loc[df["Aktie"] == "AAPL", "Sentiment"].iloc[0] == "positive"


def test_empty_news_returns_neutral_zero_score():
    result = score_news_items("AAPL", [])

    assert result.news_score == 0.0
    assert result.sentiment == NewsSentiment.NEUTRAL
    assert result.news_count == 0
    assert result.reasons == []
