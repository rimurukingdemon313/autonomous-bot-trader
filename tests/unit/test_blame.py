"""Who lost it, the market or us: each check is shown to fail by construction, and a trade that passes them all is
the market's. A check that cannot be read never clears us."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aitrader.learning.blame import summary, verdict

T = datetime(2026, 10, 21, 9, 0, tzinfo=timezone.utc).timestamp()  # a Wednesday morning


def trade(**over):
    o = {"decision_id": "d1", "symbol": "EURUSD", "direction": "BUY", "source": "DUAL_AI", "opened": T,
         "closed": T + 3600, "net_pnl": -480.0, "planned_max_loss": 499.0, "exit_reason": "STOP", "holding_s": 3600,
         "costs_total": 40.0, "expected_costs": {"commission": 15.0, "slippage": 10.0, "financing": 5.0,
                                                "of_which_spread": 12.0},
         "dual_ai": {"rule": "AGREE", "trader1_direction": "BUY", "trader2_direction": "BUY"}}
    return {**o, **over}


GOOD = dict(decision={"context": {"data_flags": []}, "max_hold_minutes": 1440},
            risk=[{"approved": True, "checks": [{"name": "news", "passed": True}, {"name": "quote", "passed": True}]}],
            gate_approved=True, position={"quote_at_entry": {"time": T - 20}}, per_trade_risk=500.0,
            max_quote_age_s=90)


def judge(o=None, **over):
    return verdict(o or trade(), **{**GOOD, **over})


def test_a_trade_that_passes_every_check_lost_to_the_market():
    v = judge()
    assert v["verdict"] == "MARKET" and v["market"] == "STOP" and v["faults"] == []
    assert judge(trade(exit_reason="TIME", net_pnl=-120.0))["market"] == "TIME_EXIT"
    assert judge(trade(exit_reason="TARGET", net_pnl=700.0))["market"] == "TARGET"


@pytest.mark.parametrize("over,fault", [
    ({"risk": []}, "RULES: no approving risk verdict"),
    ({"risk": [{"approved": False, "checks": []}]}, "RULES: no approving risk verdict"),
    ({"risk": [{"approved": True, "checks": [{"name": "news", "passed": False}]}]}, "RULES: approved with failed checks ['news']"),
    ({"gate_approved": False}, "GATE: no hard-gate approval"),
    ({"gate_approved": None}, "GATE: the gate's decision is not read"),
    ({"decision": None}, "DATA: the decision is not in the journal"),
    ({"decision": {"context": {"data_flags": ["stale_data"]}}}, "DATA: decided on flagged data"),
    ({"position": {"quote_at_entry": {"time": T - 91}}}, "DATA: filled on a quote 91s old"),
    ({"position": {"quote_at_entry": {"time": T + 6}}}, "DATA: filled on a quote -6s old"),
    ({"position": None}, "DATA: the fill's quote is not recorded"),
])
def test_each_thing_we_control_that_fails_makes_the_trade_ours(over, fault):
    v = judge(**over)
    assert v["verdict"] == "OURS" and v["market"] is None and any(f.startswith(fault) for f in v["faults"]), v["faults"]


@pytest.mark.parametrize("over,fault", [
    ({"planned_max_loss": 520.0, "net_pnl": -500.0}, "SIZE: sized to lose $520.00"),
    ({"planned_max_loss": None}, "SIZE: the planned maximum loss is not recorded"),
    ({"dual_ai": {"rule": "DEBATE", "trader1_direction": "BUY", "trader2_direction": "SELL"}}, "DESK: not both"),
    ({"dual_ai": {"rule": "AGREE", "trader1_direction": "BUY", "trader2_direction": "SELL"}}, "DESK: not both"),
    ({"holding_s": 1440 * 60 + 601, "exit_reason": "TIME"}, "TIME: held 1450 min"),
    ({"closed": datetime(2026, 10, 26, 2, 0, tzinfo=timezone.utc).timestamp()}, "WEEKEND"),
    ({"costs_total": 1.5 * 42.0 + 5.01}, "COSTS: $68.01 against $42.00 planned"),
])
def test_the_trades_own_record_can_make_it_ours(over, fault):
    v = judge(trade(**over))
    assert v["verdict"] == "OURS" and any(f.startswith(fault) for f in v["faults"]), v["faults"]


def test_the_limits_themselves_are_not_faults():
    edge = trade(planned_max_loss=500.0, holding_s=1440 * 60 + 600, costs_total=1.5 * 42.0 + 5.0,
                 closed=datetime(2026, 10, 23, 20, 59, tzinfo=timezone.utc).timestamp())  # 16:59 New York, Friday
    assert judge(edge, position={"quote_at_entry": {"time": T - 90}})["verdict"] == "MARKET"
    assert judge(trade(), position={"quote_at_entry": {"time": T + 5}})["verdict"] == "MARKET"  # the gate's 5 s


def test_a_win_that_broke_a_rule_is_still_ours():
    v = judge(trade(net_pnl=650.0, exit_reason="TARGET"), gate_approved=False)
    assert v["verdict"] == "OURS" and v["market"] is None


def test_a_stop_filled_beyond_the_plan_is_the_markets_and_named():
    roll = datetime(2026, 10, 21, 21, 5, tzinfo=timezone.utc).timestamp()
    v = judge(trade(net_pnl=-644.82, planned_max_loss=498.95, closed=roll))
    assert v["verdict"] == "MARKET" and v["market"] == "STOP_BEYOND_PLAN (in the rollover)"
    assert judge(trade(net_pnl=-640.0))["market"] == "STOP_BEYOND_PLAN"
    assert judge(trade(net_pnl=-499.0 * 1.02 - 2.0))["market"] == "STOP"  # inside the slack: within the plan


def test_an_unreadable_result_is_never_the_market():
    assert judge(trade(net_pnl=None))["verdict"] == "OURS"
    assert judge(trade(closed=None))["verdict"] == "OURS"


def test_the_summary_counts_the_market_and_us_and_lists_every_fault():
    vs = [judge(), judge(trade(decision_id="d2", exit_reason="TIME", net_pnl=-100.0)),
          judge(trade(decision_id="d3", net_pnl=-700.0)),
          judge(trade(decision_id="d4", net_pnl=-300.0), gate_approved=False),
          judge(trade(decision_id="d5", net_pnl=600.0, exit_reason="TARGET"))]
    s = summary(vs)
    assert (s["trades"], s["losses"], s["market_losses"], s["ours"], s["ours_losses"]) == (5, 4, 3, 1, 1)
    assert s["loss_usd"] == -1580.0 and s["market_loss_usd"] == -1280.0 and s["ours_loss_usd"] == -300.0
    assert s["market_by_kind"] == {"STOP": {"n": 1, "usd": -480.0}, "TIME_EXIT": {"n": 1, "usd": -100.0},
                                   "STOP_BEYOND_PLAN": {"n": 1, "usd": -700.0}}
    assert [t["decision_id"] for t in s["ours_trades"]] == ["d4"] and s["ours_trades"][0]["faults"]
    assert [t["decision_id"] for t in s["beyond_plan"]] == ["d3"]
