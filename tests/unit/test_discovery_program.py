"""The closed loop end to end on a market whose answer is known: preregister, run once, record.

Covers: registration before any outcome, refusal to run twice or to run changed design/code,
the holdout, leakage blocking, deterministic replay, resuming an interrupted run, a planted
edge found and validated, and an honest FAILED in a market with no edge."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from aitrader.research.discovery.battery import BatteryRules
from aitrader.research.discovery.catalog import FeatureCatalog, FeatureRecord
from aitrader.research.discovery.hypothesis import Ledger
from aitrader.research.discovery.program import DiscoveryProgram, ModelPlan, ProgramDesign, ProgramError
from aitrader.research.discovery.study import Segment
from aitrader.research.registry import Holdout, Registry
from tests.unit.discovery_market import SYMBOLS, planted

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
SEALED = datetime(2026, 1, 1, tzinfo=timezone.utc)
HOLDOUT = Holdout("synthetic", date(2012, 6, 1), SEALED, "test seal")
SEGS = (Segment("discovery", "fit", date(2010, 1, 11), date(2010, 10, 1)),
        Segment("validation", "select", date(2010, 10, 11), date(2011, 6, 1)),
        Segment("confirmation", "judge", date(2011, 6, 11), date(2012, 4, 1)))
N = 20_000


def record(name, kind="continuous"):
    return FeatureRecord(name, f"synthetic column {name}", "test", kind, "H1", ("synthetic bars",),
                         "tests/unit/discovery_market.py", "1", "known at the bar close by construction",
                         "planted or noise, by construction", "DP-T1")


RECORDS = {"A": record("A", "categorical"), "B": record("B"), "er120": record("er120"),
           "vol_ratio": record("vol_ratio")}


def passed(name):
    return [], 12, list(SYMBOLS)


def make_design(registry, **kw):
    d = ProgramDesign(
        id="DP-T1", title="planted-edge test", question="Does A=high predict a rise?", universe="synthetic",
        instruments=SYMBOLS, segments=SEGS, states=("B",), triggers=("A",), groups=(("A", ((0.0,), (1.0,), (2.0,))),),
        exits=("E1", "E2"), rules=BatteryRules(t_threshold=1.0, permutations=40, random_draws=4),
        holdout_start=HOLDOUT.start, screen_min_n=30, screen_keep=4, validation_min_n=30, finalists=2,
        model=ModelPlan(features=("A", "B"), quantiles=(0.975,), stride=1), feature_budget=6)
    d = replace(d, **kw)
    thr = registry.threshold_for_next(d.universe, d.segments[2].start, d.segments[2].end, new_tests=d.judged_tests())
    return replace(d, rules=replace(d.rules, t_threshold=thr))


def setup(tmp_path, **kw):
    reg = Registry.load(tmp_path / "registry.jsonl", HOLDOUT)
    d = make_design(reg, **kw)
    prog = DiscoveryProgram(d, reg, Ledger(tmp_path / "ledger.jsonl"), FeatureCatalog(tmp_path / "features.jsonl"),
                            tmp_path / "knowledge", lambda: NOW, RECORDS)
    return prog


def reopen(tmp_path, design, **kw):
    reg = Registry.load(tmp_path / "registry.jsonl", HOLDOUT)
    return DiscoveryProgram(design, reg, Ledger(tmp_path / "ledger.jsonl"), FeatureCatalog(tmp_path / "features.jsonl"),
                            tmp_path / "knowledge", lambda: NOW, RECORDS, **kw)


@pytest.fixture(scope="module")
def market():
    return planted(n=N)


@pytest.fixture(scope="module")
def completed(tmp_path_factory, market):
    tmp = tmp_path_factory.mktemp("prog")
    prog = setup(tmp)
    prog.preregister(tmp / "DP-T1.md", "DP-T1.md", passed)
    art = prog.run(market)
    return tmp, prog, art


def test_preregistration_records_everything_and_reads_no_outcome(tmp_path):
    prog = setup(tmp_path)
    trial = prog.preregister(tmp_path / "DP-T1.md", "DP-T1.md", passed)
    reg = Registry.load(tmp_path / "registry.jsonl", HOLDOUT)
    assert reg.status_of("DP-T1") == "PENDING" and trial.tests == 3
    assert [u.role for u in trial.uses] == ["fit", "select", "judge"]
    assert trial.configurations == prog.design.configurations() == 2 * 15 + 4 * 2 + 2 * 1 * 2 + 3
    doc = (tmp_path / "DP-T1.md").read_text()
    assert f"t >= {prog.design.rules.t_threshold:.4f}" in doc and "30 tests" in doc
    cat = FeatureCatalog(tmp_path / "features.jsonl")
    assert cat.budget("DP-T1") == (4, 6) and all(cat.leakage_status(r.id) == "PASSED" for r in RECORDS.values())
    assert Ledger(tmp_path / "ledger.jsonl").counts() == {} and not (tmp_path / "knowledge").exists()


def test_a_planted_edge_is_found_validated_and_recorded_everywhere(completed):
    tmp, prog, art = completed
    assert art["verdict"] == "PASSED" and art["validated"]
    led = Ledger(tmp / "ledger.jsonl")
    for hid in art["validated"]:
        h = led.get(hid)
        assert led.state(hid) == "VALIDATED" and h.side == "BUY"
        assert "A=high" in h.condition or h.condition.startswith("model:")
    assert art["screen"]["tests"] == 30 and art["screen"]["discoveries"] >= 1
    assert all(c["side"] == "BUY" for c in art["confirmation"] if c["board"]["verdict"] == "VALIDATED")
    reg = Registry.load(tmp / "registry.jsonl", HOLDOUT)
    v = reg.verdict_of("DP-T1")
    assert v.status == "PASSED" and v.result["artifact_sha256"] == art["sha256"]
    cat = FeatureCatalog(tmp / "features.jsonl")
    assert cat.experiments("A@1") == ["DP-T1"] and cat.results("A@1")[0]["result"]["validated"]
    for f in ("DP-T1.json", "DP-T1-screen.json", "DP-T1-trades.json", "DP-T1-model-BUY.json"):
        assert (tmp / "knowledge" / f).exists()
    assert all(k["status"].endswith("not a trading rule") for k in art["knowledge"])
    # the model family, trained on discovery with its threshold chosen on validation, finds it too
    assert "DP-T1-M1" in art["validated"] and art["model"]["finalist"]["side"] == "BUY"
    assert led.get("DP-T1-M1").condition == "model:DP-T1-M1:q0.975"


def test_a_program_runs_once(completed, market):
    tmp, prog, _ = completed
    with pytest.raises(ProgramError):
        reopen(tmp, prog.design).run(market)


def test_a_changed_design_or_changed_code_is_refused(tmp_path, market):
    prog = setup(tmp_path)
    prog.preregister(tmp_path / "DP-T1.md", "DP-T1.md", passed)
    with pytest.raises(ProgramError):
        reopen(tmp_path, replace(prog.design, screen_q=0.2)).run(market)
    with pytest.raises(ProgramError):
        reopen(tmp_path, prog.design, code_hash=lambda: "edited after registration").run(market)
    assert Registry.load(tmp_path / "registry.jsonl", HOLDOUT).status_of("DP-T1") == "PENDING"


def test_a_market_without_an_edge_fails_honestly(tmp_path):
    prog = setup(tmp_path)
    prog.preregister(tmp_path / "DP-T1.md", "DP-T1.md", passed)
    art = prog.run(planted(n=N, plant=False))
    assert art["verdict"] == "FAILED" and art["validated"] == [] and art["knowledge"] == []
    assert art["next_experiment"] and art["screen"]["tests"] == 30
    assert not (art["model"] or {}).get("finalist")  # the model finds nothing to pass validation either
    assert Registry.load(tmp_path / "registry.jsonl", HOLDOUT).verdict_of("DP-T1").status == "FAILED"


def test_replaying_the_same_run_gives_the_same_bytes(completed, tmp_path, market):
    tmp, _, art = completed
    prog = setup(tmp_path)
    prog.preregister(tmp_path / "DP-T1.md", "DP-T1.md", passed)
    again = prog.run(market)
    assert again == art
    for f in ("DP-T1.json", "DP-T1-screen.json", "DP-T1-trades.json"):
        assert (tmp_path / "knowledge" / f).read_bytes() == (tmp / "knowledge" / f).read_bytes()


def test_an_interrupted_run_resumes_to_the_same_result(completed, tmp_path, market):
    _, _, art = completed
    prog = setup(tmp_path)
    prog.preregister(tmp_path / "DP-T1.md", "DP-T1.md", passed)
    assert prog.run(market, stop_after="screen") == {"stopped_after": "screen"}
    assert reopen(tmp_path, prog.design).run(market, stop_after="validation") == {"stopped_after": "validation"}
    final = reopen(tmp_path, prog.design).run(market)  # a fresh process: everything reloaded from disk
    assert final == art
    lines = [json.loads(x) for x in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    drafts = [x["id"] for x in lines if x["event"] == "DRAFT"]
    assert len(drafts) == len(set(drafts))  # nothing drafted twice


def test_a_leaky_feature_stops_preregistration_and_is_remembered(tmp_path):
    prog = setup(tmp_path)

    def leaky(name):
        return ([123], 12, ["AAA"]) if name == "B" else passed(name)

    with pytest.raises(ProgramError):
        prog.preregister(tmp_path / "DP-T1.md", "DP-T1.md", leaky)
    assert not Registry.load(tmp_path / "registry.jsonl", HOLDOUT).trials
    assert FeatureCatalog(tmp_path / "features.jsonl").leakage_status("B@1") == "FAILED"
    assert not (tmp_path / "DP-T1.md").exists()


def test_the_judged_period_cannot_touch_the_holdout_and_the_threshold_is_the_registrys(tmp_path):
    reg = Registry.load(tmp_path / "registry.jsonl", HOLDOUT)
    late = (SEGS[0], SEGS[1], Segment("confirmation", "judge", date(2011, 6, 11), date(2012, 7, 1)))
    with pytest.raises(ProgramError):
        make_design(reg, segments=late).validate()
    prog = setup(tmp_path)
    soft = replace(prog.design, rules=replace(prog.design.rules, t_threshold=1.5))
    with pytest.raises(ProgramError):
        reopen(tmp_path, soft).preregister(tmp_path / "x.md", "x.md", passed)


def test_research_knowledge_never_goes_where_production_loads(tmp_path):
    reg = Registry.load(tmp_path / "registry.jsonl", HOLDOUT)
    with pytest.raises(ProgramError):
        DiscoveryProgram(make_design(reg), reg, Ledger(tmp_path / "l.jsonl"), FeatureCatalog(tmp_path / "f.jsonl"),
                         tmp_path / "models" / "artifacts", lambda: NOW, RECORDS)


def test_the_committed_dp001_design_is_the_one_the_code_builds():
    """While DP-001 is pending, the design the code builds must hash to the one in the registry, or
    the run would be refused; before registration it must at least be valid."""
    from pathlib import Path
    from aitrader.research.discovery.universe import dp001, dp001_as_registered, feature_records
    root = Path(__file__).resolve().parents[2]
    h = Holdout.load(root / "research" / "holdout.json")
    reg = Registry.load(root / "research" / "registry.jsonl", h)
    assert set(feature_records("DP-001")) >= set(dp001(reg).features())
    if not any(t.id == "DP-001" for t in reg.trials):
        dp001(reg).validate()
        return
    if reg.status_of("DP-001") == "PENDING":
        d = dp001_as_registered(reg)
        assert reg.get("DP-001").design["design_sha256"] == d.sha256()
