"""The research pipeline's report (scripts/research_report.py): built on a small registry whose answers are known by
construction, and once on the committed record itself. It keeps each day's research apart from the cumulative record,
counts only ideas actually listed as dropped, flags evidence edited after its verdict, and never reads a trading
figure."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import scripts.research_report as RR

DAY = date(2026, 11, 9)
NOW = datetime(2026, 11, 9, 23, 30, tzinfo=timezone.utc)
SPEC = "a" * 64


def no_classification(root):
    return {"counts": {"REJECTED": 2, "VALIDATED": 1},
            "standing": [{"edge_id": "X-1", "program": "X-1", "status": "VALIDATED", "t_stat": 3.9, "t_required": 3.4,
                          "out_of_sample_expectancy": 0.006, "note": "a test note", "source": "research/knowledge/X-1.json"}]}


def knowledge(root: Path, pid: str, verdict: str) -> str:
    body = {"program": pid, "verdict": verdict, "t": 1.0}
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (root / "research" / "knowledge" / f"{pid}.json").write_text(json.dumps(body, indent=1, sort_keys=True))
    return body["sha256"]


def repo(tmp_path: Path) -> Path:
    r = tmp_path
    for d in ("research/knowledge", "research/preregistrations", "docs"):
        (r / d).mkdir(parents=True, exist_ok=True)
    (r / "research" / "holdout.json").write_text(json.dumps(
        {"universe": "fx-majors", "start": "2017-01-01", "sealed_at": "2026-09-26T20:28:47+00:00",
         "rationale": "a test seal"}))
    (r / "research" / "preregistrations" / "A-1.md").write_text(f"# A-1\n\nspec sha256 {SPEC}\n")
    (r / "research" / "preregistrations" / "B-1.md").write_text("# B-1\n\nno hash here\n")

    def trial(pid, when, uses, prereg=None, spec=None):
        return {"kind": "trial", "id": pid, "registered": when, "title": f"{pid}: a title", "hypothesis": "Is it?",
                "preregistration": prereg, "design": {"spec_sha256": spec} if spec else {}, "tests": 1,
                "configurations": 1, "result": {}, "status": "PENDING", "uses": uses}
    judge = [{"universe": "equity-index-daily", "start": "1990-01-01", "end": "2020-01-01", "role": "judge"}]
    rows = [  # in time order: the registry refuses back-filling
        trial("archive-x", "2026-09-23T00:00:00+00:00",
              [{"universe": "fx-majors", "start": "2012-01-01", "end": "2016-01-01", "role": "judge"}]),
        trial("FWD-1", "2026-11-01T00:00:00+00:00",
              [{"universe": "equity-index-forward", "start": "2026-11-01", "end": "2029-12-01", "role": "judge"}]),
        trial("OLD-1", "2026-11-08T10:00:00+00:00", judge, "research/preregistrations/A-1.md", SPEC),
        {"kind": "verdict", "trial": "OLD-1", "recorded": "2026-11-08T11:00:00+00:00", "status": "FAILED",
         "result": {"artifact": "research/knowledge/OLD-1.json", "artifact_sha256": knowledge(r, "OLD-1", "FAILED")}},
        trial("A-1", "2026-11-09T08:00:00+00:00", judge, "research/preregistrations/A-1.md", SPEC),
        {"kind": "verdict", "trial": "A-1", "recorded": "2026-11-09T09:00:00+00:00", "status": "FAILED",
         "result": {"artifact": "research/knowledge/A-1.json", "artifact_sha256": knowledge(r, "A-1", "FAILED"),
                    "t": 1.2}},
        trial("B-1", "2026-11-09T10:00:00+00:00", judge, "research/preregistrations/B-1.md", "b" * 64),
        {"kind": "verdict", "trial": "B-1", "recorded": "2026-11-09T10:30:00+00:00", "status": "FAILED", "result": {}},
    ]
    (r / "research" / "registry.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
    (r / "research" / "QUEUE.md").write_text("\n".join([
        "# Queue", "",
        "**Checked on 2026-11-09, 06:30 UTC, and dropped before building.**", "",
        "| Idea | Why it was dropped |", "|---|---|", "| First idea | no power |", "| Second idea | costs |", "",
        "**Checked on 2026-11-09, 00:30 UTC, and dropped before building: Z-1 (row 3).** Its analysis:", "",
        "| | |", "|---|---|", "| The trade | a line of analysis, not an idea |", "| Its power | t 1.1 |", "",
        "**Checked on 2026-11-08, 21:30 UTC, and dropped before building.**", "",
        "| Idea | Why it was dropped |", "|---|---|", "| An older idea | already judged |", "",
        "**The cadence from 2026-11-09.** Not a check.", "", "| Idea | x |", "|---|---|", "| Not counted | x |", ""]))
    return r


def test_the_daily_section_holds_only_that_days_research_and_a_quiet_day_says_so(tmp_path):
    r = RR.build_report(repo(tmp_path), DAY, NOW, no_classification)
    t = r["today"]
    assert [x["id"] for x in t["registered"]] == ["A-1", "B-1"] and [x["id"] for x in t["verdicts"]] == ["A-1", "B-1"]
    assert [(x["heading"][:30], x["ideas"]) for x in t["dropped_before_building"]] == [
        ("Checked on 2026-11-09, 06:30 U", ["First idea", "Second idea"]),
        ("Checked on 2026-11-09, 00:30 U", [])]  # an analysis table lists no ideas
    c = r["cumulative"]
    assert c["trials"] == 5 and c["verdicts"] == 3 and c["by_verdict"] == {"FAILED": 3}
    assert c["dropped_before_building"] == 3 and c["drop_checks"] == 3 and c["drop_days"] == 2
    quiet = RR.build_report(tmp_path, date(2026, 11, 10), NOW, no_classification)
    text = RR.markdown(quiet)
    assert "Nothing new today" in text and "ما صار شي جديد" in text
    assert quiet["cumulative"] == {**c}  # the cumulative record does not depend on the day asked


def test_evidence_edited_after_its_verdict_and_a_spec_hash_missing_from_its_preregistration_are_flagged(tmp_path):
    root = repo(tmp_path)
    r = RR.build_report(root, DAY, NOW, no_classification)
    assert r["cumulative"]["evidence_changed"] == [] and r["cumulative"]["spec_not_quoted"] == ["B-1"]
    assert r["cumulative"]["evidence_checked"] == 2 == r["cumulative"]["evidence_unchanged"]
    k = root / "research" / "knowledge" / "OLD-1.json"
    body = json.loads(k.read_text())
    k.write_text(json.dumps({**body, "verdict": "PASSED"}))  # rewritten after the verdict, its old hash kept
    r = RR.build_report(root, DAY, NOW, no_classification)
    assert r["cumulative"]["evidence_changed"] == ["OLD-1"]
    text = RR.markdown(r)
    assert "**changed: OLD-1**" in text and "| OLD-1 | FAILED |" in text
    assert re.search(r"\| OLD-1 \| FAILED \|[^\n]*\*\*NO\*\* \|$", text, re.M)


def test_forward_tests_are_listed_apart_from_records_that_will_never_be_judged_here(tmp_path):
    r = RR.build_report(repo(tmp_path), DAY, NOW, no_classification)
    kinds = {p["id"]: p["kind"] for p in r["cumulative"]["pending"]}
    assert kinds == {"FWD-1": "forward", "archive-x": "archive record"}
    text = RR.markdown(r)
    forward = text.split("**Forward tests running")[1].split("## The bar")[0]
    assert "FWD-1 (registered 2026-11-01; data to 2029-12-01)" in forward
    assert "archive-x (archive record)" in forward.split("Also registered without a verdict here")[1]


def test_the_bars_count_every_test_on_each_market(tmp_path):
    r = RR.build_report(repo(tmp_path), DAY, NOW, no_classification)
    bars = r["cumulative"]["bars"]
    assert bars["equity-index-daily"]["tests"] == 3 and bars["fx-majors"]["tests"] == 1
    assert bars["equity-index-daily"]["next_bar_t"] > bars["fx-majors"]["next_bar_t"]  # more reading, a higher bar


def test_on_the_committed_record_no_evidence_has_changed_and_only_trnd1_is_validated(tmp_path):
    root = Path(RR.ROOT)
    r = RR.build_report(root, DAY, NOW)
    c = r["cumulative"]
    assert c["evidence_changed"] == [] and c["spec_not_quoted"] == [] and c["evidence_checked"] >= 50
    assert [s["edge_id"] for s in r["classification"]["standing"] if s["status"] == "VALIDATED"] == ["TRND-1"]
    assert c["bars"]["fx-majors"]["next_bar_t"] > 3.6
    text = RR.markdown(r)
    assert text.startswith("# Research pipeline report") and "RESEARCH ONLY · NO MONEY · NOT A TRADING RESULT" in text
    assert "بالعربي" in text and "TRADING_REPORT.md" in text
    for paper_word in ("equity now", "realized", "unrealized", "open exposure"):  # nothing from the paper account
        assert paper_word not in text.lower()
