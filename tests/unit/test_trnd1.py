"""TRND-1 on markets built so the answer is known: each month's last close is its month-end; the rule holds a month
only when the previous month-end close was above the mean of the ten month-ends before it, and pays each switch; a
decision reads no later close; a month without a close is never bridged; a market that falls slowly enough for the
filter to step aside passes, and choppy, falling or suddenly crashing ones fail; the judge never reads the holdout,
nor the holdout the judged years; the holdout needs every month of every index; the threshold counts every earlier
test on stock-index data."""

from __future__ import annotations

import hashlib
import json
from datetime import date

import pytest

import scripts.trnd1 as T


def series(start: tuple[int, int], end: tuple[int, int], ret) -> dict[date, float]:
    """One close a month, on the 28th, from `start` to `end` inclusive; month k's close is month k-1's times
    1 + ret(k-1)."""
    (y, m), out, p, k = start, {}, 100.0, 0
    while (y, m) <= end:
        out[date(y, m, 28)] = p
        p *= 1 + ret(k)
        k += 1
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def slow_crashes(k: int) -> float:
    """Forty-eight months up 1.5% a month with a 1% wiggle, then twelve months down 4% a month, over and over."""
    return (0.015 + (0.01 if k % 2 else -0.01)) if k % 60 < 48 else -0.04


def choppy(k: int) -> float:
    return 0.03 if k % 4 < 2 else -0.03


def sudden_crashes(k: int) -> float:
    """Up 1% a month, and once every ten years a 40% fall in a single month: no warning for a monthly filter."""
    return -0.40 if k % 120 == 119 else 0.01


def judged(ret) -> dict:
    return {T.JUDGED_INDEX: series((1927, 12), (1989, 12), ret)}


def test_month_ends_take_each_months_last_close():
    closes = {date(2000, 1, 3): 1.0, date(2000, 1, 31): 2.0, date(2000, 2, 1): 3.0, date(2000, 2, 29): 4.0,
              date(2000, 3, 15): 5.0}
    assert T.month_ends(closes) == [(date(2000, 1, 31), 2.0), (date(2000, 2, 29), 4.0), (date(2000, 3, 15), 5.0)]


def test_the_rule_holds_only_above_its_ten_month_mean_and_pays_each_switch():
    closes = {date(2000, m, 28): 100.0 for m in range(1, 11)}  # January..October 2000 at 100
    closes |= {date(2000, 11, 28): 110.0, date(2000, 12, 28): 99.0, date(2001, 1, 28): 120.0, date(2001, 2, 28): 126.0}
    rows = T.held_months(closes)
    # October's close equals its mean: not above, so November is flat. November's 110 is above its mean of 101, so
    # December is held (-10%, plus the entry). December's 99 is below 100.9: January is flat (the exit). January's 120
    # is above 102.9: February is held (+5%, plus the entry).
    assert [(r["month"], r["held"], r["switch"]) for r in rows] == [
        (date(2000, 11, 1), False, False), (date(2000, 12, 1), True, True), (date(2001, 1, 1), False, True),
        (date(2001, 2, 1), True, True)]
    assert [r["net"] for r in rows] == pytest.approx([0.0, -0.1 - T.COST_SIDE, -T.COST_SIDE, 0.05 - T.COST_SIDE])
    assert [r["net"] for r in T.held_months(closes, cost_x=2.0)] == pytest.approx(
        [0.0, -0.1 - 2 * T.COST_SIDE, -2 * T.COST_SIDE, 0.05 - 2 * T.COST_SIDE])
    assert [r["index"] for r in rows] == pytest.approx([0.1, -0.1, 120 / 99 - 1, 0.05])


def test_a_decision_reads_no_close_after_its_month_end():
    closes = judged(slow_crashes)[T.JUDGED_INDEX]
    before = T.held_months(closes)
    cut = date(1950, 6, 28)
    changed = {d: p * (7.0 if d > cut else 1.0) * (0.5 if d > date(1951, 3, 1) else 1.0) for d, p in closes.items()}
    after = T.held_months(changed)
    # every decision up to and including the one taken at June 1950's close (for July) is the same
    keep = [r["held"] for r in before if r["month"] <= date(1950, 7, 1)]
    assert keep == [r["held"] for r in after if r["month"] <= date(1950, 7, 1)] and len(keep) > 250
    assert [r["net"] for r in before if r["month"] <= date(1950, 6, 1)] == \
        [r["net"] for r in after if r["month"] <= date(1950, 6, 1)]


def test_a_month_without_a_close_is_never_bridged():
    data = judged(slow_crashes)
    data[T.JUDGED_INDEX] = {d: p for d, p in data[T.JUDGED_INDEX].items() if (d.year, d.month) != (1960, 3)}
    rows = T.held_months(data[T.JUDGED_INDEX])
    months = {r["month"] for r in rows}
    # March 1960 has no close, so no return spans it, and no decision's ten months include it: March..January 1961
    assert not any(date(1960, 3, 1) <= m <= date(1961, 1, 1) for m in months)
    assert date(1960, 2, 1) in months and date(1961, 2, 1) in months
    res = T.gates(data, thr=3.3761)
    assert res["months"]["n"] == 732 - 11 and not res["passed"] and res["failed_gates"] == ["complete"]


def test_a_market_that_falls_slowly_passes_and_choppy_falling_or_sudden_ones_fail():
    res = T.gates(judged(slow_crashes), thr=3.3761)
    assert res["passed"], res["failed_gates"]
    assert res["months"]["n"] == 732 and res["worst_fall"] < res["worst_fall_holding_all_the_time"]
    assert res["development"]["n"] == 360 and res["validation"]["n"] == 372
    t = res["months"]["t"]  # the bar is applied exactly
    assert T.gates(judged(slow_crashes), thr=t - 1e-9)["passed"]
    assert T.gates(judged(slow_crashes), thr=t + 1e-9)["failed_gates"] == ["t"]

    chop = T.gates(judged(choppy), thr=3.3761)  # the filter buys after rises and sells after falls
    assert not chop["passed"] and chop["months"]["mean"] < 0 and "t" in chop["failed_gates"]
    falling = T.gates(judged(lambda k: -0.01), thr=3.3761)  # never held: no return at all, and no t
    assert not falling["passed"] and falling["time_in_market"] == 0 and falling["months"]["t"] is None
    sudden = T.gates(judged(sudden_crashes), thr=3.3761)  # held through every one-month crash
    assert not sudden["passed"] and "smaller_crash" in sudden["failed_gates"]
    assert sudden["worst_fall"] >= sudden["worst_fall_holding_all_the_time"]  # the crash, then the exit's cost


def test_worst_fall_compounds_from_the_highest_point():
    assert T.worst_fall([0.1, -0.5, 0.2, -0.5]) == pytest.approx(1 - 1.1 * 0.5 * 1.2 * 0.5 / 1.1)  # from 1.1 to 0.33
    assert T.worst_fall([0.01, 0.02]) == 0.0


def _manifest(tmp_path, bodies: dict[str, str]) -> None:
    man = {"series": {}}
    for sym, body in bodies.items():
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))


def test_the_judge_never_reads_the_holdout_nor_the_holdout_the_judged_years(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "DATA", tmp_path)
    body = "date,close\n1926-12-31,1.0\n1927-12-30,1.0\n1989-12-29,2.0\n1990-01-02,3.0\n2019-12-31,4.0\n" \
           "2020-01-02,5.0\n2026-09-30,6.0\n2026-10-01,7.0\n"
    _manifest(tmp_path, {s: body for s in T.HOLDOUT_INDICES})
    judge = T.load((T.JUDGED_INDEX,), T.FIRST, T.JUDGE[1])[T.JUDGED_INDEX]
    assert sorted(judge) == [date(1927, 12, 30), date(1989, 12, 29)]
    hold = T.load(T.HOLDOUT_INDICES, T.WARMUP_FROM, T.HOLD[1])
    assert all(sorted(v) == [date(2020, 1, 2), date(2026, 9, 30)] for v in hold.values())
    (tmp_path / "GSPC.csv").write_text(body.replace("2.0", "9.0"))
    with pytest.raises(SystemExit, match="does not match its manifest"):
        T.load((T.JUDGED_INDEX,), T.FIRST, T.JUDGE[1])


def test_the_holdout_needs_every_month_of_every_index():
    def index(shift: int) -> dict[date, float]:
        return series((2020, 1), (2026, 9), lambda k: slow_crashes(k + shift))
    data = {sym: index(7 * i) for i, sym in enumerate(T.HOLDOUT_INDICES)}
    res = T.holdout_result(data)
    assert res["months"]["n"] == 69 and res["verdict"] == "PASSED" and res["classification"] == "VALIDATED"
    data[T.HOLDOUT_INDICES[2]] = {d: p for d, p in data[T.HOLDOUT_INDICES[2]].items() if (d.year, d.month) != (2026, 9)}
    short = T.holdout_result(data)
    assert short["months"]["n"] == 68 and short["verdict"] == "FAILED" and short["failed_gates"] == ["complete"]
    flat = {sym: series((2020, 1), (2026, 9), choppy) for sym in T.HOLDOUT_INDICES}
    assert T.holdout_result(flat)["verdict"] == "FAILED"


def test_the_threshold_counts_every_earlier_test_on_stock_index_data():
    counts = {"multi-asset-etf": 12, "multi-asset-long": 10, "equity-index-b": 2, "equity-index-forward": 3,
              "index-cfd-intraday": 32, "us-equity-etf": 6, "us-vol-etp": 2, "us-treasury-daily": 2, "fx-majors": 174}

    class Reg:
        def tests_on(self, u, a, b):
            return counts.get(u, 0)
    assert T.threshold(Reg()) == pytest.approx(T.bonferroni_t(67 + T.TESTS))  # neither Treasuries nor FX count
    assert round(T.threshold(Reg()), 4) == 3.3761
