"""The discovery lab's panel: several instruments on one time grid, and causal features of it.

A `Panel` holds, for T rows (days or hours) and N instruments:

- `ret[t, a]`: the simple return of the tradable instrument realized AT row t, from its previous priced row. NaN when
  the instrument has no price at row t. A missing price is never filled.
- `aux[name][t]`: any other state series known at row t's close (a curve's slope, open interest). NaN when unknown.
- `cost[a]`: the one-way cost of a trade, a fraction of notional.
- `hold_cost[t, a]`: an extra one-way cost of HOLDING over the interval that starts at row t (a futures roll).

Every feature here is causal: its value at row t is computed from rows <= t only. `signals.causal` proves that for each
rule by truncation, and the tests prove it for each feature.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


@dataclass
class Panel:
    name: str
    times: list
    assets: tuple
    ret: np.ndarray
    aux: dict
    cost: dict
    ppy: float
    hold_cost: np.ndarray | None = None
    cache: dict = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.ret = np.asarray(self.ret, dtype=float)
        if self.ret.shape != (len(self.times), len(self.assets)):
            raise ValueError(f"ret is {self.ret.shape}, expected {(len(self.times), len(self.assets))}")
        if any(self.times[i] >= self.times[i + 1] for i in range(len(self.times) - 1)):
            raise ValueError("the panel's times must be strictly increasing")
        if self.hold_cost is None:
            self.hold_cost = np.zeros_like(self.ret)
        for k, v in self.aux.items():
            if len(v) != len(self.times):
                raise ValueError(f"aux {k} has {len(v)} rows, expected {len(self.times)}")

    @property
    def T(self) -> int:
        return len(self.times)

    def col(self, asset: str) -> int:
        return self.assets.index(asset)

    def fwd(self) -> np.ndarray:
        """fwd[t, a]: the return from row t to the instrument's NEXT priced row, for rows where it is priced; NaN
        elsewhere. This is what a position decided at row t's close earns."""
        if "fwd" not in self.cache:
            out = np.full_like(self.ret, np.nan)
            for j in range(len(self.assets)):
                rows = np.nonzero(np.isfinite(self.ret[:, j]))[0]
                if len(rows) > 1:
                    out[rows[:-1], j] = self.ret[rows[1:], j]
            self.cache["fwd"] = out
        return self.cache["fwd"]

    def head(self, n: int) -> "Panel":
        """The first n rows only: what was known at row n - 1's close."""
        return Panel(self.name, self.times[:n], self.assets, self.ret[:n].copy(),
                     {k: np.asarray(v)[:n].copy() for k, v in self.aux.items()}, dict(self.cost), self.ppy,
                     self.hold_cost[:n].copy())

    def rows(self, start, end) -> np.ndarray:
        """A boolean mask of the rows whose time is in [start, end)."""
        return np.array([start <= t < end for t in self.times], dtype=bool)


# ── trailing arithmetic: row t reads rows <= t only ─────────────────────────

def _shift(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[:len(x) - k]
    return out


def roll_sum(x: np.ndarray, k: int) -> np.ndarray:
    """The sum of the last k rows (a missing row adds nothing). NaN where row t itself is missing, or before k rows."""
    ok = np.isfinite(x)
    c = np.cumsum(np.where(ok, x, 0.0))
    out = c.copy()
    out[k:] = c[k:] - c[:-k]
    out[:k - 1] = np.nan
    out[~ok] = np.nan
    return out


def _roll_moments(x: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ok = np.isfinite(x)
    z = np.where(ok, x, 0.0)
    n, s, q = np.cumsum(ok.astype(float)), np.cumsum(z), np.cumsum(z * z)
    for a in (n, s, q):
        a[k:] = a[k:] - a[:-k].copy()
    return n, s, q


def roll_mean_std(x: np.ndarray, k: int, min_n: int) -> tuple[np.ndarray, np.ndarray]:
    """The mean and the standard deviation of the valid values among the last k rows; NaN with fewer than min_n."""
    n, s, q = _roll_moments(x, k)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = s / n
        var = (q - n * mean * mean) / (n - 1)
    bad = n < max(min_n, 2)
    mean[bad], var[bad] = np.nan, np.nan
    return mean, np.sqrt(np.where(var > 0, var, np.nan))


def roll_z(x: np.ndarray, w: int, min_n: int | None = None) -> np.ndarray:
    """(x[t] - mean) / sd over the last w rows, row t included."""
    mean, sd = roll_mean_std(x, w, min_n or w // 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (x - mean) / sd


def roll_rank(x: np.ndarray, w: int, min_n: int | None = None) -> np.ndarray:
    """The share of the valid values among the last w rows (row t included) that are <= x[t]: in (0, 1]."""
    min_n = min_n or w // 2
    pad = np.concatenate([np.full(w - 1, np.nan), x])
    win = sliding_window_view(pad, w)
    valid = np.isfinite(win)
    with np.errstate(invalid="ignore"):
        le = (win <= x[:, None]) & valid
    n = valid.sum(axis=1)
    out = le.sum(axis=1) / np.maximum(n, 1)
    out[(n < min_n) | ~np.isfinite(x)] = np.nan
    return out


# ── the feature vocabulary ──────────────────────────────────────────────────

def key(spec) -> str:
    return json.dumps(spec, sort_keys=True, separators=(",", ":"))


def log_ret(p: Panel) -> np.ndarray:
    if "lr" not in p.cache:
        with np.errstate(invalid="ignore", divide="ignore"):
            p.cache["lr"] = np.log1p(p.ret)
    return p.cache["lr"]


def feat(p: Panel, f: dict) -> np.ndarray:
    """One feature series, [T]. Kinds:

    - ret(a, k): the instrument's log return over the last k rows;
    - vol(a, k): the standard deviation of its last k one-row log returns;
    - volr(a, k, k2): vol(a, k) / vol(a, k2);
    - absret(a): the size of its last one-row log return;
    - spread(a, b, k): ret(a, k) - ret(b, k);
    - mkt(k): the mean of ret(., k) over the instruments priced at t;
    - disp(k): their standard deviation (at least two priced);
    - aux(name[, d]): a state series, or its change over d rows.
    """
    k_ = "f:" + key(f)
    if k_ in p.cache:
        return p.cache[k_]
    lr, kind = log_ret(p), f["f"]
    if kind == "ret":
        out = roll_sum(lr[:, p.col(f["a"])], f["k"])
    elif kind == "vol":
        out = roll_mean_std(lr[:, p.col(f["a"])], f["k"], max(5, f["k"] // 2))[1]
        out = np.where(np.isfinite(lr[:, p.col(f["a"])]), out, np.nan)
    elif kind == "volr":
        with np.errstate(invalid="ignore", divide="ignore"):
            out = feat(p, {"f": "vol", "a": f["a"], "k": f["k"]}) / feat(p, {"f": "vol", "a": f["a"], "k": f["k2"]})
    elif kind == "absret":
        out = np.abs(lr[:, p.col(f["a"])])
    elif kind == "spread":
        out = feat(p, {"f": "ret", "a": f["a"], "k": f["k"]}) - feat(p, {"f": "ret", "a": f["b"], "k": f["k"]})
    elif kind in ("mkt", "disp"):
        m = np.column_stack([feat(p, {"f": "ret", "a": a, "k": f["k"]}) for a in p.assets])
        n = np.isfinite(m).sum(axis=1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # a row with no instrument priced: NaN, set below
            out = np.nanmean(m, axis=1) if kind == "mkt" else np.nanstd(m, axis=1)
        out = np.where(n >= (1 if kind == "mkt" else 2), out, np.nan)
    elif kind == "aux":
        out = np.asarray(p.aux[f["name"]], dtype=float)
        if f.get("d"):
            out = out - _shift(out, f["d"])
    else:
        raise ValueError(f"unknown feature {kind!r}")
    p.cache[k_] = out
    return out


def rank(p: Panel, f: dict, w: int) -> np.ndarray:
    k_ = f"r{w}:" + key(f)
    if k_ not in p.cache:
        p.cache[k_] = roll_rank(feat(p, f), w)
    return p.cache[k_]


def zscore(p: Panel, f: dict, w: int) -> np.ndarray:
    k_ = f"z{w}:" + key(f)
    if k_ not in p.cache:
        p.cache[k_] = roll_z(feat(p, f), w)
    return p.cache[k_]


def library(p: Panel, short: tuple = (1, 5, 20), vol: tuple = (5, 60)) -> list[dict]:
    """The features every method may read: each instrument's returns over a few horizons, its volatility ratio and the
    size of its last move; every state series and its change; the market's mean move and its dispersion. No calendar
    feature: the calendar families are closed (docs/DISCOVERY_PROGRAM.md)."""
    out = []
    for a in p.assets:
        out += [{"f": "ret", "a": a, "k": k} for k in short]
        out += [{"f": "volr", "a": a, "k": vol[0], "k2": vol[1]}, {"f": "absret", "a": a}]
    for i, a in enumerate(p.assets):
        out += [{"f": "spread", "a": a, "b": b, "k": short[-1]} for b in p.assets[i + 1:]]
    for name in sorted(p.aux):
        out += [{"f": "aux", "name": name}, {"f": "aux", "name": name, "d": short[1]}]
    if len(p.assets) > 1:
        out += [{"f": "mkt", "k": short[1]}, {"f": "disp", "k": short[-1]}]
    return out


__all__ = ["Panel", "feat", "key", "library", "log_ret", "rank", "roll_mean_std", "roll_rank", "roll_sum", "roll_z",
           "zscore"]
