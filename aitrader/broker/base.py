"""The broker boundary. Only the execution engine talks to a broker.

Errors are typed so the execution engine can act on what is KNOWN:

- BrokerError        a read failed (retry-safe, nothing changed)
- BrokerRejected     a write definitely did not happen
- AmbiguousExecution a write may or may not have happened — never resend;
                     reconcile by querying the broker (EXECUTION_CONTRACT.md §2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..risk.engine import InstrumentSpec, Quote


class BrokerError(RuntimeError):
    pass


class BrokerRejected(BrokerError):
    pass


class AmbiguousExecution(BrokerError):
    pass


@dataclass(frozen=True)
class AccountSnapshot:
    equity: float
    balance: float
    currency: str
    time: int


@dataclass(frozen=True)
class BrokerPosition:
    id: str
    symbol: str
    side: int
    qty: float
    entry: float
    stop: float | None
    target: float | None
    client_id: str | None
    opened: int


@dataclass(frozen=True)
class Fill:
    order_id: str
    position_id: str
    price: float
    time: int


@dataclass(frozen=True)
class ClosedTrade:
    position_id: str
    client_id: str | None
    symbol: str
    side: int
    qty: float
    entry: float
    exit: float
    opened: int
    closed: int
    reason: str  # STOP | TARGET | TIME | MANUAL | UNKNOWN
    pnl: float | None  # account currency; None if the broker did not say
    mfe_price: float | None = None
    mae_price: float | None = None


class Broker(Protocol):
    name: str

    def is_demo(self) -> bool | None: ...
    def account(self) -> AccountSnapshot: ...
    def positions(self) -> list[BrokerPosition]: ...
    def quote(self, symbol: str) -> Quote | None: ...
    def spec(self, symbol: str) -> InstrumentSpec | None: ...
    def place_market(self, symbol: str, side: int, qty: float, stop: float, target: float,
                     client_id: str, meta: dict | None = None, permit=None) -> Fill: ...
    def close(self, position_id: str, client_id: str, reason: str = "MANUAL") -> ClosedTrade: ...
    def find_by_client_id(self, client_id: str) -> BrokerPosition | None: ...
    def closed_since(self, t: int) -> list[ClosedTrade]: ...
