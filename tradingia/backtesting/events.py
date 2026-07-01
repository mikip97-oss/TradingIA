from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class BarEvent:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class SignalEvent:
    symbol: str
    timestamp: datetime
    target_percent: float
    reason: str = ""


@dataclass(frozen=True)
class OrderEvent:
    symbol: str
    timestamp: datetime
    side: OrderSide
    quantity: int
    order_type: str = "MKT"


@dataclass(frozen=True)
class FillEvent:
    symbol: str
    timestamp: datetime
    side: OrderSide
    quantity: int
    price: float
    commission: float
    slippage: float
