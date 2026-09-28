"""The market map: the structure a price-action trader reads off a chart, computed, not guessed.

Given to the model traders so they do not have to infer it from rows of numbers:

- swings and market structure (HH/HL, LH/LL), and the latest break of structure:
  BOS when it continues the trend, CHoCH when it changes it;
- the order block behind that break (the last opposite candle before the move);
- fair value gaps (three-candle imbalances) that price has not yet filled;
- resting liquidity: equal highs / equal lows that have not been taken, and the
  latest sweep (a wick through a swing that closed back inside);
- previous day / previous week high and low, today's range and each session's
  range (Asia 00-07, London 07-12, New York 12-21 UTC), and round numbers.

No look-ahead, by construction: only bars that closed at or before `as_of` are
used; a swing needs K bars on each side, so it exists only once those K bars
have closed; FVG fills, order-block tests and sweeps are found by walking the
later bars forward, never by looking at a final value. Distances are in the
timeframe's own ATR(14), so they read the same on every pair.

Information for the team, never an instruction: nothing here trades.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from ..data.bars import BarSeries
from ..data.resample import resample

MAP_VERSION = "market-map-1.0.0"
K = 2                    # a swing needs K lower highs (higher lows) on each side
EQUAL_TOL_ATR = 0.10     # two swings this close are "equal": liquidity rests beyond them
MIN_FVG_ATR = 0.10       # smaller gaps are noise
SESSIONS = (("asia", 0, 7), ("london", 7, 12), ("new_york", 12, 21))


def _digits(symbol: str) -> int:
    return 3 if symbol.endswith("JPY") else 5


def _t(ts: float) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%d %H:%M")


def _completed(bars: BarSeries | None, as_of: int) -> BarSeries | None:
    if bars is None or len(bars) == 0:
        return None
    n = int((bars.available_at <= as_of).sum())
    return bars.take(slice(0, n)) if n else None


def _atr(h, lo, c, n=14) -> float:
    pc = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - lo, np.maximum(abs(h - pc), abs(lo - pc)))
    return float(tr[-min(n, len(tr)):].mean())


def swings(h: np.ndarray, lo: np.ndarray, k: int = K) -> tuple[list[int], list[int]]:
    """Indices of confirmed swing highs and lows: bar i is a swing high when its high is above the
    k bars before it and not below the k bars after it (all of which have closed)."""
    n = len(h)
    highs = [i for i in range(k, n - k) if h[i] > h[i - k:i].max() and h[i] >= h[i + 1:i + k + 1].max()]
    lows = [i for i in range(k, n - k) if lo[i] < lo[i - k:i].min() and lo[i] <= lo[i + 1:i + k + 1].min()]
    return highs, lows


def _structure(bars: BarSeries, d: int) -> dict:
    o, h, lo, c = bars.mid_open, bars.mid_high, bars.mid_low, bars.mid_close
    t, n = bars.open_time, len(bars)
    atr = _atr(h, lo, c)
    sh, sl = swings(h, lo)
    trend = "range"
    if len(sh) >= 2 and len(sl) >= 2:
        hh, hl = h[sh[-1]] > h[sh[-2]], lo[sl[-1]] > lo[sl[-2]]
        trend = "up (HH+HL)" if hh and hl else "down (LH+LL)" if not hh and not hl else "range (mixed swings)"

    # Walk forward: at bar j only swings confirmed by j (index + K <= j) may be broken.
    state, last, broken_h, broken_l = None, None, set(), set()
    for j in range(n):
        avail_h = [i for i in sh if i + K <= j and i not in broken_h]
        avail_l = [i for i in sl if i + K <= j and i not in broken_l]
        if avail_h and c[j] > h[avail_h[-1]]:
            i = avail_h[-1]
            broken_h.update(x for x in avail_h if h[x] < c[j])
            last = {"kind": "BOS" if state == "up" else "CHoCH", "direction": "bullish", "level": round(float(h[i]), d),
                    "at_bar": j, "swing": i}
            state = "up"
        elif avail_l and c[j] < lo[avail_l[-1]]:
            i = avail_l[-1]
            broken_l.update(x for x in avail_l if lo[x] > c[j])
            last = {"kind": "BOS" if state == "down" else "CHoCH", "direction": "bearish", "level": round(float(lo[i]), d),
                    "at_bar": j, "swing": i}
            state = "down"

    out: dict = {"atr": round(atr, d + 1), "trend": trend,
                 "last_swing_high": round(float(h[sh[-1]]), d) if sh else None,
                 "last_swing_low": round(float(lo[sl[-1]]), d) if sl else None, "last_break": None, "order_block": None}
    if last is None:
        return out
    j = last["at_bar"]
    out["last_break"] = {"kind": last["kind"], "direction": last["direction"], "level": last["level"],
                         "time": _t(t[j]), "bars_ago": n - 1 - j}
    # The order block: the last opposite-coloured candle before the move that broke structure.
    bull = last["direction"] == "bullish"
    ob = next((i for i in range(j - 1, max(last["swing"] - 1, j - 25, -1), -1)
               if (c[i] < o[i] if bull else c[i] > o[i])), None)
    if ob is not None:
        lo_z, hi_z = float(lo[ob]), float(h[ob])
        status = "untested"
        for x in range(j + 1, n):  # walk forward: tested when price comes back into it, broken when it closes through
            if (c[x] < lo_z) if bull else (c[x] > hi_z):
                status = "broken"
                break
            if (lo[x] <= hi_z) if bull else (h[x] >= lo_z):
                status = "tested"
        mid = (lo_z + hi_z) / 2
        out["order_block"] = {"side": "demand" if bull else "supply", "low": round(lo_z, d), "high": round(hi_z, d),
                              "time": _t(t[ob]), "status": status,
                              "distance_atr": round((c[-1] - mid) / atr, 2) if atr > 0 else None}
    return out


def _fvgs(bars: BarSeries, d: int, keep: int = 3) -> list[dict]:
    h, lo, c, t = bars.mid_high, bars.mid_low, bars.mid_close, bars.open_time
    atr, n, found = _atr(h, lo, c), len(bars), []
    for i in range(2, n):
        if lo[i] > h[i - 2] and lo[i] - h[i - 2] >= MIN_FVG_ATR * atr:
            bottom, top, side = float(h[i - 2]), float(lo[i]), "bullish"
        elif h[i] < lo[i - 2] and lo[i - 2] - h[i] >= MIN_FVG_ATR * atr:
            bottom, top, side = float(h[i]), float(lo[i - 2]), "bearish"
        else:
            continue
        status = "open"
        for x in range(i + 1, n):  # walk forward: entered = mitigated, traded through = filled
            inside = lo[x] <= top if side == "bullish" else h[x] >= bottom
            through = lo[x] <= bottom if side == "bullish" else h[x] >= top
            if through:
                status = "filled"
                break
            if inside:
                status = "mitigated"
        if status != "filled":
            found.append({"side": side, "low": round(bottom, d), "high": round(top, d), "time": _t(t[i - 1]),
                          "status": status,
                          "distance_atr": round((c[-1] - (bottom + top) / 2) / atr, 2) if atr > 0 else None})
    return sorted(found, key=lambda f: abs(f["distance_atr"] or 0))[:keep]


def _liquidity(bars: BarSeries, d: int) -> dict:
    h, lo, c, t = bars.mid_high, bars.mid_low, bars.mid_close, bars.open_time
    atr, n = _atr(h, lo, c), len(bars)
    sh, sl = swings(h, lo)
    tol = EQUAL_TOL_ATR * atr

    def equal(idx, arr, above):
        """Swings within tolerance of each other form one pool (touches = how many); a pool counts
        only while no later bar has traded beyond it."""
        pools, used = [], set()
        for a in range(len(idx)):
            if a in used:
                continue
            members = [b for b in range(a, len(idx)) if b not in used and abs(arr[idx[b]] - arr[idx[a]]) <= tol]
            if len(members) < 2:
                continue
            used.update(members)
            pts = [idx[b] for b in members]
            level = max(arr[i] for i in pts) if above else min(arr[i] for i in pts)
            later = h[pts[-1] + 1:] if above else lo[pts[-1] + 1:]
            taken = bool(len(later)) and (later.max() > level if above else later.min() < level)
            if not taken:
                pools.append({"level": round(float(level), d), "touches": len(pts), "since": _t(t[pts[0]]),
                              "distance_atr": round((level - c[-1]) / atr, 2) if atr > 0 else None})
        return sorted(pools, key=lambda p: abs(p["distance_atr"] or 0))[:2]

    sweep = None
    for j in range(max(K + 1, n - 12), n):  # a wick through a confirmed swing that closed back inside
        prior_h = [i for i in sh if i + K < j]
        prior_l = [i for i in sl if i + K < j]
        if prior_h and h[j] > h[prior_h[-1]] and c[j] < h[prior_h[-1]]:
            sweep = {"side": "swept highs (bearish signal)", "level": round(float(h[prior_h[-1]]), d),
                     "time": _t(t[j]), "bars_ago": n - 1 - j}
        if prior_l and lo[j] < lo[prior_l[-1]] and c[j] > lo[prior_l[-1]]:
            sweep = {"side": "swept lows (bullish signal)", "level": round(float(lo[prior_l[-1]]), d),
                     "time": _t(t[j]), "bars_ago": n - 1 - j}
    return {"equal_highs": equal(sh, h, True), "equal_lows": equal(sl, lo, False), "last_sweep": sweep}


def _levels(h1: BarSeries, as_of: int, d: int, symbol: str) -> dict:
    out: dict = {}
    try:
        d1 = resample(h1, "D1", as_of=as_of)
    except ValueError:
        d1 = None
    if d1 is not None and len(d1):
        out["previous_day"] = {"high": round(float(d1.mid_high[-1]), d), "low": round(float(d1.mid_low[-1]), d),
                               "date": datetime.fromtimestamp(int(d1.open_time[-1]), timezone.utc).strftime("%Y-%m-%d")}
        weeks = [datetime.fromtimestamp(int(x), timezone.utc).isocalendar()[:2] for x in d1.open_time]
        this_week = datetime.fromtimestamp(as_of, timezone.utc).isocalendar()[:2]
        prev = sorted({w for w in weeks if w < this_week})
        if prev:
            m = np.array([w == prev[-1] for w in weeks])
            out["previous_week"] = {"high": round(float(d1.mid_high[m].max()), d), "low": round(float(d1.mid_low[m].min()), d)}
    day0 = as_of - as_of % 86400
    today = h1.open_time >= day0
    if today.any():
        out["today"] = {"high": round(float(h1.mid_high[today].max()), d), "low": round(float(h1.mid_low[today].min()), d)}
        hours = (h1.open_time - day0) // 3600
        for name, a, b in SESSIONS:
            m = today & (hours >= a) & (hours < b)
            if m.any():
                out.setdefault("sessions_today", {})[name] = {"high": round(float(h1.mid_high[m].max()), d),
                                                              "low": round(float(h1.mid_low[m].min()), d)}
    hour = datetime.fromtimestamp(as_of, timezone.utc).hour
    out["session_now"] = next((nm for nm, a, b in SESSIONS if a <= hour < b), "off-hours (21-24 UTC)")
    step = 0.5 if symbol.endswith("JPY") else 0.005  # round numbers: the half and whole figures
    px = float(h1.mid_close[-1])
    below = np.floor(px / step) * step
    out["round_numbers"] = {"below": round(float(below), d), "above": round(float(below + step), d)}
    return out


def market_map(symbol: str, h1: BarSeries | None, lower: dict | None, as_of: int) -> dict | None:
    """The map for `symbol` as of `as_of`, from completed bars only; None when there is no H1 history."""
    h1 = _completed(h1, as_of)
    if h1 is None or len(h1) < 30:
        return None
    d = _digits(symbol)
    frames = {tf: _completed(b, as_of) for tf, b in (lower or {}).items() if tf in ("M5", "M15")}
    frames["H1"] = h1.take(slice(max(0, len(h1) - 240), len(h1)))
    out: dict = {"version": MAP_VERSION, "price": round(float(h1.mid_close[-1]), d),
                 "note": "computed from completed bars; distances in that timeframe's ATR(14), negative = below price",
                 "structure": {}, "fair_value_gaps": {}, "liquidity": {}}
    finest = next((frames[tf] for tf in ("M5", "M15") if frames.get(tf) is not None and len(frames[tf])), h1)
    out["price"] = round(float(finest.mid_close[-1]), d)  # the latest completed close, finest timeframe
    for tf in ("M5", "M15", "H1"):
        b = frames.get(tf)
        if b is None or len(b) < 10 + 2 * K:
            continue
        b = b.take(slice(max(0, len(b) - 120), len(b)))
        out["structure"][tf] = _structure(b, d)
        out["fair_value_gaps"][tf] = _fvgs(b, d)
        if tf in ("M15", "H1"):
            out["liquidity"][tf] = _liquidity(b, d)
    out["levels"] = _levels(h1, as_of, d, symbol)
    return out
