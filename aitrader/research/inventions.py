"""The invention ledger: every trading mechanism proposed from first principles, written down before any of its
data is read, and kept for good whatever became of it (research/inventions.jsonl, docs/INVENTIONS.md).

An invention is admitted only with its whole argument: the economic mechanism, why it should exist, who creates it,
why competition has not removed it, when it should appear and disappear, its holding period and risk, the relation
between the mechanism and expected return, predictions that can be measured, what would refute it, the closest
known approaches and how it differs from each. A mechanism of a family that has failed is admitted only if it says
what is different this time. The ledger is append-only: a later line records a new status; nothing is rewritten.

It approves nothing. A registered invention is judged by its preregistered test, like any other hypothesis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LEDGER_VERSION = "inventions-1.0.0"
STATUSES = ("PROPOSED", "REJECTED_BEFORE_TEST", "REGISTERED", "FAILED", "INCONCLUSIVE", "PASSED", "VALIDATED")
#: the whole argument an invention must carry before it is admitted
ARGUMENT = ("definition", "mechanism", "why_exists", "participants", "why_not_competed_away", "appears_when",
            "disappears_when", "holding_and_risk", "return_relation")
LISTS = ("predictions", "refuted_if", "closest_known", "families")
#: families this registry has already judged and seen fail, with the programs that showed it
FAILED_FAMILIES = {
    "funding carry": ("CR-1", "CR-2", "CR-3", "CR-4", "CR-5", "RADAR-1 (paper)", "RADX-1"),
    "cross-sectional momentum": ("XSM-1",), "time-series momentum": ("XTS-1", "CRY-1"),
    "calendar and flow": ("MEH-1", "TME-1", "RBL-1", "TSY-1", "FOMC-1A", "PHD-1"),
    "new-listing drift": ("NEWL-1",), "forced-deleveraging rebound": ("LIQ-1",),
}


class LedgerError(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    name: str
    status: str
    at: str
    body: dict


def check(e: dict, failed: dict[str, tuple[str, ...]] | None = None) -> None:
    """Refuse an entry that is incomplete, or that belongs to a failed family without saying how it differs."""
    failed = FAILED_FAMILIES if failed is None else failed
    for k in ("name", "status", "at"):
        if not str(e.get(k, "")).strip():
            raise LedgerError(f"an invention needs its {k}")
    if e["status"] not in STATUSES:
        raise LedgerError(f"{e['name']}: unknown status {e['status']!r}")
    if e["status"] == "REJECTED_BEFORE_TEST":
        if not str(e.get("reason", "")).strip():
            raise LedgerError(f"{e['name']}: a rejection names its reason")
        return
    if e["status"] in ("REGISTERED", "FAILED", "INCONCLUSIVE", "PASSED", "VALIDATED") and not e.get("trial"):
        raise LedgerError(f"{e['name']}: a {e['status']} invention names its registered trial")
    if e["status"] != "PROPOSED" and "definition" not in e:
        return  # a status line: the argument was checked when the invention was proposed
    for k in ARGUMENT:
        if len(str(e.get(k, "")).strip()) < 20:
            raise LedgerError(f"{e['name']}: '{k}' is missing or too short to be an argument")
    for k in LISTS:
        if not isinstance(e.get(k), list) or not e[k] or not all(str(x).strip() for x in e[k]):
            raise LedgerError(f"{e['name']}: '{k}' must be a non-empty list")
    for c in e["closest_known"]:
        if not isinstance(c, dict) or not c.get("approach") or not c.get("differs_by"):
            raise LedgerError(f"{e['name']}: each closest known approach names how this differs from it")
    for fam in e["families"]:
        if fam in failed and not str(e.get("vs_failed", {}).get(fam, "")).strip():
            raise LedgerError(f"{e['name']}: the family '{fam}' failed here ({', '.join(failed[fam])}): say what is "
                              "different this time, or do not propose it")


def load(path: Path | str) -> list[Entry]:
    p = Path(path)
    out = []
    for line in p.read_text().splitlines() if p.exists() else []:
        if line.strip():
            d = json.loads(line)
            out.append(Entry(d["name"], d["status"], d["at"], d))
    return out


def current(entries: list[Entry]) -> dict[str, Entry]:
    """Each invention's latest status."""
    out: dict[str, Entry] = {}
    for e in entries:
        out[e.name] = e
    return out


def append(path: Path | str, e: dict) -> None:
    """Add a line. A new name must come with its whole argument; a known name may only move to a new status, and a
    failed or rejected invention is never proposed again under its own name."""
    entries = load(path)
    now = current(entries)
    if e["name"] in now:
        if e["status"] == "PROPOSED":
            raise LedgerError(f"{e['name']} is already in the ledger ({now[e['name']].status}): a new idea takes a new name")
        if now[e["name"]].status in ("FAILED", "REJECTED_BEFORE_TEST", "VALIDATED"):
            raise LedgerError(f"{e['name']} is closed ({now[e['name']].status}): its record stays as it is")
    elif e["status"] not in ("PROPOSED", "REJECTED_BEFORE_TEST"):
        raise LedgerError(f"{e['name']} must be proposed, with its argument, before it can be {e['status']}")
    check(e)
    with Path(path).open("a") as f:
        f.write(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n")


def report(entries: list[Entry]) -> str:
    """The ledger as a page: every invention, its latest status, and its reason or trial."""
    now = current(entries)
    first = {}
    for e in entries:
        first.setdefault(e.name, e)
    lines = ["| Invention | Status | Families | Trial or reason |", "|---|---|---|---|"]
    for name in sorted(now, key=lambda n: first[n].at):
        e = now[name]
        why = e.body.get("trial") or e.body.get("reason") or first[name].body.get("trial") or ""
        fams = ", ".join(first[name].body.get("families", []))
        lines.append(f"| {name} | {e.status} | {fams} | {str(why).replace('|', '/')} |")
    return "\n".join(lines) + "\n"
