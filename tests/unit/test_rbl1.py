"""RBL-1 on markets built so the answer is known: the calendar gives each month's rebalance, T-4, T and T+1; the signal
is the 60/40 portfolio's equity drift since the last rebalance; each side pays its costs and its financing; a month
missing a close is no trade; the hold reads nothing outside the rebalance close and its own window; a market that
reverses its month's stock-bond gap in the last week passes and one that does not fails; the judge never reads the
holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date

import pytest

import scripts.rbl1 as B


def nyse_days(start: date, end: date) -> list[date]:
    out, y, m = [], start.year, start.month
    while date(y, m, 1) < end:
        out += [d for d in B.trading_days(y, m) if start <= d < end]
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def market(reversal: float, start=date(2002, 8, 1), end=date(2026, 10, 1)) -> dict:
    """Stocks beat bonds by 3% over the first part of odd months and trail them by 3% in even months; over each month's
    last week and the next month's first day (T-3..T+1) stocks then move by `reversal` a day against that gap. A small
    alternating wiggle and a 0.02% daily drift ride on top. Bonds drift 0.01% a day. The T-bill yield is 2% every day."""
    days = nyse_days(start, end)
    hold, sign_of = set(), {}
    for mo in B.months(start, end):
        sign = 1 if mo["month_end"].month % 2 else -1
        for d in [d for d in B.trading_days(mo["open"].year, mo["open"].month) if d > mo["open"]] + [mo["close"]]:
            hold.add(d)
            sign_of[d] = sign
    early = {}
    for mo in B.months(start, end):
        sign = 1 if mo["month_end"].month % 2 else -1
        span = [d for d in B.trading_days(mo["open"].year, mo["open"].month) if d <= mo["open"]]
        for d in span:
            early[d] = sign * 0.03 / len(span)
    sp, bd, irx, p, q = {}, {}, {}, 100.0, 100.0
    for i, d in enumerate(days):
        if i:
            wiggle = 0.002 if i % 2 else -0.002
            move = -sign_of[d] * reversal if d in hold else early.get(d, 0.0)
            p *= 1 + 0.0002 + wiggle + move
            q *= 1 + 0.0001
        sp[d], bd[d], irx[d] = p, q, 2.0
    return {B.MARKET: sp, B.BOND: bd, B.RATE: irx}


def test_the_calendar_gives_each_months_rebalance_open_end_and_close():
    mos = {mo["month_end"]: mo for mo in B.months(date(2021, 1, 1), date(2022, 1, 1))}
    may = mos[date(2021, 5, 28)]  # Memorial Day on the 31st
    assert (may["rebalance"], may["open"], may["close"]) == (date(2021, 4, 30), date(2021, 5, 24), date(2021, 6, 1))
    dec = mos[date(2021, 12, 31)]  # Christmas observed on Friday the 24th; New Year's Day 2022 fell on a Saturday
    assert (dec["open"], dec["close"]) == (date(2021, 12, 27), date(2022, 1, 3))


def test_the_signal_is_the_60_40_portfolios_equity_drift():
    data = {B.MARKET: {date(2021, 4, 30): 100.0, date(2021, 5, 24): 110.0},
            B.BOND: {date(2021, 4, 30): 50.0, date(2021, 5, 24): 50.0}}
    assert B.signal(data, date(2021, 4, 30), date(2021, 5, 24)) == pytest.approx(0.66 / 1.06 - 0.6)
    assert B.signal(data, date(2021, 4, 29), date(2021, 5, 24)) is None  # a missing close is no signal


def test_each_side_pays_its_costs_and_its_financing():
    data = market(0.0)
    rows, skipped = B.book(data, date(2021, 6, 1), date(2021, 7, 2))  # the holds that close on June 1 and July 1
    assert skipped == [] and [(r["month_end"], r["side"]) for r in rows] == [(date(2021, 5, 28), -1),
                                                                             (date(2021, 6, 30), 1)]
    sp = data[B.MARKET]
    a, b = date(2021, 5, 24), date(2021, 6, 1)  # May: stocks ran ahead, so short; eight nights
    short = -(sp[b] / sp[a] - 1) - 2 * B.COST_SIDE + (0.02 - B.MARKUP_PA) * 8 / 365
    assert rows[0]["net"] == pytest.approx(short)
    a, b = date(2021, 6, 24), date(2021, 7, 1)  # June: stocks fell behind, so long; seven nights
    long = sp[b] / sp[a] - 1 - 2 * B.COST_SIDE - (0.02 + B.MARKUP_PA) * 7 / 365
    rows, _ = B.book(data, date(2021, 6, 2), date(2021, 8, 1))
    assert rows[0]["net"] == pytest.approx(long)
    x2, _ = B.book(data, date(2021, 6, 2), date(2021, 8, 1), cost_x=2.0)
    assert x2[0]["net"] == pytest.approx(long - 2 * B.COST_SIDE - B.MARKUP_PA * 7 / 365)


def test_a_month_missing_a_close_or_its_financing_is_no_trade():
    data = market(0.0)
    data[B.MARKET] = {d: p for d, p in data[B.MARKET].items() if d != date(2015, 6, 29)}  # inside June's hold
    rows, skipped = B.book(data, date(2015, 6, 1), date(2015, 8, 4))  # the holds that close on June 1 to August 3
    assert [str(r["month_end"]) for r in rows] == ["2015-05-29", "2015-07-31"] and skipped == ["2015-06-30"]
    data = market(0.0)
    data[B.RATE] = {d: v for d, v in data[B.RATE].items() if not date(2015, 9, 1) <= d <= date(2015, 9, 24)}
    rows, skipped = B.book(data, date(2015, 10, 1), date(2015, 10, 2))  # September's hold closes on October 1
    assert rows == [] and skipped == ["2015-09-30"]


def test_the_hold_reads_nothing_but_the_rebalance_close_and_its_own_window():
    data = market(0.004)
    before = B.book(data, date(2016, 3, 2), date(2016, 4, 2))[0]  # March's hold: the 24th (Good Friday the 25th) to April 1
    assert [r["month_end"] for r in before] == [date(2016, 3, 31)]
    keep = {date(2016, 2, 29)} | {d for d in data[B.MARKET] if date(2016, 3, 24) <= d <= date(2016, 4, 1)}
    changed = {s: {d: p * (1.0 if d in keep else 7.0) for d, p in data[s].items()} for s in (B.MARKET, B.BOND)}
    assert B.book({**data, **changed}, date(2016, 3, 2), date(2016, 4, 2))[0] == before


def test_a_market_that_reverses_the_months_gap_passes_and_one_that_does_not_fails():
    res = B.gates(market(0.002), thr=3.18)
    assert res["passed"], res["failed_gates"]
    assert res["months"]["n"] == 192  # the holds closing in 2003..2018: December 2002 to November 2018
    assert res["short_months"]["n"] == res["long_months"]["n"] == 96
    flat = B.gates(market(0.0), thr=3.18)
    assert not flat["passed"] and "t" in flat["failed_gates"]
    wrong = B.gates(market(-0.002), thr=3.18)  # the last week follows the gap instead of reversing it
    assert not wrong["passed"] and wrong["months"]["mean"] < 0


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (B.MARKET, B.BOND, B.RATE):
        body = "date,close\n2018-12-28,1.0\n2018-12-31,1.0\n2019-01-02,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2018, 12, 31) for v in B.load(B.JUDGE[1]).values())
    (tmp_path / "SPY.csv").write_text("date,close\n2018-12-28,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        B.load(B.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_us_equity_and_treasury_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "equity-index-b": 2, "us-vol-etp": 2,
                    "us-equity-etf": 5, "us-treasury-daily": 2}.get(u, 0)
    assert B.threshold(Reg()) == pytest.approx(max(3.0, B.bonferroni_t(33 + B.TESTS)))
    assert round(B.threshold(Reg()), 4) == 3.1804
