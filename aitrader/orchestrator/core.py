"""The central orchestrator: coordinates, never overrides.

It knows what data is available, which agents must run, whether a decision is
ready, what the risk engine said, what execution did, what must be
remembered, and when to learn and reflect. It cannot bypass the risk engine
or the execution checks: it only calls them.

The same object runs a backtest (ReplayFeed + PaperBroker on replayed
bars) and paper/demo trading (live feed + paper or broker adapter). Nothing
in here knows which one it is, so a backtest measures the system that runs.

Event types written to the immutable log (a subset in backtests, see
`OrchestratorConfig.events`):

  MARKET_DATA_UPDATED ANALYSIS_REQUESTED ANALYSIS_COMPLETED DECISION_READY
  RISK_APPROVED RISK_REJECTED ORDER_* POSITION_CLOSED TRADE_REVIEW_REQUESTED
  TRADE_REVIEWED REFLECTION_REQUESTED REFLECTION_COMPLETED
  LEARNING_HYPOTHESIS_CREATED LEARNING_HYPOTHESIS_VALIDATED
  LEARNING_HYPOTHESIS_REJECTED LESSON_RETIRED KNOWLEDGE_VERSION_UPDATED
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from ..agents.brain import Brain
from ..agents.types import AccountView, MarketContext
from ..broker.base import BrokerError
from ..broker.paper import pip_of
from ..data.resample import bucket_start
from ..decision.synthesis import Decision
from ..execution.engine import ExecutionEngine
from ..features.store import LOOKBACK, compute_at
from ..learning.experience import Evaluation, ExperienceView, session_of
from ..learning.review import postmortem, reflect
from ..memory.db import Database
from ..memory.patterns import PatternMemory
from ..research.labels import TEMPLATE_BY_KEY, CostModel, atr24
from ..risk.engine import AccountState, RiskEngine
from .tracker import ACTIONS, OutcomeTracker, Tracked

ORCHESTRATOR_VERSION = "orchestrator-1.0.0"


class NullKnowledge:
    """No learned knowledge: used to measure what learning adds (ablation)."""

    def lessons_matching(self, *a): return []
    def family_regime_stats(self, *a): return None
    def objection_effect(self, *a): return None
    def agent_reliability(self, *a): return 0.0


@dataclass
class OrchestratorConfig:
    symbols: list[str]
    timeframe: str = "H1"
    mode: str = "PAPER"  # BACKTEST | PAPER | DEMO
    analog_k: int = 100
    analog_z: float = 1.28
    journal: str = "full"  # full | trades
    events: str = "all"  # all | key
    learn_every_s: int = 7 * 86400
    reflect_every_trades: int = 25
    max_data_age_s: int = 2 * 3600
    start_balance: float = 20_000.0
    costs: CostModel = field(default_factory=CostModel)
    #: False = the memory-only ablation: no lessons, no measured penalties.
    learning_enabled: bool = True


class Orchestrator:
    def __init__(self, cfg: OrchestratorConfig, *, db: Database, feed, broker, brain: Brain,
                 risk: RiskEngine, execution: ExecutionEngine, experience: ExperienceView,
                 memory: PatternMemory, regime_for: Callable[[int], object], clock: Callable[[], int],
                 versions: dict) -> None:
        self.cfg, self.db, self.feed, self.broker = cfg, db, feed, broker
        self.brain, self.risk, self.execution = brain, risk, execution
        self.experience, self.memory, self.regime_for = experience, memory, regime_for
        self.clock, self.versions = clock, dict(versions)
        self.tracker = OutcomeTracker(pip_of, cfg.costs, on_resolved=self._on_resolved)
        self.experience.on_lesson = self._on_lesson
        self._last_learn = 0
        self._trades_since_reflect = 0
        self._postmortems: list[dict] = []
        self._closed_r: list[float] = [r["r"] for r in db.query("SELECT r FROM trades ORDER BY seq") if r["r"] is not None]
        self.knowledge_version = (db.one("SELECT MAX(version) AS v FROM knowledge_versions") or {}).get("v") or 0
        self.versions["knowledge"] = self.knowledge_version
        self.counts = {"decisions": 0, "no_trade": 0, "trade_decisions": 0, "risk_rejected": 0,
                       "executed": 0, "closed": 0, "errors": 0}
        self.status: dict = {"symbols": {}, "last_cycle": None, "errors": []}
        self.listeners: list[Callable[[str, dict], None]] = []

    # ── journaling ──────────────────────────────────────────────────────

    def _event(self, type_: str, payload: dict, ref: str | None = None, key: bool = False) -> None:
        if self.cfg.events == "all" or key:
            self.db.event(type_, payload, ref)
        for fn in self.listeners:
            try:
                fn(type_, payload)
            except Exception:
                pass

    # ── bars: the market moves ──────────────────────────────────────────

    def on_bar_closed(self, symbol: str, bar: dict) -> None:
        if hasattr(self.broker, "on_bar"):
            self.broker.on_bar(symbol, bar)  # paper: stops/targets
        self.tracker.on_bar(symbol, bar)

    # ── the cycle ───────────────────────────────────────────────────────

    def cycle(self, t: int, symbols: list[str] | None = None) -> dict:
        report = {"t": t, "decisions": []}
        self.experience.advance(t)
        self._process_closures(t)
        self._time_exits(t)
        for symbol in symbols if symbols is not None else self.cfg.symbols:
            try:
                d = self.decide(symbol, t)
                if d is not None:
                    report["decisions"].append({"symbol": symbol, "decision": d.decision})
            except Exception as exc:  # a crash in one symbol is NO_TRADE for it, and visible
                self.counts["errors"] += 1
                msg = f"{symbol}: {type(exc).__name__}: {exc}"
                self.status["errors"] = (self.status["errors"] + [{"t": t, "error": msg}])[-50:]
                self._event("CYCLE_ERROR", {"symbol": symbol, "error": msg,
                                            "trace": traceback.format_exc()[-2000:]}, key=True)
        if t - self._last_learn >= self.cfg.learn_every_s:
            self.learn(t)
        self.status["last_cycle"] = t
        return report

    def _account_state(self, t: int) -> tuple[AccountState, AccountView]:
        try:
            snap = self.broker.account()
            equity, balance = snap.equity, snap.balance
        except BrokerError:
            equity = balance = None
        try:
            positions = [{"symbol": p.symbol, "side": p.side, "qty": p.qty,
                          "notional": p.qty * (100 if p.symbol.startswith("XAU") else 100_000) * p.entry}
                         for p in self.broker.positions()]
        except BrokerError:
            positions = None
        day = int(bucket_start(np.array([t]), "D1")[0])
        ds = self.db.get_kv("day_start", None)
        if equity is not None and (not ds or ds.get("day") != day):
            ds = {"day": day, "equity": equity}
            self.db.set_kv("day_start", ds, reason="new trading day")
        peak = self.db.get_kv("peak_equity", None)
        if equity is not None and (peak is None or equity > peak):
            peak = equity
            if self.cfg.events == "all":
                self.db.set_kv("peak_equity", peak, reason="new equity high")
            else:
                with self.db.tx() as c:
                    c.execute("INSERT INTO kv(key, value, updated) VALUES ('peak_equity', ?, ?) ON CONFLICT(key) "
                              "DO UPDATE SET value=excluded.value, updated=excluded.updated", (json.dumps(peak), time.time()))
        ks = self.db.get_kv("kill_switch", None)
        kill = None if not isinstance(ks, dict) or "active" not in ks else bool(ks["active"])
        state = AccountState(
            equity=equity, balance=balance, day_start_equity=(ds or {}).get("equity"), peak_equity=peak,
            start_balance=self.cfg.start_balance, open_positions=positions if positions is not None else [],
            closed_r=list(self._closed_r[-30:]), kill_switch=kill if positions is not None else None,
            paused=bool(self.db.get_kv("paused", False)), halted=bool(self.db.get_kv("halted", False)))
        dd = ((equity - peak) / peak * -100) if equity and peak else None
        view = AccountView(equity, balance, dd, [{"symbol": p["symbol"], "side": p["side"]} for p in (positions or [])],
                           ((equity - ds["equity"]) / ds["equity"] * 100) if equity and ds else None)
        return state, view

    def decide(self, symbol: str, t: int) -> Decision | None:
        window = self.feed.bars(symbol, t, LOOKBACK)
        if window is None or len(window) == 0:
            self.status["symbols"][symbol] = {"t": t, "state": "NO_DATA"}
            return None
        self._event("MARKET_DATA_UPDATED", {"symbol": symbol, "bars": len(window),
                                            "last_close": int(window.available_at[-1])})
        flags = []
        age = t - int(window.available_at[-1])
        if age > self.cfg.max_data_age_s:
            flags.append(f"latest bar closed {age // 60} minutes ago")
        fv = compute_at(window, t)
        regime_model = self.regime_for(t)
        regime = regime_model.classify(fv.values)
        atr = float(atr24(window)[-1]) if len(window) > 25 else float("nan")
        quote = self.feed.quote(symbol, t)
        ev = self.memory.query(fv.values, t, k=self.cfg.analog_k, z=self.cfg.analog_z) if fv.complete else None
        state, view = self._account_state(t)
        ctx = MarketContext(
            symbol, self.cfg.timeframe, t, fv, regime, atr if np.isfinite(atr) else None,
            quote.bid if quote else None, quote.ask if quote else None, quote.time if quote else None,
            {"swing_high_dist_atr": fv.values.get("smc_hi_dist"), "swing_low_dist_atr": fv.values.get("smc_lo_dist"),
             "range_pos120": fv.values.get("range_pos120")},
            view, data_flags=flags, analogs={a: ev for a in ACTIONS} if ev is not None else {},
            analog_meta={"available": ev.available if ev else 0, "memory_version": self.memory.version},
            knowledge=self.experience if self.cfg.learning_enabled else NullKnowledge(), mode=self.cfg.mode)
        self._event("ANALYSIS_REQUESTED", {"symbol": symbol, "t": t})
        thought = self.brain.think(ctx, self.versions)
        d = thought.decision
        self.counts["decisions"] += 1
        self._event("ANALYSIS_COMPLETED", {"symbol": symbol, "timings_ms": thought.timings_ms,
                                           "agents": {k: r.status for k, r in thought.reports.items()}})
        journal = self.cfg.journal == "full" or d.is_trade
        if journal:
            self._journal_decision(ctx, thought)
        self._event("DECISION_READY", {"id": d.id, "symbol": symbol, "decision": d.decision,
                                       "reason": d.no_trade_reason or d.thesis}, ref=d.id)

        verdict = None
        executed = None
        if d.is_trade:
            self.counts["trade_decisions"] += 1
            spec = None
            try:
                spec = self.broker.spec(symbol)
            except BrokerError:
                spec = None
            verdict = self.risk.evaluate(d, state, spec, quote, t, self.execution.executed_ids())
            if not self.db.one("SELECT 1 AS x FROM risk_verdicts WHERE decision_id=?", (d.id,)):
                self.db.append("risk_verdicts", {"decision_id": d.id, "approved": int(verdict.approved),
                                                 "payload": verdict.as_dict()})
            self._event("RISK_APPROVED" if verdict.approved else "RISK_REJECTED",
                        {"id": d.id, "reasons": verdict.reasons, "qty": verdict.qty}, ref=d.id, key=True)
            if verdict.halt:
                self.db.set_kv("halted", True, reason=verdict.halt)
            if verdict.approved:
                res = self.execution.execute(d, verdict, meta={"swap_per_night": self.cfg.costs.swap_atr_per_night * (atr or 0)})
                executed = res.status == "FILLED"
                self.counts["executed"] += int(executed)
            else:
                self.counts["risk_rejected"] += 1
        else:
            self.counts["no_trade"] += 1

        # Track every action's outcome from here, and remember what was evaluated.
        setup = thought.reports.get("setup")
        cands = []
        for c in (setup.candidates if setup and setup.ok else [])[:4]:
            objs = sorted({o.code for r in thought.reports.values() for o in r.objections
                           if o.data.get("action") in (None, c.action)})
            if d.is_trade and verdict is not None and not verdict.approved and c.action == f"{d.template}:{d.decision}":
                objs.append("RISK_REJECTED")
            cands.append({"family": c.family, "action": c.action, "direction": c.direction,
                          "objections": objs, "predicted_r": c.expected_r, "predicted_win": c.win_rate,
                          "traded": bool(executed) and c.action == f"{d.template}:{d.decision}" and c.family == d.family})
        llm_dirs = {o["agent"]: o.get("direction", "NONE") for o in thought.llm_opinions if o.get("ok")}
        self.tracker.track(d.id, symbol, t, atr, fv.array(), {
            "candidates": cands, "regime": regime.label, "vol": regime.vol_state, "decision": d.decision,
            "llm": llm_dirs, "journal": journal})
        self.status["symbols"][symbol] = {
            "t": t, "decision": d.decision, "reason": d.no_trade_reason or d.thesis, "regime": regime.label,
            "vol": regime.vol_state, "familiar": regime.familiar, "confidence": d.confidence,
            "expected_R": d.expected_R, "lower_R": d.lower_R, "required": d.required_edge,
            "risk": (verdict.as_dict() if verdict else None), "bid": ctx.bid, "ask": ctx.ask,
            "agents": d.agents, "decision_id": d.id}
        return d

    def _journal_decision(self, ctx: MarketContext, thought) -> None:
        d = thought.decision
        with self.db.tx() as c:
            exists = c.execute("SELECT 1 FROM decisions WHERE id=?", (d.id,)).fetchone()
            if exists:
                return  # the same decision point, seen again after a restart: already on record
            self.db.append("decisions", {"id": d.id, "symbol": d.instrument, "timeframe": d.timeframe,
                                         "decision": d.decision, "mode": d.mode,
                                         "payload": {**d.as_dict(), "context": ctx.as_dict()}}, conn=c)
            for name, r in thought.reports.items():
                self.db.append("agent_reports", {"decision_id": d.id, "agent": name, "payload": r.as_dict()}, conn=c)

    # ── outcomes ────────────────────────────────────────────────────────

    def _on_resolved(self, tr: Tracked) -> None:
        by_action = {leg.action: leg for leg in tr.legs}
        outcomes = np.array([[by_action[a].r for a in self.memory.action_keys]], dtype=float)
        resolved_at = max(leg.exit_time for leg in tr.legs)
        self.memory.add(tr.features[None, :], outcomes, np.array([resolved_at]), tr.symbol, np.array([tr.decision_time]))
        for c in tr.context["candidates"]:
            if c["traded"]:
                continue  # its real result arrives with the closed trade
            leg = by_action[c["action"]]
            self.experience.record(Evaluation(
                tr.key, tr.symbol, tr.decision_time, leg.exit_time, c["family"], c["action"], c["direction"],
                tr.context["regime"], tr.context["vol"], session_of(tr.decision_time), tuple(c["objections"]),
                False, float(leg.r), c["predicted_r"], c["predicted_win"], dict(tr.context["llm"])))
        if tr.context.get("journal") and self.cfg.journal == "full" and tr.context["decision"] == "NO_TRADE":
            with self.db.tx() as conn:
                if not conn.execute("SELECT 1 FROM episodes WHERE decision_id=?", (tr.key,)).fetchone():
                    self.db.append("episodes", {"decision_id": tr.key, "kind": "NO_TRADE", "symbol": tr.symbol,
                                                "payload": {"shadow": {a: round(float(l.r), 4) for a, l in by_action.items()},
                                                            "resolved_at": resolved_at, "candidates": tr.context["candidates"]}},
                                   conn=conn)

    def _process_closures(self, t: int) -> None:
        for row, ct in self.execution.sync_closures():
            dec_row = self.db.one("SELECT payload FROM decisions WHERE id=?", (row["decision_id"],))
            dec = json.loads(dec_row["payload"]) if dec_row else {}
            pos_payload = json.loads(row["payload"]) if row.get("payload") else {}
            risk_amount = pos_payload.get("risk_amount")
            r = (ct.pnl / risk_amount) if (ct.pnl is not None and risk_amount) else None
            risk_dist = abs(row["entry"] - row["stop"]) or None
            side = 1 if row["side"] == "BUY" else -1
            mfe = ((ct.mfe_price - row["entry"]) * side / risk_dist) if (risk_dist and ct.mfe_price) else None
            mae = ((ct.mae_price - row["entry"]) * side / risk_dist) if (risk_dist and ct.mae_price) else None
            regime_exit = None
            win = self.feed.bars(row["symbol"], ct.closed, LOOKBACK)
            if win is not None and len(win):
                regime_exit = self.regime_for(ct.closed).classify(compute_at(win, ct.closed).values).label
            slip = pos_payload.get("slippage")
            trade = {"r": r, "mfe_r": mfe, "mae_r": mae, "bars_held": max(0, (ct.closed - ct.opened) // 3600),
                     "exit_reason": ct.reason, "predicted_win": dec.get("probability"), "predicted_r": dec.get("expected_R"),
                     "slippage_r": (abs(slip) / risk_dist) if (slip is not None and risk_dist) else None,
                     "regime_entry": (dec.get("regime") or {}).get("label"), "regime_exit": regime_exit,
                     "data_flags": ((dec.get("context") or {}).get("data_flags"))}
            pm = postmortem(trade)
            self._postmortems.append(pm)
            record = {"decision": {k: dec.get(k) for k in ("id", "decision", "family", "template", "thesis",
                                                           "expected_R", "lower_R", "probability", "confidence",
                                                           "required_edge", "regime", "versions")},
                      "position": {k: row[k] for k in ("id", "symbol", "side", "qty", "entry", "stop", "target", "opened")},
                      "exit": {"price": ct.exit, "time": ct.closed, "reason": ct.reason, "pnl": ct.pnl},
                      "r": r, "mfe_r": mfe, "mae_r": mae, "postmortem": pm}
            with self.db.tx() as c:
                if c.execute("SELECT 1 FROM trades WHERE position_id=?", (row["id"],)).fetchone():
                    continue
                self.db.append("trades", {"position_id": row["id"], "decision_id": row["decision_id"],
                                          "symbol": row["symbol"], "r": r, "pnl": ct.pnl, "payload": record}, conn=c)
                ep = self.db.append("episodes", {"decision_id": row["decision_id"], "kind": "TRADE",
                                                 "symbol": row["symbol"], "payload": record}, conn=c)
                self.db.append("postmortems", {"episode_id": ep["id"], "payload": pm}, conn=c)
            self._event("TRADE_REVIEWED", {"position": row["id"], "r": r, "cause": pm["cause"]}, ref=row["id"], key=True)
            self.counts["closed"] += 1
            if r is not None:
                self._closed_r.append(r)
                cand_objs = sorted({c["code"] for c in dec.get("contradicting_evidence", []) if c.get("code")})
                self.experience.record(Evaluation(
                    row["decision_id"], row["symbol"], int(row["opened"]), int(ct.closed), dec.get("family") or "?",
                    f"{dec.get('template')}:{row['side']}", side, (dec.get("regime") or {}).get("label", "?"),
                    (dec.get("regime") or {}).get("vol_state", "?"), session_of(int(row["opened"])),
                    tuple(cand_objs), True, float(r), dec.get("expected_R"), dec.get("probability")))
            self._trades_since_reflect += 1
        if self._trades_since_reflect >= self.cfg.reflect_every_trades:
            self.reflect(t)

    def _time_exits(self, t: int) -> None:
        for row in self.db.query("SELECT * FROM positions WHERE status='OPEN'"):
            dec = self.db.one("SELECT payload FROM decisions WHERE id=?", (row["decision_id"],))
            tpl = TEMPLATE_BY_KEY.get((json.loads(dec["payload"]) if dec else {}).get("template") or "")
            if tpl is not None and t - row["opened"] >= tpl.max_bars * 3600:
                self.execution.close_position(row["id"], "TIME")

    # ── learning ────────────────────────────────────────────────────────

    def _on_lesson(self, version: dict) -> None:
        self.db.append("lessons", {"lesson_id": version["lesson_id"], "version": version["version"],
                                   "status": version["status"], "payload": version})
        kind = {"CANDIDATE": "LEARNING_HYPOTHESIS_CREATED", "VALIDATED": "LEARNING_HYPOTHESIS_VALIDATED",
                "REJECTED": "LEARNING_HYPOTHESIS_REJECTED", "RETIRED": "LESSON_RETIRED"}[version["status"]]
        self._event(kind, {"lesson": version["lesson_id"], "version": version["version"],
                           "statement": version.get("statement")}, ref=version["lesson_id"], key=True)

    def learn(self, t: int) -> list[dict]:
        self._last_learn = t
        changes = self.experience.learn(t)
        if changes:
            self.knowledge_version += 1
            self.versions["knowledge"] = self.knowledge_version
            active = [v[-1]["lesson_id"] for v in self.experience.lessons.values() if v[-1]["status"] == "VALIDATED"]
            self.db.append("knowledge_versions", {"version": self.knowledge_version, "payload": {
                "t": t, "changes": [{"lesson": c["lesson_id"], "version": c["version"], "status": c["status"]} for c in changes],
                "active_lessons": active, "parent": self.knowledge_version - 1}})
            self._event("KNOWLEDGE_VERSION_UPDATED", {"version": self.knowledge_version, "active": active}, key=True)
        return changes

    def reflect(self, t: int) -> dict:
        self._trades_since_reflect = 0
        self._event("REFLECTION_REQUESTED", {"t": t}, key=True)
        rel = {a: self.experience.agent_reliability(a, t) for a in ("adversary_llm", "reviewer_llm")}
        out = reflect(self.experience.resolved, self._postmortems[-500:], t, rel)
        self.db.append("reflections", {"payload": out})
        self._event("REFLECTION_COMPLETED", {"t": t, "hypotheses": out.get("hypotheses", [])}, key=True)
        return out
