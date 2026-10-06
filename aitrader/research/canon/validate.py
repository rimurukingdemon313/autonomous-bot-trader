"""The validation battery for canonical-engine trades (VALIDATION_CONTRACT.md §5-7).

Every number is computed from `Trade` ledgers, deterministically: each random step takes an explicit
seed. Nothing here chooses a parameter. It measures, compares against placebos, and applies a
contract whose thresholds are fixed in a preregistration before any result exists.

The unit of inference is the **daily book**: on each New York trading date, the equal-weight mean net
of the trades entered that day. Trades in correlated instruments on the same day are not independent
observations, and the daily book does not pretend they are.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, timezone
from statistics import NormalDist
from typing import Callable, Iterable

import numpy as np

from .engine import NY, Trade

VALIDATE_VERSION = "canon-validate-1.0.0"
MIN_SAMPLE = 100  # below this many trades a statistic is labelled "insufficient"


def ny_date(epoch: int) -> date:
    return datetime.fromtimestamp(int(epoch), timezone.utc).astimezone(NY).date()


def tstat(x) -> float | None:
    x = np.asarray(x, float)
    if len(x) < 2:
        return None
    sd = x.std(ddof=1)
    return float(x.mean() / (sd / math.sqrt(len(x)))) if sd > 0 else None


def daily_book(trades: list[Trade], value: Callable[[Trade], float] = lambda x: x.net_bp
               ) -> tuple[list[date], np.ndarray]:
    by: dict[date, list[float]] = defaultdict(list)
    for x in trades:
        by[ny_date(x.entry_t)].append(value(x))
    days = sorted(by)
    return days, np.array([np.mean(by[d]) for d in days])


def max_drawdown(series) -> float:
    c = np.cumsum(np.asarray(series, float))
    if not len(c):
        return 0.0
    peak = np.maximum.accumulate(np.r_[0.0, c])[1:]
    return float(np.max(peak - c)) if len(c) else 0.0


def summary(trades: list[Trade]) -> dict:
    """The full ledger: gross, every cost component, net, uncertainty, shape, exposure."""
    n = len(trades)
    if not n:
        return {"trades": 0, "sample": "insufficient"}
    net = np.array([x.net_bp for x in trades])
    days, book = daily_book(trades)
    t_day = tstat(book)
    se = book.std(ddof=1) / math.sqrt(len(book)) if len(book) > 1 else float("nan")
    first, last = min(x.entry_t for x in trades), max(x.exit_t for x in trades)
    months = max((last - first) / (86400 * 30.4375), 1e-9)
    symbols = {x.symbol for x in trades}
    held = sum(x.exit_t - x.entry_t for x in trades)
    pos, neg = net[net > 0], net[net < 0]
    order = np.sort(net)[::-1]
    k1 = max(1, int(round(0.01 * n)))
    total = float(net.sum())
    comp = {k: round(float(np.mean([getattr(x, k) for x in trades])), 4)
            for k in ("gross_bp", "spread_bp", "slip_bp", "through_bp", "comm_bp", "fin_bp")}
    return {
        "trades": n, "days": len(days), "instruments": sorted(symbols),
        "sample": "insufficient" if n < MIN_SAMPLE else "adequate",
        "trades_per_month": round(n / months, 2),
        "exposure": round(held / ((last - first) * len(symbols)), 4) if last > first else None,
        **comp,
        "cost_bp": round(float(np.mean([x.cost_bp for x in trades])), 4),
        "net_bp": round(float(net.mean()), 4),
        "net_bp_ci95_day": [round(float(book.mean() - 1.96 * se), 4), round(float(book.mean() + 1.96 * se), 4)]
        if math.isfinite(se) else None,
        "t_day": round(t_day, 3) if t_day is not None else None,
        "win_rate": round(float((net > 0).mean()), 4),
        "avg_win_bp": round(float(pos.mean()), 3) if len(pos) else None,
        "avg_loss_bp": round(float(neg.mean()), 3) if len(neg) else None,
        "profit_factor": round(float(pos.sum() / -neg.sum()), 4) if len(neg) and neg.sum() < 0 else None,
        "median_bp": round(float(np.median(net)), 4),
        "worst_5pct_bp": round(float(np.percentile(net, 5)), 3),
        "max_drawdown_bp_daybook": round(max_drawdown(book), 2),
        "total_bp_daybook": round(float(book.sum()), 2),
        "net_bp_without_top_1pct": round(float(order[k1:].mean()), 4) if n > k1 else None,
        "net_bp_without_top_5": round(float(order[5:].mean()), 4) if n > 5 else None,
        "top5_share_of_total": round(float(order[:5].sum() / total), 4) if total > 0 else None,
        "exit_reasons": dict(sorted({r: sum(x.reason == r for x in trades) for r in {x.reason for x in trades}}
                                    .items())),
    }


def by_key(trades: list[Trade], key: Callable[[Trade], object]) -> dict:
    groups: dict = defaultdict(list)
    for x in trades:
        groups[key(x)].append(x)
    out = {}
    for k in sorted(groups, key=str):
        g = groups[k]
        _, book = daily_book(g)
        t = tstat(book)
        out[str(k)] = {"trades": len(g), "net_bp": round(float(np.mean([x.net_bp for x in g])), 4),
                       "gross_bp": round(float(np.mean([x.gross_bp for x in g])), 4),
                       "t_day": round(t, 3) if t is not None else None}
    return out


def welch_t(a, b) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return None
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    return float((a.mean() - b.mean()) / math.sqrt(va + vb)) if va + vb > 0 else None


def vs_placebo(real: list[Trade], placebos: list[list[Trade]]) -> dict:
    """Real net per trade against the pooled placebo trades (Welch t), and the real mean's rank among
    the placebo runs' means."""
    pooled = [x.net_bp for run in placebos for x in run]
    means = [float(np.mean([x.net_bp for x in run])) for run in placebos if run]
    rm = float(np.mean([x.net_bp for x in real])) if real else float("nan")
    t = welch_t([x.net_bp for x in real], pooled)
    return {"runs": len(placebos), "placebo_net_bp": round(float(np.mean(pooled)), 4) if pooled else None,
            "real_net_bp": round(rm, 4), "welch_t": round(t, 3) if t is not None else None,
            "share_of_runs_beaten": round(float(np.mean([rm > m for m in means])), 4) if means else None}


def permutation_sides(trades: list[Trade], n: int = 2000, seed: int = 0, block: int = 5) -> dict:
    """Does the chosen DIRECTION matter? Each trade's long-side mid move is kept; the sides are shuffled
    in blocks of `block` consecutive trades (keeping their serial structure). p = share of shuffles
    whose mean signed gross is at least the real one. Meaningless for single-direction strategies
    (returns None)."""
    if len({x.side for x in trades}) < 2 or len(trades) < 2 * block:
        return {"p": None, "reason": "one direction only, or too few trades"}
    move = np.array([x.side * x.gross_bp for x in trades])  # the long-side move
    sides = np.array([x.side for x in trades])
    obs = float(np.mean(sides * move))
    rng = np.random.default_rng(seed)
    blocks = [sides[i:i + block] for i in range(0, len(sides), block)]
    ge = 0
    for _ in range(n):
        perm = np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])[:len(move)]
        ge += float(np.mean(perm * move)) >= obs
    return {"observed_gross_bp": round(obs, 4), "p": round((ge + 1) / (n + 1), 4), "n": n, "block": block,
            "seed": seed}


def monte_carlo(trades: list[Trade], n: int = 5000, seed: int = 0, block: int = 10) -> dict:
    """Moving-block bootstrap of the daily book: the distribution of total net and of maximum drawdown
    over a sample of the same length."""
    _, book = daily_book(trades)
    m = len(book)
    if m < 2 * block:
        return {"sample": "insufficient"}
    rng = np.random.default_rng(seed)
    starts_max = m - block + 1
    tot, dd = np.empty(n), np.empty(n)
    nb = math.ceil(m / block)
    for i in range(n):
        idx = (rng.integers(0, starts_max, nb)[:, None] + np.arange(block)).ravel()[:m]
        s = book[idx]
        tot[i], dd[i] = s.sum(), max_drawdown(s)
    pct = lambda a, q: round(float(np.percentile(a, q)), 2)  # noqa: E731
    return {"n": n, "block_days": block, "seed": seed,
            "total_bp_p05_p50_p95": [pct(tot, 5), pct(tot, 50), pct(tot, 95)],
            "max_dd_bp_p50_p95": [pct(dd, 50), pct(dd, 95)],
            "prob_total_le_0": round(float((tot <= 0).mean()), 4)}


def windows(trades: list[Trade], edges: Iterable[tuple[str, str]]) -> dict:
    """Consecutive non-overlapping evaluation windows (the rule has nothing fitted, so walk-forward is
    the sequence of out-of-sample windows)."""
    out = {}
    for a, b in edges:
        lo, hi = date.fromisoformat(a), date.fromisoformat(b)
        g = [x for x in trades if lo <= ny_date(x.entry_t) < hi]
        s = summary(g)
        out[f"{a}..{b}"] = {k: s.get(k) for k in ("trades", "gross_bp", "cost_bp", "net_bp", "t_day")}
    nets = [v["net_bp"] for v in out.values() if v.get("trades")]
    return {"windows": out, "share_positive": round(float(np.mean([v > 0 for v in nets])), 4) if nets else None}


def halves(trades: list[Trade]) -> list[dict]:
    days = sorted({ny_date(x.entry_t) for x in trades})
    if len(days) < 2:
        return []
    mid = days[len(days) // 2]
    out = []
    for g in ([x for x in trades if ny_date(x.entry_t) < mid], [x for x in trades if ny_date(x.entry_t) >= mid]):
        s = summary(g)
        out.append({k: s.get(k) for k in ("trades", "net_bp", "t_day")})
    return out


def bonferroni_t(tests: int, alpha: float = 0.05) -> float:
    return NormalDist().inv_cdf(1 - alpha / (2 * tests))


__all__ = ["MIN_SAMPLE", "VALIDATE_VERSION", "bonferroni_t", "by_key", "daily_book", "halves", "max_drawdown",
           "monte_carlo", "ny_date", "permutation_sides", "summary", "tstat", "vs_placebo", "welch_t", "windows"]
