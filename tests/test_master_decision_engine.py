from tradingia.decision import DecisionInput, DecisionWeights, MasterDecisionEngine


def _partial_score_value(partial_scores: str, score_name: str) -> float:
    for part in partial_scores.split(";"):
        name, _, value = part.strip().partition("=")
        if name == score_name:
            return float(value)
    raise AssertionError(f"{score_name} fehlt in Teil-Scores: {partial_scores}")


def test_master_decision_engine_creates_top_chance_from_strong_scores():
    engine = MasterDecisionEngine()

    result = engine.score(
        DecisionInput(
            ticker="NVDA",
            daytrade_score=92,
            catalyst_score=88,
            news_score=84,
            trade_score=78,
            ai_percent=80,
            market_regime="bull",
        )
    )

    assert result.final_score >= 90
    assert result.recommendation == "⭐⭐⭐⭐⭐ Top Chance"
    assert "Bull-Regime bestätigt Long-Setup" in result.reasons
    assert result.partial_scores["DayTradeScore"] == 92


def test_master_decision_engine_penalizes_bear_regime_for_long_setups():
    engine = MasterDecisionEngine()

    bull = engine.score(DecisionInput(ticker="AAPL", daytrade_score=80, catalyst_score=80, market_regime="bull"))
    bear = engine.score(DecisionInput(ticker="AAPL", daytrade_score=80, catalyst_score=80, market_regime="bear"))

    assert bear.final_score < bull.final_score
    assert "Bear-Regime reduziert Long-Setup" in bear.reasons


def test_master_decision_engine_uses_configurable_weights():
    engine = MasterDecisionEngine(DecisionWeights(daytrade=1.0, catalyst=0.0, news=0.0, trade=0.0, ai=0.0, regime_bonus=0.0, regime_penalty=0.0))

    result = engine.score(DecisionInput(ticker="MSFT", daytrade_score=75, catalyst_score=10, news_score=10, trade_score=10, ai_percent=10))

    assert result.final_score == 75
    assert result.recommendation == "⭐⭐⭐ Beobachten"


def test_master_decision_engine_score_many_returns_sorted_dataframe():
    engine = MasterDecisionEngine()

    df = engine.score_many(
        [
            DecisionInput(ticker="WEAK", daytrade_score=30, catalyst_score=20),
            DecisionInput(ticker="STRONG", daytrade_score=90, catalyst_score=90, news_score=80, market_regime="bull"),
        ]
    )

    assert list(df.columns) == ["Aktie", "FinalScore", "Empfehlung", "wichtigste Gründe", "Teil-Scores"]
    assert list(df["Aktie"])[0] == "STRONG"
    assert _partial_score_value(df.iloc[0]["Teil-Scores"], "DayTradeScore") == 90


def test_master_decision_engine_handles_missing_scores():
    engine = MasterDecisionEngine()

    result = engine.score(DecisionInput(ticker="EMPTY"))

    assert result.final_score == 0
    assert result.recommendation == "Kein Trade"
    assert "keine Teil-Scores vorhanden" in result.reasons
