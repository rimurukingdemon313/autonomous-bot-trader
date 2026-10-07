"""The running system: wiring, scheduler, position monitor, and read models.

MODE=PAPER is the only mode: public market data (Yahoo Finance, estimated
spreads) and a simulated paper account; orders never leave the process. No
broker is integrated (the TradeLocker integration was removed); a MetaTrader 5
adapter is planned once a strategy shows positive forward evidence in paper.

With DATA_SOURCE=offline the system still starts, serves the dashboard and
health, and reports DATA: NOT CONNECTED — it does not trade on invented
prices (rule: never fabricate a value).

Startup sequence: open the database -> load knowledge -> reconcile broker
state (before any decision) -> start the scheduler. If reconciliation
fails, trading starts PAUSED and the dashboard says why.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import threading
import time
import traceback
from pathlib import Path

import numpy as np

from ..agents.brain import MODEL_MODES, Brain, BrainConfig
from ..agents.trading_room import member_records
from ..data.calendar import EconomicCalendar
from ..memory.history import HistoryDesk
from ..backtest.metrics import summarise
from ..broker.paper import PaperBroker
from ..decision.synthesis import EvidenceSynthesizer
from ..execution.engine import ExecutionEngine
from ..learning.experience import ExperienceView
from ..learning import metrics as fwd_metrics
from ..learning.forward import partition as fwd_partition
from ..llm.provider import LLMClient, LLMConfig
from ..memory.db import Database
from ..memory.patterns import PatternMemory
from ..memory.trade_memory import TradeMemory
from ..observability import log_event, recent
from ..orchestrator.core import Orchestrator, OrchestratorConfig
from ..orchestrator.tracker import ACTIONS
from ..regime.model import RegimeModel
from ..risk.engine import RiskEngine
from ..risk.hard_gate import HardRiskGate
from ..decision.edge_status import PAPER_MODES
from ..learning import paper_metrics
from ..version import stamp
from .config import ServiceConfig, ServiceConfigError

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "models" / "artifacts"


def storage_state(data_dir: str, env=None) -> dict:
    """Whether the database survives a redeploy, from what the platform itself says.

    Railway sets RAILWAY_VOLUME_MOUNT_PATH only when a volume is attached. Without one, every
    redeploy starts from an empty disk: the paper account back to its start balance, every trade,
    lesson and reflection gone. That must be visible on the dashboard, not discovered afterwards.
    Off Railway nothing here can tell, so it says UNKNOWN rather than guessing."""
    e = os.environ if env is None else env
    mount = (e.get("RAILWAY_VOLUME_MOUNT_PATH") or "").strip()
    on_railway = any(e.get(k) for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_PROJECT_ID",
                                        "RAILWAY_SERVICE_ID"))
    here = Path(data_dir).resolve()
    if mount:
        m = Path(mount).resolve()
        if here == m or m in here.parents:
            return {"status": "PERSISTENT", "detail": f"Railway volume at {mount}"}
        return {"status": "NOT PERSISTENT",
                "detail": f"DATA_DIR {data_dir} is not on the volume ({mount}): a redeploy erases the account"}
    if on_railway:
        return {"status": "NOT PERSISTENT",
                "detail": "no Railway volume attached: a redeploy resets the paper account and erases every "
                          "trade and lesson. Add a Volume with mount path /data"}
    return {"status": "UNKNOWN", "detail": "not on Railway: whether this disk survives a restart is not known here"}

#: 1.1.0: decide only every `decision_every_bars` H1 closes (the tested cadence);
#: bookkeeping still runs every hour. 1.0.0 decided every hour.
#: 1.2.0: DECISION_MODE (evidence | llm_trader); the model trader's record in status.
#: 1.3.0: DECISION_MODE=trading_room; the room's members and each member's record in status.
#: 1.4.0: DECISION_INTERVAL_MIN / SYMBOLS_PER_CYCLE for the model-trader modes; open paper
#: positions are checked on M1 bars between H1 closes; live memory saved at most every 15 min.
#: 1.5.0: DATA reads CONNECTED only when bars arrive (quotes alone: QUOTES ONLY, NO BARS, with the
#: reason); a pair with no data shows NO_DATA and why.
#: 1.6.0: SCAN_TIMEFRAME=M15 (the opportunity scanner: every M15 close, H1/H4 as context) and
#: DECISION_MODE=edges (promoted edges only); the evidence system keeps its tested H1 cadence.
#: 1.7.0: LIVE_TRADING / PAPER_MODE / EXPERIMENTAL_EXECUTE; startup reconciliation also reads the account
#: and lists journal positions the broker no longer holds; the forward ledger resolves every 5 minutes;
#: /readyz, /metrics, /api/evidence, /api/lessons.
SERVICE_VERSION = "service-1.7.0"
#: modes that may decide more often than the evidence system's tested H1 cadence
FLEX_MODES = MODEL_MODES + ("edges",)
FAST_DELAY_S = 15       # after a minute boundary, give the broker time to publish the M1/M5 bar
MEMORY_SAVE_EVERY_S = 900
FORWARD_EVERY_S = 300  # forward-ledger resolution cadence (reads only)


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


class Runtime:
    def __init__(self, cfg: ServiceConfig, *, feed=None, broker=None, clock=None,
                 knowledge_dir: Path | None = None) -> None:
        self.cfg = cfg
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir is not None else KNOWLEDGE_DIR
        self.started = time.time()
        self.clock = clock or (lambda: int(time.time()))
        Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
        self.db = Database(Path(cfg.data_dir) / "aitrader.db")
        self.storage = storage_state(cfg.data_dir)
        if self.storage["status"] == "NOT PERSISTENT":
            log_event("STARTUP", f"storage: {self.storage['detail']}", severity="warning")
        if self.db.get_kv("kill_switch", None) is None:
            self.db.set_kv("kill_switch", {"active": False}, reason="first start")
        if self.db.get_kv("paused", None) is None:
            if cfg.mode == "PAPER_FORWARD":
                # MODE=PAPER_FORWARD is itself the operator's explicit decision to let the system trade ON PAPER
                # and measure itself; it is set in the deployment's own configuration, never by the dashboard.
                self.db.set_kv("paused", False, reason="first start in PAPER_FORWARD: the paper forward test runs "
                                                       "(not real money; research status unchanged: NO EDGE)")
            else:
                # Nothing trades until an operator decides it should: PR-001 found no
                # edge, so starting to trade is an explicit, authenticated act (resume).
                self.db.set_kv("paused", True, reason="first start: paused until an operator resumes "
                                                      "(PR-001 found no demonstrated edge)")
        self.llm = LLMClient(LLMConfig.from_env())
        self.feed, self.broker = feed, broker
        if self.feed is None or self.broker is None:
            self._connect()
        self.memory, self.regime, self.knowledge_meta = self._load_knowledge()
        self.history, self.history_meta = self._load_history()
        self.experience = ExperienceView()
        self._replay_experience()
        # PAPER simulates every trade; DEMO sends an unvalidated trade only with EXPERIMENTAL_EXECUTE=true.
        # The hard risk gate (FTMO-style limits) is the last step before the paper broker; its state and its lock
        # live in the same database and survive a restart.
        self.gate = HardRiskGate(self.db, cfg.hard_profile, self.clock)
        self.execution = ExecutionEngine(self.db, self.broker, self.clock, gate=self.gate,
                                         allow_unvalidated=cfg.mode in PAPER_MODES or cfg.experimental_execute,
                                         max_decision_age_s=cfg.max_decision_age_s,
                                         paper_forward=cfg.mode == "PAPER_FORWARD")
        self.orch = Orchestrator(
            OrchestratorConfig(list(cfg.symbols), mode=cfg.mode, journal="full", events="all",
                               start_balance=cfg.start_balance, experimental_execute=cfg.experimental_execute),
            db=self.db, feed=self.feed, broker=self.broker,
            brain=Brain(llm=self.llm, synthesizer=EvidenceSynthesizer(), config=BrainConfig.from_env()),
            risk=RiskEngine(dataclasses.replace(cfg.risk, hard=cfg.hard_profile)), execution=self.execution, experience=self.experience,
            memory=self.memory, regime_for=lambda t: self.regime, clock=self.clock,
            # The calendar is read from the internet like the broker: only for a live feed.
            news=(EconomicCalendar(Path(cfg.data_dir) / "calendar_cache.json")
                  if cfg.data_source == "yahoo" else None),
            history=self.history,
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
        self._last_fast_seen: dict[str, int] = {}
        self._forward_at = 0
        self._rotation = 0
        self._memory_saved_at = 0.0
        if cfg.decision_interval_min and self.orch.brain.config.decision_mode not in FLEX_MODES:
            raise ServiceConfigError(
                f"DECISION_INTERVAL_MIN={cfg.decision_interval_min} applies only to DECISION_MODE=llm_trader, "
                "trading_room or edges: the evidence system runs at the cadence it was tested at (every "
                f"{self.decide_every_bars} H1 closes)")
        if cfg.scan_timeframe == "M15" and self.orch.brain.config.decision_mode not in FLEX_MODES:
            raise ServiceConfigError(
                "SCAN_TIMEFRAME=M15 applies only to DECISION_MODE=edges, llm_trader or trading_room: the evidence "
                f"system was tested deciding every {self.decide_every_bars} H1 closes, and a cadence it was never "
                "tested at would run a system whose trade frequency and overlap were never measured")
        self._reconcile_at_start()

    # ── wiring ──────────────────────────────────────────────────────────

    def _connect(self) -> None:
        if self.cfg.data_source == "yahoo":
            # PAPER on public prices: no broker session exists, so nothing can reach one.
            from ..data.yahoo import YahooFeed
            self.feed = YahooFeed(self.cfg.symbols, self.clock, spreads_pips=self.cfg.spreads_pips)
            log_event("STARTUP", "data source: Yahoo Finance (paper account, estimated spreads)")
        else:
            self.feed = OfflineFeed(self.cfg.symbols)
            log_event("STARTUP", "data source: offline (no prices: nothing will trade)", severity="warning")
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
        memory, meta["memory_source"] = None, "base"
        if live_mem.exists():
            try:
                memory = PatternMemory.load(live_mem)
                meta["memory_source"] = "live (grown forward from the verified base)"
            except Exception as exc:
                # An unreadable live copy (cut off by a stop mid-write, before saves were atomic) must
                # not stop the service: it is set aside, kept for inspection, and the verified base
                # is used. What is lost is the patterns grown since the base; that is said, not hidden.
                aside = live_mem.with_name(f"memory_live.unreadable-{int(time.time())}.npz")
                try:
                    live_mem.replace(aside)
                except OSError:
                    aside = live_mem
                meta["memory_source"] = (f"base (the live copy could not be read: {type(exc).__name__}; "
                                         f"kept as {aside.name}; patterns grown since the base are not in use)")
                log_event("STARTUP", f"memory_live.npz unreadable ({type(exc).__name__}: {exc}): set aside as "
                          f"{aside.name}, using the verified base memory", severity="critical")
        if memory is None:
            memory = PatternMemory.load(mem_path)
        return memory, RegimeModel.from_json(reg_path.read_text()), meta

    def _load_history(self):
        """The history desk's reference memory, only if it matches its card; else the verified base memory.

        A missing or mismatched history.npz never loads: the desk then reads the
        knowledge base's own (verified) memory, and status says which one it uses.
        """
        kdir = self.knowledge_dir
        path, card = kdir / "history.npz", kdir / "history_card.json"
        if path.exists() and card.exists():
            meta = json.loads(card.read_text())
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest == meta.get("sha256"):
                desk = HistoryDesk(PatternMemory.load(path), "history.npz (every H1 bar, 2007-2016)")
                return desk, {"integrity": "VERIFIED", "version": meta.get("version"), **desk.size()}
            log_event("STARTUP", "history.npz does not match its card: not loaded", severity="critical",
                      expected=str(meta.get("sha256"))[:16], actual=digest[:16])
            reason = "MISMATCH"
        else:
            reason = "MISSING"
        if self.regime is not None and len(self.memory):
            desk = HistoryDesk(self.memory, "knowledge base memory (one situation every 4 H1 bars)")
            return desk, {"integrity": f"FALLBACK (history.npz {reason})", **desk.size()}
        return None, {"integrity": reason}

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
        """Before anything can trade: order intents left SUBMITTING/UNKNOWN are resolved by querying the
        broker (never resent), broker positions this journal does not know are orphans, journal positions
        the broker no longer holds are listed, and the account balance is read. Any error, orphan or
        unreadable account pauses trading until an operator looks."""
        try:
            rep = self.execution.reconcile()
            try:
                known_open = {r["id"] for r in self.db.query("SELECT id FROM positions WHERE status='OPEN'")}
                at_broker = {p.id for p in self.broker.positions()}
                rep["missing_at_broker"] = sorted(known_open - at_broker)  # closed while we were down: synced next cycle
                snap = self.broker.account()
                rep["account"] = {"equity": snap.equity, "balance": snap.balance, "currency": snap.currency}
            except Exception as exc:
                rep["account"] = None
                rep.setdefault("error", f"account/positions unreadable: {type(exc).__name__}: {exc}")
            self.health["reconcile"] = {"t": self.clock(), **rep}
            if rep.get("error") or rep.get("orphans") or rep.get("still_unknown"):
                why = rep.get("error") or ("orphan positions" if rep.get("orphans") else
                                           f"{len(rep['still_unknown'])} order(s) of unknown outcome")
                self.db.set_kv("paused", True, reason=f"startup reconciliation: {why}")
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

    @property
    def decision_interval_s(self) -> int | None:
        """Seconds between decisions: 900 for the M15 scanner, DECISION_INTERVAL_MIN in the model modes, else
        None (the H1 clock at the tested cadence)."""
        if self.cfg.scan_timeframe == "M15":
            return 900  # every M15 close (+ FAST_DELAY_S for the broker to publish it)
        return self.cfg.decision_interval_min * 60 if self.cfg.decision_interval_min else None

    def _cycle_symbols(self) -> list[str] | None:
        """The pairs this decision cycle analyses: all of them, or the next SYMBOLS_PER_CYCLE in rotation."""
        k, syms = self.cfg.symbols_per_cycle, list(self.cfg.symbols)
        if not k or k >= len(syms):
            return None
        pick = [syms[(self._rotation + i) % len(syms)] for i in range(k)]
        self._rotation = (self._rotation + k) % len(syms)
        return pick

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
            rep = self.orch.cycle(t, self._cycle_symbols() if decide else [])
            self.health.update(last_cycle=t, last_cycle_error=None, cycles=self.health["cycles"] + 1)
            if time.time() - self._memory_saved_at >= MEMORY_SAVE_EVERY_S:
                self.memory.save(Path(self.cfg.data_dir) / "memory_live.npz")
                self._memory_saved_at = time.time()
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
        self._monitor_fast(now)
        self.orch.time_exits(now)  # a holding time of minutes is honoured between cycles
        if now - self._forward_at >= FORWARD_EVERY_S:  # forward outcomes resolve as bars complete
            self._forward_at = now
            self.health["forward"] = {"t": now, **self.orch.forward_tick(now)}
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

    def _monitor_fast(self, now: int) -> None:
        """Open PAPER positions: apply completed M1 bars, so a stop or target is hit within
        the minute rather than at the next H1 close. A broker account (DEMO) holds its own
        stops and targets; bars before the position opened are ignored by the paper broker."""
        if not hasattr(self.broker, "on_bar") or not hasattr(self.feed, "bars_tf"):
            return
        open_syms = {p.symbol for p in self.broker.positions()}
        for s in open_syms:
            # 60 minutes back: while the team deliberates (minutes, with free models) this loop
            # waits, and no completed minute may be skipped; already-applied bars are filtered.
            bars = self.feed.bars_tf(s, "M1", now, 60)
            if bars is None or len(bars) == 0:
                continue
            for i in range(len(bars)):
                close_t = int(bars.available_at[i])
                if close_t <= self._last_fast_seen.get(s, 0):
                    continue
                self._last_fast_seen[s] = close_t
                self.broker.on_bar(s, {"open_time": int(bars.open_time[i]), "close_time": close_t,
                                       **{f: float(getattr(bars, f)[i]) for f in (
                                           "bid_open", "bid_high", "bid_low", "bid_close",
                                           "ask_open", "ask_high", "ask_low", "ask_close")}})

    def _loop(self) -> None:
        next_cycle = self._next_cycle_time()
        next_decision = self._next_decision_time()
        while not self._stop.is_set():
            try:
                self.monitor_once()
                now = self.clock()
                if next_decision is not None:
                    # Frequent cadence: every cycle decides, and carries the hourly bookkeeping.
                    if now >= next_decision:
                        self.run_cycle(decide=True)
                        next_decision = self._next_decision_time()
                elif now >= next_cycle:
                    self.run_cycle(decide=self.is_decision_hour(next_cycle))
                    next_cycle = self._next_cycle_time()
            except Exception as exc:
                self.health["last_cycle_error"] = f"{type(exc).__name__}: {exc}"
            self._stop.wait(min(self.cfg.monitor_interval_s, 5) if next_decision is not None
                            else self.cfg.monitor_interval_s)

    def _next_decision_time(self) -> int | None:
        iv = self.decision_interval_s
        if iv is None:
            return None
        now = self.clock()
        return (now // iv + 1) * iv + FAST_DELAY_S

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
        except Exception as exc:  # said, not swallowed: patterns grown since the last save are lost
            log_event("SHUTDOWN", f"live memory not saved: {type(exc).__name__}: {exc}", severity="critical")

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
        broker_state = "PAPER (simulated)" if isinstance(self.broker, PaperBroker) else "NOT CONNECTED"
        demo = None  # no broker account exists (PAPER only)
        feed_ok = getattr(self.feed, "last_ok", None)
        ks = self.db.get_kv("kill_switch", None)
        return {
            "system": "ONLINE" if db_ok else "DEGRADED", "mode": self.cfg.mode, "time": now,
            "uptime_s": int(time.time() - self.started),
            "components": {
                "data": self._data_state(now, feed_ok),
                "broker": broker_state, "demo_verification": demo,
                "ai": ("READY" if self.llm.config.enabled else "QUANT ONLY (no LLM configured)"),
                "ai_providers": self.llm.health().get("by_provider", {}),
                "data_source": self.cfg.data_source,
                "decision_mode": self.orch.brain.config.decision_mode,
                "decision_interval_min": self.cfg.decision_interval_min or None,
                "history_desk": self.history_meta,
                "news_calendar": (self.orch.news.state(refresh=False) if self.orch.news is not None else {"status": "NOT_CONFIGURED"}),
                "symbols_per_cycle": self.cfg.symbols_per_cycle or len(self.cfg.symbols),
                "ai_trader_record": (TradeMemory(self.db).record()
                                     if self.orch.brain.config.decision_mode in MODEL_MODES else None),
                "trading_room": ({"members": self.orch.brain.room.members(),
                                  "head": self.orch.brain.config.room.head or None,
                                  "records": member_records(self.db)}
                                 if self.orch.brain.config.decision_mode == "trading_room" else None),
                "database": "HEALTHY" if db_ok else "UNAVAILABLE", "db_latency_ms": db_ms,
                "storage": self.storage,
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

    # ── forward evidence, lessons, readiness, metrics ───────────────────

    def _baseline(self) -> float | None:
        """The unconditional baseline: the mean shadow R of the declared template entries (both directions,
        every decision point) over EVALUATION weeks. None until such outcomes exist."""
        xs = []
        for r in self.db.query("SELECT payload FROM evaluations"):
            for e in json.loads(r["payload"]).get("evaluations", []):
                if fwd_partition(e["decision_time"]) == "EVALUATION" and e.get("outcome_r") is not None:
                    xs.append(float(e["outcome_r"]))
        return round(float(np.mean(xs)), 4) if xs else None

    def evidence(self) -> dict:
        """Everything the forward ledger knows, by every dimension that could hide a concentration.
        Labels: nothing here is VALIDATED unless research and an operator promoted it."""
        rows = self.orch.forward.rows(as_of=self.clock())
        learn = [r for r in rows if r["partition"] == "LEARNING"]
        ev = [r for r in rows if r["partition"] == "EVALUATION"]
        baseline = self._baseline()
        by_class = {}
        for sc in sorted({r.get("signal_class") or "?" for r in rows}):
            sub = [r for r in rows if (r.get("signal_class") or "?") == sc]
            by_class[sc] = {"all": fwd_metrics.stats(sub), "learning": fwd_metrics.stats([r for r in sub if r["partition"] == "LEARNING"]),
                            "eligibility": fwd_metrics.eligibility(sub, baseline)}
        return {
            "version": fwd_metrics.METRICS_VERSION,
            "statement": ("Forward evidence, after costs. No edge is VALIDATED: every trade here is EXPERIMENTAL "
                          "unless it came from a promoted, validated edge. ELIGIBLE_FOR_REVIEW is the most forward "
                          "data can say."),
            "partition_rule": "every third ISO week is EVALUATION; lessons and model memory read LEARNING only",
            "ledger": dict(self.orch.forward.stats),
            "all": fwd_metrics.stats(rows), "learning": fwd_metrics.stats(learn), "evaluation": fwd_metrics.stats(ev),
            "baseline_evaluation_mean_r": baseline,
            "by_signal_class": by_class,
            # Track A (deterministic) vs Track B (the same minus the advisory model's would-be vetoes)
            "ai_veto_ab": fwd_metrics.ai_veto_ab(rows),
            "by_route": fwd_metrics.breakdown(rows, lambda r: r.get("route")),
            "by_edge_status": fwd_metrics.breakdown(rows, lambda r: r.get("edge_status")),
            "by_symbol": fwd_metrics.breakdown(rows, lambda r: r["symbol"]),
            "by_model": fwd_metrics.breakdown(rows, lambda r: r.get("model") or "none"),
            "by_regime": fwd_metrics.breakdown(rows, lambda r: r.get("regime") or "?"),
            "by_timeframe": fwd_metrics.breakdown(rows, lambda r: r.get("timeframe") or "?"),
            "by_session": fwd_metrics.breakdown(rows, lambda r: r.get("session") or "?"),
            "calibration_by_model": {m: fwd_metrics.calibration([r for r in rows if (r.get("model") or "none") == m])
                                     for m in sorted({r.get("model") or "none" for r in rows})},
            "daily": fwd_metrics.periods(rows, "%Y-%m-%d"), "weekly": fwd_metrics.periods(rows, "%G-W%V"),
            "monthly": fwd_metrics.periods(rows, "%Y-%m"),
            "recent": [{k: r.get(k) for k in ("decision_id", "symbol", "t", "side", "signal_class", "edge_status", "route",
                                              "model", "confidence", "partition", "timeframe")}
                       | {"outcome": (r["outcome"] or {}).get("reason") if r.get("outcome") else "PENDING",
                          "net_r": (r.get("outcome") or {}).get("net_r"), "cost_r": (r.get("outcome") or {}).get("cost_r")}
                       for r in rows[-30:][::-1]],
        }

    def lessons(self) -> dict:
        latest = self.orch.lesson_book.latest()
        return {"forward": sorted(latest.values(), key=lambda v: (v["status"] != "ACTIVE", v["code"], v["scope"])),
                "counts": {s: sum(1 for v in latest.values() if v["status"] == s) for s in ("CANDIDATE", "ACTIVE", "REJECTED")},
                "rule": ("CANDIDATE from LEARNING outcomes; ACTIVE only after confirmation on EVALUATION outcomes that "
                         "resolved later; an ACTIVE lesson is information for the models, never a rule or a size"),
                "experience": self.experience.summary() if hasattr(self.experience, "summary") else None}

    def readiness(self) -> dict:
        """Ready = may make decisions safely now. Paused is a valid state (ready, not trading)."""
        reasons = []
        try:
            self.db.ping()
        except Exception:
            reasons.append("database unavailable")
        if self.regime is None:
            reasons.append(f"knowledge base {self.knowledge_meta.get('integrity', 'MISSING')}: no regime model")
        rec = self.health.get("reconcile")
        if rec is None:
            reasons.append("startup reconciliation has not run")
        elif rec.get("error"):
            reasons.append(f"startup reconciliation: {rec['error']}")
        ks = self.db.get_kv("kill_switch", None)
        if not isinstance(ks, dict) or "active" not in ks:
            reasons.append("kill switch unreadable (treated as active)")
        try:
            self.broker.account()
        except Exception as exc:
            reasons.append(f"broker account unreadable: {type(exc).__name__}")
        return {"ready": not reasons, "reasons": reasons, "mode": self.cfg.mode, "live_trading": False,
                "paused": bool(self.db.get_kv("paused", False)), "halted": bool(self.db.get_kv("halted", False)),
                "kill_switch": ks}

    def metrics_text(self) -> str:
        """Prometheus text format. Counters and gauges only; no secret and no free text."""
        st = self.status()
        rows = self.orch.forward.rows(as_of=self.clock())
        s = fwd_metrics.stats(rows)
        lines = []

        def g(name, value, help_, labels=""):
            lines.append(f"# HELP aitrader_{name} {help_}")
            lines.append(f"# TYPE aitrader_{name} gauge")
            v = "NaN" if value is None else (1 if value is True else 0 if value is False else value)
            lines.append(f"aitrader_{name}{labels} {v}")

        g("up", 1, "the service is running")
        g("ready", self.readiness()["ready"], "ready to make decisions safely")
        g("paused", bool(st["paused"]), "trading paused")
        g("halted", bool(st["halted"]), "halted by the risk engine")
        g("kill_switch", (st["kill_switch"] or {}).get("active", True) if isinstance(st["kill_switch"], dict) else True,
          "kill switch active (unreadable counts as active)")
        g("live_trading", 0, "live trading: always 0, there is no live path")
        for k, v in self.orch.counts.items():
            g(f"decisions_{k}", v, f"orchestrator count: {k}")
        g("forward_proposals", len(rows), "forward proposals recorded")
        g("forward_resolved", s["n"], "forward outcomes resolved with an R")
        g("forward_net_r_total", s.get("net_r_total"), "sum of net R over resolved forward outcomes")
        g("forward_cost_r_total", s.get("cost_r_total"), "sum of cost R over resolved forward outcomes")
        g("forward_expectancy_r", s.get("expectancy_r"), "mean net R per resolved forward outcome")
        llm = self.llm.health()
        g("llm_calls_today", llm.get("calls_today", 0), "language-model calls today")
        g("llm_failed_total", llm.get("failed", 0), "language-model calls failed")
        for name, p in (llm.get("by_provider") or {}).items():
            lab = '{provider="%s"}' % "".join(ch for ch in name if ch.isalnum() or ch in "_-")
            g("llm_provider_ok", p.get("ok", 0), "calls answered by provider", lab)
            g("llm_provider_failed", p.get("failed", 0), "calls failed by provider", lab)
            g("llm_provider_tokens", (p.get("prompt_tokens") or 0) + (p.get("completion_tokens") or 0),
              "tokens used by provider", lab)
            g("llm_provider_cost_usd", p.get("est_cost_usd"), "estimated cost (NaN = not priced)", lab)
        return "\n".join(lines) + "\n"

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

    def _live_positions(self) -> list[dict]:
        """Open positions for the live panel: levels, R now, the P/L the broker values them at (None
        when it cannot), and what the team said when it opened them (holding time, timeframe, thesis)."""
        pnl = self.broker.unrealised_by_position() if hasattr(self.broker, "unrealised_by_position") else {}
        out = []
        for t in self.trades(closed=False):
            dec = self.db.one("SELECT payload FROM decisions WHERE id=?", (t["decision_id"],)) if t.get("decision_id") else None
            d = json.loads(dec["payload"]) if dec else {}
            hold = d.get("max_hold_minutes") or ((d.get("max_hold_hours") or 0) * 60) or None
            out.append({**{k: t[k] for k in ("id", "symbol", "side", "qty", "entry", "current", "stop", "target", "r_now",
                                            "opened")},
                        "pnl": None if pnl.get(t["id"]) is None else round(pnl[t["id"]], 2),
                        "max_hold_minutes": hold, "timeframe": d.get("timeframe"),
                        "method": (((d.get("independent_evidence") or {}).get("room") or {}).get("joint") or {}).get("method"),
                        "thesis": str(d.get("thesis") or "")[:240] or None})
        return out

    def live(self) -> dict:
        """The few numbers the live panel polls every couple of seconds: cheap by design (no
        performance summary, no history scan). Every value is read, never estimated; one that cannot
        be read is None, with the reason."""
        now = self.clock()
        try:
            snap = self.broker.account()
        except Exception as exc:
            return {"available": False, "reason": f"{type(exc).__name__}: {exc}", "time": now}
        eq, bal = snap.equity, snap.balance
        ds = self.db.get_kv("day_start", None) or {}
        day = ds.get("day")
        recent = self.trades(closed=True, limit=200)
        today = [t for t in recent if day is not None and t["closed"] is not None and t["closed"] >= day]
        last = self.db.one("SELECT symbol, decision, payload FROM decisions ORDER BY seq DESC LIMIT 1")
        lp = json.loads(last["payload"]) if last else {}
        return {
            "available": True, "time": now, "currency": snap.currency,
            "start_balance": self.cfg.start_balance, "balance": bal, "equity": eq,
            "floating_pnl": round(eq - bal, 2), "total_pnl": round(eq - self.cfg.start_balance, 2),
            "daily_pnl": round(eq - ds["equity"], 2) if ds.get("equity") else None,
            "positions": self._live_positions(),
            "today": {"trades": len(today), "wins": sum(1 for t in today if (t["r"] or 0) > 0),
                      "pnl": round(sum(t["pnl"] for t in today if t["pnl"] is not None), 2)} if day is not None else None,
            "last_trade": ({k: recent[0][k] for k in ("symbol", "side", "r", "pnl", "exit_reason", "closed")}
                           if recent else None),
            "last_decision": ({"symbol": last["symbol"], "decision": last["decision"], "time": lp.get("timestamp"),
                               "reason": lp.get("no_trade_reason") or lp.get("thesis")} if last else None),
        }

    def paper_forward(self) -> dict:
        """The PAPER FORWARD TEST panel: what the system's own paper trades did, read from the account, the
        hard gate and the closed-trade outcomes. Every figure is read; one that cannot be is None, with why.
        Presentation only: nothing here can open, size or close a trade."""
        out: dict = {"mode": self.cfg.mode, "banner": "PAPER FORWARD TEST", "money": "NOT REAL MONEY",
                     "active": self.cfg.mode == "PAPER_FORWARD", "live_trading": False,
                     "research_status": "NO EDGE — DO NOT TRADE (historical research; this test measures forward)",
                     "profile": self.cfg.hard_profile.name, "start_balance": self.cfg.hard_profile.starting_balance}
        gate = self.gate.status()
        out["risk_status"] = gate.get("risk_status") or gate.get("state")
        out["gate"] = {k: gate.get(k) for k in ("state", "risk_status", "lock", "day_lock", "kill",
                                                "daily_limit_violations", "ftmo_rules_passed_so_far", "day",
                                                "trading_days", "min_trading_days", "challenge_target",
                                                "challenge_objective_met")}
        paused = bool(self.db.get_kv("paused", True))
        ks = self.db.get_kv("kill_switch", None)
        killed = not isinstance(ks, dict) or ks.get("active") is not False
        locked = out["risk_status"] in ("DAILY_LOCK", "MAX_LOSS_LOCK", "KILLED", "FAULT")
        out["bot_status"] = ("RISK LOCK" if killed or locked else "PAUSED" if paused else
                             "STARTING" if out["risk_status"] == "NOT_STARTED" else "RUNNING")
        try:
            snap = self.broker.account()
            eq = snap.equity
            start = self.cfg.hard_profile.starting_balance
            day = (gate.get("day") or {})
            out["account"] = {"equity": round(eq, 2), "balance": round(snap.balance, 2),
                              "total_pnl": round(eq - start, 2),
                              "today_pnl": round(eq - day["reference"], 2) if day.get("reference") else None,
                              "day_reference": day.get("reference"),
                              "drawdown_from_start": round(min(0.0, eq - start), 2),
                              "max_loss_floor": self.cfg.hard_profile.total_loss_floor,
                              "daily_loss_limit": self.cfg.hard_profile.daily_loss_limit}
        except Exception as exc:  # noqa: BLE001 - shown as unavailable, never as a number
            out["account"] = {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
        outcomes = []
        for row in self.db.query("SELECT payload FROM trades ORDER BY seq"):
            o = (json.loads(row["payload"]) or {}).get("outcome")
            if o:
                outcomes.append(o)
        out["performance"] = paper_metrics.report(outcomes)
        out["open_positions"] = self._live_positions()
        out["recent_trades"] = outcomes[-20:][::-1]
        out["pipeline"] = [json.loads(e["payload"]) for e in
                           self.db.query("SELECT payload FROM events WHERE type='PIPELINE' ORDER BY seq DESC LIMIT 20")]
        return out

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
                        "independent_evidence": p.get("independent_evidence"),
                        "edge_status": p.get("edge_status") or ("NONE" if r["decision"] == "NO_TRADE" else "UNLABELLED"),
                        "signal_class": p.get("signal_class"), "ai_verdict": p.get("ai_verdict"),
                        "ai_model": (p.get("ai") or {}).get("model"), "ai_provider": (p.get("ai") or {}).get("provider"),
                        "ai_latency_ms": (p.get("ai") or {}).get("latency_ms"),
                        "confidence_stated": ((p.get("ai") or {}).get("view") or {}).get("confidence"),
                        "reasons_against": ((p.get("ai") or {}).get("view") or {}).get("reasons_against"),
                        "cost_r": (p.get("cost_estimate") or {}).get("total_r"),
                        "timeframes": p.get("timeframes")})
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

    def _data_state(self, now: int, feed_ok) -> str:
        """CONNECTED only when the bars decisions need arrive; a live quote alone is not enough to
        decide, and saying CONNECTED then would hide why nothing trades."""
        if not feed_ok or now - feed_ok >= 1800:
            return "NOT CONNECTED"
        bars_ok = getattr(self.feed, "last_bars_ok", "n/a")
        if bars_ok == "n/a" or (bars_ok and now - bars_ok < 3 * 3600):
            return "CONNECTED"
        err = next((e for e in (getattr(self.feed, "data_error", lambda s: None)(s) for s in self.cfg.symbols) if e), None)
        return f"QUOTES ONLY, NO BARS ({err or 'no H1 bars received yet'})"

    def market(self) -> list[dict]:
        out = []
        now = self.clock()
        open_syms = {r["symbol"]: r["side"] for r in self.db.query("SELECT symbol, side FROM positions WHERE status='OPEN'")}
        for s in self.cfg.symbols:
            st = self.orch.status["symbols"].get(s, {})
            # One pair's failed price must not blank the whole table: that pair shows no
            # price and says why, the others still show theirs. Nothing is invented.
            try:
                q, q_err = (self.feed.quote(s, now) if hasattr(self.feed, "quote") else None), None
            except Exception as exc:
                q, q_err = None, f"{type(exc).__name__}: {exc}"[:160]
            out.append({"symbol": s, "bid": q.bid if q else None, "ask": q.ask if q else None,
                        "quote_error": q_err if q_err else (None if q else "no price available"),
                        "spread": (q.ask - q.bid) if q else None, "quote_time": q.time if q else None,
                        "regime": st.get("regime"), "vol": st.get("vol"), "familiar": st.get("familiar"),
                        "decision": st.get("decision") or st.get("state"), "reason": st.get("reason"),
                        "last_decision_t": st.get("t"),
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
        judgement = ROOT / "research" / "results" / "PR-001-judgement.json"
        verdicts = None
        if judgement.exists():
            j = json.loads(judgement.read_text())["verdicts"]
            verdicts = {k: v["verdict"] for k, v in j.items()}
        return {"trials": trials, "holdout": {"start": str(reg.holdout.start), "spent": reg.holdout_spent()},
                "next_threshold_t": round(reg.threshold_for_next(reg.holdout.universe), 3),
                "pr001": json.loads(summary.read_text()) if summary.exists() else None,
                "pr001_verdicts": verdicts,
                "proposals": [json.loads(r["payload"]) for r in self.db.query(
                    "SELECT payload FROM experiments ORDER BY seq DESC LIMIT 50")]}

    def events(self, since: int = 0, limit: int = 200) -> list[dict]:
        rows = self.db.query("SELECT seq, ts, type, ref, payload FROM events WHERE seq>? ORDER BY seq DESC LIMIT ?",
                             (since, limit))
        return [{"seq": r["seq"], "ts": r["ts"], "type": r["type"], "ref": r["ref"], "payload": json.loads(r["payload"])}
                for r in rows]

    def logs(self) -> list[dict]:
        return recent(100)
