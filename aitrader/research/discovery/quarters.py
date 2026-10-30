"""QT-1: the two "Quarters" schools as precise M5 rules (research only). qt-1.0.0

The owner asked (2026-10-30) whether the Quarters school, taught alongside SMC, would trade better than letting a
model read direction. Two schools share the name, and both are tested here, each as its own teachers state it:

- PRICE quarters (the Quarters Theory of round-number "quarter points"). Price is said to move from one quarter
  level to the next, 25 pips apart (00, 25, 50, 75; 0.25 yen on a JPY pair), reversing at an untouched level or
  running to the next one once a level breaks. The academic version of the claim is Osler (2000, 2003): take-profit
  orders cluster at round numbers (reversals) and stop-loss orders just beyond them (accelerations).
  Q1 fades the first touch of an untouched quarter level; Q2 trades a close through one.
- TIME quarters (the Quarterly Theory). Every period has four quarters: accumulation, manipulation, distribution,
  then continuation or reversal (AMDX). The day's quarters are the 6-hour sessions from 18:00 New York (Asia,
  London, New York AM, New York PM). The "true open" is the open of the second quarter: 00:00 New York for the day,
  the start of the second 90-minute quarter for a session. The manipulation is a false move away from the true
  open, and the distribution runs the other way. T1 trades the day's cycle; T2 and T3 the 90-minute cycle of the
  New York AM and the London sessions.

Every rule is a causal function of bars up to and including the signal bar's close, and returns `intraday.Signal`s
that `intraday.simulate` fills on bid/ask with the project's costs and the production risk engine's entry checks.
Nothing here sizes a live trade: the risk engine remains the only sizing authority.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import numpy as np

from .intraday import Bars, Signal, _r_target, _window

QUARTERS_VERSION = "qt-1.0.0"
QUARTER_PIPS = 25.0
DAY_MIN = 1440


# ── New York time ───────────────────────────────────────────────────────

def _us_dst(year: int) -> tuple[int, int]:
    """US daylight time, 2007 rules: from the second Sunday of March 02:00 EST (07:00 UTC) to the first Sunday of
    November 02:00 EDT (06:00 UTC), as epoch seconds."""
    mar1, nov1 = date(year, 3, 1), date(year, 11, 1)
    start = 1 + (6 - mar1.weekday()) % 7 + 7
    end = 1 + (6 - nov1.weekday()) % 7
    ts = lambda m, d, h: int(datetime(year, m, d, h, tzinfo=timezone.utc).timestamp())  # noqa: E731
    return ts(3, start, 7), ts(11, end, 6)


def ny_offset_hours(t: np.ndarray) -> np.ndarray:
    """New York's offset from UTC at each time: -4 in daylight time, -5 otherwise."""
    t = np.asarray(t, np.int64)
    off = np.full(len(t), -5, np.int64)
    if not len(t):
        return off
    y0 = datetime.fromtimestamp(int(t.min()), timezone.utc).year
    y1 = datetime.fromtimestamp(int(t.max()), timezone.utc).year
    for y in range(y0, y1 + 1):
        a, b = _us_dst(y)
        off[(t >= a) & (t < b)] = -4
    return off


def ny_clock(b: Bars):
    """Per bar: the New York trading day (it starts at 18:00 New York), the minute of that day (0 = 18:00), and the
    UTC offset in hours."""
    off = ny_offset_hours(b.t)
    shifted = b.t + off * 3600 + 6 * 3600
    return shifted // 86400, (shifted % 86400) // 60, off


def _utc_hour(ny_minute_of_day: int, off: int) -> int:
    """The UTC hour of a New York trading-day minute, under the offset in force."""
    return int(((18 * 60 + ny_minute_of_day) // 60 - off) % 24)


# ── price quarters ──────────────────────────────────────────────────────

def _day_extremes(b: Bars):
    """The trading day's high and low through each bar (22:00 UTC boundary, the day the window rules use)."""
    hi, lo = b.h.copy(), b.l.copy()
    for k in range(1, len(b)):
        if b.day[k] == b.day[k - 1]:
            hi[k], lo[k] = max(hi[k], hi[k - 1]), min(lo[k], lo[k - 1])
    return hi, lo


def quarter_fade(b: Bars, q: float = QUARTER_PIPS, stop: float = 12.5, r: float = 2.0, valid: int = 24,
                 hold: int = 48) -> list[Signal]:
    """Q1: fade the first touch of an untouched quarter level. The levels are every q pips. At a bar's close
    (07:00-20:00 UTC), take the first level above the day's high so far and the first below its low so far, both
    untouched today; when the nearer one is within q/2 of the close, a limit order rests AT it, against the
    approach, for `valid` bars: a sell at the level above, a buy at the level below. Stop `stop` pips beyond the
    level; target r times that from it; one order per level per day."""
    step = q * b.pip
    dh, dl = _day_extremes(b)
    ok = _window(b, 7, 20)
    out, used = [], set()
    for i in np.flatnonzero(ok):
        up = (np.floor(dh[i] / step + 1e-9) + 1) * step  # untouched: above every price traded today
        dn = (np.ceil(dl[i] / step - 1e-9) - 1) * step
        du, dd = up - b.c[i], b.c[i] - dn
        side, lvl, dist = (-1, up, du) if du <= dd else (1, dn, dd)
        key = (int(b.day[i]), round(lvl / step))
        if dist > step / 2 or key in used:
            continue
        used.add(key)
        st = lvl - side * stop * b.pip
        out.append(Signal(int(i), side, st, _r_target(lvl, st, side, r), hold, limit=float(lvl), valid=valid))
    return out


def quarter_break(b: Bars, q: float = QUARTER_PIPS, stop: float = 12.5, r: float = 2.0,
                  hold: int = 48) -> list[Signal]:
    """Q2: trade a close through a quarter level. When a bar (07:00-20:00 UTC) closes beyond a level of the q-pip
    grid that the previous bar closed on the other side of, buy (up) or sell (down) at the next open; stop `stop`
    pips from the close; target r times that. The first break of each level in each direction per day."""
    step = q * b.pip
    ok = _window(b, 7, 20)
    out, used = [], set()
    for i in np.flatnonzero(ok):
        if i == 0 or b.day[i] != b.day[i - 1]:
            continue
        a, c = np.floor(b.c[i - 1] / step + 1e-9), np.floor(b.c[i] / step + 1e-9)
        if a == c:
            continue
        side = 1 if c > a else -1
        lvl = int(c if side > 0 else a)  # the level crossed nearest the close
        key = (int(b.day[i]), lvl, side)
        if key in used:
            continue
        used.add(key)
        st = b.c[i] - side * stop * b.pip
        out.append(Signal(int(i), side, st, _r_target(b.c[i], st, side, r), hold))
    return out


# ── time quarters ───────────────────────────────────────────────────────

def _days(nyday: np.ndarray):
    days, start = np.unique(nyday, return_index=True)
    return zip(start, np.r_[start[1:], len(nyday)])


def _at(idx, minute, m):
    """The bar of a day opening at New York trading-day minute m, or None."""
    k = np.flatnonzero(minute[idx] == m)
    return int(idx[k[0]]) if len(k) else None


def daily_amd(b: Bars, buf: float = 0.10, r: float = 2.0, min_bars: int = 36) -> list[Signal]:
    """T1: the day's quarters. Asia (18:00-00:00 New York) accumulates a range; London (00:00-06:00) manipulates;
    New York AM (06:00-12:00) distributes. At the close of London's last bar (05:55): when London traded beyond
    the Asian range on ONE side only and closed on that side of the true day open (00:00), trade the other way at
    06:00. Stop beyond London's extreme + buf x ATR; target r R; time exit at 12:00 New York. Each range needs
    `min_bars` bars."""
    nyday, minute, off = ny_clock(b)
    out = []
    for s, e in _days(nyday):
        idx = np.arange(s, e)
        asia, london = idx[minute[idx] < 360], idx[(minute[idx] >= 360) & (minute[idx] < 720)]
        j, tdo = _at(idx, minute, 715), _at(idx, minute, 360)
        if len(asia) < min_bars or len(london) < min_bars or j is None or tdo is None or b.weekday[j] >= 5:
            continue
        a = b.atr[j]
        if not a > 0:
            continue
        ah, al, lh, ll, c, o = b.h[asia].max(), b.l[asia].min(), b.h[london].max(), b.l[london].min(), b.c[j], b.o[tdo]
        dl = _utc_hour(720 + 360, int(off[j]))
        if lh > ah and ll >= al and c > o:
            st = lh + buf * a
            out.append(Signal(j, -1, st, _r_target(c, st, -1, r), 72, deadline_hour=dl))
        elif ll < al and lh <= ah and c < o:
            st = ll - buf * a
            out.append(Signal(j, 1, st, _r_target(c, st, 1, r), 72, deadline_hour=dl))
    return out


def session_true_open(b: Bars, session: int, buf: float = 0.10, r: float = 2.0, min_bars: int = 12) -> list[Signal]:
    """T2/T3: a session's 90-minute quarters. `session` is the session's start, in minutes from 18:00 New York
    (720 = New York AM, 06:00; 360 = London, 00:00). Q1 is its first 90 minutes; Q2 the next 90, opening at the
    true session open. At the close of Q2's last bar: when Q2 ran beyond Q1's range on ONE side only (the false
    move) and closed on that side of the true open, trade the other way at the next open. Stop beyond Q2's extreme
    + buf x ATR; target r R; time exit at the session's end. Each quarter needs `min_bars` bars."""
    nyday, minute, off = ny_clock(b)
    out = []
    for s, e in _days(nyday):
        idx = np.arange(s, e)
        q1 = idx[(minute[idx] >= session) & (minute[idx] < session + 90)]
        q2 = idx[(minute[idx] >= session + 90) & (minute[idx] < session + 180)]
        j, tso = _at(idx, minute, session + 175), _at(idx, minute, session + 90)
        if len(q1) < min_bars or len(q2) < min_bars or j is None or tso is None or b.weekday[j] >= 5:
            continue
        a = b.atr[j]
        if not a > 0:
            continue
        h1, l1, h2, l2, c, o = b.h[q1].max(), b.l[q1].min(), b.h[q2].max(), b.l[q2].min(), b.c[j], b.o[tso]
        dl = _utc_hour(session + 360, int(off[j]))
        if h2 > h1 and l2 >= l1 and c > o:
            st = h2 + buf * a
            out.append(Signal(j, -1, st, _r_target(c, st, -1, r), 36, deadline_hour=dl))
        elif l2 < l1 and h2 <= h1 and c < o:
            st = l2 - buf * a
            out.append(Signal(j, 1, st, _r_target(c, st, 1, r), 36, deadline_hour=dl))
    return out


def ny_true_open(b: Bars, buf: float = 0.10, r: float = 2.0) -> list[Signal]:
    """T2: the New York AM session (06:00-12:00 New York); true session open 07:30, entry 09:00."""
    return session_true_open(b, 720, buf, r)


def london_true_open(b: Bars, buf: float = 0.10, r: float = 2.0) -> list[Signal]:
    """T3: the London session (00:00-06:00 New York); true session open 01:30, entry 03:00."""
    return session_true_open(b, 360, buf, r)


__all__ = ["QUARTERS_VERSION", "QUARTER_PIPS", "daily_amd", "london_true_open", "ny_clock", "ny_offset_hours",
           "ny_true_open", "quarter_break", "quarter_fade", "session_true_open"]
