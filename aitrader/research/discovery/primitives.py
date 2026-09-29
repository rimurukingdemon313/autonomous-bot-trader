"""New candidate features for research dimensions the 23 production features do not cover.

Each primitive is a DECLARED, causal function of bars closed at or before the decision bar:

    dimension            primitive          definition
    session / time       session            UTC session of the bar close: 0 Asia 00-07, 1 London 07-12,
                                            2 NY overlap 12-16, 3 NY late 16-21, 4 off-hours 21-24
                         weekday            UTC weekday of the bar close, 0 = Monday
    multi-timeframe      h4_trend           (H4 close - SMA12 of H4 closes) / ATR12(H4), last H4 bar closed
                         d1_trend           (D1 close - SMA20 of D1 closes) / ATR14(D1), last D1 bar closed
    cross-asset          usd_basket         mean 24-bar move of the OTHER USD pairs, in their ATR units,
                                            signed so that + means the dollar strengthened
    correlation          usd_corr           120-bar correlation of this pair's 1-bar change with the basket's
                                            (hours where either side is missing are left out, >= 100 needed)
    lagged               lag_r24            the 24-bar move measured 24 bars earlier (yesterday's day)
    range contraction    range_contraction  24-bar high-low range / 120-bar high-low range
    range expansion      bar_range          last bar's high-low / ATR24
    regime transition    vol_shift          ATR24/ATR240 now minus its value 24 bars ago
    trend persistence    up_persistence     share of the last 24 bars that closed up
    volatility state     atr_pctile         rank of ATR24 within its last 240 values, 0..1

Nothing here is assumed to predict anything; they are candidate research dimensions only.
Point-in-time rules: higher timeframes come from buckets that CLOSED by the bar's close; other
instruments' bars are aligned on the same open time (they close at the same instant); a value
that needs more history than exists is NaN, never a default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ...data.bars import BarSeries
from ...data.resample import resample
from ...features.store import INDEX, _lag, _roll, _safe_div, compute_matrix
from .catalog import truncation_leaks

PRIMITIVES_VERSION = "primitives-1.0.0"
#: pairs whose price rises when the dollar strengthens (+1) or weakens (-1)
USD_SIGN = {"USDJPY": 1, "USDCAD": 1, "USDCHF": 1, "EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "NZDUSD": -1}
MIN_BASKET = 3


@dataclass(frozen=True)
class Primitive:
    name: str
    dimension: str
    definition: str
    kind: str  # continuous | categorical
    requires: tuple[str, ...]
    fn: Callable[[BarSeries, np.ndarray, dict], np.ndarray]  # (own H1 bars, own feature matrix, others) -> column
    categories: tuple[int, ...] = ()

    def column(self, series: BarSeries, matrix: np.ndarray | None = None, others: dict | None = None) -> np.ndarray:
        m = compute_matrix(series) if matrix is None else matrix
        return np.asarray(self.fn(series, m, others or {}), float)


def _close_hour(s: BarSeries) -> np.ndarray:
    return ((s.available_at % 86400) // 3600).astype(int)


def _session(s, m, o):
    h = _close_hour(s)
    return np.select([h < 7, h < 12, h < 16, h < 21], [0, 1, 2, 3], 4).astype(float)


def _weekday(s, m, o):
    return (((s.available_at // 86400) + 3) % 7).astype(float)  # 1970-01-01 was a Thursday


def _htf_trend(tf: str, sma: int, atr_n: int):
    def fn(s, m, o):
        if len(s) == 0:
            return np.zeros(0)
        h = resample(s, tf, as_of=int(s.available_at[-1]))
        out = np.full(len(s), np.nan)
        if len(h) == 0:  # no other early exit: the rolling windows already leave short history NaN, and a
            return out   # length threshold here made a truncated series disagree with the full one
        c, hi, lo = h.mid_close, h.mid_high, h.mid_low
        pc = _lag(c, 1)
        tr = np.fmax(hi - lo, np.fmax(np.abs(hi - pc), np.abs(lo - pc)))
        tr[0] = np.nan
        val = _safe_div(c - _roll(c, sma, np.mean), _roll(tr, atr_n, np.mean))
        k = np.searchsorted(h.available_at, s.available_at, side="right") - 1  # last HTF bar closed by then
        ok = k >= 0
        out[ok] = val[k[ok]]
        return out
    return fn


def _aligned(s: BarSeries, other: BarSeries, col: np.ndarray) -> np.ndarray:
    """`col` of another instrument at the same open time as each of s's bars (NaN where it has none)."""
    pos = np.searchsorted(other.open_time, s.open_time)
    pos = np.clip(pos, 0, max(len(other) - 1, 0))
    out = np.full(len(s), np.nan)
    if len(other):
        hit = other.open_time[pos] == s.open_time
        out[hit] = col[pos[hit]]
    return out


class Others(dict):
    """Other instruments' H1 bars by symbol, each feature matrix computed once and reused."""

    def __init__(self, series: dict) -> None:
        super().__init__(series)
        self._matrices: dict[str, np.ndarray] = {}

    def matrix(self, symbol: str) -> np.ndarray:
        if symbol not in self._matrices:
            self._matrices[symbol] = compute_matrix(self[symbol])
        return self._matrices[symbol]


def _matrix(o: dict, symbol: str) -> np.ndarray:
    return o.matrix(symbol) if isinstance(o, Others) else compute_matrix(o[symbol])


def _basket(s: BarSeries, o: dict, column: str) -> np.ndarray:
    parts = []
    for sym, sign in USD_SIGN.items():
        if sym == s.symbol or sym not in o:
            continue
        parts.append(sign * _aligned(s, o[sym], _matrix(o, sym)[:, INDEX[column]]))
    if not parts:
        return np.full(len(s), np.nan)
    stack = np.vstack(parts)
    fin = np.isfinite(stack)
    cnt = fin.sum(axis=0)
    total = np.where(fin, stack, 0.0).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cnt >= MIN_BASKET, total / cnt, np.nan)


def _usd_basket(s, m, o):
    return _basket(s, o, "r24")


CORR_WINDOW, CORR_MIN_PAIRS = 120, 100


def _usd_corr(s, m, o):
    own = m[:, INDEX["r1"]]
    bask = _basket(s, o, "r1")
    n, w = len(s), CORR_WINDOW
    out = np.full(n, np.nan)
    if n < w:
        return out
    a, b = sliding_window_view(own, w), sliding_window_view(bask, w)
    both = np.isfinite(a) & np.isfinite(b)  # hours where either side has no bar are left out, not filled
    cnt = both.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ma = np.where(both, a, 0.0).sum(axis=1) / cnt
        mb = np.where(both, b, 0.0).sum(axis=1) / cnt
        da = np.where(both, a - ma[:, None], 0.0)
        db = np.where(both, b - mb[:, None], 0.0)
        num = (da * db).sum(axis=1)
        den = np.sqrt((da ** 2).sum(axis=1) * (db ** 2).sum(axis=1))
        r = np.where((cnt >= CORR_MIN_PAIRS) & (den > 0), num / den, np.nan)
    out[w - 1:] = r
    return out


def _lag_r24(s, m, o):
    return _lag(m[:, INDEX["r24"]], 24)


def _range_contraction(s, m, o):
    h, lo = s.mid_high, s.mid_low
    return _safe_div(_roll(h, 24, np.max) - _roll(lo, 24, np.min), _roll(h, 120, np.max) - _roll(lo, 120, np.min))


def _bar_range(s, m, o):
    c, h, lo = s.mid_close, s.mid_high, s.mid_low
    pc = _lag(c, 1)
    tr = np.fmax(h - lo, np.fmax(np.abs(h - pc), np.abs(lo - pc)))
    tr[:1] = np.nan
    return _safe_div(h - lo, _roll(tr, 24, np.mean))


def _vol_shift(s, m, o):
    v = m[:, INDEX["vol_ratio"]]
    return v - _lag(v, 24)


def _up_persistence(s, m, o):
    c = s.mid_close
    up = np.concatenate(([np.nan], (np.diff(c) > 0).astype(float)))
    return _roll(up, 24, np.mean)


def _atr_pctile(s, m, o):
    c, h, lo = s.mid_close, s.mid_high, s.mid_low
    pc = _lag(c, 1)
    tr = np.fmax(h - lo, np.fmax(np.abs(h - pc), np.abs(lo - pc)))
    tr[:1] = np.nan
    atr = _roll(tr, 24, np.mean)
    n, w = len(s), 240
    out = np.full(n, np.nan)
    if n < w:
        return out
    win = sliding_window_view(atr, w)
    last = win[:, -1:]
    ok = np.all(np.isfinite(win), axis=1)
    out[w - 1:] = np.where(ok, (win <= last).mean(axis=1), np.nan)
    return out


PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("session", "session/time", "UTC session of the bar close: 0 Asia 00-07, 1 London 07-12, "
              "2 NY overlap 12-16, 3 NY late 16-21, 4 off-hours 21-24", "categorical", ("own bars",), _session,
              (0, 1, 2, 3, 4)),
    Primitive("weekday", "session/time", "UTC weekday of the bar close, 0 = Monday (6 = Sunday evening open)",
              "categorical", ("own bars",), _weekday, (0, 1, 2, 3, 4, 6)),
    Primitive("h4_trend", "multi-timeframe", "(H4 close - SMA12(H4 close)) / ATR12(H4), from the last H4 bar closed",
              "continuous", ("own bars",), _htf_trend("H4", 12, 12)),
    Primitive("d1_trend", "multi-timeframe", "(D1 close - SMA20(D1 close)) / ATR14(D1), from the last D1 bar closed",
              "continuous", ("own bars",), _htf_trend("D1", 20, 14)),
    Primitive("usd_basket", "cross-asset", "mean r24 of the OTHER USD pairs signed so that + = dollar stronger "
              "(needs at least 3 pairs at that hour)", "continuous", ("own bars", "USD pairs H1"), _usd_basket),
    Primitive("usd_corr", "correlation", "Pearson correlation of r1 with the USD basket's r1 over the last 120 bars "
              "(at least 100 hours where both exist)", "continuous", ("own bars", "USD pairs H1"), _usd_corr),
    Primitive("lag_r24", "lagged", "r24 of 24 bars earlier", "continuous", ("own bars",), _lag_r24),
    Primitive("range_contraction", "range", "(24-bar high - low) / (120-bar high - low)", "continuous",
              ("own bars",), _range_contraction),
    Primitive("bar_range", "range", "(high - low) / ATR24 of the last bar", "continuous", ("own bars",), _bar_range),
    Primitive("vol_shift", "regime transition", "vol_ratio - vol_ratio 24 bars earlier", "continuous", ("own bars",),
              _vol_shift),
    Primitive("up_persistence", "trend persistence", "share of the last 24 bars closing up", "continuous",
              ("own bars",), _up_persistence),
    Primitive("atr_pctile", "volatility state", "rank of ATR24 within its last 240 values", "continuous",
              ("own bars",), _atr_pctile),
)

#: cross-sectional primitives, kept apart from PRIMITIVES so that the registered DP-001/DP-002 designs
#: (which enumerate PRIMITIVES) are unchanged; each program that uses one names it explicitly
XS_VERSION = "xs-1.0.0"
XS_MIN = 6  # of the 7 USD pairs


def _xs_mom(s, m, o):
    """This pair's currency's r24 against the dollar minus the median across the 7 USD pairs,
    signed to the pair's direction (+ = buying this pair buys the relatively strong currency).
    Own bars from `s`; the others aligned on the same open time; NaN for a non-USD pair."""
    if s.symbol not in USD_SIGN:
        return np.full(len(s), np.nan)
    rows = []
    for sym, sign in USD_SIGN.items():
        col = m[:, INDEX["r24"]] if sym == s.symbol else (
            _aligned(s, o[sym], _matrix(o, sym)[:, INDEX["r24"]]) if sym in o else np.full(len(s), np.nan))
        rows.append(-sign * col)  # strength of the non-USD currency against the dollar
    stack = np.vstack(rows)
    cnt = np.isfinite(stack).sum(axis=0)
    ok = cnt >= XS_MIN
    med = np.full(len(s), np.nan)
    if ok.any():
        med[ok] = np.nanmedian(stack[:, ok], axis=0)
    own = -USD_SIGN[s.symbol] * m[:, INDEX["r24"]]
    return np.where(ok, -USD_SIGN[s.symbol] * (own - med), np.nan)


XS_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("xs_mom", "cross-sectional", "r24 of this pair's currency against the dollar minus the median of the "
              "7 USD pairs' currencies (at least 6 present), signed so + = buying the pair buys the relatively "
              "strong currency; NaN for a pair without USD", "continuous", ("own bars", "USD pairs"), _xs_mom),
)
PRIMITIVE_BY_NAME = {p.name: p for p in PRIMITIVES + XS_PRIMITIVES}


def primitive_leakage(p: Primitive, series: BarSeries, others: dict, rows) -> list[int]:
    """Rows where `p` is not causal: see catalog.truncation_leaks (own AND other instruments cut)."""
    return truncation_leaks(lambda s, o: p.column(s, None, o), series, others, rows)
