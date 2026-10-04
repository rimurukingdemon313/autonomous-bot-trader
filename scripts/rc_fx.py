"""RC-FX: the two FX questions this project has not yet asked (research/preregistrations/RC-FX.md).

Runs locally (H.10, BIS rates and COT are in data/):

    python scripts/rc_fx.py spec
    python scripts/rc_fx.py preregister
    python scripts/rc_fx.py judge      # 1990-01 -> 2016-12 (X1); 2007-04 -> 2016-12 (X2); the 2017+ seal holds
    python scripts/rc_fx.py holdout    # only for an X1 pass: opens the fx-majors holdout (2017+) once

X1 combines carry, momentum and value (each failed alone in RV-1/XS-001; the combination was never
tested). X2 asks whether COT positioning adds value as a low-frequency filter on monthly trend.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data import h10  # noqa: E402
from aitrader.data.cot import CotStore  # noqa: E402
from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import rc, retail  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID, HID = "RC-FX", "RC-FX-H"
DOC = "research/preregistrations/RC-FX.md"
SPEC = R / "specs" / "RC-FX.json"
HOLDOUT_FILE = R / "holdout.json"  # the project's fx-majors holdout, 2017-01-01 onward
OUT = R / "knowledge"
NY = ZoneInfo("America/New_York")
CODE = ("aitrader/research/discovery/retail.py", "aitrader/research/discovery/rc.py", "scripts/rc_fx.py")
AREA = {"USD": "US", "EUR": "XM", "GBP": "GB", "JPY": "JP", "AUD": "AU", "NZD": "NZ", "CAD": "CA", "CHF": "CH"}
#: currency -> (spread pips in the market quote, pip, market quote is USD per unit)
FX = {"EUR": (0.2, 0.0001, True), "GBP": (0.5, 0.0001, True), "AUD": (0.3, 0.0001, True), "NZD": (0.5, 0.0001, True),
      "JPY": (0.3, 0.01, False), "CHF": (0.5, 0.0001, False), "CAD": (0.5, 0.0001, False)}
JUDGE = (date(1990, 1, 1), date(2017, 1, 1))
DEV = (date(1990, 1, 1), date(2004, 1, 1))
VAL = (date(2004, 1, 1), date(2017, 1, 1))
MODERN = (date(2009, 1, 1), date(2017, 1, 1))
COT_JUDGE = (date(2007, 4, 1), date(2017, 1, 1))
COT_HALVES = ((date(2007, 4, 1), date(2012, 1, 1)), (date(2012, 1, 1), date(2017, 1, 1)))
HOLD = (date(2017, 1, 1), date(2026, 10, 1))
HOLD_SPLIT = date(2022, 1, 1)
COSTS = retail.Costs()
T_FLOOR = 3.0
MAX_DD = 0.30
TOP_YEAR = 0.30
HYPOTHESES = {
    "RCFX-X1-COMPOSITE": ("composite", {"mom": 252, "value_years": 5.0, "k": 2},
                          {"mom": [126, 189, 252], "value_years": [4.0, 5.0, 6.0], "k": [2, 3]}),
    "RCFX-X2-COT-FILTER": ("cot_filter", {"lookback": 252, "threshold": 0.90},
                           {"lookback": [126, 252], "threshold": [0.80, 0.90, 0.95]}),
}
GATES = {
    "t": "t of the mean monthly net return over the judged period >= max(3.0, the registry's Bonferroni value)",
    "development": "X1: mean net > 0 in 1990-2003; X2: in 2007-04..2011", "validation": "X1: mean net > 0 in 2004-2016; X2: in 2012-2016",
    "modern": "mean net > 0 in 2009-2016", "costs_x2": "mean net > 0 with every cost assumption doubled",
    "delay": "mean net > 0 with every fill one fixing later", "leave_one_out": "mean net > 0 leaving out any one currency",
    "top_year": f"no year supplies more than {TOP_YEAR:.0%} of the sum of positive years",
    "region": "at least 75% of the grid has mean net > 0 and its median t >= 2.0",
    "drawdown": f"maximum drawdown (sum of monthly net, 1x) <= {MAX_DD:.0%}",
    "value_added": "X2 only: (filtered - unfiltered) monthly mean > 0 with paired t >= 2.0, > 0 in both halves, "
                   "and > 0 in at least 75% of the grid",
}
CLASSES = ("X1: HOLDOUT_ELIGIBLE if every gate passes, else REJECTED. X2 is never holdout-eligible: its base (monthly "
           "FX trend) is already rejected (CP-001, R2D) and 2007-2016 is too short to prove an absolute edge; it is "
           "PROMISING if value_added passes and its own mean net > 0 (COT is then worth a separate preregistered "
           "study), else REJECTED")
HOLDOUT_RULE = ("fx-majors 2017-01 -> 2026-09, once, passers only: t >= z(1 - 0.05/k) one-sided; mean net > 0 in "
                "2017-2021 and in 2022-2026; costs_x2 > 0. H.10 vintage 2026-09-29 (inverse rounded to 4 decimals, "
                "at most ~0.6 bp per fixing: declared)")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(HOLDOUT_FILE))


def spec(reg: Registry) -> dict:
    t = reg.threshold_for_next("fx-majors", *JUDGE, new_tests=len(HYPOTHESES))
    return {"program": PID, "versions": {"retail": retail.RETAIL_VERSION, "rc": rc.RC_VERSION, "h10": h10.H10_VERSION},
            "fx": FX, "areas": AREA, "costs": COSTS.__dict__, "costs_x2": COSTS.stressed().__dict__,
            "periods": {"judge": [str(d) for d in JUDGE], "development": [str(d) for d in DEV],
                        "validation": [str(d) for d in VAL], "modern": [str(d) for d in MODERN],
                        "cot_judge": [str(d) for d in COT_JUDGE], "cot_halves": [[str(a), str(b)] for a, b in COT_HALVES],
                        "holdout": [str(d) for d in HOLD], "holdout_split": str(HOLD_SPLIT)},
            "hypotheses": HYPOTHESES, "gates": GATES, "classes": CLASSES, "holdout_rule": HOLDOUT_RULE,
            "t_required": round(max(T_FLOOR, t), 4), "fx_lag_fixings": rc.FX_LAG}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


# ── data ────────────────────────────────────────────────────────────────

def fixings(series: dict[str, h10.H10Series], end: date):
    """USD per unit of each currency on the union of H.10 dates before `end` (NaN = no fixing)."""
    days = sorted({d for s in series.values() for d in s.dates if d < end})
    pos = {d: i for i, d in enumerate(days)}
    out = {}
    for c in FX:
        s = series[c]
        a = np.full(len(days), np.nan)
        for d, v in zip(s.dates, s.value):
            if d in pos:
                a[pos[d]] = v if FX[c][2] else 1.0 / v
        out[c] = a
    return days, out


def load_judge():
    store = h10.H10Store(ROOT / "data" / "h10", Holdout.load(HOLDOUT_FILE))
    return fixings(store.load(), JUDGE[1])


def load_holdout(key):
    if key is None:
        raise SystemExit("the 2026 vintage is holdout data: a key from open_final_test is required")
    name = "2026-09-29"
    fname = h10.vintage_file(name)
    raw = (ROOT / "data" / "h10" / fname).read_bytes()
    want = json.loads((ROOT / "data" / "h10" / "manifest.json").read_text())["files"][fname]["sha256"]
    if hashlib.sha256(raw).hexdigest() != want:
        raise SystemExit(f"{fname} does not match data/h10/manifest.json; refusing")
    return fixings(h10.official_series(raw, require_grid=False), HOLD[1])


def instruments() -> dict:
    return {c: retail.Instrument(c, "fx", c, spread_pips=sp, pip=pip, usd_per_unit_quote=q) for c, (sp, pip, q) in FX.items()}


def cot_pct(days, key=None):
    """pct(ccy, j): COT-1's leveraged-money percentile public at 17:00 New York the day before fill j."""
    cot = CotStore(ROOT / "data" / "cot", Holdout.load(HOLDOUT_FILE)).load(key)

    def pct(ccy, j):
        if j < 1 or ccy not in cot:
            return float("nan")
        s = cot[ccy]
        d = days[j - 1]
        t = int(datetime(d.year, d.month, d.day, 17, tzinfo=NY).timestamp())
        share = (s.fields["lev_long"] - s.fields["lev_short"]) / np.where(s.fields["oi"] > 0, s.fields["oi"], np.nan)
        return rc.cot_percentile(s.as_of, s.available_at, share, t)

    return pct


# ── rules and evaluation ────────────────────────────────────────────────

def targets(rule, params, days, usd, rates, pct=None):
    carry = lambda c, d: rates.at(AREA[c], d)  # noqa: E731
    if rule == "composite":
        return rc.fx_composite(days, usd, carry, mom=params["mom"], value_years=params["value_years"], k=params["k"])
    if rule == "tsmom":
        return rc.fx_tsmom(days, usd, lookback=params["lookback"])
    if rule == "cot_filter":
        base = rc.fx_tsmom(days, usd, lookback=params["lookback"])
        return rc.cot_filter(days, base, pct, params["threshold"])
    raise ValueError(rule)


def _grid(g):
    cells = [{}]
    for k, vals in g.items():
        cells = [{**c, k: v} for c in cells for v in vals]
    return cells


def _months(res, period, names=None):
    return dict(retail.monthly(res.dates, res.net(names), *period))


def evaluate(hid, days, usd, rates, period, sub, pct=None, grid=True):
    rule, params, g = HYPOTHESES[hid]
    inst = instruments()
    rate = lambda c, d: rates.at(AREA[c], d)  # noqa: E731
    tg = targets(rule, params, days, usd, rates, pct)
    res = retail.simulate(days, usd, tg, inst, rate, COSTS)
    e = {"net": retail.summarize(res, *period),
         "costs_x2": retail.summarize(retail.simulate(days, usd, tg, inst, rate, COSTS.stressed()), *period),
         "delay": retail.summarize(retail.simulate(days, usd, retail.delay(tg, usd, 1), inst, rate, COSTS), *period),
         "before_broker": retail.summarize(retail.simulate(days, usd, tg, inst, rate, COSTS.frictionless()), *period),
         "by_year": retail.by_year(res, *period), "leverage": retail.leverage_table(res, *period),
         "sub": {k: retail.summarize(res, *p) for k, p in sub.items()},
         "per_currency": {c: retail.summarize(res, *period, names=[c]) for c in FX},
         "leave_one_out": {c: round(float(np.mean(list(_months(res, period, [m for m in FX if m != c]).values()))), 6)
                           for c in FX}}
    if rule == "cot_filter":
        base = retail.simulate(days, usd, targets("tsmom", {"lookback": params["lookback"]}, days, usd, rates), inst, rate, COSTS)
        e["unfiltered"] = retail.summarize(base, *period)
        e["value_added"] = _value_added(res, base, period)
    if grid and g:
        cells = []
        for cell in _grid(g):
            r = retail.simulate(days, usd, targets(rule, cell, days, usd, rates, pct), inst, rate, COSTS)
            s = retail.summarize(r, *period)
            row = {"params": cell, "mean_monthly": s.get("mean_monthly"), "t": s.get("t"), "annual_return": s.get("annual_return")}
            if rule == "cot_filter":
                b = retail.simulate(days, usd, targets("tsmom", {"lookback": cell["lookback"]}, days, usd, rates), inst, rate, COSTS)
                row["value_added"] = _value_added(r, b, period)["mean_monthly"]
            cells.append(row)
        e["grid"] = cells
    e["_res"] = res
    return e


def _value_added(res, base, period):
    a, b = _months(res, period), _months(base, period)
    d = [a[k] - b.get(k, 0.0) for k in sorted(a)]
    s = retail.month_stats(d)
    halves = {f"{h[0]}..{h[1]}": round(float(np.mean([a[k] - b.get(k, 0.0) for k in a
                                                     if h[0] <= date(k[0], k[1], 1) < h[1]] or [0.0])), 6) for h in COT_HALVES}
    return {**s, "halves": halves}


def gates(e, t_req, rule):
    s = e["net"]
    years = e["by_year"]
    pos = sum(v for v in years.values() if v > 0)
    g = {"t": (s.get("t") or 0) >= t_req,
         "development": (e["sub"]["development"].get("mean_monthly") or 0) > 0,
         "validation": (e["sub"]["validation"].get("mean_monthly") or 0) > 0,
         "modern": (e["sub"]["modern"].get("mean_monthly") or 0) > 0,
         "costs_x2": (e["costs_x2"].get("mean_monthly") or 0) > 0,
         "delay": (e["delay"].get("mean_monthly") or 0) > 0,
         "leave_one_out": all(v > 0 for v in e["leave_one_out"].values()),
         "top_year": pos > 0 and max(years.values(), default=0) <= TOP_YEAR * pos,
         "drawdown": (s.get("max_drawdown") if s.get("max_drawdown") is not None else 9) <= MAX_DD}
    if e.get("grid"):
        g["region"] = (np.mean([(c["mean_monthly"] or 0) > 0 for c in e["grid"]]) >= 0.75
                       and float(np.median([c["t"] or 0 for c in e["grid"]])) >= 2.0)
    if rule == "cot_filter":
        va = e["value_added"]
        g["value_added"] = ((va.get("mean_monthly") or 0) > 0 and (va.get("t") or 0) >= 2.0
                            and all(v > 0 for v in va["halves"].values())
                            and np.mean([(c.get("value_added") or 0) > 0 for c in e["grid"]]) >= 0.75)
    return g


def _write(name, body):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def _check_frozen(reg, trial_id):
    frozen = json.loads(SPEC.read_text())
    if reg.get(trial_id).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec():
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "t_required", s["t_required"])


def cmd_preregister(now):
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="RC-FX: FX factor composite and COT as a low-frequency filter, retail costs",
                       hypothesis="Does a carry+momentum+value composite earn a significant net return after retail "
                                  "FX costs and swaps, and does COT crowding add value to monthly trend?",
                       uses=(Use("fx-majors", JUDGE[0], JUDGE[1], "judge"),), tests=len(HYPOTHESES),
                       configurations=sum(len(_grid(g)) for _, _, g in HYPOTHESES.values()), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required"]
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    days, usd = load_judge()
    pct = cot_pct(days)
    results, monthly_net = {}, {}
    for hid, (rule, _, _) in HYPOTHESES.items():
        if rule == "cot_filter":
            period, sub = COT_JUDGE, {"development": COT_HALVES[0], "validation": COT_HALVES[1], "modern": MODERN}
        else:
            period, sub = JUDGE, {"development": DEV, "validation": VAL, "modern": MODERN}
        e = evaluate(hid, days, usd, rates, period, sub, pct)
        res = e.pop("_res")
        e["gates"] = gates(e, t_req, rule)
        e["failed_gates"] = [k for k, v in e["gates"].items() if not v]
        e["passed"] = rule != "cot_filter" and all(e["gates"].values())
        if e["passed"]:
            e["classification"] = "HOLDOUT_ELIGIBLE"
        elif rule == "cot_filter" and e["gates"]["value_added"] and (e["net"].get("mean_monthly") or 0) > 0:
            e["classification"] = "PROMISING"
        else:
            e["classification"] = "REJECTED"
        results[hid] = e
        monthly_net[hid] = _months(res, period)
        s = e["net"]
        print(hid, json.dumps({k: s.get(k) for k in ("n", "annual_return", "t", "sharpe", "max_drawdown", "trades",
                                                     "financing_annual", "trading_cost_annual")}),
              "failed:", e["failed_gates"], flush=True)
    common = sorted(set(monthly_net["RCFX-X1-COMPOSITE"]) & set(monthly_net["RCFX-X2-COT-FILTER"]))
    corr = float(np.corrcoef([monthly_net["RCFX-X1-COMPOSITE"][k] for k in common],
                             [monthly_net["RCFX-X2-COT-FILTER"][k] for k in common])[0, 1]) if len(common) > 2 else None
    passers = [h for h, r in results.items() if r["passed"]]
    body = _write(PID, {"program": PID, "kind": "retail", "results": results, "passers": passers,
                        "verdict": "PASSED" if passers else "FAILED",
                        "classification": {h: r["classification"] for h, r in results.items()},
                        "correlation_x1_x2_monthly": round(corr, 3) if corr is not None else None,
                        "t_required": t_req, "spec_sha256": frozen["sha256"]})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print("verdict", body["verdict"], "passers", passers)


def cmd_holdout(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    passers = judged["passers"]
    if not passers:
        raise SystemExit("no holdout-eligible candidate: the fx-majors holdout stays sealed")
    reg.register(Trial(id=HID, registered=now, title="RC-FX holdout: fx-majors 2017+", hypothesis=", ".join(passers),
                       uses=(Use("fx-majors", HOLD[0], date(2100, 1, 1), "judge"),), tests=len(passers),
                       configurations=len(passers), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": passers}))
    key = open_final_test(reg, HID)
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    days, usd = load_holdout(key)
    z = NormalDist().inv_cdf(1 - 0.05 / len(passers))
    out = {}
    for hid in passers:
        e = evaluate(hid, days, usd, rates, HOLD, {"2017_2021": (HOLD[0], HOLD_SPLIT), "2022_2026": (HOLD_SPLIT, HOLD[1])},
                     grid=False)
        e.pop("_res")
        g = {"t": (e["net"].get("t") or 0) >= z, "first_half": (e["sub"]["2017_2021"].get("mean_monthly") or 0) > 0,
             "second_half": (e["sub"]["2022_2026"].get("mean_monthly") or 0) > 0,
             "costs_x2": (e["costs_x2"].get("mean_monthly") or 0) > 0}
        e.update(gates=g, verdict="VALIDATED" if all(g.values()) else "REJECTED", failed_gates=[k for k, v in g.items() if not v])
        out[hid] = e
    verdict = "PASSED" if any(v["verdict"] == "VALIDATED" for v in out.values()) else "FAILED"
    body = _write(HID, {"program": HID, "kind": "retail", "holdout_of": PID, "results": out, "verdict": verdict,
                        "t_required": round(z, 4), "classification": {h: v["verdict"] for h, v in out.items()}})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json", "artifact_sha256": body["sha256"]}))
    print("holdout verdict", verdict)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "judge": lambda: cmd_judge(now),
     "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
