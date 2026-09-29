"""The research lab: disciplined, autonomous hypothesis testing (RESEARCH_CONTRACT §5).

    OBSERVE -> HYPOTHESIS -> DECLARED SPEC -> REGISTER -> WALK-FORWARD (purged,
    embargoed) -> OUT-OF-SAMPLE -> BASELINES -> ROBUSTNESS -> VERDICT -> VERSION

What makes it disciplined, in code rather than in intent:

- **Declared space.** A spec may only use values the `HypothesisSpace`
  declares: instruments, timeframes, features (base or grammar candidates),
  model families, action templates. Anything else is refused. The AI's
  freedom is real and bounded, as PROJECT_SPEC §3 requires.
- **Register first.** `run` refuses a trial that is not in the registry.
  Registration records the data periods and their roles, and FREEZES the
  significance threshold, taken from the registry at that moment, and the
  pass rules into the trial. Every later test on the same universe and
  period faces a higher bar.
- **No rescue.** A spec whose *substance* (instruments, timeframe,
  features, model, template, side) matches a FAILED trial is refused.
  Changing only the threshold, the cadence or the dates does not make a
  hypothesis new.
- **The holdout is out of reach.** A spec that touches the sealed holdout
  is refused. The data store also truncates there.
- **Hypotheses from a language model** may only be judged on data after the
  model's declared training cutoff: a model that has read about a period
  cannot be tested on it.
- **Walk-forward.** For each judged fold, the model is fit only on rows
  whose OUTCOMES resolved before the fold began, minus an embargo. At
  most one position per instrument at a time; the next entry comes after
  the previous exit.
- **Baselines.** The unconditional R of the same template: 20 seeded draws
  of the same number of entries at random eligible rows and sides. When a
  different family is tested, the k-NN analogue family (the current system's
  estimator) is also run on the same folds.
- **Robustness.** Spread ×1.5 and slippage ×2, and a one-bar entry delay.
  A PASS needs a positive mean in every perturbation.
- **Isolation.** A PASS writes a frozen, hashed artifact under
  `research/artifacts/`, never under `models/artifacts/` where production
  loads. A FAIL writes no artifact. Promotion to production is a separate,
  reviewed step that needs the single-use holdout test.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from ..data import instruments
from ..data.bars import BarSeries
from ..data.resample import resample
from ..features.store import INDEX, NAMES, compute_matrix
from .features_lab import candidate
from .labels import BUY, SELL, TEMPLATE_BY_KEY, CostModel, compute_labels
from .models import MODEL_FAMILIES, MODELS_VERSION
from .registry import Registry, RegistryError, Trial, Use, Verdict

#: 1.1.0: M15 decisions and higher-timeframe context features ("H4:er120"); knn_baseline flag.
LAB_VERSION = "lab-1.1.0"
EMBARGO_DAYS = 5
PRODUCTION_ARTIFACTS = Path(__file__).resolve().parents[2] / "models" / "artifacts"
SOURCES = ("human", "scan", "reflection", "lesson", "feature", "llm")


class LabError(RegistryError):
    """The lab refused: the spec or the request would break research discipline."""


# ── the declared space ──────────────────────────────────────────────────


@dataclass(frozen=True)
class HypothesisSpace:
    universe: str
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...] = ("M15", "H1", "H4", "D1")
    base_features: tuple[str, ...] = NAMES
    allow_candidate_features: bool = True
    models: tuple[str, ...] = tuple(MODEL_FAMILIES)
    templates: tuple[str, ...] = tuple(TEMPLATE_BY_KEY)

    def check(self, spec: "HypothesisSpec") -> None:
        problems = []
        if spec.universe != self.universe:
            problems.append(f"universe {spec.universe!r} is not {self.universe!r}")
        problems += [f"instrument {s} not declared" for s in spec.symbols if s not in self.symbols]
        if spec.timeframe not in self.timeframes:
            problems.append(f"timeframe {spec.timeframe} not declared")
        for f in spec.features:
            if f in self.base_features:
                continue
            ctx = context_feature(f)
            if ctx is not None:  # "H1:er120" / "H4:ma_slope": a base feature on a closed higher-timeframe bar
                if ctx[1] not in self.base_features or not _higher(ctx[0], spec.timeframe):
                    problems.append(f"context feature {f}: needs a declared feature on a higher timeframe")
                continue
            if not self.allow_candidate_features:
                problems.append(f"feature {f} not declared")
                continue
            try:
                candidate(f)
            except ValueError as exc:
                problems.append(f"feature {f}: {exc}")
        if spec.model not in self.models:
            problems.append(f"model {spec.model} not declared")
        if spec.template not in self.templates:
            problems.append(f"template {spec.template} not declared")
        if problems:
            raise LabError("outside the declared hypothesis space: " + "; ".join(problems))


@dataclass(frozen=True)
class PassRules:
    min_trades: int = 200
    beat_random_t: float = 2.0
    min_positive_fold_share: float = 0.6
    robustness_mean_positive: bool = True


@dataclass(frozen=True)
class HypothesisSpec:
    id: str
    statement: str
    source: str
    universe: str
    symbols: tuple[str, ...]
    timeframe: str
    features: tuple[str, ...]
    model: str
    template: str
    fit_start: date
    judge_start: date
    judge_end: date  # exclusive
    threshold_r: float = 0.0  # trade only when the predicted R exceeds this; else NO_TRADE
    sides: tuple[int, ...] = (BUY, SELL)
    every: int = 4
    fold_days: int = 365
    llm_cutoff: date | None = None
    compare_features: tuple[str, ...] | None = None  # feature hypothesis: the base set it must beat
    rules: PassRules = PassRules()
    seed: int = 7
    knn_baseline: bool = True  # the k-NN comparison; impractical (quadratic) on M15-sized data

    def __post_init__(self) -> None:
        if self.source not in SOURCES:
            raise LabError(f"source must be one of {SOURCES}")
        if not self.fit_start < self.judge_start < self.judge_end:
            raise LabError("need fit_start < judge_start < judge_end")
        if not self.features:
            raise LabError("a hypothesis needs at least one feature")

    def substance(self) -> str:
        """What the hypothesis IS; a threshold or date change does not make it new."""
        core = {"universe": self.universe, "symbols": sorted(self.symbols), "timeframe": self.timeframe,
                "features": sorted(self.features), "model": self.model, "template": self.template,
                "sides": sorted(self.sides), "compare": sorted(self.compare_features or ())}
        return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:16]

    def to_json(self) -> dict:
        d = asdict(self)
        for k in ("fit_start", "judge_start", "judge_end", "llm_cutoff"):
            d[k] = d[k].isoformat() if d[k] else None
        return d

    @classmethod
    def from_json(cls, d: dict) -> "HypothesisSpec":
        d = dict(d)
        for k in ("fit_start", "judge_start", "judge_end", "llm_cutoff"):
            d[k] = date.fromisoformat(d[k]) if d.get(k) else None
        for k in ("symbols", "features", "sides"):
            d[k] = tuple(d[k])
        d["compare_features"] = tuple(d["compare_features"]) if d.get("compare_features") else None
        d["rules"] = PassRules(**d["rules"])
        return cls(**d)


_TF_SECONDS = {"M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}


def context_feature(f: str) -> tuple[str, str] | None:
    """("H4", "er120") for "H4:er120": a base feature read on the last CLOSED bar of a higher timeframe."""
    if ":" not in f:
        return None
    tf, name = f.split(":", 1)
    return (tf, name) if tf in _TF_SECONDS and name in INDEX else None


def _higher(tf: str, decision_tf: str) -> bool:
    return _TF_SECONDS.get(tf, 0) > _TF_SECONDS.get(decision_tf, 10 ** 9)


def _epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


# ── the lab ─────────────────────────────────────────────────────────────


class ResearchLab:
    def __init__(self, registry: Registry, space: HypothesisSpace, artifacts_dir: Path | str,
                 clock=None) -> None:
        self.registry, self.space = registry, space
        self.artifacts_dir = Path(artifacts_dir).resolve()
        if self.artifacts_dir == PRODUCTION_ARTIFACTS or PRODUCTION_ARTIFACTS in self.artifacts_dir.parents:
            raise LabError("the lab never writes where production loads (models/artifacts)")
        self.clock = clock or (lambda: datetime.now(timezone.utc).replace(microsecond=0))

    # 1. register ---------------------------------------------------------

    def register(self, spec: HypothesisSpec) -> Trial:
        self.space.check(spec)
        if spec.source == "llm":
            if spec.llm_cutoff is None:
                raise LabError("a language-model hypothesis must declare the model's training cutoff")
            if spec.fit_start < spec.llm_cutoff:
                raise LabError(f"a language-model hypothesis cannot be fit or judged on data before the "
                               f"model's training cutoff ({spec.llm_cutoff}): it may have read what happened")
        h = self.registry.holdout
        if h is not None and h.universe == spec.universe and spec.judge_end > h.start:
            raise LabError(f"the sealed holdout starts {h.start}; the lab never touches it")
        for t in self.registry.trials:
            if t.design.get("substance") == spec.substance() and self.registry.status_of(t.id) == "FAILED":
                raise LabError(f"{t.id} already tested this hypothesis and FAILED; a variation of its "
                               f"threshold, cadence or dates is not a new hypothesis")
        threshold = self.registry.threshold_for_next(spec.universe, spec.judge_start, spec.judge_end)
        n_config = 2 if spec.compare_features else 1
        trial = Trial(
            id=spec.id, registered=self.clock(), title=spec.statement[:120], hypothesis=spec.statement,
            uses=(Use(spec.universe, spec.fit_start, spec.judge_start, "fit"),
                  Use(spec.universe, spec.judge_start, spec.judge_end, "judge")),
            tests=1, configurations=n_config, preregistration=f"lab:{spec.substance()}",
            design={"lab": LAB_VERSION, "models": MODELS_VERSION, "spec": spec.to_json(),
                    "substance": spec.substance(), "threshold_t": round(threshold, 4)})
        return self.registry.register(trial)

    # 2. run --------------------------------------------------------------

    def run(self, trial_id: str, series: dict[str, BarSeries], record: bool = True) -> dict:
        try:
            trial = self.registry.get(trial_id)
        except KeyError:
            raise LabError(f"{trial_id} is not registered: nothing is evaluated before it is") from None
        if self.registry.status_of(trial_id) != "PENDING":
            raise LabError(f"{trial_id} already has a verdict; a trial is judged once")
        spec = HypothesisSpec.from_json(trial.design["spec"])
        threshold_t = float(trial.design["threshold_t"])
        costs = CostModel()
        data = self._dataset(spec, series, costs, delay=0)
        main = self._walk_forward(spec, data, spec.features)
        result = {"trial": trial_id, "lab": LAB_VERSION, "spec": spec.to_json(), "threshold_t": threshold_t,
                  "system": main["stats"], "folds": main["folds"], "by_symbol": main["by_symbol"]}
        rnd = self._random_baseline(spec, data, main)
        result["random"] = rnd
        result["vs_random_welch_t"] = _welch(main["r"], rnd["r_all"])
        if spec.model != "knn" and spec.knn_baseline:
            knn = self._walk_forward(replace(spec, model="knn"), data, spec.features)
            result["knn_baseline"] = knn["stats"]
            result["vs_knn_welch_t"] = _welch(main["r"], knn["r"])
        if spec.compare_features:
            base = self._walk_forward(spec, data, spec.compare_features)
            result["without_candidates"] = base["stats"]
            result["vs_base_welch_t"] = _welch(main["r"], base["r"])
        result["robustness"] = {}
        for name, c, d in (("costs_x1.5_slip_x2", replace(costs, spread_multiple=1.5, slippage_pips=costs.slippage_pips * 2), 0),
                           ("one_bar_delay", costs, 1)):
            pert = self._walk_forward(spec, self._dataset(spec, series, c, delay=d), spec.features)
            result["robustness"][name] = pert["stats"]
        result["verdict"], result["checks"] = self._judge(spec, result, threshold_t)
        result["result_hash"] = hashlib.sha256(json.dumps(
            {k: result[k] for k in ("system", "folds", "random", "robustness")}, sort_keys=True, default=str
        ).encode()).hexdigest()[:16]
        if record:
            self.registry.record_verdict(Verdict(trial_id, self.clock(),
                                                 "PASSED" if result["verdict"] == "PASS" else "FAILED",
                                                 {k: result[k] for k in ("verdict", "checks", "system", "result_hash")}))
            if result["verdict"] == "PASS":
                result["artifact"] = str(self._freeze(spec, data, result))
        return result

    # 3. data -------------------------------------------------------------

    def _dataset(self, spec: HypothesisSpec, series: dict[str, BarSeries], costs: CostModel, delay: int) -> dict:
        cands = {f: candidate(f) for f in set(spec.features) | set(spec.compare_features or ())
                 if f not in INDEX and context_feature(f) is None}
        ctx_feats = [f for f in set(spec.features) | set(spec.compare_features or ()) if context_feature(f)]
        out = {}
        for sym in spec.symbols:
            s = series[sym]
            if spec.timeframe != s.timeframe:
                s = resample(s, spec.timeframe, as_of=int(s.available_at[-1]))
            m = compute_matrix(s)
            cols = {n: m[:, INDEX[n]] for n in NAMES}
            for f, c in cands.items():
                cols[f] = c.column(m)
            htf = {}
            for f in ctx_feats:
                tf, name = context_feature(f)
                if tf not in htf:
                    h = resample(s, tf, as_of=int(s.available_at[-1]))
                    k = np.searchsorted(h.available_at, s.available_at, side="right") - 1  # last CLOSED bar
                    htf[tf] = (compute_matrix(h), k)
                hm, k = htf[tf]
                col = np.full(len(s), np.nan)
                ok = k >= 0
                col[ok] = hm[k[ok], INDEX[name]]
                cols[f] = col
            rows = np.arange(0, len(s), spec.every)
            lab = compute_labels(s, instruments.get(sym).pip, rows=rows, costs=costs, delay_bars=delay)
            out[sym] = {"cols": cols, "rows": rows, "t": s.available_at[rows], "labels": lab}
        return out

    def _xy(self, spec, data, feats, side):
        X, y, t, rt, ex, sym = [], [], [], [], [], []
        for s, d in data.items():
            o = d["labels"].outcomes[(spec.template, side)]
            X.append(np.column_stack([d["cols"][f][d["rows"]] for f in feats]))
            y.append(o.r); t.append(d["t"]); rt.append(o.resolve_time); ex.append(o.exit_index)
            sym += [s] * len(d["rows"])
        return (np.vstack(X), np.concatenate(y), np.concatenate(t), np.concatenate(rt),
                np.concatenate(ex), np.array(sym))

    # 4. walk-forward -----------------------------------------------------

    def _walk_forward(self, spec: HypothesisSpec, data: dict, feats: tuple[str, ...]) -> dict:
        fit = MODEL_FAMILIES[spec.model]
        start, end = _epoch(spec.judge_start), _epoch(spec.judge_end)
        embargo = EMBARGO_DAYS * 86400
        preds, sets = {}, {}
        for side in spec.sides:
            X, y, t, rt, ex, sym = self._xy(spec, data, feats, side)
            sets[side] = (X, y, t, rt, sym)
            preds[side] = np.full(len(y), np.nan)
            f0 = start
            while f0 < end:
                f1 = min(end, f0 + spec.fold_days * 86400)
                # Train only on rows decided in the fit window or later, whose outcome
                # RESOLVED before the fold began minus an embargo: no overlap with the fold.
                train = (t >= _epoch(spec.fit_start)) & (rt >= 0) & (rt < f0 - embargo) & np.isfinite(y)
                test = (t >= f0) & (t < f1)
                if train.sum() >= 50 and test.any():
                    preds[side][test] = fit(X[train], y[train]).predict(X[test])
                f0 = f1
        # Trade selection: best side above threshold; one position per instrument at a time.
        X0, y0, t0, rt0, sym0 = sets[spec.sides[0]]
        taken_r, taken_t, taken_sym, taken_side = [], [], [], []
        busy_until: dict[str, float] = {}
        order = np.argsort(t0, kind="stable")
        for i in order:
            if not (start <= t0[i] < end):
                continue
            best, side_best = -np.inf, None
            for side in spec.sides:
                p = preds[side][i]
                if np.isfinite(p) and p > spec.threshold_r and p > best:
                    best, side_best = p, side
            if side_best is None or t0[i] < busy_until.get(sym0[i], -1):
                continue
            r = sets[side_best][1][i]
            if not np.isfinite(r):
                continue
            taken_r.append(r); taken_t.append(t0[i]); taken_sym.append(sym0[i]); taken_side.append(side_best)
            busy_until[sym0[i]] = sets[side_best][3][i]
        r = np.array(taken_r)
        folds, f0 = [], start
        tt = np.array(taken_t)
        while f0 < end:
            f1 = min(end, f0 + spec.fold_days * 86400)
            sel = (tt >= f0) & (tt < f1) if len(tt) else np.array([], bool)
            folds.append({"start": datetime.fromtimestamp(f0, timezone.utc).date().isoformat(),
                          "n": int(sel.sum()), "mean_R": round(float(r[sel].mean()), 4) if sel.any() else None})
            f0 = f1
        by_symbol = {}
        for s in spec.symbols:
            sel = np.array(taken_sym) == s if taken_sym else np.array([], bool)
            by_symbol[s] = {"n": int(sel.sum()), "mean_R": round(float(r[sel].mean()), 4) if sel.any() else None}
        return {"r": r, "stats": _stats(r), "folds": folds, "by_symbol": by_symbol,
                "sides": taken_side, "t": taken_t, "symbols": taken_sym}

    def _random_baseline(self, spec: HypothesisSpec, data: dict, main: dict) -> dict:
        """20 draws of the same NUMBER of entries at random eligible rows with a random side
        (with replacement; no position overlap is enforced, so it is a baseline of the
        unconditional R distribution, not a simulated account)."""
        rng = np.random.default_rng(spec.seed)
        start, end = _epoch(spec.judge_start), _epoch(spec.judge_end)
        pools = []
        for side in spec.sides:
            X, y, t, rt, ex, sym = self._xy(spec, data, spec.features, side)
            ok = (t >= start) & (t < end) & np.isfinite(y)
            pools.append((y[ok], t[ok], rt[ok], sym[ok]))
        n = len(main["r"])
        runs = []
        for _ in range(20):
            out = []
            for k in range(n):
                y, t, rt, sym = pools[rng.integers(len(pools))]
                if len(y):
                    out.append(float(y[rng.integers(len(y))]))
            runs.append(out)
        r_all = np.array([x for run in runs for x in run])
        return {"r_all": r_all, "stats": _stats(r_all), "runs": 20}

    # 0. observe ----------------------------------------------------------

    def scan(self, scan_id: str, series: dict[str, BarSeries], *, universe: str, symbols: tuple[str, ...],
             timeframe: str, template: str, fit_start: date, fit_end: date,
             features: tuple[str, ...] | None = None, every: int = 4, alpha: float = 0.05) -> dict:
        """OBSERVE on fit data only: which declared features carry information about outcomes?

        Spearman rank correlation of each feature with the realised R of each
        side, on rows decided AND resolved inside [fit_start, fit_end), and
        NON-OVERLAPPING: per instrument, a row counts only if it was decided
        after the previous counted row's outcome resolved. Overlapping
        outcomes share most of their path, so counting them as independent
        inflates t; a random walk then shows "significant" hour effects. The
        family-wise error is controlled by Bonferroni over every
        (feature, side) scanned. The scan is registered as exposure of the
        fit period (tests = 0: it judges nothing), so a later judge on the
        same data is visible. It returns observations and unregistered DRAFT
        specs, nothing else.
        """
        from statistics import NormalDist

        feats = tuple(features or self.space.base_features)
        probe = HypothesisSpec(scan_id, "scan", "scan", universe, symbols, timeframe, feats, "ridge", template,
                               fit_start, fit_end, fit_end + timedelta(days=1), every=every)
        self.space.check(probe)
        h = self.registry.holdout
        if h is not None and h.universe == universe and fit_end > h.start:
            raise LabError("a scan never touches the sealed holdout")
        n_tests = len(feats) * 2
        self.registry.register(Trial(
            id=scan_id, registered=self.clock(), title=f"information scan {timeframe} {template}",
            hypothesis="observation only: which declared features relate to outcomes on fit data",
            uses=(Use(universe, fit_start, fit_end, "fit"),), tests=0, configurations=n_tests,
            design={"lab": LAB_VERSION, "kind": "scan", "features": list(feats), "alpha": alpha}))
        data = self._dataset(probe, series, CostModel(), delay=0)
        z_crit = NormalDist().inv_cdf(1 - alpha / (2 * n_tests))
        f0, f1 = _epoch(fit_start), _epoch(fit_end)
        obs = []
        for side in (BUY, SELL):
            X, y, t, rt, ex, sym = self._xy(probe, data, feats, side)
            ok = (t >= f0) & (rt >= 0) & (rt < f1) & np.isfinite(y)
            ok &= _non_overlapping(t, rt, sym)
            for j, f in enumerate(feats):
                x = X[ok, j]
                m = np.isfinite(x)
                n = int(m.sum())
                if n < 100:
                    continue
                rx = np.argsort(np.argsort(x[m])).astype(float)
                ry = np.argsort(np.argsort(y[ok][m])).astype(float)
                rho = float(np.corrcoef(rx, ry)[0, 1]) if rx.std() > 0 and ry.std() > 0 else 0.0
                tstat = rho * np.sqrt(max(n - 2, 1) / max(1e-12, 1 - rho * rho))
                obs.append({"feature": f, "side": "BUY" if side == BUY else "SELL", "n": n,
                            "spearman": round(rho, 4), "t": round(float(tstat), 3),
                            "significant": bool(abs(tstat) > z_crit)})
        obs.sort(key=lambda o: -abs(o["t"]))
        return {"scan": scan_id, "tests": n_tests, "z_critical": round(z_crit, 3),
                "observations": obs, "significant": [o for o in obs if o["significant"]]}

    def draft_from_scan(self, scan: dict, *, id_prefix: str, universe: str, symbols: tuple[str, ...],
                        timeframe: str, template: str, fit_start: date, judge_start: date, judge_end: date,
                        model: str = "ridge") -> list[HypothesisSpec]:
        """One unregistered draft per significant feature: an observation, stated as a testable claim."""
        out = []
        for i, o in enumerate(scan["significant"]):
            out.append(HypothesisSpec(
                f"{id_prefix}-{i + 1}", f"{o['feature']} predicts {template} {o['side']} outcomes "
                f"(fit-period Spearman {o['spearman']:+.3f}, t {o['t']:+.2f})", "scan", universe, symbols,
                timeframe, (o["feature"],), model, template, fit_start, judge_start, judge_end))
        return out

    # 5. judge, freeze ----------------------------------------------------

    def _judge(self, spec: HypothesisSpec, res: dict, threshold_t: float) -> tuple[str, dict]:
        s, rules = res["system"], spec.rules
        filled = [f for f in res["folds"] if f["n"]]
        pos = sum(1 for f in filled if f["mean_R"] > 0)
        checks = {
            "mean_R_positive": bool(s["n"] and s["mean_R"] > 0),
            "t_above_registry_threshold": bool(s.get("t") is not None and s["t"] > threshold_t),
            "min_trades": s["n"] >= rules.min_trades,
            "beats_random": bool(res["vs_random_welch_t"] is not None and res["vs_random_welch_t"] > rules.beat_random_t),
            "positive_fold_share": bool(filled and pos / len(filled) >= rules.min_positive_fold_share),
            "robust": all(v["n"] and v["mean_R"] > 0 for v in res["robustness"].values()),
        }
        if spec.compare_features:
            checks["beats_without_candidates"] = bool(res.get("vs_base_welch_t") is not None
                                                      and res["vs_base_welch_t"] > threshold_t)
        return ("PASS" if all(checks.values()) else "FAIL"), checks

    def _freeze(self, spec: HypothesisSpec, data: dict, result: dict) -> Path:
        """Refit on everything before judge_end (never past it) and write a hashed artifact."""
        fit = MODEL_FAMILIES[spec.model]
        end = _epoch(spec.judge_end)
        models = {}
        for side in spec.sides:
            X, y, t, rt, ex, sym = self._xy(spec, data, spec.features, side)
            train = (t >= _epoch(spec.fit_start)) & (rt >= 0) & (rt < end) & np.isfinite(y)
            models[str(side)] = fit(X[train], y[train]).to_json()
        body = {"trial": spec.id, "spec": spec.to_json(), "models": models, "features": list(spec.features),
                "result_hash": result["result_hash"], "status": "RESEARCH_CANDIDATE",
                "note": "PASSED in the lab. Not VALIDATED: that needs the robustness review and the single-use "
                        "holdout test. Production does not load from this directory."}
        raw = json.dumps(body, sort_keys=True, default=str).encode()
        body["sha256"] = hashlib.sha256(raw).hexdigest()
        out = self.artifacts_dir / spec.id
        out.mkdir(parents=True, exist_ok=True)
        (out / "artifact.json").write_text(json.dumps(body, indent=1, default=str))
        return out / "artifact.json"


def _non_overlapping(t: np.ndarray, rt: np.ndarray, sym: np.ndarray) -> np.ndarray:
    """Per instrument, keep a row only if it was decided after the previous kept row resolved."""
    keep = np.zeros(len(t), bool)
    last: dict[str, float] = {}
    for i in np.argsort(t, kind="stable"):
        if rt[i] < 0:
            continue
        if t[i] >= last.get(sym[i], -np.inf):
            keep[i] = True
            last[sym[i]] = rt[i]
    return keep


def _stats(r: np.ndarray) -> dict:
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return {"n": 0, "mean_R": None, "t": None, "win_rate": None}
    sd = float(r.std(ddof=1)) if n > 1 else 0.0
    return {"n": n, "mean_R": round(float(r.mean()), 4),
            "t": round(float(r.mean() / (sd / math.sqrt(n))), 3) if sd > 0 else None,
            "win_rate": round(float((r > 0).mean()), 4)}


def _welch(a: np.ndarray, b: np.ndarray) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return None
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return round(float((a.mean() - b.mean()) / se), 3) if se > 0 else None
