"""RADX-1 (aitrader/perf/radx.py) on ledgers built so the answer is known, and the statistics that say when they are
undefined (aitrader/perf/stats.py)."""

from __future__ import annotations

import pytest

from aitrader.perf import radx
from aitrader.perf.stats import check, drawdown, mean_t, trade_stats

H = 3600
T0 = radx.CUT - 1000 * H


def pos(coin, opened, hours, net, spread=0.30, reason="spread_reversed", cost=34.0):
    """A closed position whose net is exactly `net` bp: all of it funding, no price move."""
    return {"id": f"{coin}-a-b-{opened}", "coin": coin, "opened": opened, "closed": opened + hours * H,
            "short_px0": 1.0, "long_px0": 1.0, "short_px": 1.0, "long_px": 1.0, "funding_bp": net + cost,
            "cost_bp": cost, "entry_spread_apr": spread, "reason": reason}


def ledger(closed):
    return {"closed": closed, "open": [], "marks": [{"t": max(p["closed"] for p in closed), "pnl_bp_total": 0.0, "open": 0}]}


def test_net_is_funding_plus_both_legs_less_costs():
    p = {"funding_bp": 10.0, "cost_bp": 34.0, "short_px0": 2.0, "short_px": 1.9, "long_px0": 2.0, "long_px": 1.95}
    # the short leg fell 5% (a gain of 500 bp), the long leg fell 2.5% (a loss of 250 bp)
    assert radx.net_bp(p) == pytest.approx(10.0 + 250.0 - 34.0)


def test_a_position_is_classed_by_what_was_known_when_it_was_opened():
    rows = radx.classify([pos("A", T0, 2, -30, reason="spread_decayed"),
                          pos("A", T0 + 5 * H, 2, -34),                       # 3 h after a decayed exit: churn
                          pos("A", T0 + 8 * H, 2, 5, reason="spread_decayed"),  # 1 h after a REVERSED exit: not churn
                          pos("A", T0 + 30 * H, 2, 5),                       # 20 h after a decayed exit: too late
                          pos("B", T0 + 5 * H, 2, 5, spread=0.80)])           # another coin's first position
    by = {(r["coin"], r["opened"]): r for r in rows}
    assert [by[("A", T0 + k * H)]["churn"] for k in (0, 5, 8, 30)] == [False, True, False, False]
    assert by[("A", T0 + 5 * H)]["hours_since_previous"] == 3 and by[("A", T0 + 5 * H)]["previous_reason"] == "spread_decayed"
    assert by[("B", T0 + 5 * H)]["hours_since_previous"] is None and not by[("B", T0 + 5 * H)]["thin"]
    assert by[("A", T0)]["thin"]


def test_a_position_reopened_in_the_hour_it_was_closed_is_churn():
    rows = radx.classify([pos("A", T0, 1, -34, reason="spread_decayed"), pos("A", T0 + H, 1, -34)])
    assert rows[1]["hours_since_previous"] == 0 and rows[1]["churn"]


def build(later_thin=-30.0, later_churn=-34.0, n=20):
    """A design part, and a later part with `n` thin entries and `n` churn entries at the given mean net (with a
    little spread between positions), and good positions beside them."""
    closed, t = [], T0
    for i in range(10):
        closed += [pos(f"D{i}", t + i * H, 3, -30)]
    t = radx.CUT
    for i in range(n):
        wob = (i % 5 - 2) * 2.0
        closed += [pos(f"T{i % 7}", t + i * 40 * H, 3, later_thin + wob, spread=0.30)]
        closed += [pos(f"C{i % 4}", t + i * 40 * H + 10 * H, 1, 9.0, spread=0.90, reason="spread_decayed"),
                   pos(f"C{i % 4}", t + i * 40 * H + 12 * H, 1, later_churn + wob, spread=0.90)]
        closed += [pos(f"G{i % 3}", t + i * 40 * H + 20 * H, 30, 40.0 + wob, spread=0.90)]
    return ledger(closed)


def test_both_predictions_hold_on_a_later_part_built_to_lose_there():
    out = radx.evaluate(build())
    assert out["verdict"] == "PASSED" and out["gates"] == {"P1_thin_entries": True, "P2_churn_after_decay": True}
    later = out["later"]
    assert later["P1_thin_entries"]["positions"] == 20 and later["P1_thin_entries"]["mean_bp"] == pytest.approx(-30.0)
    assert later["P2_churn_after_decay"]["positions"] == 20 and later["P2_churn_after_decay"]["mean_bp"] == pytest.approx(-34.0)
    assert later["P1_thin_entries"]["others"] == 60 and out["design"]["positions"] == 10


def test_the_verdict_reads_the_later_part_only_and_fails_when_a_class_does_not_lose():
    out = radx.evaluate(build(later_thin=+12.0))
    assert out["verdict"] == "FAILED" and out["gates"] == {"P1_thin_entries": False, "P2_churn_after_decay": True}
    # the design part lost in the thin class all the same: it does not decide
    assert out["design"]["P1_thin_entries"]["mean_bp"] == pytest.approx(-30.0)


def test_a_loss_that_is_not_told_from_zero_does_not_hold():
    led = build(n=3)  # three positions a class: a mean of -30 with a spread, but too few to reach the bar... unless tight
    side = radx.evaluate(led)["later"]["P1_thin_entries"]
    assert side["positions"] == 3
    wide = ledger([pos("A", radx.CUT + i * 50 * H, 2, x) for i, x in enumerate((-200.0, 150.0, -60.0, 30.0, -90.0, 20.0))])
    s = radx.evaluate(wide)["later"]["P1_thin_entries"]
    assert s["mean_bp"] < 0 and s["t"] > -radx.BAR and not radx.holds(s)


def test_one_coin_must_not_carry_a_class():
    closed = [pos("BAD", radx.CUT + i * 50 * H, 2, -80.0 - i) for i in range(12)]
    closed += [pos(f"OK{i}", radx.CUT + i * 50 * H + 5 * H, 2, 6.0 + (i % 3)) for i in range(4)]
    s = radx.evaluate(ledger(closed))["later"]["P1_thin_entries"]
    assert s["t"] <= -radx.BAR and s["worst_coin"] == "BAD" and s["mean_bp_without_worst_coin"] > 0
    assert not radx.holds(s)


def test_open_positions_are_left_out():
    led = build()
    led["open"] = [{**pos("T0", radx.CUT + 9999 * H, 1, -500.0), "closed": None, "reason": None}]
    assert radx.evaluate(led)["later"]["positions"] == radx.evaluate(build())["later"]["positions"]


# ── statistics that say when they are undefined ─────────────────────────────

def test_no_closed_trade_gives_no_ratio_and_says_why():
    s = trade_stats([])
    assert s["closed"] == 0 and s["total"] == 0 and s["sample"] == "none"
    for k in ("win_rate", "expectancy", "t", "average_win", "average_loss", "profit_factor"):
        assert s[k] is None and s["undefined"][k] == "no closed trade"


def test_ratios_of_a_few_trades_are_computed_and_labelled_a_small_sample():
    s = trade_stats([10.0, -4.0, 6.0, -2.0])
    assert s["win_rate"] == 0.5 and s["average_win"] == 8.0 and s["average_loss"] == -3.0
    assert s["profit_factor"] == pytest.approx(16.0 / 6.0) and s["expectancy"] == 2.5 and s["sample"] == "insufficient"
    assert trade_stats([1.0] * 30)["sample"] == "ok"


def test_a_profit_factor_without_a_loss_is_undefined_never_infinite_or_zero():
    s = trade_stats([5.0, 7.0])
    assert s["profit_factor"] is None and "no losing trade" in s["undefined"]["profit_factor"]
    assert s["average_loss"] is None and s["win_rate"] == 1.0
    assert trade_stats([-5.0])["average_win"] is None and trade_stats([-5.0])["t"] is None


def test_mean_t_and_drawdown():
    assert mean_t([]) == (None, None) and mean_t([3.0]) == (3.0, None) and mean_t([2.0, 2.0]) == (2.0, None)
    m, t = mean_t([1.0, 2.0, 3.0])
    assert m == 2.0 and t == pytest.approx(2.0 / (1.0 / 3 ** 0.5))
    d = drawdown([100.0, 99.0, 104.0, 101.0, 103.0])
    assert d["max"] == 3.0 and d["now"] == 1.0 and (d["peak_at"], d["trough_at"]) == (2, 3)
    assert drawdown([100.0, 98.0])["max"] == 2.0 and drawdown([])["max"] is None


def test_a_reconciliation_fails_on_a_missing_figure_and_on_a_difference_beyond_its_tolerance():
    assert check("a", 10.0, 10.004, 0.01)["ok"] and not check("a", 10.0, 10.02, 0.01)["ok"]
    assert not check("a", None, 1.0)["ok"] and not check("a", 1.0, float("nan"), 1.0)["ok"]
    assert check("a", "x", "x")["ok"] and not check("a", "x", "y")["ok"]
