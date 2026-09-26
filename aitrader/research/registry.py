"""The experiment registry: every hypothesis ever judged, and on which data.

A significance claim is a claim about a denominator. The registry is where
the denominator lives (RESEARCH_CONTRACT.md §4):

- append-only JSON lines, committed to the repository;
- every trial records the market periods it used and in which ROLE
  (fit / select / judge) — any role contaminates that period for a later
  trial that wants to call it unseen;
- contamination is keyed by UNIVERSE, not by file: a second vendor's copy of
  the same prices is not new evidence;
- a result is a separate VERDICT line, never an edit of the registration;
- the final holdout is mechanically single-use.

Runtime experiments proposed by the learning loop use the same types and
are written to the database; this file-backed registry is the research
record that travels with the code.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Iterable

ROLES = ("fit", "select", "judge")
STATUSES = ("PENDING", "PASSED", "FAILED", "INCONCLUSIVE", "INVALID", "ABANDONED")


class RegistryError(ValueError):
    """The registry refused a write because it would corrupt the record."""


class HoldoutSpent(RegistryError):
    """The final holdout has already been used; it cannot be reused."""


@dataclass(frozen=True)
class Holdout:
    universe: str
    start: date
    sealed_at: datetime
    rationale: str

    @classmethod
    def load(cls, path: Path | str) -> "Holdout":
        raw = json.loads(Path(path).read_text())
        return cls(raw["universe"], date.fromisoformat(raw["start"]),
                   datetime.fromisoformat(raw["sealed_at"]), raw["rationale"])

    def start_epoch(self) -> int:
        return int(datetime(self.start.year, self.start.month, self.start.day,
                            tzinfo=timezone.utc).timestamp())


@dataclass(frozen=True)
class Use:
    universe: str
    start: date
    end: date  # exclusive
    role: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise RegistryError(f"unknown role {self.role!r}; expected one of {ROLES}")
        if not self.start < self.end:
            raise RegistryError(f"empty range {self.start} → {self.end}")

    def overlaps(self, universe: str, start: date, end: date) -> bool:
        return self.universe == universe and self.start < end and start < self.end

    def to_json(self) -> dict:
        return {"universe": self.universe, "start": self.start.isoformat(),
                "end": self.end.isoformat(), "role": self.role}

    @classmethod
    def from_json(cls, raw: dict) -> "Use":
        return cls(raw["universe"], date.fromisoformat(raw["start"]),
                   date.fromisoformat(raw["end"]), raw["role"])


@dataclass(frozen=True)
class Trial:
    """A registered hypothesis. `tests` = verdicts read (the multiple-testing
    denominator); `configurations` = parameter sets actually evaluated."""

    id: str
    registered: datetime
    title: str
    hypothesis: str
    uses: tuple[Use, ...]
    tests: int
    configurations: int
    status: str = "PENDING"
    preregistration: str | None = None
    design: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise RegistryError(f"trial id {self.id!r} must be a plain slug")
        if self.status not in STATUSES:
            raise RegistryError(f"unknown status {self.status!r}")
        if self.tests < 0 or self.configurations < max(self.tests, 1):
            raise RegistryError(f"{self.id}: configurations ({self.configurations}) must be >= tests ({self.tests}) and >= 1")
        if self.registered.tzinfo is None:
            raise RegistryError(f"{self.id}: registration time must be timezone-aware")

    def to_json(self) -> dict:
        raw = asdict(self)
        raw["kind"] = "trial"
        raw["registered"] = self.registered.isoformat()
        raw["uses"] = [u.to_json() for u in self.uses]
        return raw

    @classmethod
    def from_json(cls, raw: dict) -> "Trial":
        return cls(
            id=raw["id"], registered=datetime.fromisoformat(raw["registered"]),
            title=raw["title"], hypothesis=raw["hypothesis"],
            uses=tuple(Use.from_json(u) for u in raw["uses"]),
            tests=int(raw["tests"]), configurations=int(raw["configurations"]),
            status=raw.get("status", "PENDING"), preregistration=raw.get("preregistration"),
            design=dict(raw.get("design") or {}), result=dict(raw.get("result") or {}),
        )


@dataclass(frozen=True)
class Verdict:
    trial: str
    recorded: datetime
    status: str
    result: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status == "PENDING" or self.status not in STATUSES:
            raise RegistryError(f"a verdict must be final, not {self.status!r}")
        if self.recorded.tzinfo is None:
            raise RegistryError("verdict time must be timezone-aware")

    def to_json(self) -> dict:
        return {"kind": "verdict", "trial": self.trial, "recorded": self.recorded.isoformat(),
                "status": self.status, "result": self.result}

    @classmethod
    def from_json(cls, raw: dict) -> "Verdict":
        return cls(raw["trial"], datetime.fromisoformat(raw["recorded"]), raw["status"],
                   dict(raw.get("result") or {}))


def bonferroni_t(tests: int, alpha: float = 0.05) -> float:
    if tests < 1:
        raise ValueError("at least one test is needed to set a threshold")
    return NormalDist().inv_cdf(1 - alpha / (2 * tests))


def holm(pvalues: Iterable[float], alpha: float = 0.05) -> list[bool]:
    ps = list(pvalues)
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    rejected = [False] * len(ps)
    for rank, i in enumerate(order):
        if ps[i] > alpha / (len(ps) - rank):
            break
        rejected[i] = True
    return rejected


class Registry:
    def __init__(self, path: Path | str, holdout: Holdout | None = None,
                 entries: Iterable[Trial | Verdict] = ()) -> None:
        self.path = Path(path)
        self.holdout = holdout
        self._trials: list[Trial] = []
        self._verdicts: dict[str, Verdict] = {}
        for e in entries:
            self._accept(e)

    @classmethod
    def load(cls, path: Path | str, holdout: Holdout | None = None) -> "Registry":
        path = Path(path)
        entries: list[Trial | Verdict] = []
        if path.exists():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    kind = raw.get("kind", "trial")
                    if kind == "trial":
                        entries.append(Trial.from_json(raw))
                    elif kind == "verdict":
                        entries.append(Verdict.from_json(raw))
                    else:
                        raise ValueError(f"unknown kind {kind!r}")
                except (KeyError, ValueError, TypeError) as exc:
                    raise RegistryError(f"{path}:{n}: unreadable entry ({exc})") from exc
        return cls(path, holdout, entries)

    @property
    def trials(self) -> tuple[Trial, ...]:
        return tuple(self._trials)

    def get(self, trial_id: str) -> Trial:
        for t in self._trials:
            if t.id == trial_id:
                return t
        raise KeyError(trial_id)

    def status_of(self, trial_id: str) -> str:
        v = self._verdicts.get(trial_id)
        return v.status if v else self.get(trial_id).status

    def verdict_of(self, trial_id: str) -> Verdict | None:
        return self._verdicts.get(trial_id)

    def register(self, trial: Trial) -> Trial:
        self._accept(trial)
        self._append(trial)
        return trial

    def record_verdict(self, verdict: Verdict) -> Verdict:
        self._accept(verdict)
        self._append(verdict)
        return verdict

    def _append(self, entry: Trial | Verdict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_json(), sort_keys=True) + "\n")

    def _accept(self, entry: Trial | Verdict) -> None:
        if isinstance(entry, Verdict):
            trial = self.get(entry.trial)
            if self.status_of(trial.id) != "PENDING":
                raise RegistryError(f"{trial.id} already has a final status ({self.status_of(trial.id)})")
            if entry.recorded < trial.registered:
                raise RegistryError(f"{trial.id}: verdict predates its registration")
            self._verdicts[trial.id] = entry
            return
        trial = entry
        if any(t.id == trial.id for t in self._trials):
            raise RegistryError(f"trial {trial.id!r} already exists; ids are never reused")
        if self._trials and trial.registered < self._trials[-1].registered:
            raise RegistryError(f"trial {trial.id!r} is dated before the last entry; no back-filling")
        if self.holdout is not None:
            h = self.holdout
            if trial.registered >= h.sealed_at and any(
                    u.overlaps(h.universe, h.start, date.max) for u in trial.uses):
                if trial.preregistration is None:
                    raise RegistryError(f"{trial.id}: the final holdout is used only by a pre-registered final test")
                # Exposure recorded BEFORE the seal (the archive's verdicts) is
                # declared and counted in thresholds; the single-use rule
                # governs this project's conduct from the moment of sealing.
                prior = [t for t in self.touching(h.universe, h.start, date.max)
                         if t.registered >= h.sealed_at]
                if prior:
                    raise HoldoutSpent(
                        f"the final holdout ({h.universe} from {h.start}) was already used by "
                        f"{', '.join(t.id for t in prior)}; it answers one question, once")
        self._trials.append(trial)

    # ── queries ─────────────────────────────────────────────────────────

    def touching(self, universe: str, start: date, end: date,
                 roles: tuple[str, ...] = ROLES) -> list[Trial]:
        return [t for t in self._trials
                if any(u.role in roles and u.overlaps(universe, start, end) for u in t.uses)]

    def tests_on(self, universe: str, start: date = date.min, end: date = date.max) -> int:
        return sum(t.tests for t in self.touching(universe, start, end))

    def configurations_on(self, universe: str, start: date = date.min, end: date = date.max) -> int:
        return sum(t.configurations for t in self.touching(universe, start, end))

    def is_unseen(self, universe: str, start: date, end: date) -> bool:
        return not self.touching(universe, start, end)

    def holdout_spent(self) -> bool:
        h = self.holdout
        return bool(h and [t for t in self.touching(h.universe, h.start, date.max)
                           if t.registered >= h.sealed_at])

    def prior_exposure_of_holdout(self) -> list[Trial]:
        """Trials that touched the holdout period before it was sealed."""
        h = self.holdout
        if not h:
            return []
        return [t for t in self.touching(h.universe, h.start, date.max) if t.registered < h.sealed_at]

    def threshold_for_next(self, universe: str, start: date = date.min, end: date = date.max,
                           new_tests: int = 1, alpha: float = 0.05) -> float:
        return bonferroni_t(self.tests_on(universe, start, end) + new_tests, alpha)

    def exposure_by_year(self, universe: str) -> dict[int, int]:
        years: dict[int, int] = {}
        for t in self._trials:
            touched = {y for u in t.uses if u.universe == universe
                       for y in range(u.start.year, (u.end - timedelta(days=1)).year + 1)}
            for y in touched:
                years[y] = years.get(y, 0) + t.tests
        return dict(sorted(years.items()))
