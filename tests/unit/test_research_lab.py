"""The research lab, feature lab, model families and hypothesis sources.

Every market here is built so the right answer is known: a planted trend
the lab must find, and a random walk it must reject.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from aitrader.backtest.runner import epoch
from aitrader.data.bars import BarSeries
from aitrader.features.store import INDEX
from aitrader.llm.provider import LLMClient, LLMConfig
from aitrader.research import features_lab as fl
from aitrader.research.hypotheses import llm_drafts, proposals_from_reflection
from aitrader.research.lab import HypothesisSpace, HypothesisSpec, LabError, PassRules, ResearchLab
from aitrader.research.models import fit_knn, fit_logistic, fit_ridge
from aitrader.research.registry import Holdout, Registry, Trial, Use

SYMS = ("EURUSD", "GBPUSD")
SPACE = HypothesisSpace("synthetic", SYMS)


def market(symbol, n, seed, base, drift_size, block=300):
    rng = np.random.default_rng(seed)
    drift = np.repeat(rng.choice([-1, 1], size=n // block + 1) * drift_size, block)[:n]
    mid = base * np.exp(np.cumsum(drift + rng.normal(0, 0.0009, n)))
    o = np.concatenate(([mid[0]], mid[:-1]))
    wick = np.abs(rng.normal(0, 0.0004, n)) * base
    hi, lo = np.maximum(o, mid) + wick, np.minimum(o, mid) - wick
    spread = base * 0.00008 * np.ones(n)
    h = spread / 2
    return BarSeries.from_columns(symbol, "H1", "synthetic", open_time=epoch(2009, 1, 5) + 3600 * np.arange(n),
                                  bid_open=o - h, bid_high=hi - h, bid_low=lo - h, bid_close=mid - h,
                                  ask_open=o + h, ask_high=hi + h, ask_low=lo + h, ask_close=mid + h,
                                  ticks=rng.integers(100, 900, n), spread_mean=spread, spread_max=spread * 2)


@pytest.fixture(scope="module")
def planted():
    return {"EURUSD": market("EURUSD", 9000, 1, 1.3, 0.0004), "GBPUSD": market("GBPUSD", 9000, 2, 1.5, 0.0004)}


@pytest.fixture(scope="module")
def walk():
    return {"EURUSD": market("EURUSD", 9000, 1, 1.3, 0.0), "GBPUSD": market("GBPUSD", 9000, 2, 1.5, 0.0)}


def spec(id_="h1", **kw):
    base = dict(id=id_, statement="24-bar momentum predicts the next move", source="human", universe="synthetic",
                symbols=SYMS, timeframe="H1", features=("r24", "r120"), model="ridge", template="T1",
                fit_start=date(2009, 1, 5), judge_start=date(2009, 5, 1), judge_end=date(2009, 12, 31),
                fold_days=60, rules=PassRules(min_trades=60))
    base.update(kw)
    return HypothesisSpec(**base)


def lab(tmp_path, registry=None, clock=None):
    reg = registry or Registry(tmp_path / "registry.jsonl")
    return ResearchLab(reg, SPACE, tmp_path / "artifacts", clock=clock)


# ── model families ──────────────────────────────────────────────────────


def test_model_families_recover_relationships_known_by_construction():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(3000, 3))
    y = 0.8 * X[:, 0] - 0.4 * X[:, 1] + rng.normal(0, 0.3, 3000)
    ridge = fit_ridge(X, y)
    w = ridge.params["w"]
    assert w[0] > 0.5 and w[1] < -0.2 and abs(w[2]) < 0.05
    q = np.array([[2.0, 0, 0], [-2.0, 0, 0]])
    assert ridge.predict(q)[0] > ridge.predict(q)[1]
    assert fit_logistic(X, y).predict(q)[0] > fit_logistic(X, y).predict(q)[1]
    assert fit_knn(X, y, k=50).predict(q)[0] > fit_knn(X, y, k=50).predict(q)[1]
    assert json.dumps(ridge.to_json())  # a frozen artifact is plain data


# ── the lab: known answers ──────────────────────────────────────────────


def test_the_lab_finds_a_planted_edge_and_rejects_a_random_walk(tmp_path, planted, walk):
    lb = lab(tmp_path)
    lb.register(spec("planted"))
    res = lb.run("planted", planted)
    assert res["verdict"] == "PASS" and all(res["checks"].values())
    assert res["system"]["mean_R"] > 0.3 and res["vs_random_welch_t"] > 5
    assert Path(res["artifact"]).exists()
    assert lb.registry.status_of("planted") == "PASSED"

    lb.register(spec("walk"))
    res = lb.run("walk", walk)
    assert res["verdict"] == "FAIL" and not res["checks"]["mean_R_positive"]
    assert "artifact" not in res and not (tmp_path / "artifacts" / "walk").exists()
    assert lb.registry.status_of("walk") == "FAILED"


def test_nothing_is_evaluated_before_it_is_registered_and_a_trial_is_judged_once(tmp_path, walk):
    lb = lab(tmp_path)
    with pytest.raises(LabError, match="not registered"):
        lb.run("never-registered", walk)
    lb.register(spec("once"))
    lb.run("once", walk)
    with pytest.raises(LabError, match="judged once"):
        lb.run("once", walk)


@pytest.mark.parametrize("change,match", [
    (dict(features=("r24", "not_a_feature")), "not_a_feature"),
    (dict(model="deep_net"), "model deep_net"),
    (dict(template="T9"), "template T9"),
    (dict(symbols=("EURUSD", "XAUUSD")), "XAUUSD"),
    (dict(features=("zscore(r24,50)",)), "outside the declared grid"),
    (dict(timeframe="M1"), "timeframe M1"),
])
def test_a_spec_outside_the_declared_space_is_refused(tmp_path, change, match):
    with pytest.raises(LabError, match=match):
        lab(tmp_path).register(spec(**change))


def test_a_failed_hypothesis_cannot_be_rescued_by_changing_its_threshold_or_dates(tmp_path, walk):
    lb = lab(tmp_path)
    lb.register(spec("try1"))
    assert lb.run("try1", walk)["verdict"] == "FAIL"
    for i, change in enumerate([dict(threshold_r=0.2), dict(every=2), dict(judge_start=date(2009, 6, 1))]):
        with pytest.raises(LabError, match="already tested"):
            lb.register(spec(f"rescue{i}", **change))
    lb.register(spec("genuinely-new", features=("er120",)))  # a different hypothesis is allowed, and counted


def test_the_threshold_is_frozen_at_registration_and_rises_with_every_prior_test(tmp_path):
    reg = Registry(tmp_path / "r.jsonl")
    t0 = datetime(2026, 9, 27, tzinfo=timezone.utc)
    for i in range(9):
        reg.register(Trial(f"prior{i}", t0, "p", "p", (Use("synthetic", date(2009, 1, 1), date(2010, 1, 1), "judge"),),
                           tests=1, configurations=1))
    lb = ResearchLab(reg, SPACE, tmp_path / "a", clock=lambda: t0.replace(hour=1))
    trial = lb.register(spec("tenth"))
    assert trial.design["threshold_t"] == pytest.approx(2.807, abs=0.01)  # Bonferroni over 10 tests
    assert trial.tests == 1 and trial.uses[1].role == "judge"


def test_language_model_hypotheses_cannot_be_judged_before_the_model_cutoff(tmp_path):
    lb = lab(tmp_path)
    with pytest.raises(LabError, match="training cutoff"):
        lb.register(spec("llm-no-cutoff", source="llm"))
    with pytest.raises(LabError, match="may have read"):
        lb.register(spec("llm-old", source="llm", llm_cutoff=date(2025, 1, 1)))
    lb.register(spec("llm-forward", source="llm", llm_cutoff=date(2009, 1, 1)))  # data after the cutoff only


def test_the_sealed_holdout_is_out_of_reach_of_specs_and_scans(tmp_path, walk):
    h = Holdout("synthetic", date(2009, 10, 1), datetime(2026, 9, 1, tzinfo=timezone.utc), "test seal")
    lb = lab(tmp_path, Registry(tmp_path / "r.jsonl", h))
    with pytest.raises(LabError, match="holdout"):
        lb.register(spec("into-holdout"))
    with pytest.raises(LabError, match="holdout"):
        lb.scan("scan-into", walk, universe="synthetic", symbols=SYMS, timeframe="H1", template="T1",
                fit_start=date(2009, 1, 5), fit_end=date(2009, 12, 1))


def test_results_are_reproducible_from_the_registered_spec(tmp_path, planted):
    hashes = []
    for k in range(2):
        lb = lab(tmp_path / str(k))
        lb.register(spec("repro"))
        hashes.append(lb.run("repro", planted, record=False)["result_hash"])
    assert hashes[0] == hashes[1]


def test_the_lab_never_writes_where_production_loads(tmp_path):
    from aitrader.research.lab import PRODUCTION_ARTIFACTS
    with pytest.raises(LabError, match="never writes where production loads"):
        ResearchLab(Registry(tmp_path / "r.jsonl"), SPACE, PRODUCTION_ARTIFACTS)
    with pytest.raises(LabError, match="never writes where production loads"):
        ResearchLab(Registry(tmp_path / "r.jsonl"), SPACE, PRODUCTION_ARTIFACTS / "sub")


def test_walk_forward_trains_only_on_outcomes_resolved_before_each_fold(tmp_path, planted):
    """Corrupt every outcome that resolves after the first fold begins: that fold's choices must not change."""
    from aitrader.research.labels import CostModel
    lb = lab(tmp_path)
    s = spec("wf")
    data = lb._dataset(s, planted, CostModel(), 0)
    full = lb._walk_forward(s, data, s.features)
    fold_start = datetime(2009, 5, 1, tzinfo=timezone.utc).timestamp()
    fold_end = fold_start + 60 * 86400
    for d in data.values():
        for o in d["labels"].outcomes.values():
            o.r[o.resolve_time >= fold_start] = 100.0  # a future the first fold must never learn from
    again = lb._walk_forward(s, data, s.features)
    first = [t for t in full["t"] if t < fold_end]
    assert len(first) > 10
    assert [t for t in again["t"] if t < fold_end] == first
    assert again["t"] != full["t"]  # later folds DO learn from outcomes that resolved before them


# ── features: a declared grammar and the leakage gate ───────────────────


def test_the_feature_grammar_is_finite_and_countable():
    cands = fl.enumerate_candidates(("r24", "er120", "vol_ratio"))
    assert len(cands) == 3 * (3 + 2 + 2) + 2 * 3  # diff/zscore/rank grids + ratio/product pairs
    assert len(set(cands)) == len(cands)
    with pytest.raises(ValueError, match="grammar"):
        fl.candidate("fourier(r24,5)")


def test_the_leakage_gate_rejects_a_leaky_feature_and_admits_a_causal_one(walk):
    s = walk["EURUSD"].take(slice(0, 1500))
    assert fl.leakage_gate(fl.candidate("zscore(r24,24)"), s)["status"] == "ELIGIBLE"
    leak = fl.CandidateFeature("next_bar_change", lambda m: np.roll(m[:, INDEX["r1"]], -1))
    rep = fl.leakage_gate(leak, s)
    assert rep["status"] == "REJECTED_LEAKAGE" and rep["violations"]


def test_a_feature_hypothesis_is_judged_by_its_incremental_value(tmp_path, planted):
    lb = lab(tmp_path)
    lb.register(spec("feat", features=("hour_sin", "diff(r120,24)"), compare_features=("hour_sin",), source="feature"))
    res = lb.run("feat", planted)
    assert res["without_candidates"]["mean_R"] is None or res["without_candidates"]["mean_R"] < res["system"]["mean_R"]
    assert "beats_without_candidates" in res["checks"]
    assert lb.registry.get("feat").configurations == 2  # both sets were evaluated, and both are counted


# ── hypothesis sources ──────────────────────────────────────────────────


def test_the_scan_finds_the_planted_relationship_on_fit_data_only_and_is_recorded(tmp_path, planted, walk):
    lb = lab(tmp_path)
    kw = dict(universe="synthetic", symbols=SYMS, timeframe="H1", template="T1",
              fit_start=date(2009, 1, 5), fit_end=date(2009, 5, 1), features=("r24", "hour_sin", "er24"))
    found = lb.scan("scan-planted", planted, **kw)
    assert any(o["feature"] == "r24" for o in found["significant"])
    assert found["z_critical"] > 2.5  # Bonferroni over 6 tests
    trial = lb.registry.get("scan-planted")
    assert trial.tests == 0 and [u.role for u in trial.uses] == ["fit"]
    drafts = lb.draft_from_scan(found, id_prefix="from-scan", universe="synthetic", symbols=SYMS, timeframe="H1",
                                template="T1", fit_start=date(2009, 1, 5), judge_start=date(2009, 5, 1),
                                judge_end=date(2009, 12, 31))
    assert drafts and all(d.source == "scan" for d in drafts)
    assert all(d.id not in [t.id for t in lb.registry.trials] for d in drafts)  # drafts are NOT registered
    nothing = lb.scan("scan-walk", walk, **kw)
    # On a random walk no PRICE feature predicts outcomes. The hour may: labels charge swap per
    # New York close crossed, so the entry hour changes the cost of BOTH sides alike. That is a real
    # cost relationship, and the scan is right to report it.
    assert not [o for o in nothing["significant"] if o["feature"] in ("r24", "er24")]
    hour = [o for o in nothing["significant"] if o["feature"] == "hour_sin"]
    assert all(o["spearman"] > 0 for o in hour)  # same sign for BUY and SELL: a cost, not a direction


def test_reflection_becomes_structured_proposals_that_change_nothing():
    refl = {"t": 1, "hypotheses": [{"kind": "REPEATED_MISTAKE", "cause": "ENTRY_TIMING", "text": "x"},
                                   {"kind": "OBJECTION_UNINFORMATIVE", "code": "LATE_ENTRY", "text": "y"}],
            "by_family": {"BREAKOUT": {"n": 60, "mean": -0.3, "se": 0.1}, "TREND_PULLBACK": {"n": 5, "mean": -1, "se": 0.5}}}
    props = proposals_from_reflection(refl, {"L:a": [{"status": "VALIDATED"}]})
    kinds = sorted(p["kind"] for p in props)
    assert kinds == ["LESSON_OFFLINE", "MISTAKE_FEATURE", "OBJECTION_INFORMATION", "UNDERPERFORMING_CONTEXT"]
    assert all(p["status"] == "PROPOSED" and p["suggested_test"] for p in props)
    again = proposals_from_reflection(refl, {"L:a": [{"status": "VALIDATED"}]})
    assert [p["signature"] for p in props] == [p["signature"] for p in again]  # stable, so journalled once


def _llm(content):
    def t(url, headers, body, timeout):
        return {"choices": [{"message": {"content": content}}], "usage": {"total_tokens": 10}}
    return LLMClient(LLMConfig("openai_compatible", "https://example.test/v1", "k", "m1"), t)


def test_a_language_model_may_draft_hypotheses_only_from_the_closed_vocabulary(tmp_path):
    good = json.dumps({"hypotheses": [{"statement": "trend efficiency predicts", "features": ["er120"],
                                       "model": "logistic", "template": "T2"}]})
    kw = dict(id_prefix="llm", fit_start=date(2009, 1, 5), judge_start=date(2009, 5, 1),
              judge_end=date(2009, 12, 31), cutoff=date(2025, 6, 1))
    drafts = llm_drafts(_llm(good), SPACE, {"note": "fit-period observations"}, **kw)
    assert len(drafts) == 1 and drafts[0].source == "llm" and drafts[0].llm_cutoff == date(2025, 6, 1)
    with pytest.raises(LabError, match="training cutoff"):  # drafted on history the model may have read
        lab(tmp_path).register(drafts[0])
    bad = json.dumps({"hypotheses": [{"statement": "x", "features": ["secret_sauce"], "model": "ridge", "template": "T1"}]})
    assert llm_drafts(_llm(bad), SPACE, {}, **kw) == []
    assert llm_drafts(_llm("not json"), SPACE, {}, **kw) == []
