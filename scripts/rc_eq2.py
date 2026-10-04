"""RC-EQ2: replicate RC-EQ's two PROMISING candidates on universe B; judge Halloween on universe A
(research/preregistrations/RC-EQ2.md).

Runs on a GitHub runner (.github/workflows/rc-eq2-run.yml):

    python scripts/rc_eq2.py fetch       # universe A again (RC-EQ's raw files are not committed)
    python scripts/rc_eq2.py spec | preregister
    python scripts/rc_eq2.py judge       # E8 HALLOWEEN on universe A, 1990-2020, RC-EQ's gates
    python scripts/rc_eq2.py replicate   # opens universe B once: E1 TOM, E7 ENSEMBLE (+ E8 if it passed A)

E1 and E7 are evaluated by RC-EQ's frozen code (scripts/rc_eq.py, code hash checked), unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import rc_eq  # noqa: E402
from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import rc, rc2, retail  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID, HID = "RC-EQ2", "RC-EQ2-H"
DOC = "research/preregistrations/RC-EQ2.md"
SPEC = R / "specs" / "RC-EQ2.json"
HOLDOUT_FILE = R / "holdout-rc-eq.json"
OUT = R / "knowledge"
DATA = rc_eq.DATA
CODE = ("aitrader/research/discovery/rc2.py", "scripts/rc_eq2.py", *rc_eq.CODE)
E8 = ("RCEQ2-E8-HALLOWEEN", {"enter_month": 10, "exit_month": 4},
      {"enter_month": [9, 10, 11], "exit_month": [3, 4, 5]})
REPLICATE = ("RCEQ-E1-TOM", "RCEQ-E7-ENSEMBLE")  # RC-EQ PROMISING, rules frozen in research/specs/RC-EQ.json
MODERN_B = (date(2009, 1, 1), rc_eq.B_PERIOD[1])
B_GATES = {
    "t": "t of the mean monthly net over universe B, 1990-01 -> 2026-09, >= z(1 - 0.05/k), k = candidates on B",
    "before_2021": "mean net > 0 before 2021", "from_2021": "mean net > 0 from 2021",
    "modern": "mean net > 0 from 2009", "costs_x2": "mean net > 0 with every cost doubled",
    "delay": "mean net > 0 with every fill one close later",
}
CLASSES = {"RCEQ-E1-TOM": "B pass -> PROMISING_REPLICATED, else REJECTED (it failed RC-EQ's t gate on A, so it "
                          "cannot become VALIDATED here)",
           "RCEQ-E7-ENSEMBLE": "same as E1",
           "RCEQ2-E8-HALLOWEEN": "every RC-EQ gate on A -> sent to B; A and B pass -> VALIDATED; else REJECTED "
                                 "(PROMISING on A as defined by RC-EQ is reported, not sent to B)"}


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(HOLDOUT_FILE))


def spec(reg: Registry) -> dict:
    t1 = reg.threshold_for_next("multi-asset-long", *rc_eq.JUDGE, new_tests=1)
    t2 = reg.threshold_for_next("multi-asset-etf", date(2008, 1, 1), rc_eq.JUDGE[1], new_tests=1)
    frozen_eq = json.loads((R / "specs" / "RC-EQ.json").read_text())
    return {"program": PID, "versions": {"retail": retail.RETAIL_VERSION, "rc": rc.RC_VERSION, "rc2": rc2.RC2_VERSION},
            "e8": E8, "e8_gates": rc_eq.GATES, "replicate": REPLICATE,
            "replicate_frozen_in": {"spec_sha256": frozen_eq["sha256"], "code_sha256": frozen_eq["code_sha256"]},
            "universe_a": rc_eq.UNIVERSE_A, "universe_b": rc_eq.UNIVERSE_B,
            "periods": {"judge_a": [str(d) for d in rc_eq.JUDGE], "b": [str(d) for d in rc_eq.B_PERIOD],
                        "b_split": str(rc_eq.B_SPLIT), "b_modern": [str(d) for d in MODERN_B]},
            "b_gates": B_GATES, "classes": CLASSES, "costs": rc_eq.COSTS.__dict__,
            "t_required_e8": round(max(rc_eq.T_FLOOR, t1, t2), 4)}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _grid(g):
    cells = [{}]
    for k, vals in g.items():
        cells = [{**c, k: v} for c in cells for v in vals]
    return cells


def evaluate_e8(days, closes, universe, rates, period, sub, params=None, grid=True) -> dict:
    """RC-EQ's evaluation, for the Halloween rule (same simulator, same statistics)."""
    inst = rc_eq.instruments(universe)
    rate = lambda key, d: rates.at(key, d)  # noqa: E731
    build = lambda p: rc2.halloween(days, closes, len(universe), **p)  # noqa: E731
    tg = build(params or E8[1])
    res = retail.simulate(days, closes, tg, inst, rate, rc_eq.COSTS)
    out = {"net": retail.summarize(res, *period),
           "costs_x2": retail.summarize(retail.simulate(days, closes, tg, inst, rate, rc_eq.COSTS.stressed()), *period),
           "delay": retail.summarize(retail.simulate(days, closes, retail.delay(tg, closes, 1), inst, rate, rc_eq.COSTS), *period),
           "before_broker": retail.summarize(retail.simulate(days, closes, tg, inst, rate, rc_eq.COSTS.frictionless()), *period),
           "by_year": retail.by_year(res, *period), "leverage": retail.leverage_table(res, *period),
           "sub": {k: retail.summarize(res, *p) for k, p in sub.items()},
           "per_instrument": {n: retail.summarize(res, *period, names=[n]) for n in universe},
           "leave_one_out": {n: round(rc_eq._mean(res, period, [m for m in universe if m != n]), 6) for n in universe}}
    if grid:
        cells = []
        for cell in _grid(E8[2]):
            s = retail.summarize(retail.simulate(days, closes, build(cell), inst, rate, rc_eq.COSTS), *period)
            cells.append({"params": cell, "mean_monthly": s.get("mean_monthly"), "t": s.get("t"),
                          "annual_return": s.get("annual_return")})
        out["grid"] = cells
    out["_res"] = res
    return out


def _write(name, body):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def _check_frozen(reg, trial_id):
    frozen = json.loads(SPEC.read_text())
    if reg.get(trial_id).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    eq = json.loads((R / "specs" / "RC-EQ.json").read_text())
    if eq["code_sha256"] != rc_eq.code_hash():
        raise SystemExit("RC-EQ's frozen code changed; E1/E7 would not be the rules that were judged")
    return frozen


def cmd_fetch():
    for k, v in rc_eq._fetch(rc_eq.UNIVERSE_A, "A2").items():
        print(k, v["first"], v["last"], v["rows"])


def cmd_spec():
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "t_required_e8", s["t_required_e8"])


def cmd_preregister(now):
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="RC-EQ2: Halloween on universe A (RC-EQ's gates)",
                       hypothesis="Does holding index CFDs only November-April earn a significant net return after "
                                  "retail costs over 1990-2020?",
                       uses=(Use("multi-asset-long", rc_eq.JUDGE[0], rc_eq.JUDGE[1], "judge"),
                             Use("multi-asset-etf", date(2008, 1, 1), rc_eq.JUDGE[1], "judge")),
                       tests=1, configurations=len(_grid(E8[2])), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required_e8"]
    rates = rc.Rates(DATA / "policy_rates.csv")
    days, closes, report = rc_eq.load(rc_eq.UNIVERSE_A, rc_eq.JUDGE[1])
    sub = {"development": rc_eq.DEV, "validation": rc_eq.VAL, "modern": rc_eq.MODERN}
    e = evaluate_e8(days, closes, rc_eq.UNIVERSE_A, rates, rc_eq.JUDGE, sub)
    res = e.pop("_res")
    e["regimes"] = rc_eq._regimes(res, days, closes)
    e["gates"] = rc_eq.gates(e, t_req)
    e["passed"] = all(e["gates"].values())
    e["failed_gates"] = [k for k, v in e["gates"].items() if not v]
    s = e["net"]
    e["classification"] = ("HOLDOUT_ELIGIBLE" if e["passed"] else
                           "PROMISING" if ((s.get("t") or 0) >= 2.0 and e["gates"]["development"]
                                           and e["gates"]["validation"] and e["gates"]["costs_x2"]) else "REJECTED")
    print(E8[0], json.dumps({k: s.get(k) for k in ("n", "annual_return", "t", "sharpe", "max_drawdown", "trades",
                                                   "financing_annual")}), "failed:", e["failed_gates"], flush=True)
    passers = [E8[0]] if e["passed"] else []
    body = _write(PID, {"program": PID, "kind": "retail", "results": {E8[0]: e}, "passers": passers,
                        "verdict": "PASSED" if passers else "FAILED", "classification": {E8[0]: e["classification"]},
                        "data": {"cleaning": report, "fetch": json.loads((DATA / "fetch_manifest_A2.json").read_text())},
                        "t_required": t_req, "spec_sha256": frozen["sha256"]})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print("verdict", body["verdict"])


def cmd_replicate(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if reg.verdict_of(PID) is None:
        raise SystemExit("judge E8 first: the candidate list depends on it")
    cands = list(REPLICATE) + judged["passers"]
    reg.register(Trial(id=HID, registered=now, title="RC-EQ2 replication: universe B (never loaded)", hypothesis=", ".join(cands),
                       uses=(Use("equity-index-b", date(1900, 1, 1), date(2100, 1, 1), "judge"),), tests=len(cands),
                       configurations=len(cands), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": cands}))
    open_final_test(reg, HID)
    rc_eq._fetch(rc_eq.UNIVERSE_B, "B")
    rates = rc.Rates(DATA / "policy_rates.csv")
    days, closes, report = rc_eq.load(rc_eq.UNIVERSE_B, rc_eq.B_PERIOD[1])
    z = NormalDist().inv_cdf(1 - 0.05 / len(cands))
    sub = {"before_2021": (rc_eq.B_PERIOD[0], rc_eq.B_SPLIT), "from_2021": (rc_eq.B_SPLIT, rc_eq.B_PERIOD[1]),
           "modern": MODERN_B}
    out = {}
    for hid in cands:
        if hid == E8[0]:
            e = evaluate_e8(days, closes, rc_eq.UNIVERSE_B, rates, rc_eq.B_PERIOD, sub, grid=False)
        else:
            e = rc_eq.evaluate(hid, days, closes, rc_eq.UNIVERSE_B, rates, rc_eq.B_PERIOD, sub, grid=False)
        e.pop("_res")
        g = {"t": (e["net"].get("t") or 0) >= z,
             **{k: (e["sub"][k].get("mean_monthly") or 0) > 0 for k in ("before_2021", "from_2021", "modern")},
             "costs_x2": (e["costs_x2"].get("mean_monthly") or 0) > 0, "delay": (e["delay"].get("mean_monthly") or 0) > 0}
        ok = all(g.values())
        verdict = ("VALIDATED" if hid == E8[0] else "PROMISING_REPLICATED") if ok else "REJECTED"
        e.update(gates=g, verdict=verdict, failed_gates=[k for k, v in g.items() if not v])
        out[hid] = e
        print(hid, verdict, json.dumps({k: e["net"].get(k) for k in ("n", "annual_return", "t", "sharpe", "max_drawdown")}),
              "failed:", e["failed_gates"], flush=True)
    verdict = "PASSED" if any(v["verdict"] != "REJECTED" for v in out.values()) else "FAILED"
    body = _write(HID, {"program": HID, "kind": "retail", "holdout_of": PID, "results": out, "verdict": verdict,
                        "t_required": round(z, 4), "classification": {h: v["verdict"] for h, v in out.items()},
                        "data": {"cleaning": report, "fetch": json.loads((DATA / "fetch_manifest_B.json").read_text())}})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print("replication verdict", verdict)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"fetch": cmd_fetch, "spec": cmd_spec, "preregister": lambda: cmd_preregister(now),
     "judge": lambda: cmd_judge(now), "replicate": lambda: cmd_replicate(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
