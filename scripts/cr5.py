"""CR-5: static cross-venue carry on BTC and ETH: always short the Hyperliquid perpetual and long the Binance
perpetual (research/preregistrations/CR-5.md).

    python scripts/cr5.py spec | preregister
    python scripts/cr5.py develop      # 2023-06 -> 2025-06 (seen by CR-4: "select"), once
    python scripts/cr5.py holdout      # 2025-07-01 -> 2026-09-29, never fetched before; once, only if develop passes

No signal: the position is held continuously. It is closed and reopened (one full round trip on both legs) whenever
either leg's price has moved 25% from its reference since the last (re)open: at 3x margin per venue the losing leg's
collateral must be topped up before liquidation. Capital = 2N / 3 per coin (3x on each venue). Judged on excess
return over the US policy rate. Returns at 1x are reported, never gated.
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
from aitrader.research.crypto import xv as X  # noqa: E402
from aitrader.research.discovery.rc import Rates  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID, HID = "CR-5", "CR-5-H"
R = ROOT / "research"
DOC = "research/preregistrations/CR-5.md"
SPEC = R / "specs" / "CR-5.json"
OUT_DEV = R / "knowledge" / "CR-5-dev.json"
OUT_H = R / "knowledge" / "CR-5-holdout.json"
CODE = ("aitrader/research/crypto/xv.py", "scripts/cr5.py", "scripts/ingest_xv_window.py")
COINS = ("BTC", "ETH")
UNIVERSE = "crypto-xvenue-hl-binance"
DEV = ("2023-06-01", "2025-07-01")
HOLD = ("2025-07-01", "2026-09-29")
LEVERAGE = 3.0
REBAL_MOVE = 0.25
DEV_GATES = {"excess": "annualised excess at 3x > 0", "t_excess": ">= 2.0", "costs_x1.5": "excess > 0",
             "years": "both 2023-06..2024-06 and 2024-07..2025-06 excess > 0", "drawdown": "<= 15%"}
HOLDOUT_RULE = {"excess": "> 0 at 3x", "t_excess": ">= 2.0", "costs_x1.5": "excess > 0", "drawdown": "<= 15%",
                "monte_carlo": "block bootstrap P(total <= 0) <= 0.05"}


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
    return {"program": PID, "module": X.XV_VERSION, "coins": list(COINS), "side": "short Hyperliquid, long Binance",
            "development": list(DEV), "holdout": list(HOLD), "leverage_per_venue": LEVERAGE,
            "rebalance_move": REBAL_MOVE, "costs": "XvCosts majors: HL 4.5 bp, Binance 5 bp, half-spread 1, slippage 1",
            "risk_free": "BIS US policy rate public that day / 365", "dev_gates": DEV_GATES,
            "holdout_rule": HOLDOUT_RULE, "tests": 1, "code_sha256": code_hash()}


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


def _ep(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load(data_dir: Path, coin: str, end: str) -> X.Pair:
    z = np.load(data_dir / f"{coin}.npz")
    e = _ep(end)
    k = {n: z[n] < e for n in ("hl_t", "bn_t", "hl_ft", "bn_ft")}
    return X.Pair(coin, z["hl_t"][k["hl_t"]], z["hl_o"][k["hl_t"]], z["bn_t"][k["bn_t"]], z["bn_o"][k["bn_t"]],
                  z["hl_ft"][k["hl_ft"]], z["hl_fr"][k["hl_ft"]], z["bn_ft"][k["bn_ft"]], z["bn_fr"][k["bn_ft"]])


def static_positions(p: X.Pair, start: int, end: int, costs: X.XvCosts) -> list[X.XvPosition]:
    """Short HL / long BN from the first common daily open >= start; a segment ends at the first common daily open
    where either leg's price is >= 25% away from its value at the segment's start, or at the last common open
    before `end`."""
    common = np.intersect1d(p.hl_t[(p.hl_t >= start) & (p.hl_t < end)], p.bn_t[(p.bn_t >= start) & (p.bn_t < end)])
    out = []
    if len(common) < 2:
        return out
    i0 = 0
    hl = {int(t): p.hl_o[np.searchsorted(p.hl_t, t)] for t in common}
    bn = {int(t): p.bn_o[np.searchsorted(p.bn_t, t)] for t in common}
    for i in range(1, len(common)):
        t0, t = int(common[i0]), int(common[i])
        moved = (abs(hl[t] / hl[t0] - 1) >= REBAL_MOVE) or (abs(bn[t] / bn[t0] - 1) >= REBAL_MOVE)
        if moved or i == len(common) - 1:
            out.append(X._position(p, 1, t0, t, "rebalance" if moved else "end", costs))
            i0 = i
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


def book(data_dir: Path, period: tuple[str, str], costs: X.XvCosts) -> tuple[dict[int, float], list]:
    a, b = _ep(period[0]), _ep(period[1])
    pairs = {c: load(data_dir, c, period[1]) for c in COINS}
    pos = [q for c in COINS for q in static_positions(pairs[c], a, b, costs)]
    daily = X.daily_returns(pairs, pos, len(COINS), a, b)  # on 2N per coin (1x)
    return daily, pos


def stats(daily: dict[int, float], pos: list, lev: float) -> dict:
    days = sorted(daily)
    raw1 = np.array([daily[d] for d in days])
    raw = raw1 * lev
    rfd = np.array([rf(d) for d in days])
    ex = raw - rfd
    n = len(ex)
    sd = ex.std(ddof=1)
    cum = np.cumsum(ex)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum))
    by: dict = {}
    for d, x in zip(days, ex):
        y = datetime.fromtimestamp(d, timezone.utc)
        by.setdefault(f"{y.year}-{'H1' if y.month <= 6 else 'H2'}", []).append(x)
    return {"days": n, "positions": len(pos), "rebalances": sum(q.reason == "rebalance" for q in pos),
            "ann_return_pct": round(float(raw.mean() * 365 * 100), 3),
            "ann_return_1x_pct": round(float(raw1.mean() * 365 * 100), 3),
            "ann_rf_pct": round(float(rfd.mean() * 365 * 100), 3),
            "ann_excess_pct": round(float(ex.mean() * 365 * 100), 3),
            "ann_excess_1x_pct": round(float((raw1 - rfd).mean() * 365 * 100), 3),
            "t_excess": round(float(ex.mean() / (sd / math.sqrt(n))), 3) if sd > 0 else None,
            "sharpe_excess": round(float(ex.mean() / sd * math.sqrt(365)), 3) if sd > 0 else None,
            "max_dd_excess_pct": round(dd * 100, 3),
            "by_half_year_excess_pct": {k: round(float(np.mean(v) * 365 * 100), 3) for k, v in sorted(by.items())},
            "funding_bp_total": round(float(sum(q.funding_bp for q in pos)), 1),
            "basis_bp_total": round(float(sum(q.basis_bp for q in pos)), 1),
            "cost_bp_total": round(float(sum(q.cost_bp for q in pos)), 1), "_ex": ex.tolist()}


def mc(ex, n=5000, seed=0, block=10) -> dict:
    r = np.asarray(ex)
    m = len(r)
    rng = np.random.default_rng(seed)
    nb = math.ceil(m / block)
    tot = np.array([r[(rng.integers(0, m - block + 1, nb)[:, None] + np.arange(block)).ravel()[:m]].sum()
                    for _ in range(n)])
    return {"total_pct_p05_p50_p95": [round(float(np.percentile(tot, q)) * 100, 3) for q in (5, 50, 95)],
            "prob_total_le_0": round(float((tot <= 0).mean()), 4)}


def evaluate(data_dir: Path, period: tuple[str, str]) -> dict:
    base = stats(*book(data_dir, period, X.XvCosts()), LEVERAGE)
    s15 = stats(*book(data_dir, period, X.XvCosts().stressed(1.5)), LEVERAGE)
    return {"summary": {k: v for k, v in base.items() if k != "_ex"},
            "costs_x1.5": {k: v for k, v in s15.items() if k != "_ex"}, "monte_carlo": mc(base["_ex"])}


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
                       title="CR-5: static BTC/ETH carry, short Hyperliquid / long Binance, 3x, excess over cash",
                       hypothesis="Hyperliquid's BTC and ETH perpetuals pay structurally more funding than Binance's; "
                                  "a static short-HL/long-BN position at 3x per venue beats the US policy rate after "
                                  "costs and forced rebalances.",
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
    r = evaluate(ROOT / "data" / "cr4", DEV)
    s = r["summary"]
    h = s["by_half_year_excess_pct"]
    y1 = np.mean([v for k, v in h.items() if k in ("2023-H2", "2024-H1")])
    y2 = np.mean([v for k, v in h.items() if k in ("2024-H2", "2025-H1")])
    g = {"excess": s["ann_excess_pct"] > 0, "t_excess": (s["t_excess"] or 0) >= 2.0,
         "costs_x1.5": r["costs_x1.5"]["ann_excess_pct"] > 0, "years": bool(y1 > 0 and y2 > 0),
         "drawdown": s["max_dd_excess_pct"] <= 15.0}
    out = {"program": PID, "stage": "development", "spec_sha256": f["sha256"], **r, "gates": g,
           "failed": [k for k, v in g.items() if not v], "verdict": "PROMOTED" if all(g.values()) else "FAILED"}
    OUT_DEV.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), "PASSED" if all(g.values()) else "FAILED",
                               {"failed": out["failed"], "ann_excess_pct": s["ann_excess_pct"], "t": s["t_excess"]}))
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
    reg.register(Trial(id=HID, registered=datetime.now(timezone.utc), title="CR-5 holdout 2025-07 to 2026-09",
                       hypothesis="CR-5 holds on the sealed period", tests=1, configurations=1, preregistration=DOC,
                       uses=(Use(UNIVERSE, date.fromisoformat(HOLD[0]), date.fromisoformat(HOLD[1]), "judge"),)))
    r = evaluate(ROOT / "data" / "cr5-holdout", HOLD)
    s = r["summary"]
    g = {"excess": s["ann_excess_pct"] > 0, "t_excess": (s["t_excess"] or 0) >= 2.0,
         "costs_x1.5": r["costs_x1.5"]["ann_excess_pct"] > 0, "drawdown": s["max_dd_excess_pct"] <= 15.0,
         "monte_carlo": r["monte_carlo"]["prob_total_le_0"] <= 0.05}
    out = {"program": HID, **r, "gates": g, "failed": [k for k, x in g.items() if not x],
           "verdict": "PASSED" if all(g.values()) else "FAILED"}
    OUT_H.write_text(json.dumps(out, indent=1, default=str) + "\n")
    reg.record_verdict(Verdict(HID, datetime.now(timezone.utc), out["verdict"], {"failed": out["failed"]}))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "develop": cmd_develop, "holdout": cmd_holdout}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
