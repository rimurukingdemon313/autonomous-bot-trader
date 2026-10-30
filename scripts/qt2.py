"""QT-2: QT-1's London true open with a wider stop and a longer hold (research/preregistrations/QT-2.md).

    python scripts/qt2.py spec | preregister
    python scripts/qt2.py run    # select on development 2009-2013 by the frozen rule, judge on validation 2014-2016

ID-1's data, fill model, costs, risk-engine entry checks, matched-random control and gates (scripts/id1.py), as in
QT-1. The fx-majors holdout (2017 on) stays sealed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import id1  # noqa: E402
from aitrader.research.discovery import intraday as ID  # noqa: E402
from aitrader.research.discovery import quarters_wide as W  # noqa: E402
from aitrader.research.discovery import rc  # noqa: E402
from aitrader.research.discovery.stats import welch_t  # noqa: E402
from aitrader.research.registry import Trial, Use, Verdict  # noqa: E402

PID = "QT-2"
DOC = "research/preregistrations/QT-2.md"
SPEC = id1.R / "specs" / "QT-2.json"
CODE = ("aitrader/research/discovery/quarters_wide.py", "aitrader/research/discovery/quarters.py",
        "aitrader/research/discovery/intraday.py", "scripts/id1.py", "scripts/qt2.py")
DEV, VAL = id1.DEV, id1.VAL
HID = "T3W-LONDON-TRUE-OPEN-WIDE"
#: every configuration looked at, all charged: the stop's multiple of T3's, the reward:risk, the time exit
GRID = {"stop_mult": [1.0, 1.5, 2.0], "r": [1.5, 2.0], "until": [720, 1080]}
SELECT = ("the configuration with the highest development net R among those passing every ID-1 promotion gate; "
          "none passing: FAILED, and validation is not run")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec(reg) -> dict:
    t = reg.threshold_for_next("fx-majors", *VAL, new_tests=1)
    return {"program": PID, "version": W.QUARTERS_WIDE_VERSION, "hypothesis": HID, "grid": GRID, "select": SELECT,
            "promote": id1.PROMOTE, "judge": {k: v for k, v in id1.JUDGE.items() if k != "hybrid_beats_component"},
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": "sealed: fx-majors 2017-01 on, opened only through its own preregistration"},
            "symbols": id1.SYMBOLS, "costs": id1.COSTS.__dict__, "cost_grid": id1.COST_GRID,
            "slippage_stress_pips": id1.SLIP_STRESS, "risk_pct": id1.RISK_PCT, "random_seeds": id1.RANDOM_SEEDS,
            "t_required_validation": round(max(3.0, t), 4)}


def signals(panel: dict, cell: dict) -> dict:
    return {k: W.london_true_open_wide(b, **cell) for k, b in panel.items()}


def _run(panel, cell, rates, period, costs=id1.COSTS):
    return id1.run_trades(panel, signals(panel, cell), rates, period, costs)


def cmd_spec():
    reg = id1._registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(id1._dump({"spec": s, "sha256": id1.spec_sha(s), "code_sha256": code_hash()}))
    print(id1.spec_sha(s), "t_required_validation", s["t_required_validation"])


def cmd_preregister(now):
    reg = id1._registry()
    frozen = json.loads(SPEC.read_text())
    if id1.spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="QT-2: the London true open (QT-1 T3) with a wider stop and a "
                                                     "longer hold",
                       hypothesis="Does QT-1's London true-open signal, with its stop widened so costs take a smaller "
                                  "share of R, earn a significant net expectancy on 2014-2016?",
                       uses=(Use("fx-majors", DEV[0], DEV[1], "select"), Use("fx-majors", VAL[0], VAL[1], "judge")),
                       tests=1, configurations=len(id1._grid(GRID)), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_run(now):
    reg = id1._registry()
    frozen = json.loads(SPEC.read_text())
    if reg.get(PID).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required_validation"]
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    body: dict = {"program": PID, "spec_sha256": frozen["sha256"], "t_required_validation": t_req,
                  "selection": [], "development": {}, "validation": {}}
    dev = id1.load(DEV)
    seen = []
    for cell in id1._grid(GRID):
        sig = signals(dev, cell)
        tr = id1.run_trades(dev, sig, rates, DEV)
        s = id1.evaluate(tr, DEV, dev)
        mr = id1.matched(dev, sig, rates, DEV)
        vs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in mr])) if tr and mr else None
        g = id1.promote_gates(s, vs)
        row = {"params": cell, "summary": id1._brief(s),
               "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None, "gates": g,
               "promotable": all(g.values())}
        body["selection"].append(row)
        seen.append((cell, s, mr, vs, g))
        print("dev", json.dumps(cell), json.dumps(id1._brief(s)), "vsR", vs, "promotable", all(g.values()), flush=True)
    promotable = [x for x in seen if all(x[4].values())]
    # the record: the selected configuration, or with none promotable the best development net R, marked unpromoted
    cell, s, mr, vs, g = max(promotable or seen, key=lambda x: x[1].get("net_r") or -9)
    body["selected"] = cell if promotable else None
    body["promoted"] = [HID] if promotable else []
    body["development"][HID] = {"summary": id1._brief(s), "detail": s, "matched_random": id1._brief(id1.evaluate(mr, DEV)),
                                "params": cell, "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None,
                                "gates": g, "promoted": bool(promotable)}
    if promotable:
        val = id1.load(VAL)
        sig = signals(val, cell)
        tr = id1.run_trades(val, sig, rates, VAL)
        vsum = id1.evaluate(tr, VAL, val)
        vmr = id1.matched(val, sig, rates, VAL)
        vvs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in vmr])) if tr and vmr else None
        stress = {f"x{k}": id1._brief(id1.evaluate(_run(val, cell, rates, VAL, id1.COSTS.stressed(k)), VAL))
                  for k in id1.COST_GRID}
        stress["slippage_0.3"] = id1._brief(id1.evaluate(_run(val, cell, rates, VAL, ID.Costs(slippage_pips=id1.SLIP_STRESS)), VAL))
        grid = []
        for c in id1._grid(GRID):
            gs = id1.evaluate(_run(val, c, rates, VAL), VAL)
            grid.append({"params": c, "trades": gs.get("trades"), "net_r": gs.get("net_r"), "t_day": gs.get("t_day")})
        sym = [v for v in vsum.get("by_symbol", {}).values() if v["trades"] >= 30]
        gates = {"t_day": (vsum.get("t_day") or 0) >= t_req, "net_r": (vsum.get("net_r") or 0) > 0,
                 "profit_factor": (vsum.get("profit_factor") or 0) >= 1.2,
                 "costs_x1.5": (stress["x1.5"].get("net_r") or 0) > 0,
                 "symbols_positive": bool(sym) and np.mean([v["net_r"] > 0 for v in sym]) >= 0.6,
                 "three_month_windows": (vsum.get("windows", {}).get("3m", {}).get("profitable_share") or 0) >= 0.6,
                 "beats_matched_random": (vvs or 0) >= 2.0,
                 "grid": np.mean([(c["net_r"] or 0) > 0 for c in grid]) >= 0.75}
        body["validation"][HID] = {"summary": id1._brief(vsum), "detail": vsum, "matched_random": id1._brief(id1.evaluate(vmr, VAL)),
                                   "vs_matched_random_welch_t": round(vvs, 3) if vvs is not None else None,
                                   "stress": stress, "grid": grid, "gates": gates, "passed": all(gates.values())}
        print("val", json.dumps(cell), json.dumps(id1._brief(vsum)), "gates", gates, flush=True)
    passers = [h for h in body["promoted"] if body["validation"][h]["passed"]]
    body["passers"], body["verdict"] = passers, ("PASSED" if passers else "FAILED")
    art = id1._write(PID, body)
    reg.record_verdict(Verdict(PID, now, art["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                          "artifact_sha256": art["sha256"]}))
    print("verdict", art["verdict"], "selected", body.get("selected"), "passers", passers)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "run": lambda: cmd_run(now)}.get(
        cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
