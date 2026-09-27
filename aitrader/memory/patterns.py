"""Pattern memory: historical analogues, point-in-time.

"The current market resembles these past situations — here is what
happened after them." Historical data is EXPERIENCE, not knowledge of the
future: a past situation enters the evidence available at time T only if
its outcome had already RESOLVED by T. That rule is what makes twenty years
of memory usable in a backtest without leaking (and it is what a trader's
memory is: you remember how a situation ended only after it ended).

The distance is Euclidean over standardised features. Standardisation
statistics come from training data only and are part of the memory's
version. No vector database is used: with tens of thousands to a few
hundred thousand patterns and ~20 dimensions, an exact numpy scan is fast,
exact, and has no moving parts. That choice is revisited only if a
measured latency says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..features.store import INDEX

#: 1.1.0: evidence also reports the age and instrument concentration of the analogues.
MEMORY_VERSION = "patterns-1.1.0"

ANALOG_FEATURES = (
    "r6", "r24", "r120", "er24", "er120", "dist_ma48", "ma_slope", "vol_ratio",
    "rv_ratio", "range_pos24", "range_pos120", "brk_hi120", "brk_lo120",
    "smc_hi_dist", "smc_lo_dist", "smc_structure", "hour_sin", "hour_cos",
)


@dataclass(frozen=True)
class ActionEvidence:
    action: str  # e.g. "T1:BUY"
    n: int
    mean_r: float
    se: float
    lower: float  # mean - z * se
    win_rate: float
    median_r: float

    def as_dict(self) -> dict:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in self.__dict__.items()}


@dataclass(frozen=True)
class AnalogEvidence:
    available: int  # patterns whose outcome was known at query time
    k: int
    mean_distance: float
    typical_distance: float  # median neighbour distance in training: a similarity yardstick
    actions: dict[str, ActionEvidence]
    examples: list[dict] = field(default_factory=list)
    median_age_days: float = float("nan")  # how long ago the analogues happened
    top_symbol_share: float = float("nan")  # share of analogues from the single most common instrument

    @property
    def similarity(self) -> float:
        """1 at the training median neighbour distance, lower when farther."""
        if not np.isfinite(self.mean_distance) or self.mean_distance <= 0:
            return 0.0
        return float(min(1.0, self.typical_distance / self.mean_distance))

    def as_dict(self) -> dict:
        return {
            "available": self.available, "k": self.k,
            "mean_distance": round(self.mean_distance, 4), "similarity": round(self.similarity, 3),
            "actions": {a: e.as_dict() for a, e in self.actions.items()},
            "examples": self.examples,
            "median_age_days": round(self.median_age_days, 1) if np.isfinite(self.median_age_days) else None,
            "top_symbol_share": round(self.top_symbol_share, 3) if np.isfinite(self.top_symbol_share) else None,
        }


class PatternMemory:
    def __init__(self, mean: np.ndarray, std: np.ndarray, action_keys: tuple[str, ...],
                 typical_distance: float = 1.0, version: str = MEMORY_VERSION) -> None:
        self.version = version
        self.mean = np.asarray(mean, float)
        self.std = np.where(np.asarray(std, float) > 0, np.asarray(std, float), 1.0)
        self.action_keys = tuple(action_keys)
        self.typical_distance = float(typical_distance)
        self._x: list[np.ndarray] = []
        self._avail: list[np.ndarray] = []
        self._out: list[np.ndarray] = []
        self._meta: list[np.ndarray] = []  # symbol index, decision time
        self._symbols: list[str] = []
        self._frozen: tuple | None = None

    @classmethod
    def fit_scaler(cls, matrix: np.ndarray, action_keys: tuple[str, ...]) -> "PatternMemory":
        cols = [INDEX[f] for f in ANALOG_FEATURES]
        x = matrix[:, cols]
        x = x[np.all(np.isfinite(x), axis=1)]
        mem = cls(x.mean(axis=0), x.std(axis=0), action_keys)
        # A similarity yardstick: median distance to the nearest 50 of a sample.
        if len(x) > 2000:
            rng = np.random.default_rng(0)
            s = (x[rng.choice(len(x), 2000, replace=False)] - mem.mean) / mem.std
            d = np.sqrt(((s[:, None, :] - s[None, :, :]) ** 2).sum(-1))
            d.sort(axis=1)
            mem.typical_distance = float(np.median(d[:, 1:51]))
        return mem

    def _std(self, rows: np.ndarray) -> np.ndarray:
        return (rows - self.mean) / self.std

    def add(self, features: np.ndarray, outcomes: np.ndarray, available_at: np.ndarray,
            symbol: str, decision_time: np.ndarray) -> int:
        """Add patterns. `outcomes` is (n, n_actions) R; `available_at` is when ALL
        of a pattern's outcomes were known. Incomplete rows are skipped, not filled."""
        cols = [INDEX[f] for f in ANALOG_FEATURES]
        x = features[:, cols] if features.shape[1] != len(ANALOG_FEATURES) else features
        ok = np.all(np.isfinite(x), axis=1) & np.all(np.isfinite(outcomes), axis=1) & (available_at > 0)
        if symbol not in self._symbols:
            self._symbols.append(symbol)
        sid = self._symbols.index(symbol)
        self._x.append(self._std(x[ok]).astype(np.float32))
        self._out.append(outcomes[ok].astype(np.float32))
        self._avail.append(available_at[ok].astype(np.int64))
        self._meta.append(np.column_stack([np.full(int(ok.sum()), sid), decision_time[ok]]).astype(np.int64))
        self._frozen = None
        return int(ok.sum())

    def _arrays(self):
        if self._frozen is None:
            if not self._x:
                empty = np.zeros((0, len(ANALOG_FEATURES)), np.float32)
                self._frozen = (empty, np.zeros((0, len(self.action_keys)), np.float32),
                                np.zeros(0, np.int64), np.zeros((0, 2), np.int64), np.zeros(0, np.float32))
            else:
                x = np.concatenate(self._x)
                avail = np.concatenate(self._avail)
                order = np.argsort(avail, kind="stable")
                x = x[order]
                self._frozen = (x, np.concatenate(self._out)[order], avail[order],
                                np.concatenate(self._meta)[order], (x.astype(np.float64) ** 2).sum(1))
        return self._frozen

    def __len__(self) -> int:
        return len(self._arrays()[2])

    def query(self, values: dict[str, float] | np.ndarray, t: int, *, k: int = 100, z: float = 1.28,
              exclude_symbol: str | None = None, exclude_after: int | None = None) -> AnalogEvidence | None:
        """Nearest analogues whose outcomes were known at `t`. None if too few exist."""
        x, out, avail, meta, sq = self._arrays()
        n_avail = int(np.searchsorted(avail, t, side="right"))
        if isinstance(values, dict):
            q = np.array([values.get(f, np.nan) for f in ANALOG_FEATURES], float)
        else:
            q = np.asarray(values, float)
        if n_avail < k or not np.all(np.isfinite(q)):
            return None
        qs = self._std(q)
        d2 = sq[:n_avail] - 2.0 * (x[:n_avail].astype(np.float64) @ qs) + float(qs @ qs)
        mask = None
        if exclude_symbol is not None and exclude_symbol in self._symbols and exclude_after is not None:
            sid = self._symbols.index(exclude_symbol)
            # never let a pattern from the same instrument's current episode vote on itself
            mask = (meta[:n_avail, 0] == sid) & (meta[:n_avail, 1] >= exclude_after)
            d2 = np.where(mask, np.inf, d2)
        kk = min(k, n_avail)
        nn = np.argpartition(d2, kk - 1)[:kk]
        nn = nn[np.isfinite(d2[nn])]
        if len(nn) < max(10, k // 2):
            return None
        dist = np.sqrt(np.maximum(d2[nn], 0))
        o = out[nn].astype(np.float64)
        actions = {}
        for j, key in enumerate(self.action_keys):
            col = o[:, j]
            m, s = float(col.mean()), float(col.std(ddof=1)) if len(col) > 1 else float("nan")
            se = s / np.sqrt(len(col))
            actions[key] = ActionEvidence(key, len(col), m, se, m - z * se, float((col > 0).mean()),
                                          float(np.median(col)))
        closest = nn[np.argsort(dist)[:5]]
        examples = [{"symbol": self._symbols[int(meta[i, 0])], "time": int(meta[i, 1]),
                     "distance": round(float(np.sqrt(max(d2[i], 0))), 3),
                     "outcomes": {a: round(float(out[i, j]), 3) for j, a in enumerate(self.action_keys)}}
                    for i in closest]
        age_days = float(np.median(t - meta[nn, 1].astype(np.float64))) / 86400.0
        top_share = float(np.bincount(meta[nn, 0].astype(np.int64)).max() / len(nn))
        return AnalogEvidence(n_avail, len(nn), float(dist.mean()), self.typical_distance, actions, examples,
                              age_days, top_share)

    # ── persistence ─────────────────────────────────────────────────────

    def save(self, path, compact: bool = False) -> None:
        """`compact` stores features and outcomes as float16 (~3 significant digits):
        ample for standardised distances and R outcomes, a quarter of the size."""
        x, out, avail, meta, _ = self._arrays()
        if compact:
            x, out = x.astype(np.float16), out.astype(np.float16)
        np.savez_compressed(path, x=x, out=out, avail=avail, meta=meta, mean=self.mean, std=self.std,
                            actions=np.array(self.action_keys), symbols=np.array(self._symbols),
                            typical=np.array([self.typical_distance]), version=np.array([self.version]))

    @classmethod
    def load(cls, path) -> "PatternMemory":
        with np.load(path, allow_pickle=False) as z:
            mem = cls(z["mean"], z["std"], tuple(str(a) for a in z["actions"]), float(z["typical"][0]),
                      str(z["version"][0]))
            mem._symbols = [str(s) for s in z["symbols"]]
            mem._x, mem._out = [z["x"].astype(np.float32)], [z["out"].astype(np.float32)]
            mem._avail, mem._meta = [z["avail"]], [z["meta"]]
        return mem
