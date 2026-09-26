"""The running system: wiring, scheduler, position monitor, and read models.

MODE=PAPER  live TradeLocker market data (when credentials are configured),
            simulated $20,000 paper account, orders never leave the process.
MODE=DEMO   live TradeLocker market data AND orders on a DEMO account,
            verified by the two-signal demo guard before every order.

Without broker credentials the system still starts, serves the dashboard
and health, and reports DATA: NOT CONNECTED — it does not trade on
invented prices (rule: never fabricate a value).

Startup sequence: open the database -> load knowledge -> reconcile broker
state (before any decision) -> start the scheduler. If reconciliation
fails, trading starts PAUSED and the dashboard says why.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ..agents.brain import Brain, BrainConfig
from ..backtest.metrics import summarise
from ..broker.paper import PaperBroker
from ..data.bars import BarSeries
from ..decision.synthesis import EvidenceSynthesizer
from ..execution.engine import ExecutionEngine
from ..features.store import LOOKBACK
from ..learning.experience import ExperienceView
from ..llm.provider import LLMClient, LLMConfig
from ..memory.db import Database
from ..memory.patterns import PatternMemory
from ..observability import log_event, recent
from ..orchestrator.core import Orchestrator, OrchestratorConfig
from ..orchestrator.tracker import ACTIONS
from ..regime.model import RegimeModel
from ..risk.engine import RiskEngine
from ..version import stamp
from .config import ServiceConfig

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "models" / "artifacts"

#: 1.1.0: decide only every `decision_every_bars` H1 closes (the tested cadence);
#: bookkeeping still runs every hour. 1.0.0 decided every hour.
SERVICE_VERSION = "service-1.1.0"


class OfflineFeed:
    """No market data source configured: every read says so, nothing is invented."""

    def __init__(self, symbols):
        self._symbols = list(symbols)

    def symbols(self):
        return list(self._symbols)

    def bars(self, symbol, as_of, count):
        return None

    def quote(self, symbol, now=None):
        return None


class LiveFeedAdapter:
    """Wraps the TradeLocker adapter as the orchestrator's feed, with a short
    per-cycle cache so one decision does not fetch the same bars twice."""

    def __init__(self, tl, clock):
        self.tl = tl
        self.clock = clock
        self._cache: dict = {}
        self.last_ok: int | None = None
        self.last_error: str | None = None

    def symbols(self):
        return self.tl.symbols()

    def bars(self, symbol, as_of, count):
        key = (symbol, as_of // 60, count)
        if key not in self._cache:
            try:
                self._cache[key] = self.tl.bars(symbol, as_of, count)
                if self._cache[key] is not None:
                    self.last_ok = int(self.clock())
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                self._cache[key] = None
            if len(self._cache) > 200:
                self._cache.pop(next(iter(self._cache)))
        return self._cache[key]

    def quote(self, symbol, now=None):
        q = self.tl.quote(symbol)
        if q is not None:
            self.last_ok = int(self.clock())
        return q


class Runtime:
    def __init__(self, cfg: ServiceConfig, *, feed=None, broker=None, clock=None,
                 knowledge_dir: Path | None = None) -> None:
        self.cfg = cfg
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir is not None else KNOWLEDGE_DIR
        self.started = time.time()
        self.clock = clock or (lambda: int(time.time()))
        Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
        self.db = Database(Path(cfg.data_dir) / "aitrader.db")
        if self.db.get_kv("kill_switch", None) is None:
            self.db.set_kv("kill_switch", {"active": False}, reason="first start")
        self.llm = LLMClient(LLMConfig.from_env())
        self.tl = None
        self.feed, self.broker = feed, broker
        if self.feed is None or self.broker is None:
            self._connect()
        self.memory, self.regime, self.knowledge_meta = self._load_knowledge()
        self.experience = ExperienceView()
        self._replay_experience()
        self.execution = ExecutionEngine(self.db, self.broker, self.clock)
        self.orch = Orchestrator(
            OrchestratorConfig(list(cfg.symbols), mode=cfg.mode, journal="full", events="all",
                               start_balance=cfg.start_balance),
            db=self.db, feed=self.feed, broker=self.broker,
            brain=Brain(llm=self.llm, synthesizer=EvidenceSynthesizer(), config=BrainConfig.from_env()),
            risk=RiskEngine(cfg.risk), execution=self.execution, experience=self.experience,
            memory=self.memory, regime_for=lambda t: self.regime, clock=self.clock,
            versions={**stamp(), "service": SERVICE_VERSION, "knowledge_base": (self.knowledge_meta.get("hash", "none")
                                                     if self.knowledge_meta.get("integrity") == "VERIFIED" else "none"),
                      "llm": self.llm.config.public()["model"] or "none"})
        self.health: dict = {"reconcile": None, "last_cycle": None, "last_cycle_error": None, "cycles": 0}
        self._stop = threading.Event()
        # One writer of orchestrator state at a time: the scheduler, a dashboard
        # "scan now", bar monitoring and a knowledge revert would otherwise race,
        # and two cycles could each see no open position and each open one.
        self._cycle_lock = threading.RLock()
        self._threads: list[threading.Thread] = []
        self._last_bar_seen: dict[str, int] = {}
        self._reconcile_at_start()

    # ── wiring ──────────────────────────────────────────────────────────

    def _connect(self) -> None:
        from ..broker.tradelocker._compat import TradingConfig
        tlcfg = TradingConfig.from_env()
        if tlcfg.broker.configured:
            from ..broker.tradelocker.adapter import TradeLockerAdapter

            def intent_lookup(cid):
                row = self.db.one("SELECT * FROM intents WHERE id=?", (cid,))
                if not row:
                    return None
                p = json.loads(row["payload"])
                return {"symbol": row["symbol"], "side": row["side"], "qty": p["qty"], "ts": row["ts"]}

            self.tl = TradeLockerAdapter(
                tlcfg, list(self.cfg.symbols), intent_lookup=intent_lookup,
                claimed_positions=lambda: {r["id"] for r in self.db.query("SELECT id FROM positions")})
            self.feed = LiveFeedAdapter(self.tl, self.clock)
        else:
            self.feed = OfflineFeed(self.cfg.symbols)
        if self.cfg.mode == "DEMO":
            if self.tl is None:
                log_event("STARTUP", "MODE=DEMO but TradeLocker is not configured: running with no broker",
                          severity="critical")
                self.broker = PaperBroker(self.feed, self.clock, self.db, start_balance=self.cfg.start_balance)
                self.db.set_kv("paused", True, reason="DEMO requested without broker credentials")
            else:
                self.broker = self.tl
        else:
            self.broker = PaperBroker(self.feed, self.clock, self.db, start_balance=self.cfg.start_balance)

    def _load_knowledge(self):
        """Load the research knowledge base only if its files are the ones its card describes.

        The card's sha256 covers memory.npz + regime.json. A missing card, a
        missing file or a different hash loads NOTHING: the regime model stays
        missing, so no cycle decides (MODEL_CONTRACT.md, models/README.md).
        A live memory on the volume is this system's own forward experience,
        grown from a verified base; it replaces the base's memory only once
        the base itself has verified.
        """
        kdir = self.knowledge_dir
        mem_path, reg_path, card = kdir / "memory.npz", kdir / "regime.json", kdir / "knowledge_card.json"
        empty = PatternMemory(np.zeros(18), np.ones(18), ACTIONS)
        present = [f.name for f in (card, mem_path, reg_path) if f.exists()]
        if not present:
            log_event("STARTUP", "no knowledge base found: no decisions will be made", severity="warning")
            return empty, None, {"integrity": "MISSING"}
        if len(present) < 3:
            log_event("STARTUP", f"incomplete knowledge base (found {present}): refused", severity="critical")
            return empty, None, {"integrity": "INCOMPLETE", "found": present}
        meta = json.loads(card.read_text())
        digest = hashlib.sha256(mem_path.read_bytes() + reg_path.read_bytes()).hexdigest()
        if digest != meta.get("sha256"):
            log_event("STARTUP", "knowledge base does not match its card: refused", severity="critical",
                      expected=str(meta.get("sha256"))[:16], actual=digest[:16])
            return empty, None, {**meta, "integrity": "MISMATCH", "actual_sha256": digest}
        meta = {**meta, "integrity": "VERIFIED"}
        live_mem = Path(self.cfg.data_dir) / "memory_live.npz"
        memory = PatternMemory.load(live_mem if live_mem.exists() else mem_path)
        meta["memory_source"] = "live (grown forward from the verified base)" if live_mem.exists() else "base"
        return memory, RegimeModel.from_json(reg_path.read_text()), meta

    def _replay_experience(self) -> None:
        """Rebuild point-in-time experience from the immutable episodes after a restart."""
        from ..learning.experience import Evaluation, session_of
        n = shadows = 0
        for row in self.db.query("SELECT payload FROM evaluations ORDER BY seq"):
            for e in json.loads(row["payload"])["evaluations"]:
                self.experience.record(Evaluation(**{**e, "objections": tuple(e["objections"])}))
                shadows += 1
        for row in self.db.query("SELECT payload FROM episodes WHERE kind='TRADE' ORDER BY seq"):
            p = json.loads(row["payload"])
            d = p.get("decision") or {}
            pos = p.get("position") or {}
            if p.get("r") is None:
                continue
            self.experience.record(Evaluation(
                d.get("id") or "", pos.get("symbol", ""), int(pos.get("opened", 0)), int(p["exit"]["time"]),
                d.get("family") or "?", f"{d.get('template')}:{pos.get('side')}", 1 if pos.get("side") == "BUY" else -1,
                (d.get("regime") or {}).get("label", "?"), (d.get("regime") or {}).get("vol_state", "?"),
                session_of(int(pos.get("opened", 0))), (), True, float(p["r"]), d.get("expected_R"), d.get("probability")))
            n += 1
        self.experience.advance(self.clock())
        for row in self.db.query("SELECT payload FROM lessons ORDER BY seq"):
            v = json.loads(row["payload"])
            self.experience.lessons.setdefault(v["lesson_id"], []).append(v)
        log_event("STARTUP", f"experience restored: {n} closed trades, {shadows} shadow outcomes, "
                             f"{len(self.experience.lessons)} lessons")

    def _reconcile_at_start(self) -> None:
        try:
            rep = self.execution.reconcile()
            self.health["reconcile"] = {"t": self.clock(), **rep}
            if rep.get("error") or rep.get("orphans"):
                self.db.set_kv("paused", True, reason=f"startup reconciliation: {rep.get('error') or 'orphan positions'}")
        except Exception as exc:
            self.health["reconcile"] = {"t": self.clock(), "error": f"{type(exc).__name__}: {exc}"}
            self.db.set_kv("paused", True, reason="startup reconciliation failed")

    # ── scheduler ───────────────────────────────────────────────────────

    @property
    def decide_every_bars(self) -> int:
        """The cadence the knowledge base was built and tested with (its card), 4 H1 bars by default.

        Deciding more often than the research did would run a system whose
        trade frequency and position overlap were never measured.
        """
        return max(1, int(self.knowledge_meta.get("decision_every_bars", 4)))

    def is_decision_hour(self, t: int) -> bool:
        return ((t - self.cfg.cycle_delay_s) // 3600) % self.decide_every_bars == 0

    def run_cycle(self, t: int | None = None, decide: bool = True) -> dict:
        """One cycle. `decide=False` only advances bookkeeping: outcomes, closures, time exits."""
        with self._cycle_lock:
            return self._run_cycle_locked(int(t or self.clock()), decide)

    def _run_cycle_locked(self, t: int, decide: bool) -> dict:
        if self.regime is None:
            self.health["last_cycle_error"] = (f"no regime model: knowledge base "
                                               f"{self.knowledge_meta.get('integrity', 'MISSING')}, no decisions made")
            return {"t": t, "decisions": []}
        try:
            rep = self.orch.cycle(t, None if decide else [])
            self.health.update(last_cycle=t, last_cycle_error=None, cycles=self.health["cycles"] + 1)
            self.memory.save(Path(self.cfg.data_dir) / "memory_live.npz")
            return rep
        except Exception as exc:
            self.health["last_cycle_error"] = f"{type(exc).__name__}: {exc}"
            log_event("CYCLE", "cycle failed", severity="error", error=traceback.format_exc()[-1500:])
            return {"t": t, "error": str(exc)}

    def monitor_once(self) -> None:
        """Feed newly closed bars to the paper broker and the outcome tracker."""
        with self._cycle_lock:
            self._monitor_locked()

    def _monitor_locked(self) -> None:
        now = self.clock()
        for s in self.cfg.symbols:
            bars = self.feed.bars(s, now, 3)
            if bars is None or len(bars) == 0:
                continue
            for i in range(len(bars)):
                close_t = int(bars.available_at[i])
                if close_t <= self._last_bar_seen.get(s, 0):
                    continue
                self._last_bar_seen[s] = close_t
                bar = {"open_time": int(bars.open_time[i]), "close_time": close_t,
                       **{f: float(getattr(bars, f)[i]) for f in ("bid_open", "bid_high", "bid_low", "bid_close",
                                                                  "ask_open", "ask_high", "ask_low", "ask_close")}}
                self.orch.on_bar_closed(s, bar)

    def _loop(self) -> None:
        next_cycle = self._next_cycle_time()
        while not self._stop.is_set():
            try:
                self.monitor_once()
                if self.clock() >= next_cycle:
                    self.run_cycle(decide=self.is_decision_hour(next_cycle))
                    next_cycle = self._next_cycle_time()
            except Exception as exc:
                self.health["last_cycle_error"] = f"{type(exc).__name__}: {exc}"
            self._stop.wait(self.cfg.monitor_interval_s)

    def _next_cycle_time(self) -> int:
        now = self.clock()
        return (now // 3600 + 1) * 3600 + self.cfg.cycle_delay_s

    def start(self) -> None:
        th = threading.Thread(target=self._loop, name="scheduler", daemon=True)
        th.start()
        self._threads.append(th)

    def stop(self) -> None:
        self._stop.set()
        for th in self._threads:
            th.join(timeout=10)
        try:
            self.memory.save(Path(self.cfg.data_dir) / "memory_live.npz")
        except Exception:
            pass

    # ── controls (the dashboard can make it safer; resuming needs the token) ──

    def pause(self, reason: str) -> None:
        self.db.set_kv("paused", True, reason=reason or "operator pause")

    def kill(self, reason: str) -> None:
        self.db.set_kv("kill_switch", {"active": True, "reason": reason or "operator emergency stop",
                                       "t": self.clock()}, reason=reason or "operator emergency stop")

    def resume(self) -> None:
        self.db.set_kv("paused", False, reason="operator resume (authenticated)")

    def clear_kill(self) -> None:
        self.db.set_kv("kill_switch", {"active": False}, reason="operator cleared kill switch (authenticated)")
        self.db.set_kv("halted", False, reason="operator cleared halt (authenticated)")

    def revert_knowledge(self, version: int) -> dict:
        """Reversible learning (authenticated): undo every lesson change after `version`.

        The revert is itself a new, higher knowledge version; nothing is deleted.
        """
        with self._cycle_lock:
            rep = self.orch.revert_knowledge(int(version), self.clock())
        self.db.event("KNOWLEDGE_VERSION_REVERTED", rep)
        return rep

    # ── read models for the API ─────────────────────────────────────────

    def status(self) -> dict:
        now = self.clock()
        try:
            db_ms = round(self.db.ping() * 1000, 2)
            db_ok = True
        except Exception:
            db_ms, db_ok = None, False
        broker_state = "NOT CONNECTED"
        demo = None
        if self.tl is not None:
            demo = self.tl.demo_status()
            broker_state = "CONNECTED" if getattr(self.feed, "last_ok", None) else "CONNECTING"
        elif isinstance(self.broker, PaperBroker):
            broker_state = "PAPER (simulated)"
        feed_ok = getattr(self.feed, "last_ok", None)
        ks = self.db.get_kv("kill_switch", None)
        return {
            "system": "ONLINE" if db_ok else "DEGRADED", "mode": self.cfg.mode, "time": now,
            "uptime_s": int(time.time() - self.started),
            "components": {
                "data": "CONNECTED" if feed_ok and now - feed_ok < 1800 else "NOT CONNECTED",
                "broker": broker_state, "demo_verification": demo,
                "ai": ("READY" if self.llm.config.enabled else "QUANT ONLY (no LLM configured)"),
                "database": "HEALTHY" if db_ok else "UNAVAILABLE", "db_latency_ms": db_ms,
                "knowledge_base": self.knowledge_meta,
                "knowledge_integrity": self.knowledge_meta.get("integrity", "MISSING"),
                "regime_model": "LOADED" if self.regime is not None else "MISSING",
            },
            "last_market_update": feed_ok, "last_cycle": self.health.get("last_cycle"),
            "last_cycle_error": self.health.get("last_cycle_error"),
            "kill_switch": ks, "paused": self.db.get_kv("paused", False), "halted": self.db.get_kv("halted", False),
            "counts": self.orch.counts, "versions": self.orch.versions, "config": self.cfg.public(),
            "reconcile": self.health.get("reconcile"),
        }

    def account(self) -> dict:
        try:
            snap = self.broker.account()
            eq, bal, ccy = snap.equity, snap.balance, snap.currency
        except Exception as exc:
            return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
        trades = self.trades(closed=True, limit=5000)
        perf = summarise(trades, self.cfg.start_balance) if trades else None
        peak = self.db.get_kv("peak_equity", None)
        ds = self.db.get_kv("day_start", None) or {}
        return {
            "available": True, "currency": ccy, "start_balance": self.cfg.start_balance, "balance": bal,
            "equity": eq, "floating_pnl": round(eq - bal, 2),
            "realized_pnl": round(bal - self.cfg.start_balance, 2) if isinstance(self.broker, PaperBroker) else None,
            "daily_pnl": round(eq - ds["equity"], 2) if ds.get("equity") else None,
            "drawdown_pct": round((eq - peak) / peak * 100, 2) if peak else None,
            "daily_loss_limit_pct": self.cfg.risk.daily_loss_limit_pct,
            "risk_per_trade_pct": self.cfg.risk.risk_per_trade_pct,
            "open_positions": len(self.db.query("SELECT id FROM positions WHERE status='OPEN'")),
            "performance": ({k: perf[k] for k in ("overall", "max_consecutive_losses")} if perf else None),
        }

    def trades(self, closed: bool = True, limit: int = 200) -> list[dict]:
        if not closed:
            out = []
            for r in self.db.query("SELECT * FROM positions WHERE status='OPEN' ORDER BY opened DESC"):
                q = self.feed.quote(r["symbol"], self.clock()) if hasattr(self.feed, "quote") else None
                side = 1 if r["side"] == "BUY" else -1
                cur = (q.bid if side > 0 else q.ask) if q else None
                risk = abs(r["entry"] - r["stop"]) or None
                out.append({**{k: r[k] for k in ("id", "symbol", "side", "qty", "entry", "stop", "target", "opened", "decision_id")},
                            "current": cur, "r_now": round((cur - r["entry"]) * side / risk, 3) if (cur and risk) else None,
                            "duration_h": round((self.clock() - r["opened"]) / 3600, 1), "status": "OPEN"})
            return out
        rows = self.db.query("SELECT payload, r, pnl, symbol FROM trades ORDER BY seq DESC LIMIT ?", (limit,))
        out = []
        for r in rows:
            p = json.loads(r["payload"])
            out.append({"symbol": r["symbol"], "r": r["r"], "pnl": r["pnl"], "opened": p["position"]["opened"],
                        "closed": p["exit"]["time"], "exit_reason": p["exit"]["reason"], "side": p["position"]["side"],
                        "entry": p["position"]["entry"], "exit": p["exit"]["price"],
                        "regime": (p["decision"].get("regime") or {}).get("label"), "family": p["decision"].get("family"),
                        "cause": p["postmortem"]["cause"], "explanation": p["postmortem"]["explanation"],
                        "decision_id": p["decision"].get("id"), "mfe_r": p.get("mfe_r"), "mae_r": p.get("mae_r")})
        return out

    def decisions(self, limit: int = 50, symbol: str | None = None) -> list[dict]:
        q = "SELECT id, ts, symbol, decision, payload FROM decisions"
        args: tuple = ()
        if symbol:
            q += " WHERE symbol=?"
            args = (symbol,)
        rows = self.db.query(q + " ORDER BY seq DESC LIMIT ?", args + (limit,))
        out = []
        for r in rows:
            p = json.loads(r["payload"])
            out.append({"id": r["id"], "symbol": r["symbol"], "decision": r["decision"], "time": p.get("timestamp"),
                        "thesis": p.get("thesis"), "no_trade_reason": p.get("no_trade_reason"),
                        "confidence": p.get("confidence"), "expected_R": p.get("expected_R"), "lower_R": p.get("lower_R"),
                        "required_edge": p.get("required_edge"), "regime": (p.get("regime") or {}).get("label"),
                        "family": p.get("family"), "entry": p.get("entry"), "stop": p.get("stop_loss"),
                        "target": p.get("take_profit"), "agents": p.get("agents"),
                        "independent_evidence": p.get("independent_evidence")})
        return out

    def decision_detail(self, did: str) -> dict | None:
        row = self.db.one("SELECT payload FROM decisions WHERE id=?", (did,))
        if not row:
            return None
        reports = {r["agent"]: json.loads(r["payload"]) for r in
                   self.db.query("SELECT agent, payload FROM agent_reports WHERE decision_id=?", (did,))}
        verdict = self.db.one("SELECT payload FROM risk_verdicts WHERE decision_id=?", (did,))
        intent = self.db.one("SELECT * FROM intents WHERE decision_id=?", (did,))
        trade = self.db.one("SELECT payload FROM trades WHERE decision_id=?", (did,))
        episode = self.db.one("SELECT payload FROM episodes WHERE decision_id=?", (did,))
        return {"decision": json.loads(row["payload"]), "agents": reports,
                "risk": json.loads(verdict["payload"]) if verdict else None,
                "execution": ({k: intent[k] for k in ("id", "status", "broker_order_id")} | {"history": json.loads(intent["payload"]).get("history")}) if intent else None,
                "trade": json.loads(trade["payload"]) if trade else None,
                "episode": json.loads(episode["payload"]) if episode else None}

    def market(self) -> list[dict]:
        out = []
        now = self.clock()
        open_syms = {r["symbol"]: r["side"] for r in self.db.query("SELECT symbol, side FROM positions WHERE status='OPEN'")}
        for s in self.cfg.symbols:
            st = self.orch.status["symbols"].get(s, {})
            q = self.feed.quote(s, now) if hasattr(self.feed, "quote") else None
            out.append({"symbol": s, "bid": q.bid if q else None, "ask": q.ask if q else None,
                        "spread": (q.ask - q.bid) if q else None, "quote_time": q.time if q else None,
                        "regime": st.get("regime"), "vol": st.get("vol"), "familiar": st.get("familiar"),
                        "decision": st.get("decision"), "reason": st.get("reason"), "last_decision_t": st.get("t"),
                        "exposure": open_syms.get(s)})
        return out

    def bars(self, symbol: str, n: int = 200) -> dict:
        b = self.feed.bars(symbol, self.clock(), n)
        if b is None:
            return {"symbol": symbol, "available": False, "bars": []}
        rows = [{"t": int(b.open_time[i]), "o": float(b.mid_open[i]), "h": float(b.mid_high[i]),
                 "l": float(b.mid_low[i]), "c": float(b.mid_close[i]), "v": int(b.ticks[i])} for i in range(len(b))]
        marks = [{"t": d["time"], "decision": d["decision"], "entry": d["entry"], "stop": d["stop"], "target": d["target"]}
                 for d in self.decisions(100, symbol) if d["decision"] != "NO_TRADE"]
        open_pos = [t for t in self.trades(closed=False) if t["symbol"] == symbol]
        return {"symbol": symbol, "available": True, "bars": rows, "marks": marks, "open": open_pos}

    def memory_view(self) -> dict:
        count = lambda t, w="": (self.db.one(f"SELECT COUNT(*) AS n FROM {t} {w}") or {}).get("n", 0)
        lessons = {}
        for lid, versions in self.experience.lessons.items():
            lessons[lid] = versions[-1]
        by_status: dict = {}
        for v in lessons.values():
            by_status[v["status"]] = by_status.get(v["status"], 0) + 1
        refl = self.db.one("SELECT payload, ts FROM reflections ORDER BY seq DESC LIMIT 1")
        return {
            "episodic": {"decisions": count("decisions"), "trades": count("trades"), "episodes": count("episodes"),
                         "no_trade_episodes": count("episodes", "WHERE kind='NO_TRADE'"),
                         "postmortems": count("postmortems")},
            "pattern": {"patterns": len(self.memory), "version": self.memory.version,
                        "knowledge_base": self.knowledge_meta},
            "semantic": {"lessons": list(lessons.values())[-50:], "by_status": by_status,
                         "knowledge_version": self.orch.knowledge_version},
            "reflection": json.loads(refl["payload"]) if refl else None,
            "performance": self.experience.summary(),
            "chains": {t: self.db.verify_chain(t)[0] for t in ("decisions", "trades", "episodes", "lessons", "events")},
        }

    def research(self) -> dict:
        from ..research.registry import Holdout, Registry
        reg = Registry.load(ROOT / "research" / "registry.jsonl", Holdout.load(ROOT / "research" / "holdout.json"))
        trials = [{"id": t.id, "title": t.title, "status": reg.status_of(t.id), "tests": t.tests,
                   "registered": t.registered.isoformat(), "preregistration": t.preregistration,
                   "result": (reg.verdict_of(t.id).result if reg.verdict_of(t.id) else t.result)} for t in reg.trials]
        summary = ROOT / "research" / "results" / "PR-001-summary.json"
        return {"trials": trials, "holdout": {"start": str(reg.holdout.start), "spent": reg.holdout_spent()},
                "next_threshold_t": round(reg.threshold_for_next(reg.holdout.universe), 3),
                "pr001": json.loads(summary.read_text()) if summary.exists() else None}

    def events(self, since: int = 0, limit: int = 200) -> list[dict]:
        rows = self.db.query("SELECT seq, ts, type, ref, payload FROM events WHERE seq>? ORDER BY seq DESC LIMIT ?",
                             (since, limit))
        return [{"seq": r["seq"], "ts": r["ts"], "type": r["type"], "ref": r["ref"], "payload": json.loads(r["payload"])}
                for r in rows]

    def logs(self) -> list[dict]:
        return recent(100)
