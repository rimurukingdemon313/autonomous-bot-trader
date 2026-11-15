"""RADX-1's single look (scripts/radx1.py): the judge reads the pinned ledger once, with the registered code, and the
committed record of that look is consistent with its registration."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.radx1 as X
from aitrader.research.registry import Registry, Trial, Use
from tests.unit.test_perf_radx import build

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 11, 14, 19, 30, tzinfo=timezone.utc)


def sha(ledger) -> str:
    return hashlib.sha256(json.dumps(ledger, sort_keys=True).encode()).hexdigest()


def registered(tmp_path, ledger, code=None):
    reg = Registry(tmp_path / "registry.jsonl")
    reg.register(Trial(id=X.PID, registered=NOW - timedelta(hours=1), title="t", hypothesis="h",
                       uses=(Use(X.UNIVERSE, date(2026, 10, 30), date(2026, 11, 15), "judge"),), tests=2, configurations=2,
                       preregistration=X.DOC, design={"code_sha256": code or X.code_hash(), "ledger_sha256": sha(ledger)}))
    return reg


def test_the_judge_records_the_verdict_with_both_parts_and_every_position(tmp_path):
    led = build()
    reg = registered(tmp_path, led)
    body = X.judge(led, NOW, reg, tmp_path / "RADX-1.json")
    assert body["verdict"] == "PASSED" and reg.status_of(X.PID) == "PASSED"
    saved = json.loads((tmp_path / "RADX-1.json").read_text())
    assert saved["gates"] == {"P1_thin_entries": True, "P2_churn_after_decay": True}
    assert saved["code_sha256"] == X.code_hash() and saved["ledger"]["sha256"] == sha(led)
    assert len(saved["positions"]) == len(led["closed"]) and "validates no change" in saved["meaning"]
    v = reg.verdict_of(X.PID)
    assert v.result["gates"] == saved["gates"] and v.result["later"]["positions"] == saved["later"]["positions"]


def test_a_second_look_is_refused(tmp_path):
    led = build()
    reg = registered(tmp_path, led)
    X.judge(led, NOW, reg, tmp_path / "RADX-1.json")
    first = (tmp_path / "RADX-1.json").read_text()
    with pytest.raises(SystemExit, match="looked at once"):
        X.judge(led, NOW + timedelta(days=1), reg, tmp_path / "RADX-1.json")
    assert (tmp_path / "RADX-1.json").read_text() == first


def test_any_other_ledger_is_refused_and_nothing_is_recorded(tmp_path):
    led = build()
    reg = registered(tmp_path, led)
    later = build(later_thin=+12.0)  # a ledger that would give another answer
    with pytest.raises(SystemExit, match="not the ledger snapshot"):
        X.judge(later, NOW, reg, tmp_path / "RADX-1.json")
    assert reg.status_of(X.PID) == "PENDING" and not (tmp_path / "RADX-1.json").exists()


def test_a_changed_code_is_refused(tmp_path):
    led = build()
    reg = registered(tmp_path, led, code="0" * 64)
    with pytest.raises(SystemExit, match="code changed since registration"):
        X.judge(led, NOW, reg, tmp_path / "RADX-1.json")
    assert reg.status_of(X.PID) == "PENDING"


def test_the_committed_record_of_the_look_matches_its_registration():
    reg = X.registry()
    trial, verdict = reg.get(X.PID), reg.verdict_of(X.PID)
    doc = (ROOT / X.DOC).read_text()
    saved = json.loads(X.OUT.read_text())
    assert trial.design["code_sha256"] in doc and trial.design["ledger_sha256"] in doc
    assert saved["code_sha256"] == trial.design["code_sha256"] and saved["ledger"]["sha256"] == trial.design["ledger_sha256"] == X.SNAPSHOT_SHA256
    assert verdict is not None and verdict.status == saved["verdict"] and verdict.result["gates"] == saved["gates"]
    assert verdict.recorded > trial.registered and trial.tests == X.TESTS == 2
    # what the look found, as recorded: the thin entries held, the churn after a decayed spread did not
    assert saved["verdict"] == "FAILED" and saved["gates"] == {"P1_thin_entries": True, "P2_churn_after_decay": False}
    assert saved["later"]["P1_thin_entries"]["positions"] == 41 and saved["later"]["P2_churn_after_decay"]["positions"] == 15
    assert saved["cut"] == 1793358000 and saved["design"]["positions"] == 122 and saved["later"]["positions"] == 88
