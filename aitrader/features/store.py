"""The feature store: one definition of every feature, for research and production.

Every feature at bar i is a function of the last `LOOKBACK` bars ending at i
and nothing else. That single property gives three guarantees, each tested:

1. causality — row i never reads bar i+1 (truncation test);
2. research = production — the value computed over twenty years of history
   equals the value computed from only the last LOOKBACK bars, which is all
   the live system has (window test);
3. missing stays missing — insufficient history yields NaN, never a default.

Prices are MID prices; all distances are expressed in units of ATR(24), so
features are comparable across instruments and eras. Spread is taken from
the measured bid/ask, never assumed.

`ticks` features describe tick ACTIVITY. Spot FX has no centralised volume
and nothing here claims otherwise (DATA_CONTRACT.md §4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ..data.bars import BarSeries

FEATURE_VERSION = "feat-1.0.0"
#: Bars of history every feature needs at most, plus margin. The live system
#: must be given at least this many closed bars.
LOOKBACK = 260
SWING_K = 3  # a swing is confirmed SWING_K bars after it forms


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    group: str
    window: int
    description: str


SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec("r1", "momentum", 25, "last-bar change / ATR24"),
    FeatureSpec("r6", "momentum", 25, "6-bar change / ATR24"),
    FeatureSpec("r24", "momentum", 25, "24-bar change / ATR24"),
    FeatureSpec("r120", "momentum", 121, "120-bar change / ATR24"),
    FeatureSpec("er24", "trend", 25, "efficiency ratio over 24 bars"),
    FeatureSpec("er120", "trend", 121, "efficiency ratio over 120 bars"),
    FeatureSpec("dist_ma48", "trend", 48, "(close - SMA48) / ATR24"),
    FeatureSpec("ma_slope", "trend", 240, "(SMA48 - SMA240) / ATR24"),
    FeatureSpec("vol_ratio", "volatility", 241, "ATR24 / ATR240"),
    FeatureSpec("rv_ratio", "volatility", 241, "stdev of changes, 24 vs 240 bars"),
    FeatureSpec("range_pos24", "structure", 24, "close position in 24-bar range, 0..1"),
    FeatureSpec("range_pos120", "structure", 120, "close position in 120-bar range, 0..1"),
    FeatureSpec("brk_hi120", "structure", 121, "(close - prior 120-bar high) / ATR24"),
    FeatureSpec("brk_lo120", "structure", 121, "(close - prior 120-bar low) / ATR24"),
    FeatureSpec("spread_rel", "execution", 25, "measured spread / ATR24"),
    FeatureSpec("tick_activity", "liquidity", 240, "mean ticks 24 / mean ticks 240 (activity, not volume)"),
    FeatureSpec("hour_sin", "calendar", 1, "sin of UTC hour at bar close"),
    FeatureSpec("hour_cos", "calendar", 1, "cos of UTC hour at bar close"),
    FeatureSpec("bar_body", "price_action", 1, "(close - open) / (high - low) of the last bar"),
    FeatureSpec("smc_hi_dist", "smc", 127, "(close - last confirmed swing high) / ATR24"),
    FeatureSpec("smc_lo_dist", "smc", 127, "(close - last confirmed swing low) / ATR24"),
    FeatureSpec("smc_structure", "smc", 247, "sign(HH) + sign(HL) of the last two confirmed swings"),
    FeatureSpec("smc_sweep", "smc", 127, "+1 swept a swing low and closed above; -1 the mirror"),
)
NAMES = tuple(s.name for s in SPECS)
INDEX = {n: i for i, n in enumerate(NAMES)}


# ── windowed primitives: value i depends on inputs i-w+1..i only ────────


def _pad(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(n, np.nan)
    out[n - len(x):] = x
    return out


def _roll(x: np.ndarray, w: int, fn) -> np.ndarray:
    n = len(x)
    if n < w:
        return np.full(n, np.nan)
    return _pad(fn(sliding_window_view(x, w), axis=-1), n)


def _lag(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[: len(x) - k]
    return out


def _safe_div(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        out = a / b
    out[~np.isfinite(out)] = np.nan
    return out


def _swings(high: np.ndarray, low: np.ndarray, k: int, limit: int):
    """Last and previous CONFIRMED swing levels as of each bar.

    A swing high at j needs h[j] above the k bars before and at least the k
    after, so it is only known at j+k. Consumers read it through the lag
    `i - k`, which is what makes this causal.
    """
    n = len(high)
    idx = np.arange(n)
    cond_h = np.zeros(n, bool)
    cond_l = np.zeros(n, bool)
    if n >= 2 * k + 1:
        wh = sliding_window_view(high, 2 * k + 1)
        wl = sliding_window_view(low, 2 * k + 1)
        mid_h, mid_l = wh[:, k], wl[:, k]
        cond_h[k:n - k] = (mid_h > wh[:, :k].max(axis=1)) & (mid_h >= wh[:, k + 1:].max(axis=1))
        cond_l[k:n - k] = (mid_l < wl[:, :k].min(axis=1)) & (mid_l <= wl[:, k + 1:].min(axis=1))

    def last_two(cond, level):
        pos = np.where(cond, idx, -1)
        last = np.maximum.accumulate(pos)
        # value known at bar i: the last swing at or before i-k
        known = _lag(last.astype(float), k)
        cur = np.full(n, np.nan)
        prev = np.full(n, np.nan)
        for i in np.flatnonzero(np.isfinite(known) & (known >= 0)):
            j = int(known[i])
            if i - j > limit:
                continue
            cur[i] = level[j]
            pj = last[j - 1] if j > 0 else -1
            if pj >= 0 and i - pj <= 2 * limit:
                prev[i] = level[pj]
        return cur, prev

    hi, hi_prev = last_two(cond_h, high)
    lo, lo_prev = last_two(cond_l, low)
    return hi, hi_prev, lo, lo_prev


def compute_matrix(series: BarSeries) -> np.ndarray:
    """Feature matrix (n_bars, n_features); NaN where history is insufficient."""
    n = len(series)
    o, h, l, c = series.mid_open, series.mid_high, series.mid_low, series.mid_close
    prev_c = _lag(c, 1)
    tr = np.fmax(h - l, np.fmax(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = np.nan  # needs a previous close: never assumed
    atr24 = _roll(tr, 24, np.mean)
    atr240 = _roll(tr, 240, np.mean)
    dc = c - prev_c
    absdc = np.abs(dc)
    sma48 = _roll(c, 48, np.mean)
    sma240 = _roll(c, 240, np.mean)
    hi120 = _roll(h, 120, np.max)
    lo120 = _roll(l, 120, np.min)
    hi24 = _roll(h, 24, np.max)
    lo24 = _roll(l, 24, np.min)
    prior_hi120 = _lag(hi120, 1)
    prior_lo120 = _lag(lo120, 1)
    close_hour = ((series.open_time + series.period) % 86400) / 3600.0
    sw_hi, sw_hi_prev, sw_lo, sw_lo_prev = _swings(h, l, SWING_K, 120)
    ticks = series.ticks.astype(float)

    cols = {
        "r1": _safe_div(c - _lag(c, 1), atr24),
        "r6": _safe_div(c - _lag(c, 6), atr24),
        "r24": _safe_div(c - _lag(c, 24), atr24),
        "r120": _safe_div(c - _lag(c, 120), atr24),
        "er24": _safe_div(np.abs(c - _lag(c, 24)), _roll(absdc, 24, np.sum)),
        "er120": _safe_div(np.abs(c - _lag(c, 120)), _roll(absdc, 120, np.sum)),
        "dist_ma48": _safe_div(c - sma48, atr24),
        "ma_slope": _safe_div(sma48 - sma240, atr24),
        "vol_ratio": _safe_div(atr24, atr240),
        "rv_ratio": _safe_div(_roll(dc, 24, np.std), _roll(dc, 240, np.std)),
        "range_pos24": _safe_div(c - lo24, hi24 - lo24),
        "range_pos120": _safe_div(c - lo120, hi120 - lo120),
        "brk_hi120": _safe_div(c - prior_hi120, atr24),
        "brk_lo120": _safe_div(c - prior_lo120, atr24),
        "spread_rel": _safe_div(series.spread_mean.astype(float), atr24),
        "tick_activity": _safe_div(_roll(ticks, 24, np.mean), _roll(ticks, 240, np.mean)),
        "hour_sin": np.sin(2 * np.pi * close_hour / 24),
        "hour_cos": np.cos(2 * np.pi * close_hour / 24),
        "bar_body": _safe_div(c - o, h - l),
        "smc_hi_dist": _safe_div(c - sw_hi, atr24),
        "smc_lo_dist": _safe_div(c - sw_lo, atr24),
        "smc_structure": np.sign(sw_hi - sw_hi_prev) + np.sign(sw_lo - sw_lo_prev),
        "smc_sweep": np.where(np.isfinite(sw_lo) & (l < sw_lo) & (c > sw_lo), 1.0,
                     np.where(np.isfinite(sw_hi) & (h > sw_hi) & (c < sw_hi), -1.0,
                     np.where(np.isfinite(sw_lo) | np.isfinite(sw_hi), 0.0, np.nan))),
    }
    m = np.column_stack([cols[name] for name in NAMES]) if n else np.zeros((0, len(NAMES)))
    # Every feature is NaN until its full window exists, so a row is either
    # fully defined by its window or visibly missing.
    for j, spec in enumerate(SPECS):
        m[: min(spec.window, n), j] = np.nan
    return m


@dataclass(frozen=True)
class FeatureVector:
    """Features as known at `timestamp`, with provenance (DATA_CONTRACT.md §2)."""

    version: str
    timestamp: int  # decision time: the close of the last bar used
    bar_open_time: int
    instrument: str
    timeframe: str
    source: str
    values: dict[str, float]
    missing: tuple[str, ...]
    metadata: dict = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        return not self.missing

    def array(self, names: tuple[str, ...] = NAMES) -> np.ndarray:
        return np.array([self.values.get(n, np.nan) for n in names], dtype=float)

    def as_dict(self) -> dict:
        return {
            "version": self.version, "timestamp": self.timestamp,
            "time": datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat(),
            "instrument": self.instrument, "timeframe": self.timeframe, "source": self.source,
            "values": {k: (None if not np.isfinite(v) else round(float(v), 6)) for k, v in self.values.items()},
            "missing": list(self.missing), "metadata": self.metadata,
        }


def compute_at(series: BarSeries, t: int) -> FeatureVector:
    """Features at decision time `t` from bars CLOSED by t — the production path.

    Uses only the last LOOKBACK closed bars, exactly as the live system does.
    """
    known = series.as_of(t)
    window = known.take(slice(max(0, len(known) - LOOKBACK), len(known)))
    if len(window) == 0:
        return FeatureVector(FEATURE_VERSION, t, 0, series.symbol, series.timeframe, series.source,
                             {n: np.nan for n in NAMES}, NAMES, {"bars": 0})
    row = compute_matrix(window)[-1]
    values = {n: float(row[i]) for i, n in enumerate(NAMES)}
    missing = tuple(n for n in NAMES if not np.isfinite(values[n]))
    return FeatureVector(
        FEATURE_VERSION, t, int(window.open_time[-1]), series.symbol, series.timeframe,
        series.source, values, missing,
        {"bars": len(window), "lookback": LOOKBACK, "swing_k": SWING_K,
         "stale_seconds": int(t - window.available_at[-1])},
    )
