from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from tradingia.backtesting.engine import BacktestEngine
from tradingia.regime import MarketRegimeEngine
from tradingia.research.dashboard import ResearchDashboard, ResearchReport
from tradingia.research.optimizer import OptimizationResult, ParameterOptimizer, build_parameter_grid
from tradingia.research.strategy_lab import StrategyLab, StrategyLabResult
from tradingia.strategies.ema_crossover import EMACrossoverStrategy
from tradingia.strategies.registry import default_strategy_specs


@dataclass
class ResearchRunnerResult:
    strategy_leaderboard: pd.DataFrame
    optimizer_leaderboard: pd.DataFrame
    reports: list[ResearchReport]


def generate_sample_bars(symbol: str = "AAPL", days: int = 140) -> pd.DataFrame:
    start = datetime(2024, 1, 1, 9, 30)
    rows = []

    for index in range(days):
        trend = index * 0.28
        cycle = ((index % 12) - 6) * 0.35
        pullback = -4.0 if 70 <= index <= 82 else 0.0
        price = 100 + trend + cycle + pullback

        rows.append(
            {
                "symbol": symbol,
                "timestamp": start + timedelta(days=index),
                "open": round(price - 0.4, 4),
                "high": round(price + 1.2, 4),
                "low": round(price - 1.2, 4),
                "close": round(price, 4),
                "volume": 1_000_000 + (index % 20) * 10_000,
            }
        )

    return pd.DataFrame(rows)


def build_ema_parameter_grid() -> list[dict[str, float | int]]:
    raw_grid = build_parameter_grid(
        {
            "short_window": [3, 5, 8],
            "long_window": [10, 15, 20],
            "target_percent": [0.5, 1.0],
        }
    )
    return [parameters for parameters in raw_grid if parameters["short_window"] < parameters["long_window"]]


def run_research(
    output_dir: str | Path = "reports/research_runner",
    generated_at: datetime | None = None,
) -> ResearchRunnerResult:
    timestamp = generated_at or datetime.now()
    bars = generate_sample_bars()
    engine = BacktestEngine(initial_cash=10_000)
    dashboard = ResearchDashboard(output_dir=output_dir)

    strategy_lab = StrategyLab(engine)
    strategy_results = strategy_lab.run(
        bars,
        default_strategy_specs(),
        regime_engine=MarketRegimeEngine(fast_ema_window=5, slow_ema_window=15, trend_adx_threshold=15),
    )
    strategy_leaderboard = strategy_lab.leaderboard(strategy_results)

    optimizer = ParameterOptimizer(engine)
    optimizer_results = optimizer.run(
        bars,
        strategy_name="ema_crossover",
        strategy_class=EMACrossoverStrategy,
        parameter_grid=build_ema_parameter_grid(),
    )
    optimizer_leaderboard = optimizer.leaderboard(optimizer_results)

    reports = []
    reports.extend(_export_strategy_reports(dashboard, strategy_results, timestamp))
    reports.extend(_export_optimizer_reports(dashboard, optimizer_results, timestamp))

    return ResearchRunnerResult(strategy_leaderboard, optimizer_leaderboard, reports)


def _export_strategy_reports(
    dashboard: ResearchDashboard,
    results: list[StrategyLabResult],
    generated_at: datetime,
) -> list[ResearchReport]:
    reports = []
    for result in results:
        report_name = f"strategy_lab_{result.strategy_name}_{result.regime}"
        reports.append(dashboard.build_and_export(result.result, report_name=report_name, generated_at=generated_at))
    return reports


def _export_optimizer_reports(
    dashboard: ResearchDashboard,
    results: list[OptimizationResult],
    generated_at: datetime,
) -> list[ResearchReport]:
    reports = []
    for index, result in enumerate(results, start=1):
        short_window = result.parameters.get("short_window", "na")
        long_window = result.parameters.get("long_window", "na")
        target_percent = result.parameters.get("target_percent", "na")
        report_name = f"optimizer_{index:02d}_ema_{short_window}_{long_window}_{target_percent}"
        reports.append(dashboard.build_and_export(result.result, report_name=report_name, generated_at=generated_at))
    return reports


def main() -> None:
    result = run_research()

    print("\n=== Strategy Lab Leaderboard ===")
    print(result.strategy_leaderboard.to_string(index=False))

    print("\n=== Parameter Optimizer Leaderboard ===")
    print(result.optimizer_leaderboard.to_string(index=False))

    print("\nReports exportiert:")
    for report in result.reports:
        html_path = report.output_paths.get("html_report")
        print(f"- {report.name}: {html_path}")


if __name__ == "__main__":
    main()
