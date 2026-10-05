"""IX-3 (overnight drift at the European open): behaviour tests on constructed hour bars."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import numpy as np

from aitrader.research.discovery import ixdrift as D
from aitrader.research.discovery import ixmom as IX

SYM = "USA500IDXUSD"
SPREAD = 0.5


def bars(n_days: int = 40, drift: float = 0.001, us_last_hour=None, start: date = date(2015, 1, 5)):
    """24 hour bars per weekday. The mid rises by `drift` (fraction) during the hour after 09:00 Frankfurt
    and is flat otherwise, except that the US last hour moves by us_last_hour(k) on day k."""
    t, mid = [], []
    price, d, k = 2000.0, start, 0
    while k < n_days:
        if d.weekday() < 5:
            base = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
            e = D.entry_epoch(d)
            us_a = IX.close_epoch(SYM, d) - 3600
            for h in range(24):
                x = base + h * 3600
                t.append(x)
                mid.append(price)
                if x == e:
                    price *= 1 + drift
                if x == us_a and us_last_hour is not None:
                    price *= 1 + us_last_hour(k)
            k += 1
        d += timedelta(days=1)
    t = np.array(t, dtype=np.int64)
    m = np.array(mid)
    bid, ask = m - SPREAD / 2, m + SPREAD / 2
    return IX.Bars(SYM, t, bid, bid.copy(), bid.copy(), ask, ask.copy(), ask.copy())


def test_the_entry_is_the_xetra_open_through_daylight_saving():
    utc = lambda d: datetime.fromtimestamp(D.entry_epoch(d), timezone.utc).strftime("%H:%M")  # noqa: E731
    assert utc(date(2015, 1, 15)) == "08:00" and utc(date(2015, 7, 15)) == "07:00"


def test_the_last_us_session_before_a_monday_is_friday():
    assert D.last_us_session(date(2015, 1, 12)) == date(2015, 1, 9)
    assert D.last_us_session(date(2015, 1, 13)) == date(2015, 1, 12)


def test_a_known_drift_is_captured_long_with_one_spread_of_cost():
    ts = D.trades(bars(drift=0.001), vol_days=5)
    assert ts and all(x.side == 1 and abs(x.gross_bps - 10.0) < 1e-6 for x in ts)
    for x in ts:
        assert abs(x.cost_bps - SPREAD / ((x.entry - SPREAD / 2)) * 1e4) < 0.05


def test_the_conditional_variant_trades_only_after_a_falling_us_last_hour():
    every = D.trades(bars(us_last_hour=lambda k: 0.002 if k % 2 else -0.002), vol_days=5)
    cond = D.trades(bars(us_last_hour=lambda k: 0.002 if k % 2 else -0.002), vol_days=5, conditional=True)
    assert 0 < len(cond) < len(every)
    assert all(x.signal < 0 for x in cond)


def test_nothing_after_the_exit_changes_a_trade():
    b = bars(n_days=30)
    base = D.trades(b, vol_days=5)
    k = 15
    cut = D.entry_epoch(base[k].day) + 3600
    later = b.t > cut
    noisy = replace(b, bo=np.where(later, b.bo * 1.1, b.bo), ao=np.where(later, b.ao * 1.1, b.ao),
                    bl=np.where(later, b.bl * 1.1, b.bl), ah=np.where(later, b.ah * 1.1, b.ah))
    moved = D.trades(noisy, vol_days=5)
    assert base[: k + 1] == moved[: k + 1]


def test_doubling_costs_doubles_the_spread_paid():
    b = bars()
    for x, y in zip(D.trades(b, vol_days=5), D.trades(b, vol_days=5, cost_mult=2.0)):
        assert abs(y.cost_bps - 2 * x.cost_bps) < 1e-6


def test_the_stop_fills_at_the_stop_when_the_held_hour_trades_through_it():
    b = bars(n_days=12)
    x = D.trades(b, vol_days=5)[-1]
    i = int(np.flatnonzero(b.t == D.entry_epoch(x.day))[0])
    bl = b.bl.copy()
    bl[i] = b.bo[i] * 0.9
    y = D.trades(replace(b, bl=bl), vol_days=5)[-1]
    assert y.stopped and y.exit == y.stop
