"""IX-1 (intraday momentum into the cash close): behaviour tests on scenarios whose answer is known by
construction."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import numpy as np

from aitrader.research.discovery import ixmom as IX

SYM = "USA500IDXUSD"
SPREAD = 0.5


def _days(n: int, start: date = date(2015, 1, 5)) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def scenario(n_days: int = 30, cont: float = 0.5, seed: int = 0):
    """Each day the index moves `a` (alternating sign, varying size) from the previous cash close to
    C - 30 min, then `cont * a` more into the close. Bars run 14:30 -> 21:30 UTC (New York winter:
    the close is 21:00 UTC). Bid = mid - SPREAD/2, ask = mid + SPREAD/2; high/low = open (flat bars)."""
    rng = np.random.default_rng(seed)
    t, mid = [], []
    price = 2000.0
    for k, d in enumerate(_days(n_days)):
        c = IX.close_epoch(SYM, d)
        a = (1 if k % 2 == 0 else -1) * (0.002 + 0.002 * rng.random())
        e = c - 1800
        start = c - 6 * 3600 - 1800
        end_mid = price * (1 + a)
        close_mid = end_mid * (1 + cont * a)
        for x in range(start, c + 1800 + 1, 300):
            if x <= e:
                m = price + (end_mid - price) * (x - start) / (e - start)
            elif x <= c:
                m = end_mid + (close_mid - end_mid) * (x - e) / (c - e)
            else:
                m = close_mid
            t.append(x)
            mid.append(m)
        price = close_mid
    t = np.array(t, dtype=np.int64)
    mid = np.array(mid)
    bid, ask = mid - SPREAD / 2, mid + SPREAD / 2
    return IX.Bars(SYM, t, bid, bid.copy(), bid.copy(), ask, ask.copy(), ask.copy())


def test_close_times_follow_the_exchange_clock_through_daylight_saving():
    def utc(sym, d):
        return datetime.fromtimestamp(IX.close_epoch(sym, d), timezone.utc).strftime("%H:%M")
    assert utc("USA500IDXUSD", date(2015, 1, 15)) == "21:00"
    assert utc("USA500IDXUSD", date(2015, 7, 15)) == "20:00"
    assert utc("DEUIDXEUR", date(2015, 1, 15)) == "16:30"
    assert utc("DEUIDXEUR", date(2015, 7, 15)) == "15:30"
    assert utc("JPNIDXJPY", date(2015, 7, 15)) == "06:00"


def test_continuation_into_the_close_is_captured_with_the_known_gross_and_cost():
    b = scenario(cont=0.5)
    ts = IX.trades(b, vol_days=5)
    # Day k has k completed closes behind it; trading starts once 5 last-30-minute returns exist.
    assert len(ts) == 30 - 5
    for x in ts:
        assert x.side == (1 if x.signal > 0 else -1)
        assert x.gross_bps > 0 and not x.stopped
        # cost = one full spread (half at entry, half at exit) in bps of the entry mid, within rounding
        mid_in = x.entry - x.side * SPREAD / 2
        assert abs(x.cost_bps - SPREAD / mid_in * 1e4) < 0.05
        assert abs(x.net_bps - (x.gross_bps - x.cost_bps)) < 1e-9


def test_reversal_into_the_close_loses():
    ts = IX.trades(scenario(cont=-0.5), vol_days=5)
    assert ts and all(x.gross_bps < 0 for x in ts)


def test_a_trade_on_day_k_cannot_see_anything_after_its_entry_quote():
    b = scenario(n_days=30)
    base = IX.trades(b, vol_days=5)
    k = 15
    d = base[k].day
    entry_t = IX.close_epoch(SYM, d) - 1800
    after = b.t > entry_t
    noisy = replace(b, bo=np.where(after, b.bo * 1.05, b.bo), ao=np.where(after, b.ao * 1.05, b.ao),
                    bl=np.where(after, b.bl * 1.05, b.bl), ah=np.where(after, b.ah * 1.05, b.ah))
    moved = IX.trades(noisy, vol_days=5)
    for x, y in zip(base[:k], moved[:k]):
        assert x == y  # every earlier trade is identical
    assert moved[k].day == d and moved[k].side == base[k].side and moved[k].signal == base[k].signal
    assert moved[k].entry == base[k].entry


def test_the_protective_stop_fills_at_the_stop_or_at_a_gapping_open():
    b = scenario(n_days=12)
    ts = IX.trades(b, vol_days=5)
    x = ts[-1]
    c = IX.close_epoch(SYM, x.day)
    i = int(np.flatnonzero(b.t == c - 1800 + 600)[0])  # two bars after entry
    crash = 0.05 * (1 if x.side < 0 else -1)
    bl, ah = b.bl.copy(), b.ah.copy()
    bl[i] = b.bo[i] * (1 + crash) if x.side > 0 else bl[i]
    ah[i] = b.ao[i] * (1 + crash) if x.side < 0 else ah[i]
    y = IX.trades(replace(b, bl=bl, ah=ah), vol_days=5)[-1]
    assert y.stopped and y.exit == y.stop and y.r < -0.99


def test_doubling_costs_doubles_the_spread_paid():
    b = scenario()
    one = IX.trades(b, vol_days=5)
    two = IX.trades(b, vol_days=5, cost_mult=2.0)
    for x, y in zip(one, two):
        assert abs(y.cost_bps - 2 * x.cost_bps) < 1e-6


def test_a_delayed_entry_uses_the_next_bar_and_pays_for_the_move_it_missed():
    b = scenario(cont=0.5)
    now = IX.trades(b, vol_days=5)
    late = IX.trades(b, vol_days=5, delay=1)
    assert len(late) == len(now)
    for x, y in zip(now, late):
        assert y.side == x.side and y.gross_bps < x.gross_bps


def test_the_magnitude_filter_only_removes_days():
    b = scenario(n_days=40, seed=3)
    every = {x.day for x in IX.trades(b, vol_days=5)}
    strong = {x.day for x in IX.trades(b, vol_days=5, min_abs_z=1.0)}
    assert strong < every


def test_summary_reports_t_on_the_daily_book_and_flags_profit_factor():
    s = IX.summary(IX.trades(scenario(cont=0.5), vol_days=5))
    assert s["trades"] == s["days"] and s["net_bps"] > 0 and s["win_rate"] == 1.0
    assert s["profit_factor"] is None  # no losing trade: undefined, never infinite


def test_commission_is_charged_once_per_round_trip_and_scales_with_the_cost_multiplier():
    b = scenario()
    base = IX.trades(b, vol_days=5)
    comm = IX.trades(b, vol_days=5, commission_pts=0.2)
    double = IX.trades(b, vol_days=5, commission_pts=0.2, cost_mult=2.0)
    for x, y, z in zip(base, comm, double):
        mid_in = x.entry - x.side * SPREAD / 2
        assert abs((x.net_bps - y.net_bps) - 0.2 / mid_in * 1e4) < 1e-6
        assert abs((x.net_bps - z.net_bps) - (SPREAD + 0.4) / mid_in * 1e4) < 0.05
