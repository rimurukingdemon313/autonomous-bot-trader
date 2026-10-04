"""The multi-agent brain: runs the agents, the optional LLM layer, and synthesis.

Order and parallelism follow data dependencies, not a fixed script:

    market ─┐
            ├─> risk ────────┐
    setup ──┼─> adversary ───┼─> [LLM reviews, optional, parallel] ─> synthesis
            └─> reviewer ────┘

All five analysts report BEFORE synthesis; none of them sees the decision.

An agent that raises becomes an ERROR report and the decision fails closed.
LLM calls are made only when configured, only for the agents listed in
`llm_agents`, and only after the deterministic agents have run, so a
provider outage costs reasoning text, never safety.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..decision.synthesis import Decision, EvidenceSynthesizer
from ..llm.provider import LLMClient
from .analysts import (
    AdversarialAnalyst, MarketAnalyst, ReviewerAnalyst, RiskAnalyst, SetupAnalyst, validate_llm_review,
)
from .llm_trader import LLMTrader
from ..decision.edge_engine import load_promoted
from .edge_trader import edge_decision
from .experimental_ai import ExperimentalAI, ExperimentalConfig
from .trading_room import RoomConfig, TradingRoom
from .types import AGENT_VERSION, AgentReport, MarketContext, Objection

ROLE_PROMPTS = {
    "market": "You are the MARKET ANALYST. Describe what the evidence says about trend, momentum, "
              "volatility, liquidity and structure. You do not recommend trades.",
    "setup": "You are the SETUP ANALYST. Judge whether the leading candidate is a coherent trade "
             "given the evidence: entry, stop, target, invalidation.",
    "risk": "You are the RISK ANALYST. Your job is to find reasons NOT to trade: costs, conditions, "
            "exposure, event risk, data problems.",
    "adversary": "You are the ADVERSARIAL ANALYST. Assume the leading trade is wrong and argue why: "
                 "fake breakout, liquidity trap, weak structure, conflicting signals, overextension, "
                 "regime mismatch, data problems, overfitting. You never approve a trade.",
    "reviewer": "You are the EVIDENCE REVIEWER. Judge how far the evidence for each candidate can be "
                "trusted: sample size, noise, age, concentration, agreement, lessons. State which direction, "
                "if any, the evidence supports. NONE is a normal answer.",
}

SYSTEM_RULES = (
    "Use ONLY the evidence in the JSON you are given. The decision time is {time}. Treat it as the "
    "present: you must not use any knowledge of prices, news or events after that time, even if you "
    "have it. If evidence is missing, say so. Reply with ONE JSON object only: "
    '{{"stance": "SUPPORT|OPPOSE|NEUTRAL", "direction": "BUY|SELL|NONE", '
    '"objections": [{{"code": "<one of: {codes}>", "severity": "BLOCKING|MAJOR|MINOR", "reason": "..."}}], '
    '"summary": "at most 3 sentences"}}'
)


DECISION_MODES = ("evidence", "llm_trader", "trading_room", "edges", "experimental_ai")
#: The modes in which a language model proposes the trade (never backtestable; PAPER/DEMO only).
MODEL_MODES = ("llm_trader", "trading_room", "experimental_ai")


@dataclass
class BrainConfig:
    llm_agents: tuple[str, ...] = ("adversary", "reviewer")
    llm_required: bool = False
    agent_timeout_s: float = 10.0
    llm_timeout_s: float = 30.0
    parallel: bool = True
    #: "evidence": analogue-anchored synthesis (PR-001's system). "llm_trader": a language
    #: model proposes the trade (agents/llm_trader.py); PAPER/DEMO only, never backtested.
    decision_mode: str = "evidence"
    #: "trading_room": several models, one per provider, hunt, debate, and a head trader
    #: picks one member's trade verbatim (agents/trading_room.py). PAPER/DEMO only.
    room: RoomConfig = field(default_factory=RoomConfig)
    #: "experimental_ai": a proposer model, independent specialists, deterministic synthesis
    #: (agents/experimental_ai.py). Every trade it makes is EXPERIMENTAL. PAPER/DEMO only.
    experimental: ExperimentalConfig = field(default_factory=ExperimentalConfig)

    def __post_init__(self) -> None:
        if self.decision_mode not in DECISION_MODES:
            raise ValueError(f"DECISION_MODE must be one of {DECISION_MODES}, got {self.decision_mode!r}; "
                             "an unknown mode is refused, never replaced by a default")

    @classmethod
    def from_env(cls) -> "BrainConfig":
        agents = tuple(a.strip() for a in os.environ.get("AI_AGENTS", "adversary,reviewer").split(",") if a.strip())
        return cls(llm_agents=agents, llm_required=os.environ.get("AI_REQUIRED", "false").lower() == "true",
                   decision_mode=os.environ.get("DECISION_MODE", "evidence").strip().lower(),
                   room=RoomConfig.from_env(), experimental=ExperimentalConfig.from_env())


@dataclass
class Thought:
    decision: Decision
    reports: dict[str, AgentReport]
    llm_opinions: list[dict] = field(default_factory=list)
    timings_ms: dict = field(default_factory=dict)


class Brain:
    def __init__(self, llm: LLMClient | None = None, synthesizer: EvidenceSynthesizer | None = None,
                 risk: RiskAnalyst | None = None, adversary: AdversarialAnalyst | None = None,
                 config: BrainConfig | None = None, reviewer: ReviewerAnalyst | None = None) -> None:
        self.market = MarketAnalyst()
        self.setup = SetupAnalyst()
        self.risk = risk or RiskAnalyst()
        self.adversary = adversary or AdversarialAnalyst()
        self.reviewer = reviewer or ReviewerAnalyst()
        self.llm_trader = LLMTrader(llm)
        self.config = config or BrainConfig()
        self.room = TradingRoom(llm, self.config.room)
        self.experimental = ExperimentalAI(llm, self.config.experimental)
        self.synth = synthesizer or EvidenceSynthesizer()
        self.edges = load_promoted()[0] if self.config.decision_mode == "edges" else []
        self.llm = llm
        self._pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="agent") if self.config.parallel else None

    def _run(self, name: str, fn, *args) -> AgentReport:
        t0 = time.time()
        try:
            if self._pool is None:
                return fn(*args)
            return self._pool.submit(fn, *args).result(timeout=self.config.agent_timeout_s)
        except FutureTimeout:
            return AgentReport(name, AGENT_VERSION, "TIMEOUT", "NEUTRAL", t0, time.time(), error="agent timed out")
        except Exception as exc:  # an agent bug must not become a trade
            return AgentReport(name, AGENT_VERSION, "ERROR", "NEUTRAL", t0, time.time(),
                               error=f"{type(exc).__name__}: {exc}")

    def _parallel(self, jobs: dict[str, tuple]) -> dict[str, AgentReport]:
        if self._pool is None:
            return {k: self._run(k, *v) for k, v in jobs.items()}
        futures = {k: self._pool.submit(self._run_inline, k, *v) for k, v in jobs.items()}
        out = {}
        for k, f in futures.items():
            try:
                out[k] = f.result(timeout=self.config.agent_timeout_s)
            except FutureTimeout:
                out[k] = AgentReport(k, AGENT_VERSION, "TIMEOUT", "NEUTRAL", time.time(), time.time(), error="agent timed out")
        return out

    @staticmethod
    def _run_inline(name, fn, *args) -> AgentReport:
        t0 = time.time()
        try:
            return fn(*args)
        except Exception as exc:
            return AgentReport(name, AGENT_VERSION, "ERROR", "NEUTRAL", t0, time.time(),
                               error=f"{type(exc).__name__}: {exc}")

    def _packet(self, ctx: MarketContext, reports: dict[str, AgentReport]) -> dict:
        setup = reports.get("setup")
        cands = setup.candidates[:3] if setup else []
        return {
            "symbol": ctx.symbol, "timeframe": ctx.timeframe,
            "decision_time": datetime.fromtimestamp(ctx.t, timezone.utc).isoformat(),
            "regime": {k: v for k, v in ctx.regime.as_dict().items() if k != "reasons"},
            "features": {k: (round(v, 3) if v == v else None) for k, v in ctx.features.values.items()},
            "levels": ctx.levels,
            "candidates": [{"family": c.family, "action": c.action, "entry": c.entry, "stop": c.stop,
                            "target": c.target, "analogue_expectancy_R": c.expected_r,
                            "analogue_lower_R": c.lower_r, "analogue_win_rate": c.win_rate,
                            "n_analogues": c.n_analogs} for c in cands],
            "quant_objections": [{"code": o.code, "severity": o.severity, "message": o.message}
                                 for r in reports.values() for o in r.objections][:12],
            "market_summary": reports["market"].summary if "market" in reports else None,
        }

    def _llm_reviews(self, ctx: MarketContext, reports: dict[str, AgentReport]) -> list[dict]:
        if self.llm is None or not self.llm.config.enabled or not self.config.llm_agents:
            return []
        packet = self._packet(ctx, reports)
        from .types import OBJECTION_CODES
        system_tail = SYSTEM_RULES.format(time=packet["decision_time"], codes=", ".join(OBJECTION_CODES))
        opinions: list[dict] = []

        def call(agent: str):
            return agent, self.llm.complete_json(
                agent, ROLE_PROMPTS[agent] + "\n" + system_tail, {"role": agent, **packet},
                validate_llm_review, cache_key=f"{ctx.symbol}|{ctx.t}")

        agents = [a for a in self.config.llm_agents if a in ROLE_PROMPTS]
        results = list(self._pool.map(call, agents)) if self._pool else [call(a) for a in agents]
        for agent, res in results:
            target = reports.get(agent)
            if target is not None:
                target.llm = res.as_dict()
            if not res.ok:
                if self.config.llm_required:
                    host = reports.get(agent) or reports["adversary"]
                    host.objections.append(Objection("LLM_OBJECTION", "BLOCKING", f"{agent}+llm",
                                                     f"required language model unavailable ({res.status})"))
                opinions.append({"agent": f"{agent}_llm", "ok": False, "status": res.status})
                continue
            data = res.data or {}
            for o in data.get("objections", []):
                host = reports.get(agent) or reports["adversary"]
                host.objections.append(Objection(o["code"], o["severity"], f"{agent}+llm",
                                                 str(o.get("reason", ""))[:300]))
            opinions.append({"agent": f"{agent}_llm", "ok": True, "stance": data.get("stance"),
                             "direction": data.get("direction", "NONE"), "summary": data.get("summary", ""),
                             "model": res.model, "latency_ms": res.latency_ms})
        return opinions

    def think(self, ctx: MarketContext, versions: dict) -> Thought:
        t0 = time.perf_counter()
        first = self._parallel({"market": (self.market.analyze, ctx), "setup": (self.setup.analyze, ctx)})
        cands = first["setup"].candidates if first["setup"].ok else []
        second = self._parallel({"risk": (self.risk.analyze, ctx, cands),
                                 "adversary": (self.adversary.analyze, ctx, cands),
                                 "reviewer": (self.reviewer.analyze, ctx, cands)})
        reports = {**first, **second}
        t1 = time.perf_counter()
        if self.config.decision_mode == "edges":
            opinions = []  # promoted, measured edges decide; no model opinion is consulted
            decision = edge_decision(ctx, versions, self.edges)
            t2 = time.perf_counter()
        elif self.config.decision_mode in MODEL_MODES:
            opinions = []  # the models ARE the traders here: no separate review calls
            trader = {"trading_room": self.room, "experimental_ai": self.experimental}.get(
                self.config.decision_mode, self.llm_trader)
            decision = trader.decide(ctx, reports, versions)
            t2 = time.perf_counter()
        else:
            opinions = self._llm_reviews(ctx, reports)
            t2 = time.perf_counter()
            decision = self.synth.synthesize(ctx, reports, versions, opinions)
        return Thought(decision, reports, opinions,
                       {"agents": round((t1 - t0) * 1000, 2), "llm": round((t2 - t1) * 1000, 2),
                        "total": round((time.perf_counter() - t0) * 1000, 2)})
