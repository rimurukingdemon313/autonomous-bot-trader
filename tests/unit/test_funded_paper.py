"""FUNDED-P on markets built so the answer is known: its monthly decision is TRND-1's own; a held index earns its
fixed notional's move and each switch pays its cost; a day losing $10,000 or equity at $180,000 fails the track; +10%
then +5% pass the two phases no earlier than their 4th day, each new phase on a fresh $200,000; a close after a day
changes nothing before it; a close that is not yet final is not used; an unknown decision is flat."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.funded_paper as P
import scripts.trnd1 as T


def monthly(start: tuple[int, int], end: tuple[int, int], ret) -> dict[date, float]:
    (y, m), out, p, k = start, {}, 100.0, 0
    while (y, m) <= end:
        out[date(y, m, 28)] = p
        p *= 1 + ret(k)
        k += 1
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def test_its_monthly_decision_is_trnd1s_own():
    closes = monthly((1990, 1), (1999, 12), lambda k: 0.04 if k % 7 < 4 else -0.05)
    rows = T.held_months(closes)
    dec = P.decisions(closes)
    assert len(rows) > 100 and all(dec[(r["month"].year, r["month"].month)] == r["held"] for r in rows)
    gap = {d: c for d, c in closes.items() if (d.year, d.month) != (1995, 6)}
    after = P.decisions(gap)  # June 1995 has no close: no month whose ten month-ends include it is decided
    assert after.get((1995, 7)) is None and after[(1995, 8)] is None and after[(1996, 4)] is None
    assert after[(1996, 5)] is not None  # July 1995 to April 1996: ten again


def flat_history(first: date, days: int, level: float = 100.0) -> dict[date, float]:
    return {first + timedelta(days=i): level for i in range(days)}


def one_index(prices: list[float], first: date = date(2026, 11, 9)) -> dict[str, dict[date, float]]:
    """A year of rising month-ends (so the rule holds), then the given daily closes from `first` on."""
    hist = {date(2025, m, 28): 50.0 + m for m in range(1, 13)} | {date(2026, m, 28): 70.0 + m for m in range(1, 11)}
    return {"^GSPC": hist | {first + timedelta(days=i): p for i, p in enumerate(prices)}}


def test_a_held_index_earns_its_notional_and_each_day_pays_the_four_day_trade():
    r = P.run(one_index([100.0, 101.0, 101.0, 101.0, 101.0, 102.01]), expo=0.5)
    n = 0.5 * P.BALANCE  # one index carries the whole exposure
    pl = [h["pl"] for h in r["history"]]
    assert r["held"] == {"^GSPC": True} and r["notional_each"] == n
    assert pl[0] == pytest.approx(-n * T.COST_SIDE - P.COMPLIANCE_COST)  # opened at the first close
    assert pl[1] == pytest.approx(n * 0.01 - P.COMPLIANCE_COST)
    assert pl[4] == pytest.approx(0.0) and pl[5] == pytest.approx(n * 0.01)  # the four-day trades are over


def test_a_day_losing_10000_or_equity_at_180000_fails_the_track():
    day = P.run(one_index([100.0, 100.0, 100.0, 100.0, 95.9]), expo=1.0)  # -4.1% on $200,000 is -$8,200: survives
    assert day["status"] == "PHASE 1"
    crash = P.run(one_index([100.0, 100.0, 100.0, 100.0, 94.9]), expo=1.0)  # -5.1%: -$10,200 in a day
    assert crash["status"] == "FAILED" and "a day lost" in crash["events"][-1]["event"]
    assert crash["last_date"] == str(date(2026, 11, 13))  # the record stops at the failure
    slide = P.run(one_index([100.0] + [100.0 * 0.98 ** k for k in range(1, 8)]), expo=1.0)  # 2% a day, six days
    assert slide["status"] == "FAILED" and "maximum loss" in slide["events"][-1]["event"]
    assert slide["equity"] <= P.BALANCE - P.MAX_LOSS


def test_the_targets_pass_the_phases_no_earlier_than_their_fourth_day():
    fast = P.run(one_index([100.0, 112.0, 112.0, 112.0, 112.0]), expo=1.0)  # +12% on day 2
    assert [e["event"].split(" at ")[0] for e in fast["events"]] == ["PHASE 1 PASSED"]
    assert fast["events"][0]["date"] == str(date(2026, 11, 9) + timedelta(days=3))  # the 4th day, not the 2nd
    assert fast["status"] == "PHASE 2" and fast["base"] == P.BALANCE  # a fresh $200,000, the position reopened
    two = P.run(one_index([100.0, 112.0, 112.0, 112.0, 118.0, 118.0, 118.0, 118.0]), expo=1.0)
    assert two["status"] == "FUNDED" and two["target"] is None
    assert [e["event"].split(" at ")[0] for e in two["events"]] == ["PHASE 1 PASSED", "PHASE 2 PASSED"]


def test_a_later_close_changes_nothing_before_it_and_a_close_counts_once_final():
    base = one_index([100.0, 101.0, 99.0, 100.5, 102.0, 103.0])
    later = {"^GSPC": base["^GSPC"] | {date(2026, 11, 15): 140.0}}
    a, b = P.run(base, expo=0.5), P.run(later, expo=0.5)
    assert b["history"][:len(a["history"])] == a["history"]
    nov9 = {date(2026, 11, 9): 100.0}
    before = datetime(2026, 11, 9, 21, 29, tzinfo=timezone.utc)  # 16:29 in New York: 29 minutes after the close
    after = datetime(2026, 11, 9, 21, 30, tzinfo=timezone.utc)
    assert P.final_only("^GSPC", nov9, before) == {} and P.final_only("^GSPC", nov9, after) == nov9
    assert P.final_only("^GDAXI", nov9, datetime(2026, 11, 9, 16, 59, tzinfo=timezone.utc)) == {}  # 17:59 in Berlin


def test_an_unknown_decision_is_flat_and_said_so():
    r = P.run({"^GSPC": flat_history(date(2026, 11, 9), 6)}, expo=1.0)  # no month-ends before November
    assert r["held"] == {"^GSPC": False} and r["unknown_decisions"] == ["^GSPC 2026-11"]
    assert all(h["pl"] == pytest.approx(-P.COMPLIANCE_COST if i < 4 else 0.0) for i, h in enumerate(r["history"]))


def test_the_tracks_are_half_with_its_stop_and_full_without():
    assert P.TRACKS == {"HALF": {"expo": 0.5, "stop": 0.06}, "FULL": {"expo": 1.0, "stop": None}}
    four = {s: one_index([100.0, 100.0])["^GSPC"] for s in T.HOLDOUT_INDICES}
    assert P.run(four, expo=0.5)["notional_each"] == 25_000.0 and P.run(four, expo=1.0)["notional_each"] == 50_000.0


def test_the_one_day_stop_caps_a_crash_day_and_waits_for_the_next_decision():
    days = [100.0, 100.0, 100.0, 100.0, 80.0, 82.0, 84.0]  # a 20% crash on the fifth day (no four-day trades left)
    with_stop = P.run(one_index(days), expo=0.5, stop=0.06)
    n = 0.5 * P.BALANCE
    crash = with_stop["history"][4]["pl"]
    assert crash == pytest.approx(-n * (0.06 + P.STOP_SLIPPAGE) - n * T.COST_SIDE)  # -8%: $8,000 and the exit
    assert with_stop["status"] == "PHASE 1" and with_stop["stops"] == 1 and with_stop["held"] == {"^GSPC": False}
    assert [h["pl"] for h in with_stop["history"][5:]] == [0.0, 0.0]  # flat for the rest of the month
    without = P.run(one_index(days), expo=0.5)
    assert without["status"] == "FAILED" and "a day lost $20,000" in without["events"][-1]["event"]
    small = P.run(one_index([100.0, 100.0, 100.0, 100.0, 94.1]), expo=0.5, stop=0.06)  # -5.9%: not a stop
    assert small["stops"] == 0 and small["history"][4]["pl"] == pytest.approx(n * -0.059)


def test_after_a_stop_the_next_months_decision_reenters():
    hist = {date(2025, m, 28): 50.0 + m for m in range(1, 13)} | {date(2026, m, 28): 70.0 + m for m in range(1, 11)}
    nov = {date(2026, 11, 9) + timedelta(days=i): p for i, p in enumerate([100.0, 100.0, 100.0, 100.0, 90.0])}
    dec = {date(2026, 11, 30): 95.0, date(2026, 12, 1): 96.0}  # November's close 95 is above its ten-month mean
    r = P.run({"^GSPC": hist | nov | dec}, expo=0.5, stop=0.06)
    assert r["stops"] == 1 and r["held"] == {"^GSPC": True}
    n = 0.5 * P.BALANCE
    assert r["history"][-1]["pl"] == pytest.approx(n * (96.0 / 95.0 - 1) - n * T.COST_SIDE, abs=0.01)  # back in at 95
