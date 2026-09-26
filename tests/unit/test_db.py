"""Persistence: immutable history, hash chain, restart survival, switches."""

from __future__ import annotations

import sqlite3

import pytest

from aitrader.memory.db import IMMUTABLE, Database


def test_history_survives_a_restart(tmp_path):
    db = Database(tmp_path / "s.db")
    db.append("episodes", {"decision_id": "d1", "kind": "TRADE", "symbol": "EURUSD", "payload": {"r": -1.0}})
    db.set_kv("paused", True, reason="test")
    del db
    again = Database(tmp_path / "s.db")
    assert again.one("SELECT kind FROM episodes WHERE decision_id='d1'")["kind"] == "TRADE"
    assert again.get_kv("paused") is True


@pytest.mark.parametrize("table", ["episodes", "decisions", "trades", "lessons", "events"])
def test_history_cannot_be_rewritten_or_deleted(tmp_path, table):
    db = Database(tmp_path / "s.db")
    rows = {
        "episodes": {"decision_id": "d", "kind": "TRADE", "symbol": "X", "payload": {}},
        "decisions": {"symbol": "X", "timeframe": "H1", "decision": "BUY", "mode": "PAPER", "payload": {}},
        "trades": {"position_id": "p", "decision_id": "d", "symbol": "X", "payload": {}},
        "lessons": {"lesson_id": "L1", "version": 1, "status": "CANDIDATE", "payload": {}},
        "events": {"type": "X", "payload": {}},
    }
    row = db.append(table, rows[table])
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        with db.tx() as c:
            c.execute(f"UPDATE {table} SET ts = 0 WHERE id = ?", (row["id"],))
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        with db.tx() as c:
            c.execute(f"DELETE FROM {table} WHERE id = ?", (row["id"],))


def test_every_immutable_table_has_both_triggers(tmp_path):
    db = Database(tmp_path / "s.db")
    names = {r["name"] for r in db.query("SELECT name FROM sqlite_master WHERE type='trigger'")}
    for t in IMMUTABLE:
        assert f"immutable_{t}_update" in names and f"immutable_{t}_delete" in names


def test_the_hash_chain_detects_an_edit_that_bypasses_the_triggers(tmp_path):
    db = Database(tmp_path / "s.db")
    for i in range(5):
        db.append("episodes", {"decision_id": f"d{i}", "kind": "TRADE", "symbol": "X", "payload": {"r": i}})
    assert db.verify_chain("episodes")[0]
    with db.tx() as c:  # an attacker who drops the trigger first
        c.execute("DROP TRIGGER immutable_episodes_update")
        c.execute("UPDATE episodes SET payload = '{\"r\":99}' WHERE decision_id = 'd2'")
    ok, msg = db.verify_chain("episodes")
    assert not ok and "chain broken" in msg


def test_a_lesson_changes_only_by_a_new_version(tmp_path):
    db = Database(tmp_path / "s.db")
    db.append("lessons", {"lesson_id": "L1", "version": 1, "status": "CANDIDATE", "payload": {}})
    db.append("lessons", {"lesson_id": "L1", "version": 2, "status": "VALIDATED", "payload": {}})
    with pytest.raises(sqlite3.IntegrityError):
        db.append("lessons", {"lesson_id": "L1", "version": 2, "status": "REJECTED", "payload": {}})
    rows = db.query("SELECT version, status FROM lessons WHERE lesson_id='L1' ORDER BY version")
    assert [(r["version"], r["status"]) for r in rows] == [(1, "CANDIDATE"), (2, "VALIDATED")]


def test_a_failed_transaction_leaves_nothing_behind(tmp_path):
    db = Database(tmp_path / "s.db")
    with pytest.raises(RuntimeError):
        with db.tx() as c:
            db.append("events", {"type": "A", "payload": {}}, conn=c)
            raise RuntimeError("crash mid-write")
    assert db.query("SELECT COUNT(*) AS n FROM events")[0]["n"] == 0


def test_switch_changes_are_journaled(tmp_path):
    db = Database(tmp_path / "s.db")
    db.set_kv("kill_switch", {"active": True}, reason="operator")
    ev = db.one("SELECT * FROM events WHERE type='STATE_CHANGED'")
    assert Database.loads(ev)["reason"] == "operator"
