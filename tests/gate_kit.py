"""Test plumbing for the hard risk gate: every order a test opens goes through the real gate, as in production.

There is no test-only bypass. `open_direct` authorises the order with the gate and passes its permit, exactly
what the execution engine does. A test that needs a position therefore needs one the gate accepts.
"""

from __future__ import annotations

from dataclasses import replace

from aitrader.execution.engine import ExecutionEngine
from aitrader.memory.db import Database
from aitrader.risk.hard_gate import HardRiskGate, TradeProposal
from aitrader.risk.profile import FTMO_200K

BAL = 200_000.0  # the default evaluation account


def profile_for(balance: float, **overrides):
    p = FTMO_200K if balance == FTMO_200K.starting_balance else FTMO_200K.scaled(balance)
    return replace(p, **overrides) if overrides else p


def gate_for(broker, db: Database | None = None, **overrides) -> HardRiskGate:
    """The broker's gate, attaching one (on its own database if the broker has none) the first time."""
    if broker._gate is not None:
        return broker._gate
    if db is None:
        db = broker.db or Database(":memory:")
    if db.one("SELECT 1 AS x FROM kv WHERE key='kill_switch'") is None:  # never overwrite a test's own switch
        db.set_kv("kill_switch", {"active": False})
    gate = HardRiskGate(db, profile_for(broker.state["start_balance"], **overrides), broker.clock)
    broker.attach_gate(gate)
    return gate


def engine(db: Database, broker, clock, **kw) -> ExecutionEngine:
    return ExecutionEngine(db, broker, clock, gate=gate_for(broker, db), **kw)


def open_direct(broker, symbol: str, side: int, qty: float, stop: float, target: float, client_id: str):
    """Open a paper position the way production does: the gate's permit, then the broker."""
    gate = gate_for(broker)
    q = broker.quote(symbol)
    entry = q.ask if side > 0 else q.bid
    res = gate.authorize(TradeProposal(client_id, client_id, symbol, side, qty, entry, stop, target), broker)
    assert res.approved, res.reasons
    fill = broker.place_market(symbol, side, qty, stop, target, client_id, permit=res.permit)
    gate.confirm(client_id, fill.position_id)
    return fill
