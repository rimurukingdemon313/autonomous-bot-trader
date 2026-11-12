"""Seven independent ways of looking for structure, each reading the FIT rows of a discovery panel and nothing else.

    leadlag    cross-asset lead-lag with a causal screen: the link must survive the follower's own past and the
               common factor (a partial correlation), and the reverse direction is measured beside it
    info       information theory: the mutual information between a feature's trailing-rank bin and the next return,
               given the instrument's own last move (a transfer-entropy analogue); pairs of features for synergy
    ordinal    mathematical patterns: does the ordering of the last few returns change the next one?
    regimes    unsupervised learning: k-means regimes of the market's state, then each instrument's drift by regime
    anomaly    anomaly detection: rows whose multivariate shock is extreme, then what follows them
    evolve     evolutionary search over small rule trees, with a penalty on size
    combine    rules of DIFFERENT families joined on one instrument, and one family pooled across instruments
    breadth    on a broad panel only: ONE rule traded on every instrument at once. A cross-sectional book (the top of
               a ranking against its bottom), the same sign rule on each instrument's own feature, and an evolutionary
               search over rule trees whose fitness is the pooled book's. Many instruments are what give a small
               effect a test it can pass (research/dlab/operating_characteristic.json)

No method requires significance. Each emits its strongest rules, oriented by the fit rows, and counts every statistic it
looked at (`scanned`), so the search's size is on the record. What an emitted rule is worth is decided later, on rows
no method has read (triage.py). A rule's cell is long or short by its deviation from the instrument's own mean on the
fit rows, so no method can emit "the market went up" as a discovery.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .panel import Panel, broad, key, library, rank, shared_aux, suffixes, tfeat, zscore
from .signals import held, node, ordinal_code, pnl, positions, regime_state, shock, shock_d2, stats, xs_book

MIN_ROWS = 250  # fit rows a statistic needs
FAMILIES = ("cross-asset lead-lag", "own-lag", "information (non-linear)", "ordinal pattern", "regime", "anomaly",
            "evolved rule", "combination", "pooled book", "cross-sectional", "pooled time-series")


@dataclass
class Emit:
    spec: dict
    family: str
    method: str
    fit: float  # the method's own statistic on the fit rows: comparable within a method only
    why: str
    detail: dict = field(default_factory=dict)


@dataclass
class Context:
    p: Panel  # discovery rows only
    fit: np.ndarray  # mask of the fit rows
    seed: int = 7
    w: int = 250  # the trailing window of every rank and z-score
    lags: tuple = (1, 2, 5, 10, 20)
    top: int = 24  # rules a method may emit
    tops: dict = field(default_factory=dict)  # a method's own limit, where the lab's record has set one (brain.py)
    scanned: dict = field(default_factory=dict)

    def cap(self, method: str) -> int:
        return int(self.tops.get(method, self.top))

    @property
    def targets(self) -> list[str]:
        f = self.p.fwd()
        return [a for j, a in enumerate(self.p.assets) if (self.fit & np.isfinite(f[:, j])).sum() >= 2 * MIN_ROWS]

    def y(self, a: str) -> np.ndarray:
        return self.p.fwd()[:, self.p.col(a)]

    def count(self, method: str, n: int) -> None:
        self.scanned[method] = self.scanned.get(method, 0) + int(n)


def _t_corr(x: np.ndarray, y: np.ndarray, controls: int = 0) -> float:
    n = len(x)
    if n < 30 or x.std() == 0 or y.std() == 0:
        return 0.0
    r = float(np.corrcoef(x, y)[0, 1])
    return r * math.sqrt(max(n - 2 - controls, 1) / max(1.0 - r * r, 1e-12))


def _resid(v: np.ndarray, c: np.ndarray) -> np.ndarray:
    a = np.column_stack([np.ones(len(v)), c])
    return v - a @ np.linalg.lstsq(a, v, rcond=None)[0]


def _f(f: dict) -> str:
    """A feature, or a template of one, as text: a template's "*" (each instrument's own) is left out."""
    vals = [(v[2:] if isinstance(v, str) and v.startswith("*.") else _f(v) if isinstance(v, dict) else str(v))
            for k_, v in f.items() if k_ != "f" and v != "*"]
    return f["f"] + "(" + ",".join(vals) + ")"


def _dev_map(y: np.ndarray, cell: np.ndarray, n_cells: int, t_min: float) -> tuple[list[float], float]:
    """A position for each cell from the fit rows: the sign of the cell's mean next return less the overall mean, where
    that deviation's t is at least t_min. Also the cells' chi-square, as a z-score."""
    mean, sd = y.mean(), y.std(ddof=1)
    out, chi, dof = [], 0.0, 0
    for c in range(n_cells):
        v = y[cell == c]
        if len(v) < 20 or sd == 0:
            out.append(0.0)
            continue
        t = (v.mean() - mean) / (sd / math.sqrt(len(v)))
        chi, dof = chi + t * t, dof + 1
        out.append(float(np.sign(t)) if abs(t) >= t_min else 0.0)
    return out, (chi - dof) / math.sqrt(2 * dof) if dof else 0.0


# ── 1. lead-lag, with a causal screen ───────────────────────────────────────

def leadlag(ctx: Context) -> list[Emit]:
    p, out = ctx.p, []
    for fo in ctx.targets:
        y = ctx.y(fo)
        for le in p.assets:
            for k in ctx.lags:
                x = zscore(p, {"f": "ret", "a": le, "k": k}, ctx.w)
                own = zscore(p, {"f": "ret", "a": fo, "k": k}, ctx.w)
                mk = zscore(p, {"f": "mkt", "k": k}, ctx.w)
                m = ctx.fit & np.isfinite(x) & np.isfinite(y) & np.isfinite(own) & np.isfinite(mk)
                if m.sum() < MIN_ROWS:
                    continue
                ctx.count("leadlag", 1)
                raw = _t_corr(x[m], y[m])
                if le == fo:
                    part, rev = raw, 0.0
                else:
                    c = np.column_stack([own[m], mk[m]])
                    part = _t_corr(_resid(x[m], c), _resid(y[m], c), controls=2)
                    yl = ctx.y(le)  # the reverse: does the follower's past move lead the leader's next return?
                    mr = ctx.fit & np.isfinite(own) & np.isfinite(yl)
                    rev = _t_corr(own[mr], yl[mr]) if mr.sum() >= MIN_ROWS else 0.0
                if part == 0.0:
                    continue
                side = 1 if part > 0 else -1
                spec = {"kind": "sign", "target": fo, "feat": {"f": "ret", "a": le, "k": k}, "w": ctx.w, "band": 0.5,
                        "side": side}
                verb = "is followed by a move the same way in" if side > 0 else "is followed by a reversal in"
                why = (f"{le}'s move over the last {k} rows {verb} {fo}'s next row" if le != fo else
                       f"{fo}'s own move over the last {k} rows {'continues' if side > 0 else 'reverses'} in its next row")
                out.append(Emit(spec, "own-lag" if le == fo else "cross-asset lead-lag", "leadlag", abs(part), why,
                                {"cause": le, "effect": fo, "lag_rows": k, "t_raw": round(raw, 3),
                                 "t_given_own_past_and_market": round(part, 3), "t_reverse_direction": round(rev, 3),
                                 "n": int(m.sum())}))
    out.sort(key=lambda e: -e.fit)
    own = [e for e in out if e.family == "own-lag"][:ctx.cap("leadlag") // 3]
    return [e for e in out if e.family != "own-lag"][:ctx.cap("leadlag")] + own


# ── 2. information theory ───────────────────────────────────────────────────

def mi(a: np.ndarray, b: np.ndarray, na: int, nb: int) -> float:
    """The mutual information of two discrete series, in nats, with the Miller-Madow bias correction."""
    c = np.bincount(a * nb + b, minlength=na * nb).reshape(na, nb).astype(float)
    n = c.sum()
    pa, pb, pab = c.sum(axis=1) / n, c.sum(axis=0) / n, c / n
    nz = pab > 0
    val = float((pab[nz] * np.log(pab[nz] / (pa[:, None] * pb[None, :])[nz])).sum())
    return val - ((nz.sum() - 1) - ((pa > 0).sum() - 1) - ((pb > 0).sum() - 1)) / (2.0 * n)


def cmi(a: np.ndarray, b: np.ndarray, o: np.ndarray, na: int, nb: int, no: int) -> float:
    """I(a; b | o): what a tells about b beyond what o already tells. With b the next return and o the instrument's own
    last move, this is a transfer-entropy analogue."""
    return float(sum((o == v).mean() * mi(a[o == v], b[o == v], na, nb) for v in range(no) if (o == v).sum() >= 30))


def shift_z(stat, a: np.ndarray, n_shifts: int, rng) -> tuple[float, float]:
    """A statistic of `a` against fixed other series, and its z-score against circular shifts of `a`: a shift keeps
    each series' own distribution and autocorrelation and breaks only the link between them."""
    real = stat(a)
    if len(a) < 2 * MIN_ROWS:
        return real, 0.0
    null = np.array([stat(np.roll(a, int(s))) for s in rng.integers(60, len(a) - 60, size=n_shifts)])
    sd = float(null.std(ddof=1))
    return real, (real - float(null.mean())) / sd if sd > 0 else 0.0


def _updown(v: np.ndarray) -> np.ndarray:
    """The next return's side of its own median: 0 or 1. Two bins on purpose: a finer split of the next return would
    also measure how a feature predicts its SIZE (volatility clusters), which no long-or-short rule can use."""
    return (v > np.median(v)).astype(int)


def info(ctx: Context, n_shifts: int = 100) -> tuple[list[Emit], dict]:
    """The emitted table rules, and the audit: for each instrument, how many features carry information about its next
    return, and how many of those a linear correlation does not see."""
    p, rng = ctx.p, np.random.default_rng(ctx.seed)
    out, audit = [], {}
    e5, e3 = [0.2, 0.4, 0.6, 0.8], [1 / 3, 2 / 3]
    for tg in ctx.targets:
        feats = library(p, target=tg)
        y = ctx.y(tg)
        own_r = rank(p, {"f": "ret", "a": tg, "k": 1}, ctx.w)
        rows_all, scored = [], []
        for f in feats:
            r = rank(p, f, ctx.w)
            m = ctx.fit & np.isfinite(r) & np.isfinite(y) & np.isfinite(own_r)
            if m.sum() < 2 * MIN_ROWS:
                continue
            ctx.count("info", 1)
            xb, yb = np.searchsorted(e5, r[m], side="left"), _updown(y[m])
            ob = np.searchsorted(e3, own_r[m], side="left")
            te, z = shift_z(lambda a: cmi(a, yb, ob, 5, 2, 3), xb, n_shifts, rng)
            lin = _t_corr(r[m], y[m])
            rows_all.append({"feature": _f(f), "te_nats": round(te, 6), "z": round(z, 2), "t_linear": round(lin, 2)})
            scored.append((z, f, m, xb))
        scored.sort(key=lambda s: -s[0])
        audit[tg] = {"features": len(rows_all), "z_at_least_2": sum(r["z"] >= 2 for r in rows_all),
                     "non_linear_only": sum(r["z"] >= 2.5 and abs(r["t_linear"]) < 1.5 for r in rows_all),
                     "best": sorted(rows_all, key=lambda r: -r["z"])[:8]}
        for z, f, m, xb in scored[:max(2, round(4 * ctx.cap("info") / 24))]:  # singles: a five-bin table
            mp, _ = _dev_map(y[m], xb, 5, 1.0)
            if any(mp):
                out.append(Emit({"kind": "table", "target": tg, "feats": [f], "w": ctx.w, "edges": [e5], "map": mp},
                                "information (non-linear)", "info", z,
                                f"the rank of {_f(f)} carries information about {tg}'s next row beyond {tg}'s own "
                                f"last move", {"z_transfer_entropy": round(z, 2), "bins": 5}))
        top = scored[:6]
        pairs = []
        for i in range(len(top)):  # pairs: synergy, the information two features carry only together
            for j in range(i + 1, len(top)):
                f1, f2 = top[i][1], top[j][1]
                r1, r2 = rank(p, f1, ctx.w), rank(p, f2, ctx.w)
                m = ctx.fit & np.isfinite(r1) & np.isfinite(r2) & np.isfinite(y)
                if m.sum() < 2 * MIN_ROWS:
                    continue
                ctx.count("info", 1)
                b1, b2 = np.searchsorted(e3, r1[m], side="left"), np.searchsorted(e3, r2[m], side="left")
                yb = _updown(y[m])
                single = max(mi(b1, yb, 3, 2), mi(b2, yb, 3, 2))
                syn, z = shift_z(lambda a: mi(a, yb, 9, 2) - single, b1 * 3 + b2, n_shifts // 2, rng)
                pairs.append((z, f1, f2, m, b1 * 3 + b2))
        pairs.sort(key=lambda s: -s[0])
        for z, f1, f2, m, cell in pairs[:2]:
            mp, _ = _dev_map(y[m], cell, 9, 1.0)
            if any(mp):
                out.append(Emit({"kind": "table", "target": tg, "feats": [f1, f2], "w": ctx.w, "edges": [e3, e3],
                                 "map": mp}, "information (non-linear)", "info", z,
                                f"{_f(f1)} and {_f(f2)} together carry information about {tg}'s next row that neither "
                                f"carries alone", {"z_synergy": round(z, 2), "bins": 9}))
    if broad(p):  # many instruments: the strongest tables of the whole panel, not six from each instrument
        out = sorted(out, key=lambda e: -e.fit)[:2 * ctx.cap("info")]
    return out, audit


# ── 3. ordinal patterns ─────────────────────────────────────────────────────

def ordinal(ctx: Context) -> list[Emit]:
    out = []
    for tg in ctx.targets:
        y = ctx.y(tg)
        for k, m_ in ((1, 3), (5, 3), (1, 4)):
            code = ordinal_code(ctx.p, tg, k, m_)
            m = ctx.fit & (code >= 0) & np.isfinite(y)
            n_pat = math.factorial(m_)
            if m.sum() < max(2 * MIN_ROWS, 40 * n_pat):
                continue
            ctx.count("ordinal", n_pat)
            mp, z = _dev_map(y[m], code[m], n_pat, 1.0)
            if any(mp):
                out.append(Emit({"kind": "ordinal", "target": tg, "a": tg, "k": k, "m": m_, "map": mp},
                                "ordinal pattern", "ordinal", z,
                                f"the ordering of {tg}'s last {m_} {k}-row returns changes its next row",
                                {"patterns": n_pat, "z_chi_square": round(z, 2)}))
    return sorted(out, key=lambda e: -e.fit)[:ctx.cap("ordinal")]


# ── 4. regimes by k-means ───────────────────────────────────────────────────

def kmeans(x: np.ndarray, k: int, rng, restarts: int = 4, iters: int = 60) -> tuple[np.ndarray, np.ndarray]:
    best = (None, None, math.inf)
    for _ in range(restarts):
        c = x[rng.choice(len(x), size=k, replace=False)].copy()
        for _ in range(iters):
            lab = np.argmin(((x[:, None, :] - c[None, :, :]) ** 2).sum(axis=2), axis=1)
            new = np.array([x[lab == j].mean(axis=0) if (lab == j).any() else c[j] for j in range(k)])
            if np.allclose(new, c):
                break
            c = new
        lab = np.argmin(((x[:, None, :] - c[None, :, :]) ** 2).sum(axis=2), axis=1)
        cost = float(((x - c[lab]) ** 2).sum())
        if cost < best[2]:
            best = (c, lab, cost)
    return best[0], best[1]


def state_features(p: Panel) -> list[dict]:
    """The market's slow state. On a broad panel: the market's move, the instruments' average volatility and average
    of each per-instrument series, their dispersion, and the shared series."""
    if broad(p):
        return ([{"f": "mkt", "k": 20}, {"f": "xavg", "of": {"f": "vol", "k": 20}}, {"f": "disp", "k": 20}]
                + [{"f": "xavg", "of": {"f": "aux", "s": s_}} for s_ in suffixes(p)]
                + [{"f": "aux", "name": n} for n in shared_aux(p)])
    out = []
    for a in p.assets:
        out += [{"f": "ret", "a": a, "k": 20}, {"f": "vol", "a": a, "k": 20}]
    out += [{"f": "aux", "name": n} for n in sorted(p.aux)]
    if len(p.assets) > 1:
        out += [{"f": "disp", "k": 20}]
    return out


def regimes(ctx: Context) -> list[Emit]:
    p, rng, out = ctx.p, np.random.default_rng(ctx.seed + 1), []
    every = state_features(p)
    # the whole state at once, then each slow state series on its own: a regime need not be the largest structure in
    # the market's state to matter (returns are left out of the single series: that is the own-lag family)
    spaces = [(every, (3, 4, 5), None)] + [([f], (2, 3), None) for f in every if f["f"] not in ("ret", "mkt")]
    if broad(p):  # and each instrument's own slow state, for that instrument alone
        for tg in ctx.targets:
            own = [{"f": "vol", "a": tg, "k": 20}] + [{"f": "aux", "name": f"{tg}.{s_}"} for s_ in suffixes(p)
                                                      if f"{tg}.{s_}" in p.aux]
            spaces += [([f], (2, 3), tg) for f in own]
    for feats, ks, only in spaces:
        x = regime_state(p, feats, ctx.w)
        ok = ctx.fit & np.isfinite(x).all(axis=1)
        if ok.sum() < (2 if broad(p) else 4) * MIN_ROWS:  # a broad panel's history is often short (crypto)
            continue
        for k in ks:
            cen, lab = kmeans(x[ok], k, rng)
            full = np.full(p.T, -1)
            full[ok] = lab
            runs = np.diff(np.nonzero(np.concatenate([[True], lab[1:] != lab[:-1], [True]]))[0])
            for tg in (ctx.targets if only is None else [only]):
                y = ctx.y(tg)
                m = ok & np.isfinite(y)
                if m.sum() < 2 * MIN_ROWS:
                    continue
                ctx.count("regimes", k)
                mp, z = _dev_map(y[m], full[m], k, 1.5)
                if any(mp):
                    of = "the market's state" if len(feats) > 1 else _f(feats[0])
                    out.append(Emit({"kind": "regime", "target": tg, "feats": feats, "w": ctx.w,
                                     "centroids": np.round(cen, 4).tolist(), "map": mp}, "regime", "regimes", z,
                                    f"{tg}'s next row depends on which of {k} regimes of {of} it is in",
                                    {"k": k, "mean_run_rows": round(float(runs.mean()), 1), "z_chi_square": round(z, 2),
                                     "state_features": len(feats)}))
    return sorted(out, key=lambda e: -e.fit)[:ctx.cap("regimes")]


# ── 5. anomalies ────────────────────────────────────────────────────────────

def _frozen_shock(x: np.ndarray, ok: np.ndarray) -> dict:
    mu = x[ok].mean(axis=0)
    cov = np.cov(x[ok].T).reshape(x.shape[1], x.shape[1])
    prec = np.linalg.inv(cov + 0.1 * np.diag(np.diag(cov)))
    return {"mu": np.round(mu, 6).tolist(), "prec": np.round(prec, 6).tolist()}


def anomaly(ctx: Context) -> list[Emit]:
    """Rows whose joint shock is extreme, then what follows them. On a narrow panel the shock is every instrument's
    vol-scaled move. On a broad one it is, for each instrument, the market's move, the market's dispersion and the
    instrument's own move, each against its own trailing year."""
    p, out = ctx.p, []
    if broad(p):
        groups = []
        for tg in ctx.targets:
            feats = [{"f": "mkt", "k": 1}, {"f": "disp", "k": 1}, {"f": "ret", "a": tg, "k": 1}]
            x = np.column_stack([zscore(p, f, ctx.w) for f in feats])
            ok = ctx.fit & np.isfinite(x).all(axis=1)
            if ok.sum() >= 2 * MIN_ROWS:
                groups.append(({"feats": feats, "w": ctx.w, **_frozen_shock(x, ok)}, ok, [tg]))
    else:
        x = shock(p, 60)
        ok = ctx.fit & np.isfinite(x).all(axis=1)
        if ok.sum() < 4 * MIN_ROWS:
            return out
        groups = [({"vol_k": 60, **_frozen_shock(x, ok)}, ok, ctx.targets)]
    for base, ok, tgs in groups:
        out += _after_shock(ctx, base, ok, tgs)
    return sorted(out, key=lambda e: -e.fit)[:ctx.cap("anomaly")]


def _after_shock(ctx: Context, base: dict, ok: np.ndarray, tgs: list[str]) -> list[Emit]:
    p, out = ctx.p, []
    d2 = shock_d2(p, base)
    for pct in (97.5, 99.0):
        thr = float(np.percentile(d2[ok], pct))
        for tg in tgs:
            for hold in (1, 5):
                best = None
                for mode in ("cont", "rev", "long", "short"):
                    spec = {"kind": "anomaly", "target": tg, **base, "thr": round(thr, 4), "mode": mode, "hold": hold}
                    r = pnl(spec, p)
                    s = stats(r["gross"], ctx.fit, p.ppy, r["pos"])
                    ctx.count("anomaly", 1)
                    if s["t"] is not None and s["in_position"] >= 20 and (best is None or s["t"] > best[0]):
                        best = (s["t"], spec, mode, s["in_position"])
                if best is not None:
                    what = {"cont": "continues its own move", "rev": "reverses its own move", "long": "rises",
                            "short": "falls"}[best[2]]
                    out.append(Emit(best[1], "anomaly", "anomaly", best[0],
                                    f"after a row whose joint shock is in the top {100 - pct:g}%, {tg} {what} over the "
                                    f"next {hold} rows", {"percentile": pct, "rows_in_position": best[3]}))
    return out


# ── 6. evolutionary search ──────────────────────────────────────────────────

def evolve(ctx: Context, pop: int = 150, gens: int = 25, size_penalty: float = 0.15) -> list[Emit]:
    p, rng = ctx.p, np.random.default_rng(ctx.seed + 2)
    feats, targets = library(p), ctx.targets
    if not targets:
        return []
    lib = {t: library(p, target=t) for t in targets} if broad(p) else None
    qs = ((">", 0.7), (">", 0.8), (">", 0.9), ("<", 0.3), ("<", 0.2), ("<", 0.1))
    conds: dict = {}
    fw = {t: p.fwd()[:, p.col(t)] for t in targets}
    seen: dict = {}

    def leaf(t=None):
        fs = lib[t] if lib is not None else feats
        f = fs[int(rng.integers(len(fs)))]
        op, q = qs[int(rng.integers(len(qs)))]
        return {"feat": f, "w": ctx.w, "op": op, "q": q}

    def new():
        if lib is not None:  # a broad panel: the instrument first, then conditions on what that instrument can read
            t = targets[int(rng.integers(len(targets)))]
            n = leaf(t) if rng.random() < 0.5 else {("and" if rng.random() < 0.6 else "or"): [leaf(t), leaf(t)]}
            return {"kind": "tree", "target": t, "node": n, "side": 1 if rng.random() < 0.5 else -1,
                    "hold": 1 if rng.random() < 0.5 else 5}
        n = leaf() if rng.random() < 0.5 else {("and" if rng.random() < 0.6 else "or"): [leaf(), leaf()]}
        return {"kind": "tree", "target": targets[int(rng.integers(len(targets)))], "node": n,
                "side": 1 if rng.random() < 0.5 else -1, "hold": 1 if rng.random() < 0.5 else 5}

    def boolean(n):
        if "and" in n or "or" in n:
            a, b = (boolean(x) for x in n.get("and", n.get("or")))
            return a & b if "and" in n else a | b
        k_ = key(n)
        if k_ not in conds:
            conds[k_] = node(p, n)
        return conds[k_]

    def fitness(s):
        k_ = key(s)
        if k_ in seen:
            return seen[k_]
        ctx.count("evolve", 1)
        f = fw[s["target"]]
        rows = np.nonzero(ctx.fit & np.isfinite(f))[0]
        pos = s["side"] * held(boolean(s["node"]), s["hold"])[rows].astype(float)
        share = float((pos != 0).mean())
        val = -math.inf
        if 0.02 <= share <= 0.5:
            net = pos * f[rows] - p.cost[s["target"]] * np.abs(pos - np.concatenate([[0.0], pos[:-1]]))
            sd = net.std(ddof=1)
            if sd > 0:
                n_leaves = 2 if ("and" in s["node"] or "or" in s["node"]) else 1
                val = float(net.mean() / sd * math.sqrt(len(net))) - size_penalty * (n_leaves - 1)
        seen[k_] = val
        return val

    def mutate(s):
        s = {**s, "node": dict(s["node"])}
        r = rng.random()
        if r < 0.15:
            s["target"] = targets[int(rng.integers(len(targets)))]
        elif r < 0.3:
            s["side"] = -s["side"]
        elif r < 0.4:
            s["hold"] = 5 if s["hold"] == 1 else 1
        elif "and" in s["node"] or "or" in s["node"]:
            op = "and" if "and" in s["node"] else "or"
            kids = list(s["node"][op])
            if rng.random() < 0.25:
                s["node"] = kids[int(rng.integers(2))]
            else:
                kids[int(rng.integers(2))] = leaf(s["target"])
                s["node"] = {op: kids}
        else:
            s["node"] = (leaf(s["target"]) if rng.random() < 0.6 else
                         {("and" if rng.random() < 0.6 else "or"): [s["node"], leaf(s["target"])]})
        return s

    def cross(a, b):
        la = a["node"].get("and", a["node"].get("or", [a["node"]]))
        lb = b["node"].get("and", b["node"].get("or", [b["node"]]))
        return {**a, "node": {"and": [la[int(rng.integers(len(la)))], lb[int(rng.integers(len(lb)))]]}}

    def pick(people):
        c = [people[int(i)] for i in rng.integers(len(people), size=3)]
        return max(c, key=fitness)

    people = [new() for _ in range(pop)]
    for _ in range(gens):
        people.sort(key=fitness, reverse=True)
        nxt = people[:10]
        while len(nxt) < pop:
            r = rng.random()
            nxt.append(mutate(pick(people)) if r < 0.5 else cross(pick(people), pick(people)) if r < 0.9 else new())
        people = nxt
    ranked = sorted({key(s): s for s in people}.values(), key=fitness, reverse=True)
    out, kept = [], []
    for s in ranked:
        if fitness(s) == -math.inf or len(out) >= ctx.cap("evolve"):
            break
        pos = positions(s, p)[ctx.fit]
        if any(abs(np.corrcoef(pos, q)[0, 1]) > 0.8 for q in kept if pos.std() > 0 and q.std() > 0):
            continue  # the same behaviour again: one is enough
        kept.append(pos)
        out.append(Emit(s, "evolved rule", "evolve", fitness(s),
                        "a rule the evolutionary search kept: it has no stated mechanism until one is proposed",
                        {"generations": gens, "population": pop}))
    return out


# ── 7. combinations across families, and one family pooled across instruments ──

def combine(ctx: Context, emitted: list[Emit], fit_t: dict) -> list[Emit]:
    """`fit_t`: each emitted rule's net t on the fit rows, by spec key: the one yardstick common to all methods. Only
    the fit rows choose what is combined."""
    out = []
    base = [e for e in emitted if e.method not in ("evolve", "combine", "breadth") and fit_t.get(key(e.spec), 0) > 0]
    best: dict = {}
    for e in base:
        k_ = (e.spec["target"], e.family)
        if k_ not in best or fit_t[key(e.spec)] > fit_t[key(best[k_].spec)]:
            best[k_] = e
    for tg in ctx.targets:
        mine = sorted([e for (t, _), e in best.items() if t == tg], key=lambda e: -fit_t[key(e.spec)])
        for i in range(len(mine)):
            for j in range(i + 1, len(mine)):
                ctx.count("combine", 1)
                spec = {"kind": "combo", "target": tg, "op": "and", "parts": [mine[i].spec, mine[j].spec]}
                if (positions(spec, ctx.p)[ctx.fit] != 0).sum() >= 30:
                    out.append(Emit(spec, "combination", "combine",
                                    min(fit_t[key(mine[i].spec)], fit_t[key(mine[j].spec)]),
                                    f"{tg}: act only when a {mine[i].family} rule and a {mine[j].family} rule agree",
                                    {"families": [mine[i].family, mine[j].family]}))
        if len(mine) >= 3:
            ctx.count("combine", 1)
            out.append(Emit({"kind": "combo", "target": tg, "op": "vote", "parts": [e.spec for e in mine[:3]]},
                            "combination", "combine", float(np.mean([fit_t[key(e.spec)] for e in mine[:3]])),
                            f"{tg}: the majority of its best {', '.join(e.family for e in mine[:3])} rules",
                            {"families": [e.family for e in mine[:3]]}))
    if broad(ctx.p):  # many instruments: the strongest joins of the whole panel
        out = (sorted([e for e in out if e.spec["op"] == "and"], key=lambda e: -e.fit)[:ctx.cap("combine")]
               + sorted([e for e in out if e.spec["op"] == "vote"], key=lambda e: -e.fit)[:ctx.cap("combine") // 2])
    for fam in FAMILIES[:6]:  # breadth: one mechanism across instruments is one test with more data
        mine = [e for (t, f), e in sorted(best.items()) if f == fam]
        if len(mine) >= 2:
            ctx.count("combine", 1)
            out.append(Emit({"kind": "book", "parts": [e.spec for e in mine]}, "pooled book", "combine",
                            float(np.mean([fit_t[key(e.spec)] for e in mine])),
                            f"the best {fam} rule of each of {len(mine)} instruments, equal capital each",
                            {"family": fam, "members": len(mine)}))
    return out


# ── 8. breadth: one rule on every instrument at once ───────────────────────

def _star(x, a: str):
    """A rule template made concrete: every "*" becomes the instrument."""
    if isinstance(x, dict):
        return {k_: _star(v, a) for k_, v in x.items()}
    if isinstance(x, list):
        return [_star(v, a) for v in x]
    if isinstance(x, str) and (x == "*" or x.startswith("*.")):
        return a + x[1:]
    return x


def pooled(tpl: dict, assets) -> dict:
    """One rule template as a book: the same rule on each instrument's own features, equal capital each."""
    return {"kind": "book", "parts": [_star({**tpl, "target": "*"}, a) for a in assets]}


def breadth(ctx: Context, pop: int = 120, gens: int = 20, size_penalty: float = 0.15) -> list[Emit]:
    p = ctx.p
    tgs = ctx.targets
    if not broad(p) or len(tgs) < 6:
        return []
    cap = ctx.cap("breadth")
    own = ([{"f": "ret", "k": k} for k in (1, 2, 5, 10, 20, 60)]
           + [{"f": "vol", "k": 20}, {"f": "volr", "k": 5, "k2": 60}, {"f": "absret"}]
           + [{"f": "aux", "s": s_, **d} for s_ in suffixes(p) for d in ({}, {"d": 5})])

    def book_t(spec):
        r = pnl(spec, p)
        return stats(r["gross"], ctx.fit, p.ppy)["t"], stats(r["net"], ctx.fit, p.ppy)["t"]

    # (a) cross-sectional: the top of a ranking against its bottom, oriented by the fit rows
    xs = []
    for tpl in own:
        for q in (0.2, 0.34):
            for hold in (1, 5, 20):  # a slow book trades a fraction of a fast one's turnover: costs decide which lives
                x = {"feat": tpl, "q": q, "hold": hold, "min": max(6, len(p.assets) // 4), "side": 1}
                ctx.count("breadth", 1)
                g, _ = book_t(xs_book(p, x))
                if g is None or g == 0:
                    continue
                side = 1 if g > 0 else -1
                which = "highest" if side > 0 else "lowest"
                xs.append(Emit(xs_book(p, {**x, "side": side}), "cross-sectional", "breadth", abs(g),
                               f"the instruments with the {which} {_f(tpl)} outperform the others over the next rows",
                               {"feature": _f(tpl), "share_each_side": q, "hold_rows": hold, "instruments": len(p.assets),
                                "t_gross_fit": round(g, 3)}))
    xs.sort(key=lambda e: -e.fit)
    # (b) the same sign rule on every instrument's own feature, or on a market feature
    ts = []
    market = [{"f": "mkt", "k": k} for k in (1, 5, 20)] + [{"f": "disp", "k": 20}] + [
        {"f": "xavg", "of": {"f": "aux", "s": s_}} for s_ in suffixes(p)] + [{"f": "aux", "name": n} for n in shared_aux(p)]
    for f, mine in [(tfeat(t, "*"), True) for t in own if t["f"] != "absret"] + [({**t, "a": "*"}, True) for t in (
            {"f": "rel", "k": 5}, {"f": "rel", "k": 20})] + [(f, False) for f in market]:
        ctx.count("breadth", 1)
        tpl = {"kind": "sign", "feat": f, "w": ctx.w, "band": 0.5, "side": 1}
        g, _ = book_t(pooled(tpl, tgs))
        if g is None or g == 0:
            continue
        side = 1 if g > 0 else -1
        what = ("its own " if mine else "the market's ") + _f(f)
        ts.append(Emit(pooled({**tpl, "side": side}, tgs), "pooled time-series", "breadth", abs(g),
                       f"each instrument's next row moves {'with' if side > 0 else 'against'} {what}, beyond half a "
                       f"standard deviation of its trailing year", {"feature": _f(f), "instruments": len(tgs),
                                                                    "t_gross_fit": round(g, 3)}))
    ts.sort(key=lambda e: -e.fit)
    return xs[:cap] + ts[:max(4, cap // 2)] + _evolve_pooled(ctx, pop, gens, size_penalty)[:max(4, cap // 2)]


def _evolve_pooled(ctx: Context, pop: int, gens: int, size_penalty: float) -> list[Emit]:
    """The evolutionary search again, but every tree is traded on every instrument (its leaves read each instrument's
    own features, or the market's) and its fitness is the pooled book's net t on the fit rows."""
    p, rng, tgs = ctx.p, np.random.default_rng(ctx.seed + 3), ctx.targets
    feats = library(p, target="*")
    qs = ((">", 0.7), (">", 0.8), (">", 0.9), ("<", 0.3), ("<", 0.2), ("<", 0.1))
    fw = np.column_stack([p.fwd()[:, p.col(a)] for a in tgs])
    rows = np.nonzero(ctx.fit)[0]
    live = np.isfinite(fw[rows])
    f0 = np.where(live, fw[rows], 0.0)
    cost = np.array([p.cost[a] for a in tgs])
    conds: dict = {}
    seen: dict = {}

    def leaf():
        op, q = qs[int(rng.integers(len(qs)))]
        return {"feat": feats[int(rng.integers(len(feats)))], "w": ctx.w, "op": op, "q": q}

    def new():
        n = leaf() if rng.random() < 0.5 else {("and" if rng.random() < 0.6 else "or"): [leaf(), leaf()]}
        return {"kind": "tree", "node": n, "side": 1 if rng.random() < 0.5 else -1, "hold": 1 if rng.random() < 0.5 else 5}

    def boolean(n, a):
        if "and" in n or "or" in n:
            x, y = (boolean(c, a) for c in n.get("and", n.get("or")))
            return x & y if "and" in n else x | y
        k_ = (key(n), a)
        if k_ not in conds:
            conds[k_] = node(p, _star(n, a))
        return conds[k_]

    def fitness(s):
        k_ = key(s)
        if k_ in seen:
            return seen[k_]
        ctx.count("breadth", 1)
        pos = s["side"] * np.column_stack([held(boolean(s["node"], a), s["hold"])[rows] for a in tgs]).astype(float) * live
        share = float((pos != 0).sum() / max(live.sum(), 1))
        val = -math.inf
        if 0.02 <= share <= 0.5:
            turn = np.abs(pos - np.vstack([np.zeros((1, pos.shape[1])), pos[:-1]]))
            net = (pos * f0 - cost[None, :] * turn).mean(axis=1)
            sd = net.std(ddof=1)
            if sd > 0:
                n_leaves = 2 if ("and" in s["node"] or "or" in s["node"]) else 1
                val = float(net.mean() / sd * math.sqrt(len(net))) - size_penalty * (n_leaves - 1)
        seen[k_] = val
        return val

    def mutate(s):
        s = {**s, "node": dict(s["node"])}
        r = rng.random()
        if r < 0.2:
            s["side"] = -s["side"]
        elif r < 0.35:
            s["hold"] = 5 if s["hold"] == 1 else 1
        elif "and" in s["node"] or "or" in s["node"]:
            op = "and" if "and" in s["node"] else "or"
            kids = list(s["node"][op])
            if rng.random() < 0.25:
                s["node"] = kids[int(rng.integers(2))]
            else:
                kids[int(rng.integers(2))] = leaf()
                s["node"] = {op: kids}
        else:
            s["node"] = leaf() if rng.random() < 0.6 else {("and" if rng.random() < 0.6 else "or"): [s["node"], leaf()]}
        return s

    def pick(people):
        return max((people[int(i)] for i in rng.integers(len(people), size=3)), key=fitness)

    people = [new() for _ in range(pop)]
    for _ in range(gens):
        people.sort(key=fitness, reverse=True)
        nxt = people[:8]
        while len(nxt) < pop:
            nxt.append(mutate(pick(people)) if rng.random() < 0.8 else new())
        people = nxt
    out, kept = [], []
    for s in sorted({key(s): s for s in people}.values(), key=fitness, reverse=True):
        if fitness(s) == -math.inf or len(out) >= 12:
            break
        spec = pooled(s, tgs)
        beh = np.nan_to_num(pnl(spec, p)["net"][ctx.fit])
        if any(abs(np.corrcoef(beh, q)[0, 1]) > 0.8 for q in kept if beh.std() > 0 and q.std() > 0):
            continue
        kept.append(beh)
        out.append(Emit(spec, "pooled time-series", "breadth", fitness(s),
                        "a rule the evolutionary search kept, traded on every instrument: it has no stated mechanism "
                        "until one is proposed", {"generations": gens, "population": pop, "instruments": len(tgs),
                                                  "search": "evolutionary, pooled fitness"}))
    return out


def discover(ctx: Context) -> tuple[list[Emit], dict]:
    """Every method in turn. Returns the emitted rules and the information audit."""
    emitted = leadlag(ctx)
    table, audit = info(ctx)
    emitted += table + ordinal(ctx) + regimes(ctx) + anomaly(ctx)
    emitted += evolve(ctx, pop=300, gens=30) if broad(ctx.p) else evolve(ctx)
    emitted += breadth(ctx)
    seen, uniq = set(), []
    for e in emitted:
        if key(e.spec) not in seen:
            seen.add(key(e.spec))
            uniq.append(e)
    fit_t = {}
    for e in uniq:
        r = pnl(e.spec, ctx.p)
        fit_t[key(e.spec)] = stats(r["net"], ctx.fit, ctx.p.ppy)["t"] or 0.0
    for e in combine(ctx, uniq, fit_t):
        if key(e.spec) not in seen:
            seen.add(key(e.spec))
            uniq.append(e)
    return uniq, audit


__all__ = ["Context", "Emit", "FAMILIES", "anomaly", "breadth", "cmi", "combine", "discover", "evolve", "info", "kmeans",
           "leadlag", "mi", "ordinal", "pooled", "regimes", "shift_z"]
