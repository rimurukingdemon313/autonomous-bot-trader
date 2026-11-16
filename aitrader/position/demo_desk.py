"""TRND-1 on a broker's DEMO account, run by the system itself (docs/CTRADER.md).

The paper desk (trend_desk.py) decides at each close and fills at that close. A broker account can only be traded
while its CFDs are open, so this desk runs in the morning after the closes and brings the account to what the rule
holds now. It uses the same decision, from the same final closes, through the same risk engine, hard gate and
execution engine:

- **The month's decision** is taken exactly as the paper desk takes it (decision_for). It reads the latest final
  close; once the month's last weekday has closed, it decides the next month.
- **An index the rule holds and the account does not** is entered. The risk engine sizes it, the hard gate permits
  it, and its stop is 6% below the latest close. This happens only while this month's entry has not been filled:
  after a stop is hit, the index stays flat until the next month-end decision, as on the paper desk.
- **An index the account holds and the rule does not** is closed.
- **Every index held** has its stop moved to 6% below the latest close.
- **A broker refusal** (the market closed, no price) is decided again at the next run, under a new decision id: it
  never happened, so nothing is resent. An UNKNOWN outcome pauses the desk until the account is read (the execution
  engine's rule) and is never resent.
- **A failed demo check** trips the kill switch, and every later run refuses to trade until a person clears it.

Declared differences from the paper desk:

- The entry and the exit happen at the next morning's price, not at the close. In RC-EQ, acting a day late cost the
  rule about 0.2% a year.
- The stop is the broker's own order.

Only a rule a person promoted for DEMO (models/artifacts/promoted_rules_demo.json) executes. Without one the
execution engine refuses every entry before the broker, and the desk trades nothing.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from ..broker.base import BrokerError
from ..data.instruments import INDEX_CFDS
from ..decision.edge_status import classify
from ..execution.engine import ExecutionEngine
from ..memory.db import Database
from ..risk.engine import RiskEngine
from ..risk.hard_gate import HardRiskGate
from ..risk.profile import TRND1_PAPER_200K
from .trend_desk import (DESK_LIMITS, INDICES, RULE_ID, STOP_REL, DailyBar, DailyFeed, PromotedRule, RuleDecision,
                         RuleFileError, TrendDesk, close_time, decision_for, is_last_weekday, next_month)

#: 1.0.0: the first broker desk (the trend desk's rule, size and stop on a DEMO account, run in the morning)
DEMO_DESK_VERSION = "demo-desk-1.0.0"
DEMO_RULES_PATH = Path(__file__).resolve().parents[2] / "models" / "artifacts" / "promoted_rules_demo.json"
STATE_KEY = "demo_desk"


def load_demo_rules(path: Path | str = DEMO_RULES_PATH) -> tuple[list[PromotedRule], str]:
    """Rules a person promoted for a DEMO account. A missing file means none was. A malformed entry, or one whose mode is
    not DEMO, is an error, never a default."""
    p = Path(path)
    if not p.exists():
        return [], "no rule promoted for DEMO: models/artifacts/promoted_rules_demo.json is absent"
    rules = []
    for d in json.loads(p.read_text()).get("rules", []):
        for k in ("rule_id", "status", "health", "instruments", "mode", "promoted_by", "promoted_on", "evidence"):
            if k not in d:
                raise RuleFileError(f"DEMO promotion missing {k!r}")
        if d["mode"] != "DEMO":
            raise RuleFileError(f"{d['rule_id']}: mode {d['mode']!r} in the DEMO promotion file")
        unknown = [s for s in d["instruments"] if s not in INDEX_CFDS]
        if unknown:
            raise RuleFileError(f"{d['rule_id']}: unknown instruments {unknown}")
        rules.append(PromotedRule(d["rule_id"], d["status"], d["health"], tuple(d["instruments"]), "DEMO",
                                  d["promoted_by"], d["promoted_on"], dict(d["evidence"])))
    return rules, f"{len(rules)} rule(s) promoted for DEMO"


def build(db: Database, broker, feed: DailyFeed, clock, rules: list[PromotedRule], start_balance: float,
          rules_note: str = "") -> TrendDesk:
    """The trend desk's parts on a broker account: the hard gate on the desk's profile scaled to the account's
    starting balance, the risk engine on the desk's limits, the execution engine refusing anything not VALIDATED."""
    if db.get_kv("kill_switch") is None:
        db.set_kv("kill_switch", {"active": False}, reason="demo desk: a new account")
    profile = (TRND1_PAPER_200K if start_balance == TRND1_PAPER_200K.starting_balance else
               TRND1_PAPER_200K.scaled(start_balance, name=f"TRND1-DEMO-{start_balance:g}"))
    gate = HardRiskGate(db, profile, clock)
    broker.attach_gate(gate)
    ex = ExecutionEngine(db, broker, clock, gate=gate, allow_unvalidated=False)
    return TrendDesk(db, feed, clock, gate, broker, ex, RiskEngine(replace(DESK_LIMITS, hard=profile)), rules,
                     rules_note)


def trip(db: Database, why: str) -> None:
    """The kill switch, with the reason: a failed demo check stops every later run until a person clears it."""
    db.set_kv("kill_switch", {"active": True, "reason": why, "by": "demo desk"}, reason=f"demo check failed: {why}")


def latest(bars: dict[str, list[DailyBar]], now: int) -> dict[str, DailyBar]:
    """Each index's latest bar that had closed at `now`: nothing later is read."""
    out = {}
    for s, bs in bars.items():
        done = [b for b in bs if close_time(s, b.day) <= now]
        if done:
            out[s] = max(done, key=lambda b: b.day)
    return out


def _state(desk: TrendDesk) -> dict:
    st = desk.db.get_kv(STATE_KEY, None)
    return st if isinstance(st, dict) else {"version": DEMO_DESK_VERSION, "filled": {}, "runs": 0, "closed_r": [],
                                            "week": None, "peak": None, "failed": None}


def run(desk: TrendDesk, bars: dict[str, list[DailyBar]], now: int) -> list[dict]:
    """One morning: the account read, its closures booked, the rule's month applied, every stop moved."""
    st = _state(desk)
    out: list[dict] = []
    ks = desk.db.get_kv("kill_switch", None)
    if not isinstance(ks, dict) or ks.get("active") is not False:
        out.append(desk._event("DEMO_REFUSED", {"why": "the kill switch is active or unreadable",
                                                "kill_switch": ks}))
        return out
    rec = desk.ex.reconcile()  # an earlier run's unknown outcome is settled by reading the account, never by resending
    if any(rec.get(k) for k in ("resolved", "still_unknown", "not_found", "orphans", "error")):
        out.append(desk._event("DEMO_RECONCILED", rec))
    status = desk.gate.observe(desk.broker)
    out += desk._book_closures(st)
    desk._mark(st, now)
    if status.get("state") == "LOCKED" and not st.get("failed"):
        st["failed"] = {"t": now, "lock": status.get("lock")}
        out.append(desk._event("DEMO_ACCOUNT_FAILED", {"lock": status.get("lock")}))
    last = latest(bars, now)
    if st.get("failed"):
        for s, p in desk._held().items():
            ct = desk.ex.close_position(p.id, "FAILED")
            out.append(desk._event("DEMO_EXIT", {"symbol": s, "why": "the account failed", "closed": ct is not None},
                                   ref=p.id))
        out += desk._book_closures(st)
        desk.db.set_kv(STATE_KEY, st, reason="demo desk: a failed account")
        return out
    day_id = datetime.fromtimestamp(now, timezone.utc).strftime("%Y%m%d")
    for s in INDICES:
        b = last.get(s)
        if b is None:
            out.append(desk._event("DEMO_DECISION", {"symbol": s, "action": "NONE", "why": "no final close yet"}))
            continue
        month = (b.day.year, b.day.month)
        target = next_month(month) if is_last_weekday(b.day) else month
        key = f"{target[0]:04d}-{target[1]:02d}"
        dec = decision_for(desk.feed.closes(s, now), target)
        held = desk._held().get(s)
        base = {"symbol": s, "for_month": key, "close_day": str(b.day), "close": b.close,
                **{k: dec[k] for k in ("hold", "month_end", "month_end_close", "mean_of_ten", "why")},
                "held_before": held is not None}
        if dec["hold"] is True and held is None:
            if st["filled"].get(s) == key:
                out.append(desk._event("DEMO_DECISION", {**base, "action": "FLAT", "result": "this month's entry "
                                                         "was filled and has closed (its stop): flat until the next "
                                                         "month-end decision"}))
                continue
            out.append(desk._event("DEMO_DECISION", {**base, "action": "BUY", **_enter(desk, st, s, b, now, key,
                                                                                        dec, day_id)}))
        elif dec["hold"] is not True and held is not None:
            ct = desk.ex.close_position(held.id, "RULE")
            out.append(desk._event("DEMO_DECISION", {**base, "action": "SELL",
                                                     "result": "CLOSED" if ct is not None else "NOT_CLOSED",
                                                     "exit": getattr(ct, "exit", None), "pnl": getattr(ct, "pnl", None)},
                                   ref=held.id))
        else:
            out.append(desk._event("DEMO_DECISION", {**base, "action": "HOLD" if held is not None else "FLAT"}))
    out += desk._book_closures(st)
    for s, p in desk._held().items():
        b = last.get(s)
        if b is None or s not in INDICES:
            continue
        stop = round(b.close * (1 - STOP_REL), 2)
        if p.stop is not None and abs(stop - p.stop) < 0.005:
            continue
        res = desk.ex.modify_stop(p.id, stop, f"one-day stop: {STOP_REL:.0%} below the {b.day} close {b.close}")
        out.append(desk._event("DEMO_STOP", {"symbol": s, "close_day": str(b.day), "from": p.stop, "to": stop,
                                             "status": res["status"], "detail": res["detail"], "held": res["stop"]},
                               ref=p.id))
    st["runs"] = int(st.get("runs") or 0) + 1
    st["last_run"] = now
    desk.db.set_kv(STATE_KEY, st, reason="demo desk: a run")
    return out


def _enter(desk: TrendDesk, st: dict, s: str, b: DailyBar, now: int, key: str, dec: dict, day_id: str) -> dict:
    """One entry attempt: today's decision id, so a refusal that never happened can be decided again tomorrow, and a
    fill is recorded so the month is not entered twice."""
    evidence = ({"rule_id": RULE_ID, "for_month": key, "month_end": dec["month_end"],
                 "month_end_close": dec["month_end_close"], "mean_of_ten": dec["mean_of_ten"]},)
    stop = round(b.close * (1 - STOP_REL), 2)
    base = RuleDecision(f"{RULE_ID}:{s}:{key}:BUY:{day_id}", "BUY", s, now, stop, evidence)
    decision = replace(base, edge_status=classify(base, "trend_desk", desk.rules))
    try:
        spec, quote = desk.broker.spec(s), desk.broker.quote(s)
    except BrokerError as e:
        return {"decision_id": decision.id, "result": "NO_MARKET_DATA", "detail": str(e)}
    verdict = desk.risk.evaluate(decision, desk._account_state(st), spec, quote, now,
                                 executed_ids=desk.ex.executed_ids(), swap_per_night=0.0)
    out = {"decision_id": decision.id, "edge_status": decision.edge_status, "stop": stop,
           "risk": {"approved": verdict.approved, "qty": verdict.qty, "risk_amount": verdict.risk_amount,
                    "risk_pct": verdict.risk_pct, "reasons": verdict.reasons}}
    if not verdict.approved:
        return {**out, "result": "RISK_REJECTED"}
    res = desk.ex.execute(decision, verdict, meta={"swap_per_night": 0.0, "rule": RULE_ID})
    if res.status == "FILLED":
        st["filled"][s] = key
    return {**out, "result": res.status, "detail": res.detail, "position": res.position_id, "fill": res.fill_price}
