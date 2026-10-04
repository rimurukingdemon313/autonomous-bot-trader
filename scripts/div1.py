"""DIV-1 runner: diversified time-series momentum on a multi-asset ETF universe.

Runs where public market data is reachable (this repository's research container blocks it):

    python scripts/div1.py fetch     # daily adjusted closes -> data/div/*.csv + sha256 manifest
    python scripts/div1.py judge     # 2008-01..2020-12: development + validation, gates (holdout sealed)
    python scripts/div1.py holdout   # only if judge PASSED: opens 2021-01.. once

`spec` and `preregister` were run when the design was frozen, before any data was fetched
(research/preregistrations/DIV-1.md). `judge` refuses to run if this file, the study module or
the spec changed since then. Fetched data is never committed (licence); its hashes are recorded.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import time as _time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import trend  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID, HID = "DIV-1", "DIV-1-H"
DOC = "research/preregistrations/DIV-1.md"
SPEC = R / "specs" / "DIV-1.json"
HOLDOUT_FILE = R / "holdout-div.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "div"
UNIVERSE = "multi-asset-etf"
CODE = ("aitrader/research/discovery/trend.py", "scripts/div1.py")

ASSETS = {  # ETF -> asset class (each existed by the end of 2007)
    "SPY": "equity", "QQQ": "equity", "IWM": "equity", "EFA": "equity", "EEM": "equity", "EWJ": "equity",
    "TLT": "bonds", "IEF": "bonds", "LQD": "bonds", "TIP": "bonds",
    "GLD": "commodities", "SLV": "commodities", "USO": "commodities", "DBC": "commodities", "DBA": "commodities",
    "UUP": "currencies", "FXE": "currencies", "FXY": "currencies",
    "VNQ": "real_estate",
}
DEV = (date(2008, 1, 1), date(2015, 1, 1))
VAL = (date(2015, 1, 1), date(2021, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD_START = date(2021, 1, 1)
T_REQUIRED = 3.0
HYPOTHESES = {
    "DIV1-H1-TSMOM12": "tsmom12",
    "DIV1-H2-BLEND": "blend",
}
GATES = {
    "t": f"t of the mean monthly net return over 2008-2020 >= {T_REQUIRED} (fixed; stricter than the "
         "registry's ~2.24 for 2 tests on a fresh universe, for the project's earlier search)",
    "development": "mean net > 0 in 2008-2014", "validation": "mean net > 0 in 2015-2020",
    "costs_x2": "mean net > 0 with trading, financing and borrow costs doubled",
    "leave_one_class_out": "mean net > 0 leaving out any one asset class's contribution",
    "top_year": "no single year supplies more than 50% of the total net",
}
HOLDOUT_RULE = ("2021-01 onward, opened once for the passers: mean net > 0 and mean net with costs x2 > 0. "
                "About 68 months: a sign check, not a significance test (stated in advance)")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": trend.TREND_VERSION, "universe": UNIVERSE, "assets": ASSETS,
            "hypotheses": HYPOTHESES, "gates": GATES, "holdout_rule": HOLDOUT_RULE, "t_required": T_REQUIRED,
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout_start": str(HOLD_START)},
            "rules": {"vol_target": trend.VOL_TARGET, "com_days": trend.COM_DAYS, "lookbacks": list(trend.LOOKBACKS)},
            "costs": trend.TrendCosts().__dict__, "costs_x2": trend.TrendCosts().stressed().__dict__,
            "registry_threshold_for_reference": round(reg.threshold_for_next(UNIVERSE, JUDGE[0], JUDGE[1],
                                                                             new_tests=len(HYPOTHESES)), 4)}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def holdout() -> Holdout:
    return Holdout.load(HOLDOUT_FILE)


# ── data ────────────────────────────────────────────────────────────────

def fetch_one(sym: str) -> list[tuple[str, float]]:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1104537600"
           f"&period2={int(_time.time())}&interval=1d&events=div%2Csplits")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research; aitrader DIV-1)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read())["chart"]["result"][0]
    ts, adj = res["timestamp"], res["indicators"]["adjclose"][0]["adjclose"]
    return [(datetime.fromtimestamp(t, timezone.utc).date().isoformat(), float(a)) for t, a in zip(ts, adj)
            if a is not None and a > 0]


def cmd_fetch():
    DATA.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for sym in ASSETS:
        rows = fetch_one(sym)
        body = "date,adj_close\n" + "".join(f"{d},{c!r}\n" for d, c in rows)
        (DATA / f"{sym}.csv").write_text(body)
        manifest[sym] = {"rows": len(rows), "first": rows[0][0], "last": rows[-1][0],
                         "sha256": hashlib.sha256(body.encode()).hexdigest(),
                         "source": "Yahoo Finance chart API, adjusted close (dividends and splits)"}
        print(sym, manifest[sym]["first"], manifest[sym]["last"], manifest[sym]["rows"])
    (DATA / "manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "assets": manifest}))


def load_panel(key=None) -> trend.Panel:
    """Union calendar of all assets; truncated at the holdout start unless given the key."""
    series: dict[str, dict[date, float]] = {}
    for sym in ASSETS:
        with open(DATA / f"{sym}.csv") as f:
            series[sym] = {date.fromisoformat(r["date"]): float(r["adj_close"]) for r in csv.DictReader(f)}
    days = sorted(set().union(*[set(v) for v in series.values()]))
    if key is None:
        days = [d for d in days if d < HOLD_START]
    closes = {s: np.array([v.get(d, np.nan) for d in days], float) for s, v in series.items()}
    for s, c in closes.items():  # a missing day inside an asset's history is carried, never invented ahead
        last = np.nan
        for i in range(len(c)):
            if np.isfinite(c[i]):
                last = c[i]
            elif np.isfinite(last):
                c[i] = last
    return trend.Panel(days, closes)


# ── judgement ───────────────────────────────────────────────────────────

def _by_year(rows):
    out: dict = {}
    for r in rows:
        out.setdefault(r["date"].year, []).append(r["net"])
    return {y: round(float(np.sum(v)), 5) for y, v in sorted(out.items())}


def judge_one(panel, rule: str) -> dict:
    rows = trend.backtest(panel, rule, trend.TrendCosts(), *JUDGE)
    x2 = trend.backtest(panel, rule, trend.TrendCosts().stressed(), *JUDGE)
    s = trend.stats(rows)
    years = _by_year(rows)
    pos = sum(v for v in years.values() if v > 0)
    loco = {}
    for cls in sorted(set(ASSETS.values())):
        loco[cls] = round(float(np.mean([r["net"] - sum(v for k, v in r["contrib"].items() if ASSETS[k] == cls)
                                         for r in rows])), 6) if rows else None
    res = {"net": s, "gross": trend.stats(rows, "gross"), "cost": trend.stats(rows, "cost"),
           "development": trend.stats([r for r in rows if r["date"] < DEV[1]]),
           "validation": trend.stats([r for r in rows if r["date"] >= VAL[0]]),
           "costs_x2": trend.stats(x2), "by_year": years, "leave_one_class_out": loco,
           "by_class_contribution": {c: round(float(np.mean([sum(v for k, v in r["contrib"].items() if ASSETS[k] == c)
                                                              for r in rows])), 6) for c in sorted(set(ASSETS.values()))}}
    gates = {"t": (s.get("t") or 0) >= T_REQUIRED,
             "development": (res["development"].get("mean_monthly") or 0) > 0,
             "validation": (res["validation"].get("mean_monthly") or 0) > 0,
             "costs_x2": (res["costs_x2"].get("mean_monthly") or 0) > 0,
             "leave_one_class_out": bool(loco) and all(v is not None and v > 0 for v in loco.values()),
             "top_year": pos > 0 and max(years.values(), default=0) <= 0.5 * pos}
    res.update(gates=gates, passed=all(gates.values()), failed_gates=[k for k, v in gates.items() if not v])
    return res


def _write(name, body):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def _check_frozen(reg, trial_id):
    trial = reg.get(trial_id)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec():
    reg = Registry.load(R / "registry.jsonl", holdout())
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s))


def cmd_preregister(now):
    reg = Registry.load(R / "registry.jsonl", holdout())
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    if spec_sha(s) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="DIV-1: diversified time-series momentum (multi-asset ETFs)",
                       hypothesis="Do trailing 12-month (and 1/3/12 blended) returns predict next-month returns across asset classes, after costs?",
                       uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),), tests=len(HYPOTHESES),
                       configurations=len(HYPOTHESES), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now):
    reg = Registry.load(R / "registry.jsonl", holdout())
    frozen = _check_frozen(reg, PID)
    panel = load_panel()
    results = {h: judge_one(panel, rule) for h, rule in HYPOTHESES.items()}
    passers = [h for h, r in results.items() if r["passed"]]
    manifest = json.loads((DATA / "manifest.json").read_text())
    body = _write(PID, {"program": PID, "kind": "trend", "results": results, "passers": passers,
                        "verdict": "PASSED" if passers else "FAILED", "data_manifest": manifest,
                        "classification": {h: ("HOLDOUT_ELIGIBLE" if r["passed"] else "REJECTED") for h, r in results.items()},
                        "spec_sha256": frozen["sha256"]})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    for h, r in results.items():
        print(h, json.dumps(r["net"]), "failed:", r["failed_gates"])


def cmd_holdout(now):
    reg = Registry.load(R / "registry.jsonl", holdout())
    frozen = _check_frozen(reg, PID)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if not judged["passers"]:
        raise SystemExit("nothing passed: the DIV-1 holdout stays sealed")
    reg.register(Trial(id=HID, registered=now, title="DIV-1 sealed holdout", hypothesis=", ".join(judged["passers"]),
                       uses=(Use(UNIVERSE, HOLD_START, date(2100, 1, 1), "judge"),), tests=len(judged["passers"]),
                       configurations=len(judged["passers"]), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": judged["passers"]}))
    key = open_final_test(reg, HID)
    panel = load_panel(key)
    out = {}
    for h in judged["passers"]:
        rows = trend.backtest(panel, HYPOTHESES[h], trend.TrendCosts(), HOLD_START)
        x2 = trend.backtest(panel, HYPOTHESES[h], trend.TrendCosts().stressed(), HOLD_START)
        s, s2 = trend.stats(rows), trend.stats(x2)
        ok = (s.get("mean_monthly") or 0) > 0 and (s2.get("mean_monthly") or 0) > 0
        out[h] = {"net": s, "costs_x2": s2, "verdict": "VALIDATED" if ok else "REJECTED"}
    verdict = "PASSED" if any(v["verdict"] == "VALIDATED" for v in out.values()) else "FAILED"
    body = _write(HID, {"program": HID, "kind": "trend", "holdout_of": PID, "results": out, "verdict": verdict,
                        "classification": {h: v["verdict"] for h, v in out.items()}})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(json.dumps(out, indent=1, default=str))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"fetch": cmd_fetch, "spec": cmd_spec, "preregister": lambda: cmd_preregister(now),
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
