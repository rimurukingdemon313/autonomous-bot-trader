"""The trend desk: TRND-1, traded by the system itself, on its own paper account (docs/TREND_DESK.md).

The rule (research/preregistrations/TRND-1.md; PASSED, and VALIDATED on its holdout): hold an index for the next
month if its month-end close is above the mean of its last ten month-end closes, that one included; otherwise hold
nothing. Long or flat, never short. A month whose ten month-ends are not all there is not decided: flat.

What the desk adds to the rule, each one declared, none of them tested by TRND-1 itself:
- FUNDED-P's one-day stop (its HALF track): a stop 6% below each close, moved after every close. After it is hit, the
  index stays flat until the next month-end decision;
- the switch happens at the close of the month's last weekday. When that day has no close (an exchange holiday), at
  the next close, one trading day late;
- the size is the risk engine's, never the desk's: at most $1,500 lost at the stop, all costs included (about $25,000
  of each index, half the account across the four);
- each session's intraday low is observed before its close, so a fall inside the day counts against the daily limit
  even when the close recovered;
- if the run fails (the gate locks it at a limit, as a firm fails an account), every position is closed at that close
  and nothing more is opened.

What it never does: size a trade, approve one, send an order without the hard gate's permit, move a stop without one,
trade a rule nobody promoted, or read a bar after the one it is at. At a close it reads only bars that closed at or
before it, and a month's decision reads only the months before it.
"""

from __future__ import annotations

import json
import math
from bisect import bisect_right
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ..broker.base import BrokerError
from ..broker.paper import PaperBroker
from ..data.instruments import INDEX_CFDS
from ..decision.edge_status import classify
from ..execution.engine import ExecutionEngine
from ..memory.db import Database
from ..risk.engine import AccountState, Quote, RiskEngine, RiskLimits
from ..risk.hard_gate import HardRiskGate
from ..risk.profile import TRND1_PAPER_200K, HardRiskProfile

TREND_DESK_VERSION = "trend-desk-1.0.0"
RULE_ID = "TRND-1"
INDICES = ("US500", "NAS100", "GER40", "UK100")
MONTHS = 10
#: the one-day stop: 6% below each close (FUNDED-P's HALF track)
STOP_REL = 0.06
PROMOTED_RULES_PATH = Path(__file__).resolve().parents[2] / "models" / "artifacts" / "promoted_rules.json"
#: The desk's own limits for the risk engine. Its funded-account limits are the hard profile's (TRND1-PAPER-200K):
#: $1,500 per position at its stop, $8,000 open, $10,000 a day, $20,000 in all. The engine's own: 0.75% per trade (a
#: VALIDATED rule only; anything else stays at 0.25%), 4% open, 5% a day, no weekly limit tighter than the account's
#: maximum loss, a 10% fall from the equity peak halts it, four positions, one per index, at most 1x exposure.
DESK_LIMITS = RiskLimits(risk_per_trade_pct=0.75, daily_loss_limit_pct=5.0, weekly_loss_limit_pct=10.0,
                         max_open_risk_pct=4.0, max_drawdown_pct=10.0, max_open_positions=4,
                         max_positions_per_currency=4, max_leverage=1.0, max_quote_age_s=30, hard=TRND1_PAPER_200K)
STATE_KEY = "trend_desk"
#: a conversion rate from a day's close is used from the next 00:00 UTC on, never on the day itself
FX_SPREAD = 0.0001


# ── the promoted rule ───────────────────────────────────────────────────────

class RuleFileError(ValueError):
    pass


@dataclass(frozen=True)
class PromotedRule:
    """A rule a person promoted for the desk to trade. It never carries a size: sizing is the risk engine's."""

    rule_id: str
    status: str  # VALIDATED | PROMISING | RETIRED
    health: str  # HEALTHY | DEGRADED | RETIRED
    instruments: tuple[str, ...]
    mode: str  # PAPER: where it may trade
    promoted_by: str
    promoted_on: str
    evidence: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: dict) -> "PromotedRule":
        for k in ("rule_id", "status", "health", "instruments", "mode", "promoted_by", "promoted_on", "evidence"):
            if k not in d:
                raise RuleFileError(f"promoted rule missing {k!r}")
        for k in ("size", "lots", "units", "notional", "risk_pct", "risk_amount", "leverage"):
            if k in d:
                raise RuleFileError(f"{d['rule_id']}: a rule never carries {k!r}; sizing is the risk engine's")
        if d["status"] not in ("VALIDATED", "PROMISING", "RETIRED") or d["health"] not in ("HEALTHY", "DEGRADED",
                                                                                          "RETIRED"):
            raise RuleFileError(f"{d['rule_id']}: unknown status {d['status']!r} or health {d['health']!r}")
        if d["mode"] != "PAPER":
            raise RuleFileError(f"{d['rule_id']}: mode {d['mode']!r}; this build trades PAPER only")
        unknown = [s for s in d["instruments"] if s not in INDEX_CFDS]
        if unknown:
            raise RuleFileError(f"{d['rule_id']}: unknown instruments {unknown}")
        return cls(d["rule_id"], d["status"], d["health"], tuple(d["instruments"]), d["mode"], d["promoted_by"],
                   d["promoted_on"], dict(d["evidence"]))


def load_promoted_rules(path: Path | str = PROMOTED_RULES_PATH) -> tuple[list[PromotedRule], str]:
    """(rules, note). A missing file means nothing was promoted. A malformed one is an error, never a default."""
    p = Path(path)
    if not p.exists():
        return [], "no promoted rule: models/artifacts/promoted_rules.json is absent"
    raw = json.loads(p.read_text())
    rules = [PromotedRule.from_json(r) for r in raw.get("rules", [])]
    return rules, f"{len(rules)} promoted rule(s)"


# ── the rule ────────────────────────────────────────────────────────────────

def month_ends(closes: dict[date, float]) -> list[tuple[date, float]]:
    """Each calendar month's last close, in order."""
    last: dict = {}
    for d in sorted(closes):
        last[(d.year, d.month)] = (d, closes[d])
    return [last[k] for k in sorted(last)]


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def next_month(ym: tuple[int, int]) -> tuple[int, int]:
    return (ym[0] + (ym[1] == 12), ym[1] % 12 + 1)


def decision_for(closes: dict[date, float], month: tuple[int, int]) -> dict:
    """TRND-1's decision for `month` (year, month), from the closes before it only: hold if the last month-end close
    is above the mean of the ten month-end closes ending with it; None (flat) when those ten are not ten consecutive
    calendar months. Ask for a month only once the month before it has ended."""
    first = date(month[0], month[1], 1)
    ends = month_ends({d: c for d, c in closes.items() if d < first})
    out = {"month": f"{month[0]:04d}-{month[1]:02d}", "hold": None, "month_end": None, "month_end_close": None,
           "mean_of_ten": None}
    if len(ends) < MONTHS:
        return {**out, "why": f"{len(ends)} month-end closes before {out['month']}, {MONTHS} needed: flat"}
    window = ends[-MONTHS:]
    if _months_between(window[0][0], first) != MONTHS:
        return {**out, "why": f"the ten month-ends before {out['month']} are not ten consecutive months: flat"}
    mean = sum(c for _, c in window) / MONTHS
    d, c = window[-1]
    hold = c > mean
    return {**out, "hold": hold, "month_end": str(d), "month_end_close": c, "mean_of_ten": mean,
            "why": f"the {d} close {c:.2f} is {'above' if hold else 'not above'} the ten-month mean {mean:.2f}"}


def is_last_weekday(d: date) -> bool:
    """The month's last weekday: when the next month's decision is taken, at the close."""
    nxt = d + timedelta(days=3 if d.weekday() == 4 else 2 if d.weekday() == 5 else 1)
    return nxt.month != d.month


# ── market data, as of the desk's clock ─────────────────────────────────────

@dataclass(frozen=True)
class DailyBar:
    day: date
    open: float
    high: float
    low: float
    close: float

    def problems(self) -> list[str]:
        vals = (self.open, self.high, self.low, self.close)
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0
                   for v in vals):
            return [f"{self.day}: a price is missing, not finite or not positive ({vals})"]
        if self.low > min(self.open, self.close) + 1e-9 or self.high < max(self.open, self.close) - 1e-9:
            return [f"{self.day}: low {self.low} / high {self.high} do not contain open {self.open} and close "
                    f"{self.close}"]
        return []


def _local(symbol: str, day: date, hm: tuple[int, int]) -> int:
    inst = INDEX_CFDS[symbol]
    return int(datetime(day.year, day.month, day.day, hm[0], hm[1], tzinfo=ZoneInfo(inst.exchange_tz)).timestamp())


def close_time(symbol: str, day: date) -> int:
    return _local(symbol, day, INDEX_CFDS[symbol].close_local)


def open_time(symbol: str, day: date) -> int:
    return _local(symbol, day, INDEX_CFDS[symbol].open_local)


def rate_from(day: date) -> int:
    """A conversion rate's daily close counts from the next 00:00 UTC."""
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp()) + 86400


class DailyFeed:
    """Quotes from final daily bars, as of a time: each index at its latest close at or before it (with its declared
    spread), each conversion rate at its latest daily close available then. Nothing after the time is returned."""

    def __init__(self, bars: dict[str, list[DailyBar]], rates: dict[str, dict[date, float]]) -> None:
        self._idx = {}
        for s, bs in bars.items():
            bs = sorted(bs, key=lambda b: b.day)
            self._idx[s] = ([close_time(s, b.day) for b in bs], bs)
        self._fx = {}
        for pair, series in rates.items():
            rows = sorted((rate_from(d), c) for d, c in series.items())
            self._fx[pair] = ([t for t, _ in rows], [c for _, c in rows])
        self._override: dict[str, tuple[float, int]] = {}

    def at_low(self, prices: dict[str, float], t: int) -> None:
        """Quote these indices at these prices from `t` (an intraday low), until cleared."""
        self._override = {s: (p, t) for s, p in prices.items()}

    def clear(self) -> None:
        self._override = {}

    def quote(self, symbol: str, now: int | None = None) -> Quote | None:
        now = int(now if now is not None else 2 ** 62)
        if symbol in self._override and self._override[symbol][1] <= now:
            price, t = self._override[symbol]
            half = INDEX_CFDS[symbol].spread / 2
            return Quote(symbol, price - half, price + half, t)
        if symbol in self._idx:
            times, bs = self._idx[symbol]
            i = bisect_right(times, now) - 1
            if i < 0:
                return None
            half = INDEX_CFDS[symbol].spread / 2
            return Quote(symbol, bs[i].close - half, bs[i].close + half, times[i])
        if symbol in self._fx:
            times, closes = self._fx[symbol]
            i = bisect_right(times, now) - 1
            if i < 0:
                return None
            return Quote(symbol, closes[i] - FX_SPREAD / 2, closes[i] + FX_SPREAD / 2, times[i])
        return None

    def closes(self, symbol: str, now: int) -> dict[date, float]:
        """Every close of `symbol` at or before `now`."""
        times, bs = self._idx.get(symbol, ([], []))
        return {b.day: b.close for t, b in zip(times, bs) if t <= now}


class DeskClock:
    def __init__(self, t: int) -> None:
        self.t = int(t)

    def __call__(self) -> int:
        return self.t


# ── the desk ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RuleDecision:
    """One entry the rule asks for. Only these fields reach the risk engine and the execution engine."""

    id: str
    decision: str  # BUY: the rule is long or flat
    instrument: str
    timestamp: int
    stop_loss: float
    supporting_evidence: tuple = ()
    take_profit: None = None  # a rule exit: its next decision or its stop closes it
    exit_kind: str = "RULE"
    signal_class: str = "TREND"
    family: str = RULE_ID
    edge_status: str = "NONE"
    confidence: None = None
    probability: None = None
    expected_R: None = None
    ai: None = None


@dataclass
class TrendDesk:
    db: Database
    feed: DailyFeed
    clock: DeskClock
    gate: HardRiskGate
    broker: PaperBroker
    ex: ExecutionEngine
    risk: RiskEngine
    rules: list[PromotedRule]
    rules_note: str = ""

    @classmethod
    def build(cls, db: Database, feed: DailyFeed, clock: DeskClock, rules: list[PromotedRule], rules_note: str = "",
              profile: HardRiskProfile = TRND1_PAPER_200K, limits: RiskLimits = DESK_LIMITS) -> "TrendDesk":
        if db.get_kv("kill_switch") is None:
            db.set_kv("kill_switch", {"active": False}, reason="trend desk: a new account")
        gate = HardRiskGate(db, profile, clock)
        broker = PaperBroker(feed, clock, db, start_balance=profile.starting_balance, currency=profile.currency,
                             gate=gate)
        # Only a VALIDATED decision executes: an unpromoted rule is refused before the broker, never traded smaller.
        ex = ExecutionEngine(db, broker, clock, gate=gate, allow_unvalidated=False)
        return cls(db, feed, clock, gate, broker, ex, RiskEngine(limits), rules, rules_note)

    # ── state ──

    def state(self) -> dict:
        st = self.db.get_kv(STATE_KEY, None)
        return st if isinstance(st, dict) else {"version": TREND_DESK_VERSION, "applied": {}, "last_session": None,
                                                "week": None, "peak": None, "closed_r": [], "failed": None}

    def _save(self, st: dict, reason: str) -> None:
        self.db.set_kv(STATE_KEY, st, reason=reason)

    def _event(self, kind: str, payload: dict, ref: str | None = None) -> dict:
        from ..version import stamp  # late: the version module imports every component, this one included
        row = {"t": self.clock(), "version": TREND_DESK_VERSION, "rule": RULE_ID, **payload, "versions": stamp()}
        self.db.event(kind, row, ref=ref)
        return {"kind": kind, **row}

    def _held(self) -> dict:
        return {p.symbol: p for p in self.broker.positions()}

    def _account_state(self, st: dict) -> AccountState:
        try:
            snap = self.broker.account()
            equity, balance = snap.equity, snap.balance
        except BrokerError:
            equity = balance = None
        positions = []
        try:
            for p in self.broker.positions():
                spec, q = self.broker.spec(p.symbol), self.broker.quote(p.symbol)
                if spec is None or q is None:
                    positions.append({"symbol": p.symbol, "side": p.side, "qty": p.qty, "notional": float("inf"),
                                      "risk_amount": None})
                    continue
                units = p.qty * spec.contract_size * spec.value_per_price_unit
                px = q.bid if p.side > 0 else q.ask
                positions.append({"symbol": p.symbol, "side": p.side, "qty": p.qty, "notional": units * px,
                                  "risk_amount": max(0.0, (px - p.stop) * p.side) * units})
        except BrokerError:
            positions = None
        day = (self.gate.status().get("day") or {})
        ks = self.db.get_kv("kill_switch", None)
        kill = None if not isinstance(ks, dict) or "active" not in ks else bool(ks["active"])
        return AccountState(equity=equity, balance=balance, day_start_equity=day.get("reference"),
                            peak_equity=st.get("peak"), start_balance=self.gate.profile.starting_balance,
                            open_positions=positions if positions is not None else [],
                            week_start_equity=(st.get("week") or {}).get("equity"),
                            closed_r=list(st.get("closed_r") or [])[-30:],
                            kill_switch=kill if positions is not None else None,
                            paused=bool(self.db.get_kv("paused", False)), halted=bool(self.db.get_kv("halted", False)))

    def _mark(self, st: dict, t: int) -> None:
        """The week's opening equity and the equity peak, from the account as it stands."""
        try:
            eq = self.broker.account().equity
        except BrokerError:
            return
        week = int((t // 86400 - 4) // 7)  # ISO weeks: day 4 of the epoch is a Monday
        if not st.get("week") or st["week"].get("id") != week:
            st["week"] = {"id": week, "equity": eq}
        st["peak"] = eq if st.get("peak") is None else max(st["peak"], eq)

    # ── one session: the indices that close at one moment ──

    def session(self, day: date, bars: dict[str, DailyBar]) -> list[dict]:
        """The close of `day` for these indices, which all close at the same moment. In order: their stops against
        the day's range; the account at their intraday lows, then at their closes; closed trades; the rule's
        decisions; the stops moved to 6% below the closes. Returns what happened."""
        symbols = sorted(bars, key=INDICES.index)
        t = close_time(symbols[0], day)
        if any(close_time(s, day) != t for s in symbols):
            raise ValueError(f"{symbols} do not close at the same moment on {day}")
        st = self.state()
        if st.get("last_session") is not None and t <= st["last_session"]:
            return []  # already done: a session is applied once
        out: list[dict] = []
        # 1. the day's range: each stop first (a gap through it fills at the open); then the account at the lows
        self.clock.t = max(self.clock.t, t - 60)
        for s in symbols:
            b = bars[s]
            half = INDEX_CFDS[s].spread / 2
            self.broker.on_bar(s, {"open_time": open_time(s, day), "close_time": t,
                                   "bid_open": b.open - half, "bid_high": b.high - half, "bid_low": b.low - half,
                                   "ask_open": b.open + half, "ask_high": b.high + half, "ask_low": b.low + half})
        self.feed.at_low({s: bars[s].low for s in symbols}, self.clock.t)
        try:
            low = self.gate.observe(self.broker)
        finally:
            self.feed.clear()
        out.append(self._event("DESK_INTRADAY_LOW", {"day": str(day), "symbols": symbols,
                                                     "lows": {s: bars[s].low for s in symbols},
                                                     "equity": low.get("equity_conservative"),
                                                     "risk_status": low.get("risk_status")}))
        # 2. the close
        self.clock.t = t
        status = self.gate.observe(self.broker)
        out += self._book_closures(st)
        self._mark(st, t)
        if status.get("state") == "LOCKED" and not st.get("failed"):
            st["failed"] = {"day": str(day), "t": t, "lock": status.get("lock")}
            out.append(self._event("DESK_ACCOUNT_FAILED", {"day": str(day), "lock": status.get("lock")}))
        if st.get("failed"):
            for s, p in self._held().items():  # a failed account is closed, as the firm would close it
                ct = self.ex.close_position(p.id, "FAILED")
                out.append(self._event("DESK_EXIT", {"symbol": s, "day": str(day), "why": "the account failed",
                                                     "closed": ct is not None}, ref=p.id))
            out += self._book_closures(st)
            st["last_session"] = t
            self._save(st, f"trend desk: {day} session (failed account)")
            return out
        # 3. the rule, and what its exits closed
        for s in symbols:
            out += self._decide(st, s, day, bars[s], t)
        out += self._book_closures(st)
        # 4. the one-day stops
        held = self._held()
        for s in symbols:
            p = held.get(s)
            if p is None:
                continue
            stop = round(bars[s].close * (1 - STOP_REL), 2)
            if p.stop is not None and abs(stop - p.stop) < 0.005:
                continue
            res = self.ex.modify_stop(p.id, stop, f"one-day stop: {STOP_REL:.0%} below the {day} close {bars[s].close}")
            out.append(self._event("DESK_STOP", {"symbol": s, "day": str(day), "from": p.stop, "to": stop,
                                                 "status": res["status"], "detail": res["detail"],
                                                 "held": res["stop"]}, ref=p.id))
        st["last_session"] = t
        self._save(st, f"trend desk: {day} session")
        return out

    def _book_closures(self, st: dict) -> list[dict]:
        """Positions the broker has closed (a stop, a rule exit, a failed account) are booked, with their R."""
        out = []
        for row, ct in self.ex.sync_closures():
            risk = (json.loads(row.get("payload") or "{}") or {}).get("risk_amount")
            r = (ct.pnl / risk) if (ct.pnl is not None and risk) else None
            st["closed_r"] = (list(st.get("closed_r") or []) + [r])[-200:]
            out.append(self._event("DESK_TRADE_CLOSED", {"position": row["id"], "symbol": ct.symbol,
                                                         "entry": ct.entry, "exit": ct.exit, "qty": ct.qty,
                                                         "opened": ct.opened, "closed": ct.closed, "reason": ct.reason,
                                                         "pnl": ct.pnl, "r": r, "commission": ct.commission,
                                                         "slippage_cost": ct.slippage_cost,
                                                         "spread_cost": ct.spread_cost}, ref=row["id"]))
        return out

    def _decide(self, st: dict, s: str, day: date, bar: DailyBar, t: int) -> list[dict]:
        month = (day.year, day.month)
        target = next_month(month) if is_last_weekday(day) else month
        key = f"{target[0]:04d}-{target[1]:02d}"
        if st["applied"].get(s) == key:
            return []
        dec = decision_for(self.feed.closes(s, t), target)
        held = self._held().get(s)
        late = target == month and st["applied"].get(s) is not None
        base = {"symbol": s, "day": str(day), "for_month": key, **{k: dec[k] for k in
                ("hold", "month_end", "month_end_close", "mean_of_ten", "why")}, "close": bar.close,
                "held_before": held is not None, "late": late}
        if dec["hold"] is True and held is None:
            ev = self._enter(st, s, bar, t, key, dec)
            st["applied"][s] = key
            return [self._event("DESK_DECISION", {**base, "action": "BUY", **ev})]
        if dec["hold"] is not True and held is not None:
            ct = self.ex.close_position(held.id, "RULE")
            if ct is None:  # not closed: decided again at the next close, never retried in a loop
                return [self._event("DESK_DECISION", {**base, "action": "SELL", "result": "NOT_CLOSED"}, ref=held.id)]
            st["applied"][s] = key
            return [self._event("DESK_DECISION", {**base, "action": "SELL", "result": "CLOSED", "exit": ct.exit,
                                                  "pnl": ct.pnl}, ref=held.id)]
        st["applied"][s] = key
        return [self._event("DESK_DECISION", {**base, "action": "HOLD" if held is not None else "FLAT"})]

    def _enter(self, st: dict, s: str, bar: DailyBar, t: int, key: str, dec: dict) -> dict:
        evidence = ({"rule_id": RULE_ID, "for_month": key, "month_end": dec["month_end"],
                     "month_end_close": dec["month_end_close"], "mean_of_ten": dec["mean_of_ten"]},)
        stop = round(bar.close * (1 - STOP_REL), 2)
        base = RuleDecision(f"{RULE_ID}:{s}:{key}:BUY", "BUY", s, t, stop, evidence)
        decision = replace(base, edge_status=classify(base, "trend_desk", self.rules))
        verdict = self.risk.evaluate(decision, self._account_state(st), self.broker.spec(s), self.broker.quote(s), t,
                                     executed_ids=self.ex.executed_ids(), swap_per_night=0.0)
        out = {"decision_id": decision.id, "edge_status": decision.edge_status, "stop": stop,
               "risk": {"approved": verdict.approved, "qty": verdict.qty, "risk_amount": verdict.risk_amount,
                        "risk_pct": verdict.risk_pct, "reasons": verdict.reasons}}
        if not verdict.approved:
            return {**out, "result": "RISK_REJECTED"}
        res = self.ex.execute(decision, verdict, meta={"swap_per_night": 0.0, "rule": RULE_ID})
        return {**out, "result": res.status, "detail": res.detail, "position": res.position_id, "fill": res.fill_price}


def sessions(bars: dict[str, list[DailyBar]], after: int | None = None, until: int | None = None
             ) -> list[tuple[int, date, list[str]]]:
    """Every close with the indices closing at it, in time order: (time, day, symbols), strictly after `after` and at
    or before `until`."""
    groups: dict[tuple[int, date], list[str]] = {}
    for s, bs in bars.items():
        for b in bs:
            t = close_time(s, b.day)
            if (after is None or t > after) and (until is None or t <= until):
                groups.setdefault((t, b.day), []).append(s)
    return [(t, d, sorted(ss, key=INDICES.index)) for (t, d), ss in sorted(groups.items())]


__all__ = ["DESK_LIMITS", "INDICES", "MONTHS", "PROMOTED_RULES_PATH", "RULE_ID", "STOP_REL", "TREND_DESK_VERSION",
           "DailyBar", "DailyFeed", "DeskClock", "PromotedRule", "RuleDecision", "RuleFileError", "TrendDesk",
           "close_time", "decision_for", "is_last_weekday", "load_promoted_rules", "month_ends", "next_month",
           "open_time", "sessions"]
