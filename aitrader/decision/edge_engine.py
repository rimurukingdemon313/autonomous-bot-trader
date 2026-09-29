"""The edge engine: BUY, SELL or ABSTAIN from PROMOTED edges only, with the evidence attached.

    M15 bar closes -> features on M15 (execution), H1 and H4 (context and regime)
      -> every promoted edge for this instrument, BUY and SELL searched independently
      -> each matching edge scored by its measured evidence, net of today's cost
      -> the best positive score becomes the decision; none -> ABSTAIN, saying what was checked
      -> the Risk Engine sizes and may refuse it (this module never sizes anything)

An edge reaches this module only by promotion: the research record (registry trial, battery,
walk-forward, the single-use holdout) is reviewed and the edge is written to
`models/artifacts/promoted_edges.json` by a person. Research code never writes there, and
this module never imports research code. With no promoted edge the engine abstains — and
says so, rather than trading on hope.

Score (a measured quantity, not a confidence):

    score = out-of-sample mean R - 1 x its standard error - (cost now - cost assumed in testing)

i.e. a conservative estimate of the net R per trade at today's spread. An edge whose live
record has DEGRADED or been RETIRED is not used. A position already open on the instrument, or
the same setup already decided, is not doubled: the setup id is deterministic per edge, bar and side.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from statistics import NormalDist

EDGE_ENGINE_VERSION = "edge-engine-1.0.0"
PROMOTED_PATH = Path(__file__).resolve().parents[2] / "models" / "artifacts" / "promoted_edges.json"
USABLE = ("PAPER_TEST", "DEMO_TEST", "LIVE_APPROVED")
TIMEFRAMES = ("M15", "H1", "H4")


class EdgeFileError(ValueError):
    pass


@dataclass(frozen=True)
class Bound:
    timeframe: str  # M15 | H1 | H4
    feature: str
    lo: float | None = None  # inclusive
    hi: float | None = None  # exclusive

    def holds(self, frames: dict) -> bool | None:
        v = (frames.get(self.timeframe) or {}).get(self.feature)
        if v is None or not math.isfinite(v):
            return None  # unknown: never treated as a match
        return (self.lo is None or v >= self.lo) and (self.hi is None or v < self.hi)


@dataclass(frozen=True)
class PromotedEdge:
    edge_id: str
    side: str  # BUY | SELL
    instruments: tuple[str, ...]
    conditions: tuple[Bound, ...]
    stop_atr: float
    target_atr: float
    max_bars: int
    oos_mean_r: float
    oos_se: float
    oos_n: int
    cost_r_assumed: float
    status: str
    trial: str
    health: str = "HEALTHY"
    evidence: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, d: dict) -> "PromotedEdge":
        for k in ("edge_id", "side", "instruments", "conditions", "stop_atr", "target_atr", "max_bars", "oos_mean_r",
                  "oos_se", "oos_n", "cost_r_assumed", "status", "trial"):
            if k not in d:
                raise EdgeFileError(f"promoted edge missing {k!r}")
        if d["side"] not in ("BUY", "SELL") or d["stop_atr"] <= 0 or d["target_atr"] <= 0 or d["max_bars"] < 1:
            raise EdgeFileError(f"{d['edge_id']}: invalid side or exit")
        for k in ("size", "lots", "risk_pct", "risk_amount", "leverage"):
            if k in d:
                raise EdgeFileError(f"{d['edge_id']}: an edge never carries {k!r}; sizing is the Risk Engine's")
        conds = tuple(Bound(c["timeframe"], c["feature"], c.get("lo"), c.get("hi")) for c in d["conditions"])
        if not conds or any(c.timeframe not in TIMEFRAMES for c in conds):
            raise EdgeFileError(f"{d['edge_id']}: conditions must name M15, H1 or H4")
        return cls(d["edge_id"], d["side"], tuple(d["instruments"]), conds, float(d["stop_atr"]),
                   float(d["target_atr"]), int(d["max_bars"]), float(d["oos_mean_r"]), float(d["oos_se"]),
                   int(d["oos_n"]), float(d["cost_r_assumed"]), d["status"], d["trial"], d.get("health", "HEALTHY"),
                   dict(d.get("evidence") or {}))


def load_promoted(path: Path | str = PROMOTED_PATH) -> tuple[list[PromotedEdge], str]:
    """(edges, note). A missing file is not an error: it means nothing has been promoted."""
    p = Path(path)
    if not p.exists():
        return [], "no promoted edges: research has not validated one (models/artifacts/promoted_edges.json absent)"
    raw = json.loads(p.read_text())
    edges = [PromotedEdge.from_json(e) for e in raw.get("edges", [])]
    return edges, f"{len(edges)} promoted edge(s)"


def edge_health(expected_mean: float, expected_se: float, recent_r: list[float], min_n: int = 20) -> dict:
    """Is the live record normal variance around what testing measured, or real degradation?

    DEGRADED: at least `min_n` trades and the live mean is more than 2 standard errors below the
    tested mean (the gap cannot plausibly be variance). RETIRED: at least 2 x `min_n` trades and the
    live mean is below zero with 95% confidence. A few losses in a row are neither."""
    n = len(recent_r)
    if n < min_n:
        return {"state": "HEALTHY", "n": n, "reason": f"{n} live trades: too few to tell variance from decay"}
    mean = sum(recent_r) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in recent_r) / (n - 1)) if n > 1 else 0.0
    se_live = sd / math.sqrt(n) if sd > 0 else 1e-9
    gap = (mean - expected_mean) / math.sqrt(se_live ** 2 + expected_se ** 2)
    if n >= 2 * min_n and mean + NormalDist().inv_cdf(0.95) * se_live < 0:
        return {"state": "RETIRED", "n": n, "mean_r": round(mean, 4), "z_gap": round(gap, 2),
                "reason": "the live record is negative with 95% confidence"}
    if gap < -2.0:
        return {"state": "DEGRADED", "n": n, "mean_r": round(mean, 4), "z_gap": round(gap, 2),
                "reason": "the live mean is more than 2 standard errors below the tested mean"}
    return {"state": "HEALTHY", "n": n, "mean_r": round(mean, 4), "z_gap": round(gap, 2),
            "reason": "within normal variance of the tested expectation"}


def setup_id(edge_id: str, symbol: str, t: int, side: str) -> str:
    return hashlib.sha256(json.dumps([edge_id, symbol, int(t), side]).encode()).hexdigest()[:20]


def evaluate(edges: list[PromotedEdge], symbol: str, t: int, frames: dict, bid: float | None, ask: float | None,
             atr: float | None, cost_r_now_per_atr: float | None, open_symbols: set[str] = frozenset(),
             decided_setups: set[str] = frozenset()) -> dict:
    """The decision and its evidence report. Pure: no I/O, no sizing, no clock."""
    report = {"version": EDGE_ENGINE_VERSION, "symbol": symbol, "t": int(t), "checked": [], "candidates": []}

    def abstain(reason: str) -> dict:
        return {"decision": "ABSTAIN", "reason": reason, **report}

    if bid is None or ask is None or not atr or not math.isfinite(atr) or atr <= 0:
        return abstain("no live quote or ATR: nothing can be priced")
    if symbol in open_symbols:
        return abstain(f"a position on {symbol} is already open: not doubled")
    for e in edges:
        row = {"edge_id": e.edge_id, "side": e.side}
        if symbol not in e.instruments:
            continue
        if e.status not in USABLE:
            report["checked"].append(row | {"result": f"status {e.status} is not usable"})
            continue
        if e.health in ("DEGRADED", "RETIRED"):
            report["checked"].append(row | {"result": f"health {e.health}"})
            continue
        states = [c.holds(frames) for c in e.conditions]
        if any(s is None for s in states):
            report["checked"].append(row | {"result": "a condition's feature is unavailable: not matched"})
            continue
        if not all(states):
            report["checked"].append(row | {"result": "conditions not met"})
            continue
        sid = setup_id(e.edge_id, symbol, t, e.side)
        if sid in decided_setups:
            report["checked"].append(row | {"result": "this setup was already decided"})
            continue
        spread_r = (ask - bid) / (e.stop_atr * atr)
        cost_now = spread_r + (cost_r_now_per_atr or 0.0) / e.stop_atr
        extra = max(0.0, cost_now - e.cost_r_assumed)
        score = e.oos_mean_r - e.oos_se - extra
        side = 1 if e.side == "BUY" else -1
        entry = ask if side > 0 else bid
        cand = row | {"setup_id": sid, "score_R": round(score, 4), "oos_mean_R": e.oos_mean_r, "oos_se": e.oos_se,
                      "oos_n": e.oos_n, "cost_now_R": round(cost_now, 4), "cost_assumed_R": e.cost_r_assumed,
                      "entry": entry, "stop": entry - side * e.stop_atr * atr, "target": entry + side * e.target_atr * atr,
                      "max_hold_minutes": e.max_bars * 15, "trial": e.trial, "health": e.health,
                      "evidence": e.evidence}
        report["candidates"].append(cand)
        report["checked"].append(row | {"result": f"matched, score {score:+.4f}R"})
    viable = [c for c in report["candidates"] if c["score_R"] > 0]
    if not viable:
        if not edges:
            return abstain("no promoted edges exist: the research has not validated one")
        return abstain("no promoted edge both matches now and keeps a positive expected value after today's costs")
    best = max(viable, key=lambda c: (c["score_R"], c["oos_n"]))
    return {"decision": best["side"], "reason": f"edge {best['edge_id']}: expected {best['score_R']:+.4f}R after costs "
                                                f"(conservative: tested mean minus one standard error)",
            "chosen": best, **report}
