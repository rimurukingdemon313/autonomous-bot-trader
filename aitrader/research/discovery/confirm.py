"""A confirmatory program: judge hypotheses that already exist, from any source, exactly once.

This is where the loop closes for hypotheses the screen did not produce — a live lesson turned
into a veto, a language model's draft, a follow-up derived from how an earlier one failed:

    DRAFT (ledger) -> preregister(): registry trial (bins' fit period + judged period, one test
    per hypothesis, the threshold frozen from every earlier test), each hypothesis PREREGISTERED
    -> run(): the same battery and board as a discovery program -> VALIDATED | REJECTED

Rules that make the answer mean something:
- every hypothesis names ONE exit (a menu would be a selection this program cannot make);
- a hypothesis marked prospective-only is judged only on decisions made after it was drafted —
  history it could have been shaped by is refused before anything is computed;
- bins are fitted on the fit period and frozen; the judged period follows it after an embargo;
- design and code are checked against the preregistration, and the program runs once.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from ..labels import BUY, SELL, CostModel
from ..registry import Registry, Trial, Use, Verdict
from .battery import BatteryRules, regime_binnings, run_battery
from .board import adversarial_analyst, market_analyst, opportunity_analyst, reviewer, risk_analyst, synthesize
from .catalog import FeatureCatalog
from .hypothesis import Hypothesis, Ledger
from .program import REGIME_FEATURES, ProgramError, _atomic_write, _dump, _jsonable, _r, code_sha256
from .study import Condition, Segment, Study, SymbolData, epoch, fit_binning

CONFIRM_VERSION = "confirm-1.0.0"


@dataclass(frozen=True)
class ConfirmDesign:
    id: str
    title: str
    question: str
    universe: str
    instruments: tuple[str, ...]
    hypotheses: tuple[str, ...]  # ledger ids
    fit: Segment
    judge: Segment
    rules: BatteryRules
    holdout_start: date
    groups: tuple[tuple[str, tuple[tuple[float, ...], ...]], ...] = ()
    costs: CostModel = field(default_factory=CostModel)
    min_embargo_days: int = 5
    lookback_start: date | None = None

    def validate(self) -> None:
        if self.fit.role != "fit" or self.judge.role != "judge" or not self.fit.start < self.fit.end \
                or not self.judge.start < self.judge.end:
            raise ProgramError("a confirmatory program has one fit segment (for bins) and one judged segment")
        if (self.judge.start - self.fit.end).days < self.min_embargo_days:
            raise ProgramError(f"the judged segment must start {self.min_embargo_days} days after the fit segment")
        if self.judge.end > self.holdout_start:
            raise ProgramError("the judged segment reaches the sealed holdout")
        if not self.hypotheses or len(set(self.hypotheses)) != len(self.hypotheses):
            raise ProgramError("list each hypothesis once")
        if self.rules.t_threshold <= 0:
            raise ProgramError("a positive frozen threshold is required")

    def to_json(self) -> dict:
        d = asdict(self)
        d["fit"], d["judge"] = self.fit.to_json(), self.judge.to_json()
        d["holdout_start"] = self.holdout_start.isoformat()
        d["lookback_start"] = self.lookback_start.isoformat() if self.lookback_start else None
        d["groups"] = {f: [list(x) for x in g] for f, g in self.groups}
        d["version"] = CONFIRM_VERSION
        return json.loads(json.dumps(d, sort_keys=True, default=str))

    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.to_json(), sort_keys=True).encode()).hexdigest()


class ConfirmatoryProgram:
    def __init__(self, design: ConfirmDesign, registry: Registry, ledger: Ledger, catalog: FeatureCatalog,
                 knowledge_dir: Path | str, clock: Callable[[], datetime],
                 code_hash: Callable[[], str] = code_sha256, study_factory: Callable[..., Study] = Study) -> None:
        self.design, self.registry, self.ledger, self.catalog = design, registry, ledger, catalog
        self.knowledge_dir, self.clock, self.code_hash = Path(knowledge_dir), clock, code_hash
        self.study_factory = study_factory  # e.g. a CarryStudy: trade R that includes the carry proxy
        parts = self.knowledge_dir.resolve().parts
        if "models" in parts and "artifacts" in parts:
            raise ProgramError("research knowledge never goes where production loads models")

    def _hypotheses(self) -> list[Hypothesis]:
        out = []
        for hid in self.design.hypotheses:
            h = self.ledger.get(hid)
            if h.exit == "MENU":
                raise ProgramError(f"{hid} does not name one exit; choosing one here would be an uncounted selection")
            if h.condition.startswith("model:"):
                raise ProgramError(f"{hid} is a model score: judge it inside the program that froze the model")
            if h.prospective_only:
                drafted = datetime.fromisoformat(self.ledger.history(hid)[0]["at"]).date()
                if self.design.fit.start < drafted or self.design.judge.start < drafted:
                    raise ProgramError(f"{hid} is prospective only (drafted {drafted}); it cannot be fitted or judged "
                                       "on data from before it existed")
            for fid in h.features:
                if self.catalog.leakage_status(fid) != "PASSED":
                    raise ProgramError(f"{hid} uses {fid}, which has not passed the leakage test")
            out.append(h)
        return out

    def required_threshold(self) -> float:
        j = self.design.judge
        return self.registry.threshold_for_next(self.design.universe, j.start, j.end,
                                                new_tests=len(self.design.hypotheses))

    def preregister(self, doc_path: Path, doc_ref: str) -> Trial:
        d = self.design
        d.validate()
        if any(t.id == d.id for t in self.registry.trials):
            raise ProgramError(f"{d.id} is already registered")
        hs = self._hypotheses()
        for h in hs:
            if self.ledger.state(h.id) != "DRAFT":
                raise ProgramError(f"{h.id} is {self.ledger.state(h.id)}, not a draft")
        need = self.required_threshold()
        if abs(need - d.rules.t_threshold) > 1e-9:
            raise ProgramError(f"the design freezes t >= {d.rules.t_threshold:.4f}; the registry requires {need:.4f}")
        now = self.clock()
        code = self.code_hash()
        doc = (f"# {d.id} — {d.title}\n\n{d.question}\n\nHypotheses (one judged test each), bins fitted on "
               f"{d.fit.start} → {d.fit.end}, judged on {d.judge.start} → {d.judge.end} with t >= "
               f"{d.rules.t_threshold:.4f} and every battery check:\n\n" +
               "\n".join(f"- **{h.id}** ({h.kind}, {h.origin}): {h.statement} — `{h.condition}` {h.side}, exit {h.exit}"
                         for h in hs) +
               "\n\n" + "\n".join(f"- {k}: {v}" for k, v in d.rules.describe().items()) +
               f"\n\nDesign sha256 `{d.sha256()}`; code sha256 `{code}`.\n")
        _atomic_write(doc_path, doc)
        trial = self.registry.register(Trial(
            id=d.id, registered=now, title=d.title, hypothesis=d.question,
            uses=(Use(d.universe, min(d.lookback_start or d.fit.start, d.fit.start), d.fit.end, "fit"),
                  Use(d.universe, d.fit.end, d.judge.end, "judge")),
            tests=len(hs), configurations=len(hs), preregistration=doc_ref,
            design={"confirmatory_program": d.to_json(), "design_sha256": d.sha256(), "code_sha256": code}))
        for h in hs:
            self.ledger.transition(h.id, "PREREGISTERED", now, trial=d.id, preregistration_sha256=d.sha256())
        return trial

    def run(self, data: dict[str, SymbolData], data_hashes: dict[str, str] | None = None) -> dict:
        d = self.design
        trial = self.registry.get(d.id)
        if self.registry.status_of(d.id) != "PENDING":
            raise ProgramError(f"{d.id} already has a verdict; a program runs once")
        if trial.design.get("design_sha256") != d.sha256() or trial.design.get("code_sha256") != self.code_hash():
            raise ProgramError("the design or the code differs from what was preregistered")
        if self.registry.holdout is not None and d.judge.end > self.registry.holdout.start:
            raise ProgramError("the judged segment reaches the sealed holdout")
        hs = self._hypotheses()
        feats = sorted({f for h in hs for f in Condition.parse(h.condition).features} | set(REGIME_FEATURES))
        groups = {f: g for f, g in d.groups}
        base = self.study_factory(data, d.fit, {}, d.costs)
        vals = {f: {s: data[s].columns[f][base.rows[s]] for s in base.symbols} for f in feats}
        binn = {f: fit_binning(f, vals[f], groups=groups.get(f)) for f in feats}
        pert = [{f: fit_binning(f, vals[f], quantiles=(1 / 3 + q, 2 / 3 + q)) for f in feats if f not in groups}
                for q in (-d.rules.perturb, d.rules.perturb)]
        ctx = regime_binnings({f: vals[f] for f in REGIME_FEATURES})
        judge = self.study_factory(data, d.judge, binn, d.costs, context=ctx)
        out = []
        for h in hs:
            # a resumed run recomputes every judgment (it is deterministic) so the artifact is complete,
            # and only records the ledger steps that are missing
            if self.ledger.state(h.id) == "PREREGISTERED":
                self.ledger.transition(h.id, "RUNNING", self.clock(), trial=d.id, stage="confirmation", exit=h.exit)
            cond, side = Condition.parse(h.condition), BUY if h.side == "BUY" else SELL
            pb = [x for x in ({f: p[f] for f in cond.features if f in p} for p in pert) if x]
            res = run_battery(judge, cond, side, h.exit, d.rules, perturbed=pb, kind=h.kind, trials=len(hs), key=h.id)
            sign = -1.0 if h.kind == "veto" else 1.0
            opinions = [market_analyst(res), opportunity_analyst(res, {"mechanism": h.mechanism}, {
                            "confirmation": {"mean_R": res["checks"]["significance"]["mean_R"]}}),
                        risk_analyst(res),
                        adversarial_analyst(res, configurations=len(hs),
                                            prior_tests=self.registry.tests_on(d.universe, d.judge.start, d.judge.end)
                                            - len(hs)),
                        reviewer(res, segment_epochs=(epoch(d.judge.start), epoch(d.judge.end)),
                                 holdout_epoch=epoch(self.registry.holdout.start) if self.registry.holdout else 2 ** 62,
                                 declared_exit=h.exit, frozen_threshold=d.rules.t_threshold,
                                 preregistration_sha256=trial.design.get("design_sha256"),
                                 expected_sha256=d.sha256(), sign=sign)]
            syn = synthesize(res["verdict"], opinions)
            res.pop("trades")
            if self.ledger.state(h.id) == "RUNNING":
                self.ledger.transition(h.id, "COMPLETED", self.clock(), summary={
                    "n": res["checks"]["min_trades"]["n"], "t": res["checks"]["significance"]["t"],
                    "failed": res["failed"]})
            if self.ledger.state(h.id) == "COMPLETED":
                if syn["verdict"] == "VALIDATED":
                    self.ledger.transition(h.id, "VALIDATED", self.clock(),
                                           checks={k: v["pass"] for k, v in res["checks"].items()})
                else:
                    self.ledger.transition(h.id, "REJECTED", self.clock(), reason="; ".join(
                        res["failed"] + [f"blocked: {b}" for b in syn["blocked_by"]]))
            if self.ledger.state(h.id) != syn["verdict"]:
                raise ProgramError(f"{h.id} is {self.ledger.state(h.id)} in the ledger but judges {syn['verdict']} "
                                   "now: the run is not a replay")
            out.append({"id": h.id, "kind": h.kind, "origin": h.origin, "statement": h.statement,
                        "condition": h.condition, "side": h.side, "exit": h.exit, "battery": res, "board": syn})
        validated = [c["id"] for c in out if c["board"]["verdict"] == "VALIDATED"]
        body = {"program": d.id, "version": CONFIRM_VERSION, "design_sha256": d.sha256(), "code_sha256": self.code_hash(),
                "data_sha256": dict(sorted((data_hashes or {}).items())), "threshold_t": round(d.rules.t_threshold, 4),
                "judged": out, "validated": validated, "verdict": "PASSED" if validated else "FAILED",
                "knowledge": [{"id": c["id"], "statement": c["statement"],
                               "status": "VALIDATED research finding — not a trading rule"}
                              for c in out if c["id"] in validated]}
        body = json.loads(json.dumps(body, sort_keys=True, default=_jsonable))
        body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        _atomic_write(self.knowledge_dir / f"{d.id}.json", _dump(body))
        self.registry.record_verdict(Verdict(d.id, self.clock(), body["verdict"], {
            "validated": validated, "artifact": f"research/knowledge/{d.id}.json", "artifact_sha256": body["sha256"]}))
        return body


__all__ = ["CONFIRM_VERSION", "ConfirmDesign", "ConfirmatoryProgram", "_r"]
