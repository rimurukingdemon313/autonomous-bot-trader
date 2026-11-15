"""One performance cycle end to end (scripts/perf_cycle.py) on built inputs, and the limits of its workflow: it reads
the paper systems and can write to neither."""

from __future__ import annotations

import csv
import gzip
import io
import json
import re
import sqlite3
from pathlib import Path

import pytest

import scripts.perf_cycle as C
from aitrader.memory.db import Database
from aitrader.perf import radar, replay
from aitrader.radar import core as R
from tests.unit.test_perf_audit import COLS, RF, as_ledger, desk, many, radar_book

ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-11-18T12:00:00+00:00"


def inputs(tmp_path, hours=260):
    """The two systems' published files as the workflow hands them over, and the radar's cached state."""
    led, eq, st = desk()
    t = tmp_path / "trend"
    t.mkdir()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS)
    w.writeheader()
    w.writerows(led)
    (t / "ledger.csv").write_text(buf.getvalue())
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(eq[0]))
    w.writeheader()
    w.writerows(eq)
    (t / "equity.csv").write_text(buf.getvalue())
    (t / "state.json").write_text(json.dumps(st))
    db = Database(tmp_path / "desk.db")
    for e in eq:
        db.event("DESK_INTRADAY_LOW", {"day": e["day"], "equity": float(e["equity"]) - 50.0})
        db.event("DESK_EQUITY", {"day": e["day"], "equity": float(e["equity"])})
    con = sqlite3.connect(tmp_path / "desk.db")
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # the desk publishes its database after its writes are in the file
    con.close()
    (t / "desk.db.gz").write_bytes(gzip.compress((tmp_path / "desk.db").read_bytes()))
    r = tmp_path / "radar"
    r.mkdir()
    s = radar_book(hours)
    (r / "ledger.json").write_text(json.dumps(as_ledger(s)))
    (r / "REPORT.md").write_text("## Performance\n\n" + "\n".join(f"- {k}: {v}" for k, v in R.performance(s, R.Rules(), RF).items()) + "\n")
    c = tmp_path / "radar-state"
    c.mkdir()
    (c / "state.json.gz").write_bytes(gzip.compress(json.dumps(s.to_json()).encode()))
    return ["--trend", str(t), "--radar", str(r), "--radar-state", str(c), "--out", str(tmp_path / "pub"),
            "--challengers", str(tmp_path / "challengers.json"), "--now", NOW]


def test_a_cycle_reconciles_both_accounts_archives_the_quotes_replays_and_reports(tmp_path, capsys):
    args = inputs(tmp_path)
    assert C.main(args) == 0
    pub = tmp_path / "pub"
    for f in ("PERF_REPORT.md", "paper_audit.json", "replay.json", "cycles.jsonl", "quotes/manifest.json", "books/original.json.gz", "books/all-three.json.gz"):
        assert (pub / f).exists(), f
    audit = json.loads((pub / "paper_audit.json").read_text())
    assert audit["trend"]["reconciled"] and audit["radar"]["reconciled"]
    assert audit["trend"]["figures"]["realized_net"] == 480.0 and audit["trend"]["figures"]["unrealized"] == -20.0
    assert audit["trend"]["figures"]["max_drawdown_inside_a_day"]["value"] == 450.0  # the day's low, 50 under its close
    rep = json.loads((pub / "replay.json").read_text())
    assert rep["archive"]["added"] and not rep["problems"] and rep["replayed_this_cycle"]
    assert set(rep["validation"]["variants"]) == set(replay.VARIANTS) and rep["validation"]["status"] == "INCONCLUSIVE"
    assert rep["fidelity"]["trustworthy"] and rep["challengers"] == []
    book = json.loads(gzip.decompress((pub / "books" / "original.json.gz").read_bytes()))
    assert set(book) == {"open", "closed", "marks", "runs"} and book["marks"][0]["t"] == rep["validation"]["start"]
    text = (pub / "PERF_REPORT.md").read_text()
    assert "PROBLEMS THIS CYCLE" not in text and text.count("**Reconciled:") == 2
    assert "| **Realized** P&L (closed trades, after every cost) | +$480.00 from +$500.00 gross |" in text
    assert "| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | -$20.00 |" in text
    assert "None is registered." in text and "بالعربي" in text
    line = json.loads((pub / "cycles.jsonl").read_text().splitlines()[0])
    assert line["trend"]["reconciled"] and line["radar"]["reconciled"] and line["experiment"]["status"] == "INCONCLUSIVE"
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["cycle"] == 1


def test_a_second_cycle_on_the_same_hours_reuses_the_replay_and_rewrites_no_archived_day(tmp_path):
    args = inputs(tmp_path)
    assert C.main(args) == 0
    pub = tmp_path / "pub"
    first = json.loads((pub / "replay.json").read_text())
    days = {f.name: f.read_bytes() for f in (pub / "quotes").glob("*.gz")}
    assert C.main(args) == 0
    second = json.loads((pub / "replay.json").read_text())
    assert not second["replayed_this_cycle"] and second["validation"] == first["validation"] and second["archive"]["added"] == []
    assert {f.name: f.read_bytes() for f in (pub / "quotes").glob("*.gz")} == days
    assert len((pub / "cycles.jsonl").read_text().splitlines()) == 2
    assert "cycles so far: 2" in (pub / "PERF_REPORT.md").read_text()


def test_an_account_that_does_not_reconcile_is_published_and_the_run_fails(tmp_path):
    args = inputs(tmp_path)
    eq = tmp_path / "trend" / "equity.csv"
    eq.write_text(eq.read_text().replace("200460.0,200480.0", "200999.0,200480.0"))
    assert C.main(args) == 1
    text = (tmp_path / "pub" / "PERF_REPORT.md").read_text()
    assert "## PROBLEMS THIS CYCLE" in text and "TRND-1: in every session, equity is balance plus open P&L" in text
    assert "**NOT RECONCILED:" in text and (tmp_path / "pub" / "paper_audit.json").exists()
    assert json.loads((tmp_path / "pub" / "cycles.jsonl").read_text().splitlines()[0])["trend"]["reconciled"] is False


def test_without_the_radars_stored_quotes_nothing_is_replayed_and_nothing_is_invented(tmp_path):
    args = inputs(tmp_path)
    (tmp_path / "radar-state" / "state.json.gz").unlink()
    assert C.main(args) == 0
    rep = json.loads((tmp_path / "pub" / "replay.json").read_text())
    assert rep["validation"]["status"] == "NOT ENOUGH HOURS" and rep["hours"] == 0 and "not available" in rep["archive"]["note"]
    assert not (tmp_path / "pub" / "books").exists() and "NOT ENOUGH HOURS" in (tmp_path / "pub" / "PERF_REPORT.md").read_text()


def test_a_database_that_cannot_be_read_is_a_failed_check_never_a_pass(tmp_path):
    args = inputs(tmp_path)
    (tmp_path / "trend" / "desk.db.gz").write_bytes(gzip.compress(b"not a database"))
    assert C.main(args) == 1
    text = (tmp_path / "pub" / "PERF_REPORT.md").read_text()
    assert "the database could not be read" in text and "**NOT RECONCILED:" in text


def test_a_missing_system_is_a_problem_not_a_silent_gap(tmp_path):
    args = inputs(tmp_path)
    (tmp_path / "radar" / "ledger.json").unlink()
    assert C.main(args) == 1
    assert "RADAR-1: its files were not available" in (tmp_path / "pub" / "PERF_REPORT.md").read_text()


def test_a_registered_challenger_is_stepped_beside_the_original_and_waits_for_its_look(tmp_path):
    args = inputs(tmp_path)
    t0 = 1_794_009_600 + 150 * 3600
    (tmp_path / "challengers.json").write_text(json.dumps([{"id": "RADAR-C-TEST", "variant": "thick-entry", "registered_t": t0, "look_days": 60}]))
    assert C.main(args) == 0
    rep = json.loads((tmp_path / "pub" / "replay.json").read_text())
    (c,) = rep["challengers"]
    assert c["status"] == "WAIT" and c["registered_t"] == t0 and c["look_t"] == t0 + 60 * 86400
    assert not list((tmp_path / "pub").glob("challenger-*")) and "`RADAR-C-TEST` (`thick-entry`)" in (tmp_path / "pub" / "PERF_REPORT.md").read_text()


def test_the_hypothesis_follows_the_weakness_through_a_declared_variant_or_says_there_is_none():
    led, _ = many()
    a = radar.audit(led, rf_apr=RF)
    h = C.hypothesis(a, {"validation": {"variants": {"thick-entry": {"earlier": {"x": 1}, "later": {"x": 2}, "against_original_later": {"t": None}}}}})
    assert h["weakness"]["class"] == "under 50%/yr" and h["variant"] == "thick-entry" and h["replay"]["later"] == {"x": 2}
    assert all(v in replay.VARIANTS for v, _ in C.LEVERS.values())
    a["attribution"]["largest_weakness"] = {**a["attribution"]["largest_weakness"], "dimension": "venue pair", "class": "short mexc / long gate"}
    h = C.hypothesis(a, {})
    assert h["variant"] is None and "director" in h["why"]
    a["attribution"]["largest_weakness"] = None
    assert C.hypothesis(a, {})["weakness"] is None and C.hypothesis(None, {})["weakness"] is None


# ── the workflow cannot touch what it reads ─────────────────────────────────

WF = (ROOT / ".github" / "workflows" / "perf-cycle.yml").read_text()


def test_the_workflow_restores_the_radars_cache_and_never_saves_one():
    assert "actions/cache/restore@v4" in WF and "restore-keys: radar-state-" in WF
    assert "actions/cache/save" not in WF and not re.search(r"uses:\s*actions/cache@", WF)
    # the same path the radar saves under: a different path would restore nothing
    radar_wf = (ROOT / ".github" / "workflows" / "radar.yml").read_text()
    assert "path: radar-state" in WF and "path: radar-state" in radar_wf


def test_the_workflow_pushes_to_perf_data_and_nowhere_else():
    pushes = re.findall(r"git push[^\n]*", WF)
    assert pushes and all("HEAD:refs/heads/perf-data" in p for p in pushes)
    assert "workflows/radar.yml" not in WF and "trend-desk.yml" not in WF and "dispatches" not in WF
    for branch in ("trend-desk-data", "radar-data"):
        assert not re.search(rf"push[^\n]*{branch}", WF)


def test_the_workflow_runs_on_a_schedule_and_fails_visibly():
    assert re.search(r'schedule:\s*\n(\s*#[^\n]*\n)*\s*- cron: "23 \*/3 \* \* \*"', WF)
    assert "scripts/perf_cycle.py --trend in/trend-desk-data --radar in/radar-data --radar-state radar-state --out pub" in WF
    assert "if: always()" in WF and 'if [ "$code" != "0" ]' in WF


def test_the_cycle_script_imports_no_broker_and_no_order_path():
    src = (ROOT / "scripts" / "perf_cycle.py").read_text() + "".join(
        (ROOT / "aitrader" / "perf" / f).read_text() for f in ("trend.py", "radar.py", "replay.py", "radx.py", "stats.py"))
    for banned in ("aitrader.broker", "aitrader.execution", "place_market_order", "close_position", "modify_position", "requests.", "urllib"):
        assert banned not in src, banned


@pytest.mark.parametrize("name", sorted(replay.VARIANTS))
def test_every_declared_variant_is_a_valid_set_of_the_radars_own_parameters(name):
    assert isinstance(replay.rules(name), R.Rules)
