"""FX-TARGET: what $4,000 a month on $200,000 would take, from the FX results already judged (docs/FX_TARGET_REPORT.md).

    python scripts/fx_target.py      # -> research/results/FX-TARGET.json

Descriptive, not a test: it judges nothing, selects nothing and changes no verdict. It takes the monthly net returns
of the judged books and scales them to fixed risk levels chosen before looking (5%, 10% and 20% a year of volatility,
or ID-2's own 0.25%, 0.5% and 1% risk a trade), plus the one level at which the historical mean would have equalled 2%
a month. For each it reports the monthly dollar distribution on a fixed $200,000 (not compounded, as the target is
stated) and a 12-month block bootstrap of 60-month paths. The bootstrap assumes the sample's returns persist, which
none of these candidates has shown, so its probabilities are upper bounds.

    FXT-1  currency time-series momentum, 1975-1989 (H.10), swap-free; FAILED on t alone (2.71 against 3.6294)
    ID-2   the best of its 18 M5 configurations (ridge S15 tau 0.05), walk-forward 2011-2013, picked after the fact;
           REJECTED (t 1.56 against 3.5524; its profit-factor and pair gates failed)
    FXS-1  the time-of-day effect, M5 bid/ask 2009-2016; FAILED (net negative)
"""

from __future__ import annotations

import json
import math
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CAPITAL = 200_000.0
TARGET_USD = 4_000.0
TARGET_PCT = TARGET_USD / CAPITAL  # 2% a month
HORIZON_M, PATHS, BLOCK, SEED = 60, 10_000, 12, 7
DRAWDOWN_LEVELS = (0.10, 0.20, 0.50)  # 10% = a funded account's maximum loss; 50% = ruin
OUT = ROOT / "research" / "results" / "FX-TARGET.json"


# ── the judged books' monthly net returns (fractions of the capital at the book's own scale) ─────────────────

def fxt1_months() -> tuple[list[str], np.ndarray, np.ndarray]:
    """FXT-1's book as judged, and its daily marks (positions fixed inside each month, valued on H.10 noon rates)."""
    import fxt1 as T
    from aitrader.data.h10 import H10Store
    from aitrader.research.registry import Holdout
    px = T.prices_from_store(H10Store(ROOT / "data" / "h10", Holdout.load(ROOT / "research" / "holdout.json")).load())
    rows = [r for r in T.book(px, T.PERIOD) if r["n"] > 0]
    daily = []
    for r in rows:
        y, m = int(r["month"][:4]), int(r["month"][5:])
        ny, nm = T._prev(y, m, -1)
        t0, t1 = T.decision_time(y, m), T.decision_time(ny, nm)
        marks: dict[int, float] = {}
        for c, w in r["weights"].items():
            p = px[c]
            i0, i1 = p.fill_after(t0), p.fill_after(t1)
            if i0 is None or i1 is None:
                continue
            for i in range(i0 + 1, i1 + 1):
                marks[int(p.ord[i])] = marks.get(int(p.ord[i]), 0.0) + w * (p.p[i] / p.p[i - 1] - 1.0)
        daily += [marks[k] for k in sorted(marks)]
    return [r["month"] for r in rows], np.array([r["net"] for r in rows]), np.array(daily)


def id2_months() -> tuple[list[str], np.ndarray]:
    """ID-2's best configuration's monthly sums of R, net of every cost, as its artifact records them."""
    art = json.loads((ROOT / "research" / "knowledge" / "ID-2.json").read_text())
    mr = art["development"]["M-ridge-S15-tau0.05"]["detail"]["monthly_r"]
    ks = sorted(mr)
    return ks, np.array([mr[k] for k in ks], float)


def fxs1_months() -> tuple[list[str], np.ndarray, np.ndarray]:
    """FXS-1's judged trades, one unit of the capital per trade: net per month and per day, as fractions."""
    import fxs1 as F
    import id1
    panel = {k: v for k, v in id1.load(F.PERIOD).items() if k in F.PAIRS}
    trades, _ = F.make_trades(panel, F.PERIOD)
    days = F.daily(trades)
    months: dict[str, float] = OrderedDict()
    for d, v in days.items():
        months[f"{d:%Y-%m}"] = months.get(f"{d:%Y-%m}", 0.0) + v / 1e4
    return list(months), np.array(list(months.values())), np.array(list(days.values())) / 1e4


# ── the statistics ───────────────────────────────────────────────────────

def _worst_drawdown(x: np.ndarray) -> float:
    eq = np.r_[0.0, np.cumsum(x)]
    return float(np.max(np.maximum.accumulate(eq) - eq))


def paths(x: np.ndarray, n: int = PATHS, horizon: int = HORIZON_M, block: int = BLOCK, seed: int = SEED) -> np.ndarray:
    """Circular block bootstrap: n paths of `horizon` months built from runs of `block` consecutive sample months."""
    rng = np.random.default_rng(seed)
    b = min(block, max(1, len(x) // 3))
    k = int(math.ceil(horizon / b))
    starts = rng.integers(0, len(x), (n, k))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]) % len(x)
    return x[idx.reshape(n, -1)[:, :horizon]]


def profile(months: list[str], x: np.ndarray, scale: float, daily: np.ndarray | None = None,
            leverage: float | None = None) -> dict:
    """The monthly dollar figures of one risk level, on a fixed capital, and its bootstrap."""
    r = x * scale
    usd = r * CAPITAL
    sims = paths(r)
    eq = np.cumsum(sims, axis=1)
    dd = np.max(np.maximum.accumulate(np.concatenate([np.zeros((len(sims), 1)), eq], axis=1), axis=1)[:, 1:] - eq,
                axis=1)
    first_year = sims[:, :12].mean(axis=1)
    run = best = 0
    for v in r:
        run = run + 1 if v < 0 else 0
        best = max(best, run)
    years: dict[str, float] = {}
    for mth, v in zip(months, usd):
        years[mth[:4]] = years.get(mth[:4], 0.0) + v
    win12 = [usd[i:i + 12].sum() for i in range(0, max(1, len(usd) - 11))]
    out = {
        "scale": round(scale, 4), "months": len(r),
        "mean_month_usd": round(float(usd.mean())), "median_month_usd": round(float(np.median(usd))),
        "sd_month_usd": round(float(usd.std(ddof=1))), "a_year_pct": round(float(r.mean()) * 1200, 2),
        "vol_a_year_pct": round(float(r.std(ddof=1)) * math.sqrt(12) * 100, 2),
        "months_profitable": round(float((r > 0).mean()), 3), "months_at_target": round(float((usd >= TARGET_USD).mean()), 3),
        "worst_month_usd": round(float(usd.min())), "best_month_usd": round(float(usd.max())),
        "p05_month_usd": round(float(np.percentile(usd, 5))), "p95_month_usd": round(float(np.percentile(usd, 95))),
        "worst_drawdown_pct": round(_worst_drawdown(r) * 100, 2), "losing_months": int((r < 0).sum()),
        "longest_losing_run": best, "worst_12_months_usd": round(float(min(win12))),
        "by_year_usd": {y: round(v) for y, v in sorted(years.items())},
        "monthly_usd_deciles": [round(float(v)) for v in np.percentile(usd, [10, 20, 30, 40, 50, 60, 70, 80, 90])],
        "bootstrap_60m": {
            **{f"p_drawdown_{int(lv * 100)}pct": round(float((dd >= lv).mean()), 4) for lv in DRAWDOWN_LEVELS},
            "p_5y_loss": round(float((eq[:, -1] < 0).mean()), 4),
            "p_first_year_avg_at_target": round(float((first_year >= TARGET_PCT).mean()), 4),
            "p_5y_avg_at_target": round(float((sims.mean(axis=1) >= TARGET_PCT).mean()), 4),
            "median_5y_avg_month_usd": round(float(np.median(sims.mean(axis=1)) * CAPITAL)),
            "p05_5y_avg_month_usd": round(float(np.percentile(sims.mean(axis=1), 5) * CAPITAL)),
        },
    }
    if daily is not None:
        dd_ = daily * scale
        out["worst_day_pct"] = round(float(dd_.min()) * 100, 2)
        out["days_losing_5pct_or_more"] = int((dd_ <= -0.05).sum())
    if leverage is not None:
        out["average_gross_leverage"] = round(leverage * scale, 2)
    return out


def configurations(x: np.ndarray, base_vol: float | None, levels: dict[str, float]) -> dict[str, float]:
    """name -> scale. Volatility levels divide by the book's own volatility; 'target' is where the mean is 2%."""
    out = {k: (v / base_vol if base_vol else v) for k, v in levels.items()}
    m = float(x.mean())
    out["target"] = TARGET_PCT / m if m > 0 else None
    return out


def main() -> int:
    res: dict = {"capital_usd": CAPITAL, "target_month_usd": TARGET_USD,
                 "method": {"capital": "fixed, not compounded", "bootstrap": {"paths": PATHS, "horizon_months": HORIZON_M,
                                                                            "block_months": BLOCK, "seed": SEED},
                            "drawdown_levels": DRAWDOWN_LEVELS,
                            "caveat": "the bootstrap assumes the sample's returns persist; none of these books passed "
                                      "its judge, so every probability of reaching the target is an upper bound"}}
    # FXT-1
    m1, x1, d1 = fxt1_months()
    vol1 = float(x1.std(ddof=1) * math.sqrt(12))
    lev1 = json.loads((ROOT / "research" / "knowledge" / "FXT-1.json").read_text())["all"]["gross_leverage"]
    cfg1 = configurations(x1, vol1, {"conservative_5pct_vol": 0.05, "moderate_10pct_vol": 0.10,
                                     "aggressive_20pct_vol": 0.20})
    res["FXT-1"] = {"status": "FAILED on t alone (2.71 against 3.6294); never validated", "period": f"{m1[0]}..{m1[-1]}",
                    "book_vol_a_year_pct": round(vol1 * 100, 2),
                    "configurations": {k: profile(m1, x1, s, d1, lev1) for k, s in cfg1.items() if s},
                    # half the mean, the same swings: published effects lose about half after publication
                    "if_the_edge_halved": {"target_scale": round(TARGET_PCT / (x1.mean() / 2), 3),
                                           **profile(m1, x1 - x1.mean() / 2, TARGET_PCT / (x1.mean() / 2),
                                                     d1 - d1.mean() / 2, lev1)}}
    # ID-2's best configuration, R per month -> fraction at a risk per trade
    m2, r2 = id2_months()
    cfg2 = {"conservative_0.25pct_risk": 0.0025, "moderate_0.5pct_risk": 0.005, "aggressive_1pct_risk": 0.01,
            "target": TARGET_PCT / float(r2.mean()) if r2.mean() > 0 else None}
    res["ID-2 best (ridge S15 tau 0.05)"] = {
        "status": "REJECTED: t 1.56 against 3.5524, profit factor and pair gates failed; the best of 18 configurations, "
                  "picked after the fact", "period": f"{m2[0]}..{m2[-1]}",
        "configurations": {k: {"risk_per_trade_pct": round(s * 100, 3), **profile(m2, r2, s)} for k, s in cfg2.items()
                           if s}}
    # FXS-1
    m3, x3, d3 = fxs1_months()
    vol3 = float(x3.std(ddof=1) * math.sqrt(12))
    cfg3 = configurations(x3, vol3, {"conservative_5pct_vol": 0.05, "moderate_10pct_vol": 0.10,
                                     "aggressive_20pct_vol": 0.20})
    res["FXS-1"] = {"status": "FAILED: net negative", "period": f"{m3[0]}..{m3[-1]}", "book_vol_a_year_pct": round(vol3 * 100, 2),
                    "configurations": {k: profile(m3, x3, s, d3) for k, s in cfg3.items() if s},
                    "target_scale": None}
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    for name in ("FXT-1", "ID-2 best (ridge S15 tau 0.05)", "FXS-1"):
        print("==", name, res[name]["status"])
        for k, v in res[name]["configurations"].items():
            b = v["bootstrap_60m"]
            print(f"  {k:28s} scale {v['scale']:7.3f} mean ${v['mean_month_usd']:>7,} med ${v['median_month_usd']:>7,} "
                  f"prof {v['months_profitable']:.0%} >=4k {v['months_at_target']:.0%} worst ${v['worst_month_usd']:>8,} "
                  f"DD {v['worst_drawdown_pct']:.1f}% | P(DD>=10%) {b['p_drawdown_10pct']:.0%} P(DD>=50%) "
                  f"{b['p_drawdown_50pct']:.0%} P(5y avg>=4k) {b['p_5y_avg_at_target']:.0%}"
                  + (f" worst day {v['worst_day_pct']}%" if "worst_day_pct" in v else "")
                  + (f" lev {v['average_gross_leverage']}x" if "average_gross_leverage" in v else ""))
    h = res["FXT-1"]["if_the_edge_halved"]
    print(f"  FXT-1 if the edge halved: scale {h['target_scale']}, DD {h['worst_drawdown_pct']}%, "
          f"P(DD>=50%) {h['bootstrap_60m']['p_drawdown_50pct']:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
