from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class EvaluationMetrics:
    total_recommendations: int
    hit_rate: float
    average_return_pct: float
    average_gain_pct: float
    average_loss_pct: float
    best_score_threshold: float | None

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "Anzahl Empfehlungen": self.total_recommendations,
            "Trefferquote": self.hit_rate,
            "Durchschnittliche Rendite %": self.average_return_pct,
            "Durchschnittlicher Gewinn %": self.average_gain_pct,
            "Durchschnittlicher Verlust %": self.average_loss_pct,
            "Beste Score-Schwelle": self.best_score_threshold,
        }


def evaluate_recommendations(
    recommendation_files: str | Path | list[str | Path],
    future_prices: pd.DataFrame,
    *,
    horizon_days: int = 1,
    hit_threshold_pct: float = 0.0,
    score_column: str = "FinalScore",
) -> tuple[pd.DataFrame, EvaluationMetrics]:
    recommendations = load_recommendations(recommendation_files)
    if recommendations.empty:
        evaluated = _empty_evaluated_frame()
        return evaluated, _metrics(evaluated, score_column)

    prices = _normalize_price_frame(future_prices)
    rows = []
    for _, recommendation in recommendations.iterrows():
        rows.append(_evaluate_row(recommendation, prices, horizon_days, hit_threshold_pct))

    evaluated = pd.DataFrame(rows)
    metrics = _metrics(evaluated, score_column)
    return evaluated, metrics


def load_recommendations(files: str | Path | list[str | Path]) -> pd.DataFrame:
    file_list = [files] if isinstance(files, (str, Path)) else files
    frames = []
    for file in file_list:
        path = Path(file)
        if path.exists():
            frames.append(pd.read_csv(path))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _evaluate_row(recommendation: pd.Series, prices: pd.DataFrame, horizon_days: int, hit_threshold_pct: float) -> dict:
    ticker = str(recommendation.get("Aktie", "")).upper()
    recommendation_date = pd.to_datetime(recommendation.get("Datum"), errors="coerce")
    entry_price = _number_or_none(recommendation.get("Einstiegskurs"))
    exit_price = _future_price(prices, ticker, recommendation_date, horizon_days)
    performance_pct = _performance(entry_price, exit_price)
    hit = bool(performance_pct is not None and performance_pct > hit_threshold_pct)

    return {
        "Datum": recommendation.get("Datum"),
        "Aktie": ticker,
        "TodayUpScore": _number_or_none(recommendation.get("TodayUpScore")),
        "FinalScore": _number_or_none(recommendation.get("FinalScore")),
        "Empfehlung": recommendation.get("Empfehlung", ""),
        "Einstiegskurs": entry_price,
        "Vergleichskurs": exit_price,
        "Performance %": round(performance_pct, 4) if performance_pct is not None else None,
        "Treffer": hit,
        "Teil-Scores": recommendation.get("Teil-Scores", ""),
    }


def _normalize_price_frame(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return pd.DataFrame(columns=["Datum", "Aktie", "Close"])
    frame = prices.copy()
    if "Datum" not in frame.columns:
        frame = frame.reset_index().rename(columns={"index": "Datum"})
    frame["Datum"] = pd.to_datetime(frame["Datum"], errors="coerce")
    frame["Aktie"] = frame["Aktie"].astype(str).str.upper()
    return frame.sort_values(["Aktie", "Datum"]).reset_index(drop=True)


def _future_price(prices: pd.DataFrame, ticker: str, recommendation_date: pd.Timestamp, horizon_days: int) -> float | None:
    if pd.isna(recommendation_date) or prices.empty:
        return None
    target_date = recommendation_date + pd.Timedelta(days=horizon_days)
    ticker_prices = prices[(prices["Aktie"] == ticker) & (prices["Datum"] >= target_date)]
    if ticker_prices.empty:
        return None
    row = ticker_prices.iloc[0]
    return _number_or_none(row.get("Close"))


def _performance(entry_price: float | None, exit_price: float | None) -> float | None:
    if entry_price is None or exit_price is None or entry_price == 0:
        return None
    return ((exit_price - entry_price) / entry_price) * 100


def _metrics(evaluated: pd.DataFrame, score_column: str) -> EvaluationMetrics:
    valid = evaluated.dropna(subset=["Performance %"]) if not evaluated.empty else evaluated
    if valid.empty:
        return EvaluationMetrics(0, 0.0, 0.0, 0.0, 0.0, None)

    gains = valid[valid["Performance %"] > 0]["Performance %"]
    losses = valid[valid["Performance %"] <= 0]["Performance %"]
    return EvaluationMetrics(
        total_recommendations=int(len(valid)),
        hit_rate=round(float(valid["Treffer"].mean()), 4),
        average_return_pct=round(float(valid["Performance %"].mean()), 4),
        average_gain_pct=round(float(gains.mean()), 4) if not gains.empty else 0.0,
        average_loss_pct=round(float(losses.mean()), 4) if not losses.empty else 0.0,
        best_score_threshold=_best_score_threshold(valid, score_column),
    )


def _best_score_threshold(evaluated: pd.DataFrame, score_column: str) -> float | None:
    if score_column not in evaluated.columns:
        return None
    valid = evaluated.dropna(subset=[score_column, "Performance %"])
    if valid.empty:
        return None

    best_threshold = None
    best_return = None
    for threshold in sorted(valid[score_column].dropna().unique()):
        subset = valid[valid[score_column] >= threshold]
        if subset.empty:
            continue
        average_return = float(subset["Performance %"].mean())
        hit_rate = float(subset["Treffer"].mean())
        candidate = (average_return, hit_rate, float(threshold))
        if best_return is None or candidate > best_return:
            best_return = candidate
            best_threshold = float(threshold)
    return best_threshold


def _empty_evaluated_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Datum",
            "Aktie",
            "TodayUpScore",
            "FinalScore",
            "Empfehlung",
            "Einstiegskurs",
            "Vergleichskurs",
            "Performance %",
            "Treffer",
            "Teil-Scores",
        ]
    )


def _number_or_none(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
