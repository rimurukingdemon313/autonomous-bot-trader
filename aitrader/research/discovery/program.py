"""A discovery program: the closed loop, run ONCE, under a preregistration it cannot change.

    preregister()  the design -> feature catalog (budget, provenance, leakage test of every
                   feature) -> registry trial (fit / select / judge periods, test count, the
                   significance threshold frozen from every earlier test) -> preregistration
                   document. Nothing here reads an outcome.
    run()          refuses unless the trial is pending AND the design and the code are byte for
                   byte what was preregistered; then
        1. discovery (fit):       screen the declared grid; BH-FDR survivors become DRAFT hypotheses
        2. validation (select):   every declared exit for every draft; the model family is trained
                                  on discovery and its threshold chosen here; the best K advance
        3. confirmation (judge):  each finalist through the full battery, then the research board
        4. record:                ledger verdicts, catalog results, follow-up drafts (prospective
                                  only), the knowledge artifact, and LAST the registry verdict

Every step is deterministic and idempotent, so a run interrupted before its registry verdict
can be resumed and reaches exactly the same result; after the verdict it is refused. A
VALIDATED hypothesis is research knowledge: nothing here writes where production reads.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable

import numpy as np

from ..labels import BUY, SELL, CostModel
from ..models import Fitted, fit_stumps
from ..registry import Registry, RegistryError, Trial, Use, Verdict
from .battery import BATTERY_VERSION, BatteryRules, regime_binnings, run_battery
from .board import (BOARD_VERSION, CONCENTRATION, TAIL_LOSS_R, adversarial_analyst, market_analyst,
                    opportunity_analyst, reviewer, risk_analyst, synthesize)
from .catalog import CATALOG_VERSION, FeatureCatalog, FeatureRecord
from .exits import EXIT_BY_KEY, EXITS_VERSION
from .hypothesis import (HYPOTHESIS_VERSION, Hypothesis, Ledger, LedgerError, derive_next, falsification_from,
                         from_screen)
from .screen import SCREEN_VERSION, Grid, screen
from .study import STUDY_VERSION, Binning, Condition, Segment, Study, SymbolData, epoch, fit_binning

PROGRAM_VERSION = "program-1.0.0"
PACKAGE = Path(__file__).resolve().parents[2]
ORDER = {"DRAFT": 0, "PREREGISTERED": 1, "RUNNING": 2, "COMPLETED": 3, "VALIDATED": 4, "REJECTED": 4, "SHELVED": 4}
REGIME_FEATURES = ("er120", "vol_ratio")  # the battery's regime cells read these
LeakageFn = Callable[[str], tuple[list[int], int, list[str]]]


class ProgramError(RegistryError):
    """The program refused to do something that would make its result uninterpretable."""


def code_sha256(package: Path = PACKAGE) -> str:
    """Hash of every source file that computes a number in a discovery run."""
    files = sorted(list((package / "research" / "discovery").glob("*.py")) +
                   [package / "research" / f for f in ("labels.py", "models.py")] +
                   [package / "features" / "store.py", package / "data" / "resample.py", package / "data" / "bars.py"])
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(package).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


@dataclass(frozen=True)
class ModelPlan:
    family: str = "stumps"
    features: tuple[str, ...] = ()
    quantiles: tuple[float, ...] = (0.8, 0.9, 0.95)
    stride: int = 4  # train on every 4th decision row: the live cadence, and less overlap between labels
    target_exit: str = "E1"


@dataclass(frozen=True)
class ProgramDesign:
    id: str
    title: str
    question: str
    universe: str
    instruments: tuple[str, ...]
    segments: tuple[Segment, ...]  # (fit, select, judge)
    states: tuple[str, ...]
    triggers: tuple[str, ...]
    groups: tuple[tuple[str, tuple[tuple[float, ...], ...]], ...]  # declared categorical bins
    exits: tuple[str, ...]
    rules: BatteryRules
    holdout_start: date
    screen_exit: str = "E1"
    screen_min_n: int = 100
    screen_q: float = 0.10
    screen_keep: int = 20
    validation_min_t: float = 2.0
    validation_min_n: int = 100
    finalists: int = 5
    model: ModelPlan | None = None
    feature_budget: int = 40
    costs: CostModel = field(default_factory=CostModel)
    min_embargo_days: int = 5
    lookback_start: date | None = None  # first bar features may read (warm-up); counted as fit exposure
    timeframe: str = "H1"  # the decision bar; exits and features are counted in these bars

    @property
    def grid(self) -> Grid:
        return Grid(self.states, self.triggers)

    @property
    def group_map(self) -> dict:
        return {f: g for f, g in self.groups}

    def features(self) -> tuple[str, ...]:
        """Every feature the program uses, in a fixed order: grid first, then the model's."""
        seen = list(self.states + self.triggers)
        for f in (self.model.features if self.model else ()) + REGIME_FEATURES:
            if f not in seen:
                seen.append(f)
        return tuple(seen)

    def model_configurations(self) -> int:
        return 2 * len(self.model.quantiles) * len(self.exits) if self.model else 0

    def judged_tests(self) -> int:
        return self.finalists + (1 if self.model else 0)

    def configurations(self) -> int:
        return self.grid.size() + self.screen_keep * len(self.exits) + self.model_configurations() + \
            self.judged_tests()

    def validate(self) -> None:
        if len(self.segments) != 3 or tuple(s.role for s in self.segments) != ("fit", "select", "judge"):
            raise ProgramError("a program has exactly three segments: fit, select, judge — in that order")
        for s in self.segments:
            if not s.start < s.end:
                raise ProgramError(f"segment {s.name} is empty")
        for a, b in zip(self.segments, self.segments[1:]):
            if (b.start - a.end).days < self.min_embargo_days:
                raise ProgramError(f"{a.name} and {b.name} need an embargo of {self.min_embargo_days} days")
        if self.segments[2].end > self.holdout_start:
            raise ProgramError("the judged segment reaches the sealed holdout")
        if not set(self.exits) <= set(EXIT_BY_KEY) or self.screen_exit not in self.exits:
            raise ProgramError("exits must come from the declared menu, the screen's included")
        if self.rules.t_threshold <= 0 or not 1 <= self.finalists <= self.screen_keep:
            raise ProgramError("a positive frozen threshold and 1 <= finalists <= screen_keep are required")
        if len(self.features()) > self.feature_budget:
            raise ProgramError(f"{len(self.features())} features exceed the budget of {self.feature_budget}")
        for f, g in self.groups:
            if f not in self.states + self.triggers or len(g) != 3:
                raise ProgramError(f"categorical groups for {f} must be three and belong to the grid")
        if self.model and (self.model.family != "stumps" or not self.model.features):
            raise ProgramError("the model plan must name its features; only the stumps family is wired here")

    def to_json(self) -> dict:
        d = asdict(self)
        d["segments"] = [s.to_json() for s in self.segments]
        d["holdout_start"] = self.holdout_start.isoformat()
        d["lookback_start"] = self.lookback_start.isoformat() if self.lookback_start else None
        d["groups"] = {f: [list(x) for x in g] for f, g in self.groups}
        d["grid_tests"] = self.grid.size()
        d["judged_tests"] = self.judged_tests()
        d["configurations"] = self.configurations()
        d["versions"] = {"program": PROGRAM_VERSION, "study": STUDY_VERSION, "screen": SCREEN_VERSION,
                         "exits": EXITS_VERSION, "battery": BATTERY_VERSION, "board": BOARD_VERSION,
                         "hypothesis": HYPOTHESIS_VERSION, "catalog": CATALOG_VERSION}
        return json.loads(json.dumps(d, sort_keys=True, default=str))

    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.to_json(), sort_keys=True).encode()).hexdigest()


@dataclass
class ModelSignal:
    """A frozen model score above a frozen threshold, as a signal the battery can judge."""

    key: str
    fitted: Fitted
    features: tuple[str, ...]
    data: dict
    threshold: float
    perturbed: tuple[float, ...]

    def _pred(self, study: Study) -> dict:
        cache = self.__dict__.setdefault("_cache", {})
        if id(study) not in cache:
            cache[id(study)] = {s: self.fitted.predict(np.column_stack(
                [self.data[s].columns[f][study.rows[s]] for f in self.features])) for s in study.symbols}
        return cache[id(study)]

    def masks(self, study: Study) -> dict:
        return {s: p >= self.threshold for s, p in self._pred(study).items()}

    def perturbed_masks(self, study: Study) -> list[dict]:
        return [{s: p >= t for s, p in self._pred(study).items()} for t in self.perturbed]


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _dump(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n"


class DiscoveryProgram:
    def __init__(self, design: ProgramDesign, registry: Registry, ledger: Ledger, catalog: FeatureCatalog,
                 knowledge_dir: Path | str, clock: Callable[[], datetime], records: dict[str, FeatureRecord],
                 code_hash: Callable[[], str] = code_sha256) -> None:
        self.design, self.registry, self.ledger, self.catalog = design, registry, ledger, catalog
        self.knowledge_dir = Path(knowledge_dir)
        self.clock, self.records, self.code_hash = clock, records, code_hash
        if "models" in self.knowledge_dir.resolve().parts and "artifacts" in self.knowledge_dir.resolve().parts:
            raise ProgramError("research knowledge never goes where production loads models")

    # ── preregistration ─────────────────────────────────────────────────

    def required_threshold(self) -> float:
        judge = self.design.segments[2]
        return self.registry.threshold_for_next(self.design.universe, judge.start, judge.end,
                                                new_tests=self.design.judged_tests())

    def preregister(self, doc_path: Path, doc_ref: str, leakage: LeakageFn) -> Trial:
        d = self.design
        d.validate()
        if any(t.id == d.id for t in self.registry.trials):
            raise ProgramError(f"{d.id} is already registered")
        need = self.required_threshold()
        if abs(need - d.rules.t_threshold) > 1e-9:
            raise ProgramError(f"the design freezes t >= {d.rules.t_threshold:.4f} but the registry now requires "
                               f"{need:.4f} for {d.judged_tests()} more tests on the judged period")
        missing = [f for f in d.features() if f not in self.records]
        if missing:
            raise ProgramError(f"features without a catalog record: {missing}")
        now = self.clock()
        used, allowed = self.catalog.budget(d.id)
        if allowed == 0:
            self.catalog.open_program(d.id, d.feature_budget, now)
        elif allowed != d.feature_budget:
            raise ProgramError(f"{d.id} already declared a feature budget of {allowed}")
        failed = []
        for name in d.features():
            rec = self.catalog.register(self.records[name], now)
            if self.catalog.leakage_status(rec.id) != "PASSED":
                bad, rows, syms = leakage(name)
                if self.catalog.record_leakage(rec.id, bad, rows, syms, now) != "PASSED":
                    failed.append(name)
        if failed:
            raise ProgramError(f"leakage test failed for {failed}: nothing is registered; fix the feature "
                               "(a new version) before any run")
        code = self.code_hash()
        _atomic_write(doc_path, render_preregistration(d, code))
        trial = Trial(
            id=d.id, registered=now, title=d.title, hypothesis=d.question,
            uses=(Use(d.universe, min(d.lookback_start or d.segments[0].start, d.segments[0].start),
                      d.segments[0].end, "fit"),
                  Use(d.universe, d.segments[0].end, d.segments[1].end, "select"),
                  Use(d.universe, d.segments[1].end, d.segments[2].end, "judge")),
            tests=d.judged_tests(), configurations=d.configurations(), preregistration=doc_ref,
            design={"discovery_program": d.to_json(), "design_sha256": d.sha256(), "code_sha256": code,
                    "document_sha256": hashlib.sha256(doc_path.read_bytes()).hexdigest()})
        return self.registry.register(trial)

    # ── the run ─────────────────────────────────────────────────────────

    def _check_runnable(self, data: dict[str, SymbolData]) -> Trial:
        d = self.design
        trial = self.registry.get(d.id)
        if self.registry.status_of(d.id) != "PENDING":
            raise ProgramError(f"{d.id} already has a verdict ({self.registry.status_of(d.id)}); a program runs once")
        if trial.design.get("design_sha256") != d.sha256():
            raise ProgramError("the design differs from the one preregistered; register a new program instead")
        if trial.design.get("code_sha256") != self.code_hash():
            raise ProgramError("the code differs from the code preregistered; register a new program instead")
        h = self.registry.holdout
        if h is not None and d.segments[2].end > h.start:
            raise ProgramError("the judged segment reaches the sealed holdout")
        if set(data) != set(d.instruments):
            raise ProgramError(f"data for {sorted(data)} but the design declares {sorted(d.instruments)}")
        for name in d.features():
            fid = self.records[name].id
            if self.catalog.leakage_status(fid) != "PASSED":
                raise ProgramError(f"{fid} has not passed the leakage test")
            for s, sd in data.items():
                if name not in sd.columns:
                    raise ProgramError(f"{s} has no column {name!r}")
        return trial

    def _step(self, hid: str, state: str, **data) -> None:
        for e in self.ledger.history(hid):
            if e.get("state", "DRAFT") == state and e.get("data", {}).get("stage") == data.get("stage"):
                return
        cur = self.ledger.state(hid)
        if ORDER[cur] > ORDER[state] or (ORDER[cur] == 4 and ORDER[state] == 4):
            return
        self.ledger.transition(hid, state, self.clock(), **data)

    def _draft(self, h: Hypothesis) -> Hypothesis:
        try:
            existing = self.ledger.get(h.id)
        except LedgerError:
            return self.ledger.draft(h, self.clock())
        if existing.substance() != h.substance():
            raise ProgramError(f"{h.id} exists with a different substance; the run is not a replay")
        return existing

    def run(self, data: dict[str, SymbolData], data_hashes: dict[str, str] | None = None,
            stop_after: str | None = None) -> dict:
        d = self.design
        self._check_runnable(data)
        disc_seg, val_seg, conf_seg = d.segments
        ids = {f: self.records[f].id for f in d.features()}
        now = self.clock()
        for f in d.features():
            self.catalog.mark_used(ids[f], d.id, now)

        # frozen bins from the discovery rows only
        base = Study(data, disc_seg, {}, d.costs)
        values = {f: {s: data[s].columns[f][base.rows[s]] for s in base.symbols} for f in d.states + d.triggers}
        groups = d.group_map
        binn = {f: fit_binning(f, values[f], groups=groups.get(f)) for f in d.states + d.triggers}
        pert = [{f: fit_binning(f, values[f], quantiles=(1 / 3 + dq, 2 / 3 + dq))
                 for f in d.states + d.triggers if f not in groups}
                for dq in (-d.rules.perturb, d.rules.perturb)]
        reg_vals = {f: {s: data[s].columns[f][base.rows[s]] for s in base.symbols} for f in ("er120", "vol_ratio")}
        ctx = regime_binnings(reg_vals)
        studies = {s.name: Study(data, s, binn, d.costs, context=ctx) for s in d.segments}
        disc, val, conf = studies[disc_seg.name], studies[val_seg.name], studies[conf_seg.name]

        # 1. discovery: the screen
        scr = screen(disc, d.grid, exit_key=d.screen_exit, min_n=d.screen_min_n, q=d.screen_q, keep=d.screen_keep)
        rules_text = self._falsification()
        drafts = []
        for k, row in enumerate(scr["survivors"], 1):
            h = from_screen(f"{d.id}-H{k:02d}", row, program=d.id, instruments=d.instruments, feature_ids=ids,
                            rules=rules_text | {"screen_tests": scr["tests"]}, budget=len(d.exits),
                            timeframe=d.timeframe)
            drafts.append(self._draft(h))
            self._step(h.id, "PREREGISTERED", trial=d.id, preregistration_sha256=d.sha256())
        if stop_after == "screen":
            return {"stopped_after": "screen"}

        # 2. validation: every exit for every draft
        val_rows = []
        for h in drafts:
            self._step(h.id, "RUNNING", trial=d.id, stage="validation")
            cond, side = Condition.parse(h.condition), BUY if h.side == "BUY" else SELL
            per_exit = {}
            for e in d.exits:
                st = val.trades(val.masks(cond), e, side).stats()
                per_exit[e] = {"n": st["n"], "mean_R": _r(st["mean"]), "t": _r(st["t"], 3)}
            passing = [e for e in d.exits if per_exit[e]["n"] >= d.validation_min_n and per_exit[e]["t"] is not None
                       and per_exit[e]["mean_R"] > 0 and per_exit[e]["t"] >= d.validation_min_t]
            best = max(passing, key=lambda e: (per_exit[e]["t"], -d.exits.index(e))) if passing else None
            val_rows.append({"id": h.id, "condition": h.condition, "side": h.side, "per_exit": per_exit,
                             "best_exit": best, "best_t": per_exit[best]["t"] if best else None})
        ranked = sorted([v for v in val_rows if v["best_exit"]], key=lambda v: (-v["best_t"], v["id"]))
        finalist_ids = [v["id"] for v in ranked[: d.finalists]]
        for v in val_rows:
            if v["id"] in finalist_ids:
                continue
            self._step(v["id"], "COMPLETED", summary={"validation": v["per_exit"]})
            if v["best_exit"]:
                self._step(v["id"], "SHELVED", reason=f"passed validation (best {v['best_exit']}, t {v['best_t']}) "
                                                     f"but ranked below the {d.finalists} finalists; not judged")
            else:
                self._step(v["id"], "REJECTED", reason="no declared exit reached mean R > 0 with t >= "
                                                      f"{d.validation_min_t} on the validation segment")

        model_out = self._model_stage(data, disc, val) if d.model else None
        if stop_after == "validation":
            return {"stopped_after": "validation"}

        # 3. confirmation: the battery and the board
        finals = []
        for v in val_rows:
            if v["id"] in finalist_ids:
                finals.append((self.ledger.get(v["id"]), Condition.parse(v["condition"]), v["best_exit"], v, None))
        if model_out and model_out.get("finalist"):
            mf = model_out["finalist"]
            finals.append((self.ledger.get(mf["id"]), model_out["signal"], mf["exit"], mf, "model"))
        confirmations = []
        for h, cond, exit_key, vrow, kind in finals:
            self._step(h.id, "RUNNING", trial=d.id, stage="confirmation", exit=exit_key)
            side = BUY if h.side == "BUY" else SELL
            pb = [{f: p[f] for f in cond.features if f in p} for p in pert] if kind is None else []
            res = run_battery(conf, cond, side, exit_key, d.rules, perturbed=[x for x in pb if x], trials=d.configurations(),
                              key=h.id)
            per_segment = {}
            for name, st_ in (("discovery", disc), ("validation", val), ("confirmation", conf)):
                m = st_.masks(cond) if kind is None else cond.masks(st_)
                per_segment[name] = {"mean_R": _r(st_.trades(m, exit_key, side).stats()["mean"])}
            opinions = [
                market_analyst(res),
                opportunity_analyst(res, {"mechanism": h.mechanism}, per_segment),
                risk_analyst(res),
                adversarial_analyst(res, configurations=d.configurations(),
                                    prior_tests=self.registry.tests_on(d.universe, conf_seg.start, conf_seg.end)
                                    - d.judged_tests()),
                reviewer(res, segment_epochs=(epoch(conf_seg.start), epoch(conf_seg.end)),
                         holdout_epoch=epoch(self.registry.holdout.start) if self.registry.holdout else 2 ** 62,
                         declared_exit=exit_key, frozen_threshold=d.rules.t_threshold,
                         preregistration_sha256=self.registry.get(d.id).design.get("design_sha256"),
                         expected_sha256=d.sha256()),
            ]
            syn = synthesize(res["verdict"], opinions)
            tr = res.pop("trades")
            summary = {"n": res["checks"]["min_trades"]["n"], "mean_R": res["checks"]["significance"]["mean_R"],
                       "t": res["checks"]["significance"]["t"], "failed": res["failed"]}
            self._step(h.id, "COMPLETED", summary=summary)
            if syn["verdict"] == "VALIDATED":
                self._step(h.id, "VALIDATED", checks={k: v["pass"] for k, v in res["checks"].items()})
            else:
                why = res["failed"] + [f"blocked: {b}" for b in syn["blocked_by"]]
                self._step(h.id, "REJECTED", reason="; ".join(why))
            if self.ledger.state(h.id) != syn["verdict"]:
                raise ProgramError(f"{h.id} is {self.ledger.state(h.id)} in the ledger but judges {syn['verdict']} "
                                   "now: the run is not a replay")
            confirmations.append({"id": h.id, "statement": h.statement, "condition": h.condition, "side": h.side,
                                  "exit": exit_key, "kind": kind or "cell", "battery": res, "board": syn,
                                  "per_segment": per_segment,
                                  "trades": {"symbol": tr.symbol.astype(str).tolist(), "t": tr.t.astype(int).tolist(),
                                             "r": [round(float(x), 6) for x in tr.r]}})

        # 4. record: follow-ups, catalog results, knowledge, and last the registry verdict
        follow = []
        for c in confirmations:
            if c["board"]["verdict"] == "VALIDATED":
                continue
            inst_ok = tuple(c["battery"]["checks"].get("instruments", {}).get("positive", ()))
            nxt = derive_next(self.ledger.get(c["id"]), c["exit"], c["battery"]["failed"],
                              c["battery"]["checks"], program=d.id, hid=f"{c['id']}-N1", instruments_ok=inst_ok)
            if nxt is not None:
                follow.append(self._draft(nxt).id)
        validated = [c["id"] for c in confirmations if c["board"]["verdict"] == "VALIDATED"]
        uses = {c["id"]: self._features_of(c["condition"]) for c in confirmations}
        for f in d.features():
            fid = ids[f]
            if any(x["experiment"] == d.id for x in self.catalog.results(fid)):
                continue
            rows = [r for r in scr["table"] if f in Condition.parse(r["condition"]).features]
            self.catalog.record_result(fid, d.id, {
                "screen_cells": len(rows), "screen_discoveries": sum(r["discovery"] for r in rows),
                "finalists": [c for c, fs in uses.items() if f in fs],
                "validated": [c for c in validated if f in uses[c]]}, self.clock())

        artifact = self._artifact(scr, val_rows, finalist_ids, model_out, confirmations, validated, follow,
                                  data_hashes or {})
        verdict = "PASSED" if validated else "FAILED"
        self.registry.record_verdict(Verdict(d.id, self.clock(), verdict, {
            "validated": validated, "judged": [c["id"] for c in confirmations],
            "screen_discoveries": scr["discoveries"], "artifact": f"research/knowledge/{d.id}.json",
            "artifact_sha256": artifact["sha256"]}))
        return artifact

    # ── the model family ────────────────────────────────────────────────

    def _model_stage(self, data: dict, disc: Study, val: Study) -> dict:
        d, plan = self.design, self.design.model
        feats = plan.features
        configs, fits, preds = [], {}, {}
        for side in (BUY, SELL):
            X, y = [], []
            for s in disc.symbols:
                pos = np.arange(0, len(disc.rows[s]), plan.stride)
                o = disc.outcome(s, EXIT_BY_KEY[plan.target_exit], side)
                X.append(np.column_stack([data[s].columns[f][disc.rows[s][pos]] for f in feats]))
                y.append(o["r"][pos])
            fitted = fit_stumps(np.vstack(X), np.concatenate(y))
            fits[side] = fitted
            preds[side] = {s: fitted.predict(np.column_stack([data[s].columns[f][val.rows[s]] for f in feats]))
                           for s in val.symbols}
            pooled = np.concatenate(list(preds[side].values()))
            for q in plan.quantiles:
                thr = float(np.quantile(pooled, q))
                masks = {s: p >= thr for s, p in preds[side].items()}
                for e in d.exits:
                    st = val.trades(masks, e, side).stats()
                    configs.append({"side": "BUY" if side > 0 else "SELL", "quantile": q, "threshold": thr,
                                    "exit": e, "n": st["n"], "mean_R": _r(st["mean"]), "t": _r(st["t"], 3)})
        for side, f in fits.items():
            _atomic_write(self.knowledge_dir / f"{d.id}-model-{'BUY' if side > 0 else 'SELL'}.json",
                          _dump(f.to_json() | {"features": list(feats), "program": d.id}))
        passing = [c for c in configs if c["n"] >= d.validation_min_n and c["t"] is not None and c["mean_R"] > 0
                   and c["t"] >= d.validation_min_t]
        out = {"configurations": configs, "passing": len(passing), "features": list(feats)}
        if not passing:
            return out
        best = max(passing, key=lambda c: (c["t"], -configs.index(c)))
        side = BUY if best["side"] == "BUY" else SELL
        pooled = np.concatenate(list(preds[side].values()))
        lo, hi = max(0.5, best["quantile"] - d.rules.perturb), min(0.99, best["quantile"] + d.rules.perturb)
        hid = f"{d.id}-M1"
        signal = ModelSignal(hid, fits[side], feats, data, best["threshold"],
                             (float(np.quantile(pooled, lo)), float(np.quantile(pooled, hi))))
        h = Hypothesis(
            id=hid, statement=(f"A {best['side']} when the boosted-stumps score (trained on the discovery segment) is "
                               f"in its top {1 - best['quantile']:.0%} has positive net expectancy with {best['exit']}."),
            rationale=(f"model family 'stumps' on {len(feats)} catalogued features; threshold and exit chosen on the "
                       f"validation segment among {d.model_configurations()} configurations (t {best['t']})"),
            mechanism="state-dependent (conjectured): no single mechanism; an additive model of one-feature steps",
            features=tuple(self.records[f].id for f in feats), condition=f"model:{hid}:q{best['quantile']}",
            side=best["side"], instruments=d.instruments, timeframe=d.timeframe, exit=best["exit"],
            expected_effect="mean net R per trade > 0 on the confirmation segment",
            falsification=falsification_from(self._falsification()), budget=d.model_configurations(),
            origin="model", program=d.id, evidence={"validation": best})
        self._draft(h)
        self._step(hid, "PREREGISTERED", trial=d.id, preregistration_sha256=d.sha256())
        out["finalist"] = {"id": hid, "exit": best["exit"], **best}
        out["signal"] = signal
        return out

    # ── outputs ─────────────────────────────────────────────────────────

    def _features_of(self, condition: str) -> tuple[str, ...]:
        if condition.startswith("model:"):
            return self.design.model.features
        return Condition.parse(condition).features

    def _falsification(self) -> dict:
        return self.design.rules.describe()

    def _next_experiment(self, scr: dict, val_rows: list, confirmations: list, validated: list, follow: list,
                         model_out: dict | None) -> str:
        d = self.design
        if validated:
            return (f"Prospective paper monitoring of {', '.join(validated)}: record every signal from the frozen rule "
                    "on data after this run, judge with the same battery after >= 100 trades, and change nothing in "
                    "production before that verdict.")
        model = ""
        if model_out is not None:
            judged = [c for c in confirmations if c["kind"] == "model"]
            model = (f" The model finalist {judged[0]['id']} was rejected ({', '.join(judged[0]['battery']['failed']) or 'blocked by the board'})."
                     if judged else " The stumps model had no configuration that passed validation.")
        if scr["discoveries"] == 0:
            return (f"The {d.id} grid produced no cell at FDR q <= {d.screen_q} on the discovery segment.{model} Register "
                    "the next program on a dimension this grid did not cover (daily-horizon exits or regime "
                    "transitions as states) BEFORE it runs, rather than widening this grid after seeing it.")
        if not any(v["best_exit"] for v in val_rows):
            return ("Every screen discovery failed validation: they were most likely discovery-period noise." + model +
                    " The next experiment should test the screen's stability itself (split-half discovery) before "
                    "new cells.")
        return (f"All {len(confirmations)} judged hypotheses were rejected on the confirmation segment.{model} "
                f"Follow-ups drafted for prospective testing only: "
                f"{', '.join(follow) or 'none (every failure was in the core claim)'}.")

    def _artifact(self, scr, val_rows, finalist_ids, model_out, confirmations, validated, follow, hashes) -> dict:
        d = self.design
        body = {
            "program": d.id, "version": PROGRAM_VERSION, "title": d.title, "question": d.question,
            "design_sha256": d.sha256(), "code_sha256": self.code_hash(), "data_sha256": dict(sorted(hashes.items())),
            "segments": [s.to_json() for s in d.segments], "threshold_t": round(d.rules.t_threshold, 4),
            "configurations": d.configurations(),
            "leakage": {f: self.catalog.leakage_status(self.records[f].id) for f in d.features()},
            "screen": {k: scr[k] for k in ("tests", "testable", "discoveries", "q", "min_n", "exit")} |
                      {"survivors": scr["survivors"], "table": f"{d.id}-screen.json"},
            "validation": {"hypotheses": val_rows, "finalists": finalist_ids},
            "model": {k: v for k, v in (model_out or {}).items() if k != "signal"} if model_out else None,
            "confirmation": [{k: v for k, v in c.items() if k != "trades"} for c in confirmations],
            "verdict": "PASSED" if validated else "FAILED", "validated": validated,
            "knowledge": [{"id": c["id"], "statement": c["statement"], "exit": c["exit"],
                           "status": "VALIDATED research finding — not a trading rule"}
                          for c in confirmations if c["id"] in validated],
            "follow_up_drafts": follow,
            "next_experiment": self._next_experiment(scr, val_rows, confirmations, validated, follow, model_out),
            "ledger": self.ledger.counts(),
        }
        body = json.loads(json.dumps(body, sort_keys=True, default=_jsonable))
        body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        _atomic_write(self.knowledge_dir / f"{d.id}-screen.json", _dump(scr["table"]))
        _atomic_write(self.knowledge_dir / f"{d.id}-trades.json",
                      _dump({c["id"]: c["trades"] for c in confirmations}))
        _atomic_write(self.knowledge_dir / f"{d.id}.json", _dump(body))
        return body


def _jsonable(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    return str(x)


def _r(x, nd=5):
    if x is None:
        return None
    x = float(x)
    return None if not np.isfinite(x) else round(x, nd)


def render_preregistration(d: ProgramDesign, code: str) -> str:
    seg = "\n".join(f"| {s.name} | {s.start} → {s.end} | {s.role} |" for s in d.segments)
    groups = "; ".join(f"{f}: low={list(g[0])}, mid={list(g[1])}, high={list(g[2])}" for f, g in d.groups)
    rules = "\n".join(f"- **{k}** — {v}" for k, v in d.rules.describe().items())
    model = (f"`{d.model.family}` on {len(d.model.features)} features, trained on every {d.model.stride}th discovery "
             f"row per side (target: {d.model.target_exit} net R); thresholds at validation-prediction quantiles "
             f"{list(d.model.quantiles)} x exits {list(d.exits)} x both sides = {d.model_configurations()} "
             "configurations; the best passing one is judged.") if d.model else "none"
    return f"""# {d.id} — {d.title}

**Generated from the design and committed before any run on real data.** The registry entry
stores this document's hash, the design hash and the hash of the code that will run; `run()`
refuses if any of them differs. Results are written to `research/knowledge/{d.id}.json` and
judged by the rules below, unchanged.

## Question

{d.question}

## Data

- Instruments ({len(d.instruments)}): {' '.join(d.instruments)} — {d.timeframe} bid/ask bars built from complete M15 bars
  (decisions at each {d.timeframe} close; exits and feature windows are counted in {d.timeframe} bars).
- The sealed holdout (from {d.holdout_start}) is not read: the loader truncates there and every
  outcome must resolve inside its segment.

| Segment | Decision dates | Registry role |
|---|---|---|
{seg}

Outcomes never straddle segments (rows whose longest possible outcome would cross the segment end
are purged); consecutive segments are separated by at least {d.min_embargo_days} days.

## Stage 1 — discovery (fit): a bounded screen

- States ({len(d.states)}): {', '.join(d.states)}
- Triggers ({len(d.triggers)}): {', '.join(d.triggers)}
- Bins: per-instrument terciles fitted on discovery rows only and frozen; declared groups for
  categorical features ({groups}).
- Cells: every single feature bin, and every state bin x trigger bin, each for BUY and SELL:
  **{d.grid.size()} tests**, all counted (cells with fewer than {d.screen_min_n} trades get p = 1).
- Baseline exit {d.screen_exit}; one position per instrument; clustered (weekly) t; one-sided p;
  Benjamini-Hochberg at q = {d.screen_q}. The best {d.screen_keep} discoveries by (mean - 2 se)
  become DRAFT hypotheses.

## Stage 2 — validation (select)

- Each draft is evaluated with every declared exit ({', '.join(d.exits)}): {d.screen_keep * len(d.exits)}
  configurations at most. It passes with n >= {d.validation_min_n}, mean R > 0 and t >= {d.validation_min_t}
  for its best exit; the best {d.finalists} passing drafts (by t) are the finalists, each with its
  best exit frozen.
- Model family: {model}

## Stage 3 — confirmation (judge)

At most **{d.judged_tests()} judged tests**. The significance threshold is frozen now from the
registry (every earlier test on the judged period, plus these): **t >= {d.rules.t_threshold:.4f}**.
A finalist is VALIDATED only if every check passes:

{rules}

Then the research board (market, opportunity, risk, adversarial, independent reviewer) reads the
result. There is no vote: any blocking objection turns VALIDATED into REJECTED; nothing turns
REJECTED into VALIDATED. The objections that block are declared now:

- risk: any single trade worse than {TAIL_LOSS_R:.0f}R (a gap carried it past its stop; no per-trade
  limit bounds that loss);
- adversarial: one instrument or one year carries more than {CONCENTRATION:.0%} of the total R while the
  remaining trades earn less than a third as much per trade;
- reviewer: its independent recomputation of n or the clustered t disagrees with the battery; a trade
  lies outside the judged segment or reaches the holdout; two trades overlap on one instrument; the
  exit, the threshold or the design hash is not the one frozen here.

Market and opportunity analysts record concerns only. The deflated Sharpe ratio over all
{d.configurations()} configurations is reported for information.

## What the outcome means

- PASSED (at least one VALIDATED hypothesis): research knowledge, not a trading rule. The next
  step is a prospective paper test; production is not changed by this program.
- FAILED: a valid negative result. It is recorded, searchable, and counted in every later threshold.

Costs: {json.dumps(asdict(d.costs))}. Design sha256 `{d.sha256()}`; code sha256 `{code}`.
"""
