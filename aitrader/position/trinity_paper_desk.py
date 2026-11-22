"""The TRINITY desk: the owner's TRINITY-MASTER on its own $200,000 paper account (docs/TRINITY.md).

PAPER ONLY. The owner asked for it on 2026-11-21 ("read CLAUDE_HANDOFF_SPEC.md and implement it fully in the
repository"). The rule is EXPERIMENTAL: a backtest its author chose on 288 three-weekly closes, never preregistered,
never judged on data its author had not seen (research/results/TRINITY-MASTER-redteam.json). So:

- it trades only on the paper broker: the desk refuses any other, and nothing here reaches DEMO or live;
- the risk engine sizes every position as it sizes any unvalidated decision: at most 0.25% of the starting balance
  lost at its stop, all costs included, whatever the package's weights say (CLAUDE.md rules 2 and 14);
- the package's weights at their own size are measured beside it as the design book (scripts/trinity_paper_desk.py):
  never traded, never added to the desk's figures.

What the desk does, from the package's own handoff spec:
- every 15th trading day from its anchor, at the US close: TRINITY-MASTER's weights (aitrader/position/trinity.py)
  from the closes of QQQ, SPY, GLD and DBC on that grid, with the VIX, TLT and UUP read at the trading day before
  (t-1). The weights' drawdown brake reads the design book's own drawdown, as in the package;
- an instrument whose weight is above 1e-4 is held: bought if flat, its stop moved to 3.2% below the close if held.
  One whose weight is not is closed;
- every position carries a stop 3.2% below its rebalance close. A stop hit leaves the instrument flat until the next
  rebalance; between rebalances nothing is moved;
- the instruments are the package's map: QQQ -> NAS100, SPY -> US500, GLD -> XAUUSD, DBC -> USOIL. On paper NAS100 and
  US500 are priced from the cash indices, XAUUSD from GLD and USOIL from USO, the last two each scaled once, at the
  desk's first close, to the level of its futures (scripts/trinity_paper_desk.py). A swap-free CFD earns the spot or
  rolled-futures return, and a continuous futures series jumps at every roll;
- each session's intraday lows are observed before its close, so a fall inside the day counts against the daily
  limit. If the account fails (the gate locks it at a limit), everything is closed and nothing more is opened.

What it never does: size a trade, approve one, send an order without the hard gate's permit, move a stop without
one, open a position for a rule nobody promoted for paper, or read a bar after the one it is at.
"""

from __future__ import annotations

import json
from bisect import bisect_right
from dataclasses import dataclass, replace
from datetime import date, datetime
from zoneinfo import ZoneInfo

from ..broker.base import BrokerError
from ..broker.paper import PaperBroker
from ..data.instruments import COMMODITY_CFDS, INDEX_CFDS
from ..decision.edge_status import classify
from ..execution.engine import ExecutionEngine
from ..memory.db import Database
from ..risk.engine import AccountState, Quote, RiskEngine, RiskLimits
from ..risk.hard_gate import HardRiskGate
from ..risk.profile import TRINITY_PAPER_200K, HardRiskProfile
from . import trinity as T
from .trend_desk import DailyBar, DeskClock, PromotedRule

TRINITY_DESK_VERSION = "trinity-desk-1.0.0"
RULE_ID = "TRINITY-MASTER"
INSTRUMENTS = ("NAS100", "US500", "XAUUSD", "USOIL")
SIGNAL_OF = {cfd: asset for asset, cfd in T.CFD_OF.items()}
#: where each paper CFD's daily bars come from, and the futures whose level the commodity proxies are scaled to
PRICE_SOURCE = {"NAS100": "^NDX", "US500": "^GSPC", "XAUUSD": "GLD", "USOIL": "USO"}
SCALE_TO = {"XAUUSD": "GC=F", "USOIL": "CL=F"}
#: declared typical CFD spreads in price units (the index CFDs' and USOIL's are the instrument tables' own)
SPREAD = {"NAS100": INDEX_CFDS["NAS100"].spread, "US500": INDEX_CFDS["US500"].spread, "XAUUSD": 0.35,
          "USOIL": COMMODITY_CFDS["USOIL"].spread}
#: every price source here is a US session: one session a day, at the New York close
TZ = ZoneInfo("America/New_York")
OPEN_LOCAL, CLOSE_LOCAL = (9, 30), (16, 0)
#: the first rebalance: the first weekday after the desk was built
START = date(2026, 11, 23)
#: the desk's own limits for the risk engine, the package's where it states one: 1.5% at the stop per position (the
#: engine caps an unvalidated rule at 0.25% whatever this says), 4% open, 5% a day, 10% in all from the starting
#: balance, four positions, one per instrument, at most 1x exposure, a fixed size (no halving after losing runs)
DESK_LIMITS = RiskLimits(risk_per_trade_pct=1.5, daily_loss_limit_pct=5.0, weekly_loss_limit_pct=10.0,
                         max_open_risk_pct=4.0, max_drawdown_pct=10.0, max_open_positions=4,
                         max_positions_per_currency=4, max_leverage=1.0, max_quote_age_s=30, loss_streak_step=0,
                         hard=TRINITY_PAPER_200K)
STATE_KEY = "trinity_desk"
#: the statuses under which the desk may open a position; RETIRED, or no promotion at all, opens nothing
OPENS_UNDER = ("VALIDATED", "PROMISING", "EXPERIMENTAL")


def close_time(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, *CLOSE_LOCAL, tzinfo=TZ).timestamp())


def open_time(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, *OPEN_LOCAL, tzinfo=TZ).timestamp())


class TrinityFeed:
    """Quotes from final daily bars, as of a time: each instrument at its latest close at or before it, with its
    declared spread. Nothing after the time is returned. The account is in USD and so is every instrument."""

    def __init__(self, bars: dict[str, list[DailyBar]]) -> None:
        self._idx = {}
        for s, bs in bars.items():
            if s not in SPREAD:
                raise ValueError(f"{s}: not an instrument of the TRINITY desk")
            bs = sorted(bs, key=lambda b: b.day)
            self._idx[s] = ([close_time(b.day) for b in bs], bs)
        self._override: dict[str, tuple[float, int]] = {}

    def at_low(self, prices: dict[str, float], t: int) -> None:
        self._override = {s: (p, t) for s, p in prices.items()}

    def clear(self) -> None:
        self._override = {}

    def quote(self, symbol: str, now: int | None = None) -> Quote | None:
        now = int(now if now is not None else 2 ** 62)
        if symbol not in self._idx:
            return None
        half = SPREAD[symbol] / 2
        if symbol in self._override and self._override[symbol][1] <= now:
            price, t = self._override[symbol]
            return Quote(symbol, price - half, price + half, t)
        times, bs = self._idx[symbol]
        i = bisect_right(times, now) - 1
        if i < 0:
            return None
        return Quote(symbol, bs[i].close - half, bs[i].close + half, times[i])


@dataclass(frozen=True)
class TrinityDecision:
    """One entry the rule asks for. Only these fields reach the risk engine and the execution engine."""

    id: str
    decision: str  # BUY: the rule is long or flat
    instrument: str
    timestamp: int
    stop_loss: float
    supporting_evidence: tuple = ()
    take_profit: None = None  # a rule exit: its next rebalance or its stop closes it
    exit_kind: str = "RULE"
    signal_class: str = "TREND"
    family: str = RULE_ID
    edge_status: str = "NONE"
    confidence: None = None
    probability: None = None
    expected_R: None = None
    ai: None = None


@dataclass
class TrinityPaperDesk:
    db: Database
    feed: TrinityFeed
    clock: DeskClock
    gate: HardRiskGate
    broker: PaperBroker
    ex: ExecutionEngine
    risk: RiskEngine
    rules: list[PromotedRule]
    rules_note: str = ""
    anchor: date = START

    def __post_init__(self) -> None:
        if not isinstance(self.broker, PaperBroker) or getattr(self.broker, "name", None) != "paper":
            raise ValueError("the TRINITY desk trades on the paper broker only: an unvalidated rule has no other")

    @classmethod
    def build(cls, db: Database, feed: TrinityFeed, clock: DeskClock, rules: list[PromotedRule], rules_note: str = "",
              anchor: date = START, profile: HardRiskProfile = TRINITY_PAPER_200K,
              limits: RiskLimits = DESK_LIMITS) -> "TrinityPaperDesk":
        if db.get_kv("kill_switch") is None:
            db.set_kv("kill_switch", {"active": False}, reason="trinity desk: a new account")
        gate = HardRiskGate(db, profile, clock)
        broker = PaperBroker(feed, clock, db, start_balance=profile.starting_balance, currency=profile.currency,
                             gate=gate)
        # An unvalidated rule executes on the paper broker only: the engine is built for that broker and no other.
        ex = ExecutionEngine(db, broker, clock, gate=gate, allow_unvalidated=True)
        return cls(db, feed, clock, gate, broker, ex, RiskEngine(limits), rules, rules_note, anchor)

    # ── state ──

    def state(self) -> dict:
        st = self.db.get_kv(STATE_KEY, None)
        return st if isinstance(st, dict) else {"version": TRINITY_DESK_VERSION, "anchor": str(self.anchor),
                                                "rebalances": [], "last_session": None, "week": None, "peak": None,
                                                "closed_r": [], "failed": None}

    def _save(self, st: dict, reason: str) -> None:
        self.db.set_kv(STATE_KEY, st, reason=reason)

    def _event(self, kind: str, payload: dict, ref: str | None = None) -> dict:
        from ..version import stamp  # late: the version module imports every component, this one included
        row = {"t": self.clock(), "version": TRINITY_DESK_VERSION, "rule": RULE_ID, **payload, "versions": stamp()}
        self.db.event(kind, row, ref=ref)
        return {"kind": kind, **row}

    def _held(self) -> dict:
        return {p.symbol: p for p in self.broker.positions()}

    def rule(self) -> tuple[PromotedRule | None, str]:
        """The promoted rule this desk may open positions for, or None with the reason it may not."""
        r = next((x for x in self.rules if x.rule_id == RULE_ID), None)
        if r is None:
            return None, f"{RULE_ID} is not in models/artifacts/promoted_rules.json ({self.rules_note})"
        if r.mode != "PAPER" or r.status not in OPENS_UNDER or r.health != "HEALTHY":
            return None, f"{RULE_ID} is {r.status}/{r.health} in mode {r.mode}: nothing is opened"
        return r, f"{RULE_ID} promoted for PAPER as {r.status} on {r.promoted_on}"

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
        # the drawdown reference is the starting balance, as the firm's maximum loss is (the trend desk's 1.1.0)
        return AccountState(equity=equity, balance=balance, day_start_equity=day.get("reference"),
                            peak_equity=self.gate.profile.starting_balance,
                            start_balance=self.gate.profile.starting_balance,
                            open_positions=positions if positions is not None else [],
                            week_start_equity=(st.get("week") or {}).get("equity"),
                            closed_r=list(st.get("closed_r") or [])[-30:],
                            kill_switch=kill if positions is not None else None,
                            paused=bool(self.db.get_kv("paused", False)), halted=bool(self.db.get_kv("halted", False)))

    def _mark(self, st: dict, t: int) -> None:
        try:
            eq = self.broker.account().equity
        except BrokerError:
            return
        week = int((t // 86400 - 4) // 7)
        if not st.get("week") or st["week"].get("id") != week:
            st["week"] = {"id": week, "equity": eq}
        st["peak"] = eq if st.get("peak") is None else max(st["peak"], eq)

    # ── one session: the close of one US trading day ──

    def session(self, day: date, bars: dict[str, DailyBar], signals: dict[str, dict[date, float]],
                days: list[date]) -> list[dict]:
        """The close of `day`. In order: the stops against the day's range; the account at the intraday lows, then
        at the close; closed trades; on a rebalance day, the rule; the day's audit. `signals` holds the closes of
        QQQ, SPY, GLD, DBC, the VIX, TLT and UUP, and `days` their trading days; nothing after `day` is read."""
        missing = [s for s in INSTRUMENTS if s not in bars]
        if missing:
            raise ValueError(f"{day}: no bar for {missing}; a session needs every instrument's")
        t = close_time(day)
        st = self.state()
        if st.get("last_session") is not None and t <= st["last_session"]:
            return []
        out: list[dict] = []
        self.clock.t = max(self.clock.t, t - 60)
        for s in INSTRUMENTS:
            b, half = bars[s], SPREAD[s] / 2
            self.broker.on_bar(s, {"open_time": open_time(day), "close_time": t,
                                   "bid_open": b.open - half, "bid_high": b.high - half, "bid_low": b.low - half,
                                   "ask_open": b.open + half, "ask_high": b.high + half, "ask_low": b.low + half})
        self.feed.at_low({s: bars[s].low for s in INSTRUMENTS}, self.clock.t)
        try:
            low = self.gate.observe(self.broker)
        finally:
            self.feed.clear()
        out.append(self._event("DESK_INTRADAY_LOW", {"day": str(day), "symbols": list(INSTRUMENTS),
                                                     "lows": {s: bars[s].low for s in INSTRUMENTS},
                                                     "equity": low.get("equity_conservative"),
                                                     "risk_status": low.get("risk_status")}))
        self.clock.t = t
        status = self.gate.observe(self.broker)
        out += self._book_closures(st)
        self._mark(st, t)
        if status.get("state") == "LOCKED" and not st.get("failed"):
            st["failed"] = {"day": str(day), "t": t, "lock": status.get("lock")}
            out.append(self._event("DESK_ACCOUNT_FAILED", {"day": str(day), "lock": status.get("lock")}))
        if st.get("failed"):
            for s, p in self._held().items():
                ct = self.ex.close_position(p.id, "FAILED")
                out.append(self._event("DESK_EXIT", {"symbol": s, "day": str(day), "why": "the account failed",
                                                     "closed": ct is not None}, ref=p.id))
            out += self._book_closures(st)
        else:
            past = [d for d in days if d <= day]
            if self.anchor <= day and day in past and day in set(T.grid(past, self.anchor)):
                out += self._rebalance(st, day, t, bars, signals, past)
                out += self._book_closures(st)
        out.append(self._audit(day, t, rebalance=str(day) in st.get("rebalances", [])))
        st["last_session"] = t
        self._save(st, f"trinity desk: {day} session")
        return out

    def _book_closures(self, st: dict) -> list[dict]:
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

    def proposal(self, day: date, signals: dict[str, dict[date, float]], past: list[date]) -> dict:
        """TRINITY-MASTER's decision at `day` from the grid through it: the design book starts at the anchor, so its
        drawdown brake reads only what the book did since then. {"ok": False, "why"} when there is no decision."""
        g = T.grid(past, self.anchor)
        rows = T.rows_at(g, signals, past)
        at = next((i for i, r in enumerate(rows) if r["date"] == self.anchor), None)
        if at is None or at < T.WARMUP:
            return {"ok": False, "why": f"{len(rows)} grid rows through {day}; {T.WARMUP} are needed before the anchor"}
        dec = T.decide(T.features(rows), book_start=at)[-1]
        if dec["date"] != day:
            raise ValueError(f"the last grid row is {dec['date']}, not {day}")
        return {"ok": True, **dec}

    def _rebalance(self, st: dict, day: date, t: int, bars: dict[str, DailyBar], signals: dict,
                   past: list[date]) -> list[dict]:
        out: list[dict] = []
        prop = self.proposal(day, signals, past)
        st.setdefault("rebalances", []).append(str(day))
        if not prop["ok"]:
            return [self._event("DESK_REBALANCE", {"day": str(day), "decided": False, "why": prop["why"]})]
        w = prop["weights"]
        rule, why_rule = self.rule()
        out.append(self._event("DESK_REBALANCE", {"day": str(day), "decided": True, "weights": w,
                                                  "components": prop["components"], "buy": prop["buy"],
                                                  "design_dd_before": prop["dd_before"], "rule": why_rule}))
        held = self._held()
        for s in INSTRUMENTS:
            a = SIGNAL_OF[s]
            want = w[a] > T.MIN_WEIGHT
            p = held.get(s)
            base = {"symbol": s, "day": str(day), "for_rebalance": str(day), "signal_asset": a, "weight": w[a],
                    "close": bars[s].close, "held_before": p is not None}
            if want and p is None:
                if rule is None:
                    out.append(self._event("DESK_DECISION", {**base, "action": "BUY", "result": "NOT_PROMOTED",
                                                             "why": why_rule}))
                    continue
                ev = self._enter(st, s, bars[s], t, day, w)
                out.append(self._event("DESK_DECISION", {**base, "action": "BUY", **ev}))
            elif not want and p is not None:
                ct = self.ex.close_position(p.id, "RULE")
                out.append(self._event("DESK_DECISION", {**base, "action": "SELL",
                                                         "result": "CLOSED" if ct is not None else "NOT_CLOSED",
                                                         "exit": ct.exit if ct else None,
                                                         "pnl": ct.pnl if ct else None}, ref=p.id))
            elif want and p is not None:
                stop = round(bars[s].close * (1 - T.STOP_REL), 2)
                res = self.ex.modify_stop(p.id, stop, f"rebalance {day}: {T.STOP_REL:.1%} below the close "
                                                      f"{bars[s].close}")
                out.append(self._event("DESK_DECISION", {**base, "action": "HOLD", "stop_from": p.stop, "stop_to": stop,
                                                         "stop_status": res["status"], "detail": res["detail"],
                                                         "held": res["stop"]}, ref=p.id))
            else:
                out.append(self._event("DESK_DECISION", {**base, "action": "FLAT"}))
        return out

    def _enter(self, st: dict, s: str, bar: DailyBar, t: int, day: date, weights: dict) -> dict:
        evidence = ({"rule_id": RULE_ID, "rebalance": str(day), "weight": weights[SIGNAL_OF[s]],
                     "weights": dict(weights)},)
        stop = round(bar.close * (1 - T.STOP_REL), 2)
        base = TrinityDecision(f"{RULE_ID}:{s}:{day}:BUY", "BUY", s, t, stop, evidence)
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

    def _audit(self, day: date, t: int, rebalance: bool) -> dict:
        """The day's audit row (the package's HardRiskGate invariants, measured, not asserted): every position has a
        stop, the loss at the stops together is within 4% of the starting balance, and the margin within the
        equity. A figure the account cannot give is None, and its check is None, never True."""
        prof = self.gate.profile
        try:
            acct = self.broker.account()
            equity = round(acct.equity, 2)
        except BrokerError:
            acct, equity = None, None
        rows, risk_total, margin, known = [], 0.0, 0.0, True
        for p in self.broker.positions():
            spec, q = self.broker.spec(p.symbol), self.broker.quote(p.symbol)
            if spec is None or q is None:
                known = False
                rows.append({"symbol": p.symbol, "qty": p.qty, "entry": p.entry, "stop": p.stop})
                continue
            units = p.qty * spec.contract_size * spec.value_per_price_unit
            mark = q.bid if p.side > 0 else q.ask
            at_stop = None if p.stop is None else round(max(0.0, (mark - p.stop) * p.side) * units, 2)
            notional = round(units * mark, 2)
            rows.append({"symbol": p.symbol, "qty": p.qty, "entry": p.entry, "stop": p.stop, "mark": mark,
                         "notional_usd": notional, "loss_at_stop_usd": at_stop})
            risk_total += at_stop or 0.0
            margin += notional / prof.leverage
        all_stops = all(r.get("stop") is not None for r in rows)
        return self._event("DESK_AUDIT", {
            "day": str(day), "rebalance": rebalance, "equity": equity, "positions": rows,
            "loss_at_stops_usd": round(risk_total, 2) if known else None,
            "loss_at_stops_pct_of_start": round(100 * risk_total / prof.starting_balance, 3) if known else None,
            "margin_usd": round(margin, 2) if known else None,
            "checks": {"every_position_has_a_stop": all_stops,
                       "loss_at_stops_within_4pct": (risk_total <= 0.04 * prof.starting_balance + 1e-6) if known
                       else None,
                       "margin_within_equity": (margin <= equity) if known and equity is not None else None}})


def sessions(bars: dict[str, list[DailyBar]], after: int | None = None, until: int | None = None) -> list[date]:
    """The days every instrument has a bar, in order, strictly after `after` and at or before `until` (close times)."""
    common = None
    for s in INSTRUMENTS:
        ds = {b.day for b in bars.get(s, [])}
        common = ds if common is None else common & ds
    out = []
    for d in sorted(common or ()):
        t = close_time(d)
        if (after is None or t > after) and (until is None or t <= until):
            out.append(d)
    return out


__all__ = ["DESK_LIMITS", "INSTRUMENTS", "OPENS_UNDER", "PRICE_SOURCE", "RULE_ID", "SCALE_TO", "SIGNAL_OF", "SPREAD",
           "START", "STATE_KEY", "TRINITY_DESK_VERSION", "TrinityDecision", "TrinityFeed", "TrinityPaperDesk",
           "close_time", "open_time", "sessions"]
