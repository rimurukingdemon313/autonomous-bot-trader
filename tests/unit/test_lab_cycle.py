"""The autonomous lab's cycle, end to end in a scratch repository on a built market: data, then a registered scan,
then the preregistered validation of what it found, then the forward marks of what passed. Each cycle starts from a
copy of the last one's state, as a fresh machine does. Nothing runs twice; a run that dies is taken up again; a
tampered record stops every experiment; a task that keeps failing is reported, not retried for ever."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.dlab as L
import scripts.lab_cycle as C
from aitrader.research.dlab import datasets as D
from aitrader.research.dlab import feeds as F
from aitrader.research.dlab.store import Store, tasks
from aitrader.research.registry import Holdout, Registry

NOW = datetime(2026, 11, 11, 4, 0, tzinfo=timezone.utc)
W = {"fit": (date(2000, 1, 3), date(2009, 8, 1)), "check": (date(2009, 8, 1), date(2017, 4, 1)),
     "validation": (date(2017, 4, 1), date(2026, 1, 1))}
SOURCE = {"id": "arxiv:2611.00001", "origin": "arxiv", "url": "http://arxiv.org/abs/2611.00001v1",
          "title": "A paper about lead-lag", "published": "2026-11-09", "status": "UNREAD", "reproducibility": "not attempted"}


def make_lab(root, mp, feed=None):
    """A scratch repository with an empty registry, a built market with a planted lead-lag, and a feed that touches
    no network. Returns what the feed and the loader were asked."""
    r = root / "research"
    (r / "specs").mkdir(parents=True, exist_ok=True)
    (r / "preregistrations").mkdir(exist_ok=True)
    if not (r / "holdout.json").exists():
        (r / "holdout.json").write_text(json.dumps({"universe": "fx-majors", "start": "2017-01-01", "rationale": "test",
                                                    "sealed_at": "2026-09-26T20:28:47+00:00"}))
    for name, val in (("ROOT", root), ("R", r), ("OUT", r / "knowledge"), ("LEDGER", r / "dlab" / "candidates.jsonl")):
        mp.setattr(L, name, val)
    mp.setattr(L, "code_hash", lambda: "c" * 64)
    mp.setattr(C, "SEAL_SHA256", hashlib.sha256((r / "holdout.json").read_bytes()).hexdigest())
    full = D.synthetic(rows=7500, seed=100, plant={"leadlag": 0.12})
    asked = {"loads": [], "feeds": []}

    def loader(last):
        asked["loads"].append(last)
        return full.head(sum(t < last for t in full.times))

    def fake_feed(data, now):
        asked["feeds"].append(now)
        data.mkdir(parents=True, exist_ok=True)
        (data / "close.json").write_text("{}")
        man = {"retrieved": now.isoformat(), "quality": {a: {"rows": 7500, "first": "2000-01-03", "last": "2028-09-29",
                                                             "missing_days": 0, "moves_beyond_50pct": 0} for a in full.assets}}
        (data / "manifest.json").write_text(json.dumps(man))
        return man
    mp.setitem(D.WINDOWS, "synthetic", W)
    mp.setitem(L.DATASETS, "syn", ("synthetic", loader, 5))
    mp.setattr(C, "CATALOG", {"syn": {"tag": "SYN", "feed": "syn_feed", "instruments": 3}})
    mp.setattr(C, "FEEDS", {"syn_feed": feed or fake_feed})
    mp.setattr(C, "MIN_INSTRUMENTS", {"syn_feed": 3})
    mp.setattr(F, "papers", lambda known, now, week: [] if SOURCE["id"] in known else [dict(SOURCE)])
    return asked


def registry_lines(root) -> int:
    p = root / "research" / "registry.jsonl"
    return len(p.read_text().splitlines()) if p.exists() else 0


def restart(state, tmp, n):
    """A fresh machine: the next cycle sees only a copy of what the last one published."""
    new = tmp / f"state{n}"
    shutil.copytree(state, new)
    return new


@pytest.fixture(scope="module")
def story(tmp_path_factory):
    """Five cycles, one task each at first, each on a fresh copy of the state. What every cycle did is kept."""
    tmp = tmp_path_factory.mktemp("lab")
    root = tmp / "repo"
    root.mkdir()
    mp = pytest.MonkeyPatch()
    asked = make_lab(root, mp)
    posted = []
    s = tmp / "state0"
    snap = {}
    try:
        code = C.cycle(s, NOW, max_tasks=1)
        snap[1] = {"code": code, "tasks": tasks(Store(s)), "registry": registry_lines(root), "loads": list(asked["loads"])}
        s = restart(s, tmp, 1)
        code = C.cycle(s, NOW + timedelta(hours=6), max_tasks=1)
        snap[2] = {"code": code, "tasks": tasks(Store(s)), "registry": registry_lines(root), "loads": list(asked["loads"]),
                   "state": s}
        shutil.copytree(root, tmp / "repo_after_scan")
        s = restart(s, tmp, 2)
        code = C.cycle(s, NOW + timedelta(hours=12), max_tasks=1)
        snap[3] = {"code": code, "tasks": tasks(Store(s)), "registry": registry_lines(root), "loads": list(asked["loads"]),
                   "alerts": Store(s).read("alerts")}
        s = restart(s, tmp, 3)
        code = C.cycle(s, NOW + timedelta(days=1), max_tasks=4, post=lambda a: posted.append(a["id"]) or "https://x/1")
        snap[4] = {"code": code, "tasks": tasks(Store(s)), "registry": registry_lines(root), "loads": list(asked["loads"]),
                   "alerts": Store(s).read("alerts"), "forward": Store(s).read("forward"),
                   "report": (s / "LAB_REPORT.md").read_text(), "feeds": list(asked["feeds"])}
        s = restart(s, tmp, 4)
        code = C.cycle(s, NOW + timedelta(days=1, hours=6), max_tasks=4, post=lambda a: posted.append(a["id"]) or "https://x/2")
        snap[5] = {"code": code, "tasks": tasks(Store(s)), "registry": registry_lines(root), "loads": list(asked["loads"]),
                   "runs": Store(s).read("runs"), "budget": Store(s).read("budget"), "report": (s / "LAB_REPORT.md").read_text(),
                   "forward": Store(s).read("forward")}
        yield {"root": root, "tmp": tmp, "state": s, "snap": snap, "posted": posted, "asked": asked}
    finally:
        mp.undo()


def status(snap, n):
    return {k: v["status"] for k, v in snap[n]["tasks"].items()}


def test_data_first_then_a_registered_scan_then_its_validation_one_task_a_cycle(story):
    sn = story["snap"]
    assert [sn[i]["code"] for i in range(1, 6)] == [0] * 5
    assert status(sn, 1) == {"data:syn_feed:2026-11": "DONE", "scan:syn:" + C.DLAB_VERSION + ":7": "QUEUED",
                             "sources:2026-W46": "QUEUED"}
    assert sn[1]["registry"] == 0 and sn[1]["loads"] == []  # the scan waited for its data: nothing registered or read
    scan = "scan:syn:" + C.DLAB_VERSION + ":7"
    assert status(sn, 2)[scan] == "DONE" and status(sn, 2)["validate:DLAB-SYN-1"] == "QUEUED"
    assert sn[2]["registry"] == 2 and sn[2]["loads"] == [W["check"][1]]  # a trial and its verdict; discovery rows only
    assert sn[2]["tasks"][scan]["result"]["verdict"] == "PASSED" and sn[2]["tasks"][scan]["result"]["batch"] >= 1
    assert status(sn, 3)["validate:DLAB-SYN-1"] == "DONE" and sn[3]["registry"] == 4
    assert sn[3]["loads"] == [W["check"][1], W["check"][1], W["validation"][1]]  # the batch re-checked, then judged once
    v = sn[3]["tasks"]["validate:DLAB-SYN-1"]["result"]
    assert v["verdict"] == "PASSED" and v["passed"] and v["threshold_t"] == 3.0
    reg = Registry.load(story["root"] / "research" / "registry.jsonl", Holdout.load(story["root"] / "research" / "holdout.json"))
    assert [t.id for t in reg.trials] == ["DLAB-SYN-1", "DLAB-SYN-1-V"]
    assert reg.get("DLAB-SYN-1").uses[0].role == "select" and reg.get("DLAB-SYN-1-V").uses[0].role == "judge"


def test_nothing_runs_twice_across_restarts(story):
    sn = story["snap"]
    assert sn[4]["registry"] == sn[5]["registry"] == 4  # two more cycles: no trial, no verdict
    assert all(t["attempts"] == 1 for t in sn[5]["tasks"].values())  # each task started exactly once
    assert set(status(sn, 5).values()) == {"DONE"}
    ran = [r["step"] for r in sn[5]["runs"] if r["step"].startswith("task:")]
    assert len(ran) == len(set(ran)) == 5  # data, scan, validate, forward, sources
    assert len(story["asked"]["feeds"]) == 2  # the month's data once, and once more for the forward marks
    assert "No task ran" in sn[5]["report"] and len(sn[5]["budget"]) == 5
    rows = (story["root"] / "research" / "dlab" / "candidates.jsonl").read_text().splitlines()
    rules = [json.loads(x) for x in rows if '"event"' not in x]
    assert len({(r["run"], r["id"]) for r in rules}) == len(rules) > 80  # every rule kept, once


def test_a_validated_rule_raises_one_alert_and_is_marked_forward_on_rows_after_its_window(story):
    sn = story["snap"]
    raised = [a for a in sn[3]["alerts"] if a["event"] == "RAISED"]
    assert len(raised) >= 1 and all(a["level"] == "DISCOVERY" for a in raised) and "not a trading system" in raised[0]["body"]
    assert sorted(story["posted"]) == sorted(a["id"] for a in raised)  # each sent once, by the first cycle that could
    assert {a["id"] for a in sn[4]["alerts"] if a["event"] == "SENT"} == {a["id"] for a in raised}
    fwd = sn[4]["forward"]
    passed = set(sn[3]["tasks"]["validate:DLAB-SYN-1"]["result"]["passed"])
    assert {f["rule"] for f in fwd} == passed and all(f["row"] >= "2026-01-01" for f in fwd)  # after the window only
    assert len(fwd) == len({(f["rule"], f["row"]) for f in fwd}) and len(fwd) > 500 * len(passed)
    assert sn[5]["forward"] == fwd  # the same day again: no row is marked twice
    assert story["asked"]["loads"][-1].year == 2100 and "forward:2026-11-12" in sn[4]["tasks"]


def test_the_report_says_what_exists_and_claims_nothing_more(story):
    text = story["snap"][4]["report"]
    assert "RESEARCH ONLY" in text and "بالعربي" in text and "DLAB-SYN-1" in text and "DLAB-SYN-1-V" in text
    for cls in L.T.CLASSES:
        assert cls in text
    assert "A paper about lead-lag" in text and "UNREAD" in text
    assert "| `DLAB-SYN-1-V` |" in text and "PASSED" in text and "Rows since its validation window" in text
    assert "syn_feed" in text and "3 instruments" in text and "No model call" in text
    lessons = json.loads((story["root"] / "research" / "dlab" / "lessons.json").read_text())
    assert lessons["arms"]["synthetic"] and any("passed validation" in x for x in lessons["lessons"])


def copy_lab(story, tmp_path, monkeypatch, which="repo"):
    root = tmp_path / "repo"
    shutil.copytree(story["tmp"] / which if which != "repo" else story["root"], root)
    asked = make_lab(root, monkeypatch)
    return root, asked


def test_a_tampered_record_stops_every_experiment_and_is_reported(story, tmp_path, monkeypatch):
    root, asked = copy_lab(story, tmp_path, monkeypatch)
    art = root / "research" / "knowledge" / "DLAB-SYN-1.json"
    body = json.loads(art.read_text())
    body["records"][0]["class"] = "PROMISING_UNCONFIRMED"  # a candidate promoted after the fact
    art.write_text(json.dumps(body))
    state = tmp_path / "state"
    before = registry_lines(root)
    assert C.cycle(state, NOW + timedelta(days=3)) == 1
    st = Store(state)
    assert tasks(st) == {} and asked["feeds"] == [] and asked["loads"] == [] and registry_lines(root) == before
    assert [a["level"] for a in st.read("alerts")] == ["PROBLEM"] and "DLAB-SYN-1" in st.read("alerts")[0]["body"]
    assert "failed its integrity check" in (state / "LAB_REPORT.md").read_text()
    assert st.read("runs")[0]["status"] == "FAILED"


def test_a_candidate_cannot_be_dropped_from_the_ledger(story, tmp_path, monkeypatch):
    root, _ = copy_lab(story, tmp_path, monkeypatch)
    led = root / "research" / "dlab" / "candidates.jsonl"
    lines = led.read_text().splitlines()
    led.write_text("\n".join(lines[1:]) + "\n")
    assert any("ledger holds" in p for p in C.integrity())
    led.write_text("\n".join(lines) + "\n")
    assert C.integrity() == []
    (root / "research" / "holdout.json").write_text(json.dumps({"universe": "fx-majors", "start": "2020-01-01",
                                                                "rationale": "moved", "sealed_at": "2026-09-26T20:28:47+00:00"}))
    assert any("seal" in p for p in C.integrity())


def test_a_scan_whose_record_was_pushed_but_whose_queue_was_lost_is_resumed_not_repeated(story, tmp_path, monkeypatch):
    root, asked = copy_lab(story, tmp_path, monkeypatch, "repo_after_scan")
    before = registry_lines(root)
    state = tmp_path / "empty"  # the state of the cycle that ran the scan never reached lab-data
    assert C.cycle(state, NOW + timedelta(hours=7), max_tasks=2) == 0
    t = tasks(Store(state))
    scan = t["scan:syn:" + C.DLAB_VERSION + ":7"]
    assert scan["args"]["run"] == "DLAB-SYN-1" and scan["status"] == "DONE"  # the same run, not a DLAB-SYN-2
    assert registry_lines(root) == before and asked["loads"] == []  # nothing registered, no row read again
    assert t["validate:DLAB-SYN-1"]["status"] == "QUEUED"  # and its validation is queued, as it was


def test_a_feed_that_keeps_failing_is_retried_three_times_then_reported_and_blocks_no_report(tmp_path, monkeypatch):
    calls = []

    def broken(data, now):
        calls.append(now)
        raise RuntimeError("the archive did not answer")
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch, feed=broken)
    state = tmp_path / "state"
    for i in range(5):
        assert C.cycle(state, NOW + timedelta(hours=6 * i), max_tasks=2) == 0  # a failed task is not a failed cycle
    st = Store(state)
    t = tasks(st)
    assert len(calls) == 3 and t["data:syn_feed:2026-11"]["status"] == "FAILED" and t["data:syn_feed:2026-11"]["attempts"] == 3
    assert t["scan:syn:" + C.DLAB_VERSION + ":7"]["attempts"] == 0 and asked["loads"] == [] and registry_lines(root) == 0
    problems = [a for a in st.read("alerts") if a["level"] == "PROBLEM"]
    assert len(problems) == 1 and "data:syn_feed:2026-11" in problems[0]["title"]  # raised once, not every cycle
    text = (state / "LAB_REPORT.md").read_text()
    assert "failed on every attempt" in text and "the archive did not answer" in text and "its data (syn_feed) are not on file yet" in text
    assert t["sources:2026-W46"]["status"] == "DONE"  # the rest of the queue went on


def test_a_thin_panel_is_refused(tmp_path, monkeypatch):
    def thin(data, now):
        return {"retrieved": now.isoformat(), "quality": {"A0": {"rows": 900, "last": "2026-11-10"}, "A1": {"rows": 100, "last": "2026-11-10"}}}
    root = tmp_path / "repo"
    root.mkdir()
    make_lab(root, monkeypatch, feed=thin)
    assert C.cycle(tmp_path / "state", NOW, max_tasks=1) == 0
    r = tasks(Store(tmp_path / "state"))["data:syn_feed:2026-11"]
    assert r["status"] == "FAILED" and "only 1 instruments" in r["result"]["error"]


def test_a_task_is_not_started_without_the_time_it_may_need(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch)
    ticks = iter([0.0] + [43.5 * 60] * 50)  # the cycle is 43.5 minutes old when it looks at the queue
    assert C.cycle(tmp_path / "state", NOW, max_minutes=45.0, clock=lambda: next(ticks)) == 0
    t = tasks(Store(tmp_path / "state"))
    assert asked["feeds"] == [] and t["data:syn_feed:2026-11"]["attempts"] == 0  # ten minutes needed, 1.5 left
    assert t["sources:2026-W46"]["attempts"] == 0  # two needed
    assert Store(tmp_path / "state").read("budget")[0]["tasks"] == 0


def test_a_scan_registered_under_code_that_then_changed_is_abandoned_and_queued_afresh(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    make_lab(root, monkeypatch)
    state = tmp_path / "state"
    real = L.scan
    monkeypatch.setattr(L, "scan", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("the runner died")))
    assert C.cycle(state, NOW, max_tasks=2) == 0  # data, then a scan that registers and dies
    reg = Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))
    assert reg.get("DLAB-SYN-1") and reg.verdict_of("DLAB-SYN-1") is None
    monkeypatch.setattr(L, "scan", real)
    monkeypatch.setattr(L, "code_hash", lambda: "d" * 64)  # the lab's code changes before the next cycle
    assert C.cycle(state, NOW + timedelta(hours=6), max_tasks=1) == 0
    reg = Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))
    assert reg.verdict_of("DLAB-SYN-1").status == "ABANDONED" and not (root / "research" / "knowledge" / "DLAB-SYN-1.json").exists()
    t = tasks(Store(state))
    nxt = t["scan:syn:" + C.DLAB_VERSION + ":7:after-DLAB-SYN-1"]
    assert nxt["args"]["run"] == "DLAB-SYN-2" and nxt["status"] == "QUEUED"
    assert C.integrity() == []  # an abandoned scan is part of the record, not a hole in it


def test_an_alert_is_raised_once_and_sent_once_and_an_unsent_one_is_tried_again(tmp_path):
    st = Store(tmp_path)
    assert C.alert(st, NOW, "PROBLEM", "the title", "body") and not C.alert(st, NOW, "PROBLEM", "the title", "again")
    assert C.send_alerts(st, NOW, lambda a: (_ for _ in ()).throw(OSError("no network"))) == 0
    assert C.send_alerts(st, NOW, lambda a: None) == 0  # could not be sent now
    got = []
    assert C.send_alerts(st, NOW, lambda a: got.append(a["title"]) or "https://issue/1") == 1
    assert C.send_alerts(st, NOW, lambda a: got.append(a["title"]) or "https://issue/2") == 0 and got == ["the title"]
    assert C.github_issue({}) is None  # no token: a local run sends nothing
    assert callable(C.github_issue({"GITHUB_TOKEN": "t", "GITHUB_REPOSITORY": "o/r"}))
