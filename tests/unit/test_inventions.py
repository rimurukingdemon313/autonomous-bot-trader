"""The invention ledger admits a mechanism only with its whole argument, never lets a failed family back in without
saying what is different, and never rewrites a closed record."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from aitrader.research import inventions as I

ROOT = Path(__file__).resolve().parents[2]


def full(name="X-1", **kw):
    e = {"name": name, "status": "PROPOSED", "at": "2026-11-15T20:00:00+00:00", "families": ["settlement microstructure"],
         "predictions": ["a measurable thing"], "refuted_if": ["it is not there"],
         "closest_known": [{"approach": "a known one", "differs_by": "a stated difference"}]}
    for k in I.ARGUMENT:
        e[k] = f"an argument for {k} long enough to read"
    e.update(kw)
    return e


def test_an_invention_with_its_whole_argument_is_admitted_and_one_without_is_not(tmp_path):
    p = tmp_path / "l.jsonl"
    I.append(p, full())
    assert I.current(I.load(p))["X-1"].status == "PROPOSED"
    for k in ("mechanism", "why_not_competed_away", "return_relation"):
        bad = full(name="Y-" + k)
        bad[k] = ""
        with pytest.raises(I.LedgerError, match=k):
            I.append(p, bad)
    with pytest.raises(I.LedgerError, match="differs from it"):
        I.append(p, full(name="Z", closest_known=[{"approach": "a known one"}]))


def test_a_failed_family_comes_back_only_with_what_is_different(tmp_path):
    p = tmp_path / "l.jsonl"
    with pytest.raises(I.LedgerError, match="funding carry"):
        I.append(p, full(families=["funding carry"]))
    I.append(p, full(families=["funding carry"], vs_failed={"funding carry": "held ten minutes, not days"}))


def test_the_record_is_append_only_and_closed_records_stay_closed(tmp_path):
    p = tmp_path / "l.jsonl"
    with pytest.raises(I.LedgerError, match="must be proposed"):
        I.append(p, {"name": "X-1", "status": "REGISTERED", "at": "t", "trial": "X-1"})
    I.append(p, full())
    with pytest.raises(I.LedgerError, match="new name"):
        I.append(p, full())
    with pytest.raises(I.LedgerError, match="names its registered trial"):
        I.append(p, {"name": "X-1", "status": "REGISTERED", "at": "t"})
    I.append(p, {"name": "X-1", "status": "REGISTERED", "at": "t", "trial": "X-1"})
    I.append(p, {"name": "X-1", "status": "FAILED", "at": "t", "trial": "X-1"})
    with pytest.raises(I.LedgerError, match="closed"):
        I.append(p, {"name": "X-1", "status": "PASSED", "at": "t", "trial": "X-1"})
    with pytest.raises(I.LedgerError, match="reason"):
        I.append(p, {"name": "W", "status": "REJECTED_BEFORE_TEST", "at": "t"})
    I.append(p, {"name": "W", "status": "REJECTED_BEFORE_TEST", "at": "t", "reason": "no data"})
    assert "| W | REJECTED_BEFORE_TEST |" in I.report(I.load(p))


def test_the_committed_ledger_is_valid_line_by_line(tmp_path):
    q = tmp_path / "replay.jsonl"
    for e in I.load(ROOT / "research" / "inventions.jsonl"):
        I.append(q, copy.deepcopy(e.body))  # replaying it through the gate must refuse nothing
    assert I.load(q) and len(I.load(q)) == len(I.load(ROOT / "research" / "inventions.jsonl"))
