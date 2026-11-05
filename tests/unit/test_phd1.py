"""PHD-1 on markets built so the answer is known: the holiday rules give the NYSE's published calendars; the event
is the last trading day before each holiday; the computed calendar is checked against the data's own trading days;
the hold pays both sides and each night's financing; a market that pays before holidays passes and one that pays
the same every day fails; the judge never reads the holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

import pytest

import scripts.phd1 as P

KNOWN = {  # the NYSE's own published holiday calendars
    1995: ["1995-01-02", "1995-02-20", "1995-04-14", "1995-05-29", "1995-07-04", "1995-09-04", "1995-11-23",
           "1995-12-25"],
    1998: ["1998-01-01", "1998-01-19", "1998-02-16", "1998-04-10", "1998-05-25", "1998-07-03", "1998-09-07",
           "1998-11-26", "1998-12-25"],
    2021: ["2021-01-01", "2021-01-18", "2021-02-15", "2021-04-02", "2021-05-31", "2021-07-05", "2021-09-06",
           "2021-11-25", "2021-12-24"],
    2022: ["2022-01-17", "2022-02-21", "2022-04-15", "2022-05-30", "2022-06-20", "2022-07-04", "2022-09-05",
           "2022-11-24", "2022-12-26"],
    2023: ["2023-01-02", "2023-01-16", "2023-02-20", "2023-04-07", "2023-05-29", "2023-06-19", "2023-07-04",
           "2023-09-04", "2023-11-23", "2023-12-25"],
}


def test_the_holiday_rules_give_the_nyses_published_calendars():
    for y, ds in KNOWN.items():
        assert sorted(str(d) for d in P.nyse_holidays(y)) == ds, y
    assert date(2021, 12, 31) not in P.nyse_holidays(2021) | P.nyse_holidays(2022)  # a Saturday New Year's Day


def trading_days(a: date, b: date) -> list[date]:
    out, d = [], a
    while d < b:
        if d.weekday() < 5 and d not in P.nyse_holidays(d.year) and d not in P.UNSCHEDULED:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_the_event_is_the_last_trading_day_before_each_holiday():
    days = trading_days(date(2020, 12, 1), date(2022, 2, 1))
    ev = P.event_days(days)
    assert date(2020, 12, 31) in ev  # before New Year's Day 2021 (a Friday)
    assert date(2021, 1, 15) in ev  # the Friday before Martin Luther King Jr. Day
    assert date(2021, 4, 1) in ev  # before Good Friday
    assert date(2021, 11, 24) in ev and date(2021, 12, 23) in ev  # Thanksgiving; Christmas observed on the 24th
    assert date(2021, 12, 31) not in ev  # New Year's Day 2022 fell on a Saturday: no holiday, no event


def market(event_extra: float, start=date(1993, 1, 29), end=date(2022, 1, 1)):
    """SPY gains 0.03% a day plus a small fixed wiggle, and event_extra more on each event day; the T-bill yield is
    2% every day."""
    days = trading_days(start, end)
    ev = P.event_days(days)
    px, irx, p = {}, {}, 100.0
    for i, d in enumerate(days):
        if i:
            p *= 1 + 0.0003 + (0.004 if i % 2 else -0.004) + (event_extra if d in ev else 0.0)
        px[d], irx[d] = p, 2.0
    return {P.MARKET: px, P.RATE: irx}


def test_the_calendar_is_checked_against_the_datas_own_trading_days():
    data = market(0.0)
    assert P.calendar_check(sorted(data[P.MARKET])) == []
    gap = {k: v for k, v in data[P.MARKET].items() if k != date(2010, 6, 15)}
    assert P.calendar_check(sorted(gap)) == ["2010-06-15: a weekday without a close that is no known closure"]
    extra = {**data[P.MARKET], date(2010, 7, 5): 1.0}  # a close on the observed Independence Day
    assert P.calendar_check(sorted(extra)) == ["2010-07-05: a computed holiday with a close"]


def test_the_hold_pays_both_sides_and_each_nights_financing():
    data = market(0.0)
    held = P.days_held(data, date(2021, 1, 1), date(2021, 2, 1))
    d, p = date(2021, 1, 15), date(2021, 1, 14)  # an event day, held from the Thursday's close
    r = data[P.MARKET][d] / data[P.MARKET][p] - 1
    assert held["event"][d] == pytest.approx(r - 2 * P.COST_SIDE - (0.02 + P.MARKUP_PA) / 365)
    m, f = date(2021, 1, 19), date(2021, 1, 15)  # the Tuesday after the holiday: four nights from Friday
    r2 = data[P.MARKET][m] / data[P.MARKET][f] - 1
    assert held["ordinary"][m] == pytest.approx(r2 - 2 * P.COST_SIDE - 4 * (0.02 + P.MARKUP_PA) / 365)


def test_a_market_that_pays_before_holidays_passes_and_one_that_pays_every_day_alike_fails():
    res = P.gates(market(0.004), thr=3.14)
    assert res["passed"], res["failed_gates"]
    assert 200 < res["events"]["n"] < 260  # about nine a year over 27 years
    flat = P.gates(market(0.0), thr=3.14)
    assert not flat["passed"] and "beats_ordinary_days" in flat["failed_gates"]


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (P.MARKET, P.RATE):
        body = "date,close\n2021-12-30,1.0\n2021-12-31,1.0\n2022-01-03,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    assert all(max(v) == date(2021, 12, 31) for v in P.load(P.JUDGE[1]).values())
    (tmp_path / "SPY.csv").write_text("date,close\n2021-12-30,9.0\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        P.load(P.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_us_equity_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "equity-index-b": 2, "us-vol-etp": 2,
                    "us-equity-etf": 2}.get(u, 0)
    assert P.threshold(Reg()) == pytest.approx(max(3.0, P.bonferroni_t(28 + P.TESTS)))
