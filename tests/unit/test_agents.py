"""Agents, LLM layer and evidence synthesis: behaviour on constructed scenarios."""

from __future__ import annotations

import json
import urllib.error

import pytest

from aitrader.agents.analysts import AdversarialAnalyst, ReviewerAnalyst, SetupAnalyst, validate_llm_review
from aitrader.agents.brain import Brain, BrainConfig
from aitrader.agents.types import AccountView, MarketContext, Objection
from aitrader.decision.synthesis import EvidenceSynthesizer, decision_id
from aitrader.features.store import FEATURE_VERSION, NAMES, FeatureVector
from aitrader.llm.provider import LLMClient, LLMConfig, extract_json
from aitrader.memory.patterns import ActionEvidence, AnalogEvidence
from aitrader.regime.model import RegimeState

T = 1_500_000_400  # a Friday? irrelevant: tests pin hour explicitly below
T = 1_500_004_800  # 2017-07-14 03:20 UTC (Friday early morning, not rollover, not weekend)


def features(**over):
    base = {n: 0.0 for n in NAMES}
    base.update({"er120": 0.4, "ma_slope": 1.0, "vol_ratio": 1.0, "rv_ratio": 1.0, "spread_rel": 0.05,
                 "tick_activity": 1.0, "range_pos120": 0.5, "range_pos24": 0.5, "dist_ma48": -0.5,
                 "brk_hi120": -1.0, "brk_lo120": 1.0, "smc_sweep": 0.0, "smc_structure": 0.0,
                 "r24": 1.0, "r120": 3.0, "er24": 0.4, "bar_body": 0.2})
    base.update(over)
    return FeatureVector(FEATURE_VERSION, T, T - 3600, "EURUSD", "H1", "test", base, (), {"stale_seconds": 0})


def regime(label="TRENDING_UP", familiar=True, abnormal=False):
    return RegimeState(label, "NORMAL_VOL", 1 if label == "TRENDING_UP" else 0, abnormal, 1.0, familiar)


def analog(action, mean, se, n=100, similarity_dist=1.0):
    a = ActionEvidence(action, n, mean, se, mean - 1.28 * se, 0.55 if mean > 0 else 0.4, mean)
    return AnalogEvidence(5000, n, similarity_dist, 1.0, {action: a})


def ctx(analogs=None, feats=None, rg=None, account=None, flags=None, knowledge=None):
    return MarketContext("EURUSD", "H1", T, feats or features(), rg or regime(), 0.0010,
                         1.10000, 1.10006, T, {}, account or AccountView(10000, 10000, 0.0, []),
                         data_flags=flags or [], analogs=analogs or {}, knowledge=knowledge)


def brain(**kw):
    return Brain(config=BrainConfig(llm_agents=(), parallel=False), **kw)


V = {"features": FEATURE_VERSION}


def test_a_positive_lower_bound_trend_setup_becomes_a_trade():
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.20, 0.05)})
    th = brain().think(c, V)
    assert th.decision.decision == "BUY"
    assert th.decision.family == "TREND_PULLBACK"
    assert th.decision.stop_loss < th.decision.entry < th.decision.take_profit
    assert 0.5 < th.decision.confidence <= 1.0
    assert th.decision.independent_evidence["n_supporting"] >= 1


def test_no_evidence_means_no_trade_even_with_a_valid_setup():
    th = brain().think(ctx(analogs={}), V)
    assert th.decision.decision == "NO_TRADE"


def test_negative_analogue_expectancy_is_no_trade():
    th = brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", -0.05, 0.03)}), V)
    assert th.decision.decision == "NO_TRADE"


@pytest.mark.parametrize("kw,code", [
    ({"rg": regime(familiar=False)}, "UNFAMILIAR_STATE"),
    ({"rg": regime(abnormal=True)}, "ABNORMAL_MARKET"),
    ({"flags": ["gap in data"]}, "DATA_QUALITY"),
])
def test_blocking_conditions_force_no_trade_whatever_the_evidence(kw, code):
    th = brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}, **kw), V)
    assert th.decision.decision == "NO_TRADE"
    assert code in th.decision.no_trade_reason
    # A market-wide block stops the decision before any candidate is weighed.
    assert th.decision.no_trade_reason.startswith("blocked:")


def test_a_crashing_agent_fails_closed():
    class Broken(AdversarialAnalyst):
        def analyze(self, ctx, candidates):
            raise RuntimeError("bug")
    th = brain(adversary=Broken()).think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    assert th.decision.decision == "NO_TRADE"
    assert "adversary" in th.decision.no_trade_reason and th.reports["adversary"].status == "ERROR"


def test_major_objections_raise_the_bar_instead_of_voting():
    # Lower bound +0.04R. One default penalty (0.03) is cleared; two (0.06) are not.
    ev = {"T1:BUY": analog("T1:BUY", 0.04 + 1.28 * 0.02, 0.02)}
    one = brain().think(ctx(analogs=ev, feats=features(r24=5.0, dist_ma48=-0.4)), V)  # LATE_ENTRY
    assert [o.code for o in one.reports["adversary"].objections if o.data.get("action") == "T1:BUY"] == ["LATE_ENTRY"]
    assert one.decision.decision == "BUY"
    assert one.decision.required_edge == pytest.approx(0.03)
    two = brain().think(ctx(analogs=ev, feats=features(r24=5.0, dist_ma48=-0.4, smc_sweep=-1.0)), V)
    codes = {o.code for o in two.reports["adversary"].objections if o.data.get("action") == "T1:BUY"}
    assert {"LATE_ENTRY", "SWEEP_AGAINST"} <= codes
    assert two.decision.decision != "BUY"


def test_the_adversary_never_supports():
    rep = AdversarialAnalyst().analyze(ctx(), [])
    assert rep.stance in ("NEUTRAL", "OPPOSE")


def test_setup_is_not_locked_to_one_family_analogue_discovery():
    # No family triggers (flat, mid-range), but analogues favour SELL.
    feats = features(ma_slope=0.0, dist_ma48=0.3, brk_hi120=-2, brk_lo120=2, smc_sweep=0.0)
    c = ctx(analogs={"T2:SELL": analog("T2:SELL", 0.3, 0.05)}, feats=feats, rg=regime("TRANSITION"))
    rep = SetupAnalyst().analyze(c)
    assert rep.candidates and rep.candidates[0].family == "ANALOG_DISCOVERY"


def test_decision_ids_are_deterministic_for_idempotency():
    assert decision_id("EURUSD", "H1", T, "PAPER", V) == decision_id("EURUSD", "H1", T, "PAPER", V)
    assert decision_id("EURUSD", "H1", T, "PAPER", V) != decision_id("EURUSD", "H1", T + 3600, "PAPER", V)


def test_llm_agreement_cannot_lower_the_bar():
    class KV:
        def objection_effect(self, code, t): return None
        def agent_reliability(self, agent, t): return 1.0
        def lessons_matching(self, *a): return []
        def family_regime_stats(self, *a): return None
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.01 + 1.28 * 0.02, 0.02)}, knowledge=KV())
    rep = brain().think(c, V)
    base_required = rep.decision.required_edge
    s = EvidenceSynthesizer()
    agree = s.synthesize(c, rep.reports, V, [{"agent": "reviewer_llm", "direction": "BUY", "summary": ""}])
    oppose = s.synthesize(c, rep.reports, V, [{"agent": "reviewer_llm", "direction": "SELL", "summary": ""}])
    assert agree.required_edge == base_required
    assert oppose.decision == "NO_TRADE" or oppose.required_edge > base_required


# ── LLM provider ────────────────────────────────────────────────────────


GOOD = {"stance": "OPPOSE", "direction": "NONE",
        "objections": [{"code": "FAKE_BREAKOUT_RISK", "severity": "MAJOR", "reason": "thin"}], "summary": "no"}


def transport_returning(content, calls):
    def t(url, headers, body, timeout):
        calls.append((url, headers, body))
        if isinstance(content, Exception):
            raise content
        return {"choices": [{"message": {"content": content}}], "usage": {"total_tokens": 10}}
    return t


CFG = LLMConfig("openai_compatible", "https://example.test/v1", "sk-secret", "m1", fallback=("m2",))


def test_llm_valid_json_is_accepted_and_key_is_never_exposed():
    calls = []
    client = LLMClient(CFG, transport_returning(json.dumps(GOOD), calls))
    res = client.complete_json("adversary", "sys", {"x": 1}, validate_llm_review)
    assert res.ok and res.data["stance"] == "OPPOSE"
    assert "sk-secret" not in json.dumps(res.as_dict()) and "sk-secret" not in repr(CFG)
    assert "sk-secret" not in json.dumps(client.health())
    assert calls[0][1]["Authorization"] == "Bearer sk-secret"


@pytest.mark.parametrize("content,status", [
    ("I think you should buy", "INVALID_JSON"),
    ('{"stance": "MAYBE"}', "SCHEMA"),
    (json.dumps({**GOOD, "objections": [{"code": "MADE_UP", "severity": "MAJOR"}]}), "SCHEMA"),
])
def test_llm_malformed_or_out_of_vocabulary_answers_are_rejected(content, status):
    client = LLMClient(LLMConfig("openai_compatible", "https://x/v1", "", "m1"), transport_returning(content, []))
    res = client.complete_json("adversary", "s", {}, validate_llm_review)
    assert not res.ok and res.status == status and res.data is None


def test_llm_falls_back_to_the_next_model_and_respects_budget():
    calls = []
    def t(url, headers, body, timeout):
        calls.append(body["model"])
        if body["model"] == "m1":
            raise urllib.error.HTTPError(url, 400, "bad", {}, None)
        return {"choices": [{"message": {"content": json.dumps(GOOD)}}]}
    client = LLMClient(CFG, t)
    assert client.complete_json("adversary", "s", {}, validate_llm_review).model == "m2"
    tight = LLMClient(LLMConfig("openai_compatible", "https://x/v1", "", "m1", daily_budget=1),
                      transport_returning(json.dumps(GOOD), []))
    assert tight.complete_json("a", "s", {}, validate_llm_review).ok
    assert tight.complete_json("a", "s", {"y": 2}, validate_llm_review).status == "BUDGET"


def test_llm_disabled_by_default():
    assert not LLMConfig.from_env({}).enabled
    res = LLMClient(LLMConfig.from_env({})).complete_json("a", "s", {}, validate_llm_review)
    assert res.status == "DISABLED"


def test_extract_json_finds_fenced_and_embedded_objects_and_never_repairs():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('here: {"a": {"b": "}"}} done') == {"a": {"b": "}"}}
    assert extract_json('{"a": 1,}') is None


def test_required_llm_that_fails_blocks_the_trade():
    client = LLMClient(CFG, transport_returning(TimeoutError("timed out"), []))
    b = Brain(llm=client, config=BrainConfig(llm_agents=("adversary",), llm_required=True, parallel=False))
    th = b.think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    assert th.decision.decision == "NO_TRADE"


def test_optional_llm_failure_costs_reasoning_not_safety_or_the_decision():
    client = LLMClient(CFG, transport_returning(TimeoutError("timed out"), []))
    b = Brain(llm=client, config=BrainConfig(llm_agents=("adversary",), llm_required=False, parallel=False))
    th = b.think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.3, 0.02)}), V)
    assert th.decision.decision == "BUY"
    assert th.reports["adversary"].llm["ok"] is False


def test_llm_objections_are_recorded_as_a_would_be_veto_and_never_change_the_decision():
    """Takeover audit: a model veto has no forward evidence of value, so it is advisory. The deterministic
    decision (Track A) is unchanged; what the model would have vetoed (Track B) is recorded for comparison."""
    client = LLMClient(CFG, transport_returning(json.dumps(
        {**GOOD, "objections": [{"code": "DATA_QUALITY", "severity": "BLOCKING", "reason": "gap"}]}), []))
    b = Brain(llm=client, config=BrainConfig(llm_agents=("adversary",), parallel=False))
    th = b.think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    plain = brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    assert th.decision.decision == plain.decision.decision == "BUY"
    assert th.decision.ai["would_veto"] is True and th.decision.ai["would_veto_codes"] == ["DATA_QUALITY"]
    assert not any("+llm" in o.agent for r in th.reports.values() for o in r.objections)


def test_objection_vocabulary_is_closed():
    with pytest.raises(ValueError):
        Objection("VIBES", "MAJOR", "x", "y")


def test_every_agent_report_has_a_plausible_latency():
    """A duration is finished - started on ONE clock; mixing clocks shows years as milliseconds."""
    th = brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    for name, r in th.reports.items():
        assert 0 <= r.latency_ms < 60_000, (name, r.latency_ms)



# ── the Reviewer: an independent analyst of evidence quality ────────────


def rich_analog(action, mean, se, *, age_days=100.0, top_share=0.2, other=None):
    acts = {action: ActionEvidence(action, 100, mean, se, mean - 1.28 * se, 0.55, mean)}
    if other is not None:
        k, m = other
        acts[k] = ActionEvidence(k, 100, m, 0.02, m - 0.0256, 0.5, m)
    return AnalogEvidence(5000, 100, 1.0, 1.0, acts, [], age_days, top_share)


def test_the_reviewer_reports_before_synthesis_and_never_repeats_the_decision():
    th = brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    rv = th.reports["reviewer"]
    assert rv.status == "OK" and rv.stance == "DESCRIBE"
    assert rv.summary.startswith("evidence quality") and rv.summary != th.decision.thesis
    assert rv.started <= th.reports["setup"].finished + 60  # a real, timed agent run


def test_the_reviewer_grades_noise_age_concentration_and_template_disagreement():
    c = ctx(analogs={"T1:BUY": rich_analog("T1:BUY", 0.01, 0.05, age_days=5 * 365, top_share=0.8,
                                           other=("T2:BUY", -0.2))})
    cands = SetupAnalyst().analyze(c).candidates
    codes = {o.code for o in ReviewerAnalyst().analyze(c, cands).objections}
    assert {"ANALOG_NOISE", "ANALOG_STALE", "ANALOG_CONCENTRATED", "TEMPLATE_DISAGREEMENT"} <= codes
    clean = ctx(analogs={"T1:BUY": rich_analog("T1:BUY", 0.5, 0.02)})
    rep = ReviewerAnalyst().analyze(clean, SetupAnalyst().analyze(clean).candidates)
    clean_t1 = [o for o in rep.objections if o.data.get("action") == "T1:BUY"]
    assert clean_t1 == []  # good evidence draws no quality objection (T2 has no analogues and is flagged)


def test_new_quality_checks_are_minor_until_measured_so_they_cannot_change_a_decision():
    noisy = ctx(analogs={"T1:BUY": rich_analog("T1:BUY", 0.5, 0.02, age_days=9 * 365, top_share=0.9)})
    th = brain().think(noisy, V)
    minor = [o for o in th.reports["reviewer"].objections if o.code in ("ANALOG_STALE", "ANALOG_CONCENTRATED")]
    assert minor and all(o.severity == "MINOR" for o in minor)
    assert th.decision.decision == "BUY"  # informational: recorded and measured, not acted on


def test_a_crashing_reviewer_fails_closed():
    class Broken(ReviewerAnalyst):
        def analyze(self, ctx, candidates):
            raise RuntimeError("bug")
    th = brain(reviewer=Broken()).think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02)}), V)
    assert th.decision.decision == "NO_TRADE" and "reviewer" in th.decision.no_trade_reason


def test_the_adversary_argues_from_the_market_and_the_reviewer_from_the_evidence():
    weak = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.5, 0.02, n=20)})
    cands = SetupAnalyst().analyze(weak).candidates
    adv = {o.code for o in AdversarialAnalyst().analyze(weak, cands).objections}
    rev = {o.code for o in ReviewerAnalyst().analyze(weak, cands).objections}
    assert "WEAK_ANALOG_EVIDENCE" in rev and "WEAK_ANALOG_EVIDENCE" not in adv


def test_an_opposing_model_with_full_measured_reliability_still_cannot_change_the_decision():
    """Takeover audit: the model's opinion is advisory even where the knowledge base would weight it fully.
    (Before the audit an opposing model with reliability 1.0 raised the required edge.)"""
    class KV:
        def objection_effect(self, code, t): return None
        def agent_reliability(self, agent, t): return 1.0
        def lessons_matching(self, *a): return []
        def family_regime_stats(self, *a): return None
    reply = {"stance": "OPPOSE", "direction": "SELL", "objections": [], "summary": "sell"}
    client = LLMClient(CFG, transport_returning(json.dumps(reply), []))
    b = Brain(llm=client, config=BrainConfig(llm_agents=("reviewer",), parallel=False))
    c = ctx(analogs={"T1:BUY": analog("T1:BUY", 0.01 + 1.28 * 0.02, 0.02)}, knowledge=KV())
    with_model = b.think(c, V).decision
    without = brain().think(ctx(analogs={"T1:BUY": analog("T1:BUY", 0.01 + 1.28 * 0.02, 0.02)}, knowledge=KV()), V).decision
    assert (with_model.decision, with_model.required_edge) == (without.decision, without.required_edge)
    assert with_model.ai["opinions"][0]["direction"] == "SELL"  # recorded, not applied
