"""Live learning without live money: a flat, prospective record of every decision and what followed.

The service already journals, append-only and hash-chained (aitrader/memory/db.py):
- `decisions`: every decision, NO_TRADE and ABSTAIN included, with its reason, direction,
  confidence, expected R, regime and the point-in-time context (M15/H1/H4 frames in edges mode);
- `trades`: every closed paper/demo trade with R, MFE, MAE, exit reason, slippage and post-mortem;
- `evaluations`: the SHADOW outcome of every candidate that was not traded.

This module turns them into one row per decision (`observations`) and a periodic, versioned
review (`review`) that answers the Round 2 questions:

- which conditions (regime, volatility, session, family, direction) produce good or bad decisions;
- which promoted edges are degrading (edge_health: variance vs decay);
- which regimes are new (decisions the regime model flagged as unfamiliar);
- which assumptions no longer hold (live cost vs the cost an edge was tested with).

It READS the journal and WRITES NOTHING into it or into any rule. Every finding is a candidate
hypothesis for the research registry (a prospective test on data recorded after it is frozen),
never an automatic change: validated rules are not silently rewritten. The report carries its
version, and a minimum sample below which it says "insufficient" instead of a number.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

from ..decision.edge_engine import edge_health

OBSERVATIONS_VERSION = "observations-1.0.0"
MIN_N = 20  # below this a cell is reported as "insufficient", never as a rate


def _j(x) -> dict:
    if isinstance(x, dict):
        return x
    try:
        return json.loads(x or "{}")
    except (TypeError, ValueError):
        return {}


def observations(decisions: list[dict], trades: list[dict], evaluations: list[dict]) -> list[dict]:
    """One row per decision: state at decision time, the prediction, and every outcome known so far.
    Inputs are journal rows (dicts with a JSON `payload`)."""
    by_trade = {t["decision_id"]: _j(t.get("payload")) | {"r": t.get("r")} for t in trades}
    shadows: dict[str, list[dict]] = defaultdict(list)
    for e in evaluations:
        for ev in _j(e.get("payload")).get("evaluations", []):
            shadows[e["decision_id"]].append(ev)
    out = []
    for d in decisions:
        p = _j(d.get("payload"))
        ctx = p.get("context") or {}
        regime = p.get("regime") or {}
        ee = (p.get("evidence") or {}).get("edge_engine") or {}
        chosen = ee.get("chosen") or {}
        tr = by_trade.get(d["id"])
        out.append({
            "decision_id": d["id"], "t": ctx.get("t") or p.get("t"), "symbol": d.get("symbol"),
            "mode": d.get("mode"), "decision": d.get("decision"),
            "direction": {"BUY": 1, "SELL": -1}.get(d.get("decision"), 0),
            "confidence": p.get("confidence"), "expected_R": p.get("expected_R"),
            "reason": p.get("no_trade_reason") or p.get("thesis"),
            "regime": regime.get("label"), "vol_state": regime.get("vol_state"),
            "familiar": regime.get("familiar"),
            "frames": ctx.get("frames"), "edge_id": chosen.get("edge_id"),
            "cost_now_R": chosen.get("cost_now_R"), "cost_assumed_R": chosen.get("cost_assumed_R"),
            "entry": p.get("entry"), "stop": p.get("stop"), "target": p.get("target"),
            "traded": tr is not None,
            "r": tr.get("r") if tr else None, "mfe_r": tr.get("mfe_r") if tr else None,
            "mae_r": tr.get("mae_r") if tr else None,
            "exit_reason": ((tr.get("exit") or {}).get("reason") if tr else None),
            "cause": ((tr.get("postmortem") or {}).get("cause") if tr else None),
            "shadow": [{"action": s.get("action"), "r": s.get("outcome_r"), "objections": s.get("objections")}
                       for s in shadows.get(d["id"], [])],
        })
    return out


def _cell(rs: list[float]) -> dict:
    n = len(rs)
    if n < MIN_N:
        return {"n": n, "sample": "insufficient"}
    m = sum(rs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in rs) / (n - 1)) if n > 1 else 0.0
    return {"n": n, "mean_R": round(m, 4), "se": round(sd / math.sqrt(n), 4), "t": round(m / (sd / math.sqrt(n)), 2)
            if sd > 0 else None, "sample": "ok"}


def review(obs: list[dict], tested: dict[str, dict] | None = None) -> dict:
    """The periodic review. `tested`: edge_id -> {"mean": ..., "se": ..., "cost_r": ...} from the
    promoted edges, to judge live decay and live cost against what testing assumed."""
    traded = [o for o in obs if o["traded"] and o["r"] is not None]
    conditions: dict[str, dict] = {}
    for key in ("regime", "vol_state", "mode", "symbol"):
        cells: dict[str, list[float]] = defaultdict(list)
        for o in traded:
            cells[f"{o.get(key)}|{'BUY' if o['direction'] > 0 else 'SELL'}"].append(float(o["r"]))
        conditions[key] = {k: _cell(v) for k, v in sorted(cells.items())}
    causes: dict[str, int] = defaultdict(int)
    for o in traded:
        if o["r"] < 0:
            causes[o.get("cause") or "UNCLASSIFIED"] += 1
    edges = {}
    for eid, t in (tested or {}).items():
        rs = [float(o["r"]) for o in traded if o.get("edge_id") == eid]
        costs = [o["cost_now_R"] for o in obs if o.get("edge_id") == eid and o.get("cost_now_R") is not None]
        live_cost = sum(costs) / len(costs) if costs else None
        edges[eid] = {"health": edge_health(t["mean"], t["se"], rs),
                      "live_cost_R": round(live_cost, 4) if live_cost is not None else None,
                      "tested_cost_R": t.get("cost_r"),
                      "cost_assumption_holds": (None if live_cost is None or t.get("cost_r") is None
                                                else live_cost <= 1.25 * t["cost_r"])}
    unfamiliar = [o for o in obs if o.get("familiar") is False]
    return {
        "version": OBSERVATIONS_VERSION, "decisions": len(obs), "traded_resolved": len(traded),
        "abstained": sum(1 for o in obs if o["decision"] in ("NO_TRADE", "ABSTAIN")),
        "conditions": conditions, "loss_causes": dict(sorted(causes.items())), "edges": edges,
        "new_regimes": {"unfamiliar_decisions": len(unfamiliar),
                        "share": round(len(unfamiliar) / len(obs), 4) if obs else None},
        "note": "findings are hypotheses for the research registry; nothing here changes a rule",
    }


__all__ = ["MIN_N", "OBSERVATIONS_VERSION", "observations", "review"]
