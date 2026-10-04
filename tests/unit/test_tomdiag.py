"""TOM-D diagnostics: the decomposition adds up to the simulator's net, the relative-day calendar is
right, concentration and break-even arithmetic are exact, and the weighting variant is causal."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from aitrader.research.discovery import rc, retail, tomdiag
from tests.unit.test_rc import FLAT, _prices, _rc_eq, weekdays


def _inst(names):
    return {n: retail.Instrument(n, "index", "US", spread_bps=2.0) for n in names}


def test_relative_days_mark_the_month_end_from_the_calendar():
    days = weekdays(45, start=date(2001, 1, 1))
    rel = tomdiag.relative_days(days, np.ones(45), before=2, after=3)
    named = {days[j]: d for j, d in rel.items()}
    assert named[date(2001, 1, 31)] == -1 and named[date(2001, 1, 30)] == -2
    assert named[date(2001, 2, 1)] == 1 and named[date(2001, 2, 5)] == 3
    assert date(2001, 1, 15) not in named


def test_the_trade_ledger_components_add_up_to_the_simulated_net():
    days = weekdays(700, start=date(2001, 1, 1))
    closes = {k: _prices(700, s) for k, s in (("A", 1), ("B", 2))}
    tg = rc.tom(days, closes, 2)
    inst = _inst(closes)
    costs = retail.Costs()
    res = retail.simulate(days, closes, tg, inst, FLAT, costs)
    bench = retail.simulate(days, closes, tg, inst, FLAT, costs.frictionless())
    led = tomdiag.trade_ledger(res, closes, inst, costs, bench)
    assert sum(r["net"] for r in led) == pytest.approx(float(np.sum(res.net())), abs=1e-12)
    r0 = led[0]
    assert r0["spread"] == pytest.approx(-2 * 0.5 * 1.0 / 1e4) and r0["slippage"] == pytest.approx(-2 * 0.5 * 1.0 / 1e4)
    assert r0["benchmark"] == pytest.approx(-0.5 * 2.0 / 100 * r0["calendar_days"] / 360)
    assert r0["markup"] == pytest.approx(-0.5 * 2.5 / 100 * r0["calendar_days"] / 360)
    assert r0["trading_days"] == 4  # days -1, +1, +2, +3
    comp = tomdiag.components(led, 1.0)
    assert comp["net"] == pytest.approx(sum(comp[k] for k in ("gross", "spread", "slippage", "commission", "benchmark",
                                                              "markup", "dividends")), abs=1e-9)


def test_day_returns_separate_the_window_from_the_drift():
    days = weekdays(260 * 6, start=date(2000, 1, 3))
    rng = np.random.default_rng(3)
    rel = tomdiag.relative_days(days, np.ones(len(days)))
    r = np.array([0.004 if rel.get(j) in (-1, 1, 2, 3) else 0.0 for j in range(len(days))]) + rng.normal(0, 0.002, len(days))
    c = 100 * np.exp(np.cumsum(r))
    d = tomdiag.day_returns(days, {"A": c}, days[0], days[-1] + timedelta(days=1))
    assert d["difference"]["tom_minus_other_bps"] == pytest.approx(40, abs=5) and d["difference"]["welch_t"] > 10
    assert abs(d["by_day"][-3]["mean_bps"]) < 5 and d["by_day"][2]["mean_bps"] > 30


def test_concentration_and_top_trade_shares_are_exact():
    c = tomdiag.concentration({"a": 6.0, "b": 3.0, "c": 2.0, "d": -1.0})
    assert c["best_1_share"] == 0.6 and c["best_3_share"] == 1.1 and c["positive"] == 3
    led = [{"net": x} for x in (5.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -3.0)]
    assert tomdiag.top_trades_share(led, 0.10) == round(5 / 10, 3)


def test_breakeven_is_where_the_net_reaches_zero():
    # net 2.0 with a markup line of -1.0 at 2.5%: each 1% of markup costs 0.4, so 2.0 more is 5% more
    assert tomdiag.breakeven(2.0, -1.0, 2.5) == 7.5
    assert tomdiag.breakeven(-0.5, -1.0, 2.5) == pytest.approx(1.25)
    assert tomdiag.breakeven(1.0, 0.0, 2.5) is None


def test_cagr_compounds_the_daily_net():
    days = weekdays(522, start=date(2001, 1, 1))  # 24 calendar months
    daily = np.full(522, 0.0)
    daily[0] = 0.21
    assert tomdiag.cagr(days, daily, days[0], date(2003, 1, 1)) == pytest.approx(0.1, abs=1e-4)


def test_the_bootstrap_interval_contains_a_planted_mean():
    rng = np.random.default_rng(1)
    m = list(rng.normal(0.01, 0.02, 240))
    b = tomdiag.bootstrap_mean_ci(m)
    assert b["annual_lo"] < float(np.mean(m)) * 12 < b["annual_hi"] and b["p_mean_le_zero"] < 0.01
    assert b["annual_hi"] - b["annual_lo"] < 0.06


def test_inverse_volatility_keeps_the_windows_and_reads_only_past_closes():
    days = weekdays(900, start=date(2001, 1, 1))
    rng = np.random.default_rng(5)
    closes = {"LO": 100 * np.exp(np.cumsum(rng.normal(0, 0.005, 900))),
              "HI": 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 900)))}
    tg = rc.tom(days, closes, 2)
    iv = tomdiag.inverse_vol(tg, closes)
    for k in closes:
        assert np.all((iv[k] > 0) <= (tg[k] > 0))  # never a position outside a window
    late = [j for j in range(300, 900) if tg["LO"][j] > 0]
    assert all(iv["LO"][j] > iv["HI"][j] for j in late)
    assert np.mean([iv["LO"][j] + iv["HI"][j] for j in late]) == pytest.approx(1.0, rel=0.05)
    entries = [j for j in range(1, 900) if tg["LO"][j] > 0 and tg["LO"][j - 1] == 0]
    for cut in (entries[-6], entries[-3]):  # a window opening exactly at the cut: its weight is set there
        changed = {k: np.r_[v[:cut + 1], v[cut + 1:] * np.exp(rng.normal(0, 0.1, 900 - cut - 1))] for k, v in closes.items()}
        iv2 = tomdiag.inverse_vol(tg, changed)
        for k in closes:
            assert np.array_equal(iv[k][:cut + 1], iv2[k][:cut + 1])
    w = [iv["LO"][j] for j in range(900) if tg["LO"][j] > 0]
    starts = [j for j in range(1, 900) if tg["LO"][j] > 0 and tg["LO"][j - 1] == 0]
    for s in starts:  # the weight is fixed for the whole window
        e = s
        while e < 900 and tg["LO"][e] > 0:
            assert iv["LO"][e] == iv["LO"][s]
            e += 1
    assert w


def test_adverse_excursion_counts_trades_through_a_stop():
    days = weekdays(10)
    c = {"A": np.array([100.0, 96.0, 94.0, 99.0, 101.0, 100, 100, 100, 100, 100])}
    led = [{"instrument": "A", "entry": str(days[0]), "exit": str(days[4])}]
    a = tomdiag.adverse_excursion(led, c, days)
    assert a["share_below_3pct"] == 1.0 and a["share_below_5pct"] == 1.0 and a["share_below_10pct"] == 0.0


def test_the_tom_diagnostic_runs_end_to_end_on_synthetic_data(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    rc_eq, rates = _rc_eq(tmp_path, monkeypatch)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import tom_diag
    days, closes, _ = rc_eq.load(rc_eq.UNIVERSE_A, rc_eq.JUDGE[1])
    names = ["US500", "UK100", "GER40", "AUS200"]
    uni = {k: rc_eq.UNIVERSE_A[k] for k in names}
    out = tom_diag.analyse("A", days, {k: closes[k] for k in names}, uni, rates, rc_eq.JUDGE)
    led = out.pop("_ledger")
    assert set(out["calendar_neighbourhood"]) == set(tom_diag.NEIGHBOURHOOD)
    assert set(out["cost_grid"]) == {"x1", "x1.25", "x1.5", "x2", "x3"}
    assert out["leave_out"]["pairs_tested"] == 6
    full = out["components_annual"]["full"]
    assert full["net"] == pytest.approx(out["headline"]["full"]["net_annual"], abs=1e-4)
    g = out["cost_grid"]
    assert g["x1"]["annual_return"] >= g["x2"]["annual_return"] >= g["x3"]["annual_return"]
    assert out["concentration"]["trades"] == len(led) > 1000


def test_the_tom_d_plan_is_frozen_once_registered():
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    import tom_diag
    spec = root / "research" / "specs" / "TOM-D.json"
    if not spec.exists():
        pytest.skip("TOM-D not yet planned")
    frozen = json.loads(spec.read_text())
    assert frozen["code_sha256"] == tom_diag.code_hash(), "TOM-D code changed after its plan was frozen"
    assert frozen["sha256"] == tom_diag.spec_sha(frozen["spec"])
