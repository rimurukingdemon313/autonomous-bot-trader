"""Feature discovery inside a DECLARED grammar, with the same leakage gate as production.

A candidate feature is an expression over the production feature matrix
(itself causal): `diff(col, k)`, `zscore(col, w)`, `rank(col, w)`,
`ratio(a, b)` or `product(a, b)`. The grammar and its parameter grid are
finite, so `enumerate_candidates` returns a countable list, and the count
is what the registry charges when candidates are tested (RESEARCH_CONTRACT
§5: autonomous search runs inside a declared space and budget).

Every candidate must pass `truncation_violations`, the same check every
production feature passes: its value at bar i, computed on the full
history, must equal its value computed on history truncated at i. A
candidate that fails is REJECTED before any evaluation, whatever it might
have predicted: a leaky feature always "predicts".

Passing the gate makes a candidate *eligible*, nothing more. Whether it
adds information is an experiment judged out of sample by the lab
(aitrader/research/lab.py), counted in the registry. An accepted feature
reaches production only by being added to the feature store under a new
FEATURE_VERSION, a reviewed code change, never automatically.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from itertools import combinations
from typing import Callable

import numpy as np

from ..data.bars import BarSeries
from ..features.store import INDEX, NAMES, compute_matrix

FEATURE_LAB_VERSION = "feature-lab-1.0.0"

#: The declared grammar: operator -> parameter grid. Changing it widens the
#: search space, which is itself a registered change.
GRAMMAR = {
    "diff": (1, 6, 24),
    "zscore": (24, 120),
    "rank": (24, 120),
    "ratio": None,
    "product": None,
}


def _lagged(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full_like(x, np.nan)
    if k < len(x):
        out[k:] = x[:-k] if k else x
    return out


def _rolling(x: np.ndarray, w: int, fn) -> np.ndarray:
    out = np.full_like(x, np.nan)
    for i in range(w - 1, len(x)):
        win = x[i - w + 1: i + 1]
        if np.all(np.isfinite(win)):
            out[i] = fn(win, x[i])
    return out


def _zscore(win, last):
    s = win.std()
    return (last - win.mean()) / s if s > 0 else np.nan


def _rank(win, last):
    return float((win <= last).mean())


@dataclass(frozen=True)
class CandidateFeature:
    expression: str
    fn: Callable[[np.ndarray], np.ndarray]  # production feature matrix -> column

    @property
    def version(self) -> str:
        return "cand-" + hashlib.sha256(f"{FEATURE_LAB_VERSION}|{self.expression}".encode()).hexdigest()[:12]

    def column(self, matrix: np.ndarray) -> np.ndarray:
        return self.fn(matrix)


def candidate(expression: str) -> CandidateFeature:
    """Parse one grammar expression, e.g. 'zscore(r24,120)' or 'ratio(vol_ratio,rv_ratio)'."""
    op, _, rest = expression.partition("(")
    args = [a.strip() for a in rest.rstrip(")").split(",")]
    if op not in GRAMMAR:
        raise ValueError(f"{op!r} is not in the declared grammar {sorted(GRAMMAR)}")
    grid = GRAMMAR[op]
    if grid is None:
        a, b = args
        for c in (a, b):
            if c not in INDEX:
                raise ValueError(f"unknown column {c!r}")
        ia, ib = INDEX[a], INDEX[b]
        if op == "ratio":
            def fn(m, ia=ia, ib=ib):
                with np.errstate(divide="ignore", invalid="ignore"):
                    return np.where(m[:, ib] != 0, m[:, ia] / m[:, ib], np.nan)
        else:
            def fn(m, ia=ia, ib=ib):
                return m[:, ia] * m[:, ib]
    else:
        col, p = args[0], int(args[1])
        if col not in INDEX:
            raise ValueError(f"unknown column {col!r}")
        if p not in grid:
            raise ValueError(f"{op} parameter {p} is outside the declared grid {grid}")
        ic = INDEX[col]
        if op == "diff":
            def fn(m, ic=ic, p=p):
                return m[:, ic] - _lagged(m[:, ic], p)
        elif op == "zscore":
            def fn(m, ic=ic, p=p):
                return _rolling(m[:, ic], p, _zscore)
        else:
            def fn(m, ic=ic, p=p):
                return _rolling(m[:, ic], p, _rank)
    return CandidateFeature(expression, fn)


def enumerate_candidates(columns: tuple[str, ...] | None = None) -> list[str]:
    """Every expression the grammar allows over `columns`: a finite, countable space."""
    cols = tuple(columns or NAMES)
    out = []
    for op, grid in GRAMMAR.items():
        if grid is None:
            out += [f"{op}({a},{b})" for a, b in combinations(cols, 2)]
        else:
            out += [f"{op}({c},{p})" for c in cols for p in grid]
    return out


def truncation_violations(fn: Callable[[BarSeries], np.ndarray], series: BarSeries, rows) -> list[int]:
    """Rows where fn(full history)[i] differs from fn(history up to i)[i]. Empty = causal on these rows."""
    full = np.asarray(fn(series), float)
    bad = []
    for i in rows:
        part = np.asarray(fn(series.take(slice(0, i + 1))), float)
        a, b = full[i], part[i]
        same = (np.isnan(a) and np.isnan(b)) or a == b or abs(a - b) <= 1e-9 * max(1.0, abs(a))
        if not same:
            bad.append(int(i))
    return bad


def leakage_gate(cand: CandidateFeature, series: BarSeries, n_rows: int = 25) -> dict:
    """ELIGIBLE only if the candidate is causal on sampled rows of a real series; otherwise REJECTED."""
    n = len(series)
    rows = sorted(set(np.linspace(300, n - 1, n_rows).astype(int).tolist()))
    bad = truncation_violations(lambda s: cand.column(compute_matrix(s)), series, rows)
    return {"expression": cand.expression, "version": cand.version,
            "status": "ELIGIBLE" if not bad else "REJECTED_LEAKAGE", "violations": bad[:10],
            "rows_checked": len(rows)}
