"""FXT-1 (scripts/fxt1.py) on markets built so the answer is known: the month's decision sees only rates usable at
17:00 New York on its first business day and is filled at the next noon rate; quotes in units per dollar are
inverted; a currency waits for a whole floating look-back; the size targets 10% volatility, capped at 3x; costs are
turnover times the declared rate; a market that trends for years passes every gate and a random walk does not."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta

import numpy as np
import pytest

import scripts.fxt1 as T
from aitrader.data.h10 import NY, available_at


def business_days(a: date, b: date) -> list[date]:
    out, d = [], a
    while d < b:
        if T.is_business(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def prices(ccy: str, a: date, b: date, f) -> T.Prices:
    """`f(i, d)` = dollars per unit on the i-th business day d. A currency quoted per dollar is stored inverted, as
    the H.10 store returns it."""
    ds = business_days(a, b)
    p = np.array([f(i, d) for i, d in enumerate(ds)], float)
    v = 1.0 / p if ccy in T.INVERT else p
    return T.Prices(ccy, ds, v, [available_at(d) for d in ds])


def noon(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, 12, tzinfo=NY).timestamp())


# ── the calendar ──────────────────────────────────────────────────────────

def test_the_month_is_decided_at_17_00_new_york_on_its_first_business_day():
    assert T.last_business_day(2015, 12) == date(2015, 12, 31)
    assert T.last_business_day(2016, 12) == date(2016, 12, 30)  # the 31st is a Saturday
    # 1 January is a holiday and the 2nd and 3rd a weekend: December's last rate is usable on Monday the 4th
    assert T.decision_time(2016, 1) == int(datetime(2016, 1, 4, 17, tzinfo=NY).timestamp())


# ── point in time ─────────────────────────────────────────────────────────

def test_the_signal_sees_only_rates_usable_at_the_decision_and_is_filled_at_the_next_noon():
    rise = prices("GBP", date(1976, 1, 1), date(1978, 6, 1), lambda i, d: 2.0 * (1 + 0.0005 * i))
    crash = prices("GBP", date(1976, 1, 1), date(1978, 6, 1),
                   lambda i, d: 2.0 * (1 + 0.0005 * i) * (0.5 if d >= date(1977, 3, 1) else 1.0))
    # March 1977's decision reads February's last rate at most: the crash from 1 March cannot reach it
    assert T.signal(rise, 1977, 3) > 0 and T.signal(crash, 1977, 3) == pytest.approx(T.signal(rise, 1977, 3))
    i = rise.fill_after(T.decision_time(1977, 3))
    assert rise.dates[i] == date(1977, 3, 2)  # the decision is at 17:00 on 1 March; the next noon is the 2nd's


def test_quotes_per_dollar_are_inverted_so_a_strengthening_yen_is_a_long():
    yen = prices("JPY", date(1976, 1, 1), date(1978, 1, 1), lambda i, d: 0.004 * (1 + 0.001 * i))
    assert yen.p[-1] > yen.p[0] and T.signal(yen, 1977, 6) > 0


def test_a_currency_waits_until_its_whole_look_back_floated():
    aud = prices("AUD", date(1983, 1, 3), date(1986, 6, 1), lambda i, d: 0.9 * (1 + 0.0003 * i))
    assert T.signal(aud, 1984, 12) is None  # its look-back would start in November 1983, before the float
    assert T.signal(aud, 1985, 1) is not None  # from December 1983's close: floating


def test_the_size_targets_ten_percent_volatility_and_stops_at_three_times():
    daily = 0.01  # alternating +1% and -1% plus a drift up: annual volatility about 16%
    jumpy = prices("CHF", date(1976, 1, 1), date(1978, 1, 1),
                   lambda i, d: 0.4 * math.exp(0.0004 * i + (daily if i % 2 else 0.0)))
    w = T.signal(jumpy, 1977, 6)
    px = jumpy
    now = px.known_at(T.decision_time(1977, 6))
    vol = float(np.diff(np.log(px.p[now - 60:now + 1])).std(ddof=1) * math.sqrt(252))
    assert w == pytest.approx(0.10 / vol)
    calm = prices("CHF", date(1976, 1, 1), date(1978, 1, 1), lambda i, d: 0.4 * (1 + 0.00001 * i))
    assert T.signal(calm, 1977, 6) == pytest.approx(3.0)


# ── the book ──────────────────────────────────────────────────────────────

def test_a_month_earns_the_weighted_move_from_fill_to_fill_less_turnover_at_the_declared_cost():
    gbp = prices("GBP", date(1976, 1, 1), date(1978, 6, 1), lambda i, d: 2.0 * (1 + 0.0005 * i))
    rows = T.book({"GBP": gbp}, (date(1977, 3, 1), date(1977, 5, 1)))
    r0, r1 = rows
    i0, i1 = gbp.fill_after(T.decision_time(1977, 3)), gbp.fill_after(T.decision_time(1977, 4))
    w = T.signal(gbp, 1977, 3)
    assert r0["gross"] == pytest.approx(w * (gbp.p[i1] / gbp.p[i0] - 1))
    assert r0["cost"] == pytest.approx(abs(w) * T.COST_BP / 1e4)  # the first month buys the whole position
    assert r1["cost"] == pytest.approx(abs(r1["weights"]["GBP"] - w) * T.COST_BP / 1e4)
    twice = T.book({"GBP": gbp}, (date(1977, 3, 1), date(1977, 5, 1)), k=2.0)
    assert [x["cost"] for x in twice] == pytest.approx([2 * x["cost"] for x in rows])


def test_a_later_rate_changes_no_earlier_month():
    span = (date(1977, 1, 1), date(1978, 1, 1))
    a = prices("CAD", date(1975, 6, 1), date(1978, 6, 1), lambda i, d: 0.9 * (1 + 0.0004 * i))
    b = prices("CAD", date(1975, 6, 1), date(1978, 6, 1),
               lambda i, d: 0.9 * (1 + 0.0004 * i) * (3.0 if d >= date(1977, 9, 15) else 1.0))
    ra, rb = T.book({"CAD": a}, span), T.book({"CAD": b}, span)
    assert [r["net"] for r in ra[:8]] == pytest.approx([r["net"] for r in rb[:8]])  # January to August 1977


# ── the gates ─────────────────────────────────────────────────────────────

@pytest.fixture
def short_program(monkeypatch):
    monkeypatch.setattr(T, "PERIOD", (date(1975, 1, 1), date(1984, 1, 1)))
    monkeypatch.setattr(T, "DEV", (date(1975, 1, 1), date(1980, 1, 1)))
    monkeypatch.setattr(T, "VAL", (date(1980, 1, 1), date(1984, 1, 1)))
    monkeypatch.setattr(T, "BOOT_N", 300)


def trending(seed: int):
    """Each currency swings in a slow cycle (4-6 years, ±30%), with daily noise: a year's trend tends to continue."""
    rng = np.random.default_rng(seed)
    out = {}
    for j, c in enumerate(("GBP", "JPY", "CHF", "CAD")):
        period, phase = 1000 + 250 * j, rng.uniform(0, 2 * math.pi)
        noise = np.cumsum(rng.normal(0, 0.002, 4000))
        out[c] = prices(c, date(1972, 1, 3), date(1984, 3, 1),
                        lambda i, d, p=period, ph=phase, z=noise: math.exp(0.3 * math.sin(2 * math.pi * i / p + ph)
                                                                           + z[i]))
    return out


def test_a_market_that_trends_for_years_passes_every_gate(short_program):
    res = T.evaluate(trending(1), 3.6)
    assert res["passed"], res["failed_gates"]
    assert res["all"]["sharpe"] > 1.0 and res["random_signs"]["welch_t_vs_random"] >= 2.0


def test_a_random_walk_fails(short_program):
    rng = np.random.default_rng(5)
    walk = {c: prices(c, date(1972, 1, 3), date(1984, 3, 1),
                      lambda i, d, z=np.cumsum(rng.normal(0, 0.006, 4000)): math.exp(z[i]))
            for c in ("GBP", "JPY", "CHF", "CAD")}
    res = T.evaluate(walk, 3.6)
    assert not res["passed"] and "t" in res["failed_gates"]


def test_the_judged_years_end_before_any_fx_test_here_began_and_the_holdout_is_the_seal():
    assert T.PERIOD == (date(1975, 1, 1), date(1990, 1, 1)) and T.HOLD[0] == date(2017, 1, 1)
    assert T.DEV[1] == T.VAL[0] and T.DEV[0] == T.PERIOD[0] and T.VAL[1] == T.PERIOD[1]
