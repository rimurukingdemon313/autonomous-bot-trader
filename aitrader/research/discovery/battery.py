"""The validation battery and the expectancy decomposition.

A hypothesis is VALIDATED only if EVERY check passes on the segment it is judged on; each check
is stated before the run and none is skipped because it looks inconvenient:

    min_trades       enough trades to measure anything
    significance     clustered t >= the threshold frozen from the registry (all prior tests counted)
    beats_random     better than random entries with the same exit, instruments and trade count
    permutation      the condition's timing matters: circularly shifting it in time rarely does as well
    costs_stress     still positive with spread x1.5, slippage x2, commission and swap x1.5
    delay_stress     still positive when every entry is one bar late
    perturbation     still positive when every tercile edge moves by +-0.05 in quantile
    years            positive in most years that have enough trades
    instruments      positive on most instruments that have enough trades
    leave_one_out    positive with any single instrument removed
    regimes          no regime cell significantly negative, and positive in at least two
    outliers         the best 5% of trades do not carry half of the total

The deflated Sharpe ratio is reported for information. A veto hypothesis (the claim is that a
context LOSES) is judged on -R, so "robust" means "robustly bad".
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

import numpy as np

from .stats import cluster_t, deflated_sharpe, welch_t, week_of
from .study import Binning, Condition, Study, Trades

BATTERY_VERSION = "battery-1.0.0"
SESSIONS = ("asia", "london", "ny_overlap", "ny_late", "off_hours")
REGIME_CONTEXT = ("regime_er120", "regime_vol_ratio")


@dataclass(frozen=True)
class BatteryRules:
    t_threshold: float
    min_trades: int = 100
    random_welch_t: float = 2.0
    random_draws: int = 20
    permutations: int = 200
    permutation_alpha: float = 0.05
    min_year_trades: int = 20
    year_share: float = 0.6
    min_instrument_trades: int = 20
    instrument_share: float = 0.6
    regime_min_trades: int = 20
    regime_negative_t: float = -2.0
    regime_positive_cells: int = 2
    top_share: float = 0.05
    top_max_contribution: float = 0.5
    perturb: float = 0.05
    seed: int = 20260929

    def describe(self) -> dict:
        return {
            "min_trades": f"n >= {self.min_trades}",
            "significance": f"clustered (by week) t >= {self.t_threshold:.3f}",
            "beats_random": f"Welch t vs random entries >= {self.random_welch_t} ({self.random_draws} draws)",
            "permutation": f"circular-shift p < {self.permutation_alpha} ({self.permutations} shifts)",
            "costs_stress": "mean R > 0 with spread x1.5, slippage x2, commission and swap x1.5",
            "delay_stress": "mean R > 0 with entry one bar late",
            "perturbation": f"mean R > 0 with tercile edges moved by -{self.perturb} and +{self.perturb} quantile",
            "years": f">= {self.year_share:.0%} of years with >= {self.min_year_trades} trades positive (>= 2 years)",
            "instruments": f">= {self.instrument_share:.0%} of instruments with >= {self.min_instrument_trades} "
                           "trades positive (>= 2 instruments)",
            "leave_one_out": "mean R > 0 with any one instrument removed",
            "regimes": f"no regime cell (er120 x vol_ratio, discovery medians) with t <= {self.regime_negative_t}; "
                       f">= {self.regime_positive_cells} cells with >= {self.regime_min_trades} trades positive",
            "outliers": f"top {self.top_share:.0%} of trades carry < {self.top_max_contribution:.0%} of total R",
        }

    def to_json(self) -> dict:
        return asdict(self)


def _group_stats(r: np.ndarray, t: np.ndarray, keys: np.ndarray) -> dict:
    out = {}
    for k in sorted(set(keys.tolist()), key=str):
        m = keys == k
        st = cluster_t(r[m], week_of(t[m]))
        out[str(k)] = {"n": st["n"], "mean_R": _r(st["mean"]), "t": _r(st["t"], 3)}
    return out


def session_of(t: np.ndarray) -> np.ndarray:
    h = (np.asarray(t, np.int64) % 86400) // 3600
    idx = np.select([h < 7, h < 12, h < 16, h < 21], [0, 1, 2, 3], 4)
    return np.array(SESSIONS, dtype=object)[idx]


def decompose(tr: Trades) -> dict:
    """Where the expectancy comes from: wins, losses, excursions, holding time, costs, and how it
    splits by instrument, year, session and regime. Everything in R (1R = initial risk)."""
    r = tr.r
    n = tr.n
    if n == 0:
        return {"n": 0}
    wins, losses = r[r > 0], r[r < 0]
    order = np.argsort(tr.exit_t, kind="stable")
    eq = np.cumsum(r[order])
    dd = float(np.max(np.maximum.accumulate(np.concatenate(([0.0], eq)))[1:] - eq)) if n else 0.0
    streak = best = 0
    for x in r[order]:
        streak = streak + 1 if x < 0 else 0
        best = max(best, streak)
    st = tr.stats()
    reasons = {int(k): int(v) for k, v in zip(*np.unique(tr.reason, return_counts=True))}
    out = {
        "n": n, "mean_R": _r(st["mean"]), "t": _r(st["t"], 3), "clusters": st["clusters"],
        "win_rate": _r(len(wins) / n, 4), "avg_win_R": _r(wins.mean() if len(wins) else None),
        "avg_loss_R": _r(losses.mean() if len(losses) else None),
        "profit_factor": _r(wins.sum() / -losses.sum() if len(losses) and losses.sum() < 0 else None, 3),
        "total_R": _r(r.sum(), 3), "max_drawdown_R": _r(dd, 3), "longest_losing_streak": int(best),
        "mfe_R": {"mean": _r(np.nanmean(tr.mfe)), "median": _r(np.nanmedian(tr.mfe))},
        "mae_R": {"mean": _r(np.nanmean(tr.mae)), "median": _r(np.nanmedian(tr.mae))},
        "bars_held": {"mean": _r(tr.bars.mean(), 2), "median": _r(np.median(tr.bars), 1)},
        "cost_R": {"mean": _r(np.nanmean(tr.cost)), "gross_mean_R": _r(np.nanmean(r + tr.cost))},
        "exit_reasons": {{1: "target", 2: "partial+rest", -1: "stop", 0: "time"}.get(k, str(k)): v
                         for k, v in reasons.items()},
        "by_instrument": _group_stats(r, tr.t, tr.symbol.astype(str)),
        "by_year": _group_stats(r, tr.t, tr.years()),
        "by_session": _group_stats(r, tr.t, session_of(tr.t)),
    }
    if all(c in tr.context for c in REGIME_CONTEXT):
        out["by_regime"] = _group_stats(r, tr.t, regime_labels(tr))
    return out


def regime_labels(tr: Trades) -> np.ndarray:
    e, v = tr.context[REGIME_CONTEXT[0]], tr.context[REGIME_CONTEXT[1]]
    name = {0: "low", 2: "high"}
    return np.array([f"er_{name.get(int(a), 'na')}|vol_{name.get(int(b), 'na')}" for a, b in zip(e, v)], dtype=object)


def regime_binnings(values: dict[str, dict[str, np.ndarray]]) -> dict[str, Binning]:
    """Median splits of er120 and vol_ratio per symbol, from the DISCOVERY rows (bins 0 / 2)."""
    out = {}
    for name, feat in zip(REGIME_CONTEXT, ("er120", "vol_ratio")):
        edges = {}
        for sym, x in values[feat].items():
            x = np.asarray(x, float)
            x = x[np.isfinite(x)]
            if len(x) >= 30:
                m = float(np.median(x))
                edges[sym] = (m, m)
        out[name] = Binning(feat, edges)
    return out


def _seed(rules: BatteryRules, key: str) -> int:
    return rules.seed + int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def run_battery(study: Study, cond, side: int, exit_key: str, rules: BatteryRules, *,
                perturbed: list[dict[str, Binning]] = (), kind: str = "opportunity", trials: int = 1,
                key: str = "") -> dict:
    """`cond` is a Condition (bins), or any signal with `.key`, `.masks(study)` and
    `.perturbed_masks(study)` (e.g. a model score above a frozen threshold)."""
    sign = -1.0 if kind == "veto" else 1.0
    rng = np.random.default_rng(_seed(rules, key or f"{cond.key}|{side}|{exit_key}"))
    if isinstance(cond, Condition):
        masks = study.masks(cond)
        pert_masks = [study.masks(cond, pb) for pb in perturbed]
    else:
        masks = cond.masks(study)
        pert_masks = cond.perturbed_masks(study)
    main = study.trades(masks, exit_key, side, context=REGIME_CONTEXT if all(
        c in study.context_binnings for c in REGIME_CONTEXT) else ())
    r = sign * main.r
    st = cluster_t(r, week_of(main.t))
    checks: dict[str, dict] = {}

    def check(name, ok, **data):
        checks[name] = {"pass": bool(ok), **{k: v for k, v in data.items()}}

    check("min_trades", main.n >= rules.min_trades, n=main.n)
    check("significance", st["t"] is not None and st["t"] >= rules.t_threshold, t=_r(st["t"], 3),
          threshold=round(rules.t_threshold, 3), mean_R=_r(st["mean"]), se=_r(st["se"]))

    # random entries: same exit, instruments and trade count per instrument
    counts = {s: int((main.symbol == s).sum()) for s in study.symbols}
    rand = []
    for _ in range(rules.random_draws):
        rt = study.trades(study.random_masks(counts, rng), exit_key, side)
        rand.append(sign * rt.r)
    rand_r = np.concatenate(rand) if rand else np.zeros(0)
    wt = welch_t(r, rand_r)
    check("beats_random", wt is not None and wt >= rules.random_welch_t, welch_t=_r(wt, 3),
          random_mean_R=_r(rand_r.mean() if len(rand_r) else None), random_n=int(len(rand_r)))

    # circular shifts of the condition in time, outcomes left where they are
    obs = float(r.mean()) if main.n else -np.inf
    perm = []
    for _ in range(rules.permutations):
        shifted = {}
        for s, m in masks.items():
            k = int(rng.integers(max(1, len(m) // 10), max(2, 9 * len(m) // 10))) if len(m) > 2 else 0
            shifted[s] = np.roll(m, k)
        pt = study.trades(shifted, exit_key, side)
        perm.append(float((sign * pt.r).mean()) if pt.n else -np.inf)
    perm = np.asarray(perm)
    p = (1 + int(np.sum(perm >= obs))) / (1 + len(perm))
    check("permutation", main.n > 0 and p < rules.permutation_alpha, p=round(p, 4),
          shifted_mean_R=_r(float(np.mean(perm[np.isfinite(perm)])) if np.isfinite(perm).any() else None))

    for stress in ("costs", "delay"):
        s_tr = study.trades(masks, exit_key, side, stress=stress)
        m = float((sign * s_tr.r).mean()) if s_tr.n else None
        check(f"{stress}_stress", m is not None and m > 0, mean_R=_r(m), n=s_tr.n)

    if pert_masks:
        means = []
        for pm in pert_masks:
            p_tr = study.trades(pm, exit_key, side)
            means.append(float((sign * p_tr.r).mean()) if p_tr.n else None)
        check("perturbation", all(m is not None and m > 0 for m in means), mean_R=[_r(m) for m in means])
    else:
        check("perturbation", True, note="not applicable: every term is a declared category")

    years = main.years()
    ys = {int(y): float(r[years == y].mean()) for y in np.unique(years) if (years == y).sum() >= rules.min_year_trades}
    share_y = (sum(v > 0 for v in ys.values()) / len(ys)) if ys else 0.0
    check("years", len(ys) >= 2 and share_y >= rules.year_share, share=round(share_y, 3),
          by_year={k: _r(v) for k, v in ys.items()})

    syms = main.symbol.astype(str)
    per = {s: float(r[syms == s].mean()) for s in study.symbols if (syms == s).sum() >= rules.min_instrument_trades}
    share_i = (sum(v > 0 for v in per.values()) / len(per)) if per else 0.0
    check("instruments", len(per) >= 2 and share_i >= rules.instrument_share, share=round(share_i, 3),
          positive=sorted(s for s, v in per.items() if v > 0), negative=sorted(s for s, v in per.items() if v <= 0))
    loo = {s: float(r[syms != s].mean()) for s in study.symbols if (syms == s).any() and (syms != s).any()}
    check("leave_one_out", bool(loo) and all(v > 0 for v in loo.values()),
          worst=min(loo, key=loo.get) if loo else None, worst_mean_R=_r(min(loo.values())) if loo else None)

    if REGIME_CONTEXT[0] in main.context:
        labels = regime_labels(main)
        cells = {}
        for lab in sorted(set(labels.tolist())):
            m = labels == lab
            if m.sum() >= rules.regime_min_trades:
                c = cluster_t(r[m], week_of(main.t[m]))
                cells[lab] = {"n": c["n"], "mean_R": _r(c["mean"]), "t": _r(c["t"], 3)}
        neg = [k for k, v in cells.items() if v["t"] is not None and v["t"] <= rules.regime_negative_t]
        pos = [k for k, v in cells.items() if (v["mean_R"] or 0) > 0]
        check("regimes", not neg and len(pos) >= rules.regime_positive_cells, cells=cells,
              significantly_negative=neg)
    else:
        check("regimes", False, note="no regime context was provided")

    total = float(r.sum())
    k = max(1, int(np.ceil(rules.top_share * main.n))) if main.n else 0
    top = float(np.sort(r)[::-1][:k].sum()) if k else 0.0
    check("outliers", total > 0 and top / total < rules.top_max_contribution,
          top_share_of_total=_r(top / total if total > 0 else None, 3), top_trades=k)

    failed = [k for k, v in checks.items() if not v["pass"]]
    return {"version": BATTERY_VERSION, "segment": study.segment.to_json(), "condition": cond.key,
            "side": "BUY" if side > 0 else "SELL", "exit": exit_key, "kind": kind,
            "verdict": "VALIDATED" if not failed else "REJECTED", "failed": failed, "checks": checks,
            "deflated_sharpe": {k: _r(v, 4) if isinstance(v, float) else v
                                for k, v in deflated_sharpe(r, trials).items()},
            "decomposition": decompose(main), "trades": main}


def _r(x, nd=5):
    if x is None:
        return None
    x = float(x)
    return None if not np.isfinite(x) else round(x, nd)
