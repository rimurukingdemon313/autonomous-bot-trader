"""Rules as data: a spec (plain JSON) -> a position at every row, its net P&L, and a proof that it is causal.

A spec carries everything needed to recompute the rule on data it has never seen: no parameter is refitted. Kinds:

    tree      a condition, or two joined by and/or, on trailing ranks of features; held `hold` rows; one side
    sign      the sign of a feature's trailing z-score beyond a band (lead-lag, momentum, reversal)
    table     a position for each cell of one or two features' trailing-rank bins (non-linear dependence)
    ordinal   a position for each ordering of the instrument's last m returns (ordinal pattern)
    regime    a position for each cluster; a row belongs to the nearest frozen centroid of its z-scored state
    anomaly   after a row whose multivariate shock exceeds a frozen threshold: continue, reverse, long or short
    level     a raw feature above or below a fixed level (used to state earlier, closed families exactly)
    const     always one side (the instrument's own return: the baseline, never a discovery)
    combo     several rules on one instrument: all agree (and), or the majority (vote)
    book      several rules, equal capital each: the pooled test of one mechanism across instruments

A position decided at row t's close earns the instrument's return to its next priced row, less costs: the one-way
cost on every change of position, and the holding cost of that interval (a roll). A row where the instrument has no
price holds no decision: the position is whatever it was.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math

import numpy as np

from .panel import Panel, feat, key, log_ret, rank, roll_mean_std, zscore

KINDS: dict = {}


def spec_id(spec: dict) -> str:
    return hashlib.sha256(key(spec).encode()).hexdigest()[:16]


def _b(x: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(x), x, 0.0)


def held(b: np.ndarray, h: int) -> np.ndarray:
    """True at row t if b was true at any of the last h rows (t included)."""
    if h <= 1:
        return b.astype(bool)
    c = np.cumsum(b.astype(int))
    prev = np.concatenate([np.zeros(h, dtype=int), c[:-h]]) if h < len(c) else np.zeros(len(c), dtype=int)
    return (c - prev) > 0


def cond(p: Panel, c: dict) -> np.ndarray:
    r = rank(p, c["feat"], c["w"])
    with np.errstate(invalid="ignore"):
        out = (r > c["q"]) if c["op"] == ">" else (r < c["q"])
    return out & np.isfinite(r)


def node(p: Panel, n: dict) -> np.ndarray:
    if "and" in n:
        return node(p, n["and"][0]) & node(p, n["and"][1])
    if "or" in n:
        return node(p, n["or"][0]) | node(p, n["or"][1])
    return cond(p, n)


def leaves(n: dict) -> int:
    return sum(leaves(x) for x in n.get("and", n.get("or", []))) if ("and" in n or "or" in n) else 1


def _tree(p, s):
    return s["side"] * held(node(p, s["node"]), s.get("hold", 1)).astype(float)


def _sign(p, s):
    z = zscore(p, s["feat"], s["w"])
    with np.errstate(invalid="ignore"):
        return _b(s["side"] * np.sign(z) * (np.abs(z) > s["band"]))


def _bins(p, s) -> np.ndarray:
    """The cell of each row: -1 where any feature's rank is unknown."""
    idx, ok = np.zeros(p.T, dtype=int), np.ones(p.T, dtype=bool)
    for f, e in zip(s["feats"], s["edges"]):
        r = rank(p, f, s["w"])
        ok &= np.isfinite(r)
        idx = idx * (len(e) + 1) + np.searchsorted(np.asarray(e), _b(r), side="left")
    return np.where(ok, idx, -1)


def _table(p, s):
    cell = _bins(p, s)
    m = np.asarray(s["map"], dtype=float)
    return np.where(cell >= 0, m[np.maximum(cell, 0)], 0.0)


def ordinal_code(p: Panel, a: str, k: int, m: int) -> np.ndarray:
    """The ordering of the last m non-overlapping k-row returns of `a`, as an index in 0..m!-1; -1 where unknown."""
    seg = feat(p, {"f": "ret", "a": a, "k": k})
    cols = [np.concatenate([np.full(j * k, np.nan), seg[:p.T - j * k]]) if j else seg for j in range(m - 1, -1, -1)]
    x = np.column_stack(cols)
    ok = np.isfinite(x).all(axis=1)
    order = np.argsort(np.where(ok[:, None], x, 0.0), axis=1, kind="stable")
    code = np.zeros(p.T, dtype=int)
    for i in range(m):
        code = code * m + order[:, i]
    perms = {sum(v * m ** (m - 1 - i) for i, v in enumerate(pm)): n for n, pm in enumerate(itertools.permutations(range(m)))}
    lut = np.full(m ** m, -1)
    for c, n in perms.items():
        lut[c] = n
    return np.where(ok, lut[code], -1)


def _ordinal(p, s):
    code = ordinal_code(p, s["a"], s["k"], s["m"])
    m = np.asarray(s["map"], dtype=float)
    return np.where(code >= 0, m[np.maximum(code, 0)], 0.0)


def regime_state(p: Panel, feats: list, w: int) -> np.ndarray:
    return np.column_stack([np.clip(zscore(p, f, w), -4.0, 4.0) for f in feats])


def _regime(p, s):
    x = regime_state(p, s["feats"], s["w"])
    ok = np.isfinite(x).all(axis=1)
    c = np.asarray(s["centroids"], dtype=float)
    d = ((np.where(ok[:, None], x, 0.0)[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
    return np.where(ok, np.asarray(s["map"], dtype=float)[np.argmin(d, axis=1)], 0.0)


def shock(p: Panel, vol_k: int) -> np.ndarray:
    """Each instrument's last log return in units of its own trailing volatility: [T, N]."""
    lr = log_ret(p)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.column_stack([lr[:, j] / roll_mean_std(lr[:, j], vol_k, vol_k // 2)[1] for j in range(len(p.assets))])


def shock_d2(p: Panel, s: dict) -> np.ndarray:
    x = shock(p, s["vol_k"])
    ok = np.isfinite(x).all(axis=1)
    d = np.where(ok[:, None], x, 0.0) - np.asarray(s["mu"], dtype=float)
    return np.where(ok, np.einsum("ti,ij,tj->t", d, np.asarray(s["prec"], dtype=float), d), np.nan)


def _anomaly(p, s):
    d2 = shock_d2(p, s)
    with np.errstate(invalid="ignore"):
        ev = d2 > s["thr"]
    own = np.sign(_b(log_ret(p)[:, p.col(s["target"])]))
    direction = {"cont": own, "rev": -own, "long": np.ones(p.T), "short": -np.ones(p.T)}[s["mode"]] * ev
    pos = np.zeros(p.T)
    for j in range(s.get("hold", 1) - 1, -1, -1):  # the latest event's direction wins
        d = np.concatenate([np.zeros(j), direction[:p.T - j]]) if j else direction
        pos = np.where(d != 0, d, pos)
    return pos


def _level(p, s):
    x = feat(p, s["feat"])
    with np.errstate(invalid="ignore"):
        return _b(s["side"] * ((x > s["x"]) if s["op"] == ">" else (x < s["x"])))


def _combo(p, s):
    parts = np.column_stack([positions(x, p) for x in s["parts"]])
    if s["op"] == "and":
        return np.where((parts > 0).all(axis=1), 1.0, np.where((parts < 0).all(axis=1), -1.0, 0.0))
    return np.sign(parts.sum(axis=1))


KINDS.update({"tree": _tree, "sign": _sign, "table": _table, "ordinal": _ordinal, "regime": _regime,
              "anomaly": _anomaly, "level": _level, "const": lambda p, s: np.full(p.T, float(s["side"])),
              "combo": _combo})


def positions(spec: dict, p: Panel) -> np.ndarray:
    """The rule's position after each row's close, in {-1, 0, +1}; 0 where it cannot be known."""
    k_ = "pos:" + key(spec)
    if k_ not in p.cache:
        p.cache[k_] = np.asarray(KINDS[spec["kind"]](p, spec), dtype=float)
    return p.cache[k_]


def parts_of(spec: dict) -> list[dict]:
    return spec["parts"] if spec["kind"] == "book" else [spec]


def targets(spec: dict) -> tuple:
    return tuple(sorted({x["target"] for x in parts_of(spec)}))


def pnl(spec: dict, p: Panel, k: float = 1.0, delay: int = 0) -> dict:
    """The rule's net and gross return at every row ([T], NaN where no decision could be made) and its position.
    `k` scales every cost; `delay` enters that many of the instrument's priced rows late."""
    if spec["kind"] == "book":
        each = [pnl(x, p, k, delay) for x in spec["parts"]]
        any_row = np.any([np.isfinite(e["net"]) for e in each], axis=0)
        out = {f: np.where(any_row, np.mean([_b(e[f]) for e in each], axis=0), np.nan) for f in ("net", "gross")}
        out["pos"] = np.mean([np.abs(_b(e["pos"])) for e in each], axis=0)
        return out
    j = p.col(spec["target"])
    fwd = p.fwd()[:, j]
    rows = np.nonzero(np.isfinite(fwd))[0]
    pos = positions(spec, p)[rows]
    if delay:
        pos = np.concatenate([np.zeros(delay), pos[:-delay]]) if delay < len(pos) else np.zeros(len(pos))
    gross = pos * fwd[rows]
    turn = np.abs(pos - np.concatenate([[0.0], pos[:-1]]))
    cost = k * (p.cost[spec["target"]] * turn + p.hold_cost[rows, j] * np.abs(pos))
    out = {f: np.full(p.T, np.nan) for f in ("net", "gross", "pos")}
    out["net"][rows], out["gross"][rows], out["pos"][rows] = gross - cost, gross, pos
    return out


def stats(x: np.ndarray, mask: np.ndarray, ppy: float, pos: np.ndarray | None = None) -> dict:
    """The mean, t and Sharpe ratio of a return series on the rows of `mask` where it is defined."""
    v = x[mask & np.isfinite(x)]
    n = len(v)
    out = {"n": n, "mean": None, "t": None, "sharpe": None}
    if n >= 20:
        mean, sd = float(v.mean()), float(v.std(ddof=1))
        out["mean"] = mean
        if sd > 0:
            out["t"], out["sharpe"] = mean / sd * math.sqrt(n), mean / sd * math.sqrt(ppy)
    if pos is not None:
        q = _b(pos[mask & np.isfinite(x)])
        out["exposure"] = float(np.mean(np.abs(q))) if n else 0.0
        out["in_position"] = int((q != 0).sum())
        out["entries"] = int(((q != 0) & (np.concatenate([[0.0], q[:-1]]) != q)).sum())
    return out


def causal(spec: dict, p: Panel, points: int = 5, seed: int = 0) -> bool:
    """True if the position at a row is the same whether or not the later rows exist: recomputed on the panel cut at
    that row, at `points` rows spread over the panel's second half and at its last row."""
    full = [positions(x, p) for x in parts_of(spec)]
    rng = np.random.default_rng(seed)
    cuts = sorted(set(rng.integers(p.T // 2, p.T - 1, size=points).tolist()) | {p.T - 1})
    for t in cuts:
        cut = p.head(t + 1)
        for x, f in zip(parts_of(spec), full):
            if positions(x, cut)[t] != f[t]:
                return False
    return True


def nw_t(x: np.ndarray, lags: int) -> float | None:
    """The mean's t with a Newey-West standard error (Bartlett weights): robust to the autocorrelation that
    multi-row positions put into a return series."""
    v = x[np.isfinite(x)]
    n = len(v)
    if n < 30:
        return None
    e = v - v.mean()
    s = float(e @ e) / n
    for lag in range(1, lags + 1):
        s += 2.0 * (1.0 - lag / (lags + 1.0)) * float(e[lag:] @ e[:-lag]) / n
    return None if s <= 0 else float(v.mean() / math.sqrt(s / n))


def describe(spec: dict) -> str:
    """One line a person can read."""
    def f_(f):
        return f["f"] + "(" + ",".join(str(v) for k_, v in f.items() if k_ != "f") + ")"

    def n_(n):
        if "and" in n or "or" in n:
            op = "and" if "and" in n else "or"
            return "(" + f" {op} ".join(n_(x) for x in n[op]) + ")"
        return f"rank{n['w']}[{f_(n['feat'])}] {n['op']} {n['q']}"
    side = {1: "long", -1: "short"}
    k = spec["kind"]
    if k == "book":
        return "book of " + str(len(spec["parts"])) + ": " + "; ".join(describe(x) for x in spec["parts"])[:400]
    t = spec["target"]
    if k == "tree":
        return f"{side[spec['side']]} {t} for {spec.get('hold', 1)} rows while {n_(spec['node'])}"
    if k == "sign":
        d = "with" if spec["side"] > 0 else "against"
        return f"{t}: {d} the sign of z{spec['w']}[{f_(spec['feat'])}] beyond {spec['band']}"
    if k == "table":
        return f"{t}: by the rank bins of " + " x ".join(f_(f) for f in spec["feats"]) + f", map {spec['map']}"
    if k == "ordinal":
        return f"{t}: by the ordering of {spec['a']}'s last {spec['m']} {spec['k']}-row returns, map {spec['map']}"
    if k == "regime":
        return f"{t}: by {len(spec['centroids'])} regimes of {len(spec['feats'])} state features, map {spec['map']}"
    if k == "anomaly":
        return (f"{t}: {spec['mode']} for {spec.get('hold', 1)} rows after a multivariate shock beyond "
                f"{spec['thr']:.1f}")
    if k == "level":
        return f"{side[spec['side']]} {t} while {f_(spec['feat'])} {spec['op']} {spec['x']}"
    if k == "const":
        return f"always {side[spec['side']]} {t}"
    if k == "combo":
        return f"{t}: {spec['op']} of " + " | ".join(describe(x) for x in spec["parts"])[:400]
    return f"{t}: a rule of kind {k}"


def dumps(spec: dict) -> str:
    return json.dumps(spec, sort_keys=True)


__all__ = ["KINDS", "causal", "cond", "describe", "dumps", "held", "leaves", "node", "nw_t", "ordinal_code",
           "parts_of", "pnl", "positions", "regime_state", "shock", "shock_d2", "spec_id", "stats", "targets"]
