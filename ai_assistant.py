from __future__ import annotations


def erstelle_ki_analyse(aktie: dict) -> str:
    ticker = _value(aktie, "Aktie", "")
    trade_score = _number(_value(aktie, "TradeScore", _value(aktie, "Score", 0)))
    ki_percent = _number(_value(aktie, "KI %", 0))
    recommendation = _value(aktie, "Empfehlung", "")
    reasons = _value(aktie, "Gründe", "")
    entry = _number(_value(aktie, "Einstieg", 0))
    stop_loss = _number(_value(aktie, "Stop-Loss", 0))
    target = _number(_value(aktie, "Ziel", 0))
    rsi = _number(_value(aktie, "RSI", 0))
    volume_factor = _number(_value(aktie, "Volumen-Faktor", 0))
    adx = _number(_value(aktie, "ADX", 0))
    roc = _number(_value(aktie, "ROC", 0))
    today_pct = _number(_value(aktie, "Heute %", 0))
    chance_risk = _number(_value(aktie, "Chance/Risiko", 0))
    pattern = _value(aktie, "Muster", "Keine")

    lines = []
    lines.append(f"KI-Analyse für {ticker}")
    lines.append("=" * 40)
    lines.append(f"TradeScore: {_format_number(trade_score)}/100")
    lines.append(f"KI-Wahrscheinlichkeit: {_format_number(ki_percent)}%")
    lines.append(f"Empfehlung: {recommendation}")

    if reasons:
        lines.append(f"Gründe: {reasons}")

    lines.append("")
    lines.append(_summary(trade_score, recommendation))
    lines.append("")

    lines.append("Technische Werte:")
    lines.append(f"Heute: {_format_number(today_pct)}%")
    lines.append(f"RSI: {_format_number(rsi)}")
    lines.append(f"Volumen-Faktor: {_format_number(volume_factor)}x")
    lines.append(f"ADX: {_format_number(adx)}")
    lines.append(f"ROC: {_format_number(roc)}%")
    lines.append(f"Chance/Risiko: {_format_number(chance_risk)}")

    if pattern and pattern != "Keine":
        lines.append(f"Muster: {pattern}")

    lines.append("")
    lines.append("Trade-Plan:")
    lines.append(f"Einstieg: {_format_price(entry)}")
    lines.append(f"Stop-Loss: {_format_price(stop_loss)}")
    lines.append(f"Ziel: {_format_price(target)}")

    lines.append("")
    lines.append("Hinweis: Das ist keine Anlageberatung. Die Analyse bewertet nur das technische Setup aus der aktuellen Scanner-Zeile.")

    return "\n".join(lines)


def _summary(trade_score: float, recommendation: str) -> str:
    if trade_score >= 80:
        return f"Das aktuelle Setup ist sehr stark und passt zur Tabellen-Empfehlung: {recommendation}."
    if trade_score >= 70:
        return f"Das aktuelle Setup ist ein klarer Trade-Kandidat und passt zur Tabellen-Empfehlung: {recommendation}."
    if trade_score >= 60:
        return f"Das aktuelle Setup ist beobachtenswert und passt zur Tabellen-Empfehlung: {recommendation}."
    return f"Das aktuelle Setup ist schwach oder noch nicht reif. Tabellen-Empfehlung: {recommendation}."


def _value(row: dict, key: str, default):
    value = row.get(key, default)
    return default if value is None else value


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_number(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _format_price(value: float) -> str:
    return f"{value:.2f}"
