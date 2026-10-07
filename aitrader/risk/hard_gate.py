"""The hard risk gate: deterministic final authority immediately before the broker (PAPER only).

    AI / strategy decision -> trade validation (risk engine, execution checks) -> HARD RISK GATE
        -> execution permit -> paper broker

Every order the paper broker fills must carry a single-use permit that only this gate issues, bound to the exact
symbol, side, size, stop, target and client id it approved. The execution engine cannot be built without a
gate, and the paper broker refuses an order without a valid permit. So a module that calls either one directly
still goes through the gate, or does not trade.

What the gate is (docs/HARD_RISK_GATE.md):

- It never sizes, never changes a trade, never retries. It answers TRADE or NO TRADE. Anything missing,
  non-finite, contradictory, stale or unverifiable is NO TRADE.
- It reads the account from the broker itself (balance, equity, positions, quotes, specs). A caller cannot
  hand it an account state, so an AI cannot change the balance it is judged on.
- Its limits come from a frozen `HardRiskProfile` whose sha256 is fixed when the evaluation run starts. A
  different profile during the run is refused.
- The daily loss is measured on equity, valued conservatively:
  - balance plus unrealised P/L, minus the commission still due on open positions and their accrued financing;
  - against the day's reference: the highest of the balance and equity at the profile's reset time, in the
    profile's time zone.
- Breaching the daily loss limit or the maximum total loss LOCKS the evaluation run. That lock is permanent for
  the run and survives a restart. Only `reset_evaluation()` clears it.
- Corrupt state, impossible account values, conflicting or duplicate execution state, or risk data that cannot
  be verified trip the kill switch: NO TRADE until an explicit clear (`clear_kill`) or reset.
- State is one checksummed row. Every decision and every lifecycle event is an append-only, hash-chained log
  row. A missing, edited or inconsistent state fails closed.
"""

from __future__ import annotations

import json
import math
import re
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from ..memory.db import Database, _canonical, _hash
from ..observability import log_event
from .profile import HardRiskProfile, loss_per_lot, pip_of

GATE_VERSION = "hard-gate-1.0.0"
SYMBOL_RE = re.compile(r"^[A-Z0-9]{6,12}$")
RESET_CONFIRMATION = "RESET-EVALUATION"
CLEAR_KILL_CONFIRMATION = "CLEAR-KILL-SWITCH"
_STATE_KEY = "state"

#: Breaches that end the evaluation run (FTMO fails the account on either). Never cleared but by a reset.
LOCK_CODES = frozenset({"DAILY_LOSS_LIMIT", "MAX_TOTAL_LOSS"})


def _num(x) -> float | None:
    """A finite real number, or None. Booleans and strings are not numbers here."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    x = float(x)
    return x if math.isfinite(x) else None


@dataclass(frozen=True)
class TradeProposal:
    """An untrusted request to open one position. Only these numbers are read; nothing else a model says is."""

    decision_id: str
    client_id: str
    symbol: str
    side: int  # +1 buy, -1 sell
    qty: float  # lots
    entry: float | None  # the entry the decision was priced at
    stop: float | None
    target: float | None
    swap_per_night: float = 0.0  # price units per unit of base per night; a cost when positive
    source: str = "STRATEGY"


@dataclass(frozen=True)
class Permit:
    id: str
    client_id: str
    symbol: str
    side: int
    qty: float
    stop: float
    target: float | None
    issued: int
    expires: int


@dataclass
class GateResult:
    approved: bool
    code: str  # APPROVED or the first rejection code
    reasons: list[str] = field(default_factory=list)  # "CODE: detail", every failed check
    calc: dict = field(default_factory=dict)
    permit: Permit | None = None
    line: str = ""

    @property
    def decision(self) -> str:
        return "TRADE" if self.approved else "NO TRADE"


class _Reject(Exception):
    def __init__(self, code: str, detail: str, kill: bool = False, lock: bool = False) -> None:
        super().__init__(detail)
        self.code, self.detail, self.kill, self.lock = code, detail, kill, lock


class HardRiskGate:
    def __init__(self, db: Database, profile: HardRiskProfile, clock: Callable[[], int]) -> None:
        if not isinstance(profile, HardRiskProfile):
            raise TypeError("the hard risk gate needs a validated HardRiskProfile")
        self.db = db
        self._profile = profile
        self.clock = clock
        self._lock = threading.RLock()
        self._permits: dict[str, tuple[Permit, bool]] = {}  # id -> (permit, used)
        ok, msg = db.verify_chain("risk_gate_log")
        self._chain_fault = None if ok else msg

    @property
    def profile(self) -> HardRiskProfile:  # read-only: there is no setter
        return self._profile

    @contextmanager
    def transaction(self):
        """Held by the execution engine from authorisation to the broker's answer: two requests can never both
        pass the aggregate limits on the same state."""
        with self._lock:
            yield self

    # ── persistent state ────────────────────────────────────────────────

    def _log(self, kind: str, payload: dict, run_id: str | None, decision_id: str | None = None,
             approved: bool | None = None) -> None:
        self.db.append("risk_gate_log", {"kind": kind, "run_id": run_id, "decision_id": decision_id,
                                         "approved": None if approved is None else int(approved),
                                         "payload": {"version": GATE_VERSION, **payload}})

    def _save(self, st: dict) -> None:
        value = _canonical(st)
        with self.db.tx() as c:
            c.execute("INSERT INTO risk_gate_state(key, value, sha256, updated) VALUES (?, ?, ?, ?) "
                      "ON CONFLICT(key) DO UPDATE SET value=excluded.value, sha256=excluded.sha256, "
                      "updated=excluded.updated", (_STATE_KEY, value, _hash("risk-gate", {"v": value}), time.time()))

    def _runs(self) -> list[dict]:
        return self.db.query("SELECT run_id, kind, payload FROM risk_gate_log WHERE kind IN "
                             "('RUN_STARTED', 'LOCKED', 'RUN_RESET') ORDER BY seq")

    def _load(self) -> dict | None:
        """The verified state, None if no evaluation has ever started; raises _Reject(kill) if anything about it
        cannot be trusted."""
        if self._chain_fault:
            raise _Reject("STATE_CORRUPT", f"decision log integrity: {self._chain_fault}", kill=True)
        row = self.db.one("SELECT value, sha256 FROM risk_gate_state WHERE key=?", (_STATE_KEY,))
        runs = self._runs()
        started = [r for r in runs if r["kind"] == "RUN_STARTED"]
        if row is None:
            if started:
                raise _Reject("STATE_CORRUPT", f"the gate state is missing but {len(started)} evaluation run(s) are "
                                               "logged: a deleted state cannot unlock anything", kill=True)
            return None
        if _hash("risk-gate", {"v": row["value"]}) != row["sha256"]:
            raise _Reject("STATE_CORRUPT", "gate state checksum mismatch: edited or truncated", kill=True)
        try:
            st = json.loads(row["value"])
        except ValueError as exc:
            raise _Reject("STATE_CORRUPT", f"gate state is not valid JSON ({exc})", kill=True) from None
        problem = _validate_state(st)
        if problem:
            raise _Reject("STATE_CORRUPT", f"gate state invalid: {problem}", kill=True)
        if not started or started[-1]["run_id"] != st["run_id"]:
            raise _Reject("STATE_CORRUPT", f"gate state run {st['run_id']} is not the last logged run", kill=True)
        locked_logged = any(r["kind"] == "LOCKED" and r["run_id"] == st["run_id"] for r in runs)
        if locked_logged and st["lock"] is None:
            raise _Reject("STATE_CORRUPT", "the log records a lock for this run but the state is unlocked", kill=True)
        return st

    def _new_state(self, run_id: str, now: int, balance: float) -> dict:
        return {"version": GATE_VERSION, "run_id": run_id, "profile_sha256": self._profile.sha256(),
                "profile": self._profile.as_dict(), "started": now, "start_balance": balance, "lock": None,
                "kill": None, "day": None, "last_obs": None, "trading_days": [], "ledger": {}, "seen": [],
                "closed": [], "peak_equity": balance}

    def _check_flat(self, broker) -> float:
        acct, positions = broker.account(), broker.positions()
        bal, eq = _num(acct.balance), _num(acct.equity)
        p = self._profile
        if (bal is None or eq is None or abs(bal - p.starting_balance) > 0.01 or abs(eq - bal) > 0.01
                or positions or acct.currency != p.currency):
            raise _Reject("EVALUATION_REFERENCE_MISMATCH",
                          f"an evaluation starts only from a flat {p.currency} account at the profile's starting "
                          f"balance {p.starting_balance:.2f}: broker balance {acct.balance}, equity {acct.equity}, "
                          f"{len(positions)} open, currency {acct.currency}")
        return bal

    def _start(self, broker, now: int) -> dict:
        """A new evaluation run: only from a flat account at exactly the reference."""
        bal = self._check_flat(broker)
        p = self._profile
        run_id = uuid.uuid4().hex
        st = self._new_state(run_id, now, bal)
        self._log("RUN_STARTED", {"profile": p.as_dict(), "profile_sha256": p.sha256(), "balance": bal, "t": now},
                  run_id)
        self._save(st)
        return st

    # ── the decision ────────────────────────────────────────────────────

    def authorize(self, proposal: TradeProposal, broker) -> GateResult:
        """TRADE (with a single-use permit) or NO TRADE. Never raises for a bad proposal: it refuses it."""
        with self._lock:
            now = self.clock()
            calc: dict = {"t": now, "proposal": _proposal_dict(proposal), "profile": self._profile.name}
            st = None
            try:
                st = self._load()
                if st is None:
                    st = self._start(broker, now)
                calc["run_id"] = st["run_id"]
                self._gate(st, proposal, broker, now, calc)
            except _Reject as rej:
                return self._refuse(st, proposal, rej, calc, now)
            except Exception as exc:  # noqa: BLE001 - anything unexpected is NO TRADE, and the reason is kept
                return self._refuse(st, proposal, _Reject("RISK_DATA_UNVERIFIED",
                                                          f"{type(exc).__name__}: {exc}", kill=True), calc, now)
            permit = Permit(uuid.uuid4().hex, proposal.client_id, proposal.symbol, proposal.side, proposal.qty,
                            proposal.stop, proposal.target, now, now + self._profile.permit_ttl_s)
            st["ledger"][proposal.client_id] = {
                "decision_id": proposal.decision_id, "symbol": proposal.symbol, "side": proposal.side,
                "qty": proposal.qty, "stop": proposal.stop, "entry": calc["executable_entry"],
                "max_loss": calc["max_loss"], "swap_per_night": calc["swap_per_night"],
                "notional": calc["notional"], "status": "RESERVED", "position_id": None, "opened": now}
            st["seen"].append(proposal.decision_id)
            self._save(st)
            self._permits[permit.id] = (permit, False)
            res = GateResult(True, "APPROVED", [], calc, permit)
            res.line = (f"RISK_GATE_APPROVED symbol={proposal.symbol} max_loss={calc['max_loss']:.2f} "
                        f"open_risk_after={calc['open_risk_after']:.2f} equity={calc['equity_conservative']:.2f}")
            self._record(st["run_id"], proposal, res)
            return res

    def _refuse(self, st: dict | None, proposal: TradeProposal, rej: _Reject, calc: dict, now: int) -> GateResult:
        calc.setdefault("rejection", {"code": rej.code, "detail": rej.detail})
        res = GateResult(False, rej.code, [f"{rej.code}: {rej.detail}"], calc)
        res.line = f"RISK_GATE_REJECTED reason={rej.code} " + " ".join(
            f"{k}={_fmt(calc[k])}" for k in ("equity_conservative", "daily_pnl", "daily_limit", "total_pnl",
                                             "total_limit", "open_risk", "max_loss") if k in calc) + f" detail={rej.detail!r}"
        run_id = st["run_id"] if st else None
        if st is not None:  # a trusted state: keep what this call learned (the day's reference, closures)
            try:
                if rej.lock and st["lock"] is None:
                    st["lock"] = {"code": rej.code, "detail": rej.detail, "t": now}
                    self._log("LOCKED", st["lock"], run_id)
                if (rej.lock or rej.kill) and st["kill"] is None:
                    st["kill"] = {"code": rej.code, "detail": rej.detail, "t": now}
                    self._log("KILL_SWITCH", st["kill"], run_id)
                self._save(st)
            except Exception as exc:  # noqa: BLE001 - recording failed: the refusal stands regardless
                res.reasons.append(f"STATE_WRITE_FAILED: {exc}")
        elif rej.kill:  # state untrusted: the kill is recorded in the log only
            self._log("KILL_SWITCH", {"code": rej.code, "detail": rej.detail, "t": now, "state_untrusted": True},
                      run_id)
        if rej.kill or rej.lock:
            self._trip_system_kill_switch(rej)
        self._record(run_id, proposal, res)
        return res

    def _trip_system_kill_switch(self, rej: _Reject) -> None:
        """Also stop the rest of the system (orchestrator, dashboard). Clearing that switch does not clear this
        gate: its own lock and kill state stay until clear_kill / reset_evaluation."""
        try:
            self.db.set_kv("kill_switch", {"active": True, "source": "hard_risk_gate", "code": rej.code,
                                           "reason": rej.detail}, reason=f"hard risk gate: {rej.code}")
        except Exception:  # noqa: BLE001 - the gate refuses on its own state either way
            pass

    def _record(self, run_id: str | None, proposal: TradeProposal, res: GateResult) -> None:
        c = res.calc
        audit = {"timestamp": c.get("t"), "symbol": proposal.symbol, "side": proposal.side,
                 "proposed_entry": proposal.entry, "stop_loss": proposal.stop, "proposed_size": proposal.qty,
                 "monetary_risk": c.get("max_loss"), "risk_breakdown": c.get("loss_breakdown"),
                 "balance": c.get("balance"), "equity": c.get("equity"),
                 "equity_conservative": c.get("equity_conservative"), "daily_pnl": c.get("daily_pnl"),
                 "total_drawdown": c.get("total_pnl"), "open_risk": c.get("open_risk"),
                 "estimated_fees": (c.get("loss_breakdown") or {}).get("commission"),
                 "estimated_slippage": (c.get("loss_breakdown") or {}).get("slippage"),
                 "estimated_financing": (c.get("loss_breakdown") or {}).get("financing"),
                 "risk_gate_result": "APPROVED" if res.approved else "REJECTED",
                 "rejection_reason": None if res.approved else res.code, "reasons": res.reasons,
                 "final_execution_decision": "PERMIT_ISSUED" if res.approved else "NO TRADE",
                 "source": proposal.source, "calculation": c, "line": res.line}
        try:
            self._log("DECISION", audit, run_id, proposal.decision_id, res.approved)
        finally:
            log_event("RISK_GATE", res.line, severity="info" if res.approved else "warning", symbol=proposal.symbol,
                      decision_id=proposal.decision_id, code=res.code)

    def _gate(self, st: dict, pr: TradeProposal, broker, now: int, calc: dict) -> None:
        p = self._profile
        # ── evaluation state: locked, killed, profile ──
        if st["profile_sha256"] != p.sha256():
            raise _Reject("PROFILE_CHANGED", f"this evaluation run was started under profile {st['profile']['name']} "
                                             f"({st['profile_sha256'][:12]}); the gate now holds {p.name} "
                                             f"({p.sha256()[:12]}). A profile cannot change during an evaluation")
        if st["lock"] is not None:
            raise _Reject("RISK_LOCKED", f"evaluation run locked since {st['lock']['t']}: {st['lock']['code']} "
                                         f"({st['lock']['detail']}). Only an explicit evaluation reset clears it")
        if st["kill"] is not None:
            raise _Reject("KILL_SWITCH_ACTIVE", f"gate kill switch: {st['kill']['code']} ({st['kill']['detail']})")
        ks = self.db.get_kv("kill_switch", None)
        if not isinstance(ks, dict) or ks.get("active") is not False:
            raise _Reject("KILL_SWITCH_ACTIVE", f"system kill switch active or unreadable ({ks!r})")

        # ── the account, read from the broker, valued conservatively ──
        self._account(st, broker, now, calc)
        eq_c = calc["equity_conservative"]

        # ── the evaluation limits as they stand ──
        self._day(st, now, calc)
        ref, daily_floor, total_floor = calc["daily_reference"], calc["daily_floor"], p.total_loss_floor
        calc.update(daily_pnl=eq_c - ref, daily_limit=-p.daily_loss_limit, total_pnl=eq_c - p.starting_balance,
                    total_limit=-p.max_total_loss, total_floor=total_floor)
        if eq_c <= total_floor:
            raise _Reject("MAX_TOTAL_LOSS", f"equity {eq_c:.2f} <= floor {total_floor:.2f} (starting balance "
                                            f"{p.starting_balance:.2f} - max loss {p.max_total_loss:.2f})", lock=True)
        if eq_c <= daily_floor:
            raise _Reject("DAILY_LOSS_LIMIT", f"equity {eq_c:.2f} <= daily floor {daily_floor:.2f} (reference "
                                              f"{ref:.2f} - limit {p.daily_loss_limit:.2f}); daily P/L "
                                              f"{eq_c - ref:.2f}", lock=True)

        # ── the proposal ──
        if not isinstance(pr.decision_id, str) or not pr.decision_id or not isinstance(pr.client_id, str) \
                or not pr.client_id:
            raise _Reject("INVALID_REQUEST", "decision id and client id are required")
        if pr.decision_id in st["seen"] or pr.client_id in st["ledger"] or pr.client_id in st["closed"]:
            raise _Reject("DUPLICATE_REQUEST", f"decision {pr.decision_id} / client id {pr.client_id} was already "
                                               "authorised once: never twice")
        if broker.find_by_client_id(pr.client_id) is not None:
            raise _Reject("DUPLICATE_REQUEST", f"the broker already has an order with client id {pr.client_id}")
        if not isinstance(pr.symbol, str) or not SYMBOL_RE.match(pr.symbol):
            raise _Reject("INVALID_INSTRUMENT", f"symbol {pr.symbol!r} is not a valid instrument code")
        if pr.side not in (1, -1) or isinstance(pr.side, bool):
            raise _Reject("INVALID_REQUEST", f"side must be +1 or -1 (got {pr.side!r})")
        spec = broker.spec(pr.symbol)
        if spec is None or not spec.tradable:
            raise _Reject("INVALID_INSTRUMENT", f"no tradable instrument specification for {pr.symbol}")
        cs, vpu = _num(spec.contract_size), _num(spec.value_per_price_unit)
        if not cs or not vpu or cs <= 0 or vpu <= 0:
            raise _Reject("INVALID_INSTRUMENT", f"instrument {pr.symbol} has no valid contract size / value "
                                                f"({spec.contract_size}, {spec.value_per_price_unit})")
        q = self._quote(broker, pr.symbol, now, calc)
        exe = q["ask"] if pr.side > 0 else q["bid"]
        calc["executable_entry"] = exe
        entry = _num(pr.entry)
        if entry is None or entry <= 0:
            raise _Reject("INVALID_ENTRY", f"proposed entry {pr.entry!r} is not a positive finite price")
        dev = abs(entry - exe) / exe
        if dev > p.max_entry_deviation_rel:
            raise _Reject("MARKET_DATA_OUT_OF_TOLERANCE", f"proposed entry {entry} is {dev:.4%} from the executable "
                                                          f"price {exe} (max {p.max_entry_deviation_rel:.4%})")
        if pr.stop is None:
            raise _Reject("MISSING_STOP_LOSS", "every position needs a protective stop: without one its loss is "
                                               "unbounded")
        stop = _num(pr.stop)
        if stop is None or stop <= 0 or (exe - stop) * pr.side <= 0:
            raise _Reject("INVALID_STOP_LOSS", f"stop {pr.stop!r} is not on the loss side of the executable price "
                                               f"{exe}")
        if pr.target is not None:
            tgt = _num(pr.target)
            if tgt is None or tgt <= 0 or (tgt - exe) * pr.side <= 0:
                raise _Reject("INVALID_TARGET", f"target {pr.target!r} is not on the profit side of {exe}")
        qty = _num(pr.qty)
        step, min_lot, max_lot = _num(spec.lot_step), _num(spec.min_lot), _num(spec.max_lot)
        if qty is None or qty <= 0 or not step or not min_lot or not max_lot:
            raise _Reject("INVALID_POSITION_SIZE", f"size {pr.qty!r} (lot step {spec.lot_step}, min {spec.min_lot}, "
                                                   f"max {spec.max_lot}) cannot be verified")
        if abs(round(qty / step) * step - qty) > 1e-9 or qty < min_lot - 1e-12:
            raise _Reject("INVALID_POSITION_SIZE", f"size {qty} is not a multiple of the lot step {step} at or above "
                                                   f"the minimum {min_lot}")
        if qty > min(max_lot, p.max_lots) + 1e-12:
            raise _Reject("BROKER_CONSTRAINT", f"size {qty} exceeds the maximum {min(max_lot, p.max_lots)} lots")
        swap = _num(pr.swap_per_night)
        if swap is None:
            raise _Reject("RISK_NOT_COMPUTABLE", f"financing estimate {pr.swap_per_night!r} is not a number")
        calc["swap_per_night"] = swap

        # ── the trade's deterministic maximum loss, stage by stage ──
        per = loss_per_lot(p, stop_distance=abs(exe - stop), pip=pip_of(pr.symbol), contract_size=cs,
                           value_per_price_unit=vpu, swap_per_night=swap)
        parts = {k: v * qty for k, v in per.items() if k != "total"}
        parts["of_which_spread"] = (q["ask"] - q["bid"]) * cs * vpu * qty
        max_loss = parts["stop"] + parts["commission"] + parts["slippage"] + parts["financing"]
        calc.update(loss_breakdown=parts, max_loss=max_loss, risk_per_trade=p.risk_per_trade)
        if not math.isfinite(max_loss) or max_loss <= 0:
            raise _Reject("RISK_NOT_COMPUTABLE", f"maximum loss {max_loss!r} is not a positive finite amount")
        budget = p.risk_per_trade
        running = 0.0
        for part, code in (("stop", "PER_TRADE_RISK"), ("commission", "FEES_EXCEED_RISK"),
                           ("slippage", "SLIPPAGE_EXCEEDS_RISK"), ("financing", "FINANCING_EXCEEDS_RISK")):
            running += parts[part]
            if running > budget + 1e-9:
                raise _Reject(code, f"loss at the stop incl. {part}: {running:.2f} > per-trade risk {budget:.2f} "
                                    f"(stop {parts['stop']:.2f}, commission {parts['commission']:.2f}, slippage "
                                    f"{parts['slippage']:.2f}, financing {parts['financing']:.2f})")

        # ── aggregate limits ──
        open_risk, remaining = calc["open_risk"], calc["open_remaining_loss"]
        calc["open_risk_after"] = open_risk + max_loss
        if open_risk + max_loss > p.max_open_risk + 1e-9:
            raise _Reject("OPEN_RISK_LIMIT", f"open risk {open_risk:.2f} + this trade {max_loss:.2f} = "
                                             f"{open_risk + max_loss:.2f} > limit {p.max_open_risk:.2f}")
        if calc["open_count"] + 1 > p.max_open_positions:
            raise _Reject("BROKER_CONSTRAINT", f"{calc['open_count']} positions open or in flight; maximum "
                                               f"{p.max_open_positions}")
        worst = eq_c - remaining - max_loss
        calc["worst_case_equity"] = worst
        if worst <= daily_floor:
            raise _Reject("DAILY_LOSS_LIMIT", f"if every stop is hit: equity {eq_c:.2f} - open {remaining:.2f} - "
                                              f"this trade {max_loss:.2f} = {worst:.2f} <= daily floor "
                                              f"{daily_floor:.2f} (reference {ref:.2f} - limit {p.daily_loss_limit:.2f})")
        if worst <= total_floor:
            raise _Reject("MAX_TOTAL_LOSS", f"if every stop is hit: {worst:.2f} <= floor {total_floor:.2f}")
        notional = qty * cs * vpu * exe
        margin, free = notional / p.leverage, eq_c - calc["used_margin"]
        calc.update(notional=notional, required_margin=margin, free_margin=free)
        if not math.isfinite(margin) or margin <= 0:
            raise _Reject("MARGIN_INVALID", f"required margin {margin!r} cannot be computed")
        if margin > free:
            raise _Reject("MARGIN_UNAVAILABLE", f"required margin {margin:.2f} > free margin {free:.2f} at 1:"
                                                f"{p.leverage:g}")

    def _account(self, st: dict, broker, now: int, calc: dict) -> None:
        """Balance, equity and every open position, from the broker, checked against the gate's own ledger."""
        p = self._profile
        try:
            acct = broker.account()
            positions = broker.positions()
        except Exception as exc:  # noqa: BLE001
            raise _Reject("RISK_DATA_UNVERIFIED", f"account or positions unreadable: {exc}", kill=True) from None
        bal, eq = _num(acct.balance), _num(acct.equity)
        calc.update(balance=acct.balance, equity=acct.equity)
        if bal is None or eq is None or bal <= 0 or eq <= 0 or bal > 100 * p.starting_balance:
            raise _Reject("IMPOSSIBLE_ACCOUNT_STATE", f"balance {acct.balance!r}, equity {acct.equity!r}", kill=True)
        if acct.currency != p.currency:
            raise _Reject("IMPOSSIBLE_ACCOUNT_STATE", f"account currency {acct.currency} is not the profile's "
                                                      f"{p.currency}", kill=True)
        ids = [bp.client_id for bp in positions]
        if len(set(ids)) != len(ids) or len({bp.id for bp in positions}) != len(positions):
            raise _Reject("DUPLICATE_EXECUTION_STATE", f"the broker reports duplicate positions or client ids: {ids}",
                          kill=True)
        ledger = st["ledger"]
        unknown = [bp.id for bp in positions if bp.client_id not in ledger]
        if unknown:
            raise _Reject("CONFLICTING_EXECUTION_STATE", f"open positions the gate never authorised: {unknown}",
                          kill=True)
        live = {bp.client_id: bp for bp in positions}
        for cid in [c for c, e in ledger.items() if e["status"] == "OPEN" and c not in live]:
            st["closed"].append(cid)  # closed at the broker: its result is now in the balance
            del ledger[cid]
        open_risk = remaining = used_margin = due = notional_total = 0.0
        for cid, e in ledger.items():
            bp = live.get(cid)
            if bp is None:  # RESERVED: in flight or unknown outcome; counted at its full risk, conservatively
                open_risk += e["max_loss"]
                remaining += e["max_loss"]
                used_margin += e["notional"] / p.leverage
                continue
            e["status"], e["position_id"] = "OPEN", bp.id
            if _num(bp.stop) is None or abs(bp.qty - e["qty"]) > 1e-9 or bp.side != e["side"] or bp.symbol != e["symbol"]:
                raise _Reject("CONFLICTING_EXECUTION_STATE", f"position {bp.id} ({cid}) differs from what was "
                                                             f"authorised or has no stop", kill=True)
            spec, q = broker.spec(bp.symbol), broker.quote(bp.symbol)
            if spec is None or q is None or _num(q.bid) is None or _num(q.ask) is None:
                raise _Reject("RISK_DATA_UNVERIFIED", f"open position {bp.id} {bp.symbol} cannot be valued (no quote or "
                                                      "no conversion rate)", kill=True)
            units = spec.contract_size * spec.value_per_price_unit
            exit_px = q.bid if bp.side > 0 else q.ask
            nights = _rollovers(int(bp.opened), now)
            accrued = max(0.0, e["swap_per_night"]) * nights * units * bp.qty
            commission = p.commission_per_lot_rt * bp.qty
            due += commission + accrued
            to_stop = max(0.0, (exit_px - bp.stop) * bp.side) * units * bp.qty
            rem = to_stop + p.slippage_pips * pip_of(bp.symbol) * units * bp.qty + commission + \
                max(0.0, e["swap_per_night"]) * p.swap_nights_allowance * units * bp.qty
            open_risk += max(e["max_loss"], rem)
            remaining += rem
            notional = bp.qty * units * exit_px
            notional_total += notional
            used_margin += notional / p.leverage
        unreal = eq - bal
        if not positions and abs(unreal) > 0.01:
            raise _Reject("IMPOSSIBLE_ACCOUNT_STATE", f"equity {eq} differs from balance {bal} with no open position",
                          kill=True)
        if positions and abs(unreal) > notional_total + 0.01:
            raise _Reject("IMPOSSIBLE_ACCOUNT_STATE", f"unrealised P/L {unreal:.2f} exceeds the open notional "
                                                      f"{notional_total:.2f}", kill=True)
        eq_c = eq - due
        calc.update(equity_conservative=eq_c, costs_due_on_open=due, open_risk=open_risk,
                    open_remaining_loss=remaining, used_margin=used_margin, open_count=len(ledger))
        st["peak_equity"] = max(st["peak_equity"], eq_c)

    def _day(self, st: dict, now: int, calc: dict) -> None:
        """Roll the trading day at the profile's reset time in its own time zone; record the day's reference."""
        p = self._profile
        day_id = self.day_id(now)
        last = st["last_obs"]
        bal, eq_c = float(calc["balance"]), calc["equity_conservative"]
        if last is not None and now < last["t"]:
            raise _Reject("IMPOSSIBLE_ACCOUNT_STATE", f"clock went backwards ({now} < last observation {last['t']})",
                          kill=True)
        if st["day"] is None or st["day"]["id"] != day_id:
            # The reference is the highest value seen at the roll: the new day's first balance and equity, and
            # the last observation of the previous day (losses between it and the reset are counted today).
            cands = [bal, eq_c] + ([last["equity"], last["balance"]] if last else [])
            st["day"] = {"id": day_id, "reference": max(cands), "t": now, "balance": bal, "equity": eq_c}
        st["last_obs"] = {"t": now, "equity": eq_c, "balance": bal}
        ref = st["day"]["reference"]
        calc.update(day_id=day_id, daily_reference=ref, daily_floor=ref - p.daily_loss_limit,
                    reset=f"{p.reset_hour:02d}:00 {p.reset_timezone}")

    def day_id(self, now: int) -> str:
        """The trading day `now` belongs to: the local date in the profile's zone after its reset hour."""
        local = datetime.fromtimestamp(now, timezone.utc).astimezone(self._profile.tz)
        return (local - timedelta(hours=self._profile.reset_hour)).date().isoformat()

    def _quote(self, broker, symbol: str, now: int, calc: dict) -> dict:
        p = self._profile
        try:
            q = broker.quote(symbol)
        except Exception as exc:  # noqa: BLE001
            raise _Reject("MARKET_DATA_MISSING", f"no quote for {symbol}: {exc}") from None
        if q is None:
            raise _Reject("MARKET_DATA_MISSING", f"no quote for {symbol}")
        bid, ask, t = _num(q.bid), _num(q.ask), _num(q.time)
        calc["quote"] = {"bid": q.bid, "ask": q.ask, "time": q.time}
        if bid is None or ask is None or t is None or bid <= 0 or ask <= 0:
            raise _Reject("MARKET_DATA_MISSING", f"quote incomplete: bid {q.bid!r}, ask {q.ask!r}, time {q.time!r}")
        if ask < bid:
            raise _Reject("MARKET_DATA_CONTRADICTORY", f"ask {ask} below bid {bid}")
        if now - t > p.max_quote_age_s or t > now + 5:
            raise _Reject("MARKET_DATA_STALE", f"quote time {int(t)} vs now {now}: age {now - t:.0f}s (max "
                                               f"{p.max_quote_age_s}s)")
        spread = (ask - bid) / ((ask + bid) / 2)
        if spread > p.max_spread_rel:
            raise _Reject("MARKET_DATA_OUT_OF_TOLERANCE", f"spread {spread:.4%} of mid exceeds {p.max_spread_rel:.4%}")
        return {"bid": bid, "ask": ask, "time": t}

    # ── after the broker answers (called by the execution engine) ───────

    def redeem(self, permit, *, symbol: str, side: int, qty: float, stop: float, target, client_id: str) -> str | None:
        """The paper broker's check: None if the permit authorises exactly this order (it is then spent), else
        why not."""
        with self._lock:
            if not isinstance(permit, Permit):
                return "NO_EXECUTION_PERMIT: an order needs a permit issued by the hard risk gate"
            held = self._permits.get(permit.id)
            if held is None or held[0] != permit:
                return "INVALID_EXECUTION_PERMIT: not issued by this gate"
            if held[1]:
                return "INVALID_EXECUTION_PERMIT: already used"
            if self.clock() > permit.expires:
                return "INVALID_EXECUTION_PERMIT: expired"
            if (permit.symbol, permit.side, permit.qty, permit.stop, permit.target, permit.client_id) != \
                    (symbol, side, qty, stop, target, client_id):
                return "INVALID_EXECUTION_PERMIT: the order differs from what the gate approved"
            try:
                st = self._load()
            except _Reject as rej:
                return f"{rej.code}: {rej.detail}"
            if st is None or st["lock"] is not None or st["kill"] is not None:
                return "RISK_LOCKED: the gate locked or killed after the permit was issued"
            if st["ledger"].get(client_id, {}).get("status") != "RESERVED":
                return "INVALID_EXECUTION_PERMIT: no reservation for this client id"
            self._permits[permit.id] = (permit, True)
            return None

    def _load_quiet(self) -> dict | None:
        """For bookkeeping after the broker answered: an untrusted state is left alone (the next authorisation
        refuses on it), never an exception thrown into the middle of a fill."""
        try:
            return self._load()
        except _Reject:
            return None

    def confirm(self, client_id: str, position_id: str) -> None:
        with self._lock:
            st = self._load_quiet()
            e = st["ledger"].get(client_id) if st else None
            if e is None:
                return
            e["status"], e["position_id"] = "OPEN", position_id
            day = self.day_id(self.clock())
            if day not in st["trading_days"]:
                st["trading_days"].append(day)
            self._save(st)
            self._log("FILLED", {"client_id": client_id, "position_id": position_id}, st["run_id"], e["decision_id"])

    def release(self, client_id: str, reason: str) -> None:
        """The broker DEFINITELY did not open it: its reserved risk is freed. The decision is still never re-sent."""
        with self._lock:
            st = self._load_quiet()
            if st and st["ledger"].get(client_id, {}).get("status") == "RESERVED":
                e = st["ledger"].pop(client_id)
                st["closed"].append(client_id)
                self._save(st)
                self._log("RELEASED", {"client_id": client_id, "reason": reason}, st["run_id"], e["decision_id"])

    def observe(self, broker) -> dict:
        """Heartbeat: roll the day, value the account, lock on a breach. Called every cycle so a day's reference
        is taken promptly after the reset and a breach is caught even when nothing is proposed."""
        with self._lock:
            now = self.clock()
            calc: dict = {"t": now}
            st = None
            try:
                st = self._load()
                if st is None:
                    try:
                        st = self._start(broker, now)
                    except _Reject as rej:
                        return {**self.status(), "start_refused": rej.detail}
                if st["lock"] is not None:
                    return self.status()
                self._account(st, broker, now, calc)
                self._day(st, now, calc)
                p, eq_c = self._profile, calc["equity_conservative"]
                if eq_c <= p.total_loss_floor:
                    raise _Reject("MAX_TOTAL_LOSS", f"equity {eq_c:.2f} <= floor {p.total_loss_floor:.2f}", lock=True)
                if eq_c <= calc["daily_floor"]:
                    raise _Reject("DAILY_LOSS_LIMIT", f"equity {eq_c:.2f} <= daily floor {calc['daily_floor']:.2f}",
                                  lock=True)
                self._save(st)
            except _Reject as rej:
                hb = TradeProposal("heartbeat", "heartbeat", "-", 0, 0.0, None, None, None, source="HEARTBEAT")
                self._refuse(st, hb, rej, calc, now)
            return self.status()

    # ── operator / evaluation controls (never reachable by a model) ─────

    def status(self) -> dict:
        try:
            st = self._load()
        except _Reject as rej:
            return {"state": "FAULT", "code": rej.code, "detail": rej.detail, "trading": False}
        if st is None:
            return {"state": "NOT_STARTED", "trading": False, "profile": self._profile.name}
        last = st["last_obs"] or {}
        eq = last.get("equity")
        profit = None if eq is None else eq - self._profile.starting_balance
        return {"state": "LOCKED" if st["lock"] else "KILLED" if st["kill"] else "ACTIVE",
                "trading": st["lock"] is None and st["kill"] is None, "run_id": st["run_id"],
                "profile": self._profile.name, "lock": st["lock"], "kill": st["kill"], "day": st["day"],
                "equity_conservative": eq, "profit": profit,
                "challenge_target": self._profile.challenge_target,
                "verification_target": self._profile.verification_target,
                "trading_days": len(st["trading_days"]), "min_trading_days": self._profile.min_trading_days,
                "challenge_objective_met": (profit is not None and profit >= self._profile.challenge_target
                                            and len(st["trading_days"]) >= self._profile.min_trading_days),
                "open": {c: e["status"] for c, e in st["ledger"].items()}}

    def clear_kill(self, confirm: str, reason: str) -> bool:
        """Clear a kill switch tripped by unverifiable data. Never clears a lock, never a corrupt state."""
        with self._lock:
            if confirm != CLEAR_KILL_CONFIRMATION or not reason:
                return False
            st = self._load()
            if st is None or st["lock"] is not None or st["kill"] is None or st["kill"]["code"] in LOCK_CODES:
                return False
            self._log("KILL_CLEARED", {"was": st["kill"], "reason": reason}, st["run_id"])
            st["kill"] = None
            self._save(st)
            return True

    def reset_evaluation(self, broker, confirm: str, reason: str) -> dict:
        """An explicit new evaluation run (tests, or a deliberately restarted paper evaluation): the only way a
        lock or a corrupt state is cleared. The account must again be flat at the starting balance. A broken
        decision log is never cleared: that database is evidence, and a new evaluation needs a new one."""
        with self._lock:
            if confirm != RESET_CONFIRMATION or not reason:
                raise PermissionError(f"an evaluation reset needs confirm={RESET_CONFIRMATION!r} and a reason")
            if self._chain_fault:
                raise PermissionError(f"the decision log is broken ({self._chain_fault}): use a new database")
            try:
                self._check_flat(broker)
            except _Reject as rej:
                raise PermissionError(rej.detail) from None
            old = None
            try:
                old = self._load()
            except _Reject:
                pass
            now = self.clock()
            self._log("RUN_RESET", {"reason": reason, "previous_run": old["run_id"] if old else None, "t": now},
                      old["run_id"] if old else None)
            with self.db.tx() as c:
                c.execute("DELETE FROM risk_gate_state WHERE key=?", (_STATE_KEY,))
            self._permits.clear()
            return {"run_id": self._start(broker, now)["run_id"]}


def _validate_state(st) -> str | None:
    need = {"version": str, "run_id": str, "profile_sha256": str, "profile": dict, "started": int,
            "start_balance": (int, float), "trading_days": list, "ledger": dict, "seen": list, "closed": list,
            "peak_equity": (int, float)}
    if not isinstance(st, dict):
        return "not an object"
    for k, t in need.items():
        if k not in st or not isinstance(st[k], t) or isinstance(st[k], bool):
            return f"field {k} missing or of the wrong type"
    for k in ("lock", "kill", "day", "last_obs"):
        if k not in st or not (st[k] is None or isinstance(st[k], dict)):
            return f"field {k} missing or of the wrong type"
    for cid, e in st["ledger"].items():
        for k in ("decision_id", "symbol", "side", "qty", "stop", "max_loss", "swap_per_night", "notional", "status"):
            if k not in e:
                return f"ledger entry {cid} lacks {k}"
        if e["status"] not in ("RESERVED", "OPEN") or _num(e["max_loss"]) is None or e["max_loss"] <= 0:
            return f"ledger entry {cid} invalid"
    if st["day"] is not None and _num(st["day"].get("reference")) is None:
        return "day reference invalid"
    return None


def _rollovers(t0: int, t1: int) -> int:
    from ..broker.paper import rollovers  # the paper broker's own financing convention
    return rollovers(t0, t1)


def _proposal_dict(pr: TradeProposal) -> dict:
    try:
        return asdict(pr)
    except Exception:  # noqa: BLE001
        return {"repr": repr(pr)}


def _fmt(v) -> str:
    return f"{v:.2f}" if isinstance(v, float) else str(v)


__all__ = ["CLEAR_KILL_CONFIRMATION", "GATE_VERSION", "LOCK_CODES", "RESET_CONFIRMATION", "GateResult",
           "HardRiskGate", "Permit", "TradeProposal"]
