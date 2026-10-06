"""Order builders for the New York-session hypotheses NE-ON and NE-GAP (research/preregistrations/NE-1.md).

Every builder decides at the CLOSE of a named bar using only bars up to and including it. Each order's
`decided_i` is that bar. `tests/unit/test_canon_sessions.py` proves it: orders built on data truncated at
any bar equal the full-data orders decided at or before it.

Times are New York wall-clock hours converted with `zoneinfo`. The data's timestamps were measured as
true UTC (NEW_EDGE_AUDIT.md §2). A day whose required bar is missing is skipped, never filled.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import numpy as np

from .engine import NY, Order, Quotes

SESSIONS_VERSION = "ne-sessions-1.0.0"


def ny_epoch(d: date, hour: int) -> int:
    return int(datetime.combine(d, time(hour), tzinfo=NY).timestamp())


def trading_dates(q: Quotes, hour: int) -> list[date]:
    """New York weekdays on which a valid bar opens exactly at `hour`."""
    out = []
    for i in np.flatnonzero(q.valid):
        dt = datetime.fromtimestamp(int(q.t[i]), timezone.utc).astimezone(NY)
        if dt.minute == 0 and dt.hour == hour and dt.weekday() < 5:
            out.append(dt.date())
    return sorted(set(out))


def _index(q: Quotes) -> dict[int, int]:
    return {int(t): i for i, t in enumerate(q.t)}


def _prior_sd(values: list[float], k: int) -> float | None:
    """Sample sd of the last k values strictly before now (None until k exist)."""
    if len(values) < k:
        return None
    x = np.array(values[-k:])
    return float(x.std(ddof=1))


def next_weekday(d: date) -> date:
    d = d + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def overnight(q: Quotes, entry_hour: int = 16, exit_hour: int = 9, vol_days: int = 60, stop_sd: float = 3.0,
              side: int = 1) -> list[Order]:
    """NE-ON: hold from the open of the `entry_hour` bar to the first valid open at or after `exit_hour` on
    the next New York weekday (Friday -> Monday included). Decision at the close of the bar before entry:
    the rule is unconditional, so whether an order exists depends on nothing after that bar. Catastrophic
    stop: `stop_sd` x the sd of the previous `vol_days` completed overnight mid returns."""
    idx = _index(q)
    mo = q.mid_open()
    hist: list[float] = []
    orders = []
    pending: tuple[int, int] | None = None  # (entry epoch, exit epoch) of the last night, until it completes
    for a in trading_dates(q, entry_hour - 1):  # keyed on the DECISION bar: the entry bar is the future
        i_dec = idx[ny_epoch(a, entry_hour - 1)]
        if pending is not None:
            e, j = q.at_or_after(pending[0]), q.at_or_after(pending[1])
            if e < j <= i_dec and q.valid[e] and q.valid[j]:  # the night completed before this decision
                hist.append(mo[j] / mo[e] - 1)
        sd = _prior_sd(hist, vol_days)
        exit_at = ny_epoch(next_weekday(a), exit_hour)
        if sd is not None and sd > 0:
            orders.append(Order(i_dec, side, exit_at=exit_at, stop_bp=stop_sd * sd * 1e4, tag=f"ON {a}"))
        pending = (ny_epoch(a, entry_hour), exit_at)
    return orders


def gap_reversal(q: Quotes, z: float = 1.0, vol_days: int = 60, stop_sd: float = 3.0, how: str = "fade"
                 ) -> list[Order]:
    """NE-GAP: the overnight return g = mid close of the 09:00 bar (09:59) / mid open of the previous
    trading date's 16:00 bar - 1, known at the 09:00 bar's close. If |g| > z x sd(previous `vol_days` g),
    trade against it (`how`="fade"; "follow" is the price-direction baseline) from the next open (10:00)
    to the first valid open at or after 16:00. Catastrophic stop: `stop_sd` x the sd of the previous
    `vol_days` completed 10:00->16:00 mid returns."""
    if how not in ("fade", "follow"):
        raise ValueError(f"unknown how {how!r}")
    idx = _index(q)
    mo, mc = q.mid_open(), q.mid_close()
    gaps: list[float] = []
    sess: list[float] = []
    orders = []
    last16: int | None = None  # the latest valid 16:00 bar seen
    pending: tuple[int, int] | None = None  # (decision bar, 16:00 epoch) of the last session, until complete
    for d in trading_dates(q, 9):
        i9 = idx[ny_epoch(d, 9)]
        if pending is not None:
            e, x = pending[0] + 1, q.at_or_after(pending[1])
            if x < i9 and q.valid[e] and q.valid[x]:
                sess.append(mo[x] / mo[e] - 1)
            pending = None
        i16p = idx.get(ny_epoch(_prev_weekday(d), 16))
        if i16p is not None and q.valid[i16p]:
            last16 = i16p
        if last16 is None or q.t[last16] < ny_epoch(d, 9) - 4 * 86400:
            continue
        g = mc[i9] / mo[last16] - 1
        sg, ss = _prior_sd(gaps, vol_days), _prior_sd(sess, vol_days)
        if sg and ss and abs(g) > z * sg and g != 0:
            sd = -1 if g > 0 else 1
            if how == "follow":
                sd = -sd
            orders.append(Order(i9, sd, exit_at=ny_epoch(d, 16), stop_bp=stop_sd * ss * 1e4, tag=f"GAP {d}"))
        gaps.append(g)
        pending = (i9, ny_epoch(d, 16))
    return orders


def _prev_weekday(d: date) -> date:
    d = d - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def day_windows(q: Quotes, entry_hour: int, hold_hours: int, side: int = 1) -> list[Order]:
    """A long (or short) from the `entry_hour` open, held `hold_hours`: the session baselines (intraday
    long 10:00->16:00; buy-and-hold 16:00->16:00). No stop: a baseline, not a strategy."""
    idx = _index(q)
    orders = []
    for d in trading_dates(q, entry_hour):
        ie = idx.get(ny_epoch(d, entry_hour))
        if ie is None or ie < 1:
            continue
        exit_t = int((datetime.combine(d, time(entry_hour), tzinfo=NY) + timedelta(hours=hold_hours)).timestamp())
        orders.append(Order(ie - 1, side, exit_at=exit_t, tag=f"W{entry_hour}+{hold_hours} {d}"))
    return orders


def random_windows(q: Quotes, like: list[Order], seed: int, hours: tuple[int, ...] = tuple(range(24))
                   ) -> list[Order]:
    """The random-entry placebo: one order per real order, same side, same holding duration and same stop,
    entered at a random valid bar whose New York hour is in `hours`, within 10 trading days of the real
    entry (keeping the regime)."""
    rng = np.random.default_rng(seed)
    nyh = np.array([datetime.fromtimestamp(int(t), timezone.utc).astimezone(NY).hour for t in q.t])
    ok = np.flatnonzero(q.valid & np.isin(nyh, hours))
    out = []
    for o in like:
        e = o.decided_i + 1
        hold = (o.exit_at - int(q.t[e])) if o.exit_at else None
        lo, hi = np.searchsorted(ok, e - 240), np.searchsorted(ok, e + 240)
        if hi - lo < 2:
            continue
        j = int(ok[rng.integers(lo, hi)])
        if j < 1:
            continue
        out.append(Order(j - 1, o.side, exit_at=int(q.t[j]) + hold if hold else None, stop_bp=o.stop_bp,
                         max_bars=o.max_bars, tag="placebo"))
    out.sort(key=lambda x: x.decided_i)
    return out


def random_sides(like: list[Order], seed: int) -> list[Order]:
    """The direction placebo: the same orders, sides drawn at random."""
    rng = np.random.default_rng(seed)
    return [Order(o.decided_i, int(rng.choice([-1, 1])), o.exit_at, o.stop_bp, o.target_bp, o.max_bars, "rand-side")
            for o in like]


__all__ = ["SESSIONS_VERSION", "day_windows", "gap_reversal", "next_weekday", "ny_epoch", "overnight",
           "random_sides", "random_windows", "trading_dates"]
