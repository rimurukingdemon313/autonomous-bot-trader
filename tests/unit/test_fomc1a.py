"""FOMC-1A on shards built so the answer is known: the shards cover every day a window needs, each exactly once; a day
that fails twice is recorded as failed and never filled; the merge refuses a missing or foreign shard; a window that
touches a failed day is lost, and a period that loses more than one event window in ten is not judged; the rule is
FOMC-1's own code."""

from __future__ import annotations

import json
from datetime import date

import numpy as np
import pytest

import scripts.fomc1 as F
import scripts.fomc1a as A


def test_the_shards_cover_every_day_a_window_needs_each_exactly_once():
    n = 16
    seen = [d for i in range(n) for d in A.shard_days(i, n)]
    assert sorted(seen) == A.all_days() and len(seen) == len(set(seen))
    need = {w[k] for w in F.windows() for k in ("entry_day", "exit_day")}
    assert set(seen) == need and len(need) == 510
    with pytest.raises(SystemExit, match="does not exist"):
        A.shard_days(16, 16)


def minutes_for(d: date, bid: float = 2000000.0, half: float = 250.0) -> np.ndarray:
    """A day's quotes, raw and unscaled, at the two minutes a window reads and one it does not."""
    rows = []
    for hm in (F.ENTRY_NY, F.EXIT_NY, (10, 0)):
        rows.append([F.minute_end(d, hm), bid, bid, bid, bid, bid + 2 * half, bid + 2 * half, bid + 2 * half,
                     bid + 2 * half])
    return np.array(rows, dtype=float)


def test_a_day_that_fails_twice_is_recorded_as_failed_never_filled(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "DATA", tmp_path)
    monkeypatch.setattr(F, "_calendar_ok", lambda: None)
    days = A.shard_days(0, 16)
    bad, flaky, closed = days[0], days[1], days[2]
    calls: dict = {}

    def fake(sym, d, pace):
        calls[d] = calls.get(d, 0) + 1
        if d == bad or (d == flaky and calls[d] == 1):
            return None, "failed"
        if d == closed:
            return np.zeros((0, 9)), "empty"
        return minutes_for(d), "ok"
    part = A.cmd_fetch(0, 16, day_minutes=fake)
    assert part["days"][str(bad)] == "failed" and calls[bad] == 2  # a second, slower pass, then recorded
    assert part["days"][str(flaky)] == "ok" and part["days"][str(closed)] == "empty"
    taken = {(r[0], r[1]) for r in part["rows"]}
    assert (str(flaky), "14:00") in taken and (str(flaky), "13:55") in taken and (str(flaky), "10:00") not in taken
    assert not any(r[0] in (str(bad), str(closed)) for r in part["rows"])  # nothing invented for them
    assert json.loads((tmp_path / "part-0.json").read_text()) == json.loads(json.dumps(part))


def write_parts(tmp_path, n: int, failed=()):
    for i in range(n):
        days = A.shard_days(i, n)
        status = {str(d): ("failed" if d in failed else "ok") for d in days}
        rows = [r for d in days if d not in failed for r in A.take(minutes_for(d), d)]
        (tmp_path / f"part-{i}.json").write_text(json.dumps({"shard": i, "shards": n, "days": status, "rows": rows}))


def test_the_merge_refuses_a_missing_or_foreign_shard_and_scales_what_it_joins(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "DATA", tmp_path)
    write_parts(tmp_path, 4)
    man = A.cmd_merge(4)
    assert man["scale"] == 0.001 and man["days"] == 510 and man["failed_days"] == []
    q = F.load(F.HOLD[1])
    assert q[(A.all_days()[0], "14:00")] == pytest.approx((2000.0, 2000.5))
    (tmp_path / "part-3.json").unlink()
    with pytest.raises(SystemExit, match="shard 3 of 4 is missing"):
        A.cmd_merge(4)
    write_parts(tmp_path, 4)
    part = json.loads((tmp_path / "part-2.json").read_text())
    part["days"].pop(next(iter(part["days"])))
    (tmp_path / "part-2.json").write_text(json.dumps(part))
    with pytest.raises(SystemExit, match="does not cover its own days"):
        A.cmd_merge(4)


def test_a_period_that_loses_more_than_one_event_window_in_ten_is_not_judged(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "DATA", tmp_path)
    judged = [w for w in F.windows() if w["kind"] == "event" and F.JUDGE[0] <= w["event"] < F.JUDGE[1]]
    assert len(judged) == 47
    four = {w["exit_day"] for w in judged[:4]}  # 4 of 47: under one in ten, judged without them
    write_parts(tmp_path, 4, failed=four)
    A.cmd_merge(4)
    assert len(A._complete_enough(*F.JUDGE)["lost"]) == 4
    five = four | {judged[4]["entry_day"]}  # 5 of 47: more than one in ten
    write_parts(tmp_path, 4, failed=five)
    A.cmd_merge(4)
    with pytest.raises(SystemExit, match="too few to judge"):
        A._complete_enough(*F.JUDGE)
    assert A._complete_enough(*F.HOLD)["lost"] == []  # the holdout's own windows are untouched


def test_the_rule_is_fomc_1s_own_code_and_the_threshold_counts_fomc_1():
    assert A.CODE[1:] == F.CODE and "scripts/fomc1.py" in A.CODE
    assert A.F is F and A.R == F.R

    class Reg:
        def tests_on(self, u, a, b):
            return {"index-cfd-intraday": 30}.get(u, 0)
    assert A.threshold(Reg()) == pytest.approx(max(3.0, F.bonferroni_t(30 + F.TESTS)))
