"""The forward evidence ledger: every trade proposal, executed or not, followed to its outcome.

Historical research found no deployable edge, so evidence can only come forward, on prices no one
had seen when the decision was made. This ledger is that evidence:

RECORD. Every BUY/SELL proposal is written at decision time to the immutable `forward_proposals`
table: levels, holding time, edge status, route (EXECUTE / SHADOW), the risk verdict, the model
and its stated confidence, the regime, the timeframes read, the estimated cost, and its PARTITION.
Rejected and shadow proposals are recorded exactly like executed ones: learning whether the risk
engine or the shadow rule cost good trades needs both.

RESOLVE. A proposal is resolved by walking COMPLETED bars that opened at or after the decision
time, the finest timeframe the feed can supply for the span: stop before target in the same bar,
a gap through the stop fills at the open, a target fills at its price, never better; a time exit
at the close. Nothing is known before the bar that reveals it has closed. Resolution reads the
feed, so it is restart-safe by construction: an unresolved proposal is simply walked again.
After the exit the path is followed to the end of the holding window, so a stop that was "too
tight" (the target was reached later) can be told from a wrong direction.

COSTS are separated exactly: gross R - cost R = net R, where cost = the spread at the decision,
slippage on each market fill, and commission, all over the planned risk (entry to stop).

PARTITIONS. Each decision belongs, by its decision time, to LEARNING or EVALUATION in alternating
calendar-week blocks (every third ISO week is EVALUATION). Lessons and the model's memory read
LEARNING outcomes only; forward eligibility is judged on EVALUATION outcomes only. A whole week
per block keeps neighbouring, correlated decisions on the same side of the split.

Nothing here sizes, approves or sends anything. A missing price is "not resolved yet", never a
guess; after 30 days without data the outcome is recorded UNRESOLVED with no R.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import numpy as np

FORWARD_VERSION = "forward-1.0.0"
EVALUATION_WEEK_MOD = 3  # ISO week % 3 == 2 -> EVALUATION
PERIODS = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}
MAX_BARS = 1500
DEFAULT_HOLD_S = 48 * 3600
MAX_HOLD_S = 14 * 86400
POST_WINDOW_MAX_S = 2 * 86400
EXPIRE_S = 30 * 86400


def partition(t: int) -> str:
    """LEARNING or EVALUATION, fixed by the decision time alone (never by its outcome)."""
    week = datetime.fromtimestamp(int(t), timezone.utc).isocalendar()[1]
    return "EVALUATION" if week % EVALUATION_WEEK_MOD == 2 else "LEARNING"


def session_of(t: int) -> str:
    h = datetime.fromtimestamp(int(t), timezone.utc).hour
    return "ASIA" if h < 7 else "LONDON" if h < 12 else "OVERLAP" if h < 16 else "NEW_YORK" if h < 21 else "LATE"


@dataclass(frozen=True)
class Costs:
    """Declared approximations for what bid/ask bars do not contain (the same model as research labels)."""
    slippage_pips: float = 0.1
    commission_pips_rt: float = 0.7


def proposal(decision, *, t: int, bid: float | None, ask: float | None, atr: float | None, pip: float,
             costs: Costs, route: str, risk: dict | None, executed: bool | None) -> dict | None:
    """The record of one BUY/SELL proposal at decision time, or None if it carries no levels."""
    if decision.decision not in ("BUY", "SELL") or decision.stop_loss is None or decision.take_profit is None:
        return None
    side = 1 if decision.decision == "BUY" else -1
    entry = (ask if side > 0 else bid) if (bid is not None and ask is not None) else decision.entry
    if entry is None:
        return None
    risk_px = abs(entry - decision.stop_loss)
    spread = (ask - bid) if (bid is not None and ask is not None) else None
    hold = None
    if decision.max_hold_minutes:
        hold = int(decision.max_hold_minutes) * 60
    elif decision.max_hold_hours:
        hold = int(decision.max_hold_hours) * 3600
    hold = min(hold or DEFAULT_HOLD_S, MAX_HOLD_S)
    ai = decision.ai or {}
    view = ai.get("view") or {}
    return {
        "decision_id": decision.id, "symbol": decision.instrument, "t": int(t), "side": side,
        "entry": float(entry), "stop": float(decision.stop_loss), "target": float(decision.take_profit),
        "hold_s": hold, "risk_px": risk_px, "spread": spread, "pip": pip, "atr": atr,
        "stop_atr": (risk_px / atr) if atr else None,
        "reward_risk": (abs(decision.take_profit - entry) / risk_px) if risk_px else None,
        "slippage_px": costs.slippage_pips * pip, "commission_px": costs.commission_pips_rt * pip,
        "family": decision.family, "signal_class": decision.signal_class, "edge_status": decision.edge_status,
        "route": route, "risk_approved": None if risk is None else bool(risk.get("approved")),
        "risk_reasons": [] if risk is None else list(risk.get("reasons") or [])[:5],
        "executed": executed, "timeframe": decision.timeframe, "timeframes": decision.timeframes,
        "regime": (decision.regime or {}).get("label"), "vol_state": (decision.regime or {}).get("vol_state"),
        "session": session_of(t), "partition": partition(t),
        "provider": ai.get("provider"), "model": ai.get("model"), "ai_verdict": decision.ai_verdict,
        "confidence": view.get("confidence"), "expected_r_model": view.get("expected_r"),
        "expected_r": decision.expected_R, "method": view.get("method"),
        "cost_estimate": decision.cost_estimate, "version": FORWARD_VERSION,
    }


def walk(p: dict, bars, now: int) -> dict | None:
    """The outcome of proposal `p` on `bars` (completed bars, oldest first) as known at `now`, or None.

    Pure: the same proposal and bars always give the same outcome."""
    side, entry, stop, target = p["side"], p["entry"], p["stop"], p["target"]
    risk = p["risk_px"]
    if not risk or risk <= 0:
        return None
    t0, hold = p["t"], p["hold_s"]
    slip, comm = p["slippage_px"], p["commission_px"]
    fill = entry + side * slip
    end = t0 + hold
    post_end = min(end, t0 + POST_WINDOW_MAX_S) if hold > POST_WINDOW_MAX_S else end
    ot, at = bars.open_time, bars.available_at
    keep = (ot >= t0) & (at <= now)
    idx = np.nonzero(keep)[0]
    best = worst = 0.0
    t_best = t_worst = None
    exit_px = reason = exit_t = None
    post_best = None
    target_after = False
    last_seen = None
    for i in idx:
        if side > 0:
            lo, hi, op, cl = bars.bid_low[i], bars.bid_high[i], bars.bid_open[i], bars.bid_close[i]
            fav, adv = (hi - fill) / risk, (lo - fill) / risk
        else:
            lo, hi, op, cl = bars.ask_low[i], bars.ask_high[i], bars.ask_open[i], bars.ask_close[i]
            fav, adv = (fill - lo) / risk, (fill - hi) / risk
        last_seen = int(at[i])
        if exit_px is None:
            if fav > best:
                best, t_best = float(fav), int(at[i])
            if adv < worst:
                worst, t_worst = float(adv), int(at[i])
            stop_hit = lo <= stop if side > 0 else hi >= stop
            tgt_hit = hi >= target if side > 0 else lo <= target
            if stop_hit:
                exit_px = (min(op, stop) - slip) if side > 0 else (max(op, stop) + slip)
                reason = "STOP"
            elif tgt_hit:
                exit_px, reason = target, "TARGET"
            elif int(at[i]) >= end:
                exit_px, reason = cl - side * slip, "TIME"
            if exit_px is not None:
                exit_t = int(at[i])
                continue
        else:  # after the exit: the rest of the holding window, for the post-mortem only
            if int(ot[i]) >= post_end:
                break
            post_best = fav if post_best is None else max(post_best, fav)
            if (hi >= target) if side > 0 else (lo <= target):
                target_after = True
    if exit_px is None:
        return None
    if exit_t < post_end and (last_seen is None or last_seen < post_end) and now < post_end + 86400:
        return None  # the post-exit window is not complete yet: wait for it (outcome itself is fixed)
    slip_exit = 0.0 if reason == "TARGET" else slip
    spread = p["spread"] if p["spread"] is not None else 0.0
    net = ((exit_px - fill) * side - comm) / risk
    cost = (spread + slip + slip_exit + comm) / risk
    return {"decision_id": p["decision_id"], "status": "RESOLVED", "reason": reason, "exit": float(exit_px),
            "exit_time": exit_t, "resolved_at": exit_t, "net_r": round(float(net), 6),
            "cost_r": round(float(cost), 6), "gross_r": round(float(net + cost), 6),
            "win": bool(net > 0), "mfe_r": round(best, 4), "mae_r": round(worst, 4),
            "mfe_first": (t_best is not None and (t_worst is None or t_best <= t_worst)),
            "t_mfe": t_best, "t_mae": t_worst, "held_s": exit_t - t0,
            "post_exit_best_r": None if post_best is None else round(float(post_best), 4),
            "target_after_exit": target_after, "partition": p["partition"], "version": FORWARD_VERSION}


class ForwardLedger:
    def __init__(self, db, clock: Callable[[], int]) -> None:
        self.db, self.clock = db, clock
        self.stats = {"recorded": 0, "resolved": 0, "unresolved": 0, "last_error": None}

    def record(self, rec: dict | None) -> bool:
        if rec is None:
            return False
        with self.db.tx() as c:
            if c.execute("SELECT 1 FROM forward_proposals WHERE decision_id=?", (rec["decision_id"],)).fetchone():
                return False  # the same decision seen again after a restart
            self.db.append("forward_proposals", {"decision_id": rec["decision_id"], "symbol": rec["symbol"],
                                                 "t": rec["t"], "partition": rec["partition"], "payload": rec}, conn=c)
        self.stats["recorded"] += 1
        return True

    def pending(self, limit: int = 50) -> list[dict]:
        rows = self.db.query("SELECT p.payload FROM forward_proposals p LEFT JOIN forward_outcomes o "
                             "ON o.decision_id = p.decision_id WHERE o.decision_id IS NULL ORDER BY p.seq LIMIT ?",
                             (limit,))
        return [json.loads(r["payload"]) for r in rows]

    @staticmethod
    def _bars(feed, symbol: str, t0: int, until: int, now: int):
        """The finest completed bars covering t0..until, or None."""
        span = max(0, min(until, now) - t0)
        for tf, per in PERIODS.items():
            n = span // per + 3
            if n > MAX_BARS:
                continue
            try:
                b = feed.bars_tf(symbol, tf, now, int(n)) if hasattr(feed, "bars_tf") else (
                    feed.bars(symbol, now, int(n)) if tf == "H1" else None)
            except Exception:
                b = None
            if b is None or len(b) == 0:
                continue
            if int(b.open_time[0]) <= t0 + per:  # the series reaches back to the decision
                return tf, b
        return None, None

    def resolve(self, feed, now: int | None = None, limit: int = 20) -> list[dict]:
        now = int(self.clock() if now is None else now)
        done = []
        for p in self.pending(limit):
            until = p["t"] + p["hold_s"] + POST_WINDOW_MAX_S
            tf, bars = self._bars(feed, p["symbol"], p["t"], until, now)
            out = walk(p, bars, now) if bars is not None else None
            if out is None and now - p["t"] > EXPIRE_S:
                out = {"decision_id": p["decision_id"], "status": "UNRESOLVED", "reason": "NO_DATA",
                       "resolved_at": now, "net_r": None, "gross_r": None, "cost_r": None, "win": None,
                       "partition": p["partition"], "version": FORWARD_VERSION,
                       "note": "no completed bars covered the holding window within 30 days: no R is invented"}
            if out is None:
                continue
            out["resolution_timeframe"] = tf
            with self.db.tx() as c:
                if c.execute("SELECT 1 FROM forward_outcomes WHERE decision_id=?", (p["decision_id"],)).fetchone():
                    continue
                self.db.append("forward_outcomes", {"decision_id": p["decision_id"], "resolved_at": out["resolved_at"],
                                                    "partition": p["partition"], "payload": out}, conn=c)
            self.stats["resolved" if out["status"] == "RESOLVED" else "unresolved"] += 1
            done.append(out)
        return done

    def rows(self, as_of: int | None = None, partition_: str | None = None) -> list[dict]:
        """Proposals joined to their outcomes, each outcome only if it had resolved by `as_of`."""
        q = ("SELECT p.payload AS p, o.payload AS o, o.resolved_at AS ra FROM forward_proposals p "
             "LEFT JOIN forward_outcomes o ON o.decision_id = p.decision_id")
        args: tuple = ()
        if partition_:
            q += " WHERE p.partition=?"
            args = (partition_,)
        out = []
        for r in self.db.query(q + " ORDER BY p.seq", args):
            p = json.loads(r["p"])
            o = json.loads(r["o"]) if r["o"] and (as_of is None or (r["ra"] is not None and r["ra"] <= as_of)) else None
            out.append({**p, "outcome": o})
        return out


def finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
