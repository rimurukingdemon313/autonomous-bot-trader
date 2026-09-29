"""The board cannot vote, cannot upgrade, and its independent reviewer catches tampering."""

from __future__ import annotations

import copy
from datetime import date

import numpy as np
import pytest

from aitrader.llm.provider import LLMResult
from aitrader.research.discovery.battery import BatteryRules, regime_binnings, run_battery
from aitrader.research.discovery.board import (Opinion, adversarial_analyst, llm_objections, market_analyst,
                                               opportunity_analyst, reviewer, risk_analyst, synthesize)
from aitrader.research.discovery.study import Condition, Segment, Study, epoch, fit_binning
from aitrader.research.labels import BUY, CostModel
from tests.unit.discovery_market import planted

SEG = Segment("confirmation", "judge", date(2010, 1, 1), date(2013, 1, 1))
RULES = BatteryRules(t_threshold=3.0, permutations=40, random_draws=4)
EPOCHS = (epoch(SEG.start), epoch(SEG.end))
HOLDOUT = epoch(date(2017, 1, 1))


@pytest.fixture(scope="module")
def result():
    data = planted(n=20_000)
    base = Study(data, SEG, {}, CostModel(0.1, 0.7, 0.0))
    vals = lambda f: {s: data[s].columns[f][base.rows[s]] for s in base.symbols}  # noqa: E731
    st = Study(data, SEG, {"A": fit_binning("A", {}, groups=((0,), (1,), (2,)))}, CostModel(0.1, 0.7, 0.0),
               context=regime_binnings({"er120": vals("er120"), "vol_ratio": vals("vol_ratio")}))
    return run_battery(st, Condition((("A", 2),)), BUY, "E1", RULES, trials=10)


def review(res, **kw):
    args = dict(segment_epochs=EPOCHS, holdout_epoch=HOLDOUT, declared_exit="E1", frozen_threshold=3.0,
                preregistration_sha256="abc", expected_sha256="abc")
    return reviewer(res, **(args | kw))


def test_the_reviewer_recomputes_the_result_and_agrees_when_nothing_was_touched(result):
    op = review(result)
    assert op.stance == "SUPPORT" and not op.blocking
    assert op.data["n"] == result["checks"]["min_trades"]["n"]
    assert op.data["t"] == pytest.approx(result["checks"]["significance"]["t"], abs=1e-3)


@pytest.mark.parametrize("tamper", ["t", "outside", "overlap", "exit", "prereg", "threshold", "holdout"])
def test_the_reviewer_blocks_any_discrepancy(result, tamper):
    res = copy.deepcopy(result)
    kw = {}
    tr = res["trades"]
    if tamper == "t":
        res["checks"]["significance"]["t"] += 0.5
    elif tamper == "outside":
        tr.t[0] = EPOCHS[0] - 3600
    elif tamper == "overlap":
        first = np.flatnonzero(tr.symbol == tr.symbol[0])[:2]
        tr.row[first[1]] = tr.row[first[0]] + 1
    elif tamper == "exit":
        kw["declared_exit"] = "E2"
    elif tamper == "prereg":
        kw["expected_sha256"] = "something else"
    elif tamper == "threshold":
        kw["frozen_threshold"] = 2.5
    elif tamper == "holdout":
        kw["holdout_epoch"] = int(tr.exit_t.max()) - 1
    assert review(res, **kw).blocking


def test_there_is_no_vote_and_no_upgrade():
    support = [Opinion(a, ["fine"]) for a in ("market", "opportunity", "risk", "adversarial")]
    blocked = synthesize("VALIDATED", support + [Opinion("reviewer", blocking=["t does not match"])])
    assert blocked["verdict"] == "REJECTED" and blocked["blocked_by"] == ["reviewer: t does not match"]
    assert synthesize("VALIDATED", support + [Opinion("reviewer")])["verdict"] == "VALIDATED"
    assert synthesize("REJECTED", support + [Opinion("reviewer")])["verdict"] == "REJECTED"  # never upgraded
    with pytest.raises(ValueError):
        synthesize("PROBABLY_FINE", support)


def test_a_model_may_object_but_never_approve():
    ok = [Opinion(a) for a in ("market", "opportunity", "risk", "adversarial", "reviewer")]
    soft = synthesize("VALIDATED", ok, [{"text": "small sample in 2015", "blocking": False, "model": "m"}])
    hard = synthesize("VALIDATED", ok, [{"text": "the spread model ignores rollover", "blocking": True, "model": "m"}])
    assert soft["verdict"] == "VALIDATED" and hard["verdict"] == "REJECTED"
    assert synthesize("REJECTED", ok, [{"text": "looks great", "blocking": False}])["verdict"] == "REJECTED"


class Fake:
    def __init__(self, reply):
        self.reply = reply

    def complete_json(self, agent, system, packet, validate):
        err = validate(self.reply)
        return LLMResult(err is None, agent, "fake", "OK" if err is None else "SCHEMA", self.reply if err is None else None)


def test_model_objections_must_be_well_formed_or_they_are_dropped():
    good = {"objections": [{"text": "regime cells are thin", "blocking": False}]}
    assert llm_objections(Fake(good), {"x": 1}) == [{"text": "regime cells are thin", "blocking": False,
                                                     "model": "fake"}]
    assert llm_objections(Fake({"objections": [{"text": "x", "blocking": "yes"}]}), {}) == []
    assert llm_objections(Fake({"verdict": "VALIDATED"}), {}) == []


def test_risk_blocks_a_loss_that_escaped_its_stop(result):
    res = copy.deepcopy(result)
    assert not risk_analyst(res).blocking
    res["trades"].r[0] = -3.4
    op = risk_analyst(res)
    assert op.blocking and "Risk Engine" in " ".join(op.findings)


def test_the_adversary_blocks_a_result_one_instrument_carries():
    dec = {"total_R": 100.0, "by_instrument": {"AAA": {"n": 100, "mean_R": 0.8}, "BBB": {"n": 100, "mean_R": 0.2}},
           "by_year": {"2014": {"n": 100, "mean_R": 0.5}, "2015": {"n": 100, "mean_R": 0.5}}}
    res = {"decomposition": dec, "checks": {"permutation": {"p": 0.01}, "beats_random": {"welch_t": 3.0}},
           "deflated_sharpe": {"dsr": 0.99, "trials": 10}}
    op = adversarial_analyst(res, configurations=1900, prior_tests=18)
    assert op.blocking == ["AAA alone carries 80% of the total R (instrument); the rest earns +0.200R per trade"]
    dec["by_instrument"]["AAA"]["mean_R"] = 0.5
    dec["by_instrument"]["BBB"]["mean_R"] = 0.5
    assert not adversarial_analyst(res, configurations=1900, prior_tests=18).blocking


def test_a_year_that_is_most_of_the_sample_is_not_concentration():
    # 7 of 10 months fall in 2011: it carries 70% of the R because it holds 70% of the trades
    dec = {"total_R": 100.0, "by_instrument": {},
           "by_year": {"2011": {"n": 140, "mean_R": 0.5}, "2012": {"n": 60, "mean_R": 0.5}}}
    res = {"decomposition": dec, "checks": {}, "deflated_sharpe": {}}
    assert not adversarial_analyst(res, configurations=10, prior_tests=0).blocking


def test_market_and_opportunity_raise_concerns_but_never_block(result):
    res = copy.deepcopy(result)
    m = market_analyst(res)
    o = opportunity_analyst(res, {"mechanism": "reversal (conjectured)"},
                            {"discovery": {"mean_R": 0.2}, "validation": {"mean_R": -0.01}})
    assert not m.blocking and not o.blocking
    assert any("every segment" in c for c in o.concerns)
