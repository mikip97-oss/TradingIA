from datetime import datetime

import pandas as pd

from tradingia.backtesting.engine import BacktestResult
from tradingia.research.dashboard import METRIC_COLUMNS, ResearchDashboard


def make_result():
    equity_curve = [
        {"timestamp": "2024-01-01T09:30:00", "symbol": "AAPL", "cash": 10000, "equity": 10000},
        {"timestamp": "2024-01-02T09:30:00", "symbol": "AAPL", "cash": 5000, "equity": 10100},
        {"timestamp": "2024-01-03T09:30:00", "symbol": "AAPL", "cash": 10300, "equity": 10300},
        {"timestamp": "2024-01-04T09:30:00", "symbol": "AAPL", "cash": 5000, "equity": 9900},
        {"timestamp": "2024-01-05T09:30:00", "symbol": "AAPL", "cash": 9700, "equity": 9700},
    ]
    trades = [
        {"timestamp": "2024-01-01T09:30:00", "symbol": "AAPL", "side": "BUY", "quantity": 50, "price": 100, "commission": 1, "slippage": 0},
        {"timestamp": "2024-01-03T09:30:00", "symbol": "AAPL", "side": "SELL", "quantity": 50, "price": 106, "commission": 1, "slippage": 0},
        {"timestamp": "2024-01-04T09:30:00", "symbol": "AAPL", "side": "BUY", "quantity": 50, "price": 100, "commission": 1, "slippage": 0},
        {"timestamp": "2024-01-05T09:30:00", "symbol": "AAPL", "side": "SELL", "quantity": 50, "price": 94, "commission": 1, "slippage": 0},
    ]
    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades,
        metrics={"ending_equity": 9700, "total_return_pct": -3.0, "max_drawdown_pct": -5.8252},
    )


def test_research_dashboard_builds_required_metrics():
    dashboard = ResearchDashboard()

    report = dashboard.build_report(make_result(), report_name="unit_test", generated_at=datetime(2024, 1, 6, 12, 0, 0))

    assert list(report.metrics.keys()) == METRIC_COLUMNS
    assert report.metrics["Generated At"] == "2024-01-06T12:00:00"
    assert report.metrics["Report Name"] == "unit_test"
    assert report.metrics["Winrate %"] == 50.0
    assert report.metrics["Profit Factor"] > 0
    assert report.metrics["Anzahl Trades"] == 2
    assert report.metrics["Durchschnittliche Haltedauer"] == 1.5
    assert "drawdown_pct" in report.drawdown.columns
    assert "return_pct" in report.equity_curve.columns


def test_research_dashboard_exports_csv_and_html(tmp_path):
    dashboard = ResearchDashboard(output_dir=tmp_path)

    report = dashboard.build_and_export(
        make_result(),
        report_name="export_test",
        generated_at=datetime(2024, 1, 6, 12, 0, 0),
    )

    assert set(report.output_paths) == {"metrics_csv", "equity_curve_csv", "drawdown_csv", "trades_csv", "html_report"}
    for path in report.output_paths.values():
        assert path.exists()

    metrics = pd.read_csv(report.output_paths["metrics_csv"])
    assert list(metrics.columns) == METRIC_COLUMNS
    assert metrics.iloc[0]["Report Name"] == "export_test"

    html = report.output_paths["html_report"].read_text(encoding="utf-8")
    assert "TradingIA Research Report" in html
    assert "2024-01-06T12:00:00" in html


def test_research_dashboard_handles_open_positions_conservatively():
    result = BacktestResult(
        equity_curve=[{"timestamp": "2024-01-01T09:30:00", "symbol": "AAPL", "cash": 5000, "equity": 10100}],
        trades=[{"timestamp": "2024-01-01T09:30:00", "symbol": "AAPL", "side": "BUY", "quantity": 50, "price": 100, "commission": 1, "slippage": 0}],
        metrics={"ending_equity": 10100, "total_return_pct": 1.0, "max_drawdown_pct": 0.0},
    )

    report = ResearchDashboard().build_report(result, generated_at=datetime(2024, 1, 2, 12, 0, 0))

    assert report.trades.empty
    assert report.metrics["Winrate %"] == 0.0
    assert report.metrics["Profit Factor"] == 0.0
    assert report.metrics["Anzahl Trades"] == 0
