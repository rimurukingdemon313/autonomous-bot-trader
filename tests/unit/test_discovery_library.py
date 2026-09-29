"""The strategy library records WHY documented approaches decide as they do, grades sources by
evidence quality, keeps conflicts, and only ever turns a method into a hypothesis to test."""

from __future__ import annotations

import pytest

from aitrader.research.discovery.hypothesis import condition_key
from aitrader.research.discovery.library import (LIBRARY, PRINCIPLES, Method, Source, conflicts, knowledge_graph,
                                                 pending_tests, principle_priority, to_json)
from aitrader.research.discovery.universe import DAILY_FEATURES
from aitrader.features.store import NAMES
from aitrader.research.discovery.primitives import PRIMITIVE_BY_NAME


def test_every_method_is_graded_and_is_either_testable_or_says_why_not():
    for m in LIBRARY:
        assert m.evidence_quality in "ABCD" and m.decision_process and m.principles
        assert m.tests or m.untestable_because
        for t in m.tests:
            condition_key(t["condition"])  # in the engine's closed vocabulary
            feats = {p.split("=")[0] for p in t["condition"].split("&")}
            known = set(DAILY_FEATURES) if t["timeframe"] == "D1" else set(NAMES) | set(PRIMITIVE_BY_NAME)
            assert feats <= known, (m.strategy_id, feats - known)
    with pytest.raises(ValueError):
        Method("X", "x", "x", (Source("a", "book", "C"),), ("TREND_CONTINUATION",), {}, "", "", "", "", "", "", ())


def test_a_famous_name_is_not_evidence_popularity_never_ranks_a_source():
    with pytest.raises(ValueError):
        Method("Y", "y", "y", (Source("a very famous influencer", "practitioner", "S"),), ("BREAKOUT",), {}, "", "",
               "", "", "", "", (), untestable_because="n/a")
    smc = next(m for m in LIBRARY if m.strategy_id == "SL-SMC-SWEEP")
    assert smc.evidence_quality == "D"


def test_conflicting_schools_are_kept_as_a_question_not_forced_into_consensus():
    pairs = {(c["a"], c["b"]) for c in conflicts()}
    assert ("SL-TSMOM", "SL-PULLBACK") in pairs or ("SL-PULLBACK", "SL-TSMOM") in pairs
    assert all("regime" in c["question"] for c in conflicts())


def test_priority_rewards_independent_good_sources_not_repetition():
    pr = {r["principle"]: r for r in principle_priority()}
    assert pr["TREND_CONTINUATION"]["priority"] > pr["LIQUIDITY_SWEEP"]["priority"]
    assert pr["LIQUIDITY_SWEEP"]["priority"] == 0  # D-quality doctrine: tested, never prioritised by fame


def test_the_graph_links_source_method_principle_hypothesis_and_result():
    g = knowledge_graph()
    kinds = {n["kind"] for n in g["nodes"]}
    assert {"source", "method", "principle", "hypothesis", "result", "gap"} <= kinds
    rels = {e["rel"] for e in g["edges"]}
    assert {"documents", "rests_on", "tested_as", "judged_by", "blocked_by"} <= rels
    classes = {n.get("knowledge_class") for n in g["nodes"]}
    assert {"DOCUMENTED_FACT", "INFERRED_PRINCIPLE", "HYPOTHESIS", "UNCERTAIN"} <= classes
    assert "VALIDATED_EDGE" not in classes  # nothing has earned it


def test_only_untested_testable_methods_become_new_hypotheses():
    ids = {m.strategy_id for m, _ in pending_tests()}
    assert ids and all(m.status in ("RESEARCHED", "HYPOTHESIS") for m, _ in pending_tests())
    assert "SL-TSMOM" not in ids and "SL-CARRY" not in ids  # judged already / untestable
    assert len(to_json()) == len(LIBRARY) and set(PRINCIPLES)
