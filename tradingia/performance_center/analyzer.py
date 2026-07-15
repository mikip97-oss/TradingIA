from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tradingia.ml_dataset import DEFAULT_DATASET_PATH

MIN_LABELED_ROWS = 20
FACTOR_COLUMNS = [
    "FinalScore",
    "TodayUpScore",
    "TrendScore",
    "MomentumConfirmationScore",
    "DayTradeScore",
    "CatalystScore",
    "NewsScore",
    "TradeScore",
    "KI %",
]
RETURN_COLUMNS = ["Return_1h", "Return_2h", "Return_EOD"]
HIT_COLUMNS = ["Treffer_1h", "Treffer_2h", "Treffer_EOD"]
SCORE_BUCKET_LABELS = ["0-49", "50-59", "60-69", "70-79", "80-89", "90-100"]


@dataclass(frozen=True)
class PerformanceAnalysis:
    summary: pd.DataFrame
    score_buckets: pd.DataFrame
    factor_analysis: pd.DataFrame
    best_stocks: pd.DataFrame
    worst_stocks: pd.DataFrame
    weekdays: pd.DataFrame
    hours: pd.DataFrame
    best_thresholds: pd.DataFrame
    labeled_rows: int
    is_statistically_reliable: bool


def load_prediction_dataset(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        return _empty_dataset()
    try:
        frame = pd.read_csv(dataset_path)
    except pd.errors.EmptyDataError:
        return _empty_dataset()
    return _prepare_dataset(frame)


def analyze_prediction_dataset(frame: pd.DataFrame, *, min_labeled_rows: int = MIN_LABELED_ROWS) -> PerformanceAnalysis:
    prepared = _prepare_dataset(frame)
    labeled = _labeled_rows(prepared)
    labeled_count = len(labeled)
    reliable = labeled_count >= min_labeled_rows

    summary = _summary(prepared, labeled, reliable, min_labeled_rows)
    buckets = _score_buckets(labeled)
    factors = _factor_analysis(labeled)
    best_stocks = _stock_ranking(labeled, ascending=False)
    worst_stocks = _stock_ranking(labeled, ascending=True)
    weekdays = _weekday_stats(labeled)
    hours = _hour_stats(labeled)
    thresholds = _score_thresholds(labeled)

    return PerformanceAnalysis(
        summary=summary,
        score_buckets=buckets,
        factor_analysis=factors,
        best_stocks=best_stocks,
        worst_stocks=worst_stocks,
        weekdays=weekdays,
        hours=hours,
        best_thresholds=thresholds,
        labeled_rows=labeled_count,
        is_statistically_reliable=reliable,
    )


def export_performance_report(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    output_dir: str | Path = "reports/performance",
    *,
    min_labeled_rows: int = MIN_LABELED_ROWS,
) -> PerformanceAnalysis:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis = analyze_prediction_dataset(load_prediction_dataset(dataset_path), min_labeled_rows=min_labeled_rows)

    analysis.summary.to_csv(output_dir / "summary.csv", index=False, encoding="utf-8")
    analysis.score_buckets.to_csv(output_dir / "score_buckets.csv", index=False, encoding="utf-8")
    analysis.factor_analysis.to_csv(output_dir / "factor_analysis.csv", index=False, encoding="utf-8")
    (output_dir / "report.html").write_text(_html_report(analysis), encoding="utf-8")
    return analysis


def _prepare_dataset(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return _empty_dataset()
    prepared = frame.copy()
    for column in [*FACTOR_COLUMNS, *RETURN_COLUMNS, *HIT_COLUMNS, "Einstiegskurs"]:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    if "Datum" in prepared.columns:
        prepared["Datum"] = pd.to_datetime(prepared["Datum"], errors="coerce")
    if "Uhrzeit" in prepared.columns:
        prepared["Uhrzeit"] = prepared["Uhrzeit"].astype(str)
    return prepared


def _empty_dataset() -> pd.DataFrame:
    return pd.DataFrame(columns=["Datum", "Uhrzeit", "Aktie", "FinalScore", *RETURN_COLUMNS, *HIT_COLUMNS])


def _labeled_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if "Return_EOD" not in frame.columns:
        return frame.iloc[0:0].copy()
    return frame.loc[frame["Return_EOD"].notna()].copy()


def _summary(frame: pd.DataFrame, labeled: pd.DataFrame, reliable: bool, min_labeled_rows: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Kennzahl": "Anzahl Empfehlungen", "Wert": len(frame)},
            {"Kennzahl": "Anzahl gelabelter Zeilen", "Wert": len(labeled)},
            {"Kennzahl": "Belastbare Aussage", "Wert": "Ja" if reliable else f"Nein, mindestens {min_labeled_rows} gelabelte Zeilen erforderlich"},
            {"Kennzahl": "Trefferquote 1h %", "Wert": _hit_rate(labeled, "Treffer_1h")},
            {"Kennzahl": "Trefferquote 2h %", "Wert": _hit_rate(labeled, "Treffer_2h")},
            {"Kennzahl": "Trefferquote EOD %", "Wert": _hit_rate(labeled, "Treffer_EOD")},
            {"Kennzahl": "Durchschnittliche Rendite 1h %", "Wert": _mean(labeled, "Return_1h")},
            {"Kennzahl": "Durchschnittliche Rendite 2h %", "Wert": _mean(labeled, "Return_2h")},
            {"Kennzahl": "Durchschnittliche Rendite EOD %", "Wert": _mean(labeled, "Return_EOD")},
            {"Kennzahl": "Durchschnittlicher Gewinn EOD %", "Wert": _mean_filtered(labeled, "Return_EOD", positive=True)},
            {"Kennzahl": "Durchschnittlicher Verlust EOD %", "Wert": _mean_filtered(labeled, "Return_EOD", positive=False)},
        ]
    )


def _score_buckets(labeled: pd.DataFrame) -> pd.DataFrame:
    columns = ["Score-Bucket", "Anzahl Signale", "Trefferquote EOD %", "Durchschnittsrendite EOD %"]
    if labeled.empty or "FinalScore" not in labeled.columns:
        return pd.DataFrame(columns=columns)
    buckets = pd.cut(
        labeled["FinalScore"],
        bins=[-0.01, 49, 59, 69, 79, 89, 100],
        labels=SCORE_BUCKET_LABELS,
        include_lowest=True,
    )
    working = labeled.assign(**{"Score-Bucket": buckets})
    rows = []
    for label in SCORE_BUCKET_LABELS:
        group = working.loc[working["Score-Bucket"].astype(str) == label]
        rows.append(
            {
                "Score-Bucket": label,
                "Anzahl Signale": len(group),
                "Trefferquote EOD %": _hit_rate(group, "Treffer_EOD"),
                "Durchschnittsrendite EOD %": _mean(group, "Return_EOD"),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _factor_analysis(labeled: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for factor in FACTOR_COLUMNS:
        if factor not in labeled.columns or labeled.empty:
            rows.append(_empty_factor_row(factor))
            continue
        factor_values = pd.to_numeric(labeled[factor], errors="coerce")
        returns = pd.to_numeric(labeled.get("Return_EOD"), errors="coerce")
        valid = factor_values.notna() & returns.notna()
        correlation = float(factor_values[valid].corr(returns[valid])) if valid.sum() >= 2 else pd.NA
        high_group = labeled.loc[factor_values >= 70]
        high_hit_rate = _hit_rate(high_group, "Treffer_EOD")
        high_return = _mean(high_group, "Return_EOD")
        usefulness = _factor_usefulness(correlation, high_hit_rate, high_return)
        rows.append(
            {
                "Faktor": factor,
                "Korrelation Return_EOD": _round_or_na(correlation),
                "Trefferquote hoher Faktor %": high_hit_rate,
                "Durchschnittsrendite hoher Faktor %": high_return,
                "Anzahl hohe Faktorwerte": len(high_group),
                "Nutzwert": usefulness,
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty and "Nutzwert" in result.columns:
        result = result.sort_values(by="Nutzwert", ascending=False, na_position="last").reset_index(drop=True)
        result.insert(0, "Rang", range(1, len(result) + 1))
    return result


def _empty_factor_row(factor: str) -> dict:
    return {
        "Faktor": factor,
        "Korrelation Return_EOD": pd.NA,
        "Trefferquote hoher Faktor %": pd.NA,
        "Durchschnittsrendite hoher Faktor %": pd.NA,
        "Anzahl hohe Faktorwerte": 0,
        "Nutzwert": pd.NA,
    }


def _stock_ranking(labeled: pd.DataFrame, *, ascending: bool) -> pd.DataFrame:
    columns = ["Aktie", "Anzahl Signale", "Trefferquote EOD %", "Durchschnittsrendite EOD %"]
    if labeled.empty or "Aktie" not in labeled.columns:
        return pd.DataFrame(columns=columns)
    rows = []
    for ticker, group in labeled.groupby("Aktie"):
        rows.append({"Aktie": ticker, "Anzahl Signale": len(group), "Trefferquote EOD %": _hit_rate(group, "Treffer_EOD"), "Durchschnittsrendite EOD %": _mean(group, "Return_EOD")})
    return pd.DataFrame(rows, columns=columns).sort_values(by="Durchschnittsrendite EOD %", ascending=ascending).head(10).reset_index(drop=True)


def _weekday_stats(labeled: pd.DataFrame) -> pd.DataFrame:
    columns = ["Wochentag", "Anzahl Signale", "Trefferquote EOD %", "Durchschnittsrendite EOD %"]
    if labeled.empty or "Datum" not in labeled.columns:
        return pd.DataFrame(columns=columns)
    working = labeled.dropna(subset=["Datum"]).copy()
    if working.empty:
        return pd.DataFrame(columns=columns)
    working["Wochentag"] = working["Datum"].dt.day_name()
    rows = []
    for weekday, group in working.groupby("Wochentag"):
        rows.append({"Wochentag": weekday, "Anzahl Signale": len(group), "Trefferquote EOD %": _hit_rate(group, "Treffer_EOD"), "Durchschnittsrendite EOD %": _mean(group, "Return_EOD")})
    return pd.DataFrame(rows, columns=columns).sort_values(by="Durchschnittsrendite EOD %", ascending=False).reset_index(drop=True)


def _hour_stats(labeled: pd.DataFrame) -> pd.DataFrame:
    columns = ["Uhrzeit", "Anzahl Signale", "Trefferquote EOD %", "Durchschnittsrendite EOD %"]
    if labeled.empty or "Uhrzeit" not in labeled.columns:
        return pd.DataFrame(columns=columns)
    working = labeled.copy()
    working["Uhrzeit"] = working["Uhrzeit"].astype(str).str.slice(0, 5)
    rows = []
    for hour, group in working.groupby("Uhrzeit"):
        rows.append({"Uhrzeit": hour, "Anzahl Signale": len(group), "Trefferquote EOD %": _hit_rate(group, "Treffer_EOD"), "Durchschnittsrendite EOD %": _mean(group, "Return_EOD")})
    return pd.DataFrame(rows, columns=columns).sort_values(by="Durchschnittsrendite EOD %", ascending=False).head(20).reset_index(drop=True)


def _score_thresholds(labeled: pd.DataFrame) -> pd.DataFrame:
    columns = ["Score-Schwelle", "Anzahl Signale", "Trefferquote EOD %", "Durchschnittsrendite EOD %"]
    if labeled.empty or "FinalScore" not in labeled.columns:
        return pd.DataFrame(columns=columns)
    rows = []
    for threshold in range(50, 96, 5):
        group = labeled.loc[labeled["FinalScore"] >= threshold]
        rows.append({"Score-Schwelle": threshold, "Anzahl Signale": len(group), "Trefferquote EOD %": _hit_rate(group, "Treffer_EOD"), "Durchschnittsrendite EOD %": _mean(group, "Return_EOD")})
    return pd.DataFrame(rows, columns=columns).sort_values(by=["Durchschnittsrendite EOD %", "Trefferquote EOD %"], ascending=False).reset_index(drop=True)


def _html_report(analysis: PerformanceAnalysis) -> str:
    reliability = "belastbar" if analysis.is_statistically_reliable else "noch nicht belastbar"
    return f"""<!doctype html>
<html lang=\"de\">
<head><meta charset=\"utf-8\"><title>TradingIA Performance Center</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;}} table{{border-collapse:collapse;margin-bottom:28px;}} th,td{{border:1px solid #ccc;padding:6px 10px;}} th{{background:#f0f0f0;}}</style></head>
<body>
<h1>TradingIA Performance Center</h1>
<p>Status: {reliability}. Gelabelte Zeilen: {analysis.labeled_rows}. Mindestens {MIN_LABELED_ROWS} gelabelte Zeilen werden fuer belastbare Aussagen erwartet.</p>
<h2>Gesamt</h2>{analysis.summary.to_html(index=False)}
<h2>Score-Buckets</h2>{analysis.score_buckets.to_html(index=False)}
<h2>Faktoranalyse</h2>{analysis.factor_analysis.to_html(index=False)}
<h2>Beste Aktien</h2>{analysis.best_stocks.to_html(index=False)}
<h2>Schlechteste Aktien</h2>{analysis.worst_stocks.to_html(index=False)}
<h2>Beste Wochentage</h2>{analysis.weekdays.to_html(index=False)}
<h2>Beste Uhrzeiten</h2>{analysis.hours.to_html(index=False)}
<h2>Beste Score-Schwellen</h2>{analysis.best_thresholds.to_html(index=False)}
</body></html>"""


def _hit_rate(frame: pd.DataFrame, column: str) -> float | pd.NA:
    if frame.empty or column not in frame.columns:
        return pd.NA
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return pd.NA
    return round(float(values.mean() * 100), 2)


def _mean(frame: pd.DataFrame, column: str) -> float | pd.NA:
    if frame.empty or column not in frame.columns:
        return pd.NA
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return pd.NA
    return round(float(values.mean()), 4)


def _mean_filtered(frame: pd.DataFrame, column: str, *, positive: bool) -> float | pd.NA:
    if frame.empty or column not in frame.columns:
        return pd.NA
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    values = values[values > 0] if positive else values[values < 0]
    if values.empty:
        return pd.NA
    return round(float(values.mean()), 4)


def _round_or_na(value) -> float | pd.NA:
    if pd.isna(value):
        return pd.NA
    return round(float(value), 4)


def _factor_usefulness(correlation, high_hit_rate, high_return) -> float | pd.NA:
    parts = []
    if not pd.isna(correlation):
        parts.append(abs(float(correlation)) * 60)
    if not pd.isna(high_hit_rate):
        parts.append(float(high_hit_rate) * 0.3)
    if not pd.isna(high_return):
        parts.append(max(float(high_return), 0.0) * 10)
    if not parts:
        return pd.NA
    return round(sum(parts), 4)
