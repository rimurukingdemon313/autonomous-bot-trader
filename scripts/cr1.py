"""CR-1: crypto perpetual-futures programs on Binance public data (research/preregistrations/CR-1.md).

    python scripts/cr1.py spec          # freeze the design (research/specs/CR-1.json)
    python scripts/cr1.py preregister   # register (after the document quotes the spec hash)
    python scripts/cr1.py develop       # 2020-2022 once: every configuration, every gate
    python scripts/cr1.py validate      # 2023-2024 once, promoted families only

CARRY  long spot + short USDT-M perpetual while trailing funding is positive (funding-rate carry).
TSMOM  time-series momentum on the perpetual, paying or receiving the actual funding.

The 2025-01 -> 2026-09 period is the sealed holdout: never fetched by this script's data workflow.
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
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID, VID = "CR-1", "CR-1-V"
R = ROOT / "research"
DOC = "research/preregistrations/CR-1.md"
SPEC = R / "specs" / "CR-1.json"
OUT_DEV = R / "knowledge" / "CR-1-dev.json"
OUT_VAL = R / "knowledge" / "CR-1-val.json"
CODE = ("aitrader/research/crypto/cr.py", "aitrader/research/canon/validate.py", "scripts/cr1.py",
        "scripts/ingest_binance.py")
DATA = ROOT / "data" / "cr"
UNIVERSE = "crypto-binance-usdtm"
#: USDT-M perpetuals whose funding archive starts at the archive's first month (2020-01): the point-in-time
#: universe (research/results/cr-probe.json). None was delisted.
SYMBOLS = ("ADAUSDT", "BCHUSDT", "BTCUSDT", "EOSUSDT", "ETCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "TRXUSDT",
           "XLMUSDT", "XRPUSDT")
DEV = ("2020-01-01", "2023-01-01")
VAL = ("2023-01-01", "2025-01-01")
HOLDOUT = ("2025-01-01", "2026-10-01")
COSTS = C.CrCosts()
SEEDS = (1, 2, 3)
CONFIGS = {
    "CARRY-k3-in1.0": ("CARRY", dict(k=3, theta_in=0.0001, theta_out=0.0)),
    "CARRY-k1-in1.0": ("CARRY", dict(k=1, theta_in=0.0001, theta_out=0.0)),
    "CARRY-k9-in1.0": ("CARRY", dict(k=9, theta_in=0.0001, theta_out=0.0)),
    "CARRY-k3-in0.5": ("CARRY", dict(k=3, theta_in=0.00005, theta_out=0.0)),
    "CARRY-k3-in2.0": ("CARRY", dict(k=3, theta_in=0.0002, theta_out=0.0)),
    "TSMOM-28": ("TSMOM", dict(lookback_d=28)),
    "TSMOM-14": ("TSMOM", dict(lookback_d=14)),
    "TSMOM-56": ("TSMOM", dict(lookback_d=56)),
}
PRIMARY = {"CARRY": "CARRY-k3-in1.0", "TSMOM": "TSMOM-28"}
CAPITAL = {"CARRY": 2.0, "TSMOM": 1.0}
DEV_GATES = {
    "min_days": ">= 500 daily portfolio returns", "min_positions": ">= 100 positions",
    "net": "annualised net return > 0", "t_day": ">= 2.0 on the daily portfolio return",
    "costs_x1.25": "net > 0", "costs_x1.5": "net > 0", "latency": "net > 0 when every fill is one more hour late",
    "vs_placebo": "CARRY: Welch t >= 2.0 of position net vs random-timing positions of the same durations "
                  "(seeds 1-3); TSMOM: Welch t >= 2.0 of daily returns vs random daily sides (seeds 1-3) and "
                  "block permutation of position sides p <= 0.05",
    "without_top5_days": "net > 0 without the five best days",
    "neighbours": "every other configuration of the family net > 0",
    "halves": "both chronological halves net > 0",
}
VAL_GATES = {**DEV_GATES, "t_day": ">= the Bonferroni threshold", "years": "2023 and 2024 each net > 0",
             "coins": ">= 6 of 11 coins net > 0", "monte_carlo": "block bootstrap P(total <= 0) <= 0.05",
             "drawdown": "total / max drawdown >= 1.0"}
HOLDOUT_RULE = ("validation passers only, registered separately, data fetched only then: net > 0, costs x1.5 "
                "net > 0, latency net > 0 and t_day >= 1.645")


def _ep(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


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
    return {"program": PID, "module": C.CR_VERSION, "universe": UNIVERSE, "symbols": list(SYMBOLS),
            "development": list(DEV), "validation": list(VAL), "holdout": list(HOLDOUT), "holdout_rule": HOLDOUT_RULE,
            "configs": {k: [f, p] for k, (f, p) in CONFIGS.items()}, "primary": PRIMARY, "capital_per_notional": CAPITAL,
            "costs": COSTS.__dict__, "cost_stress": [1.25, 1.5, 2.0], "latency_extra_h": 1, "placebo_seeds": list(SEEDS),
            "monte_carlo": {"n": 5000, "seed": 0, "block_days": 10}, "dev_gates": DEV_GATES, "val_gates": VAL_GATES,
            "tests": len(CONFIGS), "t_required": threshold(reg), "code_sha256": code_hash()}


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


# ── data ────────────────────────────────────────────────────────────────

def load(sym: str, end: str) -> C.Coin:
    z = np.load(DATA / f"{sym}.npz")
    e = _ep(end) + 7 * 86400  # exits of positions open at the period end may need a few days of bars
    if e > _ep(HOLDOUT[0]):
        e = _ep(HOLDOUT[0])  # never past the seal
    cut = lambda t: t < e  # noqa: E731
    return C.Coin(sym, z["spot_t"][cut(z["spot_t"])], z["spot_o"][cut(z["spot_t"])], z["perp_t"][cut(z["perp_t"])],
                  z["perp_o"][cut(z["perp_t"])], z["fund_t"][cut(z["fund_t"])], z["fund_r"][cut(z["fund_t"])])


# ── statistics on daily portfolio returns ───────────────────────────────

def stats(daily: dict[int, float], positions: list[C.Position], n_coins: int) -> dict:
    days = sorted(daily)
    r = np.array([daily[d] for d in days])
    n = len(r)
    if n < 2:
        return {"days": n}
    sd = r.std(ddof=1)
    t = float(r.mean() / (sd / math.sqrt(n))) if sd > 0 else None
    cum = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum))
    order = np.sort(r)[::-1]
    net = np.array([p.net_bp for p in positions]) if positions else np.array([])
    held = sum(p.exit_t - p.entry_t for p in positions)
    span = (days[-1] - days[0] + 86400) * n_coins
    by_year: dict = {}
    for d, x in zip(days, r):
        by_year.setdefault(datetime.fromtimestamp(d, timezone.utc).year, []).append(x)
    return {
        "days": n, "positions": len(positions),
        "positions_per_month": round(len(positions) / (n / 30.4375), 2),
        "exposure": round(held / span, 4) if span else None,
        "ann_net_pct": round(float(r.mean() * 365 * 100), 3),
        "ann_vol_pct": round(float(sd * math.sqrt(365) * 100), 3),
        "sharpe_ann": round(float(r.mean() / sd * math.sqrt(365)), 3) if sd > 0 else None,
        "t_day": round(t, 3) if t is not None else None,
        "ann_net_ci95_pct": [round(float((r.mean() - 1.96 * sd / math.sqrt(n)) * 365 * 100), 3),
                             round(float((r.mean() + 1.96 * sd / math.sqrt(n)) * 365 * 100), 3)],
        "total_pct": round(float(cum[-1] * 100), 3), "max_dd_pct": round(dd * 100, 3),
        "worst_5pct_day_pct": round(float(np.percentile(r, 5) * 100), 4),
        "ann_net_pct_without_top5_days": round(float(order[5:].mean() * 365 * 100), 3) if n > 5 else None,
        "by_year_ann_pct": {str(y): round(float(np.mean(v) * 365 * 100), 3) for y, v in sorted(by_year.items())},
        "pos_gross_bp": round(float(np.mean([p.gross_bp for p in positions])), 3) if positions else None,
        "pos_funding_bp": round(float(np.mean([p.funding_bp for p in positions])), 3) if positions else None,
        "pos_basis_bp": round(float(np.mean([p.basis_bp for p in positions])), 3) if positions else None,
        "pos_cost_bp": round(float(np.mean([p.cost_bp for p in positions])), 3) if positions else None,
        "pos_net_bp": round(float(net.mean()), 3) if len(net) else None,
        "pos_win_rate": round(float((net > 0).mean()), 4) if len(net) else None,
        "pos_median_days": round(float(np.median([(p.exit_t - p.entry_t) / 86400 for p in positions])), 2)
        if positions else None,
    }


def run_family(fam: str, params: dict, coins: dict[str, C.Coin], period: tuple[str, str], costs: C.CrCosts,
               placebo: dict | None = None) -> tuple[dict[int, float], list[C.Position], dict[str, dict]]:
    a, b = _ep(period[0]), _ep(period[1])
    per_coin, allp = {}, []
    for s, c in coins.items():
        if fam == "CARRY":
            pos, _ = C.carry_positions(c, costs=costs, start=a, end=b, entries=(placebo or {}).get(s), **params)
        else:
            pos, _ = C.momentum_positions(c, params["lookback_d"], costs, a, b, sides=(placebo or {}).get(s))
        allp += pos
        per_coin[s] = {d: x for d, x in C.daily_returns(c, pos, CAPITAL[fam], a, b + 7 * 86400,
                                                         "carry" if fam == "CARRY" else "momentum").items()}
    daily = C.portfolio(per_coin)
    coin_daily = per_coin
    return daily, allp, coin_daily


def random_timing(positions: list[C.Position], coins: dict[str, C.Coin], period: tuple[str, str], seed: int) -> dict:
    """Same number and durations of positions per coin, entered at uniformly random settlement times."""
    rng = np.random.default_rng(seed)
    a, b = _ep(period[0]), _ep(period[1])
    out: dict[str, list] = {}
    for s, c in coins.items():
        mine = [p for p in positions if p.symbol == s]
        ts = c.fund_t[(c.fund_t >= a) & (c.fund_t < b)]
        out[s] = []
        for p in mine:
            hold = p.exit_t - p.entry_t
            ok = ts[ts + hold < b]
            if len(ok):
                out[s].append((int(rng.choice(ok)), int(hold)))
    return out


def random_sides(coins: dict[str, C.Coin], period: tuple[str, str], seed: int) -> dict:
    rng = np.random.default_rng(seed)
    a, b = _ep(period[0]), _ep(period[1])
    days = list(range((a // 86400) * 86400, b, 86400))
    return {s: {d: int(x) for d, x in zip(days, rng.choice([-1, 1], len(days)))} for s in coins}


def welch(a, b) -> float | None:
    return V.welch_t(np.asarray(a, float), np.asarray(b, float))


def perm_sides(positions: list[C.Position], n=2000, seed=0, block=5) -> dict:
    if len(positions) < 2 * block:
        return {"p": None}
    move = np.array([p.side * (p.basis_bp + p.funding_bp) for p in positions])  # the long-side gross
    sides = np.array([p.side for p in positions])
    obs = float(np.mean(sides * move))
    rng = np.random.default_rng(seed)
    blocks = [sides[i:i + block] for i in range(0, len(sides), block)]
    ge = sum(float(np.mean(np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])[:len(move)] * move))
             >= obs for _ in range(n))
    return {"observed_gross_bp": round(obs, 3), "p": round((ge + 1) / (n + 1), 4)}


def mc(daily: dict[int, float], n=5000, seed=0, block=10) -> dict:
    r = np.array([daily[d] for d in sorted(daily)])
    m = len(r)
    if m < 2 * block:
        return {"sample": "insufficient"}
    rng = np.random.default_rng(seed)
    tot = np.empty(n)
    nb = math.ceil(m / block)
    for i in range(n):
        idx = (rng.integers(0, m - block + 1, nb)[:, None] + np.arange(block)).ravel()[:m]
        tot[i] = r[idx].sum()
    return {"total_pct_p05_p50_p95": [round(float(np.percentile(tot, q)) * 100, 3) for q in (5, 50, 95)],
            "prob_total_le_0": round(float((tot <= 0).mean()), 4)}


def evaluate(period: tuple[str, str], names: list[str]) -> dict:
    coins = {s: load(s, period[1]) for s in SYMBOLS}
    n = len(coins)
    res: dict = {}
    a, b = _ep(period[0]), _ep(period[1])
    # baselines
    always = {}
    bh = {}
    for s, c in coins.items():
        e = C._fill([c.spot_t, c.perp_t], a)
        if e is not None:
            entries = [(e[0] - COSTS.latency_h * 3600, b - e[0])]
            pos, _ = C.carry_positions(c, 0, 0, 1, COSTS, a, b, entries=entries)
            always[s] = C.daily_returns(c, pos, 2.0, a, b + 7 * 86400, "carry")
        days = np.arange((a // 86400) * 86400, b, 86400)
        px = np.array([c.spot_o[max(0, int(np.searchsorted(c.spot_t, d, "right")) - 1)] for d in days])
        bh[s] = {int(d): float(x) for d, x in zip(days[1:], px[1:] / px[:-1] - 1)}
    res["baselines"] = {"always_on_carry": stats(C.portfolio(always), [], n),
                        "spot_buy_and_hold_equal_weight": stats(C.portfolio(bh), [], n), "no_signal": {"ann_net_pct": 0.0}}
    for name in names:
        fam, params = CONFIGS[name]
        daily, pos, per_coin = run_family(fam, params, coins, period, COSTS)
        r: dict = {"family": fam, "params": params, "summary": stats(daily, pos, n)}
        r["stress"] = {f"x{k}": stats(*run_family(fam, params, coins, period, COSTS.stressed(k))[:2], n)
                       for k in (1.25, 1.5, 2.0)}
        lat = C.CrCosts(**{**COSTS.__dict__, "latency_h": COSTS.latency_h + 1})
        r["stress"]["latency"] = stats(*run_family(fam, params, coins, period, lat)[:2], n)
        if fam == "CARRY":
            pl = [run_family(fam, params, coins, period, COSTS, random_timing(pos, coins, period, s))[1] for s in SEEDS]
            pooled = [p.net_bp for run in pl for p in run]
            r["vs_placebo"] = {"placebo_pos_net_bp": round(float(np.mean(pooled)), 3) if pooled else None,
                               "welch_t": welch([p.net_bp for p in pos], pooled)}
        else:
            pl = [run_family(fam, params, coins, period, COSTS, random_sides(coins, period, s))[0] for s in SEEDS]
            pooled = [x for d in pl for x in d.values()]
            r["vs_placebo"] = {"placebo_ann_pct": round(float(np.mean(pooled)) * 365 * 100, 3),
                               "welch_t": welch(list(daily.values()), pooled)}
            r["permutation"] = perm_sides(sorted(pos, key=lambda p: p.entry_t))
        days = sorted(daily)
        mid = days[len(days) // 2]
        r["halves"] = [stats({d: daily[d] for d in days if d < mid}, [p for p in pos if p.entry_t < mid], n),
                       stats({d: daily[d] for d in days if d >= mid}, [p for p in pos if p.entry_t >= mid], n)]
        r["by_coin_ann_pct"] = {s: round(float(np.mean(list(v.values()))) * 365 * 100, 3)
                                for s, v in per_coin.items()}  # each coin's own return on its own capital
        r["monte_carlo"] = mc(daily)
        res[name] = r
        s = r["summary"]
        print(f"{name}: ann net {s.get('ann_net_pct')}% t {s.get('t_day')} sharpe {s.get('sharpe_ann')} "
              f"maxdd {s.get('max_dd_pct')}% positions {s.get('positions')}", flush=True)
    return res


def _pos(d: dict) -> bool:
    return (d.get("ann_net_pct") or -1) > 0


def dev_gates(res: dict, fam: str) -> dict:
    p = res[PRIMARY[fam]]
    s = p["summary"]
    neigh = [k for k, (f, _) in CONFIGS.items() if f == fam and k != PRIMARY[fam]]
    plac = (p["vs_placebo"].get("welch_t") or 0) >= 2.0
    if fam == "TSMOM":
        plac = plac and (p["permutation"].get("p") or 1) <= 0.05
    g = {
        "min_days": s.get("days", 0) >= 500, "min_positions": s.get("positions", 0) >= 100, "net": _pos(s),
        "t_day": (s.get("t_day") or 0) >= 2.0, "costs_x1.25": _pos(p["stress"]["x1.25"]),
        "costs_x1.5": _pos(p["stress"]["x1.5"]), "latency": _pos(p["stress"]["latency"]), "vs_placebo": plac,
        "without_top5_days": (s.get("ann_net_pct_without_top5_days") or -1) > 0,
        "neighbours": all(_pos(res[k]["summary"]) for k in neigh),
        "halves": all(_pos(h) for h in p["halves"]),
    }
    return {"gates": g, "failed": [k for k, v in g.items() if not v], "promoted": all(g.values())}


def val_gates(res: dict, fam: str, t_req: float) -> dict:
    g = dict(dev_gates(res, fam)["gates"])
    p = res[PRIMARY[fam]]
    s = p["summary"]
    g["min_days"] = s.get("days", 0) >= 500
    g["t_day"] = (s.get("t_day") or 0) >= t_req
    g["years"] = all(v > 0 for v in s.get("by_year_ann_pct", {}).values()) and len(s.get("by_year_ann_pct", {})) >= 2
    g["coins"] = sum(v > 0 for v in p["by_coin_ann_pct"].values()) >= 6
    g["monte_carlo"] = (p["monte_carlo"].get("prob_total_le_0") or 1) <= 0.05
    g["drawdown"] = (s.get("max_dd_pct") or 0) > 0 and s.get("total_pct", 0) / s["max_dd_pct"] >= 1.0
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
                       title="CR-1: funding-rate carry and time-series momentum, Binance USDT-M perpetuals",
                       hypothesis="CARRY: long spot + short perpetual while trailing funding is positive earns the "
                                  "funding paid by leveraged longs, net of fees, spread and basis risk. TSMOM: "
                                  "the sign of the past month's return predicts the next days', net of costs and "
                                  "actual funding.",
                       uses=(Use(UNIVERSE, date.fromisoformat(DEV[0]), date.fromisoformat(DEV[1]), "select"),),
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
    promoted = [PRIMARY[fm] for fm, j in judged.items() if j["promoted"]]
    out = {"program": PID, "stage": "development", "spec_sha256": f["sha256"], "code_sha256": code_hash(),
           "results": res, "gates": judged, "promoted": promoted, "verdict": "PROMOTED" if promoted else "FAILED"}
    OUT_DEV.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), "PASSED" if promoted else "FAILED",
                               {"promoted": promoted, "failed": {k: v["failed"] for k, v in judged.items()},
                                "ann_net_pct": {k: res[k]["summary"].get("ann_net_pct") for k in CONFIGS},
                                "t_day": {k: res[k]["summary"].get("t_day") for k in CONFIGS}}))
    print("development verdict", out["verdict"], promoted, {k: v["failed"] for k, v in judged.items()})
    return 0


def cmd_validate() -> int:
    f = _frozen()
    reg = registry()
    v = reg.verdict_of(PID)
    if v is None or v.status != "PASSED":
        raise SystemExit("validation is run only for families promoted in development")
    if VID in [t.id for t in reg.trials]:
        raise SystemExit("validation was already run")
    promoted = v.result["promoted"]
    fams = [CONFIGS[p][0] for p in promoted]
    names = [k for k, (fm, _) in CONFIGS.items() if fm in fams]
    reg.register(Trial(id=VID, registered=datetime.now(timezone.utc), title="CR-1 validation 2023-2024",
                       hypothesis="CR-1 promoted primaries hold on 2023-2024",
                       uses=(Use(UNIVERSE, date.fromisoformat(VAL[0]), date.fromisoformat(VAL[1]), "judge"),),
                       tests=len(promoted), configurations=len(names), preregistration=DOC))
    res = evaluate(VAL, names)
    judged = {fm: val_gates(res, fm, f["spec"]["t_required"]) for fm in fams}
    passed = [PRIMARY[fm] for fm, j in judged.items() if j["passed"]]
    out = {"program": VID, "t_required": f["spec"]["t_required"], "results": res, "gates": judged, "passed": passed,
           "verdict": "PASSED" if passed else "FAILED"}
    OUT_VAL.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(VID, datetime.now(timezone.utc), out["verdict"],
                               {"passed": passed, "failed": {k: j["failed"] for k, j in judged.items()}}))
    print("validation verdict", out["verdict"], passed, {k: j["failed"] for k, j in judged.items()})
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "develop": cmd_develop, "validate": cmd_validate}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
