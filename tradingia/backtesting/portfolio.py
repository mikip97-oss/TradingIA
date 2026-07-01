from __future__ import annotations

from dataclasses import dataclass, field

from tradingia.backtesting.events import BarEvent, FillEvent, OrderEvent, OrderSide, SignalEvent


@dataclass
class Portfolio:
    initial_cash: float
    max_position_percent: float = 1.0
    cash: float = field(init=False)
    positions: dict[str, int] = field(default_factory=dict)
    last_prices: dict[str, float] = field(default_factory=dict)
    equity_curve: list[dict[str, float | str]] = field(default_factory=list)
    fills: list[FillEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    @property
    def equity(self) -> float:
        holdings = sum(qty * self.last_prices.get(symbol, 0.0) for symbol, qty in self.positions.items())
        return self.cash + holdings

    def mark_to_market(self, bar: BarEvent) -> None:
        self.last_prices[bar.symbol] = bar.close
        self.equity_curve.append(
            {
                "timestamp": bar.timestamp.isoformat(),
                "symbol": bar.symbol,
                "cash": round(self.cash, 6),
                "equity": round(self.equity, 6),
            }
        )

    def create_order(self, signal: SignalEvent, price: float) -> OrderEvent | None:
        target_percent = max(-self.max_position_percent, min(self.max_position_percent, signal.target_percent))
        target_value = self.equity * target_percent
        current_qty = self.positions.get(signal.symbol, 0)
        current_value = current_qty * price
        delta_value = target_value - current_value
        quantity = int(abs(delta_value) // price)

        if quantity <= 0:
            return None

        side = OrderSide.BUY if delta_value > 0 else OrderSide.SELL
        return OrderEvent(signal.symbol, signal.timestamp, side, quantity)

    def apply_fill(self, fill: FillEvent) -> None:
        signed_qty = fill.quantity if fill.side == OrderSide.BUY else -fill.quantity
        gross = fill.quantity * fill.price

        if fill.side == OrderSide.BUY:
            self.cash -= gross + fill.commission
        else:
            self.cash += gross - fill.commission

        self.positions[fill.symbol] = self.positions.get(fill.symbol, 0) + signed_qty
        if self.positions[fill.symbol] == 0:
            del self.positions[fill.symbol]

        self.last_prices[fill.symbol] = fill.price
        self.fills.append(fill)
