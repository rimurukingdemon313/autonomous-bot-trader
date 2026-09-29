"""The statistics the discovery engine judges with — small, explicit, tested against known answers.

- `cluster_t`: mean R and its t-statistic with standard errors clustered by calendar week of
  entry. Trades on different pairs in the same week share the same dollar news and the same
  risk-on/off swings; treating them as independent would overstate every t-statistic.
- `bh`: Benjamini-Hochberg false-discovery-rate control for the screening stage.
- `deflated_sharpe`: the probability that the Sharpe ratio exceeds what the best of N unskilled
  trials would show (Bailey & Lopez de Prado, 2014). Reported, not used as a gate.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

WEEK = 7 * 86400
_MONDAY = 4 * 86400  # 1970-01-05 00:00 UTC was a Monday
_N = NormalDist()


def week_of(t: np.ndarray) -> np.ndarray:
    return (np.asarray(t, np.int64) - _MONDAY) // WEEK


def cluster_t(r: np.ndarray, clusters: np.ndarray) -> dict:
    """Mean, clustered standard error (CR1) and t; None where it cannot be computed."""
    r = np.asarray(r, float)
    n = len(r)
    if n < 2:
        return {"n": n, "mean": float(r.mean()) if n else None, "se": None, "t": None, "clusters": n}
    mean = float(r.mean())
    _, g = np.unique(np.asarray(clusters), return_inverse=True)
    G = int(g.max()) + 1
    sums = np.bincount(g, weights=r - mean, minlength=G)
    if G < 2:
        return {"n": n, "mean": mean, "se": None, "t": None, "clusters": G}
    var = (G / (G - 1)) * float(np.sum(sums ** 2)) / n ** 2
    se = math.sqrt(var) if var > 0 else None
    if se is not None and se < 1e-12 * max(1.0, abs(mean)):
        se = None  # identical outcomes: floating-point noise, not a standard error
    return {"n": n, "mean": mean, "se": se, "t": (mean / se) if se else None, "clusters": G}


def p_one_sided(t: float | None) -> float:
    """P(T >= t) under the null of zero mean, normal approximation; 1.0 when t is unknown."""
    return 1.0 if t is None else 1.0 - _N.cdf(t)


def bh(pvalues: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    """(rejected, q-values) under Benjamini-Hochberg at level q over ALL the p-values given."""
    p = np.asarray(pvalues, float)
    m = len(p)
    if m == 0:
        return np.zeros(0, bool), np.zeros(0)
    order = np.argsort(p, kind="stable")
    ranked = p[order] * m / np.arange(1, m + 1)
    qv_sorted = np.minimum.accumulate(ranked[::-1])[::-1]
    qv = np.empty(m)
    qv[order] = np.minimum(qv_sorted, 1.0)
    passing = np.flatnonzero(p[order] <= q * np.arange(1, m + 1) / m)
    rejected = np.zeros(m, bool)
    if len(passing):
        rejected[order[: passing.max() + 1]] = True
    return rejected, qv


def welch_t(a: np.ndarray, b: np.ndarray) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return None
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else None


def deflated_sharpe(r: np.ndarray, trials: int) -> dict:
    """Per-trade Sharpe, the Sharpe the best of `trials` null strategies would reach by luck, and
    the probability that the observed one is above it given its sample length, skew and kurtosis."""
    r = np.asarray(r, float)
    n = len(r)
    if n < 3 or trials < 1 or r.std(ddof=1) == 0:
        return {"sharpe": None, "expected_max_null": None, "dsr": None, "trials": trials}
    sd = r.std(ddof=1)
    sr = float(r.mean() / sd)
    z = (r - r.mean()) / sd
    skew, kurt = float(np.mean(z ** 3)), float(np.mean(z ** 4))
    gamma = 0.5772156649
    if trials > 1:
        e_max = math.sqrt(1.0 / n) * ((1 - gamma) * _N.inv_cdf(1 - 1.0 / trials)
                                     + gamma * _N.inv_cdf(1 - 1.0 / (trials * math.e)))
    else:
        e_max = 0.0
    den = 1 - skew * sr + (kurt - 1) / 4 * sr ** 2
    dsr = _N.cdf((sr - e_max) * math.sqrt(n - 1) / math.sqrt(den)) if den > 0 else None
    return {"sharpe": sr, "expected_max_null": e_max, "dsr": dsr, "trials": trials}
