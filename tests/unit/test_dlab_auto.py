"""The lab's two registered steps run end to end in a scratch repository: a scan is registered before it runs, runs
once, and resumes after a crash; a batch is frozen before a validation row is loaded and judged once; a change of code
between registration and run is refused. Built markets only."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.dlab as L
from aitrader.research.dlab import datasets as D
from aitrader.research.registry import Holdout, Registry

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
W = {"fit": (date(2000, 1, 3), date(2009, 8, 1)), "check": (date(2009, 8, 1), date(2017, 4, 1)),
     "validation": (date(2017, 4, 1), date(2028, 10, 1))}


@pytest.fixture
def lab(tmp_path, monkeypatch):
    """A scratch repository with an empty registry, and a built daily market with a planted lead-lag."""
    r = tmp_path / "research"
    (r / "specs").mkdir(parents=True)
    (r / "preregistrations").mkdir()
    (r / "holdout.json").write_text(json.dumps({"universe": "fx-majors", "start": "2017-01-01", "rationale": "test",
                                                "sealed_at": "2026-09-26T20:28:47+00:00"}))
    for name, val in (("ROOT", tmp_path), ("R", r), ("OUT", r / "knowledge"), ("LEDGER", r / "dlab" / "candidates.jsonl")):
        monkeypatch.setattr(L, name, val)
    monkeypatch.setattr(L, "code_hash", lambda: "c" * 64)
    full = D.synthetic(rows=7500, seed=100, plant={"leadlag": 0.12})
    loads = []

    def loader(last):
        loads.append(last)
        return full.head(sum(t < last for t in full.times))
    monkeypatch.setitem(D.WINDOWS, "synthetic", W)
    monkeypatch.setitem(L.DATASETS, "syn", ("synthetic", loader, 5))
    return tmp_path, loads


def registry(root):
    return Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))


def test_a_scan_is_registered_before_it_runs_runs_once_and_keeps_every_rule(lab):
    root, loads = lab
    body = L.auto_scan("syn", "DLAB-SYN-1", 7, NOW)
    reg = registry(root)
    t = reg.get("DLAB-SYN-1")
    assert t.uses[0].role == "select" and (t.uses[0].start, t.uses[0].end) == (W["fit"][0], W["check"][1])
    assert t.tests == L.MAX_RULES and reg.verdict_of("DLAB-SYN-1").status == "PASSED" and body["batch"]
    doc = (root / "research" / "preregistrations" / "DLAB-SYN-1.md").read_text()
    frozen = json.loads((root / "research" / "specs" / "DLAB-SYN-1.json").read_text())
    assert frozen["sha256"] in doc and frozen["code_sha256"] in doc and "not loaded" in doc
    assert loads == [W["check"][1]]  # the one load of the scan stopped at the check rows' end
    assert reg.verdict_of("DLAB-SYN-1").result["artifact_sha256"] == body["sha256"]
    rows = [json.loads(x) for x in (root / "research" / "dlab" / "candidates.jsonl").read_text().splitlines()]
    assert len(rows) == len(body["records"]) > 80 and all(r["class"] and r["reason"] for r in rows)
    assert L.auto_scan("syn", "DLAB-SYN-1", 7, NOW + timedelta(hours=1))["sha256"] == body["sha256"]  # a rerun: the same
    assert len(registry(root).trials) == 1 and loads == [W["check"][1]]  # nothing registered or loaded again
    assert len((root / "research" / "dlab" / "candidates.jsonl").read_text().splitlines()) == len(rows)
    assert reg.tests_on("synthetic", *map(lambda d: d, W["validation"])) == 0  # the scan charged its own rows only


def test_a_scan_that_crashed_after_registering_is_run_not_registered_again(lab, monkeypatch):
    root, _ = lab
    boom = {"on": True}
    real = L.scan

    def crashing(*a, **k):
        if boom["on"]:
            raise RuntimeError("the runner died")
        return real(*a, **k)
    monkeypatch.setattr(L, "scan", crashing)
    with pytest.raises(RuntimeError):
        L.auto_scan("syn", "DLAB-SYN-2", 7, NOW)
    reg = registry(root)
    assert reg.get("DLAB-SYN-2") and reg.verdict_of("DLAB-SYN-2") is None  # registered, no verdict: nothing was read
    boom["on"] = False
    body = L.auto_scan("syn", "DLAB-SYN-2", 7, NOW + timedelta(hours=8))
    assert registry(root).verdict_of("DLAB-SYN-2").status in ("PASSED", "FAILED") and len(registry(root).trials) == 1
    assert body["summary"]["rules"] == len(body["records"])


def test_the_batch_is_frozen_before_a_validation_row_is_loaded_and_judged_once(lab):
    root, loads = lab
    scan = L.auto_scan("syn", "DLAB-SYN-1", 7, NOW)
    out = L.auto_validate("DLAB-SYN-1", NOW + timedelta(minutes=5))
    reg = registry(root)
    v = reg.get("DLAB-SYN-1-V")
    assert v.uses[0].role == "judge" and (v.uses[0].start, v.uses[0].end) == W["validation"] and v.tests == len(scan["batch"])
    # the discovery rows again (are the rules still the rules?), then the validation rows once, after the registration
    assert loads == [W["check"][1], W["check"][1], W["validation"][1]]
    doc = (root / "research" / "preregistrations" / "DLAB-SYN-1-V.md").read_text()
    frozen = json.loads((root / "research" / "specs" / "DLAB-SYN-1-V.json").read_text())
    assert frozen["sha256"] in doc and all(r["id"] in doc for r in frozen["spec"]["rules"]) and "Threshold: t >= 3.0" in doc
    assert [r["id"] for r in out["results"]] == scan["batch"] and out["verdict"] == "PASSED" and out["passed_rules"]
    assert all(set(r["gates"]) >= {"t", "costs_x2", "halves", "beats_random", "top_year"} for r in out["results"])
    events = [json.loads(x) for x in (root / "research" / "dlab" / "candidates.jsonl").read_text().splitlines() if '"VALIDATION"' in x]
    assert {e["id"] for e in events} == set(scan["batch"]) and {e["class"] for e in events} <= {"VALIDATED_ON_UNREAD_ROWS", "REJECTED_BY_VALIDATION"}
    again = L.auto_validate("DLAB-SYN-1", NOW + timedelta(days=1))
    assert again["sha256"] == out["sha256"] and len(loads) == 3  # judged once: nothing loaded again
    assert reg.tests_on("synthetic", *W["validation"]) == len(scan["batch"])  # only the judged rules are charged there


def test_code_that_changed_a_rule_or_changed_after_registration_is_refused_and_no_batch_validates_nothing(lab, monkeypatch):
    import numpy as np
    from aitrader.research.dlab import signals as S
    root, loads = lab
    scan = L.auto_scan("syn", "DLAB-SYN-1", 7, NOW)
    kinds = {r["spec"]["kind"] for r in scan["records"] if r["id"] in scan["batch"]}
    real = {k: S.KINDS[k] for k in kinds}
    for k in kinds:  # today's code computes the batch's rules differently from the scan's
        monkeypatch.setitem(S.KINDS, k, lambda p, s, f=real[k]: -f(p, s))
    with pytest.raises(SystemExit, match="no longer computes"):
        L.auto_validate("DLAB-SYN-1", NOW + timedelta(minutes=5))
    assert len(registry(root).trials) == 1 and W["validation"][1] not in loads  # nothing registered, nothing loaded
    for k in kinds:
        monkeypatch.setitem(S.KINDS, k, real[k])
    L.cmd_spec(type("A", (), {"run": "DLAB-SYN-1"})())
    f = json.loads((root / "research" / "specs" / "DLAB-SYN-1-V.json").read_text())
    (root / "research" / "preregistrations" / "DLAB-SYN-1-V.md").write_text(f["sha256"] + " " + f["code_sha256"])
    L.cmd_preregister(type("A", (), {"run": "DLAB-SYN-1"})(), NOW + timedelta(minutes=6))
    monkeypatch.setattr(L, "code_hash", lambda: "d" * 64)  # the code changes after the batch was registered
    with pytest.raises(SystemExit, match="differs"):
        L.auto_validate("DLAB-SYN-1", NOW + timedelta(minutes=7))
    assert registry(root).verdict_of("DLAB-SYN-1-V") is None and W["validation"][1] not in loads
    assert np.isfinite(scan["bar_on_validation"])
    art = root / "research" / "knowledge" / "DLAB-SYN-1.json"
    body = json.loads(art.read_text())
    body["batch"] = []
    art.write_text(json.dumps(body))
    assert L.auto_validate("DLAB-SYN-1", NOW + timedelta(minutes=6)) is None
