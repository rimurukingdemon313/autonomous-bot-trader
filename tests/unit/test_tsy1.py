"""TSY-1 on markets built so the answer is known: the events are the 10-year nominal note auctions and nothing else;
each leg pays both sides and its own financing; an auction off the calendar, too close to the last, or without a rate
is no trade; an event reads nothing after its last close; a market with the auction cycle passes and one without it
fails; the judge never reads the holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

import pytest

import scripts.tsy1 as T


def weekdays(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days) if (a + timedelta(days=i)).weekday() < 5]


def second_wednesday(y: int, m: int) -> date:
    d = date(y, m, 1)
    d += timedelta(days=(2 - d.weekday()) % 7)
    return d + timedelta(days=7)


def note(d: date, term: str, kind: str = "Note", tips: str = "No", frn: str = "No", orig: str = "") -> dict:
    return {"auction_date": str(d), "security_type": kind, "security_term": term, "original_security_term": orig,
            "reopening": "No", "inflation_index_security": tips, "floating_rate": frn}


def records(start=date(2008, 6, 1), end=date(2026, 10, 1)) -> list[dict]:
    """A 10-year auction on each month's second Wednesday (a new issue each quarter, a reopening otherwise), and the
    auctions that are not events: the 3-year the day before, the 30-year bond the day after, 10-year TIPS, a 2-year
    FRN and the 7-year near the month's end."""
    out = []
    y, m = start.year, start.month
    while date(y, m, 1) < end:
        w = second_wednesday(y, m)
        out.append(note(w, "10-Year" if m % 3 == 2 else "9-Year 11-Month", orig="10-Year" if m % 3 != 2 else ""))
        out += [note(w - timedelta(days=1), "3-Year"), note(w + timedelta(days=1), "30-Year", kind="Bond"),
                note(date(y, m, 20), "10-Year", tips="Yes"), note(date(y, m, 26), "2-Year", frn="Yes"),
                note(date(y, m, 27), "7-Year")]
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def market(cycle: float, start=date(2008, 6, 1), end=date(2026, 10, 1)) -> dict:
    """IEF gains 0.01% a day plus a fixed alternating wiggle; with `cycle`, it also loses `cycle` on each of the five
    days before a 10-year auction and gains it on each of the five after. The T-bill yield is 2% every day."""
    days = weekdays(start, end)
    auctions = [d for d in T.auction_days(records(start, end)) if d in set(days)]
    pos = {d: i for i, d in enumerate(days)}
    extra = [0.0] * len(days)
    for d in auctions:
        a = pos[d]
        for k in range(1, 6):
            if a - k >= 0:
                extra[a - k] -= cycle
            if a + k < len(days):
                extra[a + k] += cycle
    px, irx, p = {}, {}, 100.0
    for i, d in enumerate(days):
        if i:
            p *= 1 + 0.0001 + (0.003 if i % 2 else -0.003) + extra[i]
        px[d], irx[d] = p, 2.0
    return {T.BOND: px, T.RATE: irx, "auctions": T.auction_days(records(start, end))}


def test_the_events_are_the_ten_year_nominal_note_auctions():
    days = T.auction_days(records(date(2010, 1, 1), date(2010, 4, 1)))
    assert days == [second_wednesday(2010, m) for m in (1, 2, 3)]  # no TIPS, FRN, bond, 3-year or 7-year
    assert T.is_ten_year_note(note(date(2010, 3, 10), "9-Year 10-Month"))  # a reopening, even with no original term
    assert not T.is_ten_year_note(note(date(2010, 3, 10), "9-Year 10-Month", tips="Yes"))


def test_each_leg_pays_both_sides_and_its_own_financing():
    data = market(0.0)
    rows, _ = T.book(data, date(2012, 3, 1), date(2012, 4, 1))
    assert len(rows) == 1 and rows[0]["auction"] == date(2012, 3, 14)
    px = data[T.BOND]
    days = sorted(px)
    a = days.index(date(2012, 3, 14))
    s0, s1, l0, l1 = days[a - 6], days[a - 1], days[a], days[a + 5]
    assert (s0, s1, l0, l1) == (date(2012, 3, 6), date(2012, 3, 13), date(2012, 3, 14), date(2012, 3, 21))
    short = -(px[s1] / px[s0] - 1) - 2 * T.COST_SIDE + (0.02 - T.MARKUP_PA) * 7 / 365
    long = px[l1] / px[l0] - 1 - 2 * T.COST_SIDE - (0.02 + T.MARKUP_PA) * 7 / 365
    assert rows[0]["short"] == pytest.approx(short) and rows[0]["long"] == pytest.approx(long)
    assert rows[0]["net"] == pytest.approx(short + long)
    x2, _ = T.book(data, date(2012, 3, 1), date(2012, 4, 1), cost_x=2.0)
    assert x2[0]["net"] == pytest.approx(short + long - 4 * T.COST_SIDE - 2 * T.MARKUP_PA * 7 / 365)


def test_an_auction_off_the_calendar_too_close_to_the_last_or_without_a_rate_is_no_trade():
    data = market(0.0)
    data["auctions"] = sorted(data["auctions"] + [date(2012, 5, 19), date(2012, 5, 18)])  # a Saturday; 2 days later
    rows, skipped = T.book(data, date(2012, 5, 1), date(2012, 6, 1))
    assert [r["auction"] for r in rows] == [date(2012, 5, 9)]
    assert skipped["off_calendar"] == ["2012-05-19"] and skipped["overlap"] == ["2012-05-18"]
    gap = date(2012, 6, 5)  # no T-bill yield in the three weeks up to the close the June short leg opens at
    data[T.RATE] = {d: v for d, v in data[T.RATE].items() if not gap - timedelta(days=21) <= d <= gap}
    rows, skipped = T.book(data, date(2012, 6, 1), date(2012, 7, 1))
    assert rows == [] and skipped["no_rate"] == ["2012-06-13"]


def test_an_event_reads_nothing_after_its_last_close_or_before_its_first():
    data = market(0.001)
    before = T.book(data, date(2014, 9, 1), date(2014, 10, 1))[0]
    changed = {d: p * (3.0 if d > date(2014, 9, 17) or d < date(2014, 9, 2) else 1.0)
               for d, p in data[T.BOND].items()}
    after = T.book({**data, T.BOND: changed}, date(2014, 9, 1), date(2014, 10, 1))[0]
    assert before[0]["auction"] == date(2014, 9, 10) and after == before


def test_a_market_with_the_auction_cycle_passes_and_one_without_it_fails():
    res = T.gates(market(0.0012), thr=3.09)
    assert res["passed"], res["failed_gates"]
    assert res["events"]["n"] == 144  # twelve 10-year auctions a year, 2009..2020
    assert res["short_leg"]["mean"] > 0 and res["long_leg"]["mean"] > 0
    flat = T.gates(market(0.0), thr=3.09)
    assert not flat["passed"] and flat["events"]["mean"] < 0
    assert {"t", "both_legs"} <= set(flat["failed_gates"])


def test_the_judge_never_reads_the_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "DATA", tmp_path)
    man = {"series": {}}
    for sym in (T.BOND, T.RATE):
        body = "date,close\n2020-12-30,1.0\n2020-12-31,1.0\n2021-01-04,2.0\n"
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    rows = [note(date(2020, 12, 9), "9-Year 11-Month"), note(date(2021, 1, 12), "10-Year")]
    body = ",".join(T.AUCTION_FIELDS) + "\n" + "".join(",".join(r[k] for k in T.AUCTION_FIELDS) + "\n" for r in rows)
    (tmp_path / "auctions.csv").write_text(body)
    man["series"]["auctions"] = {"file": "auctions.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    data = T.load(T.JUDGE[1])
    assert all(max(data[s]) == date(2020, 12, 31) for s in (T.BOND, T.RATE))
    assert data["auctions"] == [date(2020, 12, 9)]
    (tmp_path / "auctions.csv").write_text(body.replace("2021-01-12", "2021-01-13"))
    with pytest.raises(SystemExit, match="does not match its manifest"):
        T.load(T.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_treasury_data():
    class Reg:
        def tests_on(self, u, a, b):
            return {"multi-asset-etf": 12, "multi-asset-long": 10, "us-treasury-daily": 0}.get(u, 0)
    assert T.threshold(Reg()) == pytest.approx(max(3.0, T.bonferroni_t(22 + T.TESTS)))
    assert round(T.threshold(Reg()), 4) == 3.0654  # the frozen spec's threshold
