"""QT-1, the two Quarters schools: each rule fires exactly where its teachers say, on a day built so the answer is
known; New York time follows the US daylight rules; and no rule reads a bar after its signal bar."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.research.discovery import intraday as ID
from aitrader.research.discovery import quarters as Q

PIP = 0.0001


def ts(*a) -> int:
    return int(datetime(*a, tzinfo=timezone.utc).timestamp())


def bars(mid, t0, highs=None, lows=None, spread=0.00004):
    mid = np.asarray(mid, float)
    o = np.r_[mid[0], mid[:-1]]
    h = np.maximum(o, mid) + 0.00001 if highs is None else np.asarray(highs, float)
    l = np.minimum(o, mid) - 0.00001 if lows is None else np.asarray(lows, float)
    t = t0 + 300 * np.arange(len(mid))
    hs = spread / 2
    return ID.Bars("EURUSD", PIP, t, o - hs, h - hs, l - hs, mid - hs, o + hs, h + hs, l + hs, mid + hs)


def path(*legs):
    """A mid path from (bars, to_price) legs, starting at the first leg's price."""
    out = [legs[0][1]]
    for n, px in legs[1:]:
        out += list(np.linspace(out[-1], px, n + 1)[1:])
    return np.array(out)


# ── New York time ───────────────────────────────────────────────────────

def test_new_york_time_follows_the_us_daylight_rules():
    t = np.array([ts(2015, 1, 15, 12), ts(2015, 7, 1, 12), ts(2015, 3, 8, 6, 59), ts(2015, 3, 8, 7),
                  ts(2015, 11, 1, 5, 59), ts(2015, 11, 1, 6), ts(2010, 3, 14, 7), ts(2010, 11, 7, 6)])
    assert list(Q.ny_offset_hours(t)) == [-5, -4, -5, -4, -4, -5, -4, -5]
    b = bars(np.full(3, 1.1), ts(2015, 7, 1, 22))  # 18:00 New York in daylight time: minute 0 of Thursday's day
    day, minute, off = Q.ny_clock(b)
    assert list(minute) == [0, 5, 10] and list(off) == [-4, -4, -4]
    b = bars(np.full(2, 1.1), ts(2015, 1, 14, 22, 55))  # 17:55 New York in standard time: the day's last bar
    day, minute, _ = Q.ny_clock(b)
    assert list(minute) == [1435, 0] and day[1] == day[0] + 1


# ── price quarters ──────────────────────────────────────────────────────

def test_the_fade_rests_a_limit_at_the_first_untouched_quarter_level_and_fills_only_through_it():
    t0 = ts(2015, 7, 1, 6)  # Wednesday 06:00 UTC
    mid = path((0, 1.1015), (12, 1.1016), (6, 1.1020), (6, 1.1027), (20, 1.0990), (10, 1.0990))
    b = bars(mid, t0)
    sig = Q.quarter_fade(b)
    first = sig[0]
    # at 07:00 the day traded 1.1015-1.1016: 1.1025, the first untouched level above, is nearer than 1.1000 below
    assert b.hour[first.i] == 7 and first.side == -1 and first.limit == pytest.approx(1.1025)
    assert first.stop == pytest.approx(1.1025 + 12.5 * PIP) and first.target == pytest.approx(1.1025 - 25 * PIP)
    assert first.valid == 24
    assert all(s.limit != pytest.approx(1.1025) for s in sig[1:])  # one order per level per day
    tr, _ = ID.simulate(b, sig[:1])
    assert tr and tr[0].reason == "target" and tr[0].entry == pytest.approx(1.1025)
    # a level traded before 07:00 is not "untouched": it is never faded that day; the untouched 1.1000 below is
    mid2 = path((0, 1.1010), (10, 1.1026), (14, 1.1012), (24, 1.1008))
    s2 = Q.quarter_fade(bars(mid2, t0))
    assert s2 and all(s.limit != pytest.approx(1.1025) for s in s2)
    assert s2[0].side == 1 and s2[0].limit == pytest.approx(1.1000)


def test_the_break_trades_a_close_through_a_level_once_per_level_and_direction_per_day():
    t0 = ts(2015, 7, 1, 8)
    mid = path((0, 1.0990), (20, 1.0996), (1, 1.1004), (5, 1.0996), (1, 1.1004), (5, 1.1004), (1, 1.0996),
               (10, 1.0996))
    b = bars(mid, t0)
    sig = Q.quarter_break(b)
    ups = [s for s in sig if s.side == 1]
    downs = [s for s in sig if s.side == -1]
    assert len(ups) == 1 and b.c[ups[0].i] == pytest.approx(1.1004)
    assert ups[0].stop == pytest.approx(1.1004 - 12.5 * PIP) and ups[0].target == pytest.approx(1.1004 + 25 * PIP)
    assert len(downs) == 1 and downs[0].i > ups[0].i  # the second break up the same day is not traded


# ── time quarters ───────────────────────────────────────────────────────

def _amd_day(t0, asia, london_up, london_down, london_close):
    """One New York trading day from 18:00 New York: Asia 72 bars between asia[0] and asia[1], London 72 bars
    opening at 1.1005 (the true day open) that reach london_up and london_down and close at london_close, then
    New York AM falling to 1.0950."""
    a = np.tile(asia, 36)
    a[-1] = 1.1005  # Asia's last close: the open of 00:00 New York, the true day open
    ln = path((0, 1.1005), (20, london_up), (20, london_down), (31, london_close))
    ny = path((0, london_close), (72, 1.0950))
    return bars(np.r_[a, ln, ny], t0)


def test_the_daily_cycle_sells_new_york_after_a_one_sided_london_manipulation_above_the_true_day_open():
    t0 = ts(2015, 6, 30, 22)  # Tuesday 18:00 New York (daylight time): Wednesday's trading day
    b = _amd_day(t0, (1.1000, 1.1010), 1.1030, 1.1004, 1.1020)
    sig = Q.daily_amd(b)
    assert len(sig) == 1
    s = sig[0]
    assert s.side == -1 and b.t[s.i] == ts(2015, 7, 1, 9, 55)  # London's last bar, 05:55 New York
    assert s.stop == pytest.approx(b.h[72:144].max() + 0.10 * b.atr[s.i])
    assert s.deadline_hour == 16 and s.max_bars == 72  # 12:00 New York
    tr, _ = ID.simulate(b, sig)
    assert tr[0].entry_t == ts(2015, 7, 1, 10)  # entered at 06:00 New York
    # London took BOTH sides of Asia: no manipulation to fade
    assert Q.daily_amd(_amd_day(t0, (1.1000, 1.1010), 1.1030, 1.0995, 1.1020)) == []
    # London closed back below the true day open: not a sell
    assert Q.daily_amd(_amd_day(t0, (1.1000, 1.1010), 1.1030, 1.1004, 1.1001)) == []


def _session_day(q1, q2_open, q2_extreme, q2_close):
    a = np.tile(q1, 9)  # Q1: 18 bars between its low and high,
    a[-1] = q2_open  # the last closing where Q2 opens: the true session open
    b2 = path((0, q2_open), (8, q2_extreme), (9, q2_close))
    rest = path((0, q2_close), (36, q2_close + 0.0030))
    return np.r_[a, b2, rest]


def test_the_new_york_true_open_buys_after_a_false_move_down_below_the_true_session_open_in_both_seasons():
    for t_q1, utc_signal, deadline in ((ts(2015, 7, 1, 10), ts(2015, 7, 1, 12, 55), 16),
                                       (ts(2015, 1, 14, 11), ts(2015, 1, 14, 13, 55), 17)):
        # pad the trading day from 18:00 New York with flat bars, so the session sits at its New York times
        start = t_q1 - 12 * 3600
        pad = np.full(144, 1.1005)
        mid = np.r_[pad, _session_day((1.1000, 1.1010), 1.1005, 1.0990, 1.0996)]
        b = bars(mid, start)
        sig = Q.ny_true_open(b)
        assert len(sig) == 1
        s = sig[0]
        assert s.side == 1 and b.t[s.i] == utc_signal  # Q2's last bar, 08:55 New York
        assert s.stop == pytest.approx(b.l[144 + 18:144 + 36].min() - 0.10 * b.atr[s.i])
        assert s.deadline_hour == deadline and s.max_bars == 36
        tr, _ = ID.simulate(b, sig)
        assert tr[0].reason == "target"


def test_a_session_without_a_one_sided_false_move_gives_nothing():
    t_q1 = ts(2015, 7, 1, 10)
    pad = np.full(144, 1.1005)
    inside = np.r_[pad, _session_day((1.1000, 1.1010), 1.1005, 1.1002, 1.1003)]
    assert Q.ny_true_open(bars(inside, t_q1 - 12 * 3600)) == []
    above_open = np.r_[pad, _session_day((1.1000, 1.1010), 1.1005, 1.0990, 1.1008)]
    assert Q.ny_true_open(bars(above_open, t_q1 - 12 * 3600)) == []


def test_the_london_session_uses_its_own_true_open_and_ends_at_six_new_york():
    t_q1 = ts(2015, 7, 1, 4)  # 00:00 New York
    pad = np.full(72, 1.1005)
    mid = np.r_[pad, _session_day((1.1000, 1.1010), 1.1005, 1.0990, 1.0996)]
    b = bars(mid, t_q1 - 6 * 3600)
    sig = Q.london_true_open(b)
    assert len(sig) == 1 and b.t[sig[0].i] == ts(2015, 7, 1, 6, 55) and sig[0].deadline_hour == 10


# ── no look-ahead ───────────────────────────────────────────────────────

@pytest.mark.parametrize("rule", [Q.quarter_fade, Q.quarter_break, Q.daily_amd, Q.ny_true_open, Q.london_true_open])
def test_no_rule_reads_a_bar_after_its_signal_bar(rule):
    rng = np.random.default_rng(5)
    n = 288 * 10
    mid = 1.1 + np.cumsum(rng.normal(0, 0.0003, n))
    t0 = ts(2015, 6, 29, 0)
    base = rule(bars(mid, t0))
    assert base  # the walk gives every rule signals to compare
    for k in (n // 3, n // 2, 2 * n // 3):
        moved = mid.copy()
        moved[k + 1:] += np.linspace(0.002, -0.004, n - k - 1)
        after = rule(bars(moved, t0))
        # every signal decided at or before bar k is unchanged: o[k+1] differs, but it is not read at bar k
        assert [s for s in base if s.i < k] == [s for s in after if s.i < k]


# ── QT-2: the London true open, wider ───────────────────────────────────

def test_the_wide_london_true_open_moves_only_the_stop_the_target_and_the_time_exit():
    from aitrader.research.discovery import quarters_wide as W
    t_q1 = ts(2015, 7, 1, 4)
    mid = np.r_[np.full(72, 1.1005), _session_day((1.1000, 1.1010), 1.1005, 1.0990, 1.0996)]
    b = bars(mid, t_q1 - 6 * 3600)
    assert W.london_true_open_wide(b) == Q.london_true_open(b)  # at 1x, 2R, London's end: QT-1's T3 itself
    t3, = Q.london_true_open(b)
    w, = W.london_true_open_wide(b, stop_mult=2.0, r=1.5, until=1080)
    ref = b.c[t3.i]
    assert (w.i, w.side) == (t3.i, t3.side)  # the same signal
    assert ref - w.stop == pytest.approx(2 * (ref - t3.stop)) and w.target - ref == pytest.approx(1.5 * (ref - w.stop))
    assert w.deadline_hour == 16 and w.max_bars == 108  # 12:00 New York, from the 03:00 entry
