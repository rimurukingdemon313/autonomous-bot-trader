"""The paper broker: a simulated account that behaves like a pessimistic real one.

- Market orders fill at the live ASK (buy) / BID (sell) plus slippage.
- Stops and targets are checked against each new bar's bid/ask high and low,
  STOP FIRST when both are touched; a gap through the stop fills at the open;
  a target fills at its price, never better.
- Commission per lot round trip; swap per New York close crossed (a declared
  approximation passed in by the caller, the same one the labels use).
- P/L is converted to the account currency with live rates; if a needed rate
  is missing the spec is unavailable and nothing trades (fail closed).
- State persists in the database, so a restart resumes the same account.
- A client id is accepted once; a repeat is rejected, not filled twice.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Callable

from ..data.resample import bucket_start
from ..memory.db import Database
from ..risk.engine import InstrumentSpec, Quote
from .base import AccountSnapshot, BrokerError, BrokerPosition, BrokerRejected, ClosedTrade, Fill

PAPER_VERSION = "paper-1.0.0"


def contract_size(symbol: str) -> float:
    return 100.0 if symbol.startswith("XAU") else 100_000.0


def pip_of(symbol: str) -> float:
    return 0.1 if symbol.startswith("XAU") else 0.01 if symbol.endswith("JPY") else 0.0001


class PaperBroker:
    name = "paper"

    def __init__(self, feed, clock: Callable[[], int], db: Database | None = None, *,
                 start_balance: float = 20_000.0, currency: str = "USD", slippage_pips: float = 0.1,
                 commission_per_lot_rt: float = 7.0) -> None:
        self.feed = feed
        self.clock = clock
        self.db = db
        self.currency = currency
        self.slippage_pips = slippage_pips
        self.commission = commission_per_lot_rt
        self._lock = threading.RLock()
        self.state = self._load() or {"balance": start_balance, "start_balance": start_balance,
                                      "positions": {}, "closed": [], "seq": 0, "clients": {}}

    # ── persistence ─────────────────────────────────────────────────────

    def _load(self) -> dict | None:
        if self.db is None:
            return None
        row = self.db.one("SELECT value FROM paper_account WHERE key='state'")
        return json.loads(row["value"]) if row else None

    def _save(self) -> None:
        if self.db is None:
            return
        with self.db.tx() as c:
            c.execute("INSERT INTO paper_account(key, value, updated) VALUES ('state', ?, ?) "
                      "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
                      (json.dumps(self.state), time.time()))

    # ── market facts ────────────────────────────────────────────────────

    def is_demo(self) -> bool:
        return True

    def quote(self, symbol: str) -> Quote | None:
        return self.feed.quote(symbol, self.clock())

    def _rate(self, ccy: str) -> float | None:
        """Account-currency value of one unit of `ccy`."""
        if ccy == self.currency:
            return 1.0
        now = self.clock()
        direct = self.feed.quote(f"{ccy}{self.currency}", now)
        if direct is not None:
            return (direct.bid + direct.ask) / 2
        inverse = self.feed.quote(f"{self.currency}{ccy}", now)
        if inverse is not None:
            return 2 / (inverse.bid + inverse.ask)
        return None

    def spec(self, symbol: str) -> InstrumentSpec | None:
        rate = self._rate(symbol[3:])
        if rate is None or self.feed.quote(symbol, self.clock()) is None:
            return None
        return InstrumentSpec(symbol, contract_size(symbol), 0.01, 0.01, 50.0, rate)

    # ── account ─────────────────────────────────────────────────────────

    def _unrealised(self, p: dict) -> float:
        q = self.feed.quote(p["symbol"], self.clock())
        rate = self._rate(p["symbol"][3:])
        if q is None or rate is None:
            raise BrokerError(f"no quote or rate to value the open {p['symbol']} position")
        exit_px = q.bid if p["side"] > 0 else q.ask
        return (exit_px - p["entry"]) * p["side"] * p["qty"] * contract_size(p["symbol"]) * rate

    def account(self) -> AccountSnapshot:
        with self._lock:
            eq = self.state["balance"] + sum(self._unrealised(p) for p in self.state["positions"].values())
            return AccountSnapshot(eq, self.state["balance"], self.currency, self.clock())

    def positions(self) -> list[BrokerPosition]:
        with self._lock:
            return [BrokerPosition(p["id"], p["symbol"], p["side"], p["qty"], p["entry"], p["stop"], p["target"],
                                   p["client_id"], p["opened"]) for p in self.state["positions"].values()]

    def find_by_client_id(self, client_id: str) -> BrokerPosition | None:
        with self._lock:
            pid = self.state["clients"].get(client_id)
            if pid is None:
                return None
            p = self.state["positions"].get(pid)
            if p is None:  # already closed: report the position it was
                c = next((c for c in self.state["closed"] if c["position_id"] == pid), None)
                if c is None:
                    return None
                return BrokerPosition(pid, c["symbol"], c["side"], c["qty"], c["entry"], None, None, client_id, c["opened"])
            return BrokerPosition(p["id"], p["symbol"], p["side"], p["qty"], p["entry"], p["stop"], p["target"],
                                  p["client_id"], p["opened"])

    # ── orders ──────────────────────────────────────────────────────────

    def place_market(self, symbol: str, side: int, qty: float, stop: float, target: float,
                     client_id: str, meta: dict | None = None) -> Fill:
        with self._lock:
            if client_id in self.state["clients"]:
                raise BrokerRejected(f"client id {client_id} already used")
            q = self.feed.quote(symbol, self.clock())
            if q is None:
                raise BrokerRejected(f"no price for {symbol}")
            if qty <= 0:
                raise BrokerRejected("quantity must be positive")
            slip = self.slippage_pips * pip_of(symbol)
            fill = (q.ask + slip) if side > 0 else (q.bid - slip)
            if (fill - stop) * side <= 0 or (target - fill) * side <= 0:
                raise BrokerRejected(f"stop {stop} / target {target} invalid for fill {fill}")
            self.state["seq"] += 1
            pid = f"P{self.state['seq']}"
            now = self.clock()
            self.state["positions"][pid] = {
                "id": pid, "symbol": symbol, "side": side, "qty": qty, "entry": fill, "stop": stop,
                "target": target, "client_id": client_id, "opened": now, "best": fill, "worst": fill,
                "swap_per_night": float((meta or {}).get("swap_per_night", 0.0)),
                "spread_at_entry": q.ask - q.bid}
            self.state["clients"][client_id] = pid
            self._save()
            return Fill(f"O{self.state['seq']}", pid, fill, now)

    def _close(self, pid: str, exit_px: float, when: int, reason: str) -> ClosedTrade:
        p = self.state["positions"].pop(pid)
        rate = self._rate(p["symbol"][3:])
        cs = contract_size(p["symbol"])
        nights = max(0, int((bucket_start([when], "D1")[0] - bucket_start([p["opened"]], "D1")[0]) // 86400))
        gross = (exit_px - p["entry"]) * p["side"] * p["qty"] * cs
        swap = p["swap_per_night"] * nights * p["qty"] * cs
        pnl = None if rate is None else (gross - swap) * rate - self.commission * p["qty"]
        if pnl is not None:
            self.state["balance"] += pnl
        c = {"position_id": pid, "client_id": p["client_id"], "symbol": p["symbol"], "side": p["side"],
             "qty": p["qty"], "entry": p["entry"], "exit": exit_px, "opened": p["opened"], "closed": when,
             "reason": reason, "pnl": pnl, "mfe_price": p["best"], "mae_price": p["worst"], "nights": nights}
        self.state["closed"].append(c)
        self.state["closed"] = self.state["closed"][-5000:]
        self._save()
        return ClosedTrade(**{k: c[k] for k in ClosedTrade.__dataclass_fields__})

    def close(self, position_id: str, client_id: str | None = None, reason: str = "MANUAL") -> ClosedTrade:
        with self._lock:
            p = self.state["positions"].get(position_id)
            if p is None:
                raise BrokerRejected(f"no open position {position_id}")
            q = self.feed.quote(p["symbol"], self.clock())
            if q is None:
                raise BrokerError(f"no price to close {p['symbol']}")
            slip = self.slippage_pips * pip_of(p["symbol"])
            exit_px = (q.bid - slip) if p["side"] > 0 else (q.ask + slip)
            return self._close(position_id, exit_px, self.clock(), reason)

    def on_bar(self, symbol: str, bar: dict) -> list[ClosedTrade]:
        """Apply a newly CLOSED bar to open positions: stop first, then target."""
        closed = []
        with self._lock:
            for pid, p in list(self.state["positions"].items()):
                if p["symbol"] != symbol or p["opened"] > bar["open_time"]:
                    continue
                slip = self.slippage_pips * pip_of(symbol)
                if p["side"] > 0:
                    lo, hi, op = bar["bid_low"], bar["bid_high"], bar["bid_open"]
                    p["best"], p["worst"] = max(p["best"], hi), min(p["worst"], lo)
                    if lo <= p["stop"]:
                        closed.append(self._close(pid, min(op, p["stop"]) - slip, bar["close_time"], "STOP"))
                    elif hi >= p["target"]:
                        closed.append(self._close(pid, p["target"], bar["close_time"], "TARGET"))
                else:
                    lo, hi, op = bar["ask_low"], bar["ask_high"], bar["ask_open"]
                    p["best"], p["worst"] = min(p["best"], lo), max(p["worst"], hi)
                    if hi >= p["stop"]:
                        closed.append(self._close(pid, max(op, p["stop"]) + slip, bar["close_time"], "STOP"))
                    elif lo <= p["target"]:
                        closed.append(self._close(pid, p["target"], bar["close_time"], "TARGET"))
            if not closed and self.state["positions"]:
                self._save()
        return closed

    def closed_since(self, t: int) -> list[ClosedTrade]:
        with self._lock:
            return [ClosedTrade(**{k: c[k] for k in ClosedTrade.__dataclass_fields__})
                    for c in self.state["closed"] if c["closed"] >= t]
