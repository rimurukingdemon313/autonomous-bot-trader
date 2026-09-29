"""A study: one chronological segment of the universe, its decision rows, their feature bins and
the outcome of every declared exit — with trades taken as a real account would take them.

Conventions every stage of discovery shares:
- a decision row is an H1 bar close; the trade enters at the next bar's open (exits.simulate);
- a row belongs to a segment only if its decision time is inside it AND every bar its outcome
  could need (the longest exit plus a one-bar delay) closes before the segment ends: outcomes
  never straddle two segments (purging). Segments are separated by an embargo on top;
- one position per instrument per hypothesis: a signal while a position is open is not a trade
  (greedy, in time order). Overlapping "trades" would count one price move many times;
- bins are fitted on the DISCOVERY segment only and frozen; later segments reuse the edges.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone

import numpy as np

from ...data.bars import BarSeries
from ..labels import BUY, CostModel
from .exits import EXIT_BY_KEY, ExitSpec, simulate
from .stats import cluster_t, week_of

STUDY_VERSION = "study-1.0.0"
PURGE_BARS = max(e.max_bars for e in EXIT_BY_KEY.values()) + 1  # longest exit + the delay stress
LABELS = ("low", "mid", "high")
QUANTILES = (1 / 3, 2 / 3)
STRESSES = ("base", "costs", "delay")


def stressed_costs(c: CostModel) -> CostModel:
    """Spread x1.5, slippage x2, commission and swap x1.5 — the lab's stress, a little harsher."""
    return replace(c, spread_multiple=1.5 * c.spread_multiple, slippage_pips=2 * c.slippage_pips,
                   commission_pips_rt=1.5 * c.commission_pips_rt, swap_atr_per_night=1.5 * c.swap_atr_per_night)


def epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


@dataclass(frozen=True)
class Segment:
    name: str
    role: str  # fit | select | judge (the registry's roles)
    start: date  # first decision time, inclusive
    end: date  # decisions AND their outcomes finish before this, exclusive

    def to_json(self) -> dict:
        return {"name": self.name, "role": self.role, "start": self.start.isoformat(), "end": self.end.isoformat()}


@dataclass(frozen=True)
class Condition:
    """A conjunction of (feature, bin) terms; bin 0/1/2 = low/mid/high (or a declared group)."""

    terms: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if not self.terms or len({f for f, _ in self.terms}) != len(self.terms):
            raise ValueError("a condition needs distinct features")
        if any(b not in (0, 1, 2) for _, b in self.terms):
            raise ValueError("bins are 0, 1 or 2")

    @property
    def key(self) -> str:
        return "&".join(f"{f}={LABELS[b]}" for f, b in self.terms)

    @property
    def features(self) -> tuple[str, ...]:
        return tuple(f for f, _ in self.terms)

    @classmethod
    def parse(cls, key: str) -> "Condition":
        terms = []
        for part in key.split("&"):
            f, lab = part.split("=")
            terms.append((f, LABELS.index(lab)))
        return cls(tuple(terms))


@dataclass(frozen=True)
class Binning:
    """Frozen bin edges for one feature: per-symbol tercile edges, or declared value groups."""

    feature: str
    edges: dict = field(default_factory=dict)  # symbol -> (lower, upper)
    groups: tuple[tuple[float, ...], ...] | None = None
    names: tuple[str, str, str] = LABELS

    def apply(self, symbol: str, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, float)
        out = np.full(len(x), -1, np.int8)
        ok = np.isfinite(x)
        if self.groups is not None:
            for b, vals in enumerate(self.groups):
                out[ok & np.isin(x, vals)] = b
            return out
        if symbol not in self.edges:
            return out
        lo, hi = self.edges[symbol]
        out[ok & (x < lo)] = 0
        out[ok & (x >= lo) & (x < hi)] = 1
        out[ok & (x >= hi)] = 2
        return out

    def to_json(self) -> dict:
        return {"feature": self.feature, "names": list(self.names),
                "groups": [list(g) for g in self.groups] if self.groups is not None else None,
                "edges": {s: [float(a), float(b)] for s, (a, b) in sorted(self.edges.items())}}

    @classmethod
    def from_json(cls, raw: dict) -> "Binning":
        groups = tuple(tuple(g) for g in raw["groups"]) if raw.get("groups") is not None else None
        return cls(raw["feature"], {s: (a, b) for s, (a, b) in raw.get("edges", {}).items()}, groups,
                   tuple(raw.get("names", LABELS)))


def fit_binning(feature: str, values: dict[str, np.ndarray], groups=None, names=LABELS,
                quantiles: tuple[float, float] = QUANTILES) -> Binning:
    """Edges from the given values only (the discovery rows); NaN ignored, never filled."""
    if groups is not None:
        return Binning(feature, {}, tuple(tuple(float(v) for v in g) for g in groups), tuple(names))
    edges = {}
    for sym, x in values.items():
        x = np.asarray(x, float)
        x = x[np.isfinite(x)]
        if len(x) >= 30:
            a, b = np.quantile(x, quantiles)
            edges[sym] = (float(a), float(b))
    return Binning(feature, edges, None, tuple(names))


@dataclass
class SymbolData:
    symbol: str
    series: BarSeries
    pip: float
    columns: dict[str, np.ndarray]  # feature -> column over the whole series
    atr: np.ndarray


def segment_rows(sd: SymbolData, seg: Segment, purge_bars: int = PURGE_BARS) -> np.ndarray:
    """Decision rows inside `seg` whose whole outcome window also closes inside it."""
    t0, t1 = epoch(seg.start), epoch(seg.end)
    avail = sd.series.available_at
    n = len(avail)
    rows = np.flatnonzero((avail >= t0) & (avail < t1))
    last = rows + purge_bars
    ok = (last < n) & np.isfinite(sd.atr[rows]) & (sd.atr[rows] > 0)
    ok[ok] &= avail[last[ok]] <= t1
    return rows[ok]


@dataclass
class Trades:
    """Trades actually taken (one position per instrument at a time), pooled over instruments."""

    symbol: np.ndarray
    row: np.ndarray
    t: np.ndarray  # decision time
    exit_t: np.ndarray
    r: np.ndarray
    mfe: np.ndarray
    mae: np.ndarray
    cost: np.ndarray
    bars: np.ndarray
    reason: np.ndarray
    context: dict = field(default_factory=dict)  # name -> per-trade values (e.g. regime bins)

    @property
    def n(self) -> int:
        return len(self.r)

    def stats(self) -> dict:
        return cluster_t(self.r, week_of(self.t))

    def subset(self, keep: np.ndarray) -> "Trades":
        return Trades(*(getattr(self, f)[keep] for f in ("symbol", "row", "t", "exit_t", "r", "mfe", "mae", "cost",
                                                         "bars", "reason")),
                      context={k: v[keep] for k, v in self.context.items()})

    def years(self) -> np.ndarray:
        return (self.t // 86400 * 86400).astype("datetime64[s]").astype("datetime64[Y]").astype(int) + 1970


def _next_true(mask: np.ndarray) -> np.ndarray:
    m = len(mask)
    idx = np.where(mask, np.arange(m), m)
    out = np.empty(m + 1, np.int64)
    out[:m] = np.minimum.accumulate(idx[::-1])[::-1]
    out[m] = m
    return out


def greedy(mask: np.ndarray, free_at: np.ndarray) -> np.ndarray:
    """Positions taken when every True in `mask` is a signal and a position blocks new ones
    until `free_at` (the first decision position at or after its exit bar)."""
    nxt = _next_true(mask)
    m = len(mask)
    out = []
    p = nxt[0]
    while p < m:
        out.append(p)
        p = nxt[min(int(free_at[p]), m)]
    return np.asarray(out, np.int64)


class Study:
    def __init__(self, data: dict[str, SymbolData], segment: Segment, binnings: dict[str, Binning],
                 costs: CostModel = CostModel(), purge_bars: int = PURGE_BARS,
                 context: dict[str, Binning] | None = None) -> None:
        self.data, self.segment, self.costs = data, segment, costs
        self.binnings = dict(binnings)
        self.context_binnings = dict(context or {})
        self.symbols = tuple(sorted(data))
        self.rows = {s: segment_rows(data[s], segment, purge_bars) for s in self.symbols}
        self.time = {s: data[s].series.available_at[self.rows[s]] for s in self.symbols}
        self._bins: dict[tuple[str, str, str], np.ndarray] = {}
        self._out: dict[tuple, dict] = {}

    # ── bins and masks ──────────────────────────────────────────────────

    def bins(self, symbol: str, name: str, binning: Binning | None = None) -> np.ndarray:
        """Bins of a grid feature, or of a named context (whose Binning says which column it reads)."""
        b = binning or self.binnings.get(name) or self.context_binnings[name]
        key = (symbol, b.feature, repr(sorted(b.edges.items())) + repr(b.groups))
        if key not in self._bins:
            self._bins[key] = b.apply(symbol, self.data[symbol].columns[b.feature][self.rows[symbol]])
        return self._bins[key]

    def mask(self, symbol: str, cond: Condition, binnings: dict[str, Binning] | None = None) -> np.ndarray:
        m = np.ones(len(self.rows[symbol]), bool)
        for f, b in cond.terms:
            m &= self.bins(symbol, f, (binnings or {}).get(f)) == b
        return m

    def masks(self, cond: Condition, binnings: dict[str, Binning] | None = None) -> dict[str, np.ndarray]:
        return {s: self.mask(s, cond, binnings) for s in self.symbols}

    # ── outcomes and trades ─────────────────────────────────────────────

    def outcome(self, symbol: str, exit_: ExitSpec, side: int, stress: str = "base") -> dict:
        key = (symbol, exit_.key, side, stress)
        if key not in self._out:
            sd = self.data[symbol]
            rows = self.rows[symbol]
            costs = stressed_costs(self.costs) if stress == "costs" else self.costs
            o = simulate(sd.series, rows, side, exit_, sd.pip, costs, atr=sd.atr, delay=1 if stress == "delay" else 0)
            free = np.searchsorted(rows, np.where(o.exit_index >= 0, o.exit_index, rows + 1), side="left")
            free = np.maximum(free, np.arange(len(rows)) + 1)  # never re-enter at or before the decision itself
            self._out[key] = {"r": o.r, "exit_index": o.exit_index, "free": free, "mfe": o.mfe_r, "mae": o.mae_r,
                              "cost": o.cost_r, "bars": o.bars_held, "reason": o.reason,
                              "exit_t": o.resolve_time}
        return self._out[key]

    def trades(self, masks: dict[str, np.ndarray], exit_: ExitSpec | str, side: int, stress: str = "base",
               context: tuple[str, ...] = ()) -> Trades:
        exit_ = EXIT_BY_KEY[exit_] if isinstance(exit_, str) else exit_
        parts = []
        for s in self.symbols:
            mk = masks.get(s)
            if mk is None or not mk.any():
                continue
            o = self.outcome(s, exit_, side, stress)
            valid = mk & np.isfinite(o["r"])
            pos = greedy(valid, o["free"])
            if len(pos):
                parts.append((s, pos, o))
        cols = {k: [] for k in ("symbol", "row", "t", "exit_t", "r", "mfe", "mae", "cost", "bars", "reason")}
        ctx = {c: [] for c in context}
        for s, pos, o in parts:
            cols["symbol"].append(np.full(len(pos), s, dtype=object))
            cols["row"].append(self.rows[s][pos])
            cols["t"].append(self.time[s][pos])
            for k in ("exit_t", "r", "mfe", "mae", "cost", "bars", "reason"):
                cols[k].append(o[k][pos])
            for c in context:
                ctx[c].append(self.bins(s, c)[pos])
        if not parts:
            empty = {k: np.zeros(0, dtype=object if k == "symbol" else float) for k in cols}
            return Trades(**empty, context={c: np.zeros(0, np.int8) for c in context})
        joined = {k: np.concatenate(v) for k, v in cols.items()}
        order = np.lexsort((joined["symbol"].astype(str), joined["t"]))
        tr = Trades(**{k: v[order] for k, v in joined.items()},
                    context={c: np.concatenate(v)[order] for c, v in ctx.items()})
        return tr

    def random_masks(self, counts: dict[str, int], rng: np.random.Generator) -> dict[str, np.ndarray]:
        """Uniformly random signal rows, `counts[s]` per instrument (a no-skill entry baseline)."""
        out = {}
        for s in self.symbols:
            m = np.zeros(len(self.rows[s]), bool)
            k = min(int(counts.get(s, 0)), len(m))
            if k:
                m[rng.choice(len(m), size=k, replace=False)] = True
            out[s] = m
        return out


__all__ = ["BUY", "Binning", "Condition", "LABELS", "PURGE_BARS", "STUDY_VERSION", "Segment", "Study",
           "SymbolData", "Trades", "epoch", "fit_binning", "greedy", "segment_rows", "stressed_costs"]
