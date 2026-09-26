"""Learning: point-in-time experience, the lesson lifecycle, post-mortems, reflection."""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.learning.experience import Evaluation, ExperienceView, LessonPolicy
from aitrader.learning.review import postmortem, reflect


def ev(i, r, *, t=None, resolve=None, family="BREAKOUT", d=1, regime="RANGING", vol="NORMAL_VOL",
       objections=(), traded=True, pw=0.5, pr=0.05):
    t = t if t is not None else i * 100
    return Evaluation(f"d{i}", "EURUSD", t, resolve if resolve is not None else t + 50, family, "T1:BUY", d,
                      regime, vol, "LONDON", tuple(objections), traded, r, pr, pw)


def test_outcomes_join_the_statistics_only_after_they_resolve():
    x = ExperienceView()
    x.record(ev(1, -1.0, t=100, resolve=500))
    x.advance(400)
    assert x.family_regime_stats("BREAKOUT", "RANGING", 400) is None
    x.record(ev(2, -1.0, t=200, resolve=300))
    x.advance(600)
    assert x.family_regime_stats("BREAKOUT", "RANGING", 600)["n"] == 2


def test_querying_the_past_from_a_later_state_is_refused():
    x = ExperienceView()
    x.advance(1000)
    with pytest.raises(ValueError, match="after the view advanced"):
        x.family_regime_stats("BREAKOUT", "RANGING", 999)
    with pytest.raises(ValueError):
        x.advance(10)


def test_one_loss_or_one_win_changes_nothing():
    x = ExperienceView()
    x.record(ev(1, -1.0))
    x.advance(10_000)
    assert x.learn(10_000) == [] and x.lessons == {}


def _stream(x, start, n, mean, rng, **kw):
    for i in range(n):
        x.record(ev(start + i, float(mean + rng.normal(0, 0.8)), **kw))


def test_a_lesson_needs_discovery_then_out_of_sample_confirmation():
    rng = np.random.default_rng(0)
    x = ExperienceView(LessonPolicy(min_n=60, min_oos=40))
    _stream(x, 0, 120, -0.5, rng)             # a genuinely bad context
    x.advance(20_000)
    created = x.learn(20_000)
    assert [c["status"] for c in created] == ["CANDIDATE"]
    lid = created[0]["lesson_id"]
    # Not yet acting: candidates never block.
    assert x.lessons_matching("BREAKOUT", "RANGING", "NORMAL_VOL", 1, 20_000) == []
    _stream(x, 300, 60, -0.5, rng)            # new, later evidence
    x.advance(40_000)
    changes = x.learn(40_000)
    assert [c["status"] for c in changes] == ["VALIDATED"]
    active = x.lessons_matching("BREAKOUT", "RANGING", "NORMAL_VOL", 1, 40_000)
    assert active and active[0]["lesson_id"] == lid and active[0]["version"] == 2


def test_a_lesson_that_does_not_replicate_is_rejected_and_never_acts():
    rng = np.random.default_rng(1)
    x = ExperienceView(LessonPolicy(min_n=60, min_oos=40))
    _stream(x, 0, 120, -0.5, rng)
    x.advance(20_000)
    x.learn(20_000)
    _stream(x, 300, 130, +0.3, rng)          # the pattern does not continue
    x.advance(60_000)
    statuses = [c["status"] for c in x.learn(60_000)]
    assert statuses == ["REJECTED"]
    assert x.lessons_matching("BREAKOUT", "RANGING", "NORMAL_VOL", 1, 60_000) == []


def test_lessons_are_versioned_and_their_past_state_is_reconstructable():
    rng = np.random.default_rng(0)
    x = ExperienceView(LessonPolicy(min_n=60, min_oos=40))
    _stream(x, 0, 120, -0.5, rng)
    x.advance(20_000); x.learn(20_000)
    _stream(x, 300, 60, -0.5, rng)
    x.advance(40_000); x.learn(40_000)
    versions = next(iter(x.lessons.values()))
    assert [v["status"] for v in versions] == ["CANDIDATE", "VALIDATED"]
    assert x._as_of(versions, 30_000)["status"] == "CANDIDATE"  # what it knew then


def test_discovery_threshold_is_corrected_for_every_context_examined():
    rng = np.random.default_rng(5)
    x = ExperienceView(LessonPolicy(min_n=60))
    # 40 contexts of pure noise: without a multiple-testing correction some
    # would look "significant" by chance.
    for k in range(40):
        _stream(x, k * 1000, 80, 0.0, rng, family=f"F{k}")
    x.advance(10**9)
    assert x.learn(10**9) == []


def test_objection_effect_is_measured_against_everything_else():
    x = ExperienceView()
    for i in range(100):
        x.record(ev(i, -0.5, objections=("LATE_ENTRY",)))
    for i in range(100, 200):
        x.record(ev(i, 0.3))
    x.advance(10**9)
    eff = x.objection_effect("LATE_ENTRY", 10**9)
    assert eff["mean_flagged"] == pytest.approx(-0.5) and eff["mean_other"] == pytest.approx(0.3)


def test_llm_reliability_is_zero_until_proven():
    x = ExperienceView()
    assert x.agent_reliability("reviewer_llm", 0) == 0.0


# ── post-mortem ────────────────────────────────────────────────────────


@pytest.mark.parametrize("trade,cause", [
    ({"r": -1.0, "data_flags": ["gap"]}, "DATA_PROBLEM"),
    ({"r": -1.0, "slippage_r": 0.3}, "EXECUTION_COST"),
    ({"r": -1.0, "regime_entry": "TRENDING_UP", "regime_exit": "RANGING"}, "REGIME_SHIFT"),
    ({"r": -1.0, "mfe_r": 1.3}, "EXIT_MANAGEMENT"),
    ({"r": -1.0, "mfe_r": 0.05, "bars_held": 1}, "ENTRY_TIMING"),
    ({"r": -1.0, "mfe_r": 0.5, "bars_held": 10, "predicted_win": 0.5}, "NORMAL_VARIANCE"),
    ({"r": -1.0, "mfe_r": 0.5, "bars_held": 10, "predicted_win": 0.9}, "THESIS_WRONG"),
    ({"r": 1.5, "predicted_win": 0.55}, "THESIS_CONFIRMED"),
    ({"r": 1.5, "predicted_win": 0.2}, "FAVOURABLE_VARIANCE"),
])
def test_postmortem_names_the_cause(trade, cause):
    assert postmortem(trade)["cause"] == cause


def test_postmortem_refuses_to_infer_from_an_unknown_result():
    assert postmortem({"r": None})["cause"] == "UNKNOWN"


def test_reflection_reports_calibration_repeated_mistakes_and_over_filtering():
    rng = np.random.default_rng(2)
    evs = [ev(i, float(rng.normal(-0.1, 1)), pw=0.6, pr=0.2) for i in range(80)]
    evs += [ev(100 + i, float(rng.normal(0.4, 1)), traded=False) for i in range(80)]
    pms = [{"outcome": "LOSS", "cause": "ENTRY_TIMING"}] * 12 + [{"outcome": "LOSS", "cause": "NORMAL_VARIANCE"}] * 5
    rep = reflect(evs, pms, 10**6)
    assert rep["traded"]["n"] == 80 and rep["calibration"]
    assert "ENTRY_TIMING" in rep["repeated_mistakes"]
    assert any(h["kind"] == "OVER_FILTERING" for h in rep["hypotheses"])
    assert rep["overconfidence_R"] > 0
