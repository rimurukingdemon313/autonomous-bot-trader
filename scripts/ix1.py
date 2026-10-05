"""IX-1: intraday momentum into the COMEX settlement for gold and silver, judged once
(research/preregistrations/IX-1.md). The equity-index CFDs are judged by IX-2 with the same frozen rule
and module once their bars exist (the "EQ" group stays empty here).

    python scripts/ix1.py spec          # freeze the design (writes research/specs/IX-1.json)
    python scripts/ix1.py preregister   # register the trial (after the document quotes the spec hash)
    python scripts/ix1.py run           # validation once -> gates -> report (refuses a second run)
    python scripts/ix1.py holdout       # sealed periods, passers only, once

Hypothesis (Gao, Han, Li & Zhou 2018; Baltussen, Da, Lammers & Martens 2021): the return from the previous
close to 30 minutes before today's close predicts the last 30 minutes, because short-gamma hedgers and
leveraged-ETF rebalancing trade late in the direction of the day's move. Trade in the direction of that
return for the last 30 minutes, priced at the real bid/ask (aitrader/research/discovery/ixmom.py).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.bars import BarSeries  # noqa: E402
from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import ixmom as IX  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

PID, HID = "IX-1", "IX-1-H"
R = ROOT / "research"
DOC = "research/preregistrations/IX-1.md"
SPEC = R / "specs" / "IX-1.json"
OUT = R / "knowledge" / "IX-1.json"
HOUT = R / "knowledge" / "IX-1-H.json"
CODE = ("aitrader/research/discovery/ixmom.py", "scripts/ix1.py")
IX_DATA = ROOT / "data" / "ix"

#: Groups judged separately: each is one book (equal weight across its instruments, per day).
GROUPS = {
    "EQ": {"symbols": [], "universe": "index-cfd-intraday", "bars": "M5 (Dukascopy minute candles, data/ix)",
           "validation": None, "holdout": None},
    "MET": {"symbols": ["XAUUSD", "XAGUSD"], "universe": "fx-majors", "bars": "M5 (FX-Data mirror, data/m5)",
            "validation": ("2013-01-01", "2017-01-01"), "holdout": ("2017-01-01", "2018-07-01")},
}
VARIANTS = {"ALL": 0.0, "STRONG": 1.0}  # min |signal| in causal standard deviations
OFFSET_MIN = 30
VOL_DAYS = 60
STOP_SD = 2.5
#: Costs per fill / round trip, in price units. Metals: the project's retail model (0.1 pip slippage per
#: fill, 0.7 pip commission per round trip). Index CFDs are spread-only; slippage per fill is a quarter of
#: the instrument's median quoted spread, measured on the bars before the validation period.
METAL_COSTS = {"XAUUSD": {"slip": 0.01, "commission": 0.07}, "XAGUSD": {"slip": 0.0001, "commission": 0.0007}}
INDEX_SLIP_SPREAD_FRACTION = 0.25
COST_GRID = (1.5, 2.0)
DELAY_BARS = 1
GATES = {
    "min_trades": 200,
    "net_bps": "> 0 at base costs",
    "t_day": "t on the daily book >= the registry threshold (Bonferroni over every test ever registered)",
    "costs_x1.5": "net > 0",
    "costs_x2": "net > 0 (otherwise FRAGILE, which fails)",
    "delay": "net > 0 with entry one bar later",
    "halves": "both chronological halves of validation net > 0",
    "instruments": ">= 60% of instruments with >= 50 trades net > 0 (and at least 2 instruments)",
    "profit_factor": ">= 1.05 on R",
    "top_year_share": "no calendar year contributes more than 50% of the total net",
}
HOLDOUT_RULE = ("validation passers only, once: net > 0, t_day >= z(1 - 0.05 / k) for k passers, costs x1.5 > 0, "
                "delay > 0")


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def tests() -> list[str]:
    return [f"{g}-{v}" for g in GROUPS if GROUPS[g]["symbols"] for v in VARIANTS]


def threshold(reg: Registry) -> float:
    total = sum(t.tests for t in reg.trials)
    return round(max(3.0, bonferroni_t(total + len(tests()))), 4)


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": IX.IX_VERSION, "groups": GROUPS, "variants": VARIANTS,
            "offset_min": OFFSET_MIN, "vol_days": VOL_DAYS, "stop_sd": STOP_SD, "closes": {
                s: [IX.CLOSES[s][0], IX.CLOSES[s][1].isoformat()] for g in GROUPS.values() for s in g["symbols"]},
            "metal_costs": METAL_COSTS, "index_slip_spread_fraction": INDEX_SLIP_SPREAD_FRACTION,
            "cost_grid": list(COST_GRID), "delay_bars": DELAY_BARS, "gates": GATES, "holdout_rule": HOLDOUT_RULE,
            "tests": tests(), "t_required_validation": threshold(reg), "code_sha256": code_hash()}


# ── data ─────────────────────────────────────────────────────────────────

def _epoch(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load_bars(group: str, sym: str, period: tuple[str, str], key=None) -> IX.Bars:
    """M5 bid/ask bars of one instrument inside `period`. Bars of a sealed universe from its seal date on
    are refused without the holdout key."""
    folder = ROOT / "data" / ("m5" if group == "MET" else "ix")
    parts = [BarSeries.load(p) for p in sorted(folder.glob(f"{sym}_M5_*.npz"))]
    if not parts:
        raise FileNotFoundError(f"{sym}: no M5 bars in {folder}")
    s = BarSeries.concat(parts)
    s = s.take(np.argsort(s.open_time, kind="stable"))
    s = s.take(np.r_[True, np.diff(s.open_time) > 0])
    lo, hi = _epoch(period[0]), _epoch(period[1])
    seal = Holdout.load(R / "holdout.json")
    if GROUPS[group]["universe"] == seal.universe and hi > seal.start_epoch() and key is None:
        raise PermissionError(f"{sym}: {period} reaches into the sealed {seal.universe} period; the key is required")
    s = s.take((s.open_time >= lo) & (s.open_time < hi) & (s.ask_open >= s.bid_open))
    return IX.Bars.from_series(s)


def index_slip(sym: str, before: str) -> float:
    """A quarter of the median quoted spread on the bars BEFORE the judged period (a cost input, not an
    outcome)."""
    parts = [BarSeries.load(p) for p in sorted(IX_DATA.glob(f"{sym}_M5_*.npz"))]
    s = BarSeries.concat(parts)
    m = s.open_time < _epoch(before)  # bars before the judged period only
    return float(INDEX_SLIP_SPREAD_FRACTION * np.median((s.ask_open - s.bid_open)[m]))


def costs_for(group: str, sym: str, period: tuple[str, str]) -> dict:
    if group == "MET":
        return {"slip_pts": METAL_COSTS[sym]["slip"], "commission_pts": METAL_COSTS[sym]["commission"]}
    return {"slip_pts": index_slip(sym, period[0]), "commission_pts": 0.0}


# ── judging ─────────────────────────────────────────────────────────────

def run_variant(bars: dict[str, IX.Bars], costs: dict[str, dict], z: float, **kw) -> list[IX.Trade]:
    out: list[IX.Trade] = []
    for s, b in bars.items():
        out += IX.trades(b, offset_min=OFFSET_MIN, min_abs_z=z, vol_days=VOL_DAYS, stop_sd=STOP_SD,
                         **costs[s], **kw)
    return out


def rolling_months(ts: list[IX.Trade], length: int = 3) -> dict:
    by: dict[tuple[int, int], float] = {}
    for x in ts:
        by[(x.day.year, x.day.month)] = by.get((x.day.year, x.day.month), 0.0) + x.r
    keys = sorted(by)
    if len(keys) < length:
        return {"windows": 0}
    vals = [sum(by[k] for k in keys[i:i + length]) for i in range(len(keys) - length + 1)]
    return {"windows": len(vals), "profitable_share": round(float(np.mean([v > 0 for v in vals])), 3)}


def judge(ts: list[IX.Trade], stress: dict[str, list[IX.Trade]], t_req: float) -> dict:
    s = IX.summary(ts)
    if not ts:
        return {"summary": s, "gates": {}, "passed": False}
    days = sorted({x.day for x in ts})
    mid = days[len(days) // 2]
    halves = [IX.summary([x for x in ts if x.day < mid]), IX.summary([x for x in ts if x.day >= mid])]
    elig = {k: v for k, v in s["by_symbol"].items() if v["trades"] >= 50}
    pos = [k for k, v in elig.items() if v["net_bps"] > 0]
    yearly = {}
    for x in ts:
        yearly[x.day.year] = yearly.get(x.day.year, 0.0) + x.net_bps
    total = sum(yearly.values())
    top_share = max(yearly.values()) / total if total > 0 else None
    months = len({(x.day.year, x.day.month) for x in ts})
    g = {
        "min_trades": s["trades"] >= GATES["min_trades"],
        "net_bps": s["net_bps"] > 0,
        "t_day": (s["t_day"] or 0) >= t_req,
        "costs_x1.5": IX.summary(stress["x1.5"]).get("net_bps", -1) > 0,
        "costs_x2": IX.summary(stress["x2"]).get("net_bps", -1) > 0,
        "delay": IX.summary(stress["delay"]).get("net_bps", -1) > 0,
        "halves": all(h.get("net_bps", -1) > 0 for h in halves),
        "instruments": len(elig) >= 2 and len(pos) / len(elig) >= 0.6,
        "profit_factor": (s["profit_factor"] or 0) >= 1.05,
        "top_year_share": top_share is not None and top_share <= 0.5,
    }
    return {"summary": s, "trades_per_month": round(s["trades"] / max(months, 1), 2),
            "stress": {k: {q: IX.summary(v).get(q) for q in ("trades", "gross_bps", "cost_bps", "net_bps", "t_day")}
                       for k, v in stress.items()},
            "halves": [{q: h.get(q) for q in ("trades", "net_bps", "t_day")} for h in halves],
            "rolling_3m": rolling_months(ts), "instruments_positive": f"{len(pos)}/{len(elig)}",
            "top_year_share": round(top_share, 3) if top_share is not None else None,
            "gates": g, "failed": [k for k, v in g.items() if not v], "passed": all(g.values())}


def evaluate(period_of, key=None, t_req: float = 0.0) -> dict:
    res = {}
    for gname, g in GROUPS.items():
        if not g["symbols"]:
            continue
        period = period_of(g)
        bars = {s: load_bars(gname, s, period, key) for s in g["symbols"]}
        costs = {s: costs_for(gname, s, period) for s in g["symbols"]}
        for v, z in VARIANTS.items():
            base = run_variant(bars, costs, z)
            stress = {"x1.5": run_variant(bars, costs, z, cost_mult=1.5),
                      "x2": run_variant(bars, costs, z, cost_mult=2.0),
                      "delay": run_variant(bars, costs, z, delay=DELAY_BARS)}
            res[f"{gname}-{v}"] = {"period": list(period), "costs": costs, **judge(base, stress, t_req)}
            print(f"{gname}-{v}: {res[f'{gname}-{v}']['summary']}", flush=True)
            print(f"   gates failed: {res[f'{gname}-{v}']['failed']}", flush=True)
    return res


# ── commands ────────────────────────────────────────────────────────────

def cmd_spec() -> int:
    reg = registry()
    s = spec(reg)
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps({"spec": s, "sha256": spec_sha(s)}, indent=1, default=str) + "\n")
    print("spec", spec_sha(s), "t_required", s["t_required_validation"], "tests", s["tests"])
    return 0


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


def cmd_preregister() -> int:
    f = _frozen()
    doc = (ROOT / DOC).read_text()
    if f["sha256"] not in doc:
        raise SystemExit(f"{DOC} must quote the spec sha256 {f['sha256']}")
    reg = registry()
    uses = []
    for g in f["spec"]["groups"].values():
        if g["symbols"] and g["validation"]:
            uses.append(Use(g["universe"], date.fromisoformat(g["validation"][0]),
                            date.fromisoformat(g["validation"][1]), "judge"))
    reg.register(Trial(id=PID, registered=datetime.now(timezone.utc), title="IX-1: intraday momentum into the close",
                       hypothesis="The return from the previous close to 30 minutes before today's close predicts "
                                  "the last 30 minutes, after real bid/ask costs (gamma-hedging and rebalancing flow).",
                       uses=tuple(uses), tests=len(f["spec"]["tests"]), configurations=len(f["spec"]["tests"]),
                       preregistration=DOC, design={"spec_sha256": f["sha256"], "code_sha256": code_hash(),
                                                    "threshold_t": f["spec"]["t_required_validation"]}))
    print("registered", PID)
    return 0


def cmd_run() -> int:
    f = _frozen()
    reg = registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict: it is judged once")
    t_req = f["spec"]["t_required_validation"]
    res = evaluate(lambda g: tuple(g["validation"]), t_req=t_req)
    passers = [k for k, v in res.items() if v["passed"]]
    out = {"program": PID, "spec_sha256": f["sha256"], "code_sha256": code_hash(), "t_required": t_req,
           "results": res, "passers": passers, "verdict": "PASSED" if passers else "FAILED",
           "ai_component": "none: a deterministic rule; there is no model to compare against (Track A only)"}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), out["verdict"],
                               {"passers": passers, "failed": {k: v["failed"] for k, v in res.items()},
                                "net_bps": {k: v["summary"].get("net_bps") for k, v in res.items()},
                                "t_day": {k: v["summary"].get("t_day") for k, v in res.items()}}))
    print("verdict", out["verdict"], passers)
    return 0


def cmd_holdout() -> int:
    f = _frozen()
    reg = registry()
    if reg.verdict_of(PID) is None or reg.verdict_of(PID).status != "PASSED":
        raise SystemExit("the holdout is opened only for validation passers")
    passers = reg.verdict_of(PID).result["passers"]
    groups = sorted({p.split("-")[0] for p in passers})
    if HID not in [t.id for t in reg.trials]:
        uses = tuple(Use(GROUPS[g]["universe"], date.fromisoformat(GROUPS[g]["holdout"][0]), date(2100, 1, 1),
                         "judge") for g in groups if GROUPS[g]["holdout"])
        reg.register(Trial(id=HID, registered=datetime.now(timezone.utc), title="IX-1 holdout",
                           hypothesis="IX-1 validation passers hold on the sealed period", uses=uses,
                           tests=len(passers), configurations=len(passers), preregistration=DOC,
                           design={"spec_sha256": f["sha256"], "passers": passers}))
    key = open_final_test(reg, HID) if "MET" in groups else None
    t_req = round(bonferroni_t(len(passers)), 4)
    res = evaluate(lambda g: tuple(g["holdout"]), key=key, t_req=t_req)
    res = {k: v for k, v in res.items() if k in passers}
    ok = [k for k, v in res.items() if v["summary"].get("net_bps", -1) > 0 and (v["summary"].get("t_day") or 0) >= t_req
          and v["gates"]["costs_x1.5"] and v["gates"]["delay"]]
    out = {"program": HID, "t_required": t_req, "results": res, "passers": ok, "verdict": "PASSED" if ok else "FAILED"}
    HOUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(HID, datetime.now(timezone.utc), out["verdict"], {"passers": ok}))
    print("holdout verdict", out["verdict"], ok)
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "run": cmd_run, "holdout": cmd_holdout}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
