"""CR-2: the plain funding carry (always on, no timing) must beat the risk-free rate
(research/preregistrations/CR-2.md).

    python scripts/cr2.py spec | preregister
    python scripts/cr2.py develop     # 2020-2024 (already seen by CR-1: recorded as "select"), once
    python scripts/cr2.py holdout     # 2025-01 -> 2026-09, once, only if development passes; data fetched only then

Long spot + short USDT-M perpetual on each of CR-1's 11 coins, equal capital (2N per coin), opened at the period
start and held to its end; the 1.8x forced-rebalance charge applies. The daily EXCESS return is the return on
capital minus the US policy rate (BIS, public that day) / 365: a market-neutral position must beat cash.
"""

from __future__ import annotations

import hashlib
import importlib.util
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
from aitrader.research.discovery.rc import Rates  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

_s = importlib.util.spec_from_file_location("cr1_for_cr2", ROOT / "scripts" / "cr1.py")
CR1 = importlib.util.module_from_spec(_s)
sys.modules["cr1_for_cr2"] = CR1
_s.loader.exec_module(CR1)

PID, HID = "CR-2", "CR-2-H"
R = ROOT / "research"
DOC = "research/preregistrations/CR-2.md"
SPEC = R / "specs" / "CR-2.json"
OUT_DEV = R / "knowledge" / "CR-2-dev.json"
OUT_H = R / "knowledge" / "CR-2-holdout.json"
CODE = ("aitrader/research/crypto/cr.py", "scripts/cr1.py", "scripts/cr2.py")
UNIVERSE = CR1.UNIVERSE
SYMBOLS = CR1.SYMBOLS
DEV = ("2020-01-01", "2025-01-01")
HOLD = ("2025-01-01", "2026-09-29")  # the last US policy rate on file is 2026-09-22 (+7 days stale limit)
YEARS = ("2020", "2021", "2022", "2023", "2024")
COSTS = C.CrCosts()
DEV_GATES = {
    "excess": "annualised excess return over the US policy rate > 0 (2020-2024)",
    "t_excess": ">= 2.0 on daily excess returns",
    "years": ">= 4 of the 5 calendar years with excess > 0 (walk-forward: yearly windows, one position per coin "
             "per year, nothing fitted)",
    "costs_x1.5": "excess > 0 with every cost x1.5",
    "drawdown": "maximum drawdown of cumulative excess return <= 10%",
    "coins": ">= 6 of 11 coins with excess > 0",
}
HOLDOUT_RULE = {"excess": "> 0", "t_excess": ">= 1.645 (one test, one-sided 5%)", "costs_x1.5": "excess > 0",
                "drawdown": "<= 10%"}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def spec() -> dict:
    return {"program": PID, "module": C.CR_VERSION, "universe": UNIVERSE, "symbols": list(SYMBOLS),
            "development": list(DEV), "holdout": list(HOLD), "years": list(YEARS), "costs": COSTS.__dict__,
            "capital_per_notional": 2.0, "rebalance_at": C.REBALANCE_AT,
            "risk_free": "BIS US policy rate public on the day, /365 per calendar day",
            "dev_gates": DEV_GATES, "holdout_rule": HOLDOUT_RULE, "tests": 1, "code_sha256": code_hash()}


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


_RATES: Rates | None = None


def rf_daily(day: int) -> float:
    global _RATES
    if _RATES is None:
        _RATES = Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    x = _RATES.at("US", V.ny_date(day + 43200))
    if not math.isfinite(x):
        raise SystemExit(f"no US policy rate for {V.ny_date(day)}: never assumed")
    return x / 100 / 365


def always_on(windows: list[tuple[str, str]], costs: C.CrCosts, data_dir: Path) -> tuple[dict, dict, list]:
    """One position per coin per window (opened at the window start, closed at its end), daily returns on 2N."""
    CR1.DATA = data_dir
    per_coin: dict[str, dict[int, float]] = {s: {} for s in SYMBOLS}
    positions = []
    for a_s, b_s in windows:
        a, b = CR1._ep(a_s), CR1._ep(b_s)
        for s in SYMBOLS:
            c = CR1.load(s, b_s) if b_s <= CR1.HOLDOUT[0] else load_any(s, data_dir, b)
            f = C._fill([c.spot_t, c.perp_t], a)
            if f is None:
                continue
            last = min(int(c.spot_t[-1]), int(c.perp_t[-1]), b - 3600)
            hold = max(3600, last - f[0])
            pos, _ = C.carry_positions(c, 0, 0, 1, costs, a, b, entries=[(f[0] - costs.latency_h * 3600, hold)])
            positions += pos
            per_coin[s].update(C.daily_returns(c, pos, 2.0, a, b, "carry"))
    return C.portfolio(per_coin), per_coin, positions


def load_any(sym: str, data_dir: Path, end_epoch: int) -> C.Coin:
    z = np.load(data_dir / f"{sym}.npz")
    k = lambda t: t < end_epoch  # noqa: E731
    return C.Coin(sym, z["spot_t"][k(z["spot_t"])], z["spot_o"][k(z["spot_t"])], z["perp_t"][k(z["perp_t"])],
                  z["perp_o"][k(z["perp_t"])], z["fund_t"][k(z["fund_t"])], z["fund_r"][k(z["fund_t"])])


def excess_stats(daily: dict[int, float], positions: list) -> dict:
    days = sorted(daily)
    ex = np.array([daily[d] - rf_daily(d) for d in days])
    raw = np.array([daily[d] for d in days])
    sd = ex.std(ddof=1)
    cum = np.cumsum(ex)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum))
    by_year: dict = {}
    for d, x in zip(days, ex):
        by_year.setdefault(str(datetime.fromtimestamp(d, timezone.utc).year), []).append(x)
    return {"days": len(ex), "ann_return_pct": round(float(raw.mean() * 365 * 100), 3),
            "ann_risk_free_pct": round(float((raw - ex).mean() * 365 * 100), 3),
            "ann_excess_pct": round(float(ex.mean() * 365 * 100), 3),
            "t_excess": round(float(ex.mean() / (sd / math.sqrt(len(ex)))), 3) if sd > 0 else None,
            "sharpe_excess": round(float(ex.mean() / sd * math.sqrt(365)), 3) if sd > 0 else None,
            "max_dd_excess_pct": round(dd * 100, 3),
            "by_year_excess_pct": {y: round(float(np.mean(v) * 365 * 100), 3) for y, v in sorted(by_year.items())},
            "positions": len(positions), "rebalances": int(sum(p.rebalances for p in positions)),
            "pos_funding_bp": round(float(np.mean([p.funding_bp for p in positions])), 2) if positions else None,
            "pos_basis_bp": round(float(np.mean([p.basis_bp for p in positions])), 2) if positions else None,
            "pos_cost_bp": round(float(np.mean([p.cost_bp for p in positions])), 2) if positions else None}


def coins_excess(per_coin: dict) -> dict:
    out = {}
    for s, v in per_coin.items():
        if v:
            out[s] = round(float(np.mean([x - rf_daily(d) for d, x in v.items()]) * 365 * 100), 3)
    return out


def cmd_spec() -> int:
    s = spec()
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps({"spec": s, "sha256": spec_sha(s)}, indent=1, default=str) + "\n")
    print("spec", spec_sha(s))
    return 0


def cmd_preregister() -> int:
    f = _frozen()
    if f["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {f['sha256']}")
    reg = registry()
    reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                       title="CR-2: always-on funding carry vs the risk-free rate, Binance USDT-M",
                       hypothesis="A delta-neutral long-spot/short-perpetual position on the 11 coins earns more than "
                                  "the US policy rate after fees, spread, slippage and forced rebalances.",
                       uses=(Use(UNIVERSE, date.fromisoformat(DEV[0]), date.fromisoformat(DEV[1]), "select"),),
                       tests=1, configurations=1, preregistration=DOC,
                       design={"spec_sha256": f["sha256"], "code_sha256": code_hash()}))
    print("registered", PID)
    return 0


def cmd_develop() -> int:
    f = _frozen()
    reg = registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit("development is run once")
    data = ROOT / "data" / "cr"
    windows = [(f"{y}-01-01", f"{int(y) + 1}-01-01") for y in YEARS]
    daily, per_coin, pos = always_on(windows, COSTS, data)
    s = excess_stats(daily, pos)
    s15 = excess_stats(*always_on(windows, COSTS.stressed(1.5), data)[::2])
    ce = coins_excess(per_coin)
    g = {"excess": s["ann_excess_pct"] > 0, "t_excess": (s["t_excess"] or 0) >= 2.0,
         "years": sum(v > 0 for y, v in s["by_year_excess_pct"].items() if y in YEARS) >= 4,
         "costs_x1.5": s15["ann_excess_pct"] > 0, "drawdown": s["max_dd_excess_pct"] <= 10.0,
         "coins": sum(v > 0 for v in ce.values()) >= 6}
    passed = all(g.values())
    out = {"program": PID, "stage": "development", "spec_sha256": f["sha256"], "summary": s, "costs_x1.5": s15,
           "by_coin_excess_pct": ce, "gates": g, "failed": [k for k, v in g.items() if not v],
           "verdict": "PROMOTED" if passed else "FAILED"}
    OUT_DEV.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), "PASSED" if passed else "FAILED",
                               {"failed": out["failed"], "ann_excess_pct": s["ann_excess_pct"],
                                "t_excess": s["t_excess"]}))
    print(json.dumps(out, indent=1, default=str))
    return 0


def cmd_holdout() -> int:
    _frozen()
    reg = registry()
    v = reg.verdict_of(PID)
    if v is None or v.status != "PASSED":
        raise SystemExit("the holdout is opened only if development passed")
    if HID in [t.id for t in reg.trials]:
        raise SystemExit("the holdout was already judged")
    reg.register(Trial(id=HID, registered=datetime.now(timezone.utc), title="CR-2 holdout 2025-01 to 2026-09",
                       hypothesis="CR-2 holds on the sealed period", tests=1, configurations=1, preregistration=DOC,
                       uses=(Use(UNIVERSE, date.fromisoformat(HOLD[0]), date.fromisoformat(HOLD[1]), "judge"),)))
    data = ROOT / "data" / "cr-holdout"
    daily, per_coin, pos = always_on([HOLD], COSTS, data)
    s = excess_stats(daily, pos)
    s15 = excess_stats(*always_on([HOLD], COSTS.stressed(1.5), data)[::2])
    g = {"excess": s["ann_excess_pct"] > 0, "t_excess": (s["t_excess"] or 0) >= 1.645,
         "costs_x1.5": s15["ann_excess_pct"] > 0, "drawdown": s["max_dd_excess_pct"] <= 10.0}
    out = {"program": HID, "summary": s, "costs_x1.5": s15, "by_coin_excess_pct": coins_excess(per_coin), "gates": g,
           "failed": [k for k, x in g.items() if not x], "verdict": "PASSED" if all(g.values()) else "FAILED"}
    OUT_H.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(HID, datetime.now(timezone.utc), out["verdict"], {"failed": out["failed"]}))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "develop": cmd_develop, "holdout": cmd_holdout}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
