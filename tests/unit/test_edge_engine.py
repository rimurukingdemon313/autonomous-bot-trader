"""The edge engine: BUY and SELL searched independently from promoted edges only, priced by
measured evidence net of today's cost, never sized, and always judged by the Risk Engine."""

from __future__ import annotations

import json

import pytest

from aitrader.agents.edge_trader import edge_decision
from aitrader.decision.edge_engine import (EdgeFileError, PromotedEdge, edge_health, evaluate, load_promoted,
                                           setup_id)
from aitrader.risk.engine import AccountState, InstrumentSpec, Quote, RiskEngine

T = 1_600_000_000
SPEC = InstrumentSpec("EURUSD", 100_000, 0.01, 0.01, 50.0, 1.0)


def edge(eid="E-1", side="BUY", lo=0.5, mean=0.20, se=0.05, status="PAPER_TEST", health="HEALTHY", **kw):
    d = {"edge_id": eid, "side": side, "instruments": ["EURUSD"], "stop_atr": 1.5, "target_atr": 3.0, "max_bars": 16,
         "conditions": [{"timeframe": "H4", "feature": "er120", "lo": lo},
                        {"timeframe": "M15", "feature": "r6", "hi": -1.0}],
         "oos_mean_r": mean, "oos_se": se, "oos_n": 400, "cost_r_assumed": 0.05, "status": status, "trial": "WF-X",
         "health": health} | kw
    return PromotedEdge.from_json(d)


FRAMES = {"M15": {"r6": -1.5}, "H1": {"er120": 0.4}, "H4": {"er120": 0.7}}
BID, ASK, ATR = 1.1000, 1.10006, 0.0010


def test_nothing_promoted_means_abstain_and_it_says_why(tmp_path):
    edges, note = load_promoted(tmp_path / "absent.json")
    assert edges == [] and "no promoted edges" in note
    res = evaluate([], "EURUSD", T, FRAMES, BID, ASK, ATR, None)
    assert res["decision"] == "ABSTAIN" and "no promoted edges" in res["reason"]


def test_buy_and_sell_are_searched_independently_and_the_stronger_evidence_wins():
    buy, sell = edge("B", "BUY", mean=0.20), edge("S", "SELL", mean=0.30)
    res = evaluate([buy, sell], "EURUSD", T, FRAMES, BID, ASK, ATR, None)
    assert {c["side"] for c in res["candidates"]} == {"BUY", "SELL"}
    assert res["decision"] == "SELL" and res["chosen"]["edge_id"] == "S"
    c = res["chosen"]
    assert c["entry"] == BID and c["stop"] == pytest.approx(BID + 1.5 * ATR) and c["target"] == pytest.approx(BID - 3 * ATR)
    assert c["score_R"] == pytest.approx(0.30 - 0.05)  # tested mean minus one standard error; cost within assumption


def test_an_edge_whose_conditions_do_not_hold_or_cannot_be_read_is_not_matched():
    assert evaluate([edge(lo=0.9)], "EURUSD", T, FRAMES, BID, ASK, ATR, None)["decision"] == "ABSTAIN"
    missing = {"M15": {"r6": -1.5}}  # no H4 context available
    res = evaluate([edge()], "EURUSD", T, missing, BID, ASK, ATR, None)
    assert res["decision"] == "ABSTAIN" and "unavailable" in res["checked"][0]["result"]


def test_todays_extra_cost_is_charged_against_the_edge():
    wide = evaluate([edge(mean=0.10, se=0.04)], "EURUSD", T, FRAMES, BID, BID + 0.0003, ATR, None)
    assert wide["decision"] == "ABSTAIN"  # a 3-pip spread eats the edge that a 0.6-pip spread leaves


def test_degraded_retired_or_unpromoted_edges_are_not_used():
    for kw in ({"health": "DEGRADED"}, {"health": "RETIRED"}, {"status": "VALIDATED"}):
        assert evaluate([edge(**kw)], "EURUSD", T, FRAMES, BID, ASK, ATR, None)["decision"] == "ABSTAIN"


def test_no_doubling_an_open_position_or_a_setup_already_decided():
    e = edge()
    assert evaluate([e], "EURUSD", T, FRAMES, BID, ASK, ATR, None, open_symbols={"EURUSD"})["decision"] == "ABSTAIN"
    sid = setup_id("E-1", "EURUSD", T, "BUY")
    assert evaluate([e], "EURUSD", T, FRAMES, BID, ASK, ATR, None, decided_setups={sid})["decision"] == "ABSTAIN"


def test_an_edge_file_can_never_carry_a_size(tmp_path):
    p = tmp_path / "e.json"
    bad = {"edges": [dict(edge().__dict__, conditions=[{"timeframe": "M15", "feature": "r6", "hi": 0}],
                          instruments=["EURUSD"], lots=5)]}
    p.write_text(json.dumps(bad, default=list))
    with pytest.raises(EdgeFileError):
        load_promoted(p)


def test_health_tells_normal_variance_from_decay():
    assert edge_health(0.2, 0.05, [-1.0] * 5)["state"] == "HEALTHY"  # five losses: too few to judge
    ok = [1.5, -1.0, -1.0, 1.5, -1.0] * 6
    assert edge_health(0.2, 0.05, ok)["state"] == "HEALTHY"
    assert edge_health(0.4, 0.05, [-1.0] * 18 + [1.5] * 4)["state"] == "DEGRADED"
    assert edge_health(0.4, 0.05, [-1.0] * 36 + [1.5] * 6)["state"] == "RETIRED"


class Ctx:
    symbol, timeframe, t, mode = "EURUSD", "M15", T, "PAPER"
    bid, ask, atr, exec_atr = BID, ASK, 0.004, ATR
    frames, open_symbols = FRAMES, ()

    class regime:
        @staticmethod
        def as_dict():
            return {"label": "TRENDING_UP"}


def test_an_edge_decision_is_sized_and_approved_only_by_the_risk_engine():
    d = edge_decision(Ctx, {"x": 1}, [edge()])
    assert d.decision == "BUY" and d.entry == ASK and d.max_hold_minutes == 16 * 15
    acct = AccountState(20_000, 20_000, 20_000, 20_000, 20_000, week_start_equity=20_000)
    v = RiskEngine().evaluate(d, acct, SPEC, Quote("EURUSD", BID, ASK, T), T)
    assert v.approved and v.qty > 0 and v.risk_pct <= 1.0  # the size is the engine's, from equity and the stop
    assert not RiskEngine().evaluate(d, AccountState(20_000, 20_000, 20_000, 20_000, 20_000, kill_switch=True),
                                     SPEC, Quote("EURUSD", BID, ASK, T), T).approved
    nt = edge_decision(Ctx, {"x": 1}, [])
    assert nt.decision == "NO_TRADE" and nt.no_trade_reason.startswith("ABSTAIN")


def test_every_result_answers_the_twelve_questions_without_inventing_an_answer():
    buy = edge("B", "BUY", mean=0.20, evidence={"principles": ["TREND_CONTINUATION"]})
    sell = edge("S", "SELL", mean=0.30, evidence={"principles": ["SHORT_TERM_REVERSAL"]})
    res = evaluate([buy, sell], "EURUSD", T, FRAMES, BID, ASK, ATR, None)
    a = res["answers"]
    assert len([k for k in a if k[0].isdigit()]) == 12 and a["decision"] == res["decision"] == "SELL"
    assert a["1_regime"]["measured"]["H4"]["er120"] == 0.7 and a["1_regime"]["measured"]["H4"]["vol_ratio"] is None
    assert a["2_principles_that_apply"] == ["SHORT_TERM_REVERSAL", "TREND_CONTINUATION"]
    assert a["3_principles_in_conflict"][0] == {"buy": "B", "sell": "S", "resolved_by": "the higher conservative "
                                                                                          "expected value"}
    assert (a["5_validated_buy"], a["6_validated_sell"]) == ("B", "S")
    assert a["7_expected_value_after_costs_R"] == res["chosen"]["score_R"] and a["8_entry"] == BID
    assert a["10_exit_model"]["stop_atr"] == 1.5 and "Risk Engine" in a["11_current_risk"]
    # nothing promoted: every evidence answer is None, not a guess, and the decision is ABSTAIN
    none = evaluate([], "EURUSD", T, FRAMES, BID, ASK, ATR, None)["answers"]
    assert none["decision"] == "ABSTAIN"
    assert all(none[k] is None for k in ("2_principles_that_apply", "4_relevant_edges", "5_validated_buy",
                                         "6_validated_sell", "7_expected_value_after_costs_R", "8_entry",
                                         "9_invalidation", "10_exit_model", "12_recently_degraded"))

