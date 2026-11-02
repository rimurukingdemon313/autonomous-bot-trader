"""DESK-1: what if the desk's agreements had exited or been filtered another way? (research/preregistrations/DESK-1.md)

The owner, 2026-11-02: "make it profitable; try everything, test everything". Every agreement the desk made was
followed forward to its outcome (learning/forward.py). This asks, of that record, whether a simple rule fixed at the
entry would have done better: a nearer take-profit, or skipping the trades whose planned costs are high or that fall in
the London/New York overlap. A rule is chosen on the LEARNING weeks only, and judged once on the EVALUATION weeks.

Exact, and conservative where it cannot be exact. A take-profit at k R from the fill:
- a trade that reached its own target, beyond k: took k first (the bar that reached the target reached k);
- a trade closed by its time exit: took k if its best point reached k, in any bar (no stop was touched);
- a trade stopped out: took k only if its best point reached k in a bar BEFORE the one that stopped it. When the best
  point is in the stopping bar itself, the order of its high and low is unknown, and it stays a stop;
- a trade whose own target is k or nearer: unchanged.
A take-profit exit pays the commission and no exit slippage, as the forward walk's own target exits do. A skipped
trade is no trade: 0 R.

    python scripts/desk1.py freeze           # writes research/specs/DESK-1.json (the spec, its sha256, the code's)
    python scripts/desk1.py run <aitrader.db> # checks both hashes, then selects on LEARNING and judges on EVALUATION
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "research" / "specs" / "DESK-1.json"
DOC = ROOT / "research" / "preregistrations" / "DESK-1.md"
OUT = ROOT / "research" / "knowledge" / "DESK-1.json"

SPEC = {
    "program": "DESK-1",
    "question": "would a rule fixed at the entry have made the desk's agreements pay: a nearer take-profit, or "
                "skipping the costly ones or the London/New York overlap?",
    "data": "the forward ledger of a published paper-forward shift database: every DUAL_AI agreement as proposed "
            "(taken, or refused by the risk engine), RESOLVED, each counted once",
    "baseline": "each agreement's own net R as followed forward: the trader's levels and the time exit",
    "candidates": {
        "TP-0.75": {"take_profit_r": 0.75},
        "TP-1.0": {"take_profit_r": 1.0},
        "TP-1.25": {"take_profit_r": 1.25},
        "SKIP-COST-0.20": {"skip_planned_cost_r_above": 0.20},
        "SKIP-OVERLAP": {"skip_session": "OVERLAP"},
    },
    "planned_cost_r": "(spread + 2 x slippage + commission) / risk, from the proposal at the entry",
    "measure": "per agreement, d = candidate net R - baseline net R (a skipped agreement is 0 R); paired t of d",
    "select_on": "LEARNING",
    "select": "among the candidates whose LEARNING mean d is at least 0.05 R with paired t of 2.0 or more, the one with "
              "the largest mean d; if none qualifies, DESK-1 is FAILED and EVALUATION is not judged",
    "judge_on": "EVALUATION",
    "confirmed_if": "the selected candidate's EVALUATION mean d > 0 with paired t of 2.0 or more",
    "profitable_if": "confirmed, and the selected candidate's own EVALUATION net R over the trades it takes is > 0 "
                     "with t of 2.0 or more",
    "after": {
        "FAILED or not confirmed": "nothing in the bot changes; the result is reported as it is",
        "confirmed": "it is followed forward on the H1 desk as a shadow (measured, never traded) before it can become "
                     "a rule: these agreements were all on M15, with nearer stops than H1's",
    },
    "excluded_on_purpose": "a filter by side (BUYs lost in October): it is a bet on one month's trend, not a "
                           "structure (CLAUDE.md rule 12)",
}


def spec_sha(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def code_sha() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# ── the record ───────────────────────────────────────────────────────────

def agreements(db_path: str) -> list[dict]:
    """Every DUAL_AI agreement as proposed, RESOLVED, once, with what the counterfactuals need."""
    db = sqlite3.connect(db_path)
    props = {}
    for did, payload in db.execute("SELECT decision_id, payload FROM forward_proposals"):
        p = json.loads(payload)
        if p.get("family") == "DUAL_AI":
            props[did] = p
    out, seen = [], set()
    for did, payload in db.execute("SELECT decision_id, payload FROM forward_outcomes ORDER BY seq"):
        o = json.loads(payload)
        p = props.get(did)
        if p is None or did in seen or o.get("status") != "RESOLVED" or not isinstance(o.get("net_r"), (int, float)):
            continue
        seen.add(did)
        out.append({"id": did, "partition": p.get("partition"), "side": int(p["side"]), "session": p.get("session"),
                    "entry": float(p["entry"]), "target": float(p["target"]), "risk_px": float(p["risk_px"]),
                    "spread": float(p.get("spread") or 0.0), "slippage_px": float(p.get("slippage_px") or 0.0),
                    "commission_px": float(p.get("commission_px") or 0.0), "net_r": float(o["net_r"]),
                    "reason": o.get("reason"), "mfe_r": o.get("mfe_r"), "t_mfe": o.get("t_mfe"),
                    "exit_time": o.get("exit_time")})
    return out


# ── the counterfactuals ──────────────────────────────────────────────────

def take_profit_net(a: dict, k: float) -> float:
    """The agreement's net R had it taken profit at k R from the fill (module docstring: exact, else conservative)."""
    risk = a["risk_px"]
    comm_r = a["commission_px"] / risk
    own_target_r = ((a["target"] - a["entry"]) * a["side"] - a["slippage_px"]) / risk  # from the fill
    if own_target_r <= k:
        return a["net_r"]  # its own target is k or nearer: it comes first
    reached = isinstance(a.get("mfe_r"), (int, float)) and a["mfe_r"] >= k
    if a["reason"] == "TARGET":
        return k - comm_r
    if a["reason"] == "TIME" and reached:
        return k - comm_r
    if (a["reason"] == "STOP" and reached and a.get("t_mfe") is not None and a.get("exit_time") is not None
            and a["t_mfe"] < a["exit_time"]):
        return k - comm_r
    return a["net_r"]


def planned_cost_r(a: dict) -> float:
    return (a["spread"] + 2 * a["slippage_px"] + a["commission_px"]) / a["risk_px"]


def candidate_net(a: dict, rule: dict) -> float | None:
    """The agreement's net R under `rule`; None when the rule skips it (no trade, 0 R)."""
    if "take_profit_r" in rule:
        return take_profit_net(a, float(rule["take_profit_r"]))
    if "skip_planned_cost_r_above" in rule:
        return None if planned_cost_r(a) > float(rule["skip_planned_cost_r_above"]) else a["net_r"]
    if "skip_session" in rule:
        return None if a.get("session") == rule["skip_session"] else a["net_r"]
    raise ValueError(f"unknown rule {rule}")


def _t(xs: list[float]) -> tuple[float | None, float | None]:
    n = len(xs)
    if n < 2:
        return (xs[0] if xs else None), None
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, (m / (sd / math.sqrt(n)) if sd > 0 else None)


def evaluate(rows: list[dict], rule: dict) -> dict:
    """The paired difference against the baseline, and the candidate's own record over the trades it takes."""
    d, taken = [], []
    for a in rows:
        c = candidate_net(a, rule)
        d.append((0.0 if c is None else c) - a["net_r"])
        if c is not None:
            taken.append(c)
    md, td = _t(d)
    mt, tt = _t(taken)
    wins, losses = sum(x for x in taken if x > 0), -sum(x for x in taken if x < 0)
    return {"n": len(rows), "mean_d": None if md is None else round(md, 4), "t_d": None if td is None else round(td, 2),
            "trades": len(taken), "net_r": None if mt is None else round(mt, 4), "t_net": None if tt is None else round(tt, 2),
            "win_rate": round(sum(1 for x in taken if x > 0) / len(taken), 3) if taken else None,
            "profit_factor": round(wins / losses, 3) if losses > 0 else None}


def baseline(rows: list[dict]) -> dict:
    xs = [a["net_r"] for a in rows]
    m, t = _t(xs)
    wins, losses = sum(x for x in xs if x > 0), -sum(x for x in xs if x < 0)
    return {"n": len(xs), "net_r": None if m is None else round(m, 4), "t_net": None if t is None else round(t, 2),
            "win_rate": round(sum(1 for x in xs if x > 0) / len(xs), 3) if xs else None,
            "profit_factor": round(wins / losses, 3) if losses > 0 else None}


def judge(rows: list[dict], spec: dict = SPEC) -> dict:
    """Select on LEARNING, then judge the one selected on EVALUATION, as SPEC says and nothing more."""
    learn = [a for a in rows if a["partition"] == "LEARNING"]
    evalu = [a for a in rows if a["partition"] == "EVALUATION"]
    res = {"program": spec["program"], "spec_sha256": spec_sha(spec), "n_learning": len(learn),
           "n_evaluation": len(evalu), "baseline_learning": baseline(learn), "learning": {}}
    for name, rule in spec["candidates"].items():
        res["learning"][name] = evaluate(learn, rule)
    ok = {n: r for n, r in res["learning"].items()
          if r["mean_d"] is not None and r["t_d"] is not None and r["mean_d"] >= 0.05 and r["t_d"] >= 2.0}
    if not ok:
        res["selected"], res["verdict"] = None, "FAILED"
        return res
    name = max(ok, key=lambda n: ok[n]["mean_d"])
    res["selected"] = name
    res["baseline_evaluation"] = baseline(evalu)
    e = res["evaluation"] = evaluate(evalu, spec["candidates"][name])
    confirmed = e["mean_d"] is not None and e["t_d"] is not None and e["mean_d"] > 0 and e["t_d"] >= 2.0
    profitable = confirmed and e["net_r"] is not None and e["t_net"] is not None and e["net_r"] > 0 and e["t_net"] >= 2.0
    res["verdict"] = "PROFITABLE" if profitable else "CONFIRMED" if confirmed else "NOT CONFIRMED"
    return res


def main(argv: list[str]) -> int:
    if argv[:1] == ["freeze"]:
        SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
        SPEC_PATH.write_text(json.dumps({"spec": SPEC, "sha256": spec_sha(SPEC), "code_sha256": code_sha()},
                                        indent=1, sort_keys=True) + "\n")
        print(spec_sha(SPEC))
        return 0
    if argv[:1] == ["run"] and len(argv) == 2:
        frozen = json.loads(SPEC_PATH.read_text())
        if frozen["sha256"] != spec_sha(SPEC) or frozen["code_sha256"] != code_sha():
            raise SystemExit("the spec or the code changed after it was frozen: DESK-1 does not run")
        if frozen["sha256"] not in DOC.read_text():
            raise SystemExit(f"{DOC.name} must quote the spec sha256")
        db = Path(argv[1])
        res = {**judge(agreements(str(db))), "code_sha256": code_sha(),
               "db_sha256": hashlib.sha256(db.read_bytes()).hexdigest()}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        print(json.dumps(res, indent=1, sort_keys=True))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
