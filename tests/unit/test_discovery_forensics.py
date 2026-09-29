"""Loss causes on hand-built price paths: each path is constructed so its cause is known."""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.research.discovery.exits import EXIT_BY_KEY
from aitrader.research.discovery.forensics import CAUSES, breakdown, classify
from aitrader.research.labels import BUY, CostModel
from tests.unit.test_discovery_exits import bars, flat

ATR = 0.0010
FREE = CostModel(0.0, 0.0, 0.0)
E1 = EXIT_BY_KEY["E1"]  # stop 1 ATR, target 1.5 ATR, 24 bars


def run(path, costs=FREE, row=1, half=0.0, exit_=E1):
    s = bars(path, half)
    return classify(s, row, BUY, exit_, 0.0001, costs, atr=np.full(len(s), ATR))


def test_a_winner_has_no_cause():
    path = flat(2) + [[1.1000, 1.1016, 1.0999, 1.1015]] + flat(30, 1.1015)
    assert run(path)["cause"] is None and run(path)["r"] > 0


def test_a_gross_winner_that_costs_turn_into_a_loss():
    path = flat(2) + [[1.1000, 1.1001, 1.0999, 1.1001]] * 22 + flat(10, 1.1001)  # +0.1R by the time exit
    res = run(path, costs=CostModel(0.0, 2.0, 0.0))  # 2 pips of commission on a 10-pip risk
    assert res["r"] < 0 and res["cause"] == "COSTS"


def test_a_trade_that_was_one_r_up_and_ended_red_gave_it_back():
    path = flat(2) + [[1.1000, 1.1012, 1.0999, 1.1010], [1.1010, 1.1011, 1.0985, 1.0988]] + flat(30, 1.0988)
    assert run(path)["cause"] == "EXIT_GAVE_BACK"


def test_a_stop_hunt_before_the_move_is_a_stop_too_tight():
    # dips 1.2 ATR (stops a 1-ATR stop, not a 2-ATR one), then rallies to the target
    path = flat(2) + [[1.1000, 1.1001, 1.0988, 1.0990]] + [[1.0990 + 0.0003 * k, 1.0993 + 0.0003 * k,
                                                           1.0989 + 0.0003 * k, 1.0993 + 0.0003 * k]
                                                          for k in range(10)] + flat(30, 1.1020)
    res = run(path)
    assert res["reason"] == -1 and res["cause"] == "STOP_TOO_TIGHT"


def test_a_straight_fall_is_the_wrong_direction():
    path = flat(2) + [[1.1000 - 0.0003 * k, 1.1000 - 0.0003 * k, 0.9999 - 0.0003 * k + 0.1, 1.0997 - 0.0003 * k]
                      for k in range(30)]
    path = [[o, max(o, c) + 0.00001, min(o, c) - 0.00001, c] for o, _, _, c in path]
    assert run(path)["cause"] == "WRONG_DIRECTION"


def test_the_breakdown_reports_shares_of_trades_and_of_r_lost():
    rs = [{"r": -1.0, "cause": "COSTS", "cost_r": 0.1, "mfe_r": 0.3, "mae_r": -1.0},
          {"r": -0.5, "cause": "NORMAL_VARIANCE", "cost_r": 0.1, "mfe_r": 0.1, "mae_r": -0.6},
          {"r": 1.5, "cause": None, "cost_r": 0.1, "mfe_r": 1.6, "mae_r": -0.2}]
    b = breakdown(rs)
    assert b["losers"] == 2 and b["winners"] == 1 and set(b["causes"]) == set(CAUSES)
    assert b["causes"]["COSTS"]["share_of_losses"] == 0.5
    assert b["causes"]["COSTS"]["share_of_R_lost"] == pytest.approx(1.0 / 1.5, abs=1e-3)
