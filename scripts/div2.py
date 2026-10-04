"""DIV-2 runner: DIV-1's frozen trend rules on long-history futures-style excess returns.

Runs where public market data is reachable (a GitHub Actions runner; see .github/workflows/div2-run.yml):

    python scripts/div2.py fetch     # Yahoo indices/yields, datahub commodities, H.10 FX -> data/div2/raw + manifest
    python scripts/div2.py judge     # 1990-2007 judged; 2008-2020 replicated descriptively; 2021+ sealed
    python scripts/div2.py holdout   # only if judge PASSED: opens 2021-01.. once (research/holdout-div.json)

Design: research/preregistrations/DIV-2.md. The signal and sizing are trend.py's, unchanged from DIV-1.
"""

from __future__ import annotations

import csv
import hashlib
import json
import socket
import sys
import time as _time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data import h10  # noqa: E402
from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import excess, trend  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

socket.setdefaulttimeout(30)
R = ROOT / "research"
PID, HID = "DIV-2", "DIV-2-H"
DOC = "research/preregistrations/DIV-2.md"
SPEC = R / "specs" / "DIV-2.json"
HOLDOUT_FILE = R / "holdout-div.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "div2"
RAW = DATA / "raw"
UNIVERSE = "multi-asset-long"
HOLD_UNIVERSE = "multi-asset-etf"
CODE = ("aitrader/research/discovery/trend.py", "aitrader/research/discovery/excess.py", "scripts/div2.py",
        "aitrader/data/h10.py")

EQUITY = {"SPX": "^GSPC", "NASDAQ": "^IXIC", "NIKKEI": "^N225", "FTSE": "^FTSE", "DAX": "^GDAXI", "HSI": "^HSI",
          "TSX": "^GSPTSE", "CAC": "^FCHI", "SMI": "^SSMI", "ASX": "^AXJO"}
BONDS = {"US10Y": "^TNX", "US5Y": "^FVX"}
COMMODITY_YAHOO = {"GOLD": "GC=F"}
COMMODITY_DATAHUB = {
    "WTI": "https://raw.githubusercontent.com/datasets/oil-prices/main/data/wti-daily.csv",
    "BRENT": "https://raw.githubusercontent.com/datasets/oil-prices/main/data/brent-daily.csv",
    "NATGAS": "https://raw.githubusercontent.com/datasets/natural-gas/main/data/daily.csv",
}
FX = ("AUD", "CAD", "CHF", "GBP", "JPY", "NZD", "EUR")
ASSETS = {**{k: "equity" for k in EQUITY}, **{k: "bonds" for k in BONDS},
          **{k: "commodities" for k in (*COMMODITY_YAHOO, *COMMODITY_DATAHUB)}, **{k: "currencies" for k in FX}}
DEV = (date(1990, 1, 1), date(1999, 1, 1))
VAL = (date(1999, 1, 1), date(2008, 1, 1))
JUDGE = (DEV[0], VAL[1])
SEEN = (date(2008, 1, 1), date(2021, 1, 1))
HOLD_START = date(2021, 1, 1)
T_REQUIRED = 3.0
COSTS = trend.TrendCosts(trade_bps=2.0, financing_pa=0.0, borrow_pa=0.0)
CFD_MARKUP_PA = 0.025
MAX_CARRY_DAYS = 5
HYPOTHESES = {"DIV2-H1-TSMOM12": "tsmom12", "DIV2-H2-BLEND": "blend"}
GATES = {
    "t": f"t of the mean monthly net return over 1990-2007 >= {T_REQUIRED}",
    "development": "mean net > 0 in 1990-1998", "validation": "mean net > 0 in 1999-2007",
    "costs_x2": "mean net > 0 with trading costs doubled (4 bps per unit traded)",
    "leave_one_class_out": "mean net > 0 leaving out any one asset class's contribution",
    "top_year": "no single year supplies more than 50% of the total net",
}
HOLDOUT_RULE = "2021-01 onward, opened once for the passers: mean net > 0 and mean net with costs x2 > 0"


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec(reg: Registry) -> dict:
    return {"program": PID, "versions": {"trend": trend.TREND_VERSION, "excess": excess.EXCESS_VERSION},
            "universe": UNIVERSE, "assets": ASSETS, "yahoo": {**EQUITY, **BONDS, **COMMODITY_YAHOO},
            "datahub": COMMODITY_DATAHUB, "fx": list(FX), "hypotheses": HYPOTHESES, "gates": GATES,
            "holdout_rule": HOLDOUT_RULE, "t_required": T_REQUIRED,
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "seen_replication_descriptive": [str(d) for d in SEEN], "holdout_start": str(HOLD_START)},
            "costs": COSTS.__dict__, "costs_x2": COSTS.stressed().__dict__, "cfd_markup_reported": CFD_MARKUP_PA,
            "excess_construction": {"div_yield": excess.DIV_YIELD, "duration": excess.DURATION,
                                    "funding": "USD BIS policy rate in force at the previous close",
                                    "max_carry_days": MAX_CARRY_DAYS},
            "registry_threshold_for_reference": round(reg.threshold_for_next(UNIVERSE, JUDGE[0], JUDGE[1],
                                                                             new_tests=len(HYPOTHESES)), 4)}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


# ── fetch ───────────────────────────────────────────────────────────────

UA = {"User-Agent": "Mozilla/5.0 (research; aitrader DIV-2)"}


def _get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def _yahoo(sym: str) -> list[tuple[str, float]]:
    raw = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=0&period2={int(_time.time())}&interval=1d")
    res = json.loads(raw)["chart"]["result"][0]
    return [(datetime.fromtimestamp(t, timezone.utc).date().isoformat(), float(c))
            for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c is not None and c > 0]


def _datahub(url: str) -> list[tuple[str, float]]:
    rows = list(csv.reader(_get(url).decode().splitlines()))[1:]
    return [(r[0], float(r[1])) for r in rows if len(r) >= 2 and r[1] not in ("", ".")]


def cmd_fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    man = {}
    for name, sym in {**EQUITY, **BONDS, **COMMODITY_YAHOO}.items():
        rows = _yahoo(sym)
        man[name] = _save(name, rows, f"Yahoo Finance chart API close, {sym}")
    for name, url in COMMODITY_DATAHUB.items():
        man[name] = _save(name, _datahub(url), f"EIA via datahub.io: {url}")
    fname = h10.vintage_file(h10.PRIMARY)
    raw = _get(h10.MIRROR_URL.format(commit=h10.VINTAGES[h10.PRIMARY][0]))
    want = json.loads((ROOT / "data" / "h10" / "manifest.json").read_text())["files"][fname]["sha256"]
    if hashlib.sha256(raw).hexdigest() != want:
        raise SystemExit("H.10 vintage does not match data/h10/manifest.json; refusing")
    (ROOT / "data" / "h10" / fname).write_bytes(raw)
    man["H10"] = {"file": f"data/h10/{fname}", "sha256": want, "source": "Federal Reserve H.10 via the pinned mirror"}
    (DATA / "fetch_manifest.json").write_text(_dump({"retrieved": datetime.now(timezone.utc).isoformat(), "series": man}))
    for k, v in man.items():
        print(k, v.get("first"), v.get("last"), v.get("rows"))


def _save(name, rows, source):
    body = "date,value\n" + "".join(f"{d},{v!r}\n" for d, v in rows)
    (RAW / f"{name}.csv").write_text(body)
    return {"rows": len(rows), "first": rows[0][0], "last": rows[-1][0], "source": source,
            "sha256": hashlib.sha256(body.encode()).hexdigest()}


# ── panel ───────────────────────────────────────────────────────────────

def _read(name) -> dict[date, float]:
    with open(RAW / f"{name}.csv") as f:
        return {date.fromisoformat(r["date"]): float(r["value"]) for r in csv.DictReader(f)}


class Rates:
    """BIS policy rates as published (data/div2/policy_rates.csv): the value public at time t, NaN when
    the last observation is more than 7 days old (a publisher's gap is a gap, never carried)."""

    def __init__(self, path: Path = DATA / "policy_rates.csv") -> None:
        by: dict[str, list] = {}
        with open(path) as f:
            for r in csv.DictReader(f):
                by.setdefault(r["currency"], []).append((int(r["available_at_epoch"]),
                                                         date.fromisoformat(r["effective_date"]), float(r["value_pct"])))
        self.by = {c: sorted(v) for c, v in by.items()}
        self.avail = {c: np.array([x[0] for x in v]) for c, v in self.by.items()}

    def at(self, ccy: str, d: date) -> float:
        """The rate public at the close (22:00 UTC) of day d."""
        t = int(datetime(d.year, d.month, d.day, 22, tzinfo=timezone.utc).timestamp())
        i = int(np.searchsorted(self.avail[ccy], t, "right")) - 1
        if i < 0:
            return float("nan")
        _, eff, v = self.by[ccy][i]
        return v if (d - eff).days <= 7 else float("nan")


def normalise_yield(y: np.ndarray, name: str) -> np.ndarray:
    """Yields in percent. A series quoted at 10x (the CBOE index convention: 42.5 for 4.25%) is divided
    by 10; any other scale is refused. Decided before the data was fetched (DIV-2.md)."""
    med = float(np.nanmedian(y))
    if 20.0 < med < 200.0:
        y = y / 10.0
    elif not -1.0 < med <= 20.0:
        raise SystemExit(f"{name}: median yield {med} is outside every known quoting convention; refusing")
    return y


def _aligned(series: dict[date, float], days: list[date]) -> list[float]:
    return [series.get(d, float("nan")) for d in days]


def build_indices(key=None) -> trend.Panel:
    rates = Rates()
    idx: dict[str, tuple[list[date], np.ndarray]] = {}

    def prev_rate(ccy, ds):
        return [float("nan")] + [rates.at(ccy, ds[i - 1]) for i in range(1, len(ds))]

    for name in EQUITY:
        s = _read(name)
        ds = sorted(s)
        idx[name] = (ds, excess.equity_index(ds, _aligned(s, ds), prev_rate("USD", ds)))
    for name in BONDS:
        s = _read(name)
        ds = sorted(s)
        y = np.array(_aligned(s, ds), float)
        y = normalise_yield(y, name)
        idx[name] = (ds, excess.bond_index(ds, list(y), prev_rate("USD", ds), excess.DURATION[name]))
    for name in (*COMMODITY_YAHOO, *COMMODITY_DATAHUB):
        s = _read(name)
        ds = sorted(s)
        idx[name] = (ds, excess.spot_index(ds, _aligned(s, ds)))
    hx = h10.official_series((ROOT / "data" / "h10" / h10.vintage_file(h10.PRIMARY)).read_bytes())
    for ccy in FX:
        se = hx[ccy]
        ds = list(se.dates)
        inverted = h10.SERIES[ccy][3].startswith("USD")  # USDJPY, USDCHF, USDCAD: units per USD
        usd_per = [1.0 / v if inverted else v for v in se.value]
        idx[ccy] = (ds, excess.fx_index(ds, usd_per, prev_rate(ccy, ds), prev_rate("USD", ds)))
    start = date(1988, 1, 1)
    days = sorted({d for ds, _ in idx.values() for d in ds if d >= start})
    if key is None:
        days = [d for d in days if d < HOLD_START]
    closes = {}
    for name, (ds, v) in idx.items():
        m = dict(zip(ds, v))
        c = np.array([m.get(d, np.nan) for d in days], float)
        last, last_d = np.nan, None
        for i, d in enumerate(days):  # carry only across short calendar gaps (holidays), never across exclusions
            if np.isfinite(c[i]):
                last, last_d = c[i], d
            elif np.isfinite(last) and last_d is not None and (d - last_d).days <= MAX_CARRY_DAYS and d not in m:
                c[i] = last
        closes[name] = c
    return trend.Panel(days, closes)


# ── judgement ───────────────────────────────────────────────────────────

def _by_year(rows):
    out: dict = {}
    for r in rows:
        out.setdefault(r["date"].year, []).append(r["net"])
    return {y: round(float(np.sum(v)), 5) for y, v in sorted(out.items())}


def _cfd(rows):
    return trend.stats([{"net": r["net"] - CFD_MARKUP_PA / 12 * r["gross_exposure"]} for r in rows])


def judge_one(panel, rule: str) -> dict:
    rows = trend.backtest(panel, rule, COSTS, *JUDGE)
    x2 = trend.backtest(panel, rule, COSTS.stressed(), *JUDGE)
    seen = trend.backtest(panel, rule, COSTS, *SEEN)
    s = trend.stats(rows)
    years = _by_year(rows)
    pos = sum(v for v in years.values() if v > 0)
    classes = sorted(set(ASSETS.values()))
    loco = {c: round(float(np.mean([r["net"] - sum(v for k, v in r["contrib"].items() if ASSETS[k] == c)
                                    for r in rows])), 6) for c in classes} if rows else {}
    res = {"net": s, "gross": trend.stats(rows, "gross"), "cost": trend.stats(rows, "cost"),
           "development": trend.stats([r for r in rows if r["date"] < DEV[1]]),
           "validation": trend.stats([r for r in rows if r["date"] >= VAL[0]]),
           "costs_x2": trend.stats(x2), "retail_cfd_reported": _cfd(rows), "by_year": years,
           "leave_one_class_out": loco,
           "by_class_contribution": {c: round(float(np.mean([sum(v for k, v in r["contrib"].items() if ASSETS[k] == c)
                                                              for r in rows])), 6) for c in classes},
           "avg_gross_exposure": round(float(np.mean([r["gross_exposure"] for r in rows])), 3) if rows else None,
           "avg_assets": round(float(np.mean([r["assets"] for r in rows])), 2) if rows else None,
           "seen_period_2008_2020_descriptive": {"net": trend.stats(seen), "gross": trend.stats(seen, "gross"),
                                                 "retail_cfd": _cfd(seen)}}
    gates = {"t": (s.get("t") or 0) >= T_REQUIRED,
             "development": (res["development"].get("mean_monthly") or 0) > 0,
             "validation": (res["validation"].get("mean_monthly") or 0) > 0,
             "costs_x2": (res["costs_x2"].get("mean_monthly") or 0) > 0,
             "leave_one_class_out": bool(loco) and all(v > 0 for v in loco.values()),
             "top_year": pos > 0 and max(years.values(), default=0) <= 0.5 * pos}
    res.update(gates=gates, passed=all(gates.values()), failed_gates=[k for k, v in gates.items() if not v])
    return res


def _write(name, body):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def _registry():
    return Registry.load(R / "registry.jsonl", Holdout.load(HOLDOUT_FILE))


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
    print(spec_sha(s))


def cmd_preregister(now):
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="DIV-2: DIV-1's trend rules on long-history excess returns",
                       hypothesis="Does diversified time-series momentum earn a positive net return on futures-style "
                                  "excess returns over 1990-2007?",
                       uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"), Use(UNIVERSE, SEEN[0], SEEN[1], "judge")),
                       tests=len(HYPOTHESES), configurations=len(HYPOTHESES), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_judge(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    if reg.verdict_of(PID) is not None:
        raise SystemExit("DIV-2 already has a verdict")
    panel = build_indices()
    results = {h: judge_one(panel, rule) for h, rule in HYPOTHESES.items()}
    passers = [h for h, r in results.items() if r["passed"]]
    body = _write(PID, {"program": PID, "kind": "trend", "results": results, "passers": passers,
                        "verdict": "PASSED" if passers else "FAILED",
                        "data_manifest": {"assets": ASSETS,
                                          "fetch": json.loads((DATA / "fetch_manifest.json").read_text())},
                        "classification": {h: ("HOLDOUT_ELIGIBLE" if r["passed"] else "REJECTED") for h, r in results.items()},
                        "spec_sha256": frozen["sha256"]})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    for h, r in results.items():
        print(h, json.dumps(r["net"]), "gross", r["gross"].get("annual_return"), "failed:", r["failed_gates"])


def cmd_holdout(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if not judged["passers"]:
        raise SystemExit("nothing passed: the holdout stays sealed")
    reg.register(Trial(id=HID, registered=now, title="DIV-2 sealed holdout (2021+)", hypothesis=", ".join(judged["passers"]),
                       uses=(Use(HOLD_UNIVERSE, HOLD_START, date(2100, 1, 1), "judge"),), tests=len(judged["passers"]),
                       configurations=len(judged["passers"]), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": judged["passers"]}))
    key = open_final_test(reg, HID)
    panel = build_indices(key)
    out = {}
    for h in judged["passers"]:
        rows = trend.backtest(panel, HYPOTHESES[h], COSTS, HOLD_START)
        x2 = trend.backtest(panel, HYPOTHESES[h], COSTS.stressed(), HOLD_START)
        s, s2 = trend.stats(rows), trend.stats(x2)
        ok = (s.get("mean_monthly") or 0) > 0 and (s2.get("mean_monthly") or 0) > 0
        out[h] = {"net": s, "costs_x2": s2, "retail_cfd": _cfd(rows), "verdict": "VALIDATED" if ok else "REJECTED"}
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
