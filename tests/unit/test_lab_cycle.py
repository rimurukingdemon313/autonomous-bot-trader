"""The autonomous lab's cycle, end to end in a scratch repository on a built market: data, then a registered scan,
then the preregistered validation of what it found, then the forward marks of what passed. Each cycle starts from a
copy of the last one's state, as a fresh machine does. Nothing runs twice; a run that dies is taken up again; a
tampered record stops every experiment; a task that keeps failing is reported, not retried for ever."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.dlab as L
import scripts.lab_cycle as C
from aitrader.research.dlab import datasets as D
from aitrader.research.dlab import feeds as F
from aitrader.research.dlab.panel import Panel
from aitrader.research.dlab.store import Store, tasks
from aitrader.research.registry import Holdout, Registry

NOW = datetime(2026, 11, 11, 4, 0, tzinfo=timezone.utc)
REAL = {"CATALOG": dict(C.CATALOG), "DUE": dict(C.DUE)}  # the panels the worker really scans, before any test's patch
W = {"fit": (date(2000, 1, 3), date(2009, 8, 1)), "check": (date(2009, 8, 1), date(2017, 4, 1)),
     "validation": (date(2017, 4, 1), date(2026, 1, 1))}
SOURCE = {"id": "arxiv:2611.00001", "origin": "arxiv", "url": "http://arxiv.org/abs/2611.00001v1",
          "title": "A paper about lead-lag", "published": "2026-11-09", "status": "UNREAD", "reproducibility": "not attempted"}


def make_lab(root, mp, feed=None, last="2028-09-29", daily=True, full=None, windows=None):
    """A scratch repository with an empty registry, a built market with a planted lead-lag, and a feed that touches
    no network. Returns what the feed and the loader were asked. `last` is the last day the feed says it holds; a
    `daily` panel is refreshed by the forward marks, as the ETF panel is."""
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
    full = full if full is not None else D.synthetic(rows=7500, seed=100, plant={"leadlag": 0.12})
    asked = {"loads": [], "feeds": [], "last": last}

    def loader(last):
        asked["loads"].append(last)
        return full.head(sum(t < last for t in full.times))

    def fake_feed(data, now):
        asked["feeds"].append(now)
        data.mkdir(parents=True, exist_ok=True)
        (data / "close.json").write_text("{}")
        man = {"retrieved": now.isoformat(), "incomplete": None,
               "quality": {a: {"rows": 7500, "first": "2000-01-03", "last": asked["last"], "missing_days": 0,
                               "moves_beyond_50pct": 0} for a in full.assets}}
        (data / "manifest.json").write_text(json.dumps(man))
        return man
    mp.setitem(D.WINDOWS, "synthetic", windows or W)
    mp.setitem(L.DATASETS, "syn", ("synthetic", loader, 5))
    mp.setattr(C, "CATALOG", {"syn": {"tag": "SYN", "feed": "syn_feed", "instruments": len(full.assets), "daily": daily}})
    mp.setattr(C, "FEEDS", {"syn_feed": feed or fake_feed})
    mp.setattr(C, "DUE", {})
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
                   "alerts": Store(s).read("alerts"), "report": (s / "LAB_REPORT.md").read_text()}
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
        again = C.do_forward(Store(s), s, {}, NOW + timedelta(days=2))  # the marks asked for once more, another day
        snap[6] = {"again": again, "forward": Store(s).read("forward")}
        yield {"root": root, "tmp": tmp, "state": s, "snap": snap, "posted": posted, "asked": asked}
    finally:
        mp.undo()


def status(snap, n):
    return {k: v["status"] for k, v in snap[n]["tasks"].items()}


def test_data_first_then_a_registered_scan_then_its_validation_one_task_a_cycle(story):
    sn = story["snap"]
    assert [sn[i]["code"] for i in range(1, 6)] == [0] * 5
    assert status(sn, 1) == {"data:syn_feed:2026-11": "DONE", "scan:syn:" + C.SCAN_VERSION + ":7": "QUEUED",
                             "sources:2026-W46": "QUEUED"}
    # the scan waited for its data. The data step looked at the discovery rows (is the panel usable?); nothing registered
    assert sn[1]["registry"] == 0 and set(sn[1]["loads"]) == {W["check"][1]}
    scan = "scan:syn:" + C.SCAN_VERSION + ":7"
    assert status(sn, 2)[scan] == "DONE" and status(sn, 2)["validate:DLAB-SYN-1"] == "QUEUED"
    assert sn[2]["registry"] == 2 and set(sn[2]["loads"]) == {W["check"][1]}  # a trial and its verdict; discovery rows only
    assert sn[2]["tasks"][scan]["result"]["verdict"] == "PASSED" and sn[2]["tasks"][scan]["result"]["batch"] >= 1
    assert status(sn, 3)["validate:DLAB-SYN-1"] == "DONE" and sn[3]["registry"] == 4
    # the batch re-checked on the discovery rows; the validation rows loaded once, by the judge, in the cycle that
    # registered the validation and in no cycle before it
    assert sn[3]["loads"].count(W["validation"][1]) == 1 and set(sn[3]["loads"]) == {W["check"][1], W["validation"][1]}
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
    assert len(story["snap"][4]["feeds"]) == 2  # the month's data once, and once more for the forward marks
    assert "No task ran" in sn[5]["report"] and len(sn[5]["budget"]) == 5 and "cycles so far: 5" in sn[5]["report"]
    assert "cycles so far: 4" in sn[4]["report"]
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
    assert sn[5]["forward"] == fwd  # the same day again: nothing to do
    assert sn[6]["again"] == {"rules": len(passed), "rows_added": 0} and sn[6]["forward"] == fwd  # no row is marked twice
    assert story["asked"]["loads"][-1].year == 2100 and "forward:2026-11-12" in sn[4]["tasks"]


def test_the_report_says_what_exists_and_claims_nothing_more(story):
    text = story["snap"][4]["report"]
    assert "RESEARCH ONLY" in text and "بالعربي" in text and "DLAB-SYN-1" in text and "DLAB-SYN-1-V" in text
    for cls in L.T.CLASSES:
        assert cls in text
    assert "A paper about lead-lag" in text and "UNREAD" in text
    assert "| `DLAB-SYN-1-V` |" in text and "PASSED" in text and "Rows since its validation window" in text
    assert "syn_feed" in text and "3 instruments" in text and "No model call" in text
    passed = story["snap"][3]["tasks"]["validate:DLAB-SYN-1"]["result"]["passed"]
    # every judged rule is listed with its result, and is no longer listed as waiting for its batch
    assert "VALIDATED_ON_UNREAD_ROWS: every gate held" in text and all(f"| `{i}` " in text for i in passed)
    waiting = text.split("### The strongest candidates not yet judged")[1].split("## Independent validation")[0]
    assert "in its scan's validation batch" not in waiting and "a candidate, not a trading system" in text
    # right after the validation, before any forward row is on file: the rules that passed are named, not denied
    early = story["snap"][3]["report"]
    assert "None: no rule has passed its validation" not in early and all(f"| `{i}` " in early for i in passed)
    assert early.count("0: no row after its window is on file yet") == len(passed)
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
    scan = t["scan:syn:" + C.SCAN_VERSION + ":7"]
    assert scan["args"]["run"] == "DLAB-SYN-1" and scan["status"] == "DONE"  # the same run, not a DLAB-SYN-2
    # nothing registered again; the only read is the data step's look at the discovery rows
    assert registry_lines(root) == before and set(asked["loads"]) == {W["check"][1]}
    assert t["validate:DLAB-SYN-1"]["status"] == "QUEUED"  # and its validation is queued, as it was


def test_a_feed_that_keeps_failing_is_retried_three_times_then_reported_and_blocks_no_report(tmp_path, monkeypatch):
    calls = []

    def broken(data, now):
        calls.append(now)
        raise RuntimeError("the archive did not answer")
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch, feed=broken)
    post(root, hypothesis())
    state = tmp_path / "state"
    for i in range(5):
        assert C.cycle(state, NOW + timedelta(hours=6 * i), max_tasks=2) == 0  # a failed task is not a failed cycle
    st = Store(state)
    t = tasks(st)
    assert len(calls) == 3 and t["data:syn_feed:2026-11"]["status"] == "FAILED" and t["data:syn_feed:2026-11"]["attempts"] == 3
    assert t["scan:syn:" + C.SCAN_VERSION + ":7"]["attempts"] == 0 and asked["loads"] == [] and registry_lines(root) == 0
    assert t["directed:D-leadlag"]["attempts"] == 0  # a submitted hypothesis waits for whole data too
    problems = [a for a in st.read("alerts") if a["level"] == "PROBLEM"]
    assert len(problems) == 1 and "data:syn_feed:2026-11" in problems[0]["title"]  # raised once, not every cycle
    text = (state / "LAB_REPORT.md").read_text()
    assert "failed on every attempt" in text and "the archive did not answer" in text
    assert "its data (syn_feed) are not completely on file yet" in text
    assert t["sources:2026-W46"]["status"] == "DONE"  # the rest of the queue went on


def test_a_task_that_failed_under_an_older_worker_is_tried_afresh_under_a_new_one_and_never_under_the_same(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch)
    good, box = C.FEEDS["syn_feed"], {"broken": True}

    def feed(data, now):
        if box["broken"]:
            asked["feeds"].append(now)
            raise RuntimeError("a bug in the worker")
        return good(data, now)
    monkeypatch.setattr(C, "FEEDS", {"syn_feed": feed})
    monkeypatch.setattr(C, "CYCLE_VERSION", "worker-1")
    state = tmp_path / "state"
    for i in range(5):
        assert C.cycle(state, NOW + timedelta(hours=6 * i), max_tasks=1) == 0
    t = tasks(Store(state))["data:syn_feed:2026-11"]
    assert t["status"] == "FAILED" and t["attempts"] == 3 and t["by"] == "worker-1" and len(asked["feeds"]) == 3
    box["broken"] = False  # the bug is gone from the world, and the worker is the same: the task stays where it failed
    assert C.cycle(state, NOW + timedelta(days=2), max_tasks=2) == 0
    assert len(asked["feeds"]) == 3 and not any(e["event"] == "RETRY" for e in Store(state).read("queue"))
    monkeypatch.setattr(C, "CYCLE_VERSION", "worker-2")  # a new version of the worker: what failed it may be what changed
    assert C.cycle(state, NOW + timedelta(days=2, hours=6), max_tasks=1) == 0
    t = tasks(Store(state))["data:syn_feed:2026-11"]
    assert t["status"] == "DONE" and t["attempts"] == 1 and t["by"] == "worker-2" and len(asked["feeds"]) == 4
    log = [r for r in Store(state).read("runs") if r["step"] == "queue"][-1]
    assert log["detail"]["given_back_after_a_new_version"] == ["data:syn_feed:2026-11"]
    assert C.cycle(state, NOW + timedelta(days=3), max_tasks=1) == 0  # given back once, not at every cycle
    assert sum(e["event"] == "RETRY" for e in Store(state).read("queue")) == 1
    assert "gives a failed task its attempts back, once" in (state / "LAB_REPORT.md").read_text()


def test_a_scan_waits_for_a_complete_fetch_and_what_arrived_is_kept(tmp_path, monkeypatch):
    state = {"failed": 3}

    def partial(data, now):
        data.mkdir(parents=True, exist_ok=True)
        (data / "close.json").write_text("{}")  # what arrived is on file
        why = f"the archive did not answer for {state['failed']} files (the first: A0:klines:2021-03). What arrived is kept"
        man = {"retrieved": now.isoformat(), "failed_count": state["failed"], "failed_now": ["A0:klines:2021-03"],
               "incomplete": why if state["failed"] else None,
               "quality": {a: {"rows": 7500, "last": "2028-09-29"} for a in ("A0", "A1", "A2")}}
        (data / "manifest.json").write_text(json.dumps(man))
        return man
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch, feed=partial)
    st = tmp_path / "state"
    assert C.cycle(st, NOW, max_tasks=3) == 0
    t = tasks(Store(st))
    assert t["data:syn_feed:2026-11"]["status"] == "FAILED" and "did not answer for 3 files" in t["data:syn_feed:2026-11"]["result"]["error"]
    assert (st / "data" / "syn_feed" / "close.json").exists()  # kept for the next attempt
    assert t["scan:syn:" + C.SCAN_VERSION + ":7"]["attempts"] == 0 and asked["loads"] == [] and registry_lines(root) == 0
    state["failed"] = 0  # the archive answers: the fetch completes, and only then may the panel be scanned
    assert C.cycle(st, NOW + timedelta(hours=6), max_tasks=1) == 0
    t = tasks(Store(st))
    assert t["data:syn_feed:2026-11"]["status"] == "DONE" and t["scan:syn:" + C.SCAN_VERSION + ":7"]["attempts"] == 0
    assert C.ready(t["scan:syn:" + C.SCAN_VERSION + ":7"], st, Store(st)) is None
    # a later fetch that is not complete leaves holes on file: the finished fetch of last month does not make them whole
    state["failed"] = 2
    partial(st / "data" / "syn_feed", NOW + timedelta(days=30))
    why = C.ready(t["scan:syn:" + C.SCAN_VERSION + ":7"], st, Store(st))
    assert "its data (syn_feed) are not completely on file yet" in why and "did not answer for 2 files" in why
    assert C.cycle(st, NOW + timedelta(hours=12), max_tasks=3) == 0
    assert tasks(Store(st))["scan:syn:" + C.SCAN_VERSION + ":7"]["attempts"] == 0 and registry_lines(root) == 0


def test_a_thin_panel_is_refused(tmp_path, monkeypatch):
    def thin(data, now):
        return {"retrieved": now.isoformat(), "quality": {"A0": {"rows": 900, "last": "2026-11-10"}, "A1": {"rows": 100, "last": "2026-11-10"}}}
    root = tmp_path / "repo"
    root.mkdir()
    make_lab(root, monkeypatch, feed=thin)
    assert C.cycle(tmp_path / "state", NOW, max_tasks=1) == 0
    r = tasks(Store(tmp_path / "state"))["data:syn_feed:2026-11"]
    assert r["status"] == "FAILED" and "only 1 instruments" in r["result"]["error"]


def test_files_that_arrived_but_make_no_usable_panel_stop_the_scan_before_it_is_registered(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch)
    assert C.usable_instruments("syn") == 3 and asked["loads"] == [W["check"][1]]  # counted on the discovery rows only
    monkeypatch.setattr(C, "MIN_INSTRUMENTS", {"syn_feed": 4})  # the manifest counts three; a scan here would need four

    def four(data, now):  # the files arrive whole, and say so: only the panel they make is too thin in its fit rows
        data.mkdir(parents=True, exist_ok=True)
        (data / "close.json").write_text("{}")
        man = {"retrieved": now.isoformat(), "incomplete": None,
               "quality": {a: {"rows": 7500, "last": "2028-09-29"} for a in ("A0", "A1", "A2", "A3")}}
        (data / "manifest.json").write_text(json.dumps(man))
        return man
    monkeypatch.setattr(C, "FEEDS", {"syn_feed": four})
    state = tmp_path / "state"
    assert C.cycle(state, NOW, max_tasks=2) == 0
    t = tasks(Store(state))
    r = t["data:syn_feed:2026-11"]
    assert r["status"] == "FAILED" and "only 3 instruments of the syn panel have the fit rows" in r["result"]["error"]
    assert C.incomplete(state, "syn_feed") is None  # whole files on disk are not a finished fetch: the scan still waits
    assert t["scan:syn:" + C.SCAN_VERSION + ":7"]["attempts"] == 0 and registry_lines(root) == 0  # nothing registered
    assert C.ready(t["scan:syn:" + C.SCAN_VERSION + ":7"], state, Store(state)) == "its data (syn_feed) are not completely on file yet"


def test_a_validation_waits_until_the_files_reach_the_end_of_its_window(story, tmp_path, monkeypatch):
    root = tmp_path / "repo"
    shutil.copytree(story["tmp"] / "repo_after_scan", root)
    asked = make_lab(root, monkeypatch, last="2025-12-26")  # the files stop six days before the window's end
    before = registry_lines(root)
    state = tmp_path / "state"
    assert C.cycle(state, NOW + timedelta(hours=7), max_tasks=4) == 0
    st = Store(state)
    v = tasks(st)["validate:DLAB-SYN-1"]
    assert v["status"] == "QUEUED" and v["attempts"] == 0 and v["args"]["dataset"] == "syn"  # waiting is not an attempt
    assert C.ready(v, state, st) == "its data (syn_feed) end on 2025-12-26, before its validation window does (2026-01-01)"
    # nothing was registered, and no validation row was read
    assert registry_lines(root) == before and W["validation"][1] not in asked["loads"]
    assert "before its validation window does" in (state / "LAB_REPORT.md").read_text()
    asked["last"] = "2025-12-27"  # five days: a weekend and a holiday. The files hold the window
    C.FEEDS["syn_feed"](state / "data" / "syn_feed", NOW + timedelta(hours=8))
    assert C.ready(v, state, st) is None
    assert C.cycle(state, NOW + timedelta(hours=13), max_tasks=1) == 0
    assert tasks(Store(state))["validate:DLAB-SYN-1"]["status"] == "DONE" and registry_lines(root) == before + 2


def test_the_judge_refuses_a_panel_that_stops_before_its_window_ends(story, tmp_path, monkeypatch):
    root = tmp_path / "repo"
    shutil.copytree(story["tmp"] / "repo_after_scan", root)
    make_lab(root, monkeypatch)
    universe, loader, lags = L.DATASETS["syn"]
    p = loader(W["validation"][1])
    assert str(p.times[-1]) == "2025-12-31" and L.covers(p, W["validation"]) is None
    assert L.covers(p.head(p.T - 2), W["validation"]) is None  # Monday the 29th: three days
    assert "ends on 2025-12-26, 6 days before its validation window does (2026-01-01)" in L.covers(p.head(p.T - 3), W["validation"])
    before = registry_lines(root)
    monkeypatch.setitem(L.DATASETS, "syn", (universe, lambda last: loader(min(last, date(2025, 11, 1))), lags))
    with pytest.raises(SystemExit, match="nothing is judged until the data hold the whole window"):
        L.auto_validate("DLAB-SYN-1", NOW + timedelta(days=1))
    reg = Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))
    assert reg.get("DLAB-SYN-1-V") and reg.verdict_of("DLAB-SYN-1-V") is None  # registered; not judged, so not spent
    assert not (root / "research" / "knowledge" / "DLAB-SYN-1-V.json").exists()
    assert '"VALIDATION"' not in (root / "research" / "dlab" / "candidates.jsonl").read_text()
    monkeypatch.setitem(L.DATASETS, "syn", (universe, loader, lags))  # the data arrive: the same registration is judged
    res = L.auto_validate("DLAB-SYN-1", NOW + timedelta(days=2))
    assert res["verdict"] == "PASSED" and res["validation_rows"] > 2000 and registry_lines(root) == before + 2


def test_no_forward_mark_from_a_panel_that_is_not_whole_or_a_rule_that_no_longer_computes_as_judged(story, tmp_path, monkeypatch):
    root, asked = copy_lab(story, tmp_path, monkeypatch)  # the story's repository at its end: validated rules exist
    state = tmp_path / "state"
    shutil.copytree(story["state"], state)
    st = Store(state)
    marked = st.read("forward")
    lines = (state / "forward.jsonl").read_text().splitlines()
    assert len(lines) == len(marked) > 500
    (state / "forward.jsonl").write_text("\n".join(lines[:-40]) + "\n")  # forty marks are still to be written
    before = st.read("forward")
    rules = C.validated_rules()
    assert rules and all(r["t"] >= 3.0 and r["lags"] == 5 for r in rules) and len(before) == len(marked) - 40
    later = NOW + timedelta(days=400)
    man = state / "data" / "syn_feed" / "manifest.json"
    whole = man.read_text()
    calls = []
    monkeypatch.setattr(C, "FEEDS", {"syn_feed": lambda data, now: calls.append(now)})  # a refresh that changes nothing
    # 1. files that are not a whole panel: the dataset waits, and nothing is marked
    man.write_text(json.dumps({**json.loads(whole), "incomplete": "the source did not serve A1"}))
    res = C.do_forward(st, state, {}, later)
    assert res == {"rules": len(rules), "rows_added": 0, "waiting_for_whole_data": {"syn": "the source did not serve A1"}}
    assert st.read("forward") == before and len(calls) == 1  # a daily panel: the marks asked the feed
    man.write_text(whole)
    # 2. a monthly panel is not fetched by the marks: its data task brings its rows
    monkeypatch.setattr(C, "CATALOG", {"syn": {"tag": "SYN", "feed": "syn_feed", "instruments": 3}})
    # 3. a panel whose validation rows are no longer what the judge read: the rule gives another t there
    universe, loader, lags = L.DATASETS["syn"]

    def revised(last):
        p = loader(last)
        ret = p.ret.copy()
        rows = np.nonzero(p.rows(*W["validation"]))[0][100:160]
        ret[rows] = ret[rows] * 3.0  # sixty days restated
        return Panel(p.name, p.times, p.assets, ret, p.aux, p.cost, p.ppy, p.hold_cost)
    monkeypatch.setitem(L.DATASETS, "syn", (universe, revised, lags))
    with pytest.raises(RuntimeError, match="its\n? ?judge recorded|no forward mark is written"):
        C.do_forward(st, state, {}, later)
    assert st.read("forward") == before and len(calls) == 1  # nothing written; the monthly panel's feed was not asked
    monkeypatch.setitem(L.DATASETS, "syn", (universe, loader, lags))
    res = C.do_forward(st, state, {}, later)  # the judged data again: the marks go on
    assert res == {"rules": len(rules), "rows_added": 40}
    assert {(f["rule"], f["row"], f["net"]) for f in st.read("forward")} == {(f["rule"], f["row"], f["net"]) for f in marked}


def test_forward_marks_that_keep_failing_raise_one_alert_a_month_not_one_a_day(story, tmp_path, monkeypatch):
    root, asked = copy_lab(story, tmp_path, monkeypatch)
    state = tmp_path / "state"
    shutil.copytree(story["state"], state)
    universe, loader, lags = L.DATASETS["syn"]

    def revised(last):
        p = loader(last)
        return Panel(p.name, p.times, p.assets, p.ret * 1.5, p.aux, p.cost, p.ppy, p.hold_cost)
    monkeypatch.setitem(L.DATASETS, "syn", (universe, revised, lags))
    for day in (date(2026, 11, 14), date(2026, 11, 15), date(2026, 12, 11)):
        for hour in (1, 7, 13):  # three cycles a day: the day's task fails on each
            assert C.cycle(state, datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc), max_tasks=4) == 0
    st = Store(state)
    t = tasks(st)
    assert all(t[f"forward:{d}"]["status"] == "FAILED" and t[f"forward:{d}"]["attempts"] == 3
               for d in ("2026-11-14", "2026-11-15", "2026-12-11"))
    titles = [a["title"] for a in st.read("alerts") if a["event"] == "RAISED" and a["level"] == "PROBLEM"]
    assert titles == ["the forward marks of 2026-11 failed on each of 3 attempts",
                      "the forward marks of 2026-12 failed on each of 3 attempts"]
    assert st.read("forward") == Store(story["state"]).read("forward")  # and no mark was written meanwhile


def test_a_data_task_is_named_by_the_newest_period_its_feed_can_bring(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    make_lab(root, monkeypatch)
    for k, v in REAL.items():
        monkeypatch.setattr(C, k, v)  # the real panels: crypto by the archive's month, the funds by the calendar's
    st, reg = Store(tmp_path / "state"), L._registry()

    def data(now):
        return sorted(x for x in C.seed(st, reg, now) if x.startswith("data:"))
    assert data(datetime(2026, 11, 5, tzinfo=timezone.utc)) == ["data:crypto_daily:2026-09", "data:etf_daily:2026-11"]
    assert data(datetime(2026, 11, 9, tzinfo=timezone.utc)) == []  # the same period: nothing new is due
    # from the tenth the archive should hold October whole: a new task, so the month's rows are fetched this month
    assert data(datetime(2026, 11, 10, tzinfo=timezone.utc)) == ["data:crypto_daily:2026-10"]
    assert data(datetime(2026, 12, 2, tzinfo=timezone.utc)) == ["data:etf_daily:2026-12"]
    # the funds' panel is refreshed by the forward marks each day; the perpetuals' only by its monthly data task
    assert C.CATALOG["etf-daily"].get("daily") is True and not C.CATALOG["crypto-daily"].get("daily")


PLANTED = {"kind": "sign", "target": "A1", "feat": {"f": "ret", "a": "A0", "k": 1}, "w": 250, "band": 0.5, "side": 1}


def hypothesis(sid="D-leadlag", **more) -> dict:
    return {"id": sid, "submitted": "2026-11-11", "dataset": "syn", "parents": [],
            "author": {"role": "director", "model": "test-model", "interface": "a test"},
            "title": "A0's move leads A1's next row",
            "hypothesis": "A1's next row moves with the sign of A0's last move, beyond half a standard deviation.",
            "mechanism": "A1 is slower to take in what moves A0: a lead-lag between two related instruments.",
            "why_now": "Stated directly, as one rule, rather than found by a search.",
            "refuted_by": "A check-row mean that is not positive in both halves.",
            "rules": [{"family": "cross-asset lead-lag", "why": "the link as one rule", "orient": "fit", "spec": L.mirror(PLANTED)}],
            **more}


def post(root, body, name=None) -> None:
    box = root / C.INBOX
    box.mkdir(parents=True, exist_ok=True)
    (box / f"{name or body['id']}.json").write_text(body if isinstance(body, str) else json.dumps(body))


def test_a_hypothesis_in_the_inbox_becomes_a_registered_test_and_what_it_finds_is_validated(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    asked = make_lab(root, monkeypatch)
    state = tmp_path / "state"
    assert C.cycle(state, NOW, max_tasks=1) == 0  # the data
    post(root, hypothesis())
    post(root, "{not json", "broken")
    post(root, hypothesis("another-name"), "misnamed")
    post(root, hypothesis("elsewhere", dataset="energy"))
    post(root, hypothesis("no-mechanism", mechanism=""))
    assert C.cycle(state, NOW + timedelta(hours=6), max_tasks=1) == 0
    st = Store(state)
    subs = {r["id"]: r for r in st.read("submissions")}
    assert subs["D-leadlag"]["event"] == "QUEUED" and subs["D-leadlag"]["run"] == "DLAB-SYN-D1"
    assert subs["broken"]["why"] == ["it is not JSON"] and subs["misnamed"]["why"] == ["its id is not its file's name"]
    assert "fetches no data for energy" in subs["elsewhere"]["why"][0] and "`mechanism`" in subs["no-mechanism"]["why"][0]
    t = tasks(st)
    d = t["directed:D-leadlag"]
    # asked by the director, executed by the worker, before the scan (a stated hypothesis outranks a search)
    assert d["status"] == "DONE" and d["origin"] == "director:test-model" and d["owner"] == "lab-worker" and d["attempts"] == 1
    assert d["result"]["verdict"] == "PASSED" and d["result"]["registered"] and d["result"]["batch"] == 1
    assert t["scan:syn:" + C.SCAN_VERSION + ":7"]["attempts"] == 0 and len(t) == 5  # no task for a refused submission
    assert t["validate:DLAB-SYN-D1"]["status"] == "QUEUED" and t["validate:DLAB-SYN-D1"]["origin"] == "director:test-model"
    reg = Registry.load(root / "research" / "registry.jsonl", Holdout.load(root / "research" / "holdout.json"))
    assert [x.id for x in reg.trials] == ["DLAB-SYN-D1"] and reg.get("DLAB-SYN-D1").tests == 1
    assert W["validation"][1] not in asked["loads"]  # found on the discovery rows; nothing has read the validation rows
    report, brief = (state / "LAB_REPORT.md").read_text(), (state / "DIRECTOR_BRIEFING.md").read_text()
    assert "| `DLAB-SYN-D1` | director (test-model) | A0's move leads A1's next row | 1 | 0 | 1 | PASSED |" in report
    assert "`broken`: it is not JSON" in report and "`no-mechanism`: `mechanism` must say something" in report
    assert "| `DLAB-SYN-D1` | directed_test | PASSED |" in brief and "refused: `misnamed`" in brief
    assert "How a hypothesis is submitted" in brief and "It approves nothing" in brief
    assert C.cycle(state, NOW + timedelta(hours=12), max_tasks=1) == 0  # its validation: the judge, on unread rows
    v = tasks(Store(state))["validate:DLAB-SYN-D1"]
    assert v["status"] == "DONE" and v["result"]["verdict"] == "PASSED" and asked["loads"].count(W["validation"][1]) == 1
    assert [a["level"] for a in Store(state).read("alerts") if a["event"] == "RAISED"] == ["DISCOVERY"]
    assert C.cycle(state, NOW + timedelta(hours=18), max_tasks=4) == 0  # the scan and the rest; nothing runs twice
    t = tasks(Store(state))
    # the test and its validation, then the scan and the validation of the scan's own batch: two lines each
    assert all(x["attempts"] == 1 for x in t.values()) and registry_lines(root) == 8
    assert len(Store(state).read("submissions")) == 5  # a submission is looked at once, the refused ones too
    # the director reviews it: it is no longer waiting. A review is a record, never an approval
    assert C.reviewed() == set() and "| `DLAB-SYN-D1-V` | discovery_validation | PASSED |" in (state / "DIRECTOR_BRIEFING.md").read_text()
    log = root / "research" / "director" / "log.jsonl"
    log.write_text(json.dumps({"action": "REVIEW", "of": ["DLAB-SYN-D1", "DLAB-SYN-D1-V", "DLAB-SYN-1"]}) + "\n"
                   + json.dumps({"action": "PLAN", "of": ["DLAB-OTHER"]}) + "\n")
    assert C.reviewed() == {"DLAB-SYN-D1", "DLAB-SYN-D1-V", "DLAB-SYN-1"}  # a plan is not a review
    late = C.briefing(Store(state), state, NOW + timedelta(days=1), [])
    assert "| `DLAB-SYN-1-V` | discovery_validation |" in late and "| `DLAB-SYN-D1` |" not in late  # one run still waits
    with open(log, "a") as fh:  # a line that is not JSON, or not a review, reviews nothing and stops nothing
        fh.write("not json\n" + json.dumps(["REVIEW"]) + "\n" + json.dumps({"action": "REVIEW", "of": "DLAB-X"}) + "\n"
                 + json.dumps({"action": "REVIEW", "of": ["DLAB-SYN-1-V"]}) + "\n")
    assert "None: every judged run is named in a REVIEW entry" in C.briefing(Store(state), state, NOW + timedelta(days=1), [])
    # a submission with nothing left to test is answered once: it is not a failure, and it is not retried
    post(root, hypothesis("D-again", rules=[{"family": "cross-asset lead-lag", "why": "the same rule again", "spec": PLANTED}]))
    assert C.cycle(state, NOW + timedelta(days=1, hours=6), max_tasks=4) == 0
    r = tasks(Store(state))["directed:D-again"]
    assert r["status"] == "DONE" and r["attempts"] == 1 and r["result"]["verdict"] == "REFUSED" and not r["result"]["registered"]
    assert "not looked at twice" in r["result"]["refused"][0]["why"] and registry_lines(root) == 8
    assert "`D-again`: no rule of the submission can be tested" in (state / "LAB_REPORT.md").read_text()
    # a fresh machine with no memory: the test's record is in the repository, so it is resumed under its name
    again = tmp_path / "fresh"
    assert C.cycle(again, NOW + timedelta(days=2), max_tasks=4) == 0
    t2 = tasks(Store(again))
    assert t2["directed:D-leadlag"]["args"]["run"] == "DLAB-SYN-D1" and t2["directed:D-leadlag"]["status"] == "DONE"
    assert registry_lines(root) == 8  # no second registration, no second look


def test_the_lab_fills_the_holes_in_its_own_map_once_and_then_says_why_it_is_idle(tmp_path, monkeypatch):
    full = D.synthetic(rows=1700, assets=8, seed=11, plant={"xs": 0.06}, cost=0.00005)
    win = {"fit": (full.times[250], full.times[900]), "check": (full.times[900], full.times[1350]),
           "validation": (full.times[1350], full.times[-1] + timedelta(days=1))}
    root = tmp_path / "repo"
    root.mkdir()
    make_lab(root, monkeypatch, full=full, windows=win)
    state = tmp_path / "state"
    assert C.cycle(state, NOW, max_tasks=1) == 0  # the data
    assert not [k for k in tasks(Store(state)) if k.startswith("directed:lab-coverage")]  # no map before a scan
    assert C.cycle(state, NOW + timedelta(hours=1), max_tasks=1) == 0  # the scan
    st = Store(state)
    t = tasks(st)
    cover = [k for k in t if k.startswith("directed:lab-coverage-syn-")]
    # the scan's own places left holes: the next task is queued by the cycle that ran the scan, with no one asking
    assert t["scan:syn:" + C.SCAN_VERSION + ":7"]["status"] == "DONE" and len(cover) == 1
    task = t[cover[0]]
    holes = C.coverage_of("syn", st)["holes"]
    assert task["status"] == "QUEUED" and task["origin"] == "lab:coverage" and task["args"]["run"] == "DLAB-SYN-D1"
    assert 0 < len(holes) == len(task["args"]["submission"]["rules"]) < 27
    assert {r["cell"] for r in task["args"]["submission"]["rules"]} == {C.V.cell(f, h) for f, h in holes}
    for i in range(1, 6):
        assert C.cycle(state, NOW + timedelta(hours=6 * i), max_tasks=4) == 0
    st = Store(state)
    t = tasks(st)
    done = t[cover[0]]
    assert done["status"] == "DONE" and done["attempts"] == 1 and done["result"]["registered"]
    cov = C.coverage_of("syn", st)
    assert cov["holes"] == [] and cov["cells"] == 27 and cov["looked_at"] + len(cov["set_aside"]) == 27
    assert [k for k in t if k.startswith("directed:lab-coverage")] == cover  # the map is whole: no second task, ever
    art = json.loads((root / "research" / "knowledge" / "DLAB-SYN-D1.json").read_text())
    assert art["submission"]["author"]["role"] == "lab" and len(art["records"]) + len(art["refused_before_registration"]) == len(holes)
    assert set(status_of(t).values()) == {"DONE"}
    report, brief = (state / "LAB_REPORT.md").read_text(), (state / "DIRECTOR_BRIEFING.md").read_text()
    assert "**Why nothing is queued.** The lab does not invent work." in report
    assert "of its 27 ranking-and-holding-period cells" in report and "0 are holes" in report
    assert "no submission is waiting in `research/director/inbox`" in report and "| `syn` | 27 |" in brief
    assert "- The queue is empty." in brief and "lab (none (deterministic code))" in report
    assert C.integrity() == []


def status_of(t: dict) -> dict:
    return {k: v["status"] for k, v in t.items()}


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
    nxt = t["scan:syn:" + C.SCAN_VERSION + ":7:after-DLAB-SYN-1"]
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
