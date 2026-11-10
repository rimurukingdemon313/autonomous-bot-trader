"""The lab's persistent memory: append-only tables in one directory, carried between runs on the lab-data branch.

    queue       every task's events (QUEUED, STARTED, DONE, FAILED); a task's state is the fold of its events
    runs        one line for each step of each cycle: the checkpoint log
    sources     the research-source database: papers and other sources, each with its link, date and status
    hypotheses  the hypothesis memory: every idea, where it came from (its parents), and what became of it
    forward     the paper-forward record of rules that passed validation
    alerts      what the owner must be told, and whether it has been sent
    budget      what each cycle spent: seconds, tasks, model calls

Nothing is ever rewritten. A table is a file of JSON lines, so a crash can lose at most the line being written, and a
person can read every table with a text editor. Each run starts on a fresh machine and restores this directory first:
every run is a restart.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

TABLES = ("queue", "runs", "sources", "hypotheses", "forward", "alerts", "budget")
MAX_ATTEMPTS = 3
STALE_HOURS = 6  # a task STARTED this long ago with no DONE or FAILED after it died with its machine


class Store:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, table: str) -> Path:
        if table not in TABLES:
            raise ValueError(f"unknown table {table!r}")
        return self.root / f"{table}.jsonl"

    def read(self, table: str) -> list[dict]:
        p = self.path(table)
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []

    def append(self, table: str, rows: list[dict]) -> int:
        if rows:
            with open(self.path(table), "a") as f:
                f.write("".join(json.dumps(r, sort_keys=True, default=str) + "\n" for r in rows))
                f.flush()
        return len(rows)

    def search(self, text: str, tables: tuple = ("sources", "hypotheses")) -> list[dict]:
        """Every row of the given tables that holds all of the words, in any field, in any letter case."""
        words = [w for w in text.lower().split() if w]
        out = []
        for t in tables:
            for r in self.read(t):
                blob = json.dumps(r, ensure_ascii=False).lower()
                if all(w in blob for w in words):
                    out.append({"table": t, **r})
        return out


# ── the task queue ──────────────────────────────────────────────────────────

def tasks(store: Store) -> dict[str, dict]:
    """Each task's present state, folded from its events in order."""
    out: dict[str, dict] = {}
    for e in store.read("queue"):
        t = out.setdefault(e["task"], {"task": e["task"], "kind": e.get("kind"), "args": e.get("args") or {},
                                       "priority": 0.0, "status": None, "attempts": 0, "at": None, "result": None})
        if e["event"] == "QUEUED":
            t.update(kind=e["kind"], args=e.get("args") or {}, priority=e.get("priority", 0.0))
        elif e["event"] == "PRIORITY":
            t["priority"] = e["priority"]
            continue
        elif e["event"] == "STARTED":
            t["attempts"] += 1
        t["status"], t["at"] = e["event"], e["at"]
        if e["event"] in ("DONE", "FAILED"):
            t["result"] = e.get("result")
    return out


def enqueue(store: Store, task: str, kind: str, args: dict, priority: float, now: datetime) -> bool:
    """Queue a task once. A task is known by its id, so the same experiment is never queued, or run, twice."""
    if task in tasks(store):
        return False
    store.append("queue", [{"task": task, "kind": kind, "args": args, "priority": priority, "event": "QUEUED",
                            "at": now.isoformat()}])
    return True


def mark(store: Store, task: str, event: str, now: datetime, result: object = None) -> None:
    if event not in ("STARTED", "DONE", "FAILED"):
        raise ValueError(event)
    store.append("queue", [{"task": task, "event": event, "at": now.isoformat(), "result": result}])


def reprioritize(store: Store, priorities: dict[str, float], now: datetime) -> None:
    cur = tasks(store)
    store.append("queue", [{"task": t, "event": "PRIORITY", "priority": round(p, 4), "at": now.isoformat()}
                           for t, p in sorted(priorities.items())
                           if t in cur and cur[t]["status"] != "DONE" and abs(cur[t]["priority"] - p) > 1e-9])


def runnable(store: Store, now: datetime) -> list[dict]:
    """The tasks a cycle may take, the most valuable first: queued ones; failed ones with attempts left; and ones
    whose run died (STARTED long ago, nothing since)."""
    out = []
    for t in tasks(store).values():
        if t["status"] == "QUEUED":
            out.append(t)
        elif t["status"] == "FAILED" and t["attempts"] < MAX_ATTEMPTS:
            out.append(t)
        elif t["status"] == "STARTED" and now - datetime.fromisoformat(t["at"]) >= timedelta(hours=STALE_HOURS) \
                and t["attempts"] < MAX_ATTEMPTS:
            out.append(t)
    return sorted(out, key=lambda t: (-t["priority"], t["task"]))


def abandoned(store: Store) -> list[dict]:
    """Tasks that failed, or died, on every attempt they were allowed: they need a person, and are reported."""
    return [t for t in tasks(store).values() if t["status"] in ("FAILED", "STARTED") and t["attempts"] >= MAX_ATTEMPTS]


__all__ = ["MAX_ATTEMPTS", "STALE_HOURS", "Store", "TABLES", "abandoned", "enqueue", "mark", "reprioritize", "runnable",
           "tasks"]
