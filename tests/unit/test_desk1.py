"""DESK-1's counterfactuals, on agreements built so the right answer is known: a take-profit is taken exactly when
the record proves the price reached it first, never on the bar that stopped the trade; a skipped trade is no trade;
a rule is selected on LEARNING only and judged once on EVALUATION."""

from __future__ import annotations

import pytest

from scripts.desk1 import SPEC, candidate_net, evaluate, judge, planned_cost_r, spec_sha, take_profit_net

COMM_R = 0.07  # commission 0.00007 over a risk of 0.0010


def agr(reason, net, mfe, *, t_mfe=100, exit_time=200, target_r=2.0, side=1, part="LEARNING", session="LONDON",
        spread=0.0002, slip=0.00001, comm=0.00007, risk=0.0010, i=0):
    entry = 1.1000
    target = entry + side * (slip + target_r * risk)  # target_r R from the fill, the fill being entry + side x slip
    return {"id": f"{part}-{i}-{reason}", "partition": part, "side": side, "session": session, "entry": entry,
            "target": target, "risk_px": risk, "spread": spread, "slippage_px": slip, "commission_px": comm,
            "net_r": net, "reason": reason, "mfe_r": mfe, "t_mfe": t_mfe, "exit_time": exit_time}


@pytest.mark.parametrize("side", [1, -1])
def test_a_take_profit_is_taken_only_when_the_record_proves_the_price_reached_it_first(side):
    # reached its own target (2R): the bar that reached 2R reached 1R
    assert take_profit_net(agr("TARGET", 1.93, 2.1, side=side), 1.0) == pytest.approx(1.0 - COMM_R)
    # its own target was nearer than 1R: it came first, unchanged
    assert take_profit_net(agr("TARGET", 0.68, 0.9, target_r=0.75, side=side), 1.0) == 0.68
    # closed by its time exit: 1R taken if its best point reached it, in any bar
    assert take_profit_net(agr("TIME", 0.20, 1.05, side=side), 1.0) == pytest.approx(1.0 - COMM_R)
    assert take_profit_net(agr("TIME", 0.20, 0.95, side=side), 1.0) == 0.20
    # stopped out: 1R taken only if reached in a bar BEFORE the one that stopped it
    assert take_profit_net(agr("STOP", -1.1, 1.2, t_mfe=100, exit_time=200, side=side), 1.0) == pytest.approx(
        1.0 - COMM_R)
    assert take_profit_net(agr("STOP", -1.1, 1.2, t_mfe=200, exit_time=200, side=side), 1.0) == -1.1  # same bar
    assert take_profit_net(agr("STOP", -1.1, 0.6, side=side), 1.0) == -1.1  # never reached


def test_a_skipped_trade_is_no_trade_and_its_planned_cost_is_read_at_the_entry():
    a = agr("STOP", -1.29, 0.1)
    assert planned_cost_r(a) == pytest.approx((0.0002 + 2 * 0.00001 + 0.00007) / 0.0010)  # 0.29 R
    assert candidate_net(a, {"skip_planned_cost_r_above": 0.20}) is None
    wide = agr("STOP", -1.15, 0.1, risk=0.0020)  # the same costs over twice the risk: 0.145 R
    assert candidate_net(wide, {"skip_planned_cost_r_above": 0.20}) == -1.15
    assert candidate_net(agr("STOP", -1.2, 0.1, session="OVERLAP"), {"skip_session": "OVERLAP"}) is None
    rows = [agr("STOP", -1.1, 0.1, session="OVERLAP", i=1), agr("TARGET", 1.9, 2.1, i=2)]
    e = evaluate(rows, {"skip_session": "OVERLAP"})
    assert e["mean_d"] == pytest.approx(0.55) and e["trades"] == 1 and e["net_r"] == pytest.approx(1.9)  # skip: 0 R


def stopped_after(part, n, mfe=0.8, start=0):
    """Trades that reached `mfe` R in an earlier bar, then were stopped. Their costs are under 0.20 R (a risk of 0.0020),
    so no cost filter touches them."""
    return [agr("STOP", -1.1, mfe, part=part, risk=0.0020, i=start + j) for j in range(n)]


def winners(part, n, start=0):
    return [agr("TARGET", 1.93, 2.1, part=part, risk=0.0020, i=start + j) for j in range(n)]


def test_a_rule_is_selected_on_learning_only_and_judged_once_on_evaluation():
    # 0.8 R reached before each stop: only the 0.75 R cap wins them, and every cap costs the 2 R winners
    learn = stopped_after("LEARNING", 30) + winners("LEARNING", 10, start=100)
    good_eval = stopped_after("EVALUATION", 20) + [agr("STOP", -1.1, 0.2, part="EVALUATION", risk=0.0020, i=200 + j)
                                                   for j in range(5)]
    res = judge(learn + good_eval)
    assert res["selected"] == "TP-0.75" and res["verdict"] == "PROFITABLE"
    assert res["n_learning"] == 40 and res["n_evaluation"] == 25
    assert res["learning"]["TP-1.0"]["mean_d"] < 0  # 0.8 R never reached 1 R: a 1 R cap only cuts the winners
    assert res["evaluation"]["mean_d"] > 0 and res["evaluation"]["net_r"] > 0
    res = judge(learn + winners("EVALUATION", 20, start=300))  # on EVALUATION the cap only costs
    assert res["selected"] == "TP-0.75" and res["verdict"] == "NOT CONFIRMED"


def test_the_largest_gain_is_selected_when_several_rules_qualify():
    res = judge(stopped_after("LEARNING", 30, mfe=1.3) + winners("LEARNING", 10, start=100))
    assert res["selected"] == "TP-1.25"  # 1.3 R reached: the 1.25 R cap keeps the most of each


def test_when_nothing_qualifies_on_learning_evaluation_is_never_judged():
    flat = [agr("STOP", -1.1, 0.2, risk=0.0020, i=j) for j in range(20)] + winners("LEARNING", 20, start=50)
    evalu = stopped_after("EVALUATION", 20)
    res = judge(flat + evalu)
    assert res["verdict"] == "FAILED" and res["selected"] is None
    assert "evaluation" not in res and "baseline_evaluation" not in res  # not looked at


def test_the_spec_is_frozen_by_its_hash():
    assert spec_sha(SPEC) == spec_sha(dict(SPEC)) and spec_sha({**SPEC, "select_on": "EVALUATION"}) != spec_sha(SPEC)
    assert set(SPEC["candidates"]) == {"TP-0.75", "TP-1.0", "TP-1.25", "SKIP-COST-0.20", "SKIP-OVERLAP"}
