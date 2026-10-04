"""RC-EQ: retail-CFD equity-index candidates (research/preregistrations/RC-EQ.md).

Runs where Yahoo is reachable (a GitHub Actions runner; .github/workflows/rc-eq-run.yml):

    python scripts/rc_eq.py fetch      # universe A closes -> data/rc/raw (never universe B)
    python scripts/rc_eq.py spec       # write research/specs/RC-EQ.json (before registration)
    python scripts/rc_eq.py preregister
    python scripts/rc_eq.py judge      # universe A, 1990-01 -> 2020-12; nothing from 2021 is ever loaded for A
    python scripts/rc_eq.py holdout    # only for passers: fetches universe B (never loaded before) once

Costs, financing and dividends: aitrader/research/discovery/retail.py. Rules: rc.py.
"""

from __future__ import annotations

import hashlib
import json
import socket
import sys
import time as _time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import rc, retail  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

socket.setdefaulttimeout(30)
R = ROOT / "research"
PID, HID = "RC-EQ", "RC-EQ-H"
DOC = "research/preregistrations/RC-EQ.md"
SPEC = R / "specs" / "RC-EQ.json"
HOLDOUT_FILE = R / "holdout-rc-eq.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "rc"
RAW = DATA / "raw"
CODE = ("aitrader/research/discovery/retail.py", "aitrader/research/discovery/rc.py", "scripts/rc_eq.py")

#: name -> (Yahoo ticker, financing key (BIS area; "DE|XM" = national rate before 1999), spread bps, total return)
UNIVERSE_A = {
    "US500": ("^SP500TR", "US", 2.0, True), "NAS100": ("^NDX", "US", 2.0, False),
    "JPN225": ("^N225", "JP", 2.0, False), "UK100": ("^FTSE", "GB", 2.0, False),
    "GER40": ("^GDAXI", "DE|XM", 2.0, True), "FRA40": ("^FCHI", "FR|XM", 2.0, False),
    "AUS200": ("^AXJO", "AU", 2.0, False), "HK50": ("^HSI", "HK", 5.0, False),
    "CAN60": ("^GSPTSE", "CA", 5.0, False), "SWI20": ("^SSMI", "CH", 5.0, False),
}
#: never loaded by this project before; fixed by the availability rule in RC-EQ.md (rc-probe.json)
UNIVERSE_B = {
    "US2000": ("^RUT", "US", 5.0, False), "ESP35": ("^IBEX", "ES|XM", 5.0, False),
    "NETH25": ("^AEX", "NL|XM", 5.0, False), "EU50": ("^STOXX50E", "XM", 2.0, False),
    "SWE30": ("^OMX", "SE", 5.0, False), "ITA40": ("FTSEMIB.MI", "IT|XM", 5.0, False),
    "BEL20": ("^BFX", "BE|XM", 10.0, False), "AUT20": ("^ATX", "AT|XM", 10.0, False),
    "IND50": ("^NSEI", "IN", 10.0, False), "KOR200": ("^KS11", "KR", 10.0, False),
    "NZL50": ("^NZ50", "NZ", 10.0, False), "MEX35": ("^MXX", "MX", 10.0, False),
    "BRA60": ("^BVSP", "BR", 10.0, False), "ISR125": ("^TA125.TA", "IL", 10.0, False),
    "MYS30": ("^KLSE", "MY", 10.0, False), "IDN": ("^JKSE", "ID", 10.0, False),
}
LOAD_FROM = date(1985, 1, 1)
JUDGE = (date(1990, 1, 1), date(2021, 1, 1))
DEV = (date(1990, 1, 1), date(2006, 1, 1))
VAL = (date(2006, 1, 1), date(2021, 1, 1))
MODERN = (date(2009, 1, 1), date(2021, 1, 1))
B_PERIOD = (date(1990, 1, 1), date(2026, 10, 1))
B_SPLIT = date(2021, 1, 1)
COSTS = retail.Costs()
T_FLOOR = 3.0
MAX_DD = 0.30
TOP_YEAR = 0.30
#: id -> (rule, primary parameters, neighbourhood grid)
HYPOTHESES = {
    "RCEQ-E1-TOM": ("tom", {"k_pre": 1, "k_post": 3}, {"k_pre": [1, 2, 3], "k_post": [2, 3, 4]}),
    "RCEQ-E2-DIP": ("dip", {"lookback": 5, "threshold": -1.0}, {"lookback": [3, 5, 10], "threshold": [-0.75, -1.0, -1.5]}),
    "RCEQ-E3-XSMOM": ("xsmom", {"lookback": 12, "k": 3}, {"lookback": [6, 9, 12], "k": [2, 3, 4]}),
    "RCEQ-E4-REGIME": ("regime", {"months": 10}, {"months": [6, 8, 10, 12, 14]}),
    "RCEQ-E5-VOLMAN": ("volman", {"target": 0.15, "window": 21}, {"target": [0.10, 0.15, 0.20], "window": [21, 63]}),
    "RCEQ-E6-BREAKOUT": ("breakout", {"entry": 100, "exit_ratio": 0.5}, {"entry": [50, 100, 150], "exit_ratio": [0.25, 0.5]}),
    "RCEQ-E7-ENSEMBLE": ("ensemble", {}, {}),
}
GATES = {
    "t": "t of the mean monthly net return, 1990-2020, >= max(3.0, the registry's Bonferroni value)",
    "development": "mean net > 0 in 1990-2005", "validation": "mean net > 0 in 2006-2020",
    "modern": "mean net > 0 in 2009-2020",
    "costs_x2": "mean net > 0 with every cost assumption doubled (spread, slippage, commission, both markups)",
    "delay": "mean net > 0 with every fill one close later",
    "leave_one_out": "mean net > 0 leaving out any one instrument",
    "top_year": f"no year supplies more than {TOP_YEAR:.0%} of the sum of positive years",
    "region": "at least 75% of the neighbourhood grid has mean net > 0 and its median t >= 2.0 (no magic number)",
    "drawdown": f"maximum drawdown (sum of monthly net, 1x) <= {MAX_DD:.0%}",
}
PROMISING_RULE = "not passed, but t >= 2.0, development > 0, validation > 0 and costs_x2 > 0: reported, never holdout-eligible"
HOLDOUT_RULE = ("universe B (never loaded), 1990-01 -> 2026-09, once, passers only: t >= the one-sided Bonferroni "
                "value z(1 - 0.05/k) for k passers; mean net > 0 before 2021 and from 2021; costs_x2 > 0; delay > 0")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(HOLDOUT_FILE))


def threshold(reg: Registry) -> float:
    t1 = reg.threshold_for_next("multi-asset-long", *JUDGE, new_tests=len(HYPOTHESES))
    t2 = reg.threshold_for_next("multi-asset-etf", JUDGE[0], JUDGE[1], new_tests=len(HYPOTHESES))
    return round(max(T_FLOOR, t1, t2), 4)


def spec(reg: Registry) -> dict:
    return {"program": PID, "versions": {"retail": retail.RETAIL_VERSION, "rc": rc.RC_VERSION},
            "universe_a": UNIVERSE_A, "universe_b": UNIVERSE_B, "load_from": str(LOAD_FROM),
            "periods": {"judge": [str(d) for d in JUDGE], "development": [str(d) for d in DEV],
                        "validation": [str(d) for d in VAL], "modern": [str(d) for d in MODERN],
                        "holdout_b": [str(d) for d in B_PERIOD], "holdout_split": str(B_SPLIT)},
            "costs": COSTS.__dict__, "costs_x2": COSTS.stressed().__dict__,
            "hypotheses": HYPOTHESES, "gates": GATES, "promising": PROMISING_RULE, "holdout_rule": HOLDOUT_RULE,
            "t_required": threshold(reg), "max_rate_pct": rc.MAX_RATE_PCT,
            "data_rules": {"clean": "rc.clean: one-day 20% spikes and 5+ identical closes removed, never replaced",
                           "dates": "exchange-local trading dates", "rates": "BIS policy rate public at 22:00 UTC; stale > 7 days or > 25% = not held"}}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


# ── data ────────────────────────────────────────────────────────────────

UA = {"User-Agent": "Mozilla/5.0 (research; aitrader RC-EQ)"}


def _yahoo(sym: str) -> list[tuple[str, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=0&period2={int(_time.time())}&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    tz = ZoneInfo(res["meta"]["exchangeTimezoneName"])
    rows = {}
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None and c > 0:
            rows[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).date().isoformat()] = float(c)
    return sorted(rows.items())


def _fetch(universe: dict, tag: str) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    man = {}
    for name, (sym, *_rest) in universe.items():
        rows = _yahoo(sym)
        body = "date,close\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
        (RAW / f"{name}.csv").write_text(body)
        man[name] = {"ticker": sym, "rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                     "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (DATA / f"fetch_manifest_{tag}.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))
    return man


def cmd_fetch():
    for k, v in _fetch(UNIVERSE_A, "A").items():
        print(k, v["first"], v["last"], v["rows"])


def _read(name: str):
    ds, vs = [], []
    with open(RAW / f"{name}.csv") as f:
        next(f)
        for line in f:
            d, v = line.strip().split(",")
            ds.append(date.fromisoformat(d))
            vs.append(float(v))
    return ds, vs


def load(universe: dict, end: date):
    """Cleaned closes from LOAD_FROM to `end` (exclusive) and the cleaning counts."""
    series, report = {}, {}
    for name in universe:
        ds, vs = _read(name)
        keep = [(d, v) for d, v in zip(ds, vs) if LOAD_FROM <= d < end]
        d2, v2, rep = rc.clean([d for d, _ in keep], [v for _, v in keep])
        series[name] = (d2, v2)
        report[name] = {**rep, "closes": len(d2), "first": str(d2[0]) if d2 else None}
    days, closes = rc.panel(series, LOAD_FROM, end)
    return days, closes, report


def instruments(universe: dict) -> dict:
    return {n: retail.Instrument(n, "index", key, spread_bps=sp, total_return=tr)
            for n, (_, key, sp, tr) in universe.items()}


# ── rules ───────────────────────────────────────────────────────────────

def targets(rule: str, params: dict, days, closes, universe: dict, rates: rc.Rates) -> dict:
    n = len(universe)
    if rule == "tom":
        return rc.tom(days, closes, n, **params)
    if rule == "dip":
        return rc.dip(days, closes, n, **params)
    if rule == "regime":
        return rc.regime(days, closes, n, **params)
    if rule == "volman":
        return rc.volman(days, closes, n, **params)
    if rule == "breakout":
        return rc.breakout(days, closes, n, **params)
    if rule == "xsmom":
        ok = lambda name, d: np.isfinite(rates.at(universe[name][1], d))  # noqa: E731
        return rc.xsmom(days, closes, ok, **params)
    if rule == "ensemble":
        parts = [targets(r, p, days, closes, universe, rates) for h, (r, p, _) in HYPOTHESES.items() if r != "ensemble"]
        return rc.average(*parts)
    raise ValueError(rule)


def _grid(g: dict) -> list[dict]:
    cells = [{}]
    for k, vals in g.items():
        cells = [{**c, k: v} for c in cells for v in vals]
    return cells


def _mean(res, period, names=None):
    m = [v for _, v in retail.monthly(res.dates, res.net(names), *period)]
    return float(np.mean(m)) if m else float("nan")


def evaluate(hid: str, days, closes, universe: dict, rates: rc.Rates, period, sub: dict, grid: bool = True) -> dict:
    rule, params, g = HYPOTHESES[hid]
    inst = instruments(universe)
    rate = lambda key, d: rates.at(key, d)  # noqa: E731
    tg = targets(rule, params, days, closes, universe, rates)
    res = retail.simulate(days, closes, tg, inst, rate, COSTS)
    x2 = retail.simulate(days, closes, tg, inst, rate, COSTS.stressed())
    dl = retail.simulate(days, closes, retail.delay(tg, closes, 1), inst, rate, COSTS)
    fr = retail.simulate(days, closes, tg, inst, rate, COSTS.frictionless())
    out = {"net": retail.summarize(res, *period), "costs_x2": retail.summarize(x2, *period),
           "delay": retail.summarize(dl, *period), "before_broker": retail.summarize(fr, *period),
           "by_year": retail.by_year(res, *period), "leverage": retail.leverage_table(res, *period),
           "sub": {k: retail.summarize(res, *p) for k, p in sub.items()},
           "per_instrument": {n: retail.summarize(res, *period, names=[n]) for n in universe},
           "leave_one_out": {n: round(_mean(res, period, [m for m in universe if m != n]), 6) for n in universe}}
    if grid and g:
        cells = []
        for cell in _grid(g):
            r = retail.simulate(days, closes, targets(rule, cell, days, closes, universe, rates), inst, rate, COSTS)
            s = retail.summarize(r, *period)
            cells.append({"params": cell, "mean_monthly": s.get("mean_monthly"), "t": s.get("t"),
                          "annual_return": s.get("annual_return")})
        out["grid"] = cells
    out["_res"] = res
    return out


def gates(e: dict, t_req: float) -> dict:
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
        ms = [c["mean_monthly"] or 0 for c in e["grid"]]
        ts = [c["t"] or 0 for c in e["grid"]]
        g["region"] = np.mean([m > 0 for m in ms]) >= 0.75 and float(np.median(ts)) >= 2.0
    return g


def _regimes(res, days, closes) -> dict:
    """Descriptive: annualised mean daily net in US500 bull/bear (above/below its 200-close mean at the
    previous close) and in terciles of its trailing 63-close volatility (judge-period cutoffs)."""
    c = closes["US500"]
    idx = [j for j in range(len(c)) if np.isfinite(c[j])]
    lab_bull, vol = {}, {}
    lc = np.log(np.array([c[j] for j in idx]))
    for k in range(200, len(idx)):
        lab_bull[idx[k]] = "bull" if c[idx[k - 1]] > np.mean([c[i] for i in idx[k - 200:k]]) else "bear"
        vol[idx[k]] = float(np.std(np.diff(lc[k - 63:k]), ddof=1))
    net = res.net()
    sel = [j for j in range(len(days)) if JUDGE[0] <= days[j] < JUDGE[1]]
    last, cur = {}, -1  # the latest US500 close at or before each date
    valid = set(idx)
    for j in range(len(days)):
        if j in valid:
            cur = j
        last[j] = cur
    out = {}
    for lab in ("bull", "bear"):
        xs = [net[j] for j in sel if lab_bull.get(last[j]) == lab]
        out[lab] = {"days": len(xs), "annualised_mean": round(float(np.mean(xs)) * 252, 4) if xs else None}
    vs = [vol[last[j]] for j in sel if last[j] in vol]
    if vs:
        lo, hi = np.quantile(vs, [1 / 3, 2 / 3])
        for lab, f in (("low_vol", lambda v: v <= lo), ("mid_vol", lambda v: lo < v <= hi), ("high_vol", lambda v: v > hi)):
            xs = [net[j] for j in sel if last[j] in vol and f(vol[last[j]])]
            out[lab] = {"days": len(xs), "annualised_mean": round(float(np.mean(xs)) * 252, 4) if xs else None}
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
    reg.register(Trial(id=PID, registered=now, title="RC-EQ: retail-CFD equity-index candidates (calendar, reversal, "
                       "relative strength, regime, volatility management, ensemble)",
                       hypothesis="Does any low-turnover equity-index rule earn a significant net return after retail "
                                  "CFD spreads, slippage, financing and dividends over 1990-2020?",
                       uses=(Use("multi-asset-long", JUDGE[0], JUDGE[1], "judge"),
                             Use("multi-asset-etf", date(2008, 1, 1), JUDGE[1], "judge")),
                       tests=len(HYPOTHESES), configurations=sum(max(1, len(_grid(g))) for _, _, g in HYPOTHESES.values()),
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required"]
    rates = rc.Rates(DATA / "policy_rates.csv")
    days, closes, report = load(UNIVERSE_A, JUDGE[1])
    sub = {"development": DEV, "validation": VAL, "modern": MODERN}
    results, monthly_net = {}, {}
    for hid in HYPOTHESES:
        e = evaluate(hid, days, closes, UNIVERSE_A, rates, JUDGE, sub)
        res = e.pop("_res")
        e["regimes"] = _regimes(res, days, closes)
        e["gates"] = gates(e, t_req)
        e["passed"] = all(e["gates"].values())
        e["failed_gates"] = [k for k, v in e["gates"].items() if not v]
        s = e["net"]
        e["classification"] = ("HOLDOUT_ELIGIBLE" if e["passed"] else
                               "PROMISING" if ((s.get("t") or 0) >= 2.0 and e["gates"]["development"]
                                               and e["gates"]["validation"] and e["gates"]["costs_x2"]) else "REJECTED")
        results[hid] = e
        monthly_net[hid] = dict(retail.monthly(res.dates, res.net(), *JUDGE))
        print(hid, json.dumps({k: s.get(k) for k in ("n", "annual_return", "t", "sharpe", "max_drawdown", "trades",
                                                     "profit_factor", "turnover_annual", "financing_annual")}),
              "failed:", e["failed_gates"], flush=True)
    keys = sorted(set().union(*[set(m) for m in monthly_net.values()]))
    mat = np.array([[monthly_net[h].get(k, 0.0) for k in keys] for h in HYPOTHESES])
    corr = np.corrcoef(mat)
    missing = {n: round(float(np.mean([not np.isfinite(rates.at(UNIVERSE_A[n][1], d)) for d in days
                                       if JUDGE[0] <= d < JUDGE[1]])), 4) for n in UNIVERSE_A}
    passers = [h for h, r in results.items() if r["passed"]]
    body = _write(PID, {"program": PID, "kind": "retail", "results": results, "passers": passers,
                        "verdict": "PASSED" if passers else "FAILED",
                        "classification": {h: r["classification"] for h, r in results.items()},
                        "correlation_monthly_net": {h: {k: round(float(corr[i, j]), 3) for j, k in enumerate(HYPOTHESES)}
                                                    for i, h in enumerate(HYPOTHESES)},
                        "data": {"cleaning": report, "share_of_days_without_financing_rate": missing,
                                 "fetch": json.loads((DATA / "fetch_manifest_A.json").read_text())},
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
        raise SystemExit("nothing passed: universe B stays sealed")
    reg.register(Trial(id=HID, registered=now, title="RC-EQ holdout: universe B (never loaded)", hypothesis=", ".join(passers),
                       uses=(Use("equity-index-b", date(1900, 1, 1), date(2100, 1, 1), "judge"),), tests=len(passers),
                       configurations=len(passers), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": passers}))
    open_final_test(reg, HID)
    _fetch(UNIVERSE_B, "B")
    rates = rc.Rates(DATA / "policy_rates.csv")
    days, closes, report = load(UNIVERSE_B, B_PERIOD[1])
    z = NormalDist().inv_cdf(1 - 0.05 / len(passers))
    out = {}
    for hid in passers:
        e = evaluate(hid, days, closes, UNIVERSE_B, rates, B_PERIOD,
                     {"before_2021": (B_PERIOD[0], B_SPLIT), "from_2021": (B_SPLIT, B_PERIOD[1])}, grid=False)
        e.pop("_res")
        g = {"t": (e["net"].get("t") or 0) >= z,
             "before_2021": (e["sub"]["before_2021"].get("mean_monthly") or 0) > 0,
             "from_2021": (e["sub"]["from_2021"].get("mean_monthly") or 0) > 0,
             "costs_x2": (e["costs_x2"].get("mean_monthly") or 0) > 0,
             "delay": (e["delay"].get("mean_monthly") or 0) > 0}
        e.update(gates=g, verdict="VALIDATED" if all(g.values()) else "REJECTED",
                 failed_gates=[k for k, v in g.items() if not v])
        out[hid] = e
        print(hid, e["verdict"], json.dumps({k: e["net"].get(k) for k in ("n", "annual_return", "t", "sharpe")}), flush=True)
    verdict = "PASSED" if any(v["verdict"] == "VALIDATED" for v in out.values()) else "FAILED"
    body = _write(HID, {"program": HID, "kind": "retail", "holdout_of": PID, "results": out, "verdict": verdict,
                        "t_required": round(z, 4), "classification": {h: v["verdict"] for h, v in out.items()},
                        "data": {"cleaning": report, "fetch": json.loads((DATA / "fetch_manifest_B.json").read_text())}})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print("holdout verdict", verdict)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"fetch": cmd_fetch, "spec": cmd_spec, "preregister": lambda: cmd_preregister(now),
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
