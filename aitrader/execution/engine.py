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
- There is no live path. The account must positively verify as demo/paper (`is_demo() is True`);
  anything else, including "could not tell", blocks. No argument can waive that.
- Edge status (decision/edge_status.py): only a VALIDATED decision may execute unless the
  engine was built with `allow_unvalidated=True` (the PAPER broker, or DEMO with
  EXPERIMENTAL_EXECUTE=true). A decision that does not state its status is unvalidated.
- A stale decision (older than `max_decision_age_s`) or a price that has already moved against
  the entry by more than `max_entry_drift_r` of the stop distance is refused, not chased.
- The hard risk gate (aitrader/risk/hard_gate.py) is the last step before the broker, and not optional: the
  engine cannot be built without one. Its permit is what the broker honours. The gate is held from
  authorisation to the broker's answer, so concurrent requests cannot both pass an aggregate limit.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Callable

from ..broker.base import AmbiguousExecution, BrokerError, BrokerRejected, ClosedTrade
from ..memory.db import Database
from ..risk.hard_gate import HardRiskGate, TradeProposal

#: 1.1.0: a model exit (MODEL_EXIT) is recorded under that reason; every other close is unchanged.
#: 1.2.0: a holding-time exit is recorded as TIME, not the broker's default MANUAL. Label only: the
#:        price and the moment of the close are unchanged, so P/L replays exactly as before.
#: 1.3.0: no `allow_live` argument (there is no live path); unvalidated decisions need
#:        `allow_unvalidated`; stale decisions and adverse entry drift are refused before submission.
#: 1.4.0 (takeover audit): a language-model trade (signal class LLM_TRADER / TRADING_ROOM / EXPERIMENTAL_AI)
#:        is refused here too; an order whose outcome is unknown, or a fill whose entry slippage exceeds
#:        `max_entry_slippage_r` of the stop distance, PAUSES trading until an operator has looked.
#: 1.5.0: every submission passes the hard risk gate (FTMO-style limits) and carries its permit; a request
#:        racing another for the same decision is a DUPLICATE, not an exception; a reconciled unknown order
#:        confirms or releases its gate reservation.
EXECUTION_VERSION = "exec-1.5.0"
#: Signal classes a language model originates. They are SHADOW by route; refused here as a second check.
MODEL_SIGNAL_CLASSES = frozenset({"LLM_TRADER", "TRADING_ROOM", "EXPERIMENTAL_AI"})
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
    def __init__(self, db: Database, broker, clock: Callable[[], int], *, gate: HardRiskGate,
                 allow_unvalidated: bool = False, max_decision_age_s: int = 900, max_entry_drift_r: float = 0.25,
                 max_entry_slippage_r: float = 0.2) -> None:
        if not isinstance(gate, HardRiskGate):
            raise TypeError("the execution engine needs the hard risk gate: there is no execution path without it")
        self.gate = gate
        attach = getattr(broker, "attach_gate", None)
        if attach is not None:
            attach(gate)
        self.db = db
        self.broker = broker
        self.clock = clock
        self.allow_unvalidated = allow_unvalidated
        self.max_decision_age_s = max_decision_age_s
        self.max_entry_drift_r = max_entry_drift_r
        self.max_entry_slippage_r = max_entry_slippage_r

    def _pause(self, reason: str) -> None:
        """Execution uncertainty stops new trading until an operator looks: a pause can only make it safer."""
        self.db.set_kv("paused", True, reason=reason)
        self.db.event("TRADING_PAUSED", {"reason": reason})

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
        if demo is not True:
            return f"account is not verified demo/paper (is_demo={demo}): there is no live path"
        if getattr(decision, "signal_class", None) in MODEL_SIGNAL_CLASSES:
            return (f"signal class {decision.signal_class}: a language model's own trade is research only "
                    "(shadow), never sent")
        status = getattr(decision, "edge_status", None)
        if status != "VALIDATED" and not self.allow_unvalidated:
            return (f"edge status {status or 'not stated'} is not VALIDATED and unvalidated execution is not enabled "
                    "(PAPER, or DEMO with EXPERIMENTAL_EXECUTE=true): shadow only")
        ts = getattr(decision, "timestamp", None)
        if not isinstance(ts, (int, float)):
            return "decision has no timestamp: its age cannot be checked"
        age = self.clock() - ts
        if age > self.max_decision_age_s:
            return f"decision is {int(age)}s old (max {self.max_decision_age_s}s): stale, not executed"
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
        ref = verdict.entry_ref
        if ref is not None and abs(ref - verdict.stop) > 0:
            drift = (live - ref) * side / abs(ref - verdict.stop)
            if drift > self.max_entry_drift_r:
                return (f"price moved {drift:.2f}R against the entry since the risk check (max "
                        f"{self.max_entry_drift_r}R): not chased")
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
        try:
            with self.db.tx() as c:
                c.execute("INSERT INTO intents(id, decision_id, ts, symbol, side, status, payload, updated) "
                          "VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?)",
                          (cid, decision.id, time.time(), decision.instrument, decision.decision,
                           json.dumps(payload), time.time()))
                self.db.event("ORDER_INTENT", {"intent": cid, "decision": decision.id,
                                               **{k: v for k, v in payload.items() if k != "history"}}, ref=cid, conn=c)
        except sqlite3.IntegrityError:  # a concurrent request for the same decision got there first
            return ExecutionResult(decision.id, "DUPLICATE", "intent already exists; not resent")
        problem = self._final_checks(decision, verdict)
        if problem:
            self._set_status(cid, "BLOCKED", {"reason": problem})
            return ExecutionResult(decision.id, "BLOCKED", problem)
        proposal = TradeProposal(decision.id, cid, decision.instrument, side, verdict.qty, verdict.entry_ref,
                                 verdict.stop, verdict.target, (meta or {}).get("swap_per_night", 0.0),
                                 source=str(getattr(decision, "signal_class", None) or "STRATEGY"))
        with self.gate.transaction():
            gate = self.gate.authorize(proposal, self.broker)
            if not gate.approved:
                self._set_status(cid, "BLOCKED", {"reason": gate.line, "gate": gate.code})
                return ExecutionResult(decision.id, "BLOCKED", gate.line)
            self._set_status(cid, "SUBMITTING", {"permit": gate.permit.id})
            try:
                fill = self.broker.place_market(decision.instrument, side, verdict.qty, verdict.stop,
                                                verdict.target, cid, meta=meta or {}, permit=gate.permit)
            except BrokerRejected as exc:
                self.gate.release(cid, f"broker rejected: {exc}")
                self._set_status(cid, "REJECTED", {"reason": str(exc)})
                return ExecutionResult(decision.id, "REJECTED", str(exc))
            except AmbiguousExecution as exc:
                self._set_status(cid, "UNKNOWN", {"reason": str(exc)})
                found = self._lookup(cid)
                if found is not None:
                    return ExecutionResult(decision.id, "FILLED", "confirmed by broker query after ambiguous "
                                           "response", found.id, found.entry)
                self._pause(f"order {cid} outcome unknown after an ambiguous broker response: paused until "
                            "reconciled")
                return ExecutionResult(decision.id, "UNKNOWN", f"outcome unknown ({exc}); will reconcile, never "
                                       "resend")
            except BrokerError as exc:  # anything else during a write is ambiguous too
                self._set_status(cid, "UNKNOWN", {"reason": f"{type(exc).__name__}: {exc}"})
                self._pause(f"order {cid} outcome unknown ({type(exc).__name__}): paused until reconciled")
                return ExecutionResult(decision.id, "UNKNOWN", str(exc))
            self.gate.confirm(cid, fill.position_id)
        self._record_fill(cid, decision, verdict, fill.position_id, fill.price, fill.time, fill.order_id)
        ref = verdict.entry_ref
        if ref is not None and verdict.stop is not None and abs(ref - verdict.stop) > 0:
            slip_r = (fill.price - ref) * side / abs(ref - verdict.stop)  # positive = paid more than the reference
            if slip_r > self.max_entry_slippage_r:
                self._pause(f"entry slippage {slip_r:.2f}R on {cid} exceeds {self.max_entry_slippage_r}R: paused")
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
        self.gate.confirm(cid, found.id)
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
                self.gate.release(it["id"], f"not found at the broker after {checks} checks")
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
