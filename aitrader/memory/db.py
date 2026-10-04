"""Persistent state: every memory layer, the journal, and execution state.

SQLite in WAL mode, on a persistent volume in production. Chosen over a
server database because the system is a single process (a modular monolith),
the data is small, and one file on a Railway volume survives restarts and
redeploys with no extra service to keep healthy. A second database engine
is added only when there is a measured reason (ENGINEERING_RULES.md).

IMMUTABLE HISTORY. Historical records — events, decisions, agent reports,
risk verdicts, trades, episodes, post-mortems, reflections, lesson versions,
knowledge versions, experiment registrations and verdicts — cannot be
changed after they are written:

1. database triggers refuse UPDATE and DELETE on those tables;
2. each row carries a SHA-256 chained to the previous row of its table, so
   an edit made by going around the triggers is detected by `verify_chain`.

What IS mutable is operational state that is not history: an order intent's
status, an open position, the paper account, and switches (pause, kill).
Every change to those is also written to the immutable event log.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 3  # 2: evaluations (shadow outcomes, for restart); 3: forward ledger and forward lessons

IMMUTABLE = (
    "events", "decisions", "agent_reports", "risk_verdicts", "trades", "episodes",
    "postmortems", "reflections", "lessons", "knowledge_versions", "experiments",
    "experiment_verdicts", "performance_snapshots", "evaluations",
    "forward_proposals", "forward_outcomes", "forward_lessons",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated REAL NOT NULL);

CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  type TEXT NOT NULL, ref TEXT, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type, seq);
CREATE INDEX IF NOT EXISTS idx_events_ref ON events(ref);

CREATE TABLE IF NOT EXISTS decisions (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  symbol TEXT NOT NULL, timeframe TEXT NOT NULL, decision TEXT NOT NULL, mode TEXT NOT NULL,
  payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol, ts);

CREATE TABLE IF NOT EXISTS agent_reports (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  decision_id TEXT NOT NULL, agent TEXT NOT NULL, payload TEXT NOT NULL,
  prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_reports_decision ON agent_reports(decision_id);

CREATE TABLE IF NOT EXISTS risk_verdicts (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  decision_id TEXT UNIQUE NOT NULL, approved INTEGER NOT NULL, payload TEXT NOT NULL,
  prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS intents (
  id TEXT PRIMARY KEY, decision_id TEXT UNIQUE NOT NULL, ts REAL NOT NULL, symbol TEXT NOT NULL,
  side TEXT NOT NULL, status TEXT NOT NULL, broker_order_id TEXT, payload TEXT NOT NULL, updated REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);

CREATE TABLE IF NOT EXISTS positions (
  id TEXT PRIMARY KEY, intent_id TEXT UNIQUE NOT NULL, decision_id TEXT NOT NULL, symbol TEXT NOT NULL,
  side TEXT NOT NULL, qty REAL NOT NULL, entry REAL NOT NULL, stop REAL NOT NULL, target REAL,
  opened REAL NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, updated REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);

CREATE TABLE IF NOT EXISTS trades (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  position_id TEXT UNIQUE NOT NULL, decision_id TEXT NOT NULL, symbol TEXT NOT NULL,
  r REAL, pnl REAL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS episodes (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  decision_id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, symbol TEXT NOT NULL,
  payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_episodes_kind ON episodes(kind, ts);

CREATE TABLE IF NOT EXISTS postmortems (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  episode_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS reflections (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS lessons (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  lesson_id TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL,
  prev_hash TEXT NOT NULL, hash TEXT NOT NULL, UNIQUE (lesson_id, version));

CREATE TABLE IF NOT EXISTS knowledge_versions (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  version INTEGER UNIQUE NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS experiments (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  signature TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS experiment_verdicts (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  experiment_id TEXT UNIQUE NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL,
  prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS performance_snapshots (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS evaluations (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  decision_id TEXT NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS forward_proposals (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  decision_id TEXT UNIQUE NOT NULL, symbol TEXT NOT NULL, t INTEGER NOT NULL, partition TEXT NOT NULL,
  payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS forward_outcomes (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  decision_id TEXT UNIQUE NOT NULL, resolved_at INTEGER NOT NULL, partition TEXT NOT NULL,
  payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS forward_lessons (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, ts REAL NOT NULL,
  lesson_id TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL,
  prev_hash TEXT NOT NULL, hash TEXT NOT NULL, UNIQUE (lesson_id, version));

CREATE TABLE IF NOT EXISTS paper_account (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated REAL NOT NULL);
"""


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_default)


def _default(o: Any):
    if hasattr(o, "as_dict"):
        return o.as_dict()
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(f"not serialisable: {type(o).__name__}")


def _hash(prev: str, row: dict) -> str:
    return hashlib.sha256((prev + _canonical(row)).encode()).hexdigest()


class ImmutableViolation(RuntimeError):
    pass


class Database:
    """Thread-safe SQLite access. One writer at a time; readers never block writers (WAL)."""

    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None, timeout=30)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            if self.path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(_SCHEMA)
            for table in IMMUTABLE:
                for op in ("UPDATE", "DELETE"):
                    self._conn.execute(
                        f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{op.lower()} BEFORE {op} ON {table} "
                        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable history'); END")
            self._conn.execute("INSERT INTO meta(key, value) VALUES ('schema_version', ?) ON CONFLICT(key) "
                               "DO UPDATE SET value=excluded.value WHERE CAST(value AS INTEGER) < CAST(excluded.value AS INTEGER)",
                               (str(SCHEMA_VERSION),))

    # ── low level ───────────────────────────────────────────────────────

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise

    def query(self, sql: str, args: tuple = ()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args).fetchall()]

    def one(self, sql: str, args: tuple = ()) -> dict | None:
        rows = self.query(sql, args)
        return rows[0] if rows else None

    def ping(self) -> float:
        t = time.perf_counter()
        self.query("SELECT 1")
        return time.perf_counter() - t

    # ── append-only history ─────────────────────────────────────────────

    def append(self, table: str, row: dict, conn: sqlite3.Connection | None = None) -> dict:
        """Insert into an immutable table with its hash-chain link."""
        if table not in IMMUTABLE:
            raise ValueError(f"{table} is not an append-only table")
        row = dict(row)
        row.setdefault("id", uuid.uuid4().hex)
        row.setdefault("ts", time.time())
        if isinstance(row.get("payload"), (dict, list)):
            row["payload"] = _canonical(row["payload"])

        def _do(c: sqlite3.Connection) -> dict:
            last = c.execute(f"SELECT hash FROM {table} ORDER BY seq DESC LIMIT 1").fetchone()
            prev = last[0] if last else "genesis"
            body = {k: v for k, v in row.items() if k not in ("prev_hash", "hash", "seq")}
            row["prev_hash"] = prev
            row["hash"] = _hash(prev, body)
            cols = ", ".join(row)
            c.execute(f"INSERT INTO {table} ({cols}) VALUES ({', '.join('?' * len(row))})", tuple(row.values()))
            return row

        if conn is not None:
            return _do(conn)
        with self.tx() as c:
            return _do(c)

    def verify_chain(self, table: str) -> tuple[bool, str]:
        rows = self.query(f"SELECT * FROM {table} ORDER BY seq")
        prev = "genesis"
        for r in rows:
            body = {k: v for k, v in r.items() if k not in ("prev_hash", "hash", "seq")}
            if r["prev_hash"] != prev or r["hash"] != _hash(prev, body):
                return False, f"{table}: chain broken at seq {r['seq']} (id {r['id']})"
            prev = r["hash"]
        return True, f"{table}: {len(rows)} rows verified"

    def event(self, type_: str, payload: dict, ref: str | None = None,
              conn: sqlite3.Connection | None = None) -> dict:
        return self.append("events", {"type": type_, "ref": ref, "payload": payload}, conn)

    # ── operational switches (mutable, every change journaled) ──────────

    def set_kv(self, key: str, value: Any, *, reason: str = "") -> None:
        with self.tx() as c:
            c.execute("INSERT INTO kv(key, value, updated) VALUES (?, ?, ?) "
                      "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
                      (key, _canonical(value), time.time()))
            self.event("STATE_CHANGED", {"key": key, "value": value, "reason": reason}, ref=key, conn=c)

    def get_kv(self, key: str, default: Any = None) -> Any:
        row = self.one("SELECT value FROM kv WHERE key=?", (key,))
        return json.loads(row["value"]) if row else default

    @staticmethod
    def loads(row: dict | None, field: str = "payload") -> Any:
        if row is None:
            return None
        return json.loads(row[field]) if isinstance(row.get(field), str) else row.get(field)
