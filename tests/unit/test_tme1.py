"""TME-1 on markets built so the answer is known: the calendar gives each month's last four NYSE trading days; the hold
pays both sides and each night's financing; a month missing a close is no trade; the hold reads nothing outside its
own window; a market that rallies at month-end passes and one that does not fails; the judge never reads the
holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date

import pytest

import scripts.tme1 as M


def nyse_days(start: date, end: date) -> list[date]:
    out, y, m = [], start.year, start.month
    while date(y, m, 1) < end:
        out += [d for d in M.trading_days(y, m) if start <= d < end]
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def market(month_end_extra: float, start=date(2002, 8, 1), end=date(2026, 10, 1)) -> dict:
    """IEF gains 0.01% a day plus a fixed alternating wiggle, and month_end_extra more on each of each month's last
    three trading days. The T-bill yield is 2% every day."""
    days = nyse_days(start, end)
    last3 = set()
    for a, b in M.month_ends(start, end):
        last3 |= {d for d in M.trading_days(b.year, b.month) if a < d <= b}
    px, irx, p = {}, {}, 100.0
    for i, d in enumerate(days):
        if i:
            p *= 1 + 0.0001 + (0.003 if i % 2 else -0.003) + (month_end_extra if d in last3 else 0.0)
        px[d], irx[d] = p, 2.0
    return {M.BOND: px, M.RATE: irx}


def test_the_calendar_gives_each_months_last_four_trading_days():
    ends = dict((b, a) for a, b in M.month_ends(date(2012, 10, 1), date(2022, 1, 1)))
    assert ends[date(2021, 12, 31)] == date(2021, 12, 28)  # Christmas observed on Friday the 24th
    assert ends[date(2021, 5, 28)] == date(2021, 5, 25)  # Memorial Day on the 31st
    assert ends[date(2012, 10, 31)] == date(2012, 10, 24)  # Hurricane Sandy closed the 29th and 30th


def test_the_hold_pays_both_sides_and_each_nights_financing():
    data = market(0.0)
    rows, skipped = M.book(data, date(2021, 5, 1), date(2021, 6, 1))
    assert skipped == [] and [r["month_end"] for r in rows] == [date(2021, 5, 28)]
    px = data[M.BOND]
    a, b = date(2021, 5, 25), date(2021, 5, 28)
    expect = px[b] / px[a] - 1 - 2 * M.COST_SIDE - (0.02 + M.MARKUP_PA) * 3 / 365
    assert rows[0]["net"] == pytest.approx(expect)
    x2, _ = M.book(data, date(2021, 5, 1), date(2021, 6, 1), cost_x=2.0)
    assert x2[0]["net"] == pytest.approx(expect - 2 * M.COST_SIDE - M.MARKUP_PA * 3 / 365)


def test_a_month_missing_a_close_or_its_financing_is_no_trade():
    data = market(0.0)
    data[M.BOND] = {d: p for d, p in data[M.BOND].items() if d != date(2015, 6, 26)}  # inside June's window
    rows, skipped = M.book(data, date(2015, 5, 1), date(2015, 8, 1))
    assert [str(r["month_end"]) for r in rows] == ["2015-05-29", "2015-07-31"] and skipped == ["2015-06-30"]
    data = market(0.0)
    data[M.RATE] = {d: v for d, v in data[M.RATE].items() if not date(2015, 9, 1) <= d <= date(2015, 9, 25)}
    rows, skipped = M.book(data, date(2015, 9, 1), date(2015, 10, 1))
    assert rows == [] and skipped == ["2015-09-30"]


def test_the_hold_reads_nothing_outside_its_own_window():
    data = market(0.001)
    before = M.book(data, date(2016, 3, 1), date(2016, 4, 1))[0]
    changed = {d: p * (5.0 if not date(2016, 3, 28) <= d <= date(2016, 3, 31) else 1.0)
               for d, p in data[M.BOND].items()}
    assert M.book({**data, M.BOND: changed}, date(2016, 3, 1), date(2016, 4, 1))[0] == before


def test_a_market_that_rallies_at_month_end_passes_and_one_that_does_not_fails():
    res = M.gates(market(0.0015), thr=3.08)
    assert res["passed"], res["failed_gates"]
    assert res["month_ends"]["n"] == 192  # 2003..2018, every month
    assert res["control"]["mean"] < 0 < res["month_ends"]["mean"]
    flat = M.gates(market(0.0), thr=3.08)
    assert not flat["passed"] and flat["month_ends"]["mean"] < 0 and "t" in flat["failed_gates"]


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (M.BOND, M.RATE):
        body = "date,close\n2018-12-28,1.0\n2018-12-31,1.0\n2019-01-02,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2018, 12, 31) for v in M.load(M.JUDGE[1]).values())
    (tmp_path / "IEF.csv").write_text("date,close\n2018-12-28,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        M.load(M.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_treasury_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "us-treasury-daily": 1}.get(u, 0)  # 1: TSY-1
    assert M.threshold(Reg()) == pytest.approx(max(3.0, M.bonferroni_t(23 + M.TESTS)))
