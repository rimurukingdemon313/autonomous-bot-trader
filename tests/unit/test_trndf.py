"""TRND-F on markets built so the answer is known: nothing is fetched or judged before the forward months are
complete; the forward window is exactly December 2026 to November 2029, with 2026's earlier closes read only as the
filter's warm-up; a market where the rule still steps aside from slow falls passes, and a choppy one, or one missing a
month, fails; the judge reads nothing outside its window; the rule is TRND-1's own frozen code."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone

import pytest

import scripts.trnd1 as T
import scripts.trndf as F


def series(start: tuple[int, int], end: tuple[int, int], ret) -> dict[date, float]:
    """One close a month, on the 28th; month k's close is month k-1's times 1 + ret(k-1)."""
    (y, m), out, p, k = start, {}, 100.0, 0
    while (y, m) <= end:
        out[date(y, m, 28)] = p
        p *= 1 + ret(k)
        k += 1
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def slow(k: int) -> float:
    """Twenty-four months up 1.5% a month with a 1% wiggle, then eight months down 4% a month, over and over."""
    return (0.015 + (0.01 if k % 2 else -0.01)) if k % 32 < 24 else -0.04


def four(ret, shift: int = 3) -> dict[str, dict[date, float]]:
    return {sym: series((2026, 1), (2029, 11), lambda k, i=i: ret(k + shift * i))
            for i, sym in enumerate(T.HOLDOUT_INDICES)}


def test_nothing_is_fetched_or_judged_before_the_forward_months_are_complete():
    early = datetime(2029, 12, 2, 23, 59, tzinfo=timezone.utc)
    for cmd in (F.cmd_fetch, F.cmd_judge):
        with pytest.raises(SystemExit, match="before 2029-12-03"):
            cmd(early)


def test_the_forward_window_is_december_2026_to_november_2029():
    data = four(slow)
    res = F.result(data)
    assert res["months"]["n"] == 36
    months = [r["month"] for r in T.in_period(T.held_months(data[T.JUDGED_INDEX]), *F.FORWARD)]
    assert months[0] == date(2026, 12, 1) and months[-1] == date(2029, 11, 1)
    later = {s: {**c, date(2029, 12, 28): c[max(c)] * 9.0} for s, c in data.items()}
    assert F.result(later) == res  # a close after November 2029 changes nothing


def test_a_rule_that_still_steps_aside_passes_and_choppy_or_incomplete_ones_fail():
    res = F.result(four(slow))
    assert res["verdict"] == "PASSED" and res["worst_fall"] < res["worst_fall_holding_all_the_time"]
    chop = F.result(four(lambda k: 0.03 if k % 4 < 2 else -0.03, shift=0))
    assert chop["verdict"] == "FAILED" and "mean" in chop["failed_gates"]
    data = four(slow)
    data["^FTSE"] = {d: p for d, p in data["^FTSE"].items() if (d.year, d.month) != (2028, 5)}
    gap = F.result(data)  # May 2028 has no close: eleven months are never bridged
    assert gap["months"]["n"] == 25 and gap["verdict"] == "FAILED" and gap["failed_gates"] == ["complete"]


def test_the_judge_reads_nothing_outside_its_window(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "DATA", tmp_path)
    body = "date,close\n2025-12-31,1.0\n2026-01-02,2.0\n2029-11-30,3.0\n2029-12-03,4.0\n"
    man = {"retrieved": "2029-12-03T22:00:00+00:00", "series": {}}
    for sym in T.HOLDOUT_INDICES:
        name = sym.lstrip("^")
        (tmp_path / f"{name}.csv").write_text(body)
        man["series"][sym] = {"file": f"{name}.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    got = F.load(F.WARMUP_FROM, F.FORWARD[1])
    assert all(sorted(v) == [date(2026, 1, 2), date(2029, 11, 30)] for v in got.values())
    (tmp_path / "NDX.csv").write_text(body.replace("3.0", "5.0"))
    with pytest.raises(SystemExit, match="does not match its manifest"):
        F.load(F.WARMUP_FROM, F.FORWARD[1])


def test_the_rule_is_trnd1s_own_frozen_code():
    assert F.CODE == ("scripts/trndf.py", "scripts/trnd1.py") and F.T is T
    s = F.spec()
    assert s["indices"] == list(T.HOLDOUT_INDICES) and s["months"] == T.MONTHS == 10
    assert s["cost_each_switch_side"] == T.COST_SIDE and s["forward"] == ["2026-12-01", "2029-12-01"]
