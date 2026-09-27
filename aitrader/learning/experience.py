"""Experience: point-in-time statistics over resolved outcomes, and lessons.

Every evaluated candidate — traded or not — eventually has an outcome: the R
it realised if traded, or its SHADOW outcome (what the same order would have
returned) if it was skipped or rejected. Learning from skipped trades matters:
it is the only way to know whether an objection, a lesson or the risk engine
is rejecting good trades.

POINT-IN-TIME. An outcome joins the statistics only once it has resolved.
`advance(t)` moves resolved records in; every query answers "as known at t".

LESSONS are hypotheses with a lifecycle, versioned in the database:

  CANDIDATE   created when a context (family, direction, regime, volatility)
              has >= MIN_N resolved outcomes AND its mean is significantly
              negative after a Bonferroni correction for every context examined.
  VALIDATED   only on outcomes resolved AFTER the candidate was created
              (out of sample relative to its discovery): >= MIN_OOS and still
              significantly negative. Only a validated lesson acts, and it can
              only block (AI can only subtract; a lesson never adds risk).
  REJECTED    out-of-sample evidence did not confirm it.
  RETIRED     a validated lesson whose later evidence reversed.

One loss changes nothing: the thresholds are sample sizes and significance,
so neither a single loss nor a single win can create, validate or retire a
lesson.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Callable

#: 1.1.0: `restore` (operator revert by appended versions). Learning itself is unchanged.
#: 1.2.0: standard errors and sample sizes account for overlapping outcomes and for
#: several evaluations of one decision (effective sample size); thresholds use n_eff.
LEARNING_VERSION = "learning-1.2.0"


@dataclass
class Evaluation:
    """One candidate that was evaluated, with its (eventual) outcome."""

    decision_id: str
    symbol: str
    decision_time: int
    resolve_time: int
    family: str
    action: str
    direction: int
    regime: str
    vol_state: str
    session: str
    objections: tuple[str, ...]
    traded: bool
    outcome_r: float
    predicted_r: float | None = None
    predicted_win: float | None = None
    llm_directions: dict = field(default_factory=dict)  # agent -> BUY/SELL/NONE


#: The decision cadence the system runs at (every 4th H1 close). Outcomes whose
#: horizons are longer than this overlap their neighbours and are not independent.
DECISION_SPACING_S = 4 * 3600


class _Agg:
    """Running mean and variance, with an honest standard error.

    Consecutive candidates share most of their outcome path (a 24-48 bar
    horizon, a decision every 4 bars), and the templates of one decision
    are two looks at one market move. Counting them as independent
    understates the standard error, and a lesson then "validates" on noise.
    The standard error is inflated by the overlap (mean horizon / decision
    spacing) and by the number of evaluations per decision, and every
    threshold uses the resulting effective sample size `n_eff`.
    """

    __slots__ = ("n", "s", "ss", "dur", "ids", "n_unique")

    def __init__(self) -> None:
        self.n, self.s, self.ss, self.dur = 0, 0.0, 0.0, 0.0
        self.ids: set = set()
        self.n_unique: int | None = None  # set only for derived aggregates (all minus flagged)

    def add(self, x: float, dur: float = 0.0, decision_id: str | None = None) -> None:
        self.n += 1
        self.s += x
        self.ss += x * x
        self.dur += max(0.0, dur)
        if decision_id is not None:
            self.ids.add(decision_id)

    def factor(self) -> float:
        if self.n == 0:
            return 1.0
        overlap = max(1.0, (self.dur / self.n) / DECISION_SPACING_S)
        uniq = self.n_unique if self.n_unique is not None else (len(self.ids) or self.n)
        return overlap * max(1.0, self.n / max(1, uniq))

    def stats(self) -> dict | None:
        if self.n < 2:
            return None
        m = self.s / self.n
        var = max(0.0, (self.ss - self.n * m * m) / (self.n - 1))
        f = self.factor()
        return {"n": self.n, "mean": m, "se": math.sqrt(var / self.n * f), "n_eff": self.n / f}


def _session(t: int) -> str:
    h = (t % 86400) // 3600
    return "ASIA" if h < 7 else "LONDON" if h < 12 else "OVERLAP" if h < 16 else "NEWYORK" if h < 21 else "LATE"


def context_key(e: Evaluation) -> tuple:
    return (e.family, e.direction, e.regime, e.vol_state)


@dataclass(frozen=True)
class LessonPolicy:
    min_n: int = 60
    min_oos: int = 40
    alpha: float = 0.05
    oos_z: float = 1.645  # one-sided 5% on genuinely new data
    max_oos_before_reject: int = 120
    retire_min: int = 60


class ExperienceView:
    def __init__(self, policy: LessonPolicy = LessonPolicy(),
                 on_lesson: Callable[[dict], None] | None = None) -> None:
        self.policy = policy
        self._pending: list[tuple[int, int, Evaluation]] = []
        self._seq = 0
        self.now = 0
        self.resolved: list[Evaluation] = []
        self._fam_regime: dict[tuple, _Agg] = {}
        self._ctx: dict[tuple, _Agg] = {}
        self._obj_flag: dict[str, _Agg] = {}
        self._all = _Agg()
        self._ctx_items: dict[tuple, list[tuple[int, int, float, str]]] = {}
        self._llm: dict[str, dict[str, _Agg]] = {}
        self.lessons: dict[str, list[dict]] = {}  # lesson_id -> versions (append-only)
        self._candidates_tested = 0
        self.on_lesson = on_lesson

    # ── ingestion ───────────────────────────────────────────────────────

    def record(self, e: Evaluation) -> None:
        if e.resolve_time < e.decision_time:
            raise ValueError("an outcome cannot resolve before its decision")
        self._seq += 1
        heapq.heappush(self._pending, (e.resolve_time, self._seq, e))

    def advance(self, t: int) -> list[Evaluation]:
        """Admit every outcome resolved at or before t. Returns what was admitted."""
        if t < self.now:
            raise ValueError("time cannot go backwards in an experience view")
        self.now = t
        admitted = []
        while self._pending and self._pending[0][0] <= t:
            _, _, e = heapq.heappop(self._pending)
            self._admit(e)
            admitted.append(e)
        return admitted

    def _admit(self, e: Evaluation) -> None:
        if not math.isfinite(e.outcome_r):
            return
        self.resolved.append(e)
        x, dur, did = e.outcome_r, e.resolve_time - e.decision_time, e.decision_id
        self._fam_regime.setdefault((e.family, e.regime), _Agg()).add(x, dur, did)
        self._ctx.setdefault(context_key(e), _Agg()).add(x, dur, did)
        self._ctx_items.setdefault(context_key(e), []).append((e.decision_time, e.resolve_time, x, did))
        self._all.add(x, dur, did)
        for code in set(e.objections):
            self._obj_flag.setdefault(code, _Agg()).add(x, dur, did)
        for agent, d in e.llm_directions.items():
            agree = "agree" if d == ("BUY" if e.direction > 0 else "SELL") else "oppose" if d in ("BUY", "SELL") else None
            if agree:
                self._llm.setdefault(agent, {}).setdefault(agree, _Agg()).add(x, dur, did)

    # ── point-in-time queries used by the agents ────────────────────────

    def family_regime_stats(self, family: str, regime: str, t: int) -> dict | None:
        self._check(t)
        a = self._fam_regime.get((family, regime))
        return a.stats() if a else None

    def objection_effect(self, code: str, t: int) -> dict | None:
        self._check(t)
        f = self._obj_flag.get(code)
        o = _Agg()
        if f is not None:  # unflagged = everything minus flagged: exact, whenever the code first appeared
            o.n, o.s, o.ss = self._all.n - f.n, self._all.s - f.s, self._all.ss - f.ss
            o.dur = self._all.dur - f.dur
            o.n_unique = max(1, len(self._all.ids) - len(f.ids))
        fs, os_ = (f.stats() if f else None), o.stats()
        if not fs or not os_:
            return None
        return {"n_flagged": fs["n_eff"], "mean_flagged": fs["mean"], "n_other": os_["n_eff"], "mean_other": os_["mean"],
                "se": math.sqrt(fs["se"] ** 2 + os_["se"] ** 2)}

    def agent_reliability(self, agent: str, t: int) -> float:
        """0..1: how well an LLM's opposition has predicted worse outcomes. 0 until proven."""
        self._check(t)
        d = self._llm.get(agent, {})
        a, o = (d.get("agree") or _Agg()).stats(), (d.get("oppose") or _Agg()).stats()
        if not a or not o or o["n_eff"] < 50 or a["n_eff"] < 50:
            return 0.0
        diff = a["mean"] - o["mean"]
        z = diff / math.sqrt(a["se"] ** 2 + o["se"] ** 2)
        return float(max(0.0, min(1.0, (z - 2.0) / 2.0)))

    def lessons_matching(self, family: str, regime: str, vol_state: str, direction: int, t: int) -> list[dict]:
        self._check(t)
        out = []
        for versions in self.lessons.values():
            cur = self._as_of(versions, t)
            if cur and cur["status"] == "VALIDATED" and tuple(cur["context"]) == (family, direction, regime, vol_state):
                out.append(cur)
        return out

    def _check(self, t: int) -> None:
        if t < self.now:
            # Answering for an earlier time from a later state would leak.
            raise ValueError(f"query at {t} after the view advanced to {self.now}")

    @staticmethod
    def _as_of(versions: list[dict], t: int) -> dict | None:
        cur = None
        for v in versions:
            if v["effective"] <= t:
                cur = v
        return cur

    # ── the lesson lifecycle ────────────────────────────────────────────

    def _new_version(self, lesson_id: str, status: str, t: int, **data) -> dict:
        versions = self.lessons.setdefault(lesson_id, [])
        prev = versions[-1] if versions else {}
        v = {**prev, **data, "lesson_id": lesson_id, "version": len(versions) + 1, "status": status,
             "effective": t, "learning_version": LEARNING_VERSION}
        versions.append(v)
        if self.on_lesson:
            self.on_lesson(v)
        return v

    def learn(self, t: int) -> list[dict]:
        """Create, validate, reject or retire lessons from evidence resolved by t."""
        self._check(t)
        pol = self.policy
        changes = []
        contexts = [(k, a.stats()) for k, a in self._ctx.items()]
        contexts = [(k, s) for k, s in contexts if s and s["n_eff"] >= pol.min_n]
        self._candidates_tested = max(self._candidates_tested, len(contexts))
        z_disc = NormalDist().inv_cdf(1 - pol.alpha / max(1, self._candidates_tested))
        for key, s in contexts:
            lid = "L:" + "|".join(str(x) for x in key)
            if lid in self.lessons:
                continue
            if s["mean"] + z_disc * s["se"] < 0:
                fam, d, reg, vol = key
                changes.append(self._new_version(
                    lid, "CANDIDATE", t, context=list(key),
                    statement=f"{fam} {'BUY' if d > 0 else 'SELL'} in {reg}/{vol} has negative expectancy",
                    created=t, discovery={"n": s["n"], "n_eff": round(s["n_eff"], 1), "mean": round(s["mean"], 4), "se": round(s["se"], 4),
                                          "z_threshold": round(z_disc, 3), "contexts_examined": self._candidates_tested}))
        for lid, versions in self.lessons.items():
            cur = versions[-1]
            key = tuple(cur["context"])
            since = cur["effective"]
            agg = _Agg()
            for dt, rt, r, did in self._ctx_items.get(key, ()):
                if dt > since and rt > since:
                    agg.add(r, rt - dt, did)
            st_ = agg.stats()
            if st_ is None:
                continue
            n, m, se = st_["n_eff"], st_["mean"], st_["se"]
            ev = {"n": agg.n, "n_eff": round(n, 1), "mean": round(m, 4), "se": round(se, 4)}
            if cur["status"] == "CANDIDATE":
                if n >= pol.min_oos and m + pol.oos_z * se < 0:
                    changes.append(self._new_version(lid, "VALIDATED", t, validation=ev))
                elif n >= pol.max_oos_before_reject or (n >= pol.min_oos and m - pol.oos_z * se > 0):
                    changes.append(self._new_version(lid, "REJECTED", t, validation=ev))
            elif cur["status"] == "VALIDATED":
                if n >= pol.retire_min and m - pol.oos_z * se > 0:
                    changes.append(self._new_version(lid, "RETIRED", t, retirement=ev))
        return changes

    def restore(self, undone: set[tuple[str, int]], t: int) -> list[dict]:
        """Undo lesson changes by APPENDING versions, never by deleting them.

        Each lesson touched by an undone change gets a new version, effective
        at t, carrying its state from before those changes; a lesson that did
        not exist before them is RETIRED. Version numbers are never reused, so
        the immutable lessons table and a restart both see the revert.
        """
        out = []
        for lid in sorted({lesson for lesson, _ in undone}):
            versions = self.lessons.get(lid, [])
            if not versions:
                continue
            keep = [v for v in versions if (lid, v["version"]) not in undone]
            target, cur = (keep[-1] if keep else None), versions[-1]
            if target is None:
                if cur["status"] in ("RETIRED", "REJECTED"):
                    continue
                out.append(self._new_version(lid, "RETIRED", t, reverted=True,
                                             reason="operator revert: the lesson did not exist at the target version"))
            elif cur["status"] != target["status"]:
                data = {k: v for k, v in target.items()
                        if k not in ("lesson_id", "version", "status", "effective", "learning_version")}
                out.append(self._new_version(lid, target["status"], t, **{**data, "reverted": True,
                                             "reason": f"operator revert: restored version {target['version']}"}))
        return out

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for versions in self.lessons.values():
            counts[versions[-1]["status"]] = counts.get(versions[-1]["status"], 0) + 1
        return {"resolved": len(self.resolved), "pending": len(self._pending), "lessons": counts,
                "contexts_examined": self._candidates_tested}


def session_of(t: int) -> str:
    return _session(t)
