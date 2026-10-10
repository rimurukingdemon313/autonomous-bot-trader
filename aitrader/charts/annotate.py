"""What the chart marks, computed from completed bars only and walked forward bar by bar.

The same detectors as the market map (`features/market_map.py`: confirmed swings with K bars on each side,
walk-forward BOS/CHoCH, order blocks, fair value gaps, equal highs/lows, sweeps), kept with their bar
indices so they can be drawn where they happened, plus support/resistance clusters and displacement
candles. Nothing here can see a bar after the last one it is given: a swing exists only once its K
following bars have closed, a fill, test or sweep is found by walking the later bars forward, and every ATR
used at bar i is computed from bars up to i.
"""

from __future__ import annotations

import numpy as np

from ..data.bars import BarSeries
from ..features.market_map import EQUAL_TOL_ATR, K, MIN_FVG_ATR, swings

ANNOTATE_VERSION = "chart-annotate-1.0.0"
DISPLACEMENT_BODY_ATR = 1.5   # a candle whose body is at least this many ATR(14) of the bars before it
DISPLACEMENT_BODY_SHARE = 0.6  # ... and at least this share of its own range
SR_TOL_ATR = 0.25             # swing prices this close form one support/resistance level
SR_MIN_TOUCHES = 2


def atr_path(h: np.ndarray, lo: np.ndarray, c: np.ndarray, n: int = 14) -> np.ndarray:
    """ATR(14) at every bar from that bar and the ones before it (a simple mean of true ranges)."""
    pc = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - lo, np.maximum(abs(h - pc), abs(lo - pc)))
    cs = np.concatenate(([0.0], np.cumsum(tr)))
    idx = np.arange(1, len(tr) + 1)
    start = np.maximum(0, idx - n)
    return (cs[idx] - cs[start]) / (idx - start)


def _trend(h, lo, sh, sl) -> str:
    if len(sh) >= 2 and len(sl) >= 2:
        hh, hl = h[sh[-1]] > h[sh[-2]], lo[sl[-1]] > lo[sl[-2]]
        return "UP (HH+HL)" if hh and hl else "DOWN (LH+LL)" if not hh and not hl else "RANGE (MIXED SWINGS)"
    return "RANGE"


def annotate(bars: BarSeries) -> dict:
    o, h, lo, c = bars.mid_open, bars.mid_high, bars.mid_low, bars.mid_close
    n = len(bars)
    atr_i = atr_path(h, lo, c)
    atr = float(atr_i[-1])
    sh, sl = swings(h, lo)

    pts = []
    for kind, idx, arr in (("high", sh, h), ("low", sl, lo)):
        for a, i in enumerate(idx):
            prev = arr[idx[a - 1]] if a else None
            if kind == "high":
                label = "H" if prev is None else ("HH" if arr[i] > prev else "LH")
            else:
                label = "L" if prev is None else ("HL" if arr[i] > prev else "LL")
            pts.append({"i": int(i), "kind": kind, "price": float(arr[i]), "label": label, "confirmed_at": int(i + K)})
    pts.sort(key=lambda p: p["i"])

    # BOS / CHoCH, walked forward: at bar j only swings confirmed by j may be broken
    events, state, broken_h, broken_l = [], None, set(), set()
    for j in range(n):
        avail_h = [i for i in sh if i + K <= j and i not in broken_h]
        avail_l = [i for i in sl if i + K <= j and i not in broken_l]
        if avail_h and c[j] > h[avail_h[-1]]:
            i = avail_h[-1]
            broken_h.update(x for x in avail_h if h[x] < c[j])
            events.append({"kind": "BOS" if state == "up" else "CHOCH", "dir": "bullish", "level": float(h[i]),
                           "swing": int(i), "at": j})
            state = "up"
        elif avail_l and c[j] < lo[avail_l[-1]]:
            i = avail_l[-1]
            broken_l.update(x for x in avail_l if lo[x] > c[j])
            events.append({"kind": "BOS" if state == "down" else "CHOCH", "dir": "bearish", "level": float(lo[i]),
                           "swing": int(i), "at": j})
            state = "down"

    ob = None
    if events:
        last = events[-1]
        j, bull = last["at"], last["dir"] == "bullish"
        k = next((i for i in range(j - 1, max(last["swing"] - 1, j - 25, -1), -1)
                  if (c[i] < o[i] if bull else c[i] > o[i])), None)
        if k is not None:
            z_lo, z_hi = float(lo[k]), float(h[k])
            status, end = "untested", n - 1
            for x in range(j + 1, n):
                if (c[x] < z_lo) if bull else (c[x] > z_hi):
                    status, end = "broken", x
                    break
                if (lo[x] <= z_hi) if bull else (h[x] >= z_lo):
                    status = "tested"
            ob = {"side": "demand" if bull else "supply", "i": int(k), "end": int(end), "low": z_lo, "high": z_hi,
                  "status": status}

    fvgs = []
    for i in range(2, n):
        a_i = atr_i[i]
        if lo[i] > h[i - 2] and lo[i] - h[i - 2] >= MIN_FVG_ATR * a_i:
            bottom, top, side = float(h[i - 2]), float(lo[i]), "bullish"
        elif h[i] < lo[i - 2] and lo[i - 2] - h[i] >= MIN_FVG_ATR * a_i:
            bottom, top, side = float(h[i]), float(lo[i - 2]), "bearish"
        else:
            continue
        status, end = "open", n - 1
        for x in range(i + 1, n):
            inside = lo[x] <= top if side == "bullish" else h[x] >= bottom
            through = lo[x] <= bottom if side == "bullish" else h[x] >= top
            if through:
                status, end = "filled", x
                break
            if inside:
                status = "mitigated"
        fvgs.append({"side": side, "i": i - 1, "end": int(end), "low": bottom, "high": top, "status": status})

    tol = EQUAL_TOL_ATR * atr
    pools = []
    for kind, idx, arr, above in (("EQH", sh, h, True), ("EQL", sl, lo, False)):
        used: set = set()
        for a in range(len(idx)):
            if a in used:
                continue
            members = [b for b in range(a, len(idx)) if b not in used and abs(arr[idx[b]] - arr[idx[a]]) <= tol]
            if len(members) < 2:
                continue
            used.update(members)
            mp = [idx[b] for b in members]
            level = float(max(arr[i] for i in mp) if above else min(arr[i] for i in mp))
            later = h[mp[-1] + 1:] if above else lo[mp[-1] + 1:]
            if len(later) and (later.max() > level if above else later.min() < level):
                continue  # already taken
            pools.append({"kind": kind, "level": level, "touches": len(mp), "i": int(mp[0])})

    sweeps = []
    for j in range(K + 1, n):  # a wick through a confirmed swing that closed back inside
        prior_h = [i for i in sh if i + K < j]
        prior_l = [i for i in sl if i + K < j]
        if prior_h and h[j] > h[prior_h[-1]] and c[j] < h[prior_h[-1]]:
            sweeps.append({"side": "highs", "signal": "bearish", "level": float(h[prior_h[-1]]), "at": j,
                           "tip": float(h[j])})
        if prior_l and lo[j] < lo[prior_l[-1]] and c[j] > lo[prior_l[-1]]:
            sweeps.append({"side": "lows", "signal": "bullish", "level": float(lo[prior_l[-1]]), "at": j,
                           "tip": float(lo[j])})

    # support / resistance: clusters of confirmed swing prices, strongest (most touches) first
    prices = sorted([(float(h[i]), int(i)) for i in sh] + [(float(lo[i]), int(i)) for i in sl])
    levels, group = [], []
    for p in prices:
        if group and p[0] - group[0][0] > SR_TOL_ATR * atr:
            levels.append(group)
            group = []
        group.append(p)
    if group:
        levels.append(group)
    sr = [{"level": float(np.mean([g[0] for g in grp])), "touches": len(grp), "last": max(g[1] for g in grp)}
          for grp in levels if len(grp) >= SR_MIN_TOUCHES]

    disp = []
    for i in range(1, n):
        body, rng = abs(c[i] - o[i]), h[i] - lo[i]
        ref = atr_i[i - 1]
        if ref > 0 and rng > 0 and body >= DISPLACEMENT_BODY_ATR * ref and body / rng >= DISPLACEMENT_BODY_SHARE:
            disp.append({"i": i, "dir": "bullish" if c[i] > o[i] else "bearish"})

    window = atr_i[-min(100, n):]
    pct = int(round(100 * float((window < atr).mean()))) if len(window) > 1 else None
    vol = None if pct is None else "LOW" if pct < 30 else "HIGH" if pct > 70 else "NORMAL"
    return {"version": ANNOTATE_VERSION, "n": n, "atr": atr, "trend": _trend(h, lo, sh, sl), "swings": pts,
            "events": events, "order_block": ob, "fvgs": fvgs, "pools": pools, "sweeps": sweeps, "sr": sr,
            "displacement": disp, "volatility": vol, "atr_percentile": pct}
