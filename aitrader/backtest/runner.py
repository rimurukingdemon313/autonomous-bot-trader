"""Walk-forward backtest of the WHOLE system: the same orchestrator, replayed.

Timeline (all UTC, VALIDATION_CONTRACT.md):

    warmup_start ........ start ...................... end
    [memory seeded from   [judged: decisions, trades, learning, all
     labels; regime and    point-in-time; the regime model is refit at
     scaler fitted]        each year start on data before it - embargo]

Nothing here can read past `end`: the data store truncates at the sealed
holdout, and every component reads through the feed's `as_of`.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Callable

import numpy as np

from ..agents.brain import Brain, BrainConfig
from ..broker.paper import PaperBroker, pip_of
from ..data.bars import BarSeries
from ..data.feed import ReplayFeed
from ..decision.synthesis import EvidenceSynthesizer, SynthesisConfig
from ..execution.engine import ExecutionEngine
from ..features.store import compute_matrix
from ..learning.experience import ExperienceView
from ..memory.db import Database
from ..memory.patterns import PatternMemory
from ..orchestrator.core import Orchestrator, OrchestratorConfig
from ..orchestrator.tracker import ACTIONS
from ..regime.model import RegimeModel
from ..research.labels import BUY, SELL, CostModel, compute_labels
from ..risk.engine import RiskEngine, RiskLimits
from ..version import stamp
from .metrics import summarise

EMBARGO_S = 5 * 86400


def epoch(y: int, m: int = 1, d: int = 1) -> int:
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


@dataclass
class BacktestConfig:
    name: str
    symbols: list[str]
    warmup_start: int
    start: int
    end: int
    every: int = 4  # decide every N closed H1 bars per symbol
    synthesis: SynthesisConfig = field(default_factory=SynthesisConfig)
    learning_enabled: bool = True
    costs: CostModel = field(default_factory=CostModel)
    risk: RiskLimits = field(default_factory=RiskLimits)
    start_balance: float = 20_000.0
    db_path: str = ":memory:"
    journal: str = "trades"  # "full" also journals every NO_TRADE and shadow outcome, as the service does


class _Clock:
    def __init__(self, t: int) -> None:
        self.t = t

    def __call__(self) -> int:
        return self.t


def _regime_models(series: dict[str, BarSeries], mats: dict[str, np.ndarray], start: int, end: int) -> dict[int, RegimeModel]:
    """One model per test year, fitted on every row decided before that year (minus an embargo)."""
    models = {}
    for year in range(datetime.fromtimestamp(start, timezone.utc).year, datetime.fromtimestamp(end - 1, timezone.utc).year + 1):
        # Rows decided before the year began - or before the test began, if later - minus an embargo.
        cutoff = max(epoch(year), start) - EMBARGO_S
        rows, times = [], []
        for s, m in mats.items():
            t = series[s].available_at
            sel = t <= cutoff
            rows.append(m[sel])
            times.append(t[sel])
        models[year] = RegimeModel.fit(np.concatenate(rows), np.concatenate(times), trained_until=cutoff)
    return models


def seed_memory(series: dict[str, BarSeries], mats: dict[str, np.ndarray], warmup_start: int, start: int,
                every: int, costs: CostModel) -> PatternMemory:
    """Pattern memory from the warm-up years: the same outcomes the tracker would measure."""
    warm = []
    for s, m in mats.items():
        t = series[s].available_at
        warm.append(m[(t >= warmup_start) & (t < start)])
    mem = PatternMemory.fit_scaler(np.concatenate(warm), ACTIONS)
    for s, ser in series.items():
        t = ser.available_at
        rows = np.flatnonzero((t >= warmup_start) & (t < start))
        rows = rows[::every]
        if len(rows) == 0:
            continue
        lab = compute_labels(ser, pip_of(s), rows=rows, costs=costs)
        out = np.column_stack([lab.outcomes[(a.split(":")[0], BUY if a.endswith("BUY") else SELL)].r for a in ACTIONS])
        res = np.column_stack([lab.outcomes[(a.split(":")[0], BUY if a.endswith("BUY") else SELL)].resolve_time for a in ACTIONS])
        avail = np.where(np.all(res > 0, axis=1), res.max(axis=1), -1)
        mem.add(mats[s][rows], out, avail, s, t[rows])
    return mem


def run(cfg: BacktestConfig, series: dict[str, BarSeries], progress: Callable[[str], None] | None = None) -> dict:
    t_start = time.time()
    series = {s: v.between(cfg.warmup_start - 30 * 86400, cfg.end) for s, v in series.items() if s in cfg.symbols}
    mats = {s: compute_matrix(v) for s, v in series.items()}
    regimes = _regime_models(series, mats, cfg.start, cfg.end)
    memory = seed_memory(series, mats, cfg.warmup_start, cfg.start, cfg.every, cfg.costs)
    seeded = len(memory)

    clock = _Clock(cfg.start)
    db = Database(cfg.db_path)
    db.set_kv("kill_switch", {"active": False}, reason="backtest start")
    feed = ReplayFeed(series)
    broker = PaperBroker(feed, clock, db, start_balance=cfg.start_balance,
                         slippage_pips=cfg.costs.slippage_pips, commission_per_lot_rt=cfg.costs.commission_pips_rt * 10.0)
    brain = Brain(llm=None, synthesizer=EvidenceSynthesizer(cfg.synthesis), config=BrainConfig(llm_agents=(), parallel=False))
    execution = ExecutionEngine(db, broker, clock)
    experience = ExperienceView()
    versions = {**stamp(), "synthesis_mode": cfg.synthesis.mode, "learning": cfg.learning_enabled, "backtest": cfg.name}
    orch = Orchestrator(
        OrchestratorConfig(cfg.symbols, mode="BACKTEST", journal=cfg.journal, events="key",
                           start_balance=cfg.start_balance, costs=cfg.costs, learning_enabled=cfg.learning_enabled),
        db=db, feed=feed, broker=broker, brain=brain, risk=RiskEngine(replace(cfg.risk, max_quote_age_s=3600)),
        execution=execution, experience=experience, memory=memory,
        regime_for=lambda t: regimes[datetime.fromtimestamp(t, timezone.utc).year], clock=clock, versions=versions)

    # every H1 close in the judged window, across instruments, in time order
    closes = sorted({int(x) for v in series.values() for x in v.available_at if cfg.start <= x < cfg.end})
    counters = {s: 0 for s in series}
    for i, t in enumerate(closes):
        clock.t = t
        due = []
        for s in series:
            bar = feed.bar_closing_at(s, t)
            if bar is None:
                continue
            orch.on_bar_closed(s, bar)
            counters[s] += 1
            if counters[s] % cfg.every == 0:
                due.append(s)
        orch.cycle(t, due)
        if progress and i % 5000 == 0:
            progress(f"{cfg.name}: {datetime.fromtimestamp(t, timezone.utc):%Y-%m-%d} "
                     f"decisions {orch.counts['decisions']} trades {orch.counts['executed']} memory {len(memory)}")

    rows = db.query("SELECT payload, r, pnl, symbol FROM trades ORDER BY seq")
    trades = []
    for r in rows:
        p = json.loads(r["payload"])
        trades.append({"symbol": r["symbol"], "r": r["r"], "pnl": r["pnl"], "opened": p["position"]["opened"],
                       "closed": p["exit"]["time"], "exit_reason": p["exit"]["reason"],
                       "regime": ((p["decision"].get("regime") or {}).get("label")), "family": p["decision"].get("family"),
                       "cause": p["postmortem"]["cause"]})
    return {
        "name": cfg.name, "config": {"symbols": cfg.symbols, "warmup_start": cfg.warmup_start, "start": cfg.start,
                                     "end": cfg.end, "every": cfg.every, "synthesis": cfg.synthesis.__dict__,
                                     "learning_enabled": cfg.learning_enabled, "costs": cfg.costs.describe(),
                                     "risk": {k: v for k, v in cfg.risk.__dict__.items() if k != "funded"}},
        "versions": versions, "counts": orch.counts, "seeded_patterns": seeded, "final_patterns": len(memory),
        "metrics": summarise(trades, cfg.start_balance), "trades": trades,
        "learning": experience.summary(), "knowledge_version": orch.knowledge_version,
        "lessons": {lid: v[-1] for lid, v in experience.lessons.items()},
        "loss_causes": _count([t["cause"] for t in trades if (t["r"] or 0) < 0]),
        "chains_ok": all(db.verify_chain(tb)[0] for tb in ("trades", "episodes", "decisions")),
        "seconds": round(time.time() - t_start, 1),
    }


def _count(xs) -> dict:
    out: dict = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))
