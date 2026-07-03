from ai_assistant import erstelle_ki_analyse


def test_ai_analysis_uses_trade_score_and_current_scanner_columns():
    row = {
        "Aktie": "MU",
        "TradeScore": 75,
        "KI %": 68.4,
        "Empfehlung": "Kaufen",
        "Gründe": "KI positiv, Volumen über Durchschnitt",
        "Einstieg": 132.5,
        "Stop-Loss": 128.1,
        "Ziel": 141.3,
        "Heute %": 2.4,
        "RSI": 61.2,
        "Volumen-Faktor": 1.7,
        "ADX": 24.5,
        "ROC": 3.1,
        "Chance/Risiko": 2.0,
    }

    analysis = erstelle_ki_analyse(row)

    assert "KI-Analyse für MU" in analysis
    assert "TradeScore: 75/100" in analysis
    assert "KI-Wahrscheinlichkeit: 68.4%" in analysis
    assert "Empfehlung: Kaufen" in analysis
    assert "Gründe: KI positiv, Volumen über Durchschnitt" in analysis
    assert "ADX: 24.5" in analysis
    assert "ROC: 3.1%" in analysis
    assert "Score: 0/100" not in analysis
    assert "kein bevorzugter Trade" not in analysis


def test_ai_analysis_keeps_score_fallback_for_older_rows():
    row = {
        "Aktie": "AAPL",
        "Score": 64,
        "Empfehlung": "Beobachten",
    }

    analysis = erstelle_ki_analyse(row)

    assert "TradeScore: 64/100" in analysis
    assert "Empfehlung: Beobachten" in analysis
