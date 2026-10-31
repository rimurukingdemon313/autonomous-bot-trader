"""The desk's own journal (dual-ai 1.13.0): both traders read it; it holds the desk's agreements on the pair, each
counted once, from LEARNING weeks only and outcomes resolved before the decision, never anything later."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aitrader.agents.dual_ai import JOURNAL_RECORD, TRADER1_SYSTEM, TRADER2_SYSTEM, desk_memory
from aitrader.learning import dual_ai_stats
from aitrader.learning.forward import ForwardLedger, partition
from aitrader.memory.db import Database

from tests.openrouter_kit import packet_of
from tests.unit.test_dual_ai import desk_ctx, scripted, think

LEARN_T = int(datetime(2026, 10, 20, 9, tzinfo=timezone.utc).timestamp())   # ISO week 43: LEARNING
EVAL_T = int(datetime(2026, 10, 27, 9, tzinfo=timezone.utc).timestamp())    # ISO week 44: EVALUATION
AS_OF = LEARN_T + 3 * 86400


def put(db, did, *, t=LEARN_T, family="DUAL_AI", side=1, tf="M15", net=1.0, resolved=None, sym="EURUSD",
        executed=True, conf=0.7):
    ForwardLedger(db, lambda: t).record({"decision_id": did, "symbol": sym, "t": t, "partition": partition(t),
                                         "family": family, "side": side, "timeframe": tf, "executed": executed,
                                         "confidence": conf})
    ra = resolved if resolved is not None else t + 3600
    db.append("forward_outcomes", {"decision_id": did, "resolved_at": ra, "partition": partition(t),
                                   "payload": {"decision_id": did, "status": "RESOLVED", "net_r": net,
                                               "reason": "TARGET" if net > 0 else "STOP", "resolved_at": ra}})


def test_the_pair_record_counts_each_agreement_once_from_learning_weeks_resolved_before_the_decision():
    assert partition(LEARN_T) == "LEARNING" and partition(EVAL_T) == "EVALUATION"
    db = Database(":memory:")
    put(db, "a", net=1.0)                                                    # a trade taken, M15
    put(db, "b", side=-1, tf="H1", net=-1.0, executed=False)                 # refused by the risk engine
    put(db, "c", family="DUAL_AI_LOW_CONFIDENCE", tf="H1", net=2.0, executed=False)  # under the floor
    put(db, "a:exit-wide2x", family="DUAL_AI_EXIT_WIDE2X", net=-5.0, executed=False)  # trade a closed another way
    put(db, "d", family="DUAL_AI_DEBATE_PICK", net=-5.0, executed=False)     # a disagreement: not an agreement
    put(db, "e", t=EVAL_T, net=-3.0)                                         # an EVALUATION week: never learned
    put(db, "f", net=-4.0, resolved=AS_OF + 60)                              # resolved after the decision
    put(db, "g", sym="GBPUSD", net=-4.0)                                     # another pair
    rec = dual_ai_stats.instrument_record(db, "EURUSD", as_of=AS_OF)
    assert rec["agreements"]["n"] == 3 and rec["agreements"]["expectancy_r"] == pytest.approx(2 / 3, abs=1e-3)
    assert rec["by_side"]["BUY"]["n"] == 2 and rec["by_side"]["BUY"]["expectancy_r"] == pytest.approx(1.5)
    assert rec["by_side"]["SELL"]["n"] == 1 and rec["by_side"]["SELL"]["expectancy_r"] == pytest.approx(-1.0)
    assert {k: v["n"] for k, v in rec["by_timeframe"].items()} == {"H1": 2, "M15": 1}
    assert rec["agreements"]["sample"] == "insufficient" and rec["partition"] == "LEARNING"
    assert [x["net_r"] for x in rec["latest"]] == [1.0, -1.0, 2.0] and rec["latest"][0]["traded"] is True
    assert rec["latest"][0]["decided_utc"] == "2026-10-20 09:00"
    later = dual_ai_stats.instrument_record(db, "EURUSD", as_of=AS_OF + 120)  # once it has resolved, f counts
    assert later["agreements"]["n"] == 4
    assert dual_ai_stats.instrument_record(db, "EURUSD", as_of=LEARN_T)["agreements"]["n"] == 0  # nothing yet


def test_both_traders_read_the_desk_journal():
    c = desk_ctx()
    c.memory_brief = {
        "dual_ai_instrument": {"instrument": "EURUSD", "agreements": {"n": 3}},
        "relevant_past_trades": [{"symbol": "EURUSD", "side": "BUY", "opened": LEARN_T, "R": -1.0,
                                  "exit_reason": "STOP", "post_mortem_cause": "THESIS_WRONG"}],
        "my_record": {"trades": 1, "sample": "insufficient"},
        "dual_ai": {"trades_taken": {"n": 1}, "by_desk_confidence": {}, "decisions_by_rule": {"AGREE": 1},
                    "debate_pick_if_taken": {"n": 0}},
        "validated_lessons": [],
        "forward_lessons": [{"code": "BAD_REGIME", "scope": "DUAL_AI|TRANSITION", "statement": "loses", "evidence_n": 31}],
    }
    m = desk_memory(c)
    assert m["this_instrument"]["agreements"]["n"] == 3
    (past,) = m["past_trades"]
    assert past["opened_utc"] == "2026-10-20 09:00" and "opened" not in past and past["exit_reason"] == "STOP"
    assert set(m["record_overall"]) <= set(JOURNAL_RECORD) and "trades_taken" in m["record_overall"]
    assert "debate_pick_if_taken" not in m["record_overall"]  # the dashboard's, not the traders' journal
    assert m["lessons_confirmed_out_of_sample"][0]["code"] == "BAD_REGIME"
    _, fake = think(scripted(), c)
    t1, t2 = (packet_of(x["body"]) for x in fake.calls[:2])
    assert t1["desk_memory"] == t2["desk_memory"] == m  # Trader 1, who reads the chart, reads it too
    assert "desk_measured_record" not in t2
    assert '"desk_memory"' in TRADER1_SYSTEM and '"desk_memory"' in TRADER2_SYSTEM


def test_an_empty_journal_is_said_as_empty_never_invented():
    m = desk_memory(desk_ctx())  # no memory brief at all: a first decision
    assert m["this_instrument"] is None and m["past_trades"] == [] and m["record_overall"] is None
    assert m["trades_record"] is None and m["lessons_confirmed_out_of_sample"] == []
