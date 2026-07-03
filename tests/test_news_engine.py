import json
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from tradingia.news import FinnhubNewsProvider, MockNewsProvider, NewsIntelligenceEngine, NewsItem, NewsSentiment
from tradingia.news.engine import score_news_items


class _FakeFinnhubResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


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


def test_finnhub_provider_returns_empty_list_without_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    provider = FinnhubNewsProvider(env_file=tmp_path / ".env")

    assert provider.get_news("AAPL") == []
    assert provider.last_error == "FINNHUB_API_KEY fehlt"


def test_finnhub_provider_reads_api_key_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("FINNHUB_API_KEY=from_file\n", encoding="utf-8")

    provider = FinnhubNewsProvider(env_file=env_file)

    assert provider.api_key == "from_file"


def test_finnhub_provider_maps_response_without_real_api_call(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    captured_urls = []

    def fake_urlopen(url, timeout):
        captured_urls.append(url)
        return _FakeFinnhubResponse(
            [
                {
                    "headline": "Apple beats earnings and announces partnership",
                    "summary": "Analyst upgrade follows strong growth",
                    "source": "Finnhub Test",
                    "datetime": 1704067200,
                }
            ]
        )

    provider = FinnhubNewsProvider(api_key="test_key", urlopen_func=fake_urlopen)
    news = provider.get_news("AAPL", limit=1)

    assert len(news) == 1
    assert news[0].ticker == "AAPL"
    assert news[0].headline == "Apple beats earnings and announces partnership"
    assert news[0].source == "Finnhub Test"
    assert news[0].published_at == datetime(2024, 1, 1)
    query = parse_qs(urlparse(captured_urls[0]).query)
    assert query["symbol"] == ["AAPL"]
    assert query["token"] == ["test_key"]


def test_news_engine_scores_finnhub_provider_items_without_real_api_call():
    def fake_urlopen(url, timeout):
        return _FakeFinnhubResponse(
            [
                {
                    "headline": "Nvidia beats earnings expectations",
                    "summary": "Company raises guidance after major deal",
                    "source": "Finnhub Test",
                    "datetime": 1704067200,
                }
            ]
        )

    engine = NewsIntelligenceEngine(FinnhubNewsProvider(api_key="test_key", urlopen_func=fake_urlopen))

    result = engine.score_ticker("NVDA")

    assert result.news_score > 70
    assert result.news_count == 1
    assert result.sentiment == NewsSentiment.POSITIVE
