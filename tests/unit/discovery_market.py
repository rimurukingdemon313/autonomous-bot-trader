"""Synthetic markets for the discovery tests, built so the right answer is known in advance.

`planted()` is flat noise in which, on every `every`-th bar of each instrument, a feature `A` is
set to 2 ("high") and price then rises `drift` per bar for six bars (and gives it back 20 bars
later, so there is no overall trend for other cells to ride). So BUY-after-A-high is a real,
profitable pattern by construction, SELL-after-A-high loses, and every other cell of any grid is
noise. `plant=False` builds the same market without the effect (the null world).
"""

from __future__ import annotations

import numpy as np

from aitrader.data.bars import BarSeries
from aitrader.research.discovery.study import SymbolData
from aitrader.research.labels import atr24

T0 = 1_262_563_200  # 2010-01-04 00:00 UTC, a Monday
SYMBOLS = ("AAA", "BBB", "CCC")


def series(symbol, mid, rng, wick=0.0001, half=0.00001, t0=T0, timeframe="H1"):
    n = len(mid)
    step = {"H1": 3600, "D1": 86400}[timeframe]
    o = np.concatenate(([mid[0]], mid[:-1]))
    w = np.abs(rng.normal(0, wick, n))
    hi, lo = np.maximum(o, mid) + w, np.minimum(o, mid) - w
    return BarSeries.from_columns(symbol, timeframe, "synthetic", open_time=t0 + step * np.arange(n),
                                  bid_open=o - half, bid_high=hi - half, bid_low=lo - half, bid_close=mid - half,
                                  ask_open=o + half, ask_high=hi + half, ask_low=lo + half, ask_close=mid + half,
                                  ticks=rng.integers(50, 500, n), spread_mean=np.full(n, 2 * half),
                                  spread_max=np.full(n, 4 * half))


def planted(symbols=SYMBOLS, n=3000, every=40, drift=0.0003, noise=0.0002, seed=1, plant=True, t0=T0,
            weak=(), regime_flip=False, timeframe="H1"):
    """dict symbol -> SymbolData with columns A (0/1 random, 2 at a signal), B (uniform noise) and
    er120 / vol_ratio (uniform, for regime cells). Symbols in `weak` get no effect; with
    `regime_flip` the effect REVERSES (price falls) at signals where er120 < 0.5."""
    out = {}
    for k, sym in enumerate(symbols):
        rng = np.random.default_rng(seed * 100 + k)
        er = rng.random(n)
        steps = rng.normal(0, noise, n)
        sig = np.arange(50 + k, n - 60, every)
        if plant and sym not in weak:
            for s in sig:
                d = -drift if regime_flip and er[s] < 0.5 else drift
                steps[s + 1: s + 7] += d  # the effect: six bars in its direction after the signal ...
                steps[s + 21: s + 27] -= d  # ... given back later, so the market has no overall trend
        mid = 1.1 + np.cumsum(steps)
        s_ = series(sym, mid, rng, t0=t0, timeframe=timeframe)
        a = rng.integers(0, 2, n).astype(float)
        a[sig] = 2.0
        cols = {"A": a, "B": rng.random(n), "er120": er, "vol_ratio": rng.random(n)}
        out[sym] = SymbolData(sym, s_, 0.0001, cols, atr24(s_))
    return out
