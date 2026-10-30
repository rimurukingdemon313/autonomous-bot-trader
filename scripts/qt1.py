"""QT-1: the two Quarters schools on M5 (research/preregistrations/QT-1.md).

    python scripts/qt1.py spec | preregister
    python scripts/qt1.py run        # stage 1 development 2009-2013 (all), stage 2 validation 2014-2016 (promoted only)

The data, the fill model, the costs, the controls, the gates and the evaluation are ID-1's (scripts/id1.py), reused
unchanged: only the rules are new (aitrader/research/discovery/quarters.py). The fx-majors holdout (2017 on) stays
sealed; a passer would open it through ID-1's own `holdout` procedure, preregistered first.
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
from aitrader.research.discovery import quarters as Q  # noqa: E402
from aitrader.research.discovery import rc  # noqa: E402
from aitrader.research.discovery.stats import welch_t  # noqa: E402
from aitrader.research.registry import Trial, Use, Verdict  # noqa: E402

PID = "QT-1"
DOC = "research/preregistrations/QT-1.md"
SPEC = id1.R / "specs" / "QT-1.json"
CODE = ("aitrader/research/discovery/quarters.py", "aitrader/research/discovery/intraday.py", "scripts/id1.py",
        "scripts/qt1.py")
DEV, VAL = id1.DEV, id1.VAL
FX = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD")  # the price quarters: a pip grid

#: id -> (school, rule, symbols, neighbourhood grid for robustness)
HYPOTHESES = {
    "Q1-QUARTER-FADE": ("price", "quarter_fade", FX, {"stop": [10.0, 12.5, 15.0], "r": [1.5, 2.0, 2.5]}),
    "Q2-QUARTER-BREAK": ("price", "quarter_break", FX, {"stop": [10.0, 12.5, 15.0], "r": [1.5, 2.0, 2.5]}),
    "T1-DAILY-AMD": ("time", "daily_amd", id1.SYMBOLS, {"buf": [0.05, 0.10, 0.20], "r": [1.5, 2.0, 2.5]}),
    "T2-NY-TRUE-OPEN": ("time", "ny_true_open", id1.SYMBOLS, {"buf": [0.05, 0.10, 0.20], "r": [1.5, 2.0, 2.5]}),
    "T3-LONDON-TRUE-OPEN": ("time", "london_true_open", id1.SYMBOLS, {"buf": [0.05, 0.10, 0.20], "r": [1.5, 2.0, 2.5]}),
}
PROMOTE, JUDGE = id1.PROMOTE, {k: v for k, v in id1.JUDGE.items() if k != "hybrid_beats_component"}


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec(reg) -> dict:
    t = reg.threshold_for_next("fx-majors", *VAL, new_tests=len(HYPOTHESES))
    return {"program": PID, "version": Q.QUARTERS_VERSION, "intraday_version": ID.INTRADAY_VERSION,
            "quarter_pips": Q.QUARTER_PIPS, "hypotheses": HYPOTHESES, "promote": PROMOTE, "judge": JUDGE,
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": "sealed: fx-majors 2017-01 on, opened only through ID-1's holdout procedure"},
            "costs": id1.COSTS.__dict__, "cost_grid": id1.COST_GRID, "slippage_stress_pips": id1.SLIP_STRESS,
            "risk_pct": id1.RISK_PCT, "random_seeds": id1.RANDOM_SEEDS, "t_required_validation": round(max(3.0, t), 4)}


def signals(hid: str, panel: dict, params: dict | None = None) -> dict:
    _, rule, symbols, _ = HYPOTHESES[hid]
    fn = getattr(Q, rule)
    return {k: fn(b, **(params or {})) for k, b in panel.items() if k in symbols}


def sub(panel: dict, hid: str) -> dict:
    return {k: b for k, b in panel.items() if k in HYPOTHESES[hid][2]}


def judge(hid, panel, rates, period, t_req) -> dict:
    """ID-1's validation, gate for gate (scripts/id1.py `validate`), on these rules."""
    p = sub(panel, hid)
    sig = signals(hid, p)
    tr = id1.run_trades(p, sig, rates, period)
    s = id1.evaluate(tr, period, p)
    mr = id1.matched(p, sig, rates, period)
    vs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in mr])) if tr and mr else None
    stress = {f"x{k}": id1._brief(id1.evaluate(id1.run_trades(p, sig, rates, period, id1.COSTS.stressed(k)), period))
              for k in id1.COST_GRID}
    stress["slippage_0.3"] = id1._brief(id1.evaluate(id1.run_trades(p, sig, rates, period,
                                                                    ID.Costs(slippage_pips=id1.SLIP_STRESS)), period))
    grid = []
    for cell in id1._grid(HYPOTHESES[hid][3]):
        gs = id1.evaluate(id1.run_trades(p, signals(hid, p, cell), rates, period), period)
        grid.append({"params": cell, "trades": gs.get("trades"), "net_r": gs.get("net_r"), "t_day": gs.get("t_day")})
    sym = [v for v in s.get("by_symbol", {}).values() if v["trades"] >= 30]
    gates = {"t_day": (s.get("t_day") or 0) >= t_req, "net_r": (s.get("net_r") or 0) > 0,
             "profit_factor": (s.get("profit_factor") or 0) >= 1.2,
             "costs_x1.5": (stress["x1.5"].get("net_r") or 0) > 0,
             "symbols_positive": bool(sym) and np.mean([v["net_r"] > 0 for v in sym]) >= 0.6,
             "three_month_windows": (s.get("windows", {}).get("3m", {}).get("profitable_share") or 0) >= 0.6,
             "beats_matched_random": (vs or 0) >= 2.0,
             "grid": np.mean([(c["net_r"] or 0) > 0 for c in grid]) >= 0.75}
    return {"summary": id1._brief(s), "detail": s, "matched_random": id1._brief(id1.evaluate(mr, period)),
            "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None, "stress": stress, "grid": grid,
            "gates": gates, "passed": all(gates.values())}


def _check_frozen(reg):
    frozen = json.loads(SPEC.read_text())
    if reg.get(PID).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


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
    reg.register(Trial(id=PID, registered=now, title="QT-1: the Quarters schools on M5 (price quarter levels, "
                                                     "the Quarterly Theory's time quarters)",
                       hypothesis="Does either Quarters school, as precise M5 rules, earn a significant net expectancy "
                                  "after measured bid/ask spreads, commission, slippage and financing, beyond matched "
                                  "random entries?",
                       uses=(Use("fx-majors", DEV[0], DEV[1], "select"), Use("fx-majors", VAL[0], VAL[1], "judge")),
                       tests=len(HYPOTHESES), configurations=sum(len(id1._grid(h[3])) for h in HYPOTHESES.values()),
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_run(now):
    reg = id1._registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required_validation"]
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    body: dict = {"program": PID, "spec_sha256": frozen["sha256"], "t_required_validation": t_req,
                  "development": {}, "validation": {}}
    dev = id1.load(DEV)
    for hid in HYPOTHESES:
        p = sub(dev, hid)
        sig = signals(hid, p)
        tr = id1.run_trades(p, sig, rates, DEV)
        s = id1.evaluate(tr, DEV, p)
        mr = id1.matched(p, sig, rates, DEV)
        vs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in mr])) if tr and mr else None
        g = id1.promote_gates(s, vs)
        body["development"][hid] = {"summary": id1._brief(s), "detail": s, "matched_random": id1._brief(id1.evaluate(mr, DEV)),
                                    "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None,
                                    "gates": g, "promoted": all(g.values())}
        print(hid, "dev", json.dumps(id1._brief(s)), "vsR", vs, "promoted", all(g.values()), flush=True)
    promoted = [h for h in HYPOTHESES if body["development"][h]["promoted"]]
    body["promoted"] = promoted
    if promoted:
        val = id1.load(VAL)
        for hid in promoted:
            body["validation"][hid] = judge(hid, val, rates, VAL, t_req)
            print(hid, "val", json.dumps(body["validation"][hid]["summary"]), "passed",
                  body["validation"][hid]["passed"], flush=True)
    passers = [h for h in promoted if body["validation"][h]["passed"]]
    body["passers"], body["verdict"] = passers, ("PASSED" if passers else "FAILED")
    art = id1._write(PID, body)
    reg.record_verdict(Verdict(PID, now, art["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                          "artifact_sha256": art["sha256"]}))
    print("verdict", art["verdict"], "promoted", promoted, "passers", passers)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "run": lambda: cmd_run(now)}.get(
        cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
