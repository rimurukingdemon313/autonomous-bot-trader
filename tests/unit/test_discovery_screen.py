"""Statistics with known answers, trades taken as an account would take them, and a screen that
finds an effect planted by construction — and nothing in a market that has none."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from aitrader.research.discovery.screen import Grid, screen
from aitrader.research.discovery.stats import bh, cluster_t, deflated_sharpe, p_one_sided, week_of
from aitrader.research.discovery.study import (PURGE_BARS, Binning, Condition, Segment, Study, epoch, fit_binning,
                                               greedy, segment_rows)
from aitrader.research.labels import BUY, SELL, CostModel
from tests.unit.discovery_market import planted

FREE = CostModel(0.0, 0.0, 0.0)
REAL = CostModel(0.1, 0.7, 0.0)  # outcomes in R then vary with ATR, as real ones do
ALL = Segment("all", "fit", date(2010, 1, 1), date(2011, 1, 1))
A_GROUPS = {"A": fit_binning("A", {}, groups=((0,), (1,), (2,)))}


def binnings(data, seg=ALL):
    st = Study(data, seg, {}, FREE)
    vals = {s: data[s].columns["B"][st.rows[s]] for s in st.symbols}
    return A_GROUPS | {"B": fit_binning("B", vals)}


# ── statistics ─────────────────────────────────────────────────────────


def test_benjamini_hochberg_matches_a_hand_computed_case():
    rej, qv = bh(np.array([0.01, 0.04, 0.03, 0.2]), 0.10)
    assert rej.tolist() == [True, True, True, False]
    assert qv == pytest.approx([0.04, 0.16 / 3, 0.16 / 3, 0.2])
    assert bh(np.array([0.5, 0.6]), 0.1)[0].tolist() == [False, False]


def test_clustering_by_week_does_not_reward_counting_one_week_five_times():
    rng = np.random.default_rng(0)
    r = rng.normal(0.2, 1.0, 60)
    weeks = np.arange(60)
    once = cluster_t(r, weeks)
    five = cluster_t(np.repeat(r, 5), np.repeat(weeks, 5))
    assert five["t"] == pytest.approx(once["t"])  # a naive t would be sqrt(5) times larger
    assert five["n"] == 300 and five["clusters"] == 60
    assert cluster_t(np.full(50, 1.5), np.arange(50))["t"] is None  # no variance: no t, not t = 1e14
    assert p_one_sided(None) == 1.0 and p_one_sided(0.0) == pytest.approx(0.5)


def test_weeks_start_on_monday():
    mon = epoch(date(2010, 1, 4))
    assert week_of(np.array([mon - 1, mon, mon + 6 * 86400 + 86399]))[1:].tolist() == [week_of(np.array([mon]))[0]] * 2
    assert week_of(np.array([mon - 1]))[0] == week_of(np.array([mon]))[0] - 1


def test_the_deflated_sharpe_ratio_shrinks_as_more_trials_were_run():
    r = np.random.default_rng(1).normal(0.1, 1.0, 400)
    one, many = deflated_sharpe(r, 1), deflated_sharpe(r, 5000)
    assert one["dsr"] > many["dsr"] and many["expected_max_null"] > 0


# ── study mechanics ────────────────────────────────────────────────────


def test_greedy_takes_one_position_at_a_time():
    mask = np.ones(10, bool)
    free = np.arange(10) + 3
    assert greedy(mask, free).tolist() == [0, 3, 6, 9]
    mask[3] = False
    assert greedy(mask, free).tolist() == [0, 4, 7]


def test_a_segment_purges_rows_whose_outcome_would_cross_its_end():
    data = planted(n=500)
    sd = data["AAA"]
    end_t = int(sd.series.available_at[300])
    seg = Segment("x", "fit", date(2010, 1, 1), date(2010, 1, 13))  # 2010-01-13 00:00 = bar 216's close
    rows = segment_rows(sd, seg)
    t1 = epoch(seg.end)
    assert rows.max() + PURGE_BARS < len(sd.series)
    assert sd.series.available_at[rows.max() + PURGE_BARS] <= t1 < sd.series.available_at[rows.max() + PURGE_BARS + 1]
    assert (sd.series.available_at[rows] >= epoch(seg.start)).all() and end_t > t1


def test_bins_are_fitted_per_symbol_on_the_rows_given_and_frozen():
    b = fit_binning("x", {"S": np.arange(90.0), "T": np.arange(900.0, 990.0)})
    assert b.apply("S", np.array([0.0, 45.0, 89.0, np.nan])).tolist() == [0, 1, 2, -1]
    assert b.apply("T", np.array([905.0, 950.0, 980.0])).tolist() == [0, 1, 2]
    assert b.apply("U", np.array([1.0])).tolist() == [-1]  # no edges for an unseen symbol: missing
    again = Binning.from_json(b.to_json())
    assert again.apply("S", np.arange(90.0)).tolist() == b.apply("S", np.arange(90.0)).tolist()
    g = fit_binning("s", {}, groups=((0,), (1, 2), (3, 4)))
    assert g.apply("S", np.array([0, 1, 2, 3, 4, 6])).tolist() == [0, 1, 1, 2, 2, -1]


def test_conditions_have_readable_keys_that_round_trip():
    c = Condition((("er120", 2), ("r24", 0)))
    assert c.key == "er120=high&r24=low" and Condition.parse(c.key) == c
    with pytest.raises(ValueError):
        Condition((("r24", 0), ("r24", 1)))


def test_taken_trades_never_overlap_on_one_instrument():
    data = planted()
    st = Study(data, ALL, binnings(data), FREE)
    tr = st.trades({s: np.ones(len(st.rows[s]), bool) for s in st.symbols}, "E2", BUY)
    for s in st.symbols:
        mine = tr.symbol == s
        rows = tr.row[mine]
        exits = rows + tr.bars[mine]  # entry bar row+1 plus bars held - 1
        assert (rows[1:] >= exits[:-1]).all()


# ── the screen ─────────────────────────────────────────────────────────


def test_the_screen_finds_the_planted_pattern_and_not_its_mirror():
    data = planted()
    st = Study(data, ALL, binnings(data), REAL)
    res = screen(st, Grid(("B",), ("A",)), min_n=30, keep=5)
    assert res["tests"] == 2 * (6 + 9) == len(res["table"])
    keys = [(r["condition"], r["side"]) for r in res["survivors"]]
    assert ("A=high", "BUY") in keys
    assert all(side == "BUY" and "A=high" in cond for cond, side in keys)
    sell = next(r for r in res["table"] if r["condition"] == "A=high" and r["side"] == "SELL")
    assert sell["mean_R"] < 0 and not sell["discovery"]


def test_the_screen_reports_nothing_in_a_market_with_no_effect():
    data = planted(plant=False)
    st = Study(data, ALL, binnings(data), REAL)
    res = screen(st, Grid(("B",), ("A",)), min_n=30)
    assert res["discoveries"] == 0 and res["testable"] > 0


def test_a_cell_with_too_few_trades_is_counted_but_cannot_be_a_discovery():
    data = planted()
    st = Study(data, ALL, binnings(data), FREE)
    res = screen(st, Grid(("B",), ("A",)), min_n=10_000)
    assert res["tests"] == 30 and res["testable"] == 0 and res["discoveries"] == 0
    assert all(r["p"] == 1.0 for r in res["table"])


def test_screening_twice_gives_identical_tables():
    a = screen(Study(planted(), ALL, binnings(planted()), FREE), Grid(("B",), ("A",)), min_n=30)
    b = screen(Study(planted(), ALL, binnings(planted()), FREE), Grid(("B",), ("A",)), min_n=30)
    assert a == b
