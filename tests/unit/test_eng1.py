"""ENG-1 (scripts/eng1.py) on curves built so that every answer is known.

On a market whose level never moves, a contract bought as contract 2 on a curve with log slope beta per month earns
exactly e^beta - 1 by the next month: it rolls up (or down) the curve. That is the storage premium in its purest form.
If the program priced the wrong contract at either end, the return would differ. So these tests check:
- the exchange's expiry rules, on real expiry dates;
- that the contract is identified across every roll;
- that the book is long only when the curve says so;
- the costs, the baselines, and that the holdout's data cannot reach the judge."""

from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np

import scripts.eng1 as E

HOLIDAYS = {date(2024, 11, 28), date(2024, 12, 25), date(2025, 1, 1)}


def weekdays(a: date, b: date, holidays=frozenset()) -> list[date]:
    out, d = [], a
    while d < b:
        if d.weekday() < 5 and d not in holidays:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_the_expiry_rules_match_real_last_trading_days():
    bd = weekdays(date(2024, 10, 1), date(2025, 3, 1), HOLIDAYS)
    assert E.expiry("WTI", (2024, 12), bd) == date(2024, 11, 20)  # CLZ24: 3 business days before Monday the 25th
    assert E.expiry("WTI", (2025, 1), bd) == date(2024, 12, 19)  # CLF25: the 25th is Christmas; 3 before the 24th
    assert E.expiry("HEATING_OIL", (2024, 12), bd) == date(2024, 11, 29)  # HOZ24: November's last business day
    assert E.expiry("NATGAS", (2024, 12), bd) == date(2024, 11, 26)  # NGZ24: 3 business days before Dec 1, Thanksgiving out
    assert E.front_delivery("WTI", date(2024, 11, 20), bd) == (2024, 12)  # its last trading day: still contract 1
    assert E.front_delivery("WTI", date(2024, 11, 21), bd) == (2025, 1)


def calendar(a: date, b: date) -> list[date]:
    return E.extended(weekdays(a, b))


def built(kind: str, a: date, b: date, beta_of, level_of=lambda d: 100.0, bdays=None) -> E.Curve:
    """Contracts priced at level * exp(-beta * months to delivery beyond the front), as EIA's contracts 1-3 are: beta > 0
    is backwardation. beta_of(d) and level_of(d) by day; priced on the weekdays of [a, b)."""
    bdays = bdays or calendar(a, b)
    days = [d for d in bdays if a <= d < b]
    c = {}
    for d in days:
        f = E.front_delivery(kind, d, bdays)
        c[d] = tuple(level_of(d) * math.exp(-beta_of(d) * k) for k in range(3))
        assert E.price_of(E.Curve(kind, [d], c), E._month_add(*f, 2), d, bdays) == c[d][2]
    return E.Curve(kind, days, c)


def regime(d: date) -> float:
    """Backwardated for three months, then in contango for three: a known pattern, by calendar month."""
    return 0.02 if ((d.year * 12 + d.month) // 3) % 2 == 0 else -0.015


def test_the_held_contract_is_identified_across_every_roll_whatever_the_expiry_rule():
    a, b = date(2000, 1, 1), date(2003, 1, 1)
    bdays = calendar(a, b)
    for kind in ("WTI", "HEATING_OIL", "RBOB", "NATGAS"):
        cv = built(kind, a, b, regime, bdays=bdays)
        lg = E.legs({kind: cv}, bdays, b)[kind]
        assert len(lg) >= 34
        for mo, r in lg.items():
            beta = regime(r["t"])  # the slope on the day it was bought
            assert abs(r["ret"] - (math.exp(beta) - 1)) < 1e-12, (kind, mo)  # it rolled up (or down) the curve
            assert (r["basis"] > 0) == (beta > 0) and abs(r["basis"] - 12 * beta) < 1e-12


def market(level_of=lambda d: 100.0, a=date(1990, 1, 1), b=date(2020, 1, 1)):
    bdays = calendar(a, b)
    curves = {k: built(k, a, b, regime, level_of, bdays) for k in ("WTI", "NATGAS")}
    return curves, bdays


def test_the_book_is_long_only_when_backwardated_and_earns_the_roll():
    curves, bdays = market()
    lg = E.legs(curves, bdays, date(2020, 1, 1))
    rows = [r for r in E.book(lg, (date(1991, 1, 1), date(2019, 1, 1))) if r["n"] > 0]
    assert rows
    for r in rows:
        for n, e in r["exposure"].items():
            mo = tuple(int(x) for x in r["month"].split("-"))
            assert (e > 0) == (lg[n][mo]["basis"] > 0)  # long exactly when contract 2 was above contract 3
            assert e * lg[n][mo]["ret"] >= 0  # so it never holds a contango month
    always = [r for r in E.book(lg, (date(1991, 1, 1), date(2019, 1, 1)), always=True) if r["n"] > 0]
    assert np.mean([r["net"] for r in rows]) > np.mean([r["net"] for r in always]) > -1


def test_costs_are_charged_on_every_entry_exit_and_monthly_roll():
    curves, bdays = market()
    lg = E.legs(curves, bdays, date(2020, 1, 1))
    rows = E.book({"WTI": lg["WTI"]}, (date(1991, 1, 1), date(1995, 1, 1)))
    prev = 0.0
    for r in rows:
        e = r["exposure"].get("WTI", 0.0)
        assert abs(r["trade_cost"] - abs(e - prev) * E.COST_BP["WTI"] / 1e4) < 1e-15
        assert abs(r["roll_cost"] - e * E.COST_BP["WTI"] / 1e4) < 1e-15
        assert abs(r["net"] - (r["gross"] - r["trade_cost"] - r["roll_cost"])) < 1e-15
        prev = e
    doubled = E.book({"WTI": lg["WTI"]}, (date(1991, 1, 1), date(1995, 1, 1)), k=2.0)
    assert all(abs(d["trade_cost"] - 2 * r["trade_cost"]) < 1e-15 for d, r in zip(doubled, rows))


def test_the_holdout_cannot_reach_the_judge():
    calm = market()
    wild = market(level_of=lambda d: 100.0 if d < date(2019, 1, 1) else 100.0 * (1 + (d.toordinal() % 7)))
    a = E.legs(calm[0], calm[1], E.JUDGE[1])
    b = E.legs(wild[0], wild[1], E.JUDGE[1])
    assert a == b  # what happens from 2019 on changes nothing the judge reads
    assert max(max(rows) for rows in a.values()) <= (2018, 12)


def test_a_curve_with_information_passes_its_gates_and_one_without_fails_them():
    rng = np.random.default_rng(5)
    noise = {}

    def noisy(d):  # a level that wanders, so the roll is not the only return
        k = (d.year, d.month)
        noise.setdefault(k, float(np.exp(rng.normal(0, 0.01))))
        return 100.0 * noise[k]
    curves, bdays = market(level_of=noisy)
    lg = E.legs(curves, bdays, E.JUDGE[1])
    good = E.evaluate(lg, (date(1991, 1, 1), date(2019, 1, 1)), 3.0, permutations=200)
    assert good["passed"], good["failed_gates"]

    def no_info(d):  # the sign of the slope says nothing: the level moves against the roll, half the time
        k = (d.year, d.month)
        noise.setdefault(("x",) + k, float(np.exp(rng.normal(0, 0.08))))
        return 100.0 * noise[("x",) + k]
    curves, bdays = market(level_of=no_info)
    lg = E.legs(curves, bdays, E.JUDGE[1])
    flat = {k: {mo: {**r, "basis": float(rng.normal())} for mo, r in v.items()} for k, v in lg.items()}
    bad = E.evaluate(flat, (date(1991, 1, 1), date(2019, 1, 1)), 3.0, permutations=200)
    assert not bad["passed"] and "t" in bad["failed_gates"]
