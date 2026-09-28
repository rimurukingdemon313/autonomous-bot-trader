"""The execution engine: one approved decision -> at most one broker order.

EXECUTION_CONTRACT.md, implemented:

- Idempotent: the client id is derived from the decision id, and an intent
  row is UNIQUE per decision. A second call for the same decision returns the
  existing state; it never places a second order.
- Intent before action: the intent is persisted as SUBMITTING before the
  broker is called, so a crash between the two is visible on restart.
- Writes are never retried. AmbiguousExecution -> status UNKNOWN, then the
  broker is QUERIED by client id. Found -> FILLED. Not found -> stays UNKNOWN
  and is re-checked by `reconcile()`; after repeated not-found checks it is
  recorded NOT_FOUND. At no point is the order sent again.
- Final validation right before submission: kill switch, pause, account
  type, instrument tradable, live price still on the right side of the stop.
- It never changes side, size, stop or target. It may only refuse.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Callable

from ..broker.base import AmbiguousExecution, BrokerError, BrokerRejected, ClosedTrade
from ..memory.db import Database

#: 1.1.0: a model exit (MODEL_EXIT) is recorded under that reason; every other close is unchanged.
#: 1.2.0: a holding-time exit is recorded as TIME, not the broker's default MANUAL. Label only: the
#:        price and the moment of the close are unchanged, so P/L replays exactly as before.
EXECUTION_VERSION = "exec-1.2.0"
UNKNOWN_RECHECKS = 5


@dataclass
class ExecutionResult:
    decision_id: str
    status: str  # SKIPPED | FILLED | REJECTED | UNKNOWN | DUPLICATE | BLOCKED
    detail: str
    position_id: str | None = None
    fill_price: float | None = None


def client_id_for(decision_id: str) -> str:
    return f"ai-{decision_id}"


class ExecutionEngine:
    def __init__(self, db: Database, broker, clock: Callable[[], int], *, allow_live: bool = False) -> None:
        self.db = db
        self.broker = broker
        self.clock = clock
        self.allow_live = allow_live

    # ── helpers ─────────────────────────────────────────────────────────

    def _intent(self, decision_id: str) -> dict | None:
        return self.db.one("SELECT * FROM intents WHERE decision_id=?", (decision_id,))

    def _set_status(self, intent_id: str, status: str, detail: dict, broker_order_id: str | None = None) -> None:
        with self.db.tx() as c:
            row = c.execute("SELECT payload FROM intents WHERE id=?", (intent_id,)).fetchone()
            payload = json.loads(row[0]) if row else {}
            payload.setdefault("history", []).append({"t": self.clock(), "status": status, **detail})
            c.execute("UPDATE intents SET status=?, payload=?, updated=?, broker_order_id=COALESCE(?, broker_order_id) "
                      "WHERE id=?", (status, json.dumps(payload), time.time(), broker_order_id, intent_id))
            self.db.event(f"ORDER_{status}", {"intent": intent_id, **detail}, ref=intent_id, conn=c)

    def _note(self, intent_id: str, entry: dict) -> None:
        """Append to an intent's history without changing its status."""
        with self.db.tx() as c:
            row = c.execute("SELECT payload FROM intents WHERE id=?", (intent_id,)).fetchone()
            payload = json.loads(row[0])
            payload.setdefault("history", []).append({"t": self.clock(), **entry})
            c.execute("UPDATE intents SET payload=?, updated=? WHERE id=?", (json.dumps(payload), time.time(), intent_id))
            self.db.event("ORDER_" + entry["status"], {"intent": intent_id, **entry}, ref=intent_id, conn=c)

    def executed_ids(self) -> set[str]:
        return {r["decision_id"] for r in self.db.query("SELECT decision_id FROM intents")}

    def _final_checks(self, decision, verdict) -> str | None:
        ks = self.db.get_kv("kill_switch", {"active": False})
        if not isinstance(ks, dict) or ks.get("active") is not False:
            return "kill switch active or unreadable"
        if self.db.get_kv("paused", False):
            return "trading paused"
        demo = self.broker.is_demo()
        if demo is not True and not self.allow_live:
            return f"account is not verified demo/paper (is_demo={demo})"
        try:
            q = self.broker.quote(decision.instrument)
        except BrokerError as exc:
            return f"no quote: {exc}"
        if q is None:
            return "no quote"
        side = 1 if decision.decision == "BUY" else -1
        live = q.ask if side > 0 else q.bid
        if (live - verdict.stop) * side <= 0:
            return f"price {live} already beyond the stop {verdict.stop}"
        if (verdict.target - live) * side <= 0:
            return f"price {live} already beyond the target {verdict.target}"
        return None

    # ── the one write path ──────────────────────────────────────────────

    def execute(self, decision, verdict, meta: dict | None = None) -> ExecutionResult:
        if not verdict.approved:
            return ExecutionResult(decision.id, "SKIPPED", "risk engine did not approve")
        existing = self._intent(decision.id)
        if existing is not None:
            return ExecutionResult(decision.id, "DUPLICATE", f"intent already {existing['status']}; not resent",
                                   existing.get("broker_order_id"))
        cid = client_id_for(decision.id)
        side = 1 if decision.decision == "BUY" else -1
        payload = {"qty": verdict.qty, "stop": verdict.stop, "target": verdict.target, "side": side,
                   "risk_amount": verdict.risk_amount, "version": EXECUTION_VERSION, "history": []}
        with self.db.tx() as c:
            c.execute("INSERT INTO intents(id, decision_id, ts, symbol, side, status, payload, updated) "
                      "VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)",
                      (cid, decision.id, time.time(), decision.instrument, decision.decision,
                       json.dumps(payload), time.time()))
            self.db.event("ORDER_INTENT", {"intent": cid, "decision": decision.id, **{k: v for k, v in payload.items() if k != "history"}},
                          ref=cid, conn=c)
        problem = self._final_checks(decision, verdict)
        if problem:
            self._set_status(cid, "BLOCKED", {"reason": problem})
            return ExecutionResult(decision.id, "BLOCKED", problem)
        self._set_status(cid, "SUBMITTING", {})
        try:
            fill = self.broker.place_market(decision.instrument, side, verdict.qty, verdict.stop,
                                            verdict.target, cid, meta=meta or {})
        except BrokerRejected as exc:
            self._set_status(cid, "REJECTED", {"reason": str(exc)})
            return ExecutionResult(decision.id, "REJECTED", str(exc))
        except AmbiguousExecution as exc:
            self._set_status(cid, "UNKNOWN", {"reason": str(exc)})
            found = self._lookup(cid)
            if found is not None:
                return ExecutionResult(decision.id, "FILLED", "confirmed by broker query after ambiguous response",
                                       found.id, found.entry)
            return ExecutionResult(decision.id, "UNKNOWN", f"outcome unknown ({exc}); will reconcile, never resend")
        except BrokerError as exc:  # anything else during a write is ambiguous too
            self._set_status(cid, "UNKNOWN", {"reason": f"{type(exc).__name__}: {exc}"})
            return ExecutionResult(decision.id, "UNKNOWN", str(exc))
        self._record_fill(cid, decision, verdict, fill.position_id, fill.price, fill.time, fill.order_id)
        return ExecutionResult(decision.id, "FILLED", "filled", fill.position_id, fill.price)

    def _record_fill(self, cid, decision, verdict, position_id, price, t, order_id) -> None:
        side = 1 if decision.decision == "BUY" else -1
        with self.db.tx() as c:
            c.execute("UPDATE intents SET status='FILLED', broker_order_id=?, updated=? WHERE id=?",
                      (order_id, time.time(), cid))
            c.execute("INSERT OR IGNORE INTO positions(id, intent_id, decision_id, symbol, side, qty, entry, stop, target, "
                      "opened, status, payload, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)",
                      (position_id, cid, decision.id, decision.instrument, "BUY" if side > 0 else "SELL",
                       verdict.qty, price, verdict.stop, verdict.target, t,
                       json.dumps({"slippage": price - verdict.entry_ref if verdict.entry_ref else None,
                                   "risk_amount": verdict.risk_amount}), time.time()))
            self.db.event("ORDER_FILLED", {"intent": cid, "position": position_id, "price": price}, ref=cid, conn=c)

    def _lookup(self, cid: str):
        try:
            found = self.broker.find_by_client_id(cid)
        except BrokerError:
            return None
        if found is None:
            return None
        intent = self.db.one("SELECT * FROM intents WHERE id=?", (cid,))
        p = json.loads(intent["payload"])

        class _V:  # the approved parameters, as recorded in the intent
            qty, stop, target, entry_ref, risk_amount = p["qty"], p["stop"], p["target"], None, p.get("risk_amount")

        class _D:
            id, instrument, decision = intent["decision_id"], intent["symbol"], intent["side"]
        self._record_fill(cid, _D, _V, found.id, found.entry, found.opened, None)
        return found

    # ── reconciliation: startup and periodic ────────────────────────────

    def reconcile(self) -> dict:
        report = {"resolved": [], "still_unknown": [], "not_found": [], "orphans": []}
        for it in self.db.query("SELECT * FROM intents WHERE status IN ('SUBMITTING', 'UNKNOWN')"):
            found = self._lookup(it["id"])
            if found is not None:
                report["resolved"].append(it["id"])
                continue
            p = json.loads(it["payload"])
            checks = sum(1 for h in p.get("history", []) if h.get("status") == "RECHECK") + 1
            if checks >= UNKNOWN_RECHECKS:
                self._set_status(it["id"], "NOT_FOUND", {"reason": f"broker has no such order after {checks} checks"})
                report["not_found"].append(it["id"])
            else:
                self._note(it["id"], {"status": "RECHECK", "check": checks})
                report["still_unknown"].append(it["id"])
        try:
            known = {r["id"] for r in self.db.query("SELECT id FROM positions")}
            for bp in self.broker.positions():
                if bp.id not in known:
                    report["orphans"].append({"id": bp.id, "symbol": bp.symbol, "client_id": bp.client_id})
                    self.db.event("ORPHAN_POSITION", {"id": bp.id, "symbol": bp.symbol}, ref=bp.id)
        except BrokerError as exc:
            report["error"] = str(exc)
        return report

    def sync_closures(self) -> list[tuple[dict, ClosedTrade]]:
        """Positions OPEN here but no longer open at the broker -> closed trades."""
        out = []
        open_rows = self.db.query("SELECT * FROM positions WHERE status='OPEN'")
        if not open_rows:
            return out
        try:
            live = {p.id for p in self.broker.positions()}
            since = min(r["opened"] for r in open_rows)
            closed = {c.position_id: c for c in self.broker.closed_since(int(since))}
        except BrokerError:
            return out  # cannot tell: change nothing
        for row in open_rows:
            if row["id"] in live:
                continue
            ct = closed.get(row["id"])
            if ct is None:
                continue  # gone but unexplained: wait for the broker's history rather than invent an exit
            with self.db.tx() as c:
                c.execute("UPDATE positions SET status='CLOSED', updated=? WHERE id=?", (time.time(), row["id"]))
                self.db.event("POSITION_CLOSED", {"position": row["id"], "exit": ct.exit, "reason": ct.reason,
                                                  "pnl": ct.pnl}, ref=row["id"], conn=c)
            out.append((row, ct))
        return out

    def close_position(self, position_id: str, reason: str) -> ClosedTrade | None:
        """Time exit or operator close. A close is a write: never retried."""
        row = self.db.one("SELECT * FROM positions WHERE id=? AND status='OPEN'", (position_id,))
        if row is None:
            return None
        try:
            # The model's own exit and a holding-time exit are recorded as such; an operator close
            # keeps the broker's own label.
            ct = self.broker.close(position_id, client_id_for(row["decision_id"]) + "-close",
                                   **({"reason": reason} if reason in ("MODEL_EXIT", "TIME") else {}))
        except BrokerRejected:
            return None
        except BrokerError as exc:
            self.db.event("CLOSE_UNKNOWN", {"position": position_id, "error": str(exc)}, ref=position_id)
            return None
        self.db.event("CLOSE_SENT", {"position": position_id, "reason": reason}, ref=position_id)
        return ct
