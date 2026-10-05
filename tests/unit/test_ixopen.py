"""IX-4 (NASDAQ opening-candle EMA(12) signal): behaviour tests on constructed M5 bid/ask bars."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import numpy as np

from aitrader.research.discovery import ixopen as O

SPREAD = 0.2


def day_bars(days, jump=lambda k: 1.0, drift=lambda k: 0.05, start_px=100.0):
    """Full-day M5 bars. Mid is flat at the day's level until the 09:30 New York bar, which closes `jump(k)`
    away from its open; from the next bar the mid moves `drift(k)` per bar until 16:00, then stays flat."""
    t, o, c = [], [], []
    px = start_px
    for k, d in enumerate(days):
        base = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
        sig = O.ny_epoch(d, O.OPEN)
        close = O.ny_epoch(d, O.CLOSE)
        j, dr = jump(k), drift(k)
        for x in range(base, base + 86400, 300):
            op = px
            if x == sig:
                px = px + j
            elif sig < x < close:
                px = px + dr
            t.append(x)
            o.append(op)
            c.append(px)
    t, o, c = np.array(t, np.int64), np.array(o), np.array(c)
    h, lo = np.maximum(o, c), np.minimum(o, c)
    hs = SPREAD / 2
    return O.OBars("USATECHIDXUSD", t, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs)


def weekdays(n, start=date(2015, 1, 5)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_the_signal_bar_is_0930_new_york_through_daylight_saving():
    f = lambda d: datetime.fromtimestamp(O.ny_epoch(d, O.OPEN), timezone.utc).strftime("%H:%M")  # noqa: E731
    assert f(date(2015, 1, 15)) == "14:30" and f(date(2015, 7, 15)) == "13:30"


def test_the_ema_is_the_standard_recursion():
    e = O.ema(np.array([10.0, 11.0, 12.0]), 3)  # alpha 0.5, seeded with the first value
    assert np.allclose(e, [10.0, 10.5, 11.25])


def test_a_close_above_the_ema_is_long_and_below_is_short():
    b = day_bars(weekdays(4), jump=lambda k: 1.0 if k % 2 == 0 else -1.0)
    sides = [s for _, _, s in O.signals(b)]
    assert sides == [1, -1, 1, -1]


def test_a_time_exit_earns_the_known_drift_and_pays_one_spread():
    b = day_bars(weekdays(3), jump=lambda k: 1.0, drift=lambda k: 0.05)
    ts = O.simulate(b, O.signals(b), "T30")
    assert len(ts) == 3
    for x in ts:
        assert x.side == 1 and x.reason == "time"
        assert x.exit_t - x.entry_t == 1800
        mid_in = x.entry - SPREAD / 2
        assert abs(x.gross_bps - 6 * 0.05 / mid_in * 1e4) < 1e-6  # six bars of drift
        assert abs(x.cost_bps - SPREAD / mid_in * 1e4) < 1e-6


def test_session_close_exit_and_capped_time_exits_end_at_1600_new_york():
    b = day_bars(weekdays(2))
    for rule in ("TCLOSE",):
        for x in O.simulate(b, O.signals(b), rule):
            assert x.exit_t == O.ny_epoch(x.day, O.CLOSE)


def test_nothing_after_the_entry_quote_changes_the_signal():
    days = weekdays(6)
    b = day_bars(days, jump=lambda k: 1.0 if k % 2 == 0 else -1.0)
    base = O.signals(b)
    cut = O.ny_epoch(days[3], O.OPEN) + 300  # the signal bar of day 3 has closed
    later = b.t > cut
    noisy = replace(b, bo=np.where(later, b.bo + 50, b.bo), ao=np.where(later, b.ao + 50, b.ao),
                    bc=np.where(later, b.bc + 50, b.bc), ac=np.where(later, b.ac + 50, b.ac),
                    bh=np.where(later, b.bh + 50, b.bh), ah=np.where(later, b.ah + 50, b.ah),
                    bl=np.where(later, b.bl + 50, b.bl), al=np.where(later, b.al + 50, b.al))
    assert O.signals(noisy)[:4] == base[:4]


def test_a_stop_target_exit_takes_the_target_at_its_price():
    b = day_bars(weekdays(3), jump=lambda k: 1.0, drift=lambda k: 0.2)
    for x in O.simulate(b, O.signals(b), "S1.0"):
        assert x.reason == "target" and abs(x.r - 2.0) < 0.2


def test_a_falling_market_stops_a_long_at_the_stop():
    b = day_bars(weekdays(3), jump=lambda k: 1.0, drift=lambda k: -0.5)
    for x in O.simulate(b, O.signals(b), "S1.0"):
        assert x.reason == "stop" and x.r < -0.95


def test_doubling_costs_doubles_the_spread_paid_on_time_exits():
    b = day_bars(weekdays(3))
    for x, y in zip(O.simulate(b, O.signals(b), "T60"), O.simulate(b, O.signals(b), "T60", cost_mult=2.0)):
        assert abs(y.cost_bps - 2 * x.cost_bps) < 1e-6


def test_a_delayed_entry_starts_one_bar_later():
    b = day_bars(weekdays(3))
    for x, y in zip(O.simulate(b, O.signals(b), "T60"), O.simulate(b, O.signals(b), "T60", delay=1)):
        assert y.entry_t - x.entry_t == 300


def test_baselines_keep_the_dates_and_change_only_what_they_claim_to():
    b = day_bars(weekdays(10), jump=lambda k: 1.0)
    base = O.signals(b)
    rnd = O.random_signals(b, base, seed=1, mode="dir")
    assert [(d, i) for d, i, _ in rnd] == [(d, i) for d, i, _ in base]
    assert {s for _, _, s in rnd} == {-1, 1}
    first = O.signals(b, how="first")
    assert all(s == 1 for _, _, s in first)


def test_the_rth_ema_ignores_overnight_bars():
    b = day_bars(weekdays(3))
    full, rth = O.ema_series(b, 12), O.ema_series(b, 12, rth=True)
    i = int(np.flatnonzero(b.t == O.ny_epoch(weekdays(3)[0], O.OPEN) - 300)[0])  # 09:25: outside RTH
    assert np.isfinite(full[i]) and np.isnan(rth[i])


def test_no_exit_manufactures_an_edge_on_a_pure_random_walk():
    """Filling stops exactly at the stop level made every stop-based exit look profitable on a random walk
    (+1.5 to +3 bp gross); stops now fill through the level. No exit may show a significant gross edge
    where none exists."""
    rng = np.random.default_rng(14)
    days = weekdays(600, start=date(2012, 1, 2))
    t = np.array([x for d in days for x in range(int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()),
                                                   int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
                                                   + 86400, 300)], np.int64)
    path = 100 + np.cumsum(rng.normal(0, 0.05, len(t) * 4)).reshape(len(t), 4)
    o = np.r_[100, path[:-1, -1]]
    c = path[:, -1]
    h, lo = np.maximum(o, path.max(1)), np.minimum(o, path.min(1))
    hs = 0.05
    b = O.OBars("X", t, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs)
    sig = O.signals(b)
    for rule in O.EXITS:
        g = np.array([x.gross_bps for x in O.simulate(b, sig, rule)])
        assert g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) < 2.0, rule
