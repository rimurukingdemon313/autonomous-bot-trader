"""MEH-1 on prices and indices built so the answer is known: the month's equity returns are read only from closes
before the month-end; the side follows the dollar's predicted move for each pair's quote; a month-end needs enough
pairs; a flow that moves the pairs into the fix only at month-end passes, and the same move on every weekday is no
month-end effect."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

import scripts.meh1 as M
from aitrader.research.discovery import flow


def index(days: list[date], step) -> tuple[list[date], list[float]]:
    c, cs = 100.0, []
    for i, _ in enumerate(days):
        cs.append(c)
        c *= 1 + step(i)
    return days, cs


def weekdays(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def test_the_months_equity_return_reads_only_closes_before_the_month_end():
    ds, cs = index(weekdays(date(2012, 12, 20), date(2013, 2, 10)), lambda i: 0.01)
    t = date(2013, 1, 31)  # a Thursday: its close is not known at 13:00 London
    r = M.month_to_date((ds, cs), t)
    base, last = cs[ds.index(date(2012, 12, 31))], cs[ds.index(date(2013, 1, 30))]
    assert r == pytest.approx(last / base - 1)
    later = (ds, [v if d < t else 1e9 for d, v in zip(ds, cs)])  # anything from the month-end on
    assert M.month_to_date(later, t) == pytest.approx(r)
    stale = ([d for d in ds if not date(2012, 12, 14) <= d <= date(2012, 12, 31)],
             [v for d, v in zip(ds, cs) if not date(2012, 12, 14) <= d <= date(2012, 12, 31)])
    assert M.month_to_date(stale, t) is None  # no close near the previous month's end: no signal


def test_the_side_follows_the_dollars_predicted_move_for_each_pairs_quote():
    assert M.side("EURUSD", 0.02) == 1 and M.side("USDJPY", 0.02) == -1  # US beat home: the dollar weakens
    assert M.side("AUDUSD", -0.01) == -1 and M.side("USDCAD", -0.01) == 1
    assert M.side("GBPUSD", 0.0) == 0


class Bars:
    def __init__(self, symbol, times, bid, ask):
        self.symbol, self.open_time = symbol, np.array(times, dtype=np.int64)
        self.bid_open, self.ask_open = np.array(bid, float), np.array(ask, float)


def panel(days: list[date], move_bps, pairs=flow.FIX_PAIRS):
    """Each weekday: a pair's mid at 13:00 and 15:00 London is 1.0 (100 for JPY); at 16:00 it has moved by
    move_bps(day, pair) in the dollar-WEAKENING direction (up for XXXUSD, down for USDXXX). Spread 0.2 pip."""
    out = {}
    for p in pairs:
        base, pip = (100.0, 0.01) if p.endswith("JPY") else (1.0, 0.0001)
        times, bid, ask = [], [], []
        for d in days:
            weak = 1 if p in M.USD_QUOTE else -1
            for (hh, mm), px in (((13, 0), base), ((15, 0), base),
                                 ((16, 0), base * (1 + weak * move_bps(d, p) / 1e4))):
                times.append(flow.epoch_at(d, hh, mm, flow.LONDON))
                bid.append(px - 0.1 * pip)
                ask.append(px + 0.1 * pip)
        out[p] = flow.Opens(Bars(p, times, bid, ask))
    return out


def us_beats_home(days):
    """The S&P rises 0.2% a weekday, every home index 0.1%: US beats home every month."""
    return {M.US: index(days, lambda i: 0.002), **{h: index(days, lambda i: 0.001) for h in M.HOME.values()}}


def test_a_month_end_needs_enough_pairs_and_its_observation_is_their_mean():
    days = weekdays(date(2013, 1, 1), date(2013, 2, 28))
    eq = us_beats_home(weekdays(date(2012, 12, 1), date(2013, 3, 1)))
    op = panel(days, lambda d, p: 10.0)
    (e,) = M.events(op, eq, [date(2013, 1, 31)], "MEH1-H1-13-16", flow.Costs())
    assert e["pairs"] == 7 and e["gross_bps"] == pytest.approx(10.0, abs=0.05) and e["net_bps"] < e["gross_bps"]
    few = {p: op[p] for p in list(op)[:3]}
    assert M.events(few, eq, [date(2013, 1, 31)], "MEH1-H1-13-16", flow.Costs()) == []


def judged(move_bps):
    days = weekdays(date(2009, 1, 1), date(2017, 1, 1))
    return M.judge_one(panel(days, move_bps), us_beats_home(weekdays(date(2008, 12, 1), date(2017, 1, 1))),
                       "MEH1-H1-13-16", thr=3.6)


def test_a_flow_into_the_fix_only_at_month_end_passes():
    ends = set(flow.last_business_days(date(2009, 1, 1), date(2017, 1, 1)))
    res = judged(lambda d, p: (8.0 + (d.month % 5)) if d in ends else (1.0 if d.day % 2 else -1.0))
    assert res["passed"], res["failed_gates"]
    assert res["net"]["n"] == 96 and res["specificity_welch_t"] >= 2.0


def test_the_same_move_on_every_weekday_is_no_month_end_effect():
    res = judged(lambda d, p: 8.0 + (d.day % 5))
    assert not res["passed"] and "specificity" in res["failed_gates"] and res["net"]["mean"] > 0
