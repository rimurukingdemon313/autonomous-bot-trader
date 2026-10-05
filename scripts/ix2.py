"""IX-2: intraday momentum into the cash close of equity-index CFDs, last hour, judged once
(research/preregistrations/IX-2.md).

    python scripts/ix2.py spec          # freeze the design (writes research/specs/IX-2.json)
    python scripts/ix2.py preregister   # register the trial (after the document quotes the spec hash)
    python scripts/ix2.py run           # judged period once -> gates -> report (refuses a second run)
    python scripts/ix2.py holdout       # 2021-2024, passers only, once (bars fetched only then)

The rule is IX-1's, unchanged (aitrader/research/discovery/ixmom.py, not modified: its hash is part of
IX-1's frozen record), applied to H1 bid/ask bars: signal = previous cash close -> C - 1 h; trade C - 1 h
-> C in its direction. Hour candles are used because the datafeed cannot deliver minute candles for many
years from CI runners (research/results/ix-probe.json); only indices whose cash close falls on the hour
are eligible.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.bars import BarSeries  # noqa: E402
from aitrader.research.discovery import ixmom as IX  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

PID, HID = "IX-2", "IX-2-H"
R = ROOT / "research"
DOC = "research/preregistrations/IX-2.md"
SPEC = R / "specs" / "IX-2.json"
OUT = R / "knowledge" / "IX-2.json"
HOUT = R / "knowledge" / "IX-2-H.json"
CODE = ("aitrader/research/discovery/ixmom.py", "scripts/ix2.py")
DATA = ROOT / "data" / "ix"
UNIVERSE = "index-cfd-intraday"
SYMBOLS = ["USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD", "JPNIDXJPY", "HKGIDXHKD", "AUSIDXAUD"]
JUDGE = ("2012-01-01", "2021-01-01")
HOLD = ("2021-01-01", "2025-01-01")
VARIANTS = {"ALL": 0.0, "STRONG": 1.0}
OFFSET_MIN = 60
VOL_DAYS = 60
STOP_SD = 2.5
SLIP_SPREAD_FRACTION = 0.25  # slippage per fill = a quarter of the instrument's median quoted spread
COST_GRID = (1.5, 2.0)
GATES = {
    "min_trades": 300,
    "net_bps": "> 0 at base costs",
    "t_day": "t on the daily equal-weight book >= Bonferroni over every test ever registered",
    "costs_x1.5": "net > 0",
    "costs_x2": "net > 0 (otherwise FRAGILE, which fails)",
    "late_entry": "net > 0 when entering at the typical price (O+H+L+C)/4 of the entry hour, adverse side",
    "halves": "both chronological halves net > 0",
    "instruments": ">= 60% of instruments with >= 50 trades net > 0",
    "profit_factor": ">= 1.05 on R",
    "top_year_share": "no calendar year contributes more than 50% of the total net",
}
HOLDOUT_RULE = "passers only, once, 2021-2024: net > 0, t_day >= z(1 - 0.05 / k), costs x1.5 > 0, late entry > 0"


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def tests() -> list[str]:
    return [f"EQ-{v}" for v in VARIANTS]


def threshold(reg: Registry) -> float:
    return round(max(3.0, bonferroni_t(sum(t.tests for t in reg.trials) + len(tests()))), 4)


def spec(reg: Registry) -> dict:
    return {"program": PID, "version": IX.IX_VERSION, "universe": UNIVERSE, "symbols": SYMBOLS,
            "closes": {s: [IX.CLOSES[s][0], IX.CLOSES[s][1].isoformat()] for s in SYMBOLS},
            "bars": "H1 bid/ask, Dukascopy hour candles (scripts/ingest_dukascopy_candles.py --hourly)",
            "judge": list(JUDGE), "holdout": list(HOLD), "variants": VARIANTS, "offset_min": OFFSET_MIN,
            "vol_days": VOL_DAYS, "stop_sd": STOP_SD, "slip_spread_fraction": SLIP_SPREAD_FRACTION,
            "commission": 0.0, "cost_grid": list(COST_GRID), "gates": GATES, "holdout_rule": HOLDOUT_RULE,
            "tests": tests(), "t_required": threshold(reg), "code_sha256": code_hash()}


# ── data and stress ─────────────────────────────────────────────────────

def _epoch(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load(sym: str, period: tuple[str, str]) -> tuple[IX.Bars, np.ndarray, np.ndarray]:
    """H1 bars inside `period` (bars with ask < bid dropped), plus bid/ask closes for the late-entry stress."""
    parts = [BarSeries.load(p) for p in sorted(DATA.glob(f"{sym}_H1_*.npz"))]
    if not parts:
        raise FileNotFoundError(f"{sym}: no H1 bars in {DATA}")
    s = BarSeries.concat(parts)
    s = s.take(np.argsort(s.open_time, kind="stable"))
    s = s.take(np.r_[True, np.diff(s.open_time) > 0])
    s = s.take((s.open_time >= _epoch(period[0])) & (s.open_time < _epoch(period[1])) & (s.ask_open >= s.bid_open))
    return IX.Bars.from_series(s), np.asarray(s.bid_close), np.asarray(s.ask_close)


def slip_for(b: IX.Bars) -> float:
    return float(SLIP_SPREAD_FRACTION * np.median(b.ao - b.bo))


def late_entry(ts: list[IX.Trade], b: IX.Bars, bc: np.ndarray, ac: np.ndarray, slip: float) -> list[IX.Trade]:
    """The same trades entered at the typical price of the entry hour, (O+H+L+C)/4 of the mid, plus half the
    entry bar's opening spread and the slippage on the adverse side. Exits are unchanged."""
    idx = b.index()
    out = []
    for x in ts:
        i = idx[IX.close_epoch(b.symbol, x.day) - OFFSET_MIN * 60]
        mid = lambda o, h, lo, c: (o + h + lo + c) / 4  # noqa: E731
        typ = (mid(b.bo[i], b.bh[i], b.bl[i], bc[i]) + mid(b.ao[i], b.ah[i], b.al[i], ac[i])) / 2
        half = (b.ao[i] - b.bo[i]) / 2
        entry = typ + x.side * (half + slip)
        mid_in = (b.bo[i] + b.ao[i]) / 2
        net = x.side * (x.exit - entry) / mid_in * 1e4
        dist = abs(x.entry - x.stop)
        out.append(replace(x, entry=float(entry), net_bps=float(net), cost_bps=float(x.gross_bps - net),
                           r=float(x.side * (x.exit - entry) / dist)))
    return out


def judge(ts: list[IX.Trade], stress: dict[str, list[IX.Trade]], t_req: float) -> dict:
    s = IX.summary(ts)
    if not ts:
        return {"summary": s, "gates": {}, "failed": ["no trades"], "passed": False}
    days = sorted({x.day for x in ts})
    mid = days[len(days) // 2]
    halves = [IX.summary([x for x in ts if x.day < mid]), IX.summary([x for x in ts if x.day >= mid])]
    elig = {k: v for k, v in s["by_symbol"].items() if v["trades"] >= 50}
    pos = [k for k, v in elig.items() if v["net_bps"] > 0]
    yearly: dict[int, float] = {}
    for x in ts:
        yearly[x.day.year] = yearly.get(x.day.year, 0.0) + x.net_bps
    total = sum(yearly.values())
    top = max(yearly.values()) / total if total > 0 else None
    by_month: dict[tuple[int, int], float] = {}
    for x in ts:
        by_month[(x.day.year, x.day.month)] = by_month.get((x.day.year, x.day.month), 0.0) + x.r
    keys = sorted(by_month)
    w3 = [sum(by_month[k] for k in keys[i:i + 3]) for i in range(max(0, len(keys) - 2))]
    g = {
        "min_trades": s["trades"] >= GATES["min_trades"],
        "net_bps": s["net_bps"] > 0,
        "t_day": (s["t_day"] or 0) >= t_req,
        "costs_x1.5": IX.summary(stress["x1.5"]).get("net_bps", -1) > 0,
        "costs_x2": IX.summary(stress["x2"]).get("net_bps", -1) > 0,
        "late_entry": IX.summary(stress["late"]).get("net_bps", -1) > 0,
        "halves": all(h.get("net_bps", -1) > 0 for h in halves),
        "instruments": len(elig) >= 2 and len(pos) / len(elig) >= 0.6,
        "profit_factor": (s["profit_factor"] or 0) >= 1.05,
        "top_year_share": top is not None and top <= 0.5,
    }
    return {"summary": s, "trades_per_month": round(s["trades"] / max(len(keys), 1), 2),
            "stress": {k: {q: IX.summary(v).get(q) for q in ("trades", "gross_bps", "cost_bps", "net_bps", "t_day")}
                       for k, v in stress.items()},
            "halves": [{q: h.get(q) for q in ("trades", "net_bps", "t_day")} for h in halves],
            "rolling_3m_profitable": round(float(np.mean([v > 0 for v in w3])), 3) if w3 else None,
            "instruments_positive": f"{len(pos)}/{len(elig)}", "top_year_share": round(top, 3) if top else None,
            "gates": g, "failed": [k for k, v in g.items() if not v], "passed": all(g.values())}


def evaluate(period: tuple[str, str], t_req: float) -> dict:
    data = {s: load(s, period) for s in SYMBOLS}
    slips = {s: slip_for(d[0]) for s, d in data.items()}
    res = {}
    for v, z in VARIANTS.items():
        def run(**kw):
            out = []
            for s, (b, _, _) in data.items():
                out += IX.trades(b, offset_min=OFFSET_MIN, min_abs_z=z, vol_days=VOL_DAYS, stop_sd=STOP_SD,
                                 slip_pts=slips[s], **kw)
            return out
        base = run()
        late = []
        for s, (b, bc, ac) in data.items():
            late += late_entry([x for x in base if x.symbol == s], b, bc, ac, slips[s])
        stress = {"x1.5": run(cost_mult=1.5), "x2": run(cost_mult=2.0), "late": late}
        res[f"EQ-{v}"] = {"period": list(period), "slippage_pts": slips, **judge(base, stress, t_req)}
        print(f"EQ-{v}: {res[f'EQ-{v}']['summary']}\n   failed: {res[f'EQ-{v}']['failed']}", flush=True)
    return res


# ── commands ────────────────────────────────────────────────────────────

def cmd_spec() -> int:
    s = spec(registry())
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps({"spec": s, "sha256": spec_sha(s)}, indent=1, default=str) + "\n")
    print("spec", spec_sha(s), "t_required", s["t_required"], "tests", s["tests"])
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
    if f["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {f['sha256']}")
    reg = registry()
    reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                       title="IX-2: intraday momentum into the cash close, index CFDs, last hour",
                       hypothesis="The return from the previous cash close to one hour before today's close predicts the "
                                  "last hour, after real CFD bid/ask costs (gamma-hedging and rebalancing flow).",
                       uses=(Use(UNIVERSE, date.fromisoformat(JUDGE[0]), date.fromisoformat(JUDGE[1]), "judge"),),
                       tests=len(f["spec"]["tests"]), configurations=len(f["spec"]["tests"]), preregistration=DOC,
                       design={"spec_sha256": f["sha256"], "code_sha256": code_hash(),
                               "threshold_t": f["spec"]["t_required"]}))
    print("registered", PID)
    return 0


def cmd_run() -> int:
    f = _frozen()
    reg = registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict: it is judged once")
    res = evaluate(JUDGE, f["spec"]["t_required"])
    passers = [k for k, v in res.items() if v["passed"]]
    out = {"program": PID, "spec_sha256": f["sha256"], "code_sha256": code_hash(), "t_required": f["spec"]["t_required"],
           "results": res, "passers": passers, "verdict": "PASSED" if passers else "FAILED",
           "ai_component": "none: a deterministic rule (Track A only)"}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), out["verdict"],
                               {"passers": passers, "failed": {k: v["failed"] for k, v in res.items()},
                                "net_bps": {k: v["summary"].get("net_bps") for k, v in res.items()},
                                "t_day": {k: v["summary"].get("t_day") for k, v in res.items()}}))
    print("verdict", out["verdict"], passers)
    return 0


def cmd_holdout() -> int:
    _frozen()
    reg = registry()
    v = reg.verdict_of(PID)
    if v is None or v.status != "PASSED":
        raise SystemExit("the holdout is opened only for passers")
    passers = v.result["passers"]
    if HID not in [t.id for t in reg.trials]:
        reg.register(Trial(id=HID, registered=datetime.now(timezone.utc), title="IX-2 holdout 2021-2024",
                           hypothesis="IX-2 passers hold on 2021-2024", uses=(Use(UNIVERSE, date.fromisoformat(HOLD[0]),
                           date.fromisoformat(HOLD[1]), "judge"),), tests=len(passers), configurations=len(passers),
                           preregistration=DOC))
    elif reg.status_of(HID) != "PENDING":
        raise SystemExit("the holdout was already judged")
    t_req = round(bonferroni_t(len(passers)), 4)
    res = {k: r for k, r in evaluate(HOLD, t_req).items() if k in passers}
    ok = [k for k, r in res.items() if r["summary"].get("net_bps", -1) > 0 and (r["summary"].get("t_day") or 0) >= t_req
          and r["gates"]["costs_x1.5"] and r["gates"]["late_entry"]]
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
