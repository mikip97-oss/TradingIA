from __future__ import annotations

from dataclasses import dataclass

from tradingia.backtesting.costs import TransactionCostModel
from tradingia.backtesting.data import PandasBarFeed
from tradingia.backtesting.execution import SimulatedExecutionHandler
from tradingia.backtesting.metrics import summarize_equity_curve
from tradingia.backtesting.portfolio import Portfolio
from tradingia.backtesting.strategy import Strategy


@dataclass
class BacktestResult:
    equity_curve: list[dict[str, float | str]]
    trades: list[dict[str, float | int | str]]
    metrics: dict[str, float]


class BacktestEngine:
    def __init__(
        self,
        initial_cash: float = 10000,
        costs: TransactionCostModel | None = None,
        max_position_percent: float = 1.0,
    ) -> None:
        self.initial_cash = initial_cash
        self.costs = costs or TransactionCostModel()
        self.max_position_percent = max_position_percent

    def run(self, feed: PandasBarFeed, strategy: Strategy) -> BacktestResult:
        portfolio = Portfolio(
            initial_cash=self.initial_cash,
            max_position_percent=self.max_position_percent,
        )
        execution = SimulatedExecutionHandler(self.costs)

        for bar in feed:
            portfolio.mark_to_market(bar)
            for signal in strategy.on_bar(bar):
                order = portfolio.create_order(signal, bar.close)
                if order is None:
                    continue
                fill = execution.execute(order, bar)
                portfolio.apply_fill(fill)
                portfolio.mark_to_market(bar)

        trades = [
            {
                "timestamp": fill.timestamp.isoformat(),
                "symbol": fill.symbol,
                "side": fill.side.value,
                "quantity": fill.quantity,
                "price": round(fill.price, 6),
                "commission": round(fill.commission, 6),
                "slippage": round(fill.slippage, 6),
            }
            for fill in portfolio.fills
        ]

        metrics = summarize_equity_curve(portfolio.equity_curve, self.initial_cash)
        return BacktestResult(portfolio.equity_curve, trades, metrics)
