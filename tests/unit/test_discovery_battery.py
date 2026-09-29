"""The battery passes an edge planted by construction and fails each kind of fake edge for the
reason it is fake; the decomposition is checked with a pencil."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from aitrader.research.discovery.battery import REGIME_CONTEXT, BatteryRules, decompose, regime_binnings, run_battery
from aitrader.research.discovery.study import Condition, Segment, Study, Trades, fit_binning
from aitrader.research.labels import BUY, SELL, CostModel
from tests.unit.discovery_market import planted

REAL = CostModel(0.1, 0.7, 0.0)
SEG = Segment("confirmation", "judge", date(2010, 1, 1), date(2013, 1, 1))
N = 20_000  # ~2.3 years of hourly bars: enough years for the yearly check
RULES = BatteryRules(t_threshold=3.0, permutations=60, random_draws=5)
A_HIGH = Condition((("A", 2),))


def study(data, costs=REAL):
    base = Study(data, SEG, {}, costs)
    vals = lambda f: {s: data[s].columns[f][base.rows[s]] for s in base.symbols}  # noqa: E731
    binn = {"A": fit_binning("A", {}, groups=((0,), (1,), (2,))), "B": fit_binning("B", vals("B"))}
    ctx = regime_binnings({"er120": vals("er120"), "vol_ratio": vals("vol_ratio")})
    st = Study(data, SEG, binn, costs, context=ctx)
    perturbed = [{"B": fit_binning("B", vals("B"), quantiles=(1 / 3 + d, 2 / 3 + d))} for d in (-0.05, 0.05)]
    return st, perturbed


@pytest.fixture(scope="module")
def edge():
    return study(planted(n=N))


def test_a_planted_edge_passes_every_check(edge):
    st, pert = edge
    res = run_battery(st, Condition((("B", 2), ("A", 2))), BUY, "E1", RULES, perturbed=pert, trials=30)
    assert res["verdict"] == "VALIDATED", res["failed"]
    assert res["checks"]["perturbation"]["mean_R"][0] > 0 and len(res["checks"]["perturbation"]["mean_R"]) == 2
    assert set(res["checks"]) == set(RULES.describe())  # every declared check ran, none skipped
    assert res["decomposition"]["by_regime"] and res["deflated_sharpe"]["dsr"] > 0.9


def test_the_mirror_of_an_edge_fails(edge):
    st, _ = edge
    res = run_battery(st, A_HIGH, SELL, "E1", RULES)
    assert res["verdict"] == "REJECTED"
    assert {"significance", "beats_random", "permutation", "outliers"} <= set(res["failed"])


def test_a_market_without_the_effect_fails_on_the_core_checks():
    st, _ = study(planted(n=N, plant=False))
    res = run_battery(st, A_HIGH, BUY, "E1", RULES)
    assert res["verdict"] == "REJECTED" and "significance" in res["failed"] and "permutation" in res["failed"]


def test_an_edge_on_one_instrument_fails_the_cross_instrument_checks():
    st, _ = study(planted(n=N, weak=("BBB", "CCC")))
    res = run_battery(st, A_HIGH, BUY, "E1", RULES)
    assert res["verdict"] == "REJECTED" and res["checks"]["significance"]["pass"]  # significant, yet one market
    assert {"instruments", "leave_one_out"} <= set(res["failed"])
    assert res["checks"]["instruments"]["positive"] == ["AAA"]
    assert res["checks"]["leave_one_out"]["worst"] == "AAA"


def test_an_edge_that_reverses_in_one_regime_fails_the_regime_check():
    st, _ = study(planted(n=N, regime_flip=True))
    res = run_battery(st, A_HIGH, BUY, "E1", RULES)
    assert res["verdict"] == "REJECTED" and "regimes" in res["failed"]
    assert all(k.startswith("er_low") for k in res["checks"]["regimes"]["significantly_negative"])


def test_an_edge_that_costs_eat_fails_the_cost_stress():
    data = planted(n=N)
    free, _ = study(data, CostModel(0.0, 0.0, 0.0))
    m0 = float(free.trades(free.masks(A_HIGH), "E1", BUY).r.mean())
    atr = np.median(np.concatenate([d.atr[free.rows[s]] for s, d in data.items()]))
    comm = (m0 - 0.3) * atr / 0.0001  # leaves about +0.3R before stress
    st, _ = study(data, CostModel(0.0, comm, 0.0))
    res = run_battery(st, A_HIGH, BUY, "E1", RULES)
    assert res["checks"]["significance"]["mean_R"] > 0 and res["verdict"] == "REJECTED"
    assert "costs_stress" in res["failed"] and res["checks"]["costs_stress"]["mean_R"] < 0


def test_a_veto_is_judged_on_the_losses_it_claims(edge):
    st, _ = edge
    res = run_battery(st, A_HIGH, SELL, "E1", RULES, kind="veto")
    assert res["verdict"] == "VALIDATED", res["failed"]
    assert res["decomposition"]["mean_R"] < 0  # the decomposition reports the trades as they are


def test_the_battery_gives_the_same_answer_twice(edge):
    st, _ = edge
    a = run_battery(st, A_HIGH, BUY, "E1", RULES, key="H-1")
    b = run_battery(st, A_HIGH, BUY, "E1", RULES, key="H-1")
    a.pop("trades"), b.pop("trades")
    assert a == b


def test_the_decomposition_matches_a_hand_count():
    r = np.array([1.5, -1.0, -1.0, 2.0, -1.0, 0.0])
    t = 1_262_563_200 + 86400 * np.arange(6)
    tr = Trades(symbol=np.array(["X", "X", "Y", "Y", "X", "Y"], dtype=object), row=np.arange(6), t=t,
                exit_t=t + 3600, r=r, mfe=np.full(6, 1.0), mae=np.full(6, -0.5), cost=np.full(6, 0.1),
                bars=np.array([3, 5, 2, 8, 4, 24]), reason=np.array([1, -1, -1, 1, -1, 0]))
    d = decompose(tr)
    assert d["win_rate"] == pytest.approx(2 / 6, abs=1e-4)
    assert d["avg_win_R"] == pytest.approx(1.75) and d["avg_loss_R"] == pytest.approx(-1.0)
    assert d["profit_factor"] == pytest.approx(3.5 / 3.0, abs=1e-3) and d["total_R"] == pytest.approx(0.5)
    assert d["max_drawdown_R"] == pytest.approx(2.0)  # 1.5 -> -0.5
    assert d["longest_losing_streak"] == 2
    assert d["cost_R"]["gross_mean_R"] == pytest.approx(0.5 / 6 + 0.1, abs=1e-4)  # reported to 5 places
    assert d["exit_reasons"] == {"stop": 3, "time": 1, "target": 2}
    assert d["by_instrument"]["X"]["n"] == 3 and d["by_year"]["2010"]["n"] == 6
    assert set(REGIME_CONTEXT).isdisjoint(tr.context) and "by_regime" not in d
