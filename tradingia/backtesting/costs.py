from __future__ import annotations

from dataclasses import dataclass

from tradingia.backtesting.events import OrderEvent, OrderSide


@dataclass(frozen=True)
class TransactionCostModel:
    commission_per_share: float = 0.005
    minimum_commission: float = 1.0
    slippage_bps: float = 2.0

    def commission(self, order: OrderEvent) -> float:
        return max(self.minimum_commission, abs(order.quantity) * self.commission_per_share)

    def execution_price(self, order: OrderEvent, reference_price: float) -> tuple[float, float]:
        slippage_amount = reference_price * (self.slippage_bps / 10_000)
        if order.side == OrderSide.BUY:
            return reference_price + slippage_amount, slippage_amount
        return reference_price - slippage_amount, slippage_amount
