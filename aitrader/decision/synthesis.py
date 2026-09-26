"""Evidence synthesis and the Decision record. Not a vote.

"3 BUY vs 2 SELL = BUY" treats five correlated opinions as five independent
facts. Here the decision rests on one quantitative anchor and a set of
subtractive adjustments:

1. FAIL CLOSED. A required agent that errored, timed out or is unavailable
   -> NO_TRADE. A BLOCKING objection from any agent -> NO_TRADE.
2. ANCHOR. The leading candidate's expected R after costs, estimated from
   historical analogues whose outcomes were known at decision time, with its
   standard error. It is the only quantity here that was measured against
   outcomes, so it is the only one allowed to argue FOR a trade.
3. REQUIRED EDGE. Starts at `base_margin`. Each MAJOR objection raises it by
   a penalty set by that objection's MEASURED reliability: how much worse
   flagged candidates did than unflagged ones, point-in-time
   (ExperienceView.objection_effect). With no track record yet, a default
   penalty applies. An objection that has proven uninformative costs little;
   one that has proven predictive costs what it predicted.
4. LANGUAGE MODELS can only subtract: an LLM that opposes adds a penalty
   scaled by its measured reliability (zero until earned in forward trading,
   because an LLM's judgement cannot be validated on history it may
   remember). An LLM that agrees lowers nothing.
5. TRADE only if lower-bound expectancy >= required edge. Confidence is
   P(expected R > required edge) from the analogue mean and standard error —
   derived from evidence, never a number a model reports about itself.

Independence: evidence is grouped by the data it rests on (the analogue
memory, trend features, structure features, momentum features ...). The
record reports how many INDEPENDENT groups support and oppose the trade, so
five agents restating one moving average count once.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import NormalDist

from ..agents.types import AgentReport, MarketContext, Objection, SetupCandidate

DECISION_VERSION = "decision-1.0.0"
REQUIRED_AGENTS = ("market", "setup", "risk", "adversary")

SOURCE_GROUPS = {
    "ma_slope": "trend", "er120": "trend", "er24": "trend", "dist_ma48": "trend",
    "r1": "momentum", "r6": "momentum", "r24": "momentum", "r120": "momentum",
    "smc_structure": "structure", "smc_sweep": "structure", "smc_hi_dist": "structure",
    "smc_lo_dist": "structure", "brk_hi120": "structure", "brk_lo120": "structure",
    "range_pos24": "structure", "range_pos120": "structure",
    "vol_ratio": "volatility", "rv_ratio": "volatility", "tick_activity": "liquidity",
}


@dataclass(frozen=True)
class SynthesisConfig:
    base_margin: float = 0.0  # required lower-bound expectancy, in R, before objections
    default_major_penalty: float = 0.03
    min_penalty: float = 0.01
    max_penalty: float = 0.25
    min_track_record: int = 30
    llm_opposition_penalty: float = 0.05


@dataclass
class Decision:
    id: str
    decision: str  # BUY | SELL | NO_TRADE
    instrument: str
    timeframe: str
    timestamp: int
    mode: str
    market_state: dict
    regime: dict
    thesis: str
    supporting_evidence: list[dict]
    contradicting_evidence: list[dict]
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    exit_logic: str | None
    template: str | None
    family: str | None
    expected_edge: float | None
    probability: float | None
    expected_R: float | None
    lower_R: float | None
    required_edge: float | None
    confidence: float | None
    risk_R: float | None
    invalidation: str | None
    no_trade_reason: str | None
    agents: dict
    independent_evidence: dict
    candidates_considered: int
    versions: dict
    created: float = field(default_factory=time.time)

    @property
    def is_trade(self) -> bool:
        return self.decision in ("BUY", "SELL")

    def as_dict(self) -> dict:
        d = asdict(self)
        d["time"] = datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat()
        return d


def decision_id(symbol: str, timeframe: str, t: int, mode: str, versions: dict) -> str:
    """Deterministic: the same decision point can never produce two decisions."""
    raw = json.dumps([symbol, timeframe, int(t), mode, versions], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _groups(sources) -> set[str]:
    return {SOURCE_GROUPS.get(s, s) for s in sources}


class EvidenceSynthesizer:
    def __init__(self, config: SynthesisConfig = SynthesisConfig()) -> None:
        self.config = config

    def penalty(self, obj: Objection, ctx: MarketContext) -> tuple[float, str]:
        cfg = self.config
        kv = ctx.knowledge
        eff = kv.objection_effect(obj.code, ctx.t) if kv is not None else None
        if eff and eff.get("n_flagged", 0) >= cfg.min_track_record:
            delta = eff["mean_flagged"] - eff["mean_other"]
            p = min(cfg.max_penalty, max(cfg.min_penalty, -delta))
            return p, f"measured: flagged {eff['mean_flagged']:+.3f}R vs {eff['mean_other']:+.3f}R (n={eff['n_flagged']})"
        return cfg.default_major_penalty, "default (no track record yet)"

    def synthesize(self, ctx: MarketContext, reports: dict[str, AgentReport], versions: dict,
                   llm_opinions: list[dict] | None = None) -> Decision:
        cfg = self.config
        did = decision_id(ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, versions)
        agents = {k: {"status": r.status, "stance": r.stance, "latency_ms": r.latency_ms,
                      "summary": r.summary, "objections": len(r.objections), "llm": (r.llm or {}).get("status")}
                  for k, r in reports.items()}
        state = {k: ctx.features.values.get(k) for k in ("r24", "r120", "er120", "ma_slope", "vol_ratio",
                                                         "spread_rel", "range_pos120", "smc_structure")}

        def no_trade(reason: str, cand: SetupCandidate | None = None, contra=None, support=None,
                     required=None, conf=None) -> Decision:
            return Decision(
                did, "NO_TRADE", ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, state, ctx.regime.as_dict(),
                thesis=reason, supporting_evidence=support or [], contradicting_evidence=contra or [],
                entry=None, stop_loss=None, take_profit=None, exit_logic=None,
                template=cand.template if cand else None, family=cand.family if cand else None,
                expected_edge=cand.expected_r if cand else None, probability=cand.win_rate if cand else None,
                expected_R=cand.expected_r if cand else None, lower_R=cand.lower_r if cand else None,
                required_edge=required, confidence=conf, risk_R=None, invalidation=None,
                no_trade_reason=reason, agents=agents,
                independent_evidence={}, candidates_considered=len(reports.get("setup").candidates) if reports.get("setup") else 0,
                versions=versions)

        # 1. fail closed on any required agent
        for name in REQUIRED_AGENTS:
            r = reports.get(name)
            if r is None or not r.ok:
                return no_trade(f"agent '{name}' {'missing' if r is None else r.status}: failing closed")

        objections: list[Objection] = [o for r in reports.values() for o in r.objections]
        blocking = [o for o in objections if o.severity == "BLOCKING" and not o.data.get("action")]
        if blocking:
            return no_trade("blocked: " + "; ".join(f"{o.code} ({o.agent}): {o.message}" for o in blocking[:4]),
                            contra=[o.as_dict() for o in blocking])

        cands = reports["setup"].candidates
        if not cands:
            return no_trade("no setup candidate in any family, and no analogue-discovered opportunity")

        best_decision = None
        rejected: list[str] = []
        for cand in cands:
            if cand.expected_r is None or cand.lower_r is None:
                rejected.append(f"{cand.family} {cand.action}: no analogue evidence")
                continue
            mine = [o for o in objections if o.data.get("action") in (None, cand.action)]
            block = [o for o in mine if o.severity == "BLOCKING"]
            if block:
                rejected.append(f"{cand.family} {cand.action}: {block[0].code}")
                continue
            required = cfg.base_margin
            contra = []
            for o in mine:
                if o.severity == "MAJOR":
                    p, basis = self.penalty(o, ctx)
                    required += p
                    contra.append({**o.as_dict(), "penalty_R": round(p, 4), "basis": basis})
                elif o.severity == "MINOR":
                    contra.append({**o.as_dict(), "penalty_R": 0.0, "basis": "informational"})
            for op in llm_opinions or []:
                if op.get("direction") in ("BUY", "SELL") and op["direction"] != ("BUY" if cand.direction > 0 else "SELL"):
                    w = ctx.knowledge.agent_reliability(op["agent"], ctx.t) if ctx.knowledge is not None else 0.0
                    if w > 0:
                        required += cfg.llm_opposition_penalty * w
                        contra.append({"agent": op["agent"], "code": "LLM_OBJECTION", "severity": "MAJOR",
                                       "message": op.get("summary", "")[:200], "penalty_R": round(cfg.llm_opposition_penalty * w, 4),
                                       "basis": f"measured LLM reliability {w:.2f}"})
            se = max((cand.expected_r - cand.lower_r) / 1.28, 1e-9)
            conf = float(NormalDist().cdf((cand.expected_r - required) / se))
            if cand.lower_r < required:
                rejected.append(f"{cand.family} {cand.action}: lower {cand.lower_r:+.3f}R < required {required:+.3f}R")
                continue
            best_decision = (cand, required, conf, contra)
            break

        if best_decision is None:
            top = cands[0]
            return no_trade("no candidate cleared its required edge: " + " | ".join(rejected[:4]), top,
                            contra=[o.as_dict() for o in objections][:12])

        cand, required, conf, contra = best_decision
        d = cand.direction
        support, opp_groups, sup_groups = [], set(), {"analogue-memory"}
        support.append({"agent": "setup", "claim": f"{cand.n_analogs} historical analogues: expectancy "
                        f"{cand.expected_r:+.3f}R (lower {cand.lower_r:+.3f}R), win rate {cand.win_rate:.0%}",
                        "group": "analogue-memory", "analog": cand.analog})
        for r in reports.values():
            for e in r.evidence:
                if e.direction == d:
                    support.append({**e.as_dict(), "group": sorted(_groups(e.sources))})
                    sup_groups |= _groups(e.sources)
                elif e.direction == -d:
                    contra.append({**e.as_dict(), "group": sorted(_groups(e.sources))})
                    opp_groups |= _groups(e.sources)
        side = "BUY" if d > 0 else "SELL"
        thesis = (f"{side} {ctx.symbol}: {cand.family} ({cand.template}); analogues {cand.expected_r:+.3f}R "
                  f"lower {cand.lower_r:+.3f}R >= required {required:+.3f}R after {len([c for c in contra if c.get('severity') == 'MAJOR'])} "
                  f"major objection(s); regime {ctx.regime.label}/{ctx.regime.vol_state}.")
        return Decision(
            did, side, ctx.symbol, ctx.timeframe, ctx.t, ctx.mode, state, ctx.regime.as_dict(), thesis,
            support, contra, cand.entry, cand.stop, cand.target,
            f"stop {cand.stop:.5g}, target {cand.target:.5g}, time exit after {cand.max_bars} bars",
            cand.template, cand.family, cand.expected_r, cand.win_rate, cand.expected_r, cand.lower_r,
            required, conf, 1.0, cand.invalidation, None, agents,
            {"supporting_groups": sorted(sup_groups), "opposing_groups": sorted(opp_groups),
             "n_supporting": len(sup_groups), "n_opposing": len(opp_groups)},
            len(cands), versions)
