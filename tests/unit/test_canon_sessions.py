"""NE-ON / NE-GAP order builders: causality by truncation (with a planted leak the check must catch), and
the rules' meaning on constructed New York sessions."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

from aitrader.research.canon import engine as E
from aitrader.research.canon import sessions as S


def hourly(days: int, seed: int = 0, start: date = date(2015, 1, 5), gap_bp: dict | None = None) -> E.Quotes:
    """23 hours a weekday (the CFD pauses 17:00-18:00 New York), a random walk with bid/ask; `gap_bp` maps a
    trading-day number to an extra move placed in that day's 09:00 bar."""
    rng = np.random.default_rng(seed)
    ts, mids = [], []
    px = 2000.0
    d, k = start, 0
    while k < days:
        if d.weekday() < 5:
            for h in range(24):
                if h == 17:
                    continue
                t = int(datetime(d.year, d.month, d.day, h, tzinfo=S.NY).timestamp())
                step = rng.normal(0, 2.0)
                if gap_bp and k in gap_bp and h == 9:
                    step += px * gap_bp[k] / 1e4
                ts.append(t)
                mids.append((px, px + step))
                px += step
            k += 1
        d += timedelta(days=1)
    o = np.array([m[0] for m in mids])
    c = np.array([m[1] for m in mids])
    h, lo = np.maximum(o, c) + 0.5, np.minimum(o, c) - 0.5
    hs = 0.25
    t = np.array(ts, np.int64)
    order = np.argsort(t)
    t, o, h, lo, c = t[order], o[order], h[order], lo[order], c[order]
    return E.Quotes("USA500IDXUSD", 3600, t, o - hs, h - hs, lo - hs, c - hs, o + hs, h + hs, lo + hs, c + hs)


def causal(builder, q: E.Quotes, cuts) -> bool:
    """Orders built on data cut at bar k equal the full-data orders decided at or before k. The cuts include
    every full-data decision bar: a one-bar leak only shows when the cut lands exactly on the decision."""
    full = builder(q)
    for k in sorted(set(int(c) for c in cuts) | {o.decided_i for o in full}):
        part = builder(q.truncated(k))
        want = [o for o in full if o.decided_i <= k]
        got = [o for o in part if o.decided_i <= k]
        if got != want:
            return False
    return True


@pytest.mark.parametrize("builder", [
    lambda q: S.overnight(q, vol_days=20),
    lambda q: S.gap_reversal(q, z=1.0, vol_days=20),
    lambda q: S.gap_reversal(q, z=0.0, vol_days=20, how="follow"),
])
def test_orders_are_decided_from_the_past_only(builder):
    q = hourly(120)
    cuts = np.linspace(600, len(q) - 2, 25).astype(int)
    assert causal(builder, q, cuts)


def test_the_truncation_check_catches_a_planted_one_bar_leak():
    q = hourly(120)

    def leaky(q):  # decides with the NEXT bar's close: g measured one bar too late
        shifted = replace(q, bc=np.r_[q.bc[1:], q.bc[-1]], ac=np.r_[q.ac[1:], q.ac[-1]])
        return S.gap_reversal(shifted, z=0.5, vol_days=20)

    assert not causal(leaky, q, np.linspace(600, len(q) - 2, 25).astype(int))


def test_a_large_gap_down_is_faded_long_and_followed_short():
    q = hourly(100, gap_bp={90: -150})
    d = S.trading_dates(q, 9)[90]
    fade = [o for o in S.gap_reversal(q, z=1.0, vol_days=60) if o.tag == f"GAP {d}"]
    follow = [o for o in S.gap_reversal(q, z=1.0, vol_days=60, how="follow") if o.tag == f"GAP {d}"]
    assert fade and fade[0].side == 1 and follow and follow[0].side == -1
    assert fade[0].exit_at == S.ny_epoch(d, 16)


def test_overnight_orders_enter_at_the_cash_close_and_exit_next_morning_over_weekends():
    q = hourly(80)
    orders = S.overnight(q, vol_days=20)
    fri = [o for o in orders if datetime.fromtimestamp(int(q.t[o.decided_i + 1]), timezone.utc).astimezone(S.NY)
           .weekday() == 4]
    assert fri
    for o in orders:
        entry = datetime.fromtimestamp(int(q.t[o.decided_i + 1]), timezone.utc).astimezone(S.NY)
        out = datetime.fromtimestamp(o.exit_at, timezone.utc).astimezone(S.NY)
        assert entry.hour == 16 and out.hour == 9 and out.date() == S.next_weekday(entry.date())


def test_no_order_exists_before_its_volatility_history_does():
    q = hourly(80)
    assert len(S.overnight(q, vol_days=60)) <= 80 - 60
    assert len(S.overnight(q, vol_days=20)) > len(S.overnight(q, vol_days=60))


def test_the_placebos_keep_count_side_and_holding_time():
    q = hourly(150)
    real = S.overnight(q, vol_days=20)
    pl = S.random_windows(q, real, seed=1)
    assert abs(len(pl) - len(real)) <= 2
    assert {o.side for o in pl} == {1}
    rs = S.random_sides(real, seed=2)
    assert [o.decided_i for o in rs] == [o.decided_i for o in real] and {o.side for o in rs} == {-1, 1}
