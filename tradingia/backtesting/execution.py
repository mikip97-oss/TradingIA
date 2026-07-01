from __future__ import annotations

from dataclasses import dataclass

from tradingia.backtesting.costs import TransactionCostModel
from tradingia.backtesting.events import BarEvent, FillEvent, OrderEvent


@dataclass
class SimulatedExecutionHandler:
    costs: TransactionCostModel

    def execute(self, order: OrderEvent, bar: BarEvent) -> FillEvent:
        price, slippage = self.costs.execution_price(order, bar.close)
        return FillEvent(
            symbol=order.symbol,
            timestamp=bar.timestamp,
            side=order.side,
            quantity=order.quantity,
            price=price,
            commission=self.costs.commission(order),
            slippage=slippage,
        )
