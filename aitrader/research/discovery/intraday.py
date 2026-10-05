"""ID-1: intraday M5 research on bid/ask bars (research only). id-1.0.0

Every rule here is a precise, causal function of M5 bars up to and including the signal bar's
close. Nothing is discretionary and nothing reads a later bar. Rules return SIGNALS; `simulate`
turns them into trades on bid/ask prices, with the conventions of research/labels.py and
discovery/exits.py (the project's existing fill model):

- entry at the NEXT bar's open: ASK + slippage for a buy, BID - slippage for a sell. A limit
  order fills only when the market trades THROUGH its price, at the price or a better open;
- every open position is checked bar by bar on the side it would close on (BID for a long,
  ASK for a short). A bar touching both stop and target is a STOP. A gap through the stop fills
  at the open, less slippage. A target fills at its price, never better. In a limit order's fill
  bar only the stop is checked;
- time exit at the close of the last allowed bar. A position is closed at the last bar before a
  gap longer than an hour (weekends, holidays): nothing is held through a closed market;
- commission per round trip; slippage per market fill; overnight financing per 21:00 UTC rollover
  crossed (x3 on Wednesday), at the BIS policy-rate differential minus a markup;
- one position (or pending limit order) per instrument at a time;
- the production risk engine's entry checks are applied, unchanged in spirit:
  - stop >= 3 x spread;
  - spread <= 25% of the stop;
  - round-trip cost (spread + commission + 2 x slippage) <= 25% of the stop;
  - reward:risk >= 1.2.

  A signal failing them is skipped, as the bot would skip it.

R is net of every cost and measured in units of the initial risk (entry to stop, actual fill).
Nothing here sizes a live trade: the risk engine remains the only sizing authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

INTRADAY_VERSION = "id-1.0.0"
M5 = 300
DAY_START_HOUR = 22  # trading day = 22:00 UTC -> 22:00 UTC (the retail "server day")
ROLLOVER_HOUR = 21  # financing charged per 21:00 UTC crossed (17:00 New York, standard time)


# ── panel ───────────────────────────────────────────────────────────────

@dataclass
class Bars:
    """One instrument's M5 bars with the derived, causal quantities every rule shares."""

    symbol: str
    pip: float
    t: np.ndarray  # open time, epoch seconds UTC
    bo: np.ndarray
    bh: np.ndarray
    bl: np.ndarray
    bc: np.ndarray
    ao: np.ndarray
    ah: np.ndarray
    al: np.ndarray
    ac: np.ndarray
    o: np.ndarray = field(init=False)
    h: np.ndarray = field(init=False)
    l: np.ndarray = field(init=False)
    c: np.ndarray = field(init=False)
    atr: np.ndarray = field(init=False)
    hour: np.ndarray = field(init=False)
    minute: np.ndarray = field(init=False)
    day: np.ndarray = field(init=False)  # trading-day index (22:00 UTC boundary)
    utc_day: np.ndarray = field(init=False)
    weekday: np.ndarray = field(init=False)  # of the bar's UTC date, 0 = Monday
    gap_after: np.ndarray = field(init=False)  # the next bar starts more than an hour later

    def __post_init__(self) -> None:
        self.o, self.h = (self.bo + self.ao) / 2, (self.bh + self.ah) / 2
        self.l, self.c = (self.bl + self.al) / 2, (self.bc + self.ac) / 2
        self.atr = atr(self.h, self.l, self.c, 14)
        self.hour = (self.t // 3600) % 24
        self.minute = (self.t // 60) % 60
        self.utc_day = self.t // 86400
        self.day = (self.t + (24 - DAY_START_HOUR) * 3600) // 86400
        self.weekday = (self.utc_day + 3) % 7
        nxt = np.r_[self.t[1:], self.t[-1] + 10 * 86400]
        self.gap_after = (nxt - self.t) > 3600

    def __len__(self) -> int:
        return len(self.t)

    def slice(self, lo: int, hi: int) -> "Bars":
        return Bars(self.symbol, self.pip, *(getattr(self, k)[lo:hi] for k in
                                             ("t", "bo", "bh", "bl", "bc", "ao", "ah", "al", "ac")))


def atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    """Mean true range of the last n bars, through bar t (NaN until n bars exist)."""
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    cs = np.cumsum(np.r_[0.0, tr])
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        out[n - 1:] = (cs[n:] - cs[:-n]) / n
    return out


def rolling_max(x: np.ndarray, n: int) -> np.ndarray:
    """max(x[t-n+1..t]) (NaN until n values exist)."""
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = sliding_window_view(x, n).max(axis=1)
    return out


def rolling_min(x: np.ndarray, n: int) -> np.ndarray:
    return -rolling_max(-x, n)


def ema(x: np.ndarray, n: int) -> np.ndarray:
    a = 2.0 / (n + 1)
    out = np.empty(len(x))
    v = x[0]
    for i, xi in enumerate(x):
        v = a * xi + (1 - a) * v if i else xi
        out[i] = v
    return out


def swings(h: np.ndarray, l: np.ndarray, k: int = 3):
    """Fractal swing points. A swing high at i (h[i] above the k bars on each side) is CONFIRMED at
    bar i + k, the first bar at which it is known. Returns, per bar t, the last two confirmed
    swing highs/lows known at t: (sh1, sh2, sl1, sl2), sh1 the most recent (NaN when none)."""
    n = len(h)
    is_hi = np.zeros(n, bool)
    is_lo = np.zeros(n, bool)
    for i in range(k, n - k):
        if h[i] > h[i - k:i].max() and h[i] > h[i + 1:i + k + 1].max():
            is_hi[i] = True
        if l[i] < l[i - k:i].min() and l[i] < l[i + 1:i + k + 1].min():
            is_lo[i] = True
    sh1, sh2, sl1, sl2 = (np.full(n, np.nan) for _ in range(4))
    a1 = a2 = b1 = b2 = np.nan
    for t in range(n):
        i = t - k  # the swing confirmed at t
        if i >= 0 and is_hi[i]:
            a2, a1 = a1, h[i]
        if i >= 0 and is_lo[i]:
            b2, b1 = b1, l[i]
        sh1[t], sh2[t], sl1[t], sl2[t] = a1, a2, b1, b2
    return sh1, sh2, sl1, sl2


# ── signals ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Signal:
    i: int  # signal bar (decision at its close)
    side: int  # +1 buy, -1 sell
    stop: float  # absolute price
    target: float  # absolute price
    max_bars: int  # bars held after entry before a time exit
    limit: float | None = None  # None = market at the next open
    valid: int = 0  # bars a limit order stays working
    deadline_hour: int | None = None  # time exit at the first bar at/after this UTC hour of the entry day


def _window(b: Bars, lo: int, hi: int) -> np.ndarray:
    """Bars opening in [lo:00, hi:00) UTC, Monday to Friday, with a finite ATR."""
    return (b.hour >= lo) & (b.hour < hi) & (b.weekday < 5) & np.isfinite(b.atr) & (b.atr > 0)


def _r_target(entry_ref: float, stop: float, side: int, r: float) -> float:
    return entry_ref + side * r * abs(entry_ref - stop)


def prev_day_levels(b: Bars):
    """High/low of the previous trading day (22:00 UTC boundary), known from its last bar's close."""
    days, start = np.unique(b.day, return_index=True)
    hi = np.maximum.reduceat(b.h, start)
    lo = np.minimum.reduceat(b.l, start)
    pdh, pdl = np.full(len(b), np.nan), np.full(len(b), np.nan)
    for k in range(1, len(days)):
        if days[k] - days[k - 1] <= 3:  # the previous trading day, across a weekend
            end = start[k + 1] if k + 1 < len(days) else len(b)
            pdh[start[k]:end], pdl[start[k]:end] = hi[k - 1], lo[k - 1]
    return pdh, pdl


def sweep_pd(b: Bars, pen: float = 0.10, buf: float = 0.10, r: float = 2.0, hold: int = 48) -> list[Signal]:
    """A1: previous-day high/low stop-run reversal. Short when a bar trades >= pen x ATR above the
    previous day's high and CLOSES back below it; stop beyond the bar's extreme + buf x ATR; 2R;
    first sweep of each level per day; entries 07:00-20:00 UTC. Mirror for the low."""
    pdh, pdl = prev_day_levels(b)
    ok = _window(b, 7, 20)
    out, used = [], set()
    for i in np.flatnonzero(ok & np.isfinite(pdh)):
        a = b.atr[i]
        if b.h[i] >= pdh[i] + pen * a and b.c[i] < pdh[i] and (b.day[i], -1) not in used:
            used.add((b.day[i], -1))
            st = b.h[i] + buf * a
            out.append(Signal(i, -1, st, _r_target(b.c[i], st, -1, r), hold))
        elif b.l[i] <= pdl[i] - pen * a and b.c[i] > pdl[i] and (b.day[i], 1) not in used:
            used.add((b.day[i], 1))
            st = b.l[i] - buf * a
            out.append(Signal(i, 1, st, _r_target(b.c[i], st, 1, r), hold))
    return out


def sweep_asia(b: Bars, pen: float = 0.10, buf: float = 0.10, r: float = 2.0, hold: int = 36) -> list[Signal]:
    """A2: London sweep of the Asian range. Range = high/low of the UTC day's bars 00:00-06:55; from
    07:00 to 11:55 a bar trading >= pen x ATR beyond it and closing back inside is faded; first per
    side per day; stop beyond the bar's extreme + buf x ATR; 2R."""
    out = []
    days, start = np.unique(b.utc_day, return_index=True)
    ends = np.r_[start[1:], len(b)]
    for s, e in zip(start, ends):
        asia = np.flatnonzero(b.hour[s:e] < 7) + s
        if len(asia) < 12:
            continue
        ah, al = b.h[asia].max(), b.l[asia].min()
        done = set()
        for i in range(asia[-1] + 1, e):
            if not (7 <= b.hour[i] < 12) or b.weekday[i] >= 5 or not (b.atr[i] > 0):
                continue
            a = b.atr[i]
            if -1 not in done and b.h[i] >= ah + pen * a and b.c[i] < ah:
                done.add(-1)
                st = b.h[i] + buf * a
                out.append(Signal(i, -1, st, _r_target(b.c[i], st, -1, r), hold))
            elif 1 not in done and b.l[i] <= al - pen * a and b.c[i] > al:
                done.add(1)
                st = b.l[i] - buf * a
                out.append(Signal(i, 1, st, _r_target(b.c[i], st, 1, r), hold))
    return out


def sweep_equal(b: Bars, tol: float = 0.10, pen: float = 0.10, buf: float = 0.10, lookback: int = 72,
                r: float = 2.0, hold: int = 48, k: int = 3) -> list[Signal]:
    """A3: equal highs/lows taken out. Two CONFIRMED swing highs within the last `lookback` bars,
    within tol x ATR of each other, form a level (their max). A bar trading >= pen x ATR above it
    and closing back below is faded (mirror for lows); stop beyond the bar + buf x ATR; 2R."""
    n = len(b)
    hi_conf, lo_conf = [], []  # (confirmed bar, swing bar, price)
    for i in range(k, n - k):
        if b.h[i] > b.h[i - k:i].max() and b.h[i] > b.h[i + 1:i + k + 1].max():
            hi_conf.append((i + k, i, b.h[i]))
        if b.l[i] < b.l[i - k:i].min() and b.l[i] < b.l[i + 1:i + k + 1].min():
            lo_conf.append((i + k, i, b.l[i]))
    ok = _window(b, 7, 20)
    out = []
    hp = lp = 0
    live_h: list = []
    live_l: list = []
    used = set()
    for t in range(n):
        while hp < len(hi_conf) and hi_conf[hp][0] <= t:
            live_h.append(hi_conf[hp])
            hp += 1
        while lp < len(lo_conf) and lo_conf[lp][0] <= t:
            live_l.append(lo_conf[lp])
            lp += 1
        live_h = [x for x in live_h if x[1] >= t - lookback]
        live_l = [x for x in live_l if x[1] >= t - lookback]
        if not ok[t]:
            continue
        a = b.atr[t]
        for side, live, px in ((-1, live_h, b.h), (1, live_l, b.l)):
            if len(live) < 2:
                continue
            prices = np.array([x[2] for x in live])
            best = None
            for u in range(len(live)):
                for v in range(u + 1, len(live)):
                    if abs(prices[u] - prices[v]) <= tol * a:
                        lvl = max(prices[u], prices[v]) if side < 0 else min(prices[u], prices[v])
                        key = (live[u][1], live[v][1])
                        if key not in used:
                            best = (lvl, key)
            if best is None:
                continue
            lvl, key = best
            if side < 0 and b.h[t] >= lvl + pen * a and b.c[t] < lvl:
                used.add(key)
                st = b.h[t] + buf * a
                out.append(Signal(t, -1, st, _r_target(b.c[t], st, -1, r), hold))
                break
            if side > 0 and b.l[t] <= lvl - pen * a and b.c[t] > lvl:
                used.add(key)
                st = b.l[t] - buf * a
                out.append(Signal(t, 1, st, _r_target(b.c[t], st, 1, r), hold))
                break
    return out


def _displacement(b: Bars, i: int, body: float) -> int:
    """+1/-1 when bar i is a displacement bar (|close - open| >= body x ATR), else 0."""
    d = b.c[i] - b.o[i]
    return int(np.sign(d)) if abs(d) >= body * b.atr[i] else 0


def bos_fvg(b: Bars, body: float = 1.2, buf: float = 0.10, r: float = 2.0, hold: int = 48, valid: int = 12,
            k: int = 3) -> list[Signal]:
    """A4: break of structure with displacement, then a retest of the fair-value gap. Bullish: bar t
    closes above the last confirmed swing high, is a displacement bar, and leaves a gap
    low[t] > high[t-2]. A buy limit at low[t] (the gap's top) works for `valid` bars; stop at
    low[t-2] - buf x ATR; 2R. Mirror for bearish."""
    sh1, _, sl1, _ = swings(b.h, b.l, k)
    ok = _window(b, 7, 20)
    out = []
    for t in np.flatnonzero(ok):
        if t < 2:
            continue
        a = b.atr[t]
        d = _displacement(b, t, body)
        if d > 0 and np.isfinite(sh1[t]) and b.c[t] > sh1[t] and b.c[t - 1] <= sh1[t] and b.l[t] > b.h[t - 2]:
            lim, st = b.l[t], b.l[t - 2] - buf * a
            out.append(Signal(t, 1, st, _r_target(lim, st, 1, r), hold, limit=lim, valid=valid))
        elif d < 0 and np.isfinite(sl1[t]) and b.c[t] < sl1[t] and b.c[t - 1] >= sl1[t] and b.h[t] < b.l[t - 2]:
            lim, st = b.h[t], b.h[t - 2] + buf * a
            out.append(Signal(t, -1, st, _r_target(lim, st, -1, r), hold, limit=lim, valid=valid))
    return out


def order_block(b: Bars, body: float = 1.2, buf: float = 0.10, r: float = 2.0, hold: int = 48, valid: int = 24,
                look: int = 5, k: int = 3) -> list[Signal]:
    """A6: order-block reaction. After a displacement break of the last confirmed swing high (as
    A4), the order block is the last down-close bar among the `look` bars before t. A buy limit at
    its high works for `valid` bars; stop at its low - buf x ATR; 2R. Mirror for bearish."""
    sh1, _, sl1, _ = swings(b.h, b.l, k)
    ok = _window(b, 7, 20)
    out = []
    for t in np.flatnonzero(ok):
        if t < look + 1:
            continue
        a = b.atr[t]
        d = _displacement(b, t, body)
        if d > 0 and np.isfinite(sh1[t]) and b.c[t] > sh1[t] and b.c[t - 1] <= sh1[t]:
            cand = [j for j in range(t - look, t) if b.c[j] < b.o[j]]
            if cand:
                j = cand[-1]
                lim, st = b.h[j], b.l[j] - buf * a
                if lim < b.c[t]:
                    out.append(Signal(t, 1, st, _r_target(lim, st, 1, r), hold, limit=lim, valid=valid))
        elif d < 0 and np.isfinite(sl1[t]) and b.c[t] < sl1[t] and b.c[t - 1] >= sl1[t]:
            cand = [j for j in range(t - look, t) if b.c[j] > b.o[j]]
            if cand:
                j = cand[-1]
                lim, st = b.l[j], b.h[j] + buf * a
                if lim > b.c[t]:
                    out.append(Signal(t, -1, st, _r_target(lim, st, -1, r), hold, limit=lim, valid=valid))
    return out


def choch(b: Bars, buf: float = 0.10, r: float = 2.0, hold: int = 48, k: int = 3,
          min_atr: float = 0.5, max_atr: float = 4.0) -> list[Signal]:
    """A5: change of character. In a confirmed downtrend (last swing high below the one before, last
    swing low below the one before), a close above the last confirmed swing high is a long; stop at
    the last confirmed swing low - buf x ATR (skipped unless min_atr..max_atr ATR away); 2R.
    Mirror for uptrends."""
    sh1, sh2, sl1, sl2 = swings(b.h, b.l, k)
    ok = _window(b, 7, 20)
    out = []
    for t in np.flatnonzero(ok):
        if t < 1 or not np.isfinite(sh2[t]) or not np.isfinite(sl2[t]):
            continue
        a = b.atr[t]
        down = sh1[t] < sh2[t] and sl1[t] < sl2[t]
        up = sh1[t] > sh2[t] and sl1[t] > sl2[t]
        if down and b.c[t] > sh1[t] and b.c[t - 1] <= sh1[t]:
            st = sl1[t] - buf * a
            if min_atr * a <= b.c[t] - st <= max_atr * a:
                out.append(Signal(t, 1, st, _r_target(b.c[t], st, 1, r), hold))
        elif up and b.c[t] < sl1[t] and b.c[t - 1] >= sl1[t]:
            st = sh1[t] + buf * a
            if min_atr * a <= st - b.c[t] <= max_atr * a:
                out.append(Signal(t, -1, st, _r_target(b.c[t], st, -1, r), hold))
    return out


def failed_breakout(b: Bars, look: int = 48, pen: float = 0.10, buf: float = 0.10, r: float = 2.0,
                    hold: int = 48) -> list[Signal]:
    """B5: the price-only twin of a sweep. A bar trading >= pen x ATR above the high of the previous
    `look` bars and closing back below it is faded (mirror for lows); stop beyond the bar +
    buf x ATR; 2R."""
    hi = np.r_[np.nan, rolling_max(b.h, look)[:-1]]
    lo = np.r_[np.nan, rolling_min(b.l, look)[:-1]]
    ok = _window(b, 7, 20) & np.isfinite(hi)
    out = []
    for i in np.flatnonzero(ok):
        a = b.atr[i]
        if b.h[i] >= hi[i] + pen * a and b.c[i] < hi[i]:
            st = b.h[i] + buf * a
            out.append(Signal(i, -1, st, _r_target(b.c[i], st, -1, r), hold))
        elif b.l[i] <= lo[i] - pen * a and b.c[i] > lo[i]:
            st = b.l[i] - buf * a
            out.append(Signal(i, 1, st, _r_target(b.c[i], st, 1, r), hold))
    return out


def opening_range(b: Bars, r: float = 2.0, hold: int = 48, min_atr: float = 0.5, max_atr: float = 4.0) -> list[Signal]:
    """B1: London opening-range breakout. Range = 07:00-07:25 UTC (6 bars). From 07:30 to 10:55 the
    first close beyond it is traded in its direction; stop at the opposite side (skipped unless
    min_atr..max_atr ATR away); 2R; time exit at 16:00 UTC."""
    out = []
    days, start = np.unique(b.utc_day, return_index=True)
    ends = np.r_[start[1:], len(b)]
    for s, e in zip(start, ends):
        rng = [i for i in range(s, e) if b.hour[i] == 7 and b.minute[i] < 30]
        if len(rng) < 6 or b.weekday[s] >= 5:
            continue
        hi, lo = b.h[rng].max(), b.l[rng].min()
        for i in range(rng[-1] + 1, e):
            if not ((b.hour[i] == 7 and b.minute[i] >= 30) or 8 <= b.hour[i] < 11):
                if b.hour[i] >= 11:
                    break
                continue
            a = b.atr[i]
            if not a > 0:
                continue
            if b.c[i] > hi:
                if min_atr * a <= b.c[i] - lo <= max_atr * a:
                    out.append(Signal(i, 1, lo, _r_target(b.c[i], lo, 1, r), hold, deadline_hour=16))
                break
            if b.c[i] < lo:
                if min_atr * a <= hi - b.c[i] <= max_atr * a:
                    out.append(Signal(i, -1, hi, _r_target(b.c[i], hi, -1, r), hold, deadline_hour=16))
                break
    return out


def squeeze(b: Bars, n: int = 20, pct: float = 0.10, window: int = 1000, stop_atr: float = 1.5, r: float = 2.0,
            hold: int = 36) -> list[Signal]:
    """B2: volatility contraction then breakout. Bollinger width (n, 2 sd) of the previous bar in the
    lowest `pct` of its own trailing `window` values, and a close beyond the previous n bars'
    high/low: trade the break; stop stop_atr x ATR; 2R."""
    c = b.c
    width = rolling_std(c, n) / np.where(c > 0, c, np.nan)
    rank = rolling_rank(np.nan_to_num(width, nan=np.inf), window)
    rank[~np.isfinite(width)] = np.nan
    hi = np.r_[np.nan, rolling_max(b.h, n)[:-1]]
    lo = np.r_[np.nan, rolling_min(b.l, n)[:-1]]
    prev_rank = np.r_[np.nan, rank[:-1]]
    ok = _window(b, 7, 20) & (prev_rank <= pct) & np.isfinite(hi)
    out = []
    last = -10 ** 9
    for i in np.flatnonzero(ok):
        a = b.atr[i]
        if i - last < n:
            continue
        if b.c[i] > hi[i]:
            st = b.c[i] - stop_atr * a
            out.append(Signal(i, 1, st, _r_target(b.c[i], st, 1, r), hold))
            last = i
        elif b.c[i] < lo[i]:
            st = b.c[i] + stop_atr * a
            out.append(Signal(i, -1, st, _r_target(b.c[i], st, -1, r), hold))
            last = i
    return out


def rolling_std(x: np.ndarray, n: int) -> np.ndarray:
    """Population sd of x[t-n+1..t] by cumulative sums (O(len)); NaN until n values exist."""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    c1 = np.cumsum(np.r_[0.0, x])
    c2 = np.cumsum(np.r_[0.0, x * x])
    m = (c1[n:] - c1[:-n]) / n
    v = (c2[n:] - c2[:-n]) / n - m * m
    out[n - 1:] = np.sqrt(np.maximum(v, 0.0))
    return out


def _zmove(c: np.ndarray, n: int, vol_n: int = 288) -> np.ndarray:
    """n-bar log move over (the sd of the vol_n one-bar log moves up to t) x sqrt(n)."""
    lc = np.log(c)
    r1 = np.r_[0.0, np.diff(lc)]
    sd = rolling_std(r1, vol_n)
    sd[:vol_n] = np.nan
    mv = np.r_[np.full(n, np.nan), lc[n:] - lc[:-n]]
    return mv / (sd * math.sqrt(n))


def rolling_rank(x: np.ndarray, window: int, chunk: int = 20000) -> np.ndarray:
    """Share of the previous `window` values (t-window+1..t) strictly below x[t]; chunked."""
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.full(len(x), np.nan)
    if len(x) < window:
        return out
    w = sliding_window_view(x, window)
    for a in range(0, len(w), chunk):
        blk = w[a:a + chunk]
        out[window - 1 + a:window - 1 + a + len(blk)] = (blk < blk[:, -1:]).mean(axis=1)
    out[~np.isfinite(x)] = np.nan
    return out


def momentum(b: Bars, n: int = 12, z: float = 2.0, stop_atr: float = 1.5, r: float = 2.0, hold: int = 24) -> list[Signal]:
    """B3: intraday momentum. When the n-bar move is >= z standard deviations (of the past day's
    one-bar moves), trade in its direction; stop stop_atr x ATR; 2R; at most one signal per n bars."""
    zz = _zmove(b.c, n)
    ok = _window(b, 7, 20) & np.isfinite(zz)
    out, last = [], -10 ** 9
    for i in np.flatnonzero(ok & (np.abs(zz) >= z)):
        if i - last < n:
            continue
        side = 1 if zz[i] > 0 else -1
        st = b.c[i] - side * stop_atr * b.atr[i]
        out.append(Signal(i, side, st, _r_target(b.c[i], st, side, r), hold))
        last = i
    return out


def mean_reversion(b: Bars, n: int = 20, d: float = 2.5, stop_atr: float = 1.5, hold: int = 24) -> list[Signal]:
    """B4: short-term mean reversion. When the close is >= d ATR from its EMA(n), fade it: stop
    stop_atr x ATR beyond the close, target the EMA's value at the signal; at most one signal per n bars."""
    e = ema(b.c, n)
    dist = (b.c - e) / b.atr
    ok = _window(b, 7, 20) & np.isfinite(dist)
    out, last = [], -10 ** 9
    for i in np.flatnonzero(ok & (np.abs(dist) >= d)):
        if i - last < n:
            continue
        side = -1 if dist[i] > 0 else 1
        st = b.c[i] - side * stop_atr * b.atr[i]
        out.append(Signal(i, side, st, e[i], hold))
        last = i
    return out


def session_open(b: Bars, stop_atr: float = 1.5, r: float = 2.0, hold: int = 48) -> list[Signal]:
    """B6 / session baseline: at the 07:00 UTC bar's close, trade in the direction of the move since
    the trading day began (22:00 UTC); stop stop_atr x ATR; 2R; one per day."""
    out = []
    first_of_day: dict = {}
    for i in range(len(b)):
        first_of_day.setdefault(b.day[i], i)
        if b.hour[i] == 7 and b.minute[i] == 0 and b.weekday[i] < 5 and b.atr[i] > 0:
            mv = b.c[i] - b.o[first_of_day[b.day[i]]]
            if mv == 0:
                continue
            side = 1 if mv > 0 else -1
            st = b.c[i] - side * stop_atr * b.atr[i]
            out.append(Signal(i, side, st, _r_target(b.c[i], st, side, r), hold))
    return out


USD_SIGN = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "NZDUSD": -1, "USDJPY": 1, "USDCAD": 1, "USDCHF": 1}


def usd_lag(panel: dict, n: int = 12, z: float = 2.0, lag: float = 0.5, stop_atr: float = 1.5, r: float = 2.0,
            hold: int = 24, min_pairs: int = 4) -> dict:
    """C1: cross-market USD catch-up. A USD index is the mean of the USD-signed log prices of the
    USD pairs present (each forward-filled from its own last close: past values only). When the
    index's n-bar move is >= z standard deviations (of its past day's one-bar moves) and a pair's
    own USD-signed move is <= lag standard deviations (it has not followed), trade that pair in the
    USD's direction; stop stop_atr x ATR; 2R; one signal per pair per n bars; 07:00-20:00 UTC."""
    names = [k for k in panel if k in USD_SIGN]
    grid = np.unique(np.concatenate([panel[k].t for k in names]))
    pos = {k: np.searchsorted(grid, panel[k].t) for k in names}
    lp = np.full((len(names), len(grid)), np.nan)
    for a, k in enumerate(names):
        row = np.full(len(grid), np.nan)
        row[pos[k]] = USD_SIGN[k] * np.log(panel[k].c)
        valid = np.isfinite(row)
        idx = np.where(valid, np.arange(len(grid)), -1)
        np.maximum.accumulate(idx, out=idx)
        lp[a] = np.where(idx >= 0, row[np.maximum(idx, 0)], np.nan)
    present = np.isfinite(lp).sum(axis=0)
    usd = np.where(present >= min_pairs, np.nanmean(np.where(np.isfinite(lp), lp, np.nan), axis=0), np.nan)
    # the index must be built from the same pairs over the move: demeaned per-pair moves averaged
    mv = np.full(len(grid), np.nan)
    r1 = np.full(len(grid), np.nan)
    with np.errstate(invalid="ignore"):
        d_n = np.nanmean(lp[:, n:] - lp[:, :-n], axis=0)
        d_1 = np.nanmean(lp[:, 1:] - lp[:, :-1], axis=0)
    mv[n:] = d_n
    r1[1:] = d_1
    sd = rolling_std(np.nan_to_num(r1), 288)
    zi = mv / (sd * math.sqrt(n))
    zi[present < min_pairs] = np.nan
    del usd
    out = {}
    for k in names:
        b = panel[k]
        own = USD_SIGN[k] * _zmove(b.c, n)
        zk = zi[pos[k]]
        ok = _window(b, 7, 20) & np.isfinite(own) & np.isfinite(zk)
        sig, last = [], -10 ** 9
        for i in np.flatnonzero(ok & (np.abs(zk) >= z)):
            if i - last < n:
                continue
            d = 1 if zk[i] > 0 else -1  # +1: the USD is rising
            if d * own[i] > lag:
                continue  # the pair already followed
            side = d * USD_SIGN[k]  # long USD = buy USDxxx, sell xxxUSD
            st = b.c[i] - side * stop_atr * b.atr[i]
            sig.append(Signal(i, side, st, _r_target(b.c[i], st, side, r), hold))
            last = i
        out[k] = sig
    return out


def atr_rank(b: Bars, window: int = 2016) -> np.ndarray:
    """Percentile of the current ATR among the previous `window` bars' ATRs (a week of M5)."""
    a = b.atr.copy()
    r = rolling_rank(np.nan_to_num(a, nan=-np.inf), window)
    r[~np.isfinite(a)] = np.nan
    return r


def h1_trend(b: Bars, n: int = 50, slope: int = 3) -> np.ndarray:
    """Sign of the slope of an EMA(n) of COMPLETED H1 closes over `slope` hours, as known at each
    M5 bar: only hours that ended before the bar's own hour began are used."""
    hour_id = b.t // 3600
    hours, last_idx = np.unique(hour_id, return_index=True)
    last_idx = np.r_[last_idx[1:] - 1, len(b) - 1]
    closes = b.c[last_idx]
    e = ema(closes, n)
    sl = np.full(len(hours), np.nan)
    sl[slope:] = np.sign(e[slope:] - e[:-slope])
    sl[:n] = np.nan
    k = np.searchsorted(hours, hour_id) - 1  # the last completed hour before this bar's hour
    out = np.where(k >= 0, sl[np.maximum(k, 0)], np.nan)
    return out


def filtered(signals: list[Signal], keep) -> list[Signal]:
    """A hybrid: the rule's own signals, kept only where `keep(signal)` is true."""
    return [s for s in signals if keep(s)]


def random_entries(b: Bars, seed: int, per_day: int = 1, side: int | None = None, stop_atr: float = 1.5,
                   r: float = 2.0, hold: int = 48) -> list[Signal]:
    """Control: `per_day` random bars per trading day inside 07:00-20:00 UTC, random side (or a fixed
    one); stop stop_atr x ATR; 2R. Seeded."""
    rng = np.random.default_rng(seed)
    ok = _window(b, 7, 20)
    out = []
    days = {}
    for i in np.flatnonzero(ok):
        days.setdefault(b.day[i], []).append(i)
    for d in sorted(days):
        for i in sorted(rng.choice(days[d], size=min(per_day, len(days[d])), replace=False)):
            s = side if side is not None else (1 if rng.random() < 0.5 else -1)
            st = b.c[i] - s * stop_atr * b.atr[i]
            out.append(Signal(int(i), s, st, _r_target(b.c[i], st, s, r), hold))
    return out


def matched_random(b: Bars, model: list[Signal], seed: int) -> list[Signal]:
    """Control matched to a rule: the same number of signals, at random bars with the same UTC hours
    (sampled from the rule's own signal hours), random side, the SAME stop distance in ATR and the
    same reward:risk and holding as a randomly drawn signal of the rule. Market entries only."""
    if not model:
        return []
    rng = np.random.default_rng(seed)
    hours = np.array([b.hour[s.i] for s in model])
    by_hour: dict = {}
    for i in np.flatnonzero(_window(b, 0, 24)):
        by_hour.setdefault(int(b.hour[i]), []).append(i)
    out = []
    for _ in range(len(model)):
        m = model[rng.integers(len(model))]
        ref = m.limit if m.limit is not None else b.c[m.i]
        dist_atr = abs(ref - m.stop) / b.atr[m.i]
        rr = abs(m.target - ref) / abs(ref - m.stop)
        h = int(hours[rng.integers(len(hours))])
        if h not in by_hour:
            continue
        i = int(rng.choice(by_hour[h]))
        s = 1 if rng.random() < 0.5 else -1
        st = b.c[i] - s * dist_atr * b.atr[i]
        out.append(Signal(i, s, st, _r_target(b.c[i], st, s, rr), m.max_bars))
    return sorted(out, key=lambda x: x.i)


# ── simulation ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Costs:
    commission_pips_rt: float = 0.7  # the risk engine's value (~$7 per standard lot)
    slippage_pips: float = 0.1  # per market fill, the risk engine's value
    spread_mult: float = 1.0  # stress: the measured spread widened around the mid
    markup_pa: float = 1.5  # financing markup, percent a year, either side
    # the production risk engine's entry checks (risk/engine.py RiskLimits)
    min_stop_spreads: float = 3.0
    max_spread_to_stop: float = 0.25
    max_cost_to_risk: float = 0.25
    min_reward_risk: float = 1.2

    def stressed(self, k: float) -> "Costs":
        return Costs(self.commission_pips_rt * k, self.slippage_pips * k, self.spread_mult * k, self.markup_pa * k,
                     self.min_stop_spreads, self.max_spread_to_stop, self.max_cost_to_risk, self.min_reward_risk)


@dataclass
class Trade:
    symbol: str
    side: int
    signal_i: int
    entry_i: int
    exit_i: int
    entry_t: int
    exit_t: int
    entry: float
    exit: float
    risk: float  # |entry - stop|, price units
    gross_mid: float  # mid-to-mid P&L, price units
    spread: float  # spread paid (positive = cost)
    slippage: float
    commission: float
    financing: float  # signed: + received
    reason: str  # target | stop | time | gap

    @property
    def net(self) -> float:
        return self.gross_mid - self.spread - self.slippage - self.commission + self.financing

    @property
    def r(self) -> float:
        return self.net / self.risk


RateFn = "callable(side, t_epoch) -> annual percent the position EARNS before the markup (negative = pays)"


def simulate(b: Bars, signals: list[Signal], costs: Costs = Costs(), carry=None) -> tuple[list[Trade], dict]:
    """Trades from signals, one position or pending order at a time. `carry(side, t)` gives the
    annual percent a position of that side earns over the rollover at time t (rate differential),
    None = no financing data (charged the markup only). Returns trades and skip counts."""
    pip = b.pip
    slip, comm = costs.slippage_pips * pip, costs.commission_pips_rt * pip
    skipped = {"busy": 0, "risk_checks": 0, "no_fill": 0, "end_of_data": 0, "bad_stop": 0}
    trades: list[Trade] = []
    free_from = 0
    n = len(b)

    def widen(j):
        """How far each side of bar j's quote moves out under the spread stress (0 at x1)."""
        return (b.ao[j] - b.bo[j]) / 2 * (costs.spread_mult - 1.0)

    def half(j):
        """Half the bar's spread (mean of its open and close spreads), stress included."""
        return ((b.ao[j] - b.bo[j]) + (b.ac[j] - b.bc[j])) / 4 + widen(j)

    for s in signals:
        if s.i < free_from:
            skipped["busy"] += 1
            continue
        j0 = s.i + 1
        if j0 >= n or b.gap_after[s.i]:
            skipped["end_of_data"] += 1
            continue
        side = s.side
        # ── entry ──
        if s.limit is None:
            w = widen(j0)
            entry = (b.ao[j0] + w + slip) if side > 0 else (b.bo[j0] - w - slip)
            mid_in = (b.ao[j0] + b.bo[j0]) / 2
            ei, fill_bar_limit = j0, False
            n_fills_slip = 1
        else:
            ei = None
            for j in range(j0, min(n, j0 + s.valid)):
                w = widen(j)
                if side > 0 and b.al[j] + w < s.limit:
                    entry, ei = min(b.ao[j] + w, s.limit), j
                    break
                if side < 0 and b.bh[j] - w > s.limit:
                    entry, ei = max(b.bo[j] - w, s.limit), j
                    break
                if b.gap_after[j]:
                    break
            if ei is None:
                skipped["no_fill"] += 1
                free_from = min(n, j0 + s.valid)
                continue
            fill_bar_limit = True
            n_fills_slip = 0
            mid_in = entry - side * half(ei)
        risk = (entry - s.stop) * side
        if not risk > 0:
            skipped["bad_stop"] += 1
            free_from = ei + 1
            continue
        spread_now = (b.ao[ei] - b.bo[ei]) * costs.spread_mult
        rt_cost = spread_now + comm + 2 * slip
        reward = (s.target - entry) * side
        if (risk < costs.min_stop_spreads * spread_now or spread_now > costs.max_spread_to_stop * risk
                or rt_cost > costs.max_cost_to_risk * risk or reward < costs.min_reward_risk * risk):
            skipped["risk_checks"] += 1
            free_from = ei + 1
            continue
        # ── management ──
        deadline = None
        if s.deadline_hour is not None:
            deadline = (b.utc_day[ei] * 86400) + s.deadline_hour * 3600
        exit_px, xi, why = None, None, None
        last = min(n - 1, ei + s.max_bars - 1)
        for j in range(ei, last + 1):
            w = widen(j)
            if side > 0:
                lo, hi, op, cl = b.bl[j] - w, b.bh[j] - w, b.bo[j] - w, b.bc[j] - w
                if lo <= s.stop:
                    exit_px, why = min(op, s.stop) - slip if j > ei or not fill_bar_limit else s.stop - slip, "stop"
                elif hi >= s.target and not (fill_bar_limit and j == ei):
                    exit_px, why = s.target, "target"
            else:
                lo, hi, op, cl = b.al[j] + w, b.ah[j] + w, b.ao[j] + w, b.ac[j] + w
                if hi >= s.stop:
                    exit_px, why = max(op, s.stop) + slip if j > ei or not fill_bar_limit else s.stop + slip, "stop"
                elif lo <= s.target and not (fill_bar_limit and j == ei):
                    exit_px, why = s.target, "target"
            if exit_px is not None:
                xi = j
                break
            if (deadline is not None and b.t[j] + M5 >= deadline) or j == last or b.gap_after[j]:
                exit_px, xi = cl - side * slip, j
                why = "gap" if b.gap_after[j] and j != last else "time"
                break
        if xi is None:
            skipped["end_of_data"] += 1
            break
        market_exit = why in ("stop", "time", "gap")
        if market_exit:
            n_fills_slip += 1
        # the mid at exit: the fill plus the half spread (and slippage, for a market fill) it paid
        mid_out = exit_px + side * (half(xi) + (slip if market_exit else 0.0))
        if s.limit is None:
            mid_in = mid_in  # set at entry: the open's mid
        gross_mid = (mid_out - mid_in) * side
        pnl = (exit_px - entry) * side  # includes spread and market-fill slippage
        slippage = n_fills_slip * slip
        spread = gross_mid - pnl - slippage
        fin = financing(b.t[ei], b.t[xi] + M5, side, entry, costs.markup_pa, carry)
        trades.append(Trade(b.symbol, side, s.i, ei, xi, int(b.t[ei]), int(b.t[xi]), float(entry), float(exit_px),
                            float(risk), float(gross_mid), float(spread), float(slippage), float(comm), float(fin), why))
        free_from = xi + 1
    return trades, skipped


def financing(t0: int, t1: int, side: int, price: float, markup_pa: float, carry) -> float:
    """Financing in price units for a position held from t0 to t1: per 21:00 UTC rollover crossed
    (Wednesday's counts three times), (rate the side earns - markup) x price / 365."""
    total = 0.0
    first = (t0 - ROLLOVER_HOUR * 3600) // 86400 + 1
    last = (t1 - ROLLOVER_HOUR * 3600) // 86400
    for d in range(int(first), int(last) + 1):
        roll = d * 86400 + ROLLOVER_HOUR * 3600
        if not (t0 < roll <= t1):
            continue
        wd = (d + 3) % 7
        if wd >= 5:
            continue
        mult = 3 if wd == 2 else 1
        earn = carry(side, roll) if carry is not None else 0.0
        if earn is None or not math.isfinite(earn):
            earn = 0.0
        total += mult * (earn - markup_pa) / 100.0 * price / 365.0
    return total


# ── statistics ──────────────────────────────────────────────────────────

def summarize(trades: list[Trade], risk_pct: float = 0.5, period: tuple[int, int] | None = None) -> dict:
    """Trade and account statistics over `period` (epoch seconds [start, end); default: first entry
    to last exit). Account returns are R x risk_pct, summed (no compounding). Daily statistics
    count every weekday of the period, with zero on days without a closed trade."""
    if not trades:
        return {"trades": 0}
    r = np.array([t.r for t in trades])
    risk = np.array([t.risk for t in trades])
    gross = np.array([t.gross_mid for t in trades]) / risk
    spread = np.array([t.spread for t in trades]) / risk
    slip = np.array([t.slippage for t in trades]) / risk
    comm = np.array([t.commission for t in trades]) / risk
    fin = np.array([t.financing for t in trades]) / risk
    lo, hi = period if period is not None else (trades[0].entry_t, trades[-1].exit_t + 86400)
    d0, d1 = lo // 86400, (hi - 1) // 86400
    all_days = np.arange(d0, d1 + 1)
    all_days = all_days[(all_days + 3) % 7 < 5]
    pos = {int(d): k for k, d in enumerate(all_days)}
    per_day = np.zeros(len(all_days))
    for t, x in zip(trades, r):
        k = pos.get(int(t.exit_t // 86400))
        if k is not None:
            per_day[k] += x
    n_d = len(per_day)
    t_day = float(np.mean(per_day) / np.std(per_day, ddof=1) * math.sqrt(n_d)) if n_d > 2 and np.std(per_day) > 0 else None
    wins, losses = r[r > 0], r[r <= 0]
    acct = per_day * risk_pct / 100.0
    eq = np.cumsum(acct)
    dd = float(np.max(np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq)) if len(eq) else 0.0
    years = max((hi - lo) / 86400.0 / 365.25, 1e-9)
    return {
        "trades": len(r), "trades_per_month": round(len(r) / (years * 12), 2),
        "win_rate": round(float(np.mean(r > 0)), 4),
        "avg_win_r": round(float(np.mean(wins)), 4) if len(wins) else None,
        "avg_loss_r": round(float(np.mean(losses)), 4) if len(losses) else None,
        "gross_r": round(float(np.mean(gross)), 4), "spread_r": round(float(np.mean(spread)), 4),
        "slippage_r": round(float(np.mean(slip)), 4), "commission_r": round(float(np.mean(comm)), 4),
        "financing_r": round(float(np.mean(fin)), 4), "net_r": round(float(np.mean(r)), 4),
        "t_day": round(t_day, 3) if t_day is not None else None,
        "profit_factor": round(float(wins.sum() / -losses.sum()), 3) if losses.sum() < 0 else None,
        "total_r": round(float(r.sum()), 2),
        "net_return_pct": round(float(r.sum() * risk_pct), 2),
        "annual_return_pct": round(float(r.sum() * risk_pct / years), 2),
        "sharpe": round(float(np.mean(acct) / np.std(acct, ddof=1) * math.sqrt(252)), 3) if n_d > 2 and np.std(acct) > 0 else None,
        "max_drawdown_pct": round(dd * 100, 2),
        "reasons": {k: int(sum(1 for t in trades if t.reason == k)) for k in ("target", "stop", "time", "gap")},
        "top10pct_share": _top_share(r),
        "median_bars_held": float(np.median([t.exit_i - t.entry_i + 1 for t in trades])),
    }


def _top_share(r: np.ndarray, frac: float = 0.10) -> float | None:
    tot = float(r.sum())
    if tot <= 0:
        return None
    k = max(1, int(round(len(r) * frac)))
    return round(float(np.sort(r)[::-1][:k].sum()) / tot, 3)


def monthly_r(trades: list[Trade]) -> dict:
    out: dict = {}
    for t in trades:
        d = datetime.fromtimestamp(t.exit_t, timezone.utc)
        out[(d.year, d.month)] = out.get((d.year, d.month), 0.0) + t.r
    return dict(sorted(out.items()))


def rolling_windows(months: dict, start: tuple, end: tuple, length: int, risk_pct: float = 0.5) -> dict:
    """Every window of `length` consecutive calendar months between start and end (inclusive):
    the share profitable and the distribution of returns (percent at risk_pct per trade), with each
    window's maximum drawdown on its monthly path."""
    keys = []
    y, m = start
    while (y, m) <= end:
        keys.append((y, m))
        y, m = (y + (m == 12), m % 12 + 1)
    vals = [months.get(k, 0.0) * risk_pct for k in keys]
    rets, dds = [], []
    for i in range(len(vals) - length + 1):
        w = np.array(vals[i:i + length])
        rets.append(float(w.sum()))
        eq = np.cumsum(w)
        dds.append(float(np.max(np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq)))
    if not rets:
        return {}
    a = np.array(rets)
    return {"windows": len(a), "profitable_share": round(float(np.mean(a > 0)), 3),
            "median_pct": round(float(np.median(a)), 2), "worst_pct": round(float(a.min()), 2),
            "best_pct": round(float(a.max()), 2),
            "p10_pct": round(float(np.quantile(a, 0.1)), 2), "p90_pct": round(float(np.quantile(a, 0.9)), 2),
            "median_max_dd_pct": round(float(np.median(dds)), 2), "worst_max_dd_pct": round(float(max(dds)), 2)}


__all__ = ["Bars", "Costs", "INTRADAY_VERSION", "Signal", "Trade", "USD_SIGN", "atr", "atr_rank", "bos_fvg", "choch",
           "ema", "failed_breakout", "filtered", "h1_trend", "rolling_rank", "rolling_std", "usd_lag",
           "financing", "matched_random", "mean_reversion", "momentum", "monthly_r", "opening_range", "order_block",
           "prev_day_levels", "random_entries", "rolling_windows", "session_open", "simulate", "squeeze", "summarize",
           "sweep_asia", "sweep_equal", "sweep_pd", "swings"]
