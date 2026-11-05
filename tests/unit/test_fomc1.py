"""FOMC-1 on quotes built so the answer is known: the window enters at 14:00 New York the weekday before the statement
and leaves at 13:55 on its day, through daylight saving; the spread, the slippage and each night's financing are
paid; a missing quote or an unknown rate is no trade; a drift that only the events have passes and one the ordinary
weeks share fails the timing gate; the calendar is checked at its source; the judge never reads the holdout."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone

import pytest

import scripts.fomc1 as F


def test_the_window_enters_the_weekday_before_at_14_00_and_leaves_at_13_55_through_daylight_saving():
    (ev, before, after) = F.windows((date(2015, 1, 28),))  # a Wednesday, New York on EST
    assert (ev["kind"], ev["entry_day"], ev["exit_day"]) == ("event", date(2015, 1, 27), date(2015, 1, 28))
    assert (before["entry_day"], before["exit_day"]) == (date(2015, 1, 20), date(2015, 1, 21))
    assert (after["entry_day"], after["exit_day"]) == (date(2015, 2, 3), date(2015, 2, 4))
    utc = lambda e: datetime.fromtimestamp(e, timezone.utc).strftime("%H:%M")  # noqa: E731
    assert utc(F.minute_end(date(2015, 1, 27), F.ENTRY_NY)) == "18:59"  # its close is 19:00 UTC, 14:00 EST
    assert utc(F.minute_end(date(2015, 3, 18), F.EXIT_NY)) == "17:54"   # its close is 17:55 UTC, 13:55 EDT
    (thu,) = [w for w in F.windows((date(2015, 9, 17),)) if w["kind"] == "event"]
    assert thu["entry_day"] == date(2015, 9, 16)
    (mon,) = [w for w in F.windows((date(2015, 9, 14),)) if w["kind"] == "event"]
    assert mon["entry_day"] == date(2015, 9, 11)  # over a weekend: three nights of financing


def quotes_for(ws, move, price=2000.0, half=0.25):
    """Entry and exit quotes for each window: the mid moves by move(window) between them, half-spread `half`."""
    q = {}
    for w in ws:
        out = price * (1 + move(w))
        q[(w["entry_day"], "14:00")] = (price - half, price + half)
        q[(w["exit_day"], "13:55")] = (out - half, out + half)
    return q


def test_the_spread_the_slippage_and_each_nights_financing_are_paid():
    (ev, _, _) = F.windows((date(2015, 1, 28),))
    q = quotes_for([ev], lambda w: 0.004)
    r = F.window_net(q, ev, lambda d: 0.25)
    spread = 0.5 / 2000 + 0.5 / 2008
    cost = spread / 2 + F.SLIP_SPREAD * spread + 1 * (0.25 + F.MARKUP_PA) / 100 / 360
    assert r["gross"] == pytest.approx(0.004) and r["cost"] == pytest.approx(cost)
    assert r["net"] == pytest.approx(0.004 - cost)
    assert F.window_net(q, ev, lambda d: 0.25, cost_x=2.0)["net"] == pytest.approx(0.004 - 2 * cost)
    assert F.window_net(q, ev, lambda d: float("nan")) is None  # financing unknown: no trade, never assumed
    gone = {k: v for k, v in q.items() if k != (ev["exit_day"], "13:55")}
    assert F.window_net(gone, ev, lambda d: 0.25) is None  # no quote: no trade, never filled


def judged_windows():
    return [w for w in F.windows() if F.JUDGE[0] <= w["event"] < F.JUDGE[1]]


def wiggle(w, size):
    """A known, fixed pattern of noise around zero, by the window's day."""
    return size * (1 if w["exit_day"].toordinal() % 2 else -1)


def test_a_drift_only_the_events_have_passes_every_gate():
    move = lambda w: (0.005 if w["kind"] == "event" else 0.0004) + wiggle(w, 0.002)  # noqa: E731
    res = F.gates(quotes_for(judged_windows(), move), lambda d: 0.25, thr=3.24)
    assert res["passed"], res["failed_gates"]
    assert res["net_per_event"]["n"] == res["events_listed"] == 71 and res["timing"]["controls"] > 100


def test_a_drift_the_ordinary_weeks_share_fails_the_timing_gate():
    move = lambda w: 0.003 + wiggle(w, 0.002)  # noqa: E731 - the market rises every week alike
    res = F.gates(quotes_for(judged_windows(), move), lambda d: 0.25, thr=3.24)
    assert res["net_per_event"]["t"] >= 3.24 and not res["passed"] and res["failed_gates"] == ["timing"]


def test_the_calendar_is_checked_at_its_source():
    assert F.verify_page("Federal Reserve issues FOMC statement ... For release at 2:00 p.m. EDT") is None
    assert F.verify_page("Minutes of the Federal Open Market Committee ... For release at 2:00 p.m.") == \
        "not the FOMC statement"
    assert F.verify_page("Federal Reserve issues FOMC statement ... For release at 2:15 p.m. EDT") == \
        "not released at 2:00 p.m."
    assert len(F.EVENTS) == len(set(F.EVENTS)) and all(d.weekday() in (2, 3) for d in F.EVENTS)
    per_year = {y: sum(1 for d in F.EVENTS if d.year == y) for y in range(2013, 2027)}
    assert per_year == {**{y: 8 for y in range(2013, 2026)}, 2020: 7, 2026: 6}


def test_the_judge_never_reads_the_holdout_and_refuses_a_quote_it_cannot_trust(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "DATA", tmp_path)

    def write(body):
        (tmp_path / "quotes.csv").write_text(body)
        (tmp_path / "manifest.json").write_text(json.dumps({"file": "quotes.csv",
                                                            "sha256": hashlib.sha256(body.encode()).hexdigest()}))
    write("date,time_ny,bid,ask\n2021-12-14,14:00,4600.0,4600.5\n2022-01-25,14:00,4300.0,4300.5\n")
    assert list(F.load(F.JUDGE[1])) == [(date(2021, 12, 14), "14:00")]  # cut at the holdout
    (tmp_path / "quotes.csv").write_text("date,time_ny,bid,ask\n2021-12-14,14:00,9.0,9.5\n")
    with pytest.raises(SystemExit, match="does not match its manifest"):
        F.load(F.JUDGE[1])
    write("date,time_ny,bid,ask\n2021-12-14,14:00,4601.0,4600.5\n")  # crossed
    with pytest.raises(SystemExit, match="refused, never repaired"):
        F.load(F.JUDGE[1])


def test_the_threshold_counts_every_earlier_test_on_the_index_cfds():
    class Reg:
        def tests_on(self, u, a, b):
            return {"index-cfd-intraday": 40}.get(u, 0)
    assert F.threshold(Reg()) == pytest.approx(max(3.0, F.bonferroni_t(40 + F.TESTS)))
