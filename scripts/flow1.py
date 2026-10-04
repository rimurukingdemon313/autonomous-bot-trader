"""FLOW-1 runner: scheduled order flow at the Tokyo and London fixes.

    python scripts/flow1.py spec          # freeze the design (reads no outcome)
    python scripts/flow1.py preregister   # register in research/registry.jsonl
    python scripts/flow1.py judge         # 2007-04..2016-12: development, validation, gates
    python scripts/flow1.py holdout       # only for passers; opens the sealed 2017+ data once

The design is in research/preregistrations/FLOW-1.md. Each command refuses to run if the code or
the spec changed since registration.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.store import DataStore, open_final_test  # noqa: E402
from aitrader.research.discovery import flow  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID, HID = "FLOW-1", "FLOW-1-H"
DOC = "research/preregistrations/FLOW-1.md"
SPEC = R / "specs" / "FLOW-1.json"
OUT = R / "knowledge"
UNIVERSE = "fx-majors"
CODE = ("aitrader/research/discovery/flow.py", "scripts/flow1.py", "aitrader/data/store.py", "aitrader/data/bars.py")

DEV = (date(2007, 4, 1), date(2012, 1, 1))
VAL = (date(2012, 1, 1), date(2017, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2017, 1, 1), date(2018, 6, 1))

HYPOTHESES = {
    "FLOW1-H1-GOTOBI-PRE": "On Tokyo gotobi days USDJPY rises from 08:00 to 10:00 JST (importers' dollar demand into the 09:55 fix): long",
    "FLOW1-H2-GOTOBI-POST": "On gotobi days USDJPY falls from 10:00 to 12:00 JST (the demand is gone after the fix): short",
    "FLOW1-H3-FIX-MONTHEND": "On the last business day of the month, the 15:00-15:45 London move of the USD majors reverses from 16:15 to 17:15 London: fade it",
    "FLOW1-H4-FIX-DAILY": "On all other business days, the same fade of the pre-fix move",
}
GATES = {
    "t": "t of the mean net bps over the judged period >= the registry's Bonferroni threshold",
    "development": "mean net > 0 in 2007-04..2011",
    "validation": "mean net > 0 in 2012..2016",
    "years": ">= 60% of years with >= 20 observations have positive net",
    "costs_x2": "mean net > 0 with spread, slippage and commission all doubled",
    "top_year": "no single year supplies more than 50% of the total net",
    "leave_one_pair_out": "H3/H4: mean net > 0 leaving out any one pair",
    "specificity": "H1/H2: the gotobi mean exceeds the same window on non-gotobi days (Welch t >= 2)",
}
HOLDOUT_RULE = "holdout mean net > 0 with one-sided t >= z(0.05 / passers), and mean net > 0 with costs x2"


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec(reg: Registry) -> dict:
    return {
        "program": PID, "version": flow.FLOW_VERSION, "universe": UNIVERSE,
        "question": "Do scheduled, non-informational orders at the Tokyo and London fixes move prices predictably, after costs?",
        "hypotheses": HYPOTHESES, "gates": GATES, "holdout_rule": HOLDOUT_RULE,
        "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                    "judged": [str(d) for d in JUDGE], "holdout": [str(d) for d in HOLD]},
        "costs": flow.Costs().__dict__, "costs_x2": flow.Costs().stressed(2.0).__dict__,
        "fix_pairs": list(flow.FIX_PAIRS), "min_fix_pairs": flow.MIN_FIX_PAIRS,
        "threshold_t": round(reg.threshold_for_next(UNIVERSE, JUDGE[0], JUDGE[1], new_tests=len(HYPOTHESES)), 4),
        "prior_tests_on_period": reg.tests_on(UNIVERSE, JUDGE[0], JUDGE[1]),
        "data_note": "hour 00 UTC is absent from the source for 12 of 13 instruments; H1/H2 use the 23:00, 01:00 "
                     "and 03:00 UTC bar opens, which exist",
    }


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def opens(store: DataStore, key=None) -> dict[str, flow.Opens]:
    return {s: flow.Opens(store.load(s, "M15", key=key)) for s in flow.FIX_PAIRS}


def events(op: dict, start: date, end: date, costs: flow.Costs) -> dict[str, list[dict]]:
    got = flow.gotobi_dates(start, end)
    month_end = flow.last_business_days(start, end)
    others = [d for d in flow.business_days(start, end) if d not in set(month_end)]
    non_gotobi = [d for d in flow.business_days(start, end) if d not in set(got)]
    fix_pairs = {s: op[s] for s in flow.FIX_PAIRS}
    return {
        "FLOW1-H1-GOTOBI-PRE": flow.gotobi_events(op["USDJPY"], got, "pre", costs),
        "FLOW1-H2-GOTOBI-POST": flow.gotobi_events(op["USDJPY"], got, "post", costs),
        "FLOW1-H3-FIX-MONTHEND": flow.fix_events(fix_pairs, month_end, costs),
        "FLOW1-H4-FIX-DAILY": flow.fix_events(fix_pairs, others, costs),
        "control-pre": flow.gotobi_events(op["USDJPY"], non_gotobi, "pre", costs),
        "control-post": flow.gotobi_events(op["USDJPY"], non_gotobi, "post", costs),
    }


def _period(evs, a, b):
    return [e for e in evs if a <= e["date"] < b]


def _leave_one_pair_out(evs: list[dict]) -> dict:
    pairs = sorted({p for e in evs for p in e["legs"]})
    out = {}
    for p in pairs:
        vals = [np.mean([v for q, v in e["legs"].items() if q != p]) for e in evs if any(q != p for q in e["legs"])]
        out[p] = round(float(np.mean(vals)), 4) if vals else None
    return out


def judge_one(hid: str, evs: list[dict], evs_x2: list[dict], control: list[dict] | None, threshold: float) -> dict:
    s = flow.summary(evs)
    years = flow.by_year(evs)
    big = {y: v for y, v in years.items() if v["n"] >= 20}
    total = sum(v["total"] for v in years.values())
    pos_total = sum(v["total"] for v in years.values() if v["total"] > 0)
    res = {
        "net": s, "gross": flow.summary(evs, "gross_bps"), "cost": flow.summary(evs, "cost_bps"),
        "development": flow.summary(_period(evs, *DEV)), "validation": flow.summary(_period(evs, *VAL)),
        "costs_x2": flow.summary(evs_x2), "by_year": years,
        "max_drawdown_bps": round(flow.max_drawdown([e["net_bps"] for e in evs]), 3),
        "long_short": {side: flow.summary([e for e in evs if e.get("side") == side])
                       for side in (+1, -1)} if "side" in (evs[0] if evs else {}) else None,
    }
    gates = {
        "t": s["t"] is not None and s["t"] >= threshold,
        "development": (res["development"]["mean"] or 0) > 0,
        "validation": (res["validation"]["mean"] or 0) > 0,
        "years": bool(big) and sum(v["mean"] > 0 for v in big.values()) >= 0.6 * len(big),
        "costs_x2": (res["costs_x2"]["mean"] or 0) > 0,
        "top_year": total > 0 and max((v["total"] for v in years.values()), default=0) <= 0.5 * pos_total,
    }
    if control is not None:
        wt = flow.welch_t([e["net_bps"] for e in evs], [e["net_bps"] for e in control])
        res["control"] = {"non_gotobi": flow.summary(control), "welch_t": None if wt is None else round(wt, 3)}
        gates["specificity"] = wt is not None and wt >= 2.0
    else:
        res["leave_one_pair_out"] = _leave_one_pair_out(evs)
        res["by_pair"] = {p: flow.summary([{"net_bps": e["legs"][p]} for e in evs if p in e["legs"]])
                          for p in flow.FIX_PAIRS}
        gates["leave_one_pair_out"] = bool(res["leave_one_pair_out"]) and all(
            v is not None and v > 0 for v in res["leave_one_pair_out"].values())
    res["gates"] = gates
    res["passed"] = all(gates.values())
    res["failed_gates"] = [k for k, v in gates.items() if not v]
    return res


def _check_frozen(reg: Registry, trial_id: str) -> dict:
    trial = reg.get(trial_id)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec():
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "threshold", s["threshold_t"])


def cmd_preregister(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    if spec_sha(s) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {frozen['sha256']}")
    reg.register(Trial(id=PID, registered=now, title="FLOW-1: scheduled order flow at the Tokyo and London fixes",
                       hypothesis=s["question"], uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),),
                       tests=len(HYPOTHESES), configurations=len(HYPOTHESES), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    frozen = _check_frozen(reg, PID)
    thr = frozen["spec"]["threshold_t"]
    store = DataStore(ROOT / "data" / "processed", holdout)
    op = opens(store)  # no key: the sealed 2017+ data is truncated away
    base = events(op, *JUDGE, flow.Costs())
    x2 = events(op, *JUDGE, flow.Costs().stressed(2.0))
    results = {}
    for hid in HYPOTHESES:
        ctrl = base["control-pre"] if hid.endswith("PRE") else base["control-post"] if hid.endswith("POST") else None
        results[hid] = judge_one(hid, base[hid], x2[hid], ctrl, thr)
    passers = [h for h, r in results.items() if r["passed"]]
    body = _write(PID, {"program": PID, "kind": "flow", "threshold": thr, "periods": frozen["spec"]["periods"],
                        "results": results, "passers": passers, "verdict": "PASSED" if passers else "FAILED",
                        "classification": {h: ("HOLDOUT_ELIGIBLE" if r["passed"] else "REJECTED") for h, r in results.items()},
                        "spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    for h, r in results.items():
        print(h, json.dumps(r["net"]), "dev", r["development"]["mean"], "val", r["validation"]["mean"],
              "x2", r["costs_x2"]["mean"], "failed:", r["failed_gates"])
    print("passers:", passers)


def cmd_holdout(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    frozen = _check_frozen(reg, PID)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    passers = judged["passers"]
    if not passers:
        raise SystemExit("no hypothesis passed: the sealed holdout stays sealed")
    reg.register(Trial(id=HID, registered=now, title=f"FLOW-1 sealed holdout: {', '.join(passers)}",
                       hypothesis="; ".join(HYPOTHESES[h] for h in passers),
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=len(passers), configurations=len(passers),
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "candidates": passers}))
    key = open_final_test(reg, HID)
    op = opens(DataStore(ROOT / "data" / "processed", holdout), key)
    base, x2 = events(op, *HOLD, flow.Costs()), events(op, *HOLD, flow.Costs().stressed(2.0))
    z = NormalDist().inv_cdf(1 - 0.05 / len(passers))
    out = {}
    for h in passers:
        s, s2 = flow.summary(base[h]), flow.summary(x2[h])
        ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= z and (s2["mean"] or 0) > 0)
        out[h] = {"net": s, "gross": flow.summary(base[h], "gross_bps"), "costs_x2": s2, "by_year": flow.by_year(base[h]),
                  "required_t": round(z, 3), "verdict": "VALIDATED" if ok else "REJECTED"}
    verdict = "PASSED" if any(v["verdict"] == "VALIDATED" for v in out.values()) else "FAILED"
    body = _write(HID, {"program": HID, "kind": "flow", "holdout_of": PID, "period": [str(d) for d in HOLD],
                        "results": out, "verdict": verdict,
                        "classification": {h: v["verdict"] for h, v in out.items()}})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    for h, v in out.items():
        print(h, json.dumps(v["net"]), "x2", v["costs_x2"]["mean"], v["verdict"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "judge": lambda: cmd_judge(now),
     "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
