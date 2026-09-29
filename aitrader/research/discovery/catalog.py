"""The feature catalog: every candidate feature, where it came from, and what it was used for.

Append-only JSON lines (research/discovery/features.jsonl). A feature is known by
`<name>@<version>`; changing its definition means a new version, so an old result can never
silently describe new code. Each line is one event:

    BUDGET         a program declares how many features it may introduce, once
    REGISTERED     the full record: definition, timeframe, required data, provenance, version,
                   point-in-time rule, the question it is meant to answer, the program
    LEAKAGE_CHECK  the truncation test: recomputed with every input cut at the decision bar,
                   on the rows and symbols listed; PASSED or FAILED with the offending rows
    USED           an experiment (registry trial id) used it; refused unless leakage PASSED
    RESULT         what that experiment found about it

Nothing is edited or deleted, so a feature that failed or was never useful stays searchable.
The budget exists because every feature is another degree of freedom a search can overfit
with; a program that wants more must say so up front, where the multiple-testing count sees it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import numpy as np

from ...data.bars import BarSeries

CATALOG_VERSION = "catalog-1.0.0"
EVENTS = ("BUDGET", "REGISTERED", "LEAKAGE_CHECK", "USED", "RESULT")
REQUIRED = ("name", "definition", "dimension", "kind", "timeframe", "provenance", "version", "point_in_time",
            "hypothesis", "program")


class CatalogError(ValueError):
    """The catalog refused a write that would corrupt the record."""


class BudgetExceeded(CatalogError):
    pass


class LeakyFeature(CatalogError):
    pass


@dataclass(frozen=True)
class FeatureRecord:
    name: str
    definition: str
    dimension: str
    kind: str  # continuous | categorical
    timeframe: str
    requires: tuple[str, ...]
    provenance: str  # where the definition lives: module and version
    version: str
    point_in_time: str  # when a value becomes known, stated
    hypothesis: str  # the question it is meant to answer, not a claim that it does
    program: str  # the research program whose budget it counts against

    @property
    def id(self) -> str:
        return f"{self.name}@{self.version}"

    def definition_hash(self) -> str:
        body = json.dumps([self.name, self.definition, self.kind, self.timeframe, list(self.requires),
                           self.version], sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()[:16]

    def validate(self) -> None:
        for f in REQUIRED:
            if not str(getattr(self, f) or "").strip():
                raise CatalogError(f"feature record needs {f!r}")
        if self.kind not in ("continuous", "categorical"):
            raise CatalogError(f"{self.name}: kind must be continuous or categorical")
        if not self.requires:
            raise CatalogError(f"{self.name}: required data must be declared")

    def to_json(self) -> dict:
        d = asdict(self)
        d["requires"] = list(self.requires)
        d["id"] = self.id
        d["definition_hash"] = self.definition_hash()
        return d

    @classmethod
    def from_json(cls, raw: dict) -> "FeatureRecord":
        return cls(**{k: (tuple(raw[k]) if k == "requires" else raw[k]) for k in (
            "name", "definition", "dimension", "kind", "timeframe", "requires", "provenance", "version",
            "point_in_time", "hypothesis", "program")})


class FeatureCatalog:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._budgets: dict[str, int] = {}
        self._records: dict[str, FeatureRecord] = {}
        self._registered_at: dict[str, str] = {}
        self._leakage: dict[str, dict] = {}
        self._used: dict[str, list[str]] = {}
        self._results: dict[str, list[dict]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._apply(json.loads(line))

    # ── writes ──────────────────────────────────────────────────────────

    def open_program(self, program: str, budget: int, now: datetime) -> None:
        if program in self._budgets:
            raise CatalogError(f"{program} already declared a feature budget ({self._budgets[program]}); "
                               "a budget is set once, before any feature is registered")
        if budget < 1:
            raise CatalogError("a feature budget must be at least 1")
        self._write({"event": "BUDGET", "program": program, "budget": int(budget), "at": now.isoformat()})

    def register(self, record: FeatureRecord, now: datetime) -> FeatureRecord:
        record.validate()
        existing = self._records.get(record.id)
        if existing is not None:
            if existing.definition_hash() != record.definition_hash():
                raise CatalogError(f"{record.id} is already registered with a different definition; "
                                   "bump the version instead of editing a registered feature")
            return existing
        if record.program not in self._budgets:
            raise CatalogError(f"{record.program} has not declared a feature budget")
        used = sum(1 for r in self._records.values() if r.program == record.program)
        if used >= self._budgets[record.program]:
            raise BudgetExceeded(f"{record.program} has used its budget of {self._budgets[record.program]} "
                                 f"features; {record.id} is refused")
        self._write({"event": "REGISTERED", "at": now.isoformat(), "record": record.to_json()})
        return record

    def record_leakage(self, feature_id: str, bad_rows: list[int], rows_checked: int, symbols: list[str],
                       now: datetime) -> str:
        self.get(feature_id)
        if rows_checked < 1:
            raise CatalogError("a leakage check that checked no rows is not a check")
        status = "FAILED" if bad_rows else "PASSED"
        self._write({"event": "LEAKAGE_CHECK", "id": feature_id, "status": status, "rows_checked": int(rows_checked),
                     "symbols": list(symbols), "bad_rows": [int(i) for i in bad_rows[:20]], "at": now.isoformat()})
        return status

    def mark_used(self, feature_id: str, experiment: str, now: datetime) -> None:
        self.get(feature_id)
        status = self.leakage_status(feature_id)
        if status != "PASSED":
            raise LeakyFeature(f"{feature_id} has leakage status {status}; only a feature that passed the "
                               "truncation test may be used by an experiment")
        if experiment in self._used.get(feature_id, []):
            return
        self._write({"event": "USED", "id": feature_id, "experiment": experiment, "at": now.isoformat()})

    def record_result(self, feature_id: str, experiment: str, result: dict, now: datetime) -> None:
        if experiment not in self._used.get(feature_id, []):
            raise CatalogError(f"{experiment} did not declare use of {feature_id}")
        self._write({"event": "RESULT", "id": feature_id, "experiment": experiment, "result": result,
                     "at": now.isoformat()})

    # ── reads ───────────────────────────────────────────────────────────

    def get(self, feature_id: str) -> FeatureRecord:
        try:
            return self._records[feature_id]
        except KeyError:
            raise CatalogError(f"unknown feature {feature_id!r}") from None

    def records(self) -> tuple[FeatureRecord, ...]:
        return tuple(self._records.values())

    def budget(self, program: str) -> tuple[int, int]:
        """(used, allowed) for a program."""
        return (sum(1 for r in self._records.values() if r.program == program), self._budgets.get(program, 0))

    def leakage_status(self, feature_id: str) -> str:
        return self._leakage.get(feature_id, {}).get("status", "UNCHECKED")

    def experiments(self, feature_id: str) -> list[str]:
        return list(self._used.get(feature_id, []))

    def results(self, feature_id: str) -> list[dict]:
        return list(self._results.get(feature_id, []))

    def entry(self, feature_id: str) -> dict:
        """Everything known about one feature, for reports and the CLI."""
        r = self.get(feature_id)
        return r.to_json() | {"registered": self._registered_at[feature_id],
                              "leakage": self._leakage.get(feature_id, {"status": "UNCHECKED"}),
                              "experiments": self.experiments(feature_id), "results": self.results(feature_id)}

    def search(self, text: str = "", leakage: str | None = None) -> list[dict]:
        t = text.lower()
        out = []
        for fid, r in self._records.items():
            blob = " ".join([fid, r.definition, r.dimension, r.hypothesis, r.provenance]).lower()
            if t in blob and (leakage is None or self.leakage_status(fid) == leakage):
                out.append(self.entry(fid))
        return out

    # ── internals ───────────────────────────────────────────────────────

    def _write(self, event: dict) -> None:
        self._apply(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")

    def _apply(self, e: dict) -> None:
        kind = e.get("event")
        if kind not in EVENTS:
            raise CatalogError(f"unknown catalog event {kind!r}")
        if kind == "BUDGET":
            self._budgets[e["program"]] = int(e["budget"])
        elif kind == "REGISTERED":
            rec = FeatureRecord.from_json(e["record"])
            if rec.definition_hash() != e["record"].get("definition_hash"):
                raise CatalogError(f"{rec.id}: stored definition hash does not match its definition")
            self._records[rec.id] = rec
            self._registered_at[rec.id] = e["at"]
        elif kind == "LEAKAGE_CHECK":
            self._leakage[e["id"]] = {k: e[k] for k in ("status", "rows_checked", "symbols", "bad_rows", "at")}
        elif kind == "USED":
            self._used.setdefault(e["id"], []).append(e["experiment"])
        else:
            self._results.setdefault(e["id"], []).append({"experiment": e["experiment"], "result": e["result"],
                                                         "at": e["at"]})


# ── the truncation test ────────────────────────────────────────────────


ColumnFn = Callable[[BarSeries, dict], np.ndarray]


def truncated(others: dict, t: int) -> dict:
    """Every other instrument cut at `t` (bars closed by then), recomputed from scratch."""
    return {k: v.as_of(t) for k, v in others.items()}


def truncation_leaks(column: ColumnFn, series: BarSeries, others: dict, rows) -> list[int]:
    """Rows where the value computed on full history differs from the value computed with EVERY
    input — this instrument and all others — cut at that row's close. Empty means causal there."""
    full = np.asarray(column(series, others), float)
    bad = []
    for i in rows:
        i = int(i)
        t = int(series.available_at[i])
        part = np.asarray(column(series.take(slice(0, i + 1)), truncated(others, t)), float)
        a, b = full[i], part[i]
        same = (np.isnan(a) and np.isnan(b)) or a == b or abs(a - b) <= 1e-9 * max(1.0, abs(a))
        if not same:
            bad.append(i)
    return bad
