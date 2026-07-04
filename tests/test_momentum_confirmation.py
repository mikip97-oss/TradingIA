from tradingia.momentum import MomentumInput, score_momentum_confirmation


def test_yesterday_strong_today_weak_has_low_momentum_score():
    result = score_momentum_confirmation(
        MomentumInput(
            previous_day_pct=8.0,
            today_pct=-0.5,
            volume_factor=0.9,
            distance_to_high_pct=4.0,
            roc=-0.7,
            adx=14,
            rsi=82,
        )
    )

    assert result.score < 30
    assert result.penalty > 40
    assert "Gewinnmitnahme-Risiko nach starkem Vortag" in result.risk_reasons


def test_today_strong_volume_and_near_high_has_high_momentum_score():
    result = score_momentum_confirmation(
        MomentumInput(
            previous_day_pct=2.0,
            today_pct=2.2,
            volume_factor=2.0,
            distance_to_high_pct=0.4,
            roc=1.8,
            adx=28,
            rsi=66,
            gap_pct=0.4,
            relative_strength_pct=0.8,
        )
    )

    assert result.score >= 85
    assert result.penalty == 0
    assert "erhoehtes Volumen bestaetigt Kaufinteresse" in result.reasons
    assert "sehr nahe am Tageshoch" in result.reasons


def test_gap_up_with_selloff_has_low_momentum_score():
    result = score_momentum_confirmation(
        MomentumInput(
            today_pct=-1.2,
            volume_factor=1.4,
            distance_to_high_pct=5.0,
            roc=-1.1,
            adx=20,
            rsi=48,
            gap_pct=2.5,
        )
    )

    assert result.score < 30
    assert "Gap-Up wird nicht gehalten" in result.risk_reasons
    assert "starke Intraday-Schwaeche" in result.risk_reasons


def test_high_volume_with_falling_price_has_low_momentum_score():
    result = score_momentum_confirmation(
        MomentumInput(
            today_pct=-0.8,
            volume_factor=2.4,
            distance_to_high_pct=3.2,
            roc=-0.9,
            adx=24,
            rsi=52,
        )
    )

    assert result.score < 35
    assert "hohes Volumen bei fallendem Kurs" in result.risk_reasons
    assert "negatives Intraday-Momentum" in result.risk_reasons
