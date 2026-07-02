from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from tradingia.backtesting.engine import BacktestResult


METRIC_COLUMNS = [
    "Generated At",
    "Report Name",
    "Ending Equity",
    "Return %",
    "Max Drawdown %",
    "Winrate %",
    "Profit Factor",
    "Sharpe Ratio",
    "Sortino Ratio",
    "Durchschnittlicher Gewinn",
    "Durchschnittlicher Verlust",
    "Anzahl Trades",
    "Durchschnittliche Haltedauer",
]


@dataclass
class ResearchReport:
    name: str
    generated_at: datetime
    equity_curve: pd.DataFrame
    drawdown: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict[str, float | int | str]
    output_paths: dict[str, Path] = field(default_factory=dict)


class ResearchDashboard:
    def __init__(self, output_dir: str | Path = "reports/research") -> None:
        self.output_dir = Path(output_dir)

    def build_report(
        self,
        result: BacktestResult,
        report_name: str = "backtest",
        generated_at: datetime | None = None,
    ) -> ResearchReport:
        timestamp = generated_at or datetime.now()
        equity_curve = self._equity_curve(result)
        drawdown = self._drawdown(equity_curve)
        trades = self._closed_trades(result.trades)
        metrics = self._metrics(result, equity_curve, drawdown, trades, report_name, timestamp)

        return ResearchReport(
            name=report_name,
            generated_at=timestamp,
            equity_curve=equity_curve,
            drawdown=drawdown,
            trades=trades,
            metrics=metrics,
        )

    def export(self, report: ResearchReport) -> ResearchReport:
        report_dir = self.output_dir / self._safe_report_id(report.name, report.generated_at)
        report_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = report_dir / "metrics.csv"
        equity_path = report_dir / "equity_curve.csv"
        drawdown_path = report_dir / "drawdown.csv"
        trades_path = report_dir / "trades.csv"
        html_path = report_dir / "report.html"

        pd.DataFrame([report.metrics], columns=METRIC_COLUMNS).to_csv(metrics_path, index=False)
        report.equity_curve.to_csv(equity_path, index=False)
        report.drawdown.to_csv(drawdown_path, index=False)
        report.trades.to_csv(trades_path, index=False)
        html_path.write_text(self._html(report), encoding="utf-8")

        report.output_paths = {
            "metrics_csv": metrics_path,
            "equity_curve_csv": equity_path,
            "drawdown_csv": drawdown_path,
            "trades_csv": trades_path,
            "html_report": html_path,
        }
        return report

    def build_and_export(
        self,
        result: BacktestResult,
        report_name: str = "backtest",
        generated_at: datetime | None = None,
    ) -> ResearchReport:
        return self.export(self.build_report(result, report_name, generated_at))

    def _equity_curve(self, result: BacktestResult) -> pd.DataFrame:
        equity = pd.DataFrame(result.equity_curve)
        if equity.empty:
            return pd.DataFrame(columns=["timestamp", "symbol", "cash", "equity", "return_pct"])

        equity = equity.copy()
        equity["timestamp"] = pd.to_datetime(equity["timestamp"])
        equity["equity"] = equity["equity"].astype(float)
        equity["return_pct"] = equity["equity"].pct_change().fillna(0.0) * 100
        return equity

    def _drawdown(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        if equity_curve.empty:
            return pd.DataFrame(columns=["timestamp", "equity", "drawdown_pct"])

        values = equity_curve["equity"].astype(float)
        running_max = values.cummax()
        drawdown_pct = ((values - running_max) / running_max) * 100
        return pd.DataFrame(
            {
                "timestamp": equity_curve["timestamp"],
                "equity": values,
                "drawdown_pct": drawdown_pct.fillna(0.0),
            }
        )

    def _closed_trades(self, fills: list[dict[str, float | int | str]]) -> pd.DataFrame:
        open_positions: dict[str, list[dict[str, float | int | str]]] = {}
        closed = []

        for fill in fills:
            symbol = str(fill["symbol"])
            side = str(fill["side"])
            quantity = int(fill["quantity"])
            price = float(fill["price"])
            commission = float(fill.get("commission", 0.0))
            timestamp = pd.to_datetime(fill["timestamp"])

            if side == "BUY":
                open_positions.setdefault(symbol, []).append(
                    {
                        "entry_time": timestamp,
                        "entry_price": price,
                        "quantity": quantity,
                        "commission": commission,
                    }
                )
                continue

            remaining = quantity
            positions = open_positions.setdefault(symbol, [])
            while remaining > 0 and positions:
                entry = positions[0]
                matched_quantity = min(remaining, int(entry["quantity"]))
                entry_commission = float(entry["commission"]) * (matched_quantity / int(entry["quantity"]))
                exit_commission = commission * (matched_quantity / quantity)
                pnl = (price - float(entry["entry_price"])) * matched_quantity - entry_commission - exit_commission
                holding_days = (timestamp - pd.to_datetime(entry["entry_time"])).total_seconds() / 86400

                closed.append(
                    {
                        "symbol": symbol,
                        "entry_time": entry["entry_time"],
                        "exit_time": timestamp,
                        "quantity": matched_quantity,
                        "entry_price": float(entry["entry_price"]),
                        "exit_price": price,
                        "pnl": round(pnl, 6),
                        "holding_days": round(holding_days, 6),
                    }
                )

                entry["quantity"] = int(entry["quantity"]) - matched_quantity
                remaining -= matched_quantity
                if int(entry["quantity"]) <= 0:
                    positions.pop(0)

        return pd.DataFrame(
            closed,
            columns=["symbol", "entry_time", "exit_time", "quantity", "entry_price", "exit_price", "pnl", "holding_days"],
        )

    def _metrics(
        self,
        result: BacktestResult,
        equity_curve: pd.DataFrame,
        drawdown: pd.DataFrame,
        trades: pd.DataFrame,
        report_name: str,
        generated_at: datetime,
    ) -> dict[str, float | int | str]:
        returns = equity_curve["equity"].pct_change().dropna() if not equity_curve.empty else pd.Series(dtype=float)
        downside_returns = returns[returns < 0]
        wins = trades[trades["pnl"] > 0] if not trades.empty else pd.DataFrame()
        losses = trades[trades["pnl"] < 0] if not trades.empty else pd.DataFrame()
        gross_profit = float(wins["pnl"].sum()) if not wins.empty else 0.0
        gross_loss = abs(float(losses["pnl"].sum())) if not losses.empty else 0.0

        return {
            "Generated At": generated_at.isoformat(timespec="seconds"),
            "Report Name": report_name,
            "Ending Equity": round(float(result.metrics.get("ending_equity", equity_curve["equity"].iloc[-1] if not equity_curve.empty else 0.0)), 4),
            "Return %": round(float(result.metrics.get("total_return_pct", 0.0)), 4),
            "Max Drawdown %": round(float(result.metrics.get("max_drawdown_pct", drawdown["drawdown_pct"].min() if not drawdown.empty else 0.0)), 4),
            "Winrate %": round((len(wins) / len(trades) * 100) if len(trades) else 0.0, 4),
            "Profit Factor": round((gross_profit / gross_loss) if gross_loss else 0.0, 4),
            "Sharpe Ratio": round(self._sharpe_ratio(returns), 4),
            "Sortino Ratio": round(self._sortino_ratio(returns, downside_returns), 4),
            "Durchschnittlicher Gewinn": round(float(wins["pnl"].mean()) if not wins.empty else 0.0, 4),
            "Durchschnittlicher Verlust": round(float(losses["pnl"].mean()) if not losses.empty else 0.0, 4),
            "Anzahl Trades": int(len(trades)),
            "Durchschnittliche Haltedauer": round(float(trades["holding_days"].mean()) if not trades.empty else 0.0, 4),
        }

    def _sharpe_ratio(self, returns: pd.Series) -> float:
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        return float((returns.mean() / returns.std()) * (252 ** 0.5))

    def _sortino_ratio(self, returns: pd.Series, downside_returns: pd.Series) -> float:
        if len(returns) < 2 or len(downside_returns) < 2 or downside_returns.std() == 0:
            return 0.0
        return float((returns.mean() / downside_returns.std()) * (252 ** 0.5))

    def _safe_report_id(self, report_name: str, generated_at: datetime) -> str:
        safe_name = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in report_name).strip("_")
        timestamp = generated_at.strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{safe_name or 'backtest'}"

    def _html(self, report: ResearchReport) -> str:
        metrics_table = pd.DataFrame([report.metrics], columns=METRIC_COLUMNS).to_html(index=False, escape=True)
        equity_table = report.equity_curve.tail(20).to_html(index=False, escape=True)
        drawdown_table = report.drawdown.tail(20).to_html(index=False, escape=True)
        trades_table = report.trades.to_html(index=False, escape=True)

        return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>TradingIA Research Report - {report.name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 28px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; text-align: right; }}
    th {{ background: #f0f4f8; }}
    td:first-child, th:first-child {{ text-align: left; }}
  </style>
</head>
<body>
  <h1>TradingIA Research Report</h1>
  <p><strong>Report:</strong> {report.name}</p>
  <p><strong>Erstellt:</strong> {report.generated_at.isoformat(timespec='seconds')}</p>

  <h2>Kennzahlen</h2>
  {metrics_table}

  <h2>Equity Curve</h2>
  {equity_table}

  <h2>Drawdown</h2>
  {drawdown_table}

  <h2>Geschlossene Trades</h2>
  {trades_table}
</body>
</html>
"""
