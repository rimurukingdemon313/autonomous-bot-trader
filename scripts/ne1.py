"""NE-1: two economically motivated New York-session hypotheses on US index CFDs, judged with the canonical
bid/ask engine (research/preregistrations/NE-1.md).

    python scripts/ne1.py spec          # freeze the design (writes research/specs/NE-1.json)
    python scripts/ne1.py preregister   # register NE-1 (after the document quotes the spec hash)
    python scripts/ne1.py develop       # development 2014-2016, once: every configuration, every gate
    python scripts/ne1.py validate      # validation 2017-2020, once, promoted primaries only

NE-ON  the overnight premium: long the cash close (16:00 New York) to 09:00 the next weekday.
NE-GAP overnight-intraday reversal: fade a large overnight move from 10:00 to 16:00.

Nothing is fitted. The only estimated quantities are causal rolling volatilities (60 prior days). The
2021-2024 holdout is not fetched; this script cannot read it (the data stops at 2020-12-31).
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
from aitrader.research.canon import engine as E  # noqa: E402
from aitrader.research.canon import sessions as S  # noqa: E402
from aitrader.research.canon import validate as V  # noqa: E402
from aitrader.research.discovery.rc import Rates  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID, VID = "NE-1", "NE-1-V"
R = ROOT / "research"
DOC = "research/preregistrations/NE-1.md"
SPEC = R / "specs" / "NE-1.json"
OUT_DEV = R / "knowledge" / "NE-1-dev.json"
OUT_VAL = R / "knowledge" / "NE-1-val.json"
CODE = ("aitrader/research/canon/engine.py", "aitrader/research/canon/validate.py",
        "aitrader/research/canon/sessions.py", "scripts/ne1.py")
DATA = ROOT / "data" / "ix"
UNIVERSE = "index-cfd-intraday"
SYMBOLS = ("USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD")
WARMUP = "2013-09-01"  # mid prices only, for the first 60-day volatilities (no 2013 price is ever a fill)
DEV = ("2014-01-01", "2017-01-01")
VAL = ("2017-01-01", "2021-01-01")
COSTS = E.Costs(slip_frac=0.25, stop_through_frac=0.5, commission_bp_side=0.0, markup_pa=2.5,
                short_dividend_pa=2.0, day_count=360)
SEEDS = (1, 2, 3)

#: Every configuration evaluated (all count as tests). The first of each family is its primary.
CONFIGS = {
    "ON-16-09": ("ON", dict(entry_hour=16, exit_hour=9)),
    "ON-16-08": ("ON", dict(entry_hour=16, exit_hour=8)),
    "ON-16-10": ("ON", dict(entry_hour=16, exit_hour=10)),
    "ON-15-08": ("ON", dict(entry_hour=15, exit_hour=8)),
    "ON-15-09": ("ON", dict(entry_hour=15, exit_hour=9)),
    "ON-15-10": ("ON", dict(entry_hour=15, exit_hour=10)),
    "GAP-z1.00-v60": ("GAP", dict(z=1.0, vol_days=60)),
    "GAP-z0.75-v60": ("GAP", dict(z=0.75, vol_days=60)),
    "GAP-z1.25-v60": ("GAP", dict(z=1.25, vol_days=60)),
    "GAP-z1.00-v40": ("GAP", dict(z=1.0, vol_days=40)),
    "GAP-z1.00-v80": ("GAP", dict(z=1.0, vol_days=80)),
    "GAP-z0.00-v60": ("GAP", dict(z=0.0, vol_days=60)),
}
PRIMARY = {"ON": "ON-16-09", "GAP": "GAP-z1.00-v60"}

DEV_GATES = {
    "min_trades": ">= 300 trades (three instruments pooled)",
    "net_bp": "> 0 after every cost",
    "t_day": ">= 2.0 on the daily book",
    "costs_x1.25": "net > 0", "costs_x1.5": "net > 0",
    "latency_1bar": "net > 0 with entry one bar later",
    "vs_random_window": "Welch t >= 2.0 against random entries with the same side, holding time and stop (3 seeds)",
    "mechanism": "ON: overnight gross > same-day 10:00-16:00 long gross, paired by day, t >= 2.0; "
                 "GAP: block permutation of sides p <= 0.05 and Welch t >= 2.0 against random sides",
    "without_top5": "net > 0 without the five best trades",
    "neighbours": "every other configuration of the family net > 0",
    "halves": "both chronological halves net > 0",
}
VAL_GATES = {
    "min_trades": ">= 300", "net_bp": "> 0", "t_day": ">= the Bonferroni threshold (spec t_required)",
    "costs_x1.25": "net > 0", "costs_x1.5": "net > 0", "latency_1bar": "net > 0",
    "vs_random_window": "Welch t >= 2.0", "mechanism": "as in development",
    "years": ">= 3 of the 4 calendar years net > 0",
    "vol_terciles": "net > 0 in >= 2 of 3 volatility terciles (cuts fixed on development)",
    "without_top5": "net > 0 and the five best trades < 50% of the total",
    "neighbours": "every other configuration of the family net > 0",
    "instruments": ">= 2 of 3 instruments net > 0",
    "monte_carlo": "block-bootstrap P(total <= 0) <= 0.05",
    "drawdown": "total net / maximum drawdown of the daily book >= 1.0",
}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def threshold(reg: Registry) -> float:
    return round(V.bonferroni_t(sum(t.tests for t in reg.trials) + len(CONFIGS)), 4)


def spec(reg: Registry) -> dict:
    return {"program": PID, "engine": E.CANON_VERSION, "validate": V.VALIDATE_VERSION, "sessions": S.SESSIONS_VERSION,
            "universe": UNIVERSE, "symbols": list(SYMBOLS), "warmup_mid_only_from": WARMUP, "development": list(DEV),
            "validation": list(VAL), "holdout": "2021-01-01..2025-01-01 sealed, never fetched",
            "configs": {k: [f, p] for k, (f, p) in CONFIGS.items()}, "primary": PRIMARY,
            "stop_sd": 3.0, "costs": COSTS.__dict__, "cost_stress": [1.25, 1.5, 2.0], "latency_bars": 1,
            "placebo_seeds": list(SEEDS), "permutation": {"n": 2000, "seed": 0, "block": 5},
            "monte_carlo": {"n": 5000, "seed": 0, "block_days": 10},
            "financing": "BIS policy rate (US) public at the rollover + 2.5%/yr markup, day count 360",
            "dev_gates": DEV_GATES, "val_gates": VAL_GATES, "tests": len(CONFIGS), "t_required": threshold(reg),
            "code_sha256": code_hash()}


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


# ── data ────────────────────────────────────────────────────────────────

def _epoch(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load(sym: str, end: str) -> E.Quotes:
    parts = [BarSeries.load(p) for p in sorted(DATA.glob(f"{sym}_H1_*.npz"))]
    s = BarSeries.concat(parts)
    s = s.take(np.argsort(s.open_time, kind="stable"))
    s = s.take(np.r_[True, np.diff(s.open_time) > 0])
    s = s.take((s.open_time >= _epoch(WARMUP)) & (s.open_time < _epoch(end)))
    return E.Quotes.from_series(s)


_RATES: Rates | None = None


def us_rate(epoch: int) -> float:
    global _RATES
    if _RATES is None:
        _RATES = Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    return _RATES.at("US", V.ny_date(epoch))


def orders_for(q: E.Quotes, family: str, params: dict) -> list[E.Order]:
    if family == "ON":
        return S.overnight(q, stop_sd=3.0, **params)
    return S.gap_reversal(q, stop_sd=3.0, **params)


def in_period(orders: list[E.Order], q: E.Quotes, period: tuple[str, str]) -> list[E.Order]:
    lo, hi = date.fromisoformat(period[0]), date.fromisoformat(period[1])
    return [o for o in orders if lo <= V.ny_date(int(q.t[o.decided_i])) < hi]


def run(quotes: dict[str, E.Quotes], orders: dict[str, list[E.Order]], costs: E.Costs = COSTS) -> list[E.Trade]:
    out = []
    for sym, q in quotes.items():
        out += E.simulate(q, orders[sym], costs, us_rate).trades
    return out


def evaluate(period: tuple[str, str], names: list[str], vol_cuts: dict | None = None) -> dict:
    quotes = {s: load(s, period[1]) for s in SYMBOLS}
    res: dict = {}
    base_on = {s: in_period(S.day_windows(q, 10, 6), q, period) for s, q in quotes.items()}
    intraday = run(quotes, base_on)
    bh = run(quotes, {s: in_period(S.day_windows(q, 16, 24), q, period) for s, q in quotes.items()})
    res["baselines"] = {"intraday_long_10_16": V.summary(intraday), "buy_and_hold_16_16": V.summary(bh),
                        "no_signal": {"net_bp": 0.0}}
    intraday_by_day = {(x.symbol, V.ny_date(x.entry_t)): x.gross_bp for x in intraday}
    for name in names:
        fam, params = CONFIGS[name]
        orders = {s: in_period(orders_for(q, fam, params), q, period) for s, q in quotes.items()}
        base = run(quotes, orders)
        r: dict = {"family": fam, "params": params, "summary": V.summary(base)}
        r["stress"] = {f"x{k}": V.summary(run(quotes, orders, COSTS.stressed(k))) for k in (1.25, 1.5, 2.0)}
        r["stress"]["latency_1bar"] = V.summary(run(quotes, orders, E.Costs(**{**COSTS.__dict__, "latency_bars": 1})))
        r["stress"]["gross_only"] = {"gross_bp": r["summary"].get("gross_bp")}
        placebos = [run(quotes, {s: S.random_windows(q, orders[s], seed) for s, q in quotes.items()}) for seed in SEEDS]
        r["vs_random_window"] = V.vs_placebo(base, placebos)
        if fam == "ON":
            # the matching day's 10:00-16:00 long is the session after the overnight's exit morning
            pairs = [(x.gross_bp, intraday_by_day[(x.symbol, V.ny_date(x.exit_t))]) for x in base
                     if (x.symbol, V.ny_date(x.exit_t)) in intraday_by_day]
            diff = np.array([a - b for a, b in pairs])
            t = V.tstat(diff)
            r["mechanism"] = {"pairs": len(pairs), "overnight_minus_intraday_gross_bp": round(float(diff.mean()), 4)
                              if len(diff) else None, "t": round(t, 3) if t is not None else None}
        else:
            sides = [run(quotes, {s: S.random_sides(orders[s], seed) for s in quotes}) for seed in SEEDS]
            r["vs_random_sides"] = V.vs_placebo(base, sides)
            r["permutation"] = V.permutation_sides(base, n=2000, seed=0, block=5)
            follow = {s: in_period(S.gap_reversal(q, stop_sd=3.0, how="follow", **params), q, period)
                      for s, q in quotes.items()}
            r["price_direction_baseline_follow"] = V.summary(run(quotes, follow))
        r["halves"] = V.halves(base)
        r["by_year"] = V.by_key(base, lambda x: V.ny_date(x.entry_t).year)
        r["by_instrument"] = V.by_key(base, lambda x: x.symbol)
        r["by_weekday"] = V.by_key(base, lambda x: V.ny_date(x.entry_t).weekday())
        sig = np.array([x.stop_bp / 3.0 for x in base if x.stop_bp])
        cuts = (vol_cuts or {}).get(name) or ([float(np.percentile(sig, 33.333)), float(np.percentile(sig, 66.667))]
                                              if len(sig) else [0.0, 0.0])
        r["vol_cuts_bp"] = [round(c, 4) for c in cuts]
        r["by_vol_tercile"] = V.by_key(base, lambda x: 0 if x.stop_bp / 3 <= cuts[0] else 1 if x.stop_bp / 3 <= cuts[1]
                                       else 2)
        r["monte_carlo"] = V.monte_carlo(base, n=5000, seed=0, block=10)
        res[name] = r
        s = r["summary"]
        print(f"{name}: trades {s.get('trades')} gross {s.get('gross_bp')} cost {s.get('cost_bp')} "
              f"net {s.get('net_bp')} t {s.get('t_day')}", flush=True)
    return res


def _pos(d: dict | None, k: str = "net_bp") -> bool:
    return bool(d) and (d.get(k) or 0) > 0 and d.get("trades", 0) > 0


def dev_gates(res: dict, fam: str) -> dict:
    p = res[PRIMARY[fam]]
    s = p["summary"]
    if fam == "ON":
        mech = (p["mechanism"]["t"] or 0) >= 2.0 and (p["mechanism"]["overnight_minus_intraday_gross_bp"] or 0) > 0
    else:
        mech = ((p["permutation"]["p"] or 1) <= 0.05) and ((p["vs_random_sides"]["welch_t"] or 0) >= 2.0)
    neigh = [k for k, (f, _) in CONFIGS.items() if f == fam and k != PRIMARY[fam]]
    g = {
        "min_trades": s.get("trades", 0) >= 300,
        "net_bp": _pos(s),
        "t_day": (s.get("t_day") or 0) >= 2.0,
        "costs_x1.25": _pos(p["stress"]["x1.25"]),
        "costs_x1.5": _pos(p["stress"]["x1.5"]),
        "latency_1bar": _pos(p["stress"]["latency_1bar"]),
        "vs_random_window": (p["vs_random_window"]["welch_t"] or 0) >= 2.0,
        "mechanism": mech,
        "without_top5": (s.get("net_bp_without_top_5") or -1) > 0,
        "neighbours": all(_pos(res[k]["summary"]) for k in neigh),
        "halves": all((h.get("net_bp") or -1) > 0 for h in p["halves"]) and len(p["halves"]) == 2,
    }
    return {"gates": g, "failed": [k for k, v in g.items() if not v], "promoted": all(g.values())}


def val_gates(res: dict, fam: str, t_req: float) -> dict:
    g0 = dev_gates(res, fam)["gates"]
    p = res[PRIMARY[fam]]
    s = p["summary"]
    years = [v["net_bp"] > 0 for v in p["by_year"].values()]
    terc = [v["net_bp"] > 0 for v in p["by_vol_tercile"].values()]
    inst = [v["net_bp"] > 0 for v in p["by_instrument"].values()]
    total, dd = s.get("total_bp_daybook", 0), s.get("max_drawdown_bp_daybook", 0)
    g = {
        "min_trades": g0["min_trades"], "net_bp": g0["net_bp"], "t_day": (s.get("t_day") or 0) >= t_req,
        "costs_x1.25": g0["costs_x1.25"], "costs_x1.5": g0["costs_x1.5"], "latency_1bar": g0["latency_1bar"],
        "vs_random_window": g0["vs_random_window"], "mechanism": g0["mechanism"],
        "years": sum(years) >= 3,
        "vol_terciles": sum(terc) >= 2,
        "without_top5": g0["without_top5"] and (s.get("top5_share_of_total") or 1) < 0.5,
        "neighbours": g0["neighbours"],
        "instruments": sum(inst) >= 2,
        "monte_carlo": (p["monte_carlo"].get("prob_total_le_0") or 1) <= 0.05,
        "drawdown": dd > 0 and total / dd >= 1.0,
    }
    return {"gates": g, "failed": [k for k, v in g.items() if not v], "passed": all(g.values())}


# ── commands ────────────────────────────────────────────────────────────

def cmd_spec() -> int:
    s = spec(registry())
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps({"spec": s, "sha256": spec_sha(s)}, indent=1, default=str) + "\n")
    print("spec", spec_sha(s), "t_required", s["t_required"], "tests", s["tests"])
    return 0


def cmd_preregister() -> int:
    f = _frozen()
    if f["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {f['sha256']}")
    reg = registry()
    reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                       title="NE-1: overnight premium and overnight-intraday reversal, US index CFDs (canonical engine)",
                       hypothesis="NE-ON: US index CFDs earn a positive premium from the cash close to the next "
                                  "morning, net of spread, slippage and financing. NE-GAP: large overnight moves "
                                  "partially reverse during the next cash session, net of costs.",
                       uses=(Use(UNIVERSE, date.fromisoformat(WARMUP), date.fromisoformat(DEV[0]), "fit"),
                             Use(UNIVERSE, date.fromisoformat(DEV[0]), date.fromisoformat(DEV[1]), "select")),
                       tests=len(CONFIGS), configurations=len(CONFIGS), preregistration=DOC,
                       design={"spec_sha256": f["sha256"], "code_sha256": code_hash(),
                               "threshold_t": f["spec"]["t_required"]}))
    print("registered", PID)
    return 0


def cmd_develop() -> int:
    f = _frozen()
    reg = registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict: development is run once")
    res = evaluate(DEV, list(CONFIGS))
    judged = {fam: dev_gates(res, fam) for fam in PRIMARY}
    promoted = [PRIMARY[f] for f, j in judged.items() if j["promoted"]]
    out = {"program": PID, "stage": "development", "spec_sha256": f["sha256"], "code_sha256": code_hash(),
           "results": res, "gates": judged, "promoted": promoted,
           "verdict": "PROMOTED" if promoted else "FAILED", "ai_component": "none: deterministic rules"}
    OUT_DEV.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), "PASSED" if promoted else "FAILED",
                               {"promoted": promoted, "failed": {k: v["failed"] for k, v in judged.items()},
                                "net_bp": {k: res[k]["summary"].get("net_bp") for k in CONFIGS},
                                "t_day": {k: res[k]["summary"].get("t_day") for k in CONFIGS}}))
    print("development verdict", out["verdict"], promoted, {k: v["failed"] for k, v in judged.items()})
    return 0


def cmd_validate() -> int:
    f = _frozen()
    reg = registry()
    v = reg.verdict_of(PID)
    if v is None or v.status != "PASSED":
        raise SystemExit("validation is run only for configurations promoted in development")
    promoted = v.result["promoted"]
    if VID in [t.id for t in reg.trials]:
        raise SystemExit("validation was already run")
    dev = json.loads(OUT_DEV.read_text())
    fams = [CONFIGS[p][0] for p in promoted]
    names = [k for k, (fm, _) in CONFIGS.items() if fm in fams]
    reg.register(Trial(id=VID, registered=datetime.now(timezone.utc), title="NE-1 validation 2017-2020",
                       hypothesis="NE-1 promoted primaries hold on 2017-2020",
                       uses=(Use(UNIVERSE, date.fromisoformat(VAL[0]), date.fromisoformat(VAL[1]), "judge"),),
                       tests=len(promoted), configurations=len(names), preregistration=DOC))
    cuts = {k: dev["results"][k]["vol_cuts_bp"] for k in names}
    res = evaluate(VAL, names, cuts)
    judged = {fam: val_gates(res, fam, f["spec"]["t_required"]) for fam in fams}
    passed = [PRIMARY[fm] for fm, j in judged.items() if j["passed"]]
    out = {"program": VID, "stage": "validation", "t_required": f["spec"]["t_required"], "results": res,
           "gates": judged, "passed": passed, "verdict": "PASSED" if passed else "FAILED"}
    OUT_VAL.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(VID, datetime.now(timezone.utc), out["verdict"],
                               {"passed": passed, "failed": {k: j["failed"] for k, j in judged.items()}}))
    print("validation verdict", out["verdict"], passed)
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "develop": cmd_develop, "validate": cmd_validate}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
