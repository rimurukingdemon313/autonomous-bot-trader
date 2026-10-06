"""CR-3: cross-sectional funding carry over the point-in-time Binance universe, judged on EXCESS return over the
US policy rate (research/preregistrations/CR-3.md).

    python scripts/cr3.py spec | preregister
    python scripts/cr3.py develop      # 2020-2022, once
    python scripts/cr3.py validate     # 2023-2024, once, only if development promotes
    python scripts/cr3.py holdout      # 2025-01 -> 2026-09, once, only if validation passes (data fetched then)
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.canon import validate as V  # noqa: E402
from aitrader.research.crypto import cr as C  # noqa: E402
from aitrader.research.crypto import xs as X  # noqa: E402
from aitrader.research.discovery.rc import Rates  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID, VID, HID = "CR-3", "CR-3-V", "CR-3-H"
R = ROOT / "research"
DOC = "research/preregistrations/CR-3.md"
SPEC = R / "specs" / "CR-3.json"
OUT = {"dev": R / "knowledge" / "CR-3-dev.json", "val": R / "knowledge" / "CR-3-val.json",
       "hold": R / "knowledge" / "CR-3-holdout.json"}
CODE = ("aitrader/research/crypto/cr.py", "aitrader/research/crypto/xs.py", "aitrader/research/canon/validate.py",
        "scripts/cr3.py", "scripts/ingest_binance_xs.py")
DATA = ROOT / "data" / "cr3"
UNIVERSE = "crypto-binance-usdtm-all"
DEV = ("2020-01-01", "2023-01-01")
VAL = ("2023-01-01", "2025-01-01")
HOLD = ("2025-01-01", "2026-09-29")
SEASONING_D = 30
SEEDS = (1, 2, 3)
CONFIGS = {
    "XS-s5-in3": dict(slots=5, theta_in=0.0003, theta_out=0.0),
    "XS-s3-in3": dict(slots=3, theta_in=0.0003, theta_out=0.0),
    "XS-s10-in3": dict(slots=10, theta_in=0.0003, theta_out=0.0),
    "XS-s5-in1.5": dict(slots=5, theta_in=0.00015, theta_out=0.0),
    "XS-s5-in6": dict(slots=5, theta_in=0.0006, theta_out=0.0),
}
PRIMARY = "XS-s5-in3"
DEV_GATES = {
    "min_positions": ">= 100", "excess": "annualised excess over the US policy rate > 0",
    "t_excess": ">= 2.0 on daily excess returns", "costs_x1.5": "excess > 0", "latency": "excess > 0, fills 1 h later",
    "vs_placebo": "Welch t >= 2.0 of daily returns against random coin selection at the same times (seeds 1-3)",
    "neighbours": "every other configuration excess > 0", "years": ">= 2 of 3 calendar years excess > 0",
    "drawdown": "maximum drawdown of cumulative excess <= 15%", "without_top5_days": "excess > 0",
}
VAL_GATES = {**DEV_GATES, "t_excess": ">= the Bonferroni threshold (spec t_required)",
             "years": "2023 and 2024 each excess > 0", "monte_carlo": "block bootstrap P(total excess <= 0) <= 0.05"}
HOLDOUT_RULE = {"excess": "> 0", "t_excess": ">= 1.645", "costs_x1.5": "excess > 0", "drawdown": "<= 15%"}


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
    return {"program": PID, "module": X.XS_VERSION, "carry_module": C.CR_VERSION, "universe": UNIVERSE,
            "universe_rule": "every USDT-M perpetual with a matching spot pair in the archives "
                             "(research/results/cr-probe2.json); eligible at T if both have a bar at T and have "
                             f"traded {SEASONING_D} days", "development": list(DEV), "validation": list(VAL),
            "holdout": list(HOLD), "configs": CONFIGS, "primary": PRIMARY, "seasoning_d": SEASONING_D,
            "costs": "XsCosts: spot 10 bp, perp 5 bp; half-spread/slippage 1/1 BTC ETH, 2/1 CR-1 coins, 5/3 others",
            "rebalance_at": C.REBALANCE_AT, "risk_free": "BIS US policy rate public that day / 365",
            "dev_gates": DEV_GATES, "val_gates": VAL_GATES, "holdout_rule": HOLDOUT_RULE, "tests": len(CONFIGS),
            "t_required": threshold(reg), "code_sha256": code_hash()}


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


def _ep(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load_all(data_dir: Path, end: str) -> dict[str, C.Coin]:
    e = _ep(end)
    out = {}
    for f in sorted(data_dir.glob("*.npz")):
        z = np.load(f)
        k = lambda t: t < e  # noqa: E731
        if not k(z["spot_t"]).any() or not k(z["perp_t"]).any():
            continue
        out[f.stem] = C.Coin(f.stem, z["spot_t"][k(z["spot_t"])], z["spot_o"][k(z["spot_t"])],
                             z["perp_t"][k(z["perp_t"])], z["perp_o"][k(z["perp_t"])], z["fund_t"][k(z["fund_t"])],
                             z["fund_r"][k(z["fund_t"])])
    return out


_RATES: Rates | None = None


def rf(day: int) -> float:
    global _RATES
    if _RATES is None:
        _RATES = Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    x = _RATES.at("US", V.ny_date(day + 43200))
    if not math.isfinite(x):
        raise SystemExit(f"no US policy rate for {V.ny_date(day)}: never assumed")
    return x / 100 / 365


def stats(daily: dict[int, float], positions: list) -> dict:
    days = sorted(daily)
    raw = np.array([daily[d] for d in days])
    ex = raw - np.array([rf(d) for d in days])
    n = len(ex)
    sd = ex.std(ddof=1)
    cum = np.cumsum(ex)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum))
    order = np.sort(ex)[::-1]
    by_year: dict = {}
    for d, x in zip(days, ex):
        by_year.setdefault(str(datetime.fromtimestamp(d, timezone.utc).year), []).append(x)
    net = np.array([p.net_bp for p in positions]) if positions else np.array([])
    return {"days": n, "positions": len(positions), "coins_traded": len({p.symbol for p in positions}),
            "ann_return_pct": round(float(raw.mean() * 365 * 100), 3),
            "ann_excess_pct": round(float(ex.mean() * 365 * 100), 3),
            "t_excess": round(float(ex.mean() / (sd / math.sqrt(n))), 3) if sd > 0 else None,
            "sharpe_excess": round(float(ex.mean() / sd * math.sqrt(365)), 3) if sd > 0 else None,
            "max_dd_excess_pct": round(dd * 100, 3),
            "ann_excess_without_top5_days_pct": round(float(order[5:].mean() * 365 * 100), 3) if n > 5 else None,
            "by_year_excess_pct": {y: round(float(np.mean(v) * 365 * 100), 3) for y, v in sorted(by_year.items())},
            "pos_funding_bp": round(float(np.mean([p.funding_bp for p in positions])), 2) if positions else None,
            "pos_basis_bp": round(float(np.mean([p.basis_bp for p in positions])), 2) if positions else None,
            "pos_cost_bp": round(float(np.mean([p.cost_bp for p in positions])), 2) if positions else None,
            "pos_net_bp": round(float(net.mean()), 2) if len(net) else None,
            "pos_median_days": round(float(np.median([(p.exit_t - p.entry_t) / 86400 for p in positions])), 2)
            if positions else None,
            "rebalances": int(sum(p.rebalances for p in positions)),
            "data_end_closes": int(sum(p.reason == "data_end" for p in positions)),
            "_excess_series": ex.tolist()}


def mc(ex: list[float], n=5000, seed=0, block=10) -> dict:
    r = np.asarray(ex)
    m = len(r)
    rng = np.random.default_rng(seed)
    nb = math.ceil(m / block)
    tot = np.array([r[(rng.integers(0, m - block + 1, nb)[:, None] + np.arange(block)).ravel()[:m]].sum()
                    for _ in range(n)])
    return {"total_pct_p05_p50_p95": [round(float(np.percentile(tot, q)) * 100, 3) for q in (5, 50, 95)],
            "prob_total_le_0": round(float((tot <= 0).mean()), 4)}


def evaluate(period: tuple[str, str], names: list[str], data_dir: Path = DATA) -> dict:
    a, b = _ep(period[0]), _ep(period[1])
    coins = load_all(data_dir, period[1] if period[1] <= HOLD[0] else HOLD[1])
    res: dict = {"universe_size": len(coins)}
    for name in names:
        p = CONFIGS[name]
        run = lambda costs, rng=None: X.run_book(coins, p["slots"], p["theta_in"], p["theta_out"],  # noqa: E731
                                                 SEASONING_D, costs, a, b, rng=rng)
        base = run(X.XsCosts())
        s = stats(X.book_daily(coins, base, p["slots"], a, b), base)
        r = {"params": p, "summary": {k: v for k, v in s.items() if not k.startswith("_")}}
        r["stress"] = {}
        for k in (1.25, 1.5, 2.0):
            ps = run(X.XsCosts().stressed(k))
            r["stress"][f"x{k}"] = {q: v for q, v in stats(X.book_daily(coins, ps, p["slots"], a, b), ps).items()
                                    if not q.startswith("_")}
        lat = run(X.XsCosts(latency_h=2))
        r["stress"]["latency"] = {q: v for q, v in stats(X.book_daily(coins, lat, p["slots"], a, b), lat).items()
                                  if not q.startswith("_")}
        pl = []
        for seed in SEEDS:
            pp = run(X.XsCosts(), np.random.default_rng(seed))
            pl += stats(X.book_daily(coins, pp, p["slots"], a, b), pp)["_excess_series"]
        r["vs_placebo"] = {"placebo_ann_excess_pct": round(float(np.mean(pl)) * 365 * 100, 3),
                           "welch_t": V.welch_t(np.array(s["_excess_series"]), np.array(pl))}
        r["monte_carlo"] = mc(s["_excess_series"])
        res[name] = r
        sm = r["summary"]
        print(f"{name}: return {sm['ann_return_pct']}% excess {sm['ann_excess_pct']}% t {sm['t_excess']} "
              f"dd {sm['max_dd_excess_pct']}% positions {sm['positions']} coins {sm['coins_traded']}", flush=True)
    return res


def gates(res: dict, stage: str, t_req: float = 2.0) -> dict:
    p = res[PRIMARY]
    s = p["summary"]
    years = s["by_year_excess_pct"]
    g = {"min_positions": s["positions"] >= 100, "excess": s["ann_excess_pct"] > 0,
         "t_excess": (s["t_excess"] or 0) >= t_req, "costs_x1.5": p["stress"]["x1.5"]["ann_excess_pct"] > 0,
         "latency": p["stress"]["latency"]["ann_excess_pct"] > 0,
         "vs_placebo": (p["vs_placebo"]["welch_t"] or 0) >= 2.0,
         "neighbours": all(res[k]["summary"]["ann_excess_pct"] > 0 for k in CONFIGS if k != PRIMARY and k in res),
         "drawdown": s["max_dd_excess_pct"] <= 15.0,
         "without_top5_days": (s["ann_excess_without_top5_days_pct"] or -1) > 0}
    if stage == "dev":
        g["years"] = sum(years.get(y, -1) > 0 for y in ("2020", "2021", "2022")) >= 2
    else:
        g["years"] = all(years.get(y, -1) > 0 for y in ("2023", "2024"))
        g["monte_carlo"] = p["monte_carlo"]["prob_total_le_0"] <= 0.05
    return {"gates": g, "failed": [k for k, v in g.items() if not v], "passed": all(g.values())}


def cmd_spec() -> int:
    s = spec(registry())
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps({"spec": s, "sha256": spec_sha(s)}, indent=1, default=str) + "\n")
    print("spec", spec_sha(s), "t_required", s["t_required"])
    return 0


def cmd_preregister() -> int:
    f = _frozen()
    if f["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {f['sha256']}")
    reg = registry()
    reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                       title="CR-3: cross-sectional funding carry, point-in-time Binance universe, excess over cash",
                       hypothesis="Holding delta-neutral carry in the coins whose perpetuals currently pay the most "
                                  "funding earns more than the US policy rate after all costs.",
                       uses=(Use(UNIVERSE, date.fromisoformat(DEV[0]), date.fromisoformat(DEV[1]), "select"),),
                       tests=len(CONFIGS), configurations=len(CONFIGS), preregistration=DOC,
                       design={"spec_sha256": f["sha256"], "code_sha256": code_hash(),
                               "threshold_t": f["spec"]["t_required"]}))
    print("registered", PID)
    return 0


def _record(trial: str, stage: str, res: dict, judged: dict, extra: dict) -> None:
    out = {"program": trial, "stage": stage, "results": res, "gates": judged, **extra}
    OUT[stage].write_text(json.dumps(out, indent=1, default=str) + "\n")


def cmd_develop() -> int:
    f = _frozen()
    reg = registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit("development is run once")
    res = evaluate(DEV, list(CONFIGS))
    j = gates(res, "dev")
    _record(PID, "dev", res, j, {"spec_sha256": f["sha256"], "verdict": "PROMOTED" if j["passed"] else "FAILED"})
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), "PASSED" if j["passed"] else "FAILED",
                               {"failed": j["failed"], "ann_excess_pct": {k: res[k]["summary"]["ann_excess_pct"]
                                                                          for k in CONFIGS}}))
    print("development", "PROMOTED" if j["passed"] else "FAILED", j["failed"])
    return 0


def cmd_validate() -> int:
    f = _frozen()
    reg = registry()
    v = reg.verdict_of(PID)
    if v is None or v.status != "PASSED":
        raise SystemExit("validation only after development promotes")
    if VID in [t.id for t in reg.trials]:
        raise SystemExit("validation was already run")
    reg.register(Trial(id=VID, registered=datetime.now(timezone.utc), title="CR-3 validation 2023-2024",
                       hypothesis="CR-3 primary holds on 2023-2024", tests=1, configurations=len(CONFIGS),
                       preregistration=DOC,
                       uses=(Use(UNIVERSE, date.fromisoformat(VAL[0]), date.fromisoformat(VAL[1]), "judge"),)))
    res = evaluate(VAL, list(CONFIGS))
    j = gates(res, "val", f["spec"]["t_required"])
    _record(VID, "val", res, j, {"t_required": f["spec"]["t_required"], "verdict": "PASSED" if j["passed"] else "FAILED"})
    reg.record_verdict(Verdict(VID, datetime.now(timezone.utc), "PASSED" if j["passed"] else "FAILED",
                               {"failed": j["failed"]}))
    print("validation", "PASSED" if j["passed"] else "FAILED", j["failed"])
    return 0


def cmd_holdout() -> int:
    _frozen()
    reg = registry()
    v = reg.verdict_of(VID)
    if v is None or v.status != "PASSED":
        raise SystemExit("the holdout is opened only after validation passes")
    if HID in [t.id for t in reg.trials]:
        raise SystemExit("the holdout was already judged")
    reg.register(Trial(id=HID, registered=datetime.now(timezone.utc), title="CR-3 holdout 2025-01 to 2026-09",
                       hypothesis="CR-3 primary holds on the sealed period", tests=1, configurations=1,
                       preregistration=DOC,
                       uses=(Use(UNIVERSE, date.fromisoformat(HOLD[0]), date.fromisoformat(HOLD[1]), "judge"),)))
    res = evaluate(HOLD, [PRIMARY], ROOT / "data" / "cr3-holdout")
    p = res[PRIMARY]
    s = p["summary"]
    g = {"excess": s["ann_excess_pct"] > 0, "t_excess": (s["t_excess"] or 0) >= 1.645,
         "costs_x1.5": p["stress"]["x1.5"]["ann_excess_pct"] > 0, "drawdown": s["max_dd_excess_pct"] <= 15.0}
    j = {"gates": g, "failed": [k for k, x in g.items() if not x], "passed": all(g.values())}
    _record(HID, "hold", res, j, {"verdict": "PASSED" if j["passed"] else "FAILED"})
    reg.record_verdict(Verdict(HID, datetime.now(timezone.utc), "PASSED" if j["passed"] else "FAILED",
                               {"failed": j["failed"]}))
    print("holdout", "PASSED" if j["passed"] else "FAILED", j["failed"])
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "develop": cmd_develop, "validate": cmd_validate,
            "holdout": cmd_holdout}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
