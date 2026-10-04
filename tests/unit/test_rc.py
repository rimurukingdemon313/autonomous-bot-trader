"""RC programs: retail CFD economics are charged exactly as declared, every rule is causal, a
planted effect is found and a random walk is not."""

from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np
import pytest

from aitrader.research.discovery import rc, retail


def weekdays(n, start=date(2000, 1, 3)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


FLAT = lambda key, d: 2.0  # noqa: E731  every policy rate 2%


def idx_inst(name="X", spread=2.0, tr=False):
    return {name: retail.Instrument(name, "index", "US", spread_bps=spread, total_return=tr)}


# ── retail economics ────────────────────────────────────────────────────

def test_an_index_long_pays_spread_slippage_benchmark_and_markup_and_gets_no_dividend():
    days = [date(2020, 1, 6), date(2020, 1, 7), date(2020, 1, 10)]  # 1 then 3 calendar days
    c = {"X": np.array([100.0, 101.0, 102.0])}
    t = {"X": np.array([1.0, 1.0, 0.0])}
    r = retail.simulate(days, c, t, idx_inst(), FLAT, retail.Costs())
    unit = (2.0 / 2 + 1.0) / 1e4
    assert r.cost["X"][0] == pytest.approx(unit) and r.cost["X"][2] == pytest.approx(unit)
    assert r.gross["X"][1] == pytest.approx(0.01) and r.gross["X"][2] == pytest.approx(102 / 101 - 1)
    assert r.financing["X"][1] == pytest.approx(-(2.0 + 2.5) / 100 / 360)
    assert r.financing["X"][2] == pytest.approx(-(2.0 + 2.5) / 100 * 3 / 360)
    assert np.all(r.dividends["X"] == 0)
    tr = r.trades[0]
    assert tr["side"] == 1 and tr["days"] == 4
    assert tr["ret_per_unit"] == pytest.approx(r.net().sum())


def test_an_index_short_receives_benchmark_minus_markup_and_pays_the_dividend():
    days = [date(2020, 1, 6), date(2020, 1, 7)]
    r = retail.simulate(days, {"X": np.array([100.0, 99.0])}, {"X": np.array([-0.5, -0.5])}, idx_inst(), FLAT,
                        retail.Costs())
    assert r.financing["X"][1] == pytest.approx(0.5 * (2.0 - 2.5) / 100 / 360)  # negative: the markup exceeds the rate
    assert r.dividends["X"][1] == pytest.approx(-0.5 * 3.0 / 100 / 365)
    assert r.gross["X"][1] == pytest.approx(0.005)
    tr = retail.simulate(days, {"X": np.array([100.0, 99.0])}, {"X": np.array([-0.5, -0.5])}, idx_inst(tr=True), FLAT,
                         retail.Costs())
    assert np.all(tr.dividends["X"] == 0)  # a total-return series already contains its dividends


def test_fx_financing_is_the_rate_differential_minus_the_markup():
    days = [date(2020, 1, 6), date(2020, 1, 7)]
    inst = {"AUD": retail.Instrument("AUD", "fx", "AUD", spread_pips=0.3)}
    rates = lambda k, d: {"AUD": 5.0, "USD": 1.0}[k]  # noqa: E731
    r = retail.simulate(days, {"AUD": np.array([0.7, 0.7])}, {"AUD": np.array([1.0, 1.0])}, inst, rates, retail.Costs())
    assert r.financing["AUD"][1] == pytest.approx((4.0 - 1.5) / 100 / 365)
    s = retail.simulate(days, {"AUD": np.array([0.7, 0.7])}, {"AUD": np.array([-1.0, -1.0])}, inst, rates, retail.Costs())
    assert s.financing["AUD"][1] == pytest.approx((-4.0 - 1.5) / 100 / 365)
    pips = 0.3 / 2 + 0.7 / 2 + 0.1
    assert r.cost["AUD"][0] == pytest.approx(pips * 0.0001 / 0.7)
    jpy = {"JPY": retail.Instrument("JPY", "fx", "JPY", spread_pips=0.3, pip=0.01, usd_per_unit_quote=False)}
    q = retail.simulate(days, {"JPY": np.array([1 / 150.0, 1 / 150.0])}, {"JPY": np.array([1.0, 1.0])}, jpy,
                        lambda k, d: 0.0, retail.Costs())
    assert q.cost["JPY"][0] == pytest.approx(pips * 0.01 / 150.0)  # pips in the market quote (USDJPY)


def test_a_position_is_never_held_where_its_rate_is_unknown():
    days = weekdays(4)
    rate = lambda k, d: float("nan") if d == days[1] else 2.0  # noqa: E731
    r = retail.simulate(days, {"X": np.array([100.0, 101, 102, 103])}, {"X": np.ones(4)}, idx_inst(), rate,
                        retail.Costs())
    assert list(r.position["X"]) == [1.0, 0.0, 1.0, 1.0]
    assert r.gross["X"][2] == 0.0  # flat over the unknown day's night


def test_stressed_costs_double_every_assumption_and_frictionless_removes_them():
    c = retail.Costs().stressed(2.0)
    assert (c.slippage_bps, c.index_markup_pa, c.fx_markup_pa, c.spread_mult, c.fx_commission_pips_rt) == (2.0, 5.0, 3.0, 2.0, 1.4)
    f = retail.Costs().frictionless()
    assert (f.slippage_bps, f.index_markup_pa, f.spread_mult, f.short_dividend_pa) == (0, 0, 0, 0)


def test_delay_executes_every_target_one_own_close_later():
    c = {"X": np.array([1.0, np.nan, 2.0, 3.0, 4.0])}
    d = retail.delay({"X": np.array([0.0, 9, 1, 0, 1])}, c, 1)
    assert list(d["X"]) == [0.0, 0.0, 0.0, 1.0, 0.0]


def test_month_stats_and_profit_factor_are_computed_from_the_months():
    s = retail.month_stats([0.02, -0.01, 0.03, -0.01])
    assert s["mean_monthly"] == pytest.approx(0.0075) and s["profit_factor_months"] == pytest.approx(2.5)
    assert s["max_drawdown"] == pytest.approx(0.01) and s["positive_months"] == 0.5


# ── data helpers ────────────────────────────────────────────────────────

def test_rates_switch_to_the_euro_go_stale_and_exclude_hyperinflation(tmp_path):
    from aitrader.data.rates import available_at
    rows = [("DE", date(1998, 12, 30), 3.0), ("XM", date(1999, 1, 4), 3.5), ("BR", date(2000, 1, 3), 45.0),
            ("US", date(2000, 1, 3), 5.0)]
    p = tmp_path / "r.csv"
    p.write_text("area,effective_date,value_pct,available_at_epoch\n" +
                 "".join(f"{a},{d},{v},{available_at('POLICY', d)}\n" for a, d, v in rows))
    r = rc.Rates(p)
    assert r.at("DE|XM", date(1998, 12, 31)) == 3.0
    assert math.isnan(r.at("DE|XM", date(1999, 1, 1)))  # the euro rate is not public yet
    assert r.at("DE|XM", date(1999, 1, 5)) == 3.5
    assert math.isnan(r.at("BR", date(2000, 1, 4)))  # above 25%: not held
    assert r.at("US", date(2000, 1, 10)) == 5.0 and math.isnan(r.at("US", date(2000, 1, 11)))  # 8 days: stale


def test_clean_removes_a_one_day_misprint_and_a_frozen_feed_and_nothing_else():
    days = weekdays(12)
    v = [100, 101, 150, 101, 102, 103, 103, 103, 103, 103, 103, 104]
    d2, v2, rep = rc.clean(days, v)
    assert rep == {"spikes_removed": 1, "stale_removed": 2} and 150 not in v2 and len(v2) == 9
    assert rc.clean(days, [100 * 1.3 ** k for k in range(12)])[2] == {"spikes_removed": 0, "stale_removed": 0}


# ── rules: causality ────────────────────────────────────────────────────

def _prices(n, seed):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))


@pytest.mark.parametrize("rule", ["dip", "regime", "volman", "breakout"])
def test_own_price_rules_never_read_a_later_close(rule):
    days = weekdays(900)
    c = {"A": _prices(900, 1), "B": _prices(900, 2)}
    fn = {"dip": rc.dip, "regime": rc.regime, "volman": rc.volman, "breakout": rc.breakout}[rule]
    full = fn(days, c, 2)
    for cut in (300, 555, 700):
        changed = {k: np.r_[v[:cut + 1], v[cut + 1:] * 1.5 + 7] for k, v in c.items()}
        part = fn(days, changed, 2)
        for k in c:
            assert np.array_equal(full[k][:cut + 1], part[k][:cut + 1]), (rule, cut, k)


def test_turn_of_the_month_reads_the_calendar_only_and_covers_days_minus_one_to_plus_three():
    days = weekdays(80, start=date(2001, 1, 1))
    c = {"A": _prices(80, 3)}
    a = rc.tom(days, c, 1)["A"]
    b = rc.tom(days, {"A": _prices(80, 4)}, 1)["A"]
    assert np.array_equal(a, b)
    held = [days[j] for j in range(80) if a[j] > 0]
    # the position from the second-to-last close of January to the third close of February
    assert held[:4] == [date(2001, 1, 30), date(2001, 1, 31), date(2001, 2, 1), date(2001, 2, 2)]
    exit_ = days.index(date(2001, 2, 5))
    assert a[exit_] == 0.0


def test_cross_sectional_momentum_fills_after_the_decision_and_never_reads_later_prices():
    days = weekdays(800)
    c = {k: _prices(800, s) for k, s in zip("ABCDEFG", range(10, 17))}
    ok = lambda n, d: True  # noqa: E731
    full = rc.xsmom(days, c, ok, lookback=6, k=2)
    month_end = [j for j in range(799) if days[j + 1].month != days[j].month][10]
    assert all(full[k][month_end] == full[k][month_end - 1] for k in c)  # unchanged on the decision close
    changed = {k: np.r_[v[:month_end + 1], v[month_end + 1:] * 0.3] for k, v in c.items()}
    part = rc.xsmom(days, changed, ok, lookback=6, k=2)
    for k in c:
        assert np.array_equal(full[k][:month_end + 2], part[k][:month_end + 2])
    gross = [sum(abs(full[k][j]) for k in c) for j in range(800)]
    assert max(gross) == pytest.approx(1.0)


def test_fx_rules_use_only_fixings_published_before_the_fill():
    days = weekdays(2200, start=date(1995, 1, 2))
    s = {k: _prices(2200, v) / 100 for k, v in zip(("AUD", "CAD", "CHF", "GBP", "JPY", "NZD"), range(20, 26))}
    carry = lambda c, d: {"AUD": 5.0, "CAD": 3.0, "CHF": 1.0, "GBP": 4.0, "JPY": 0.5, "NZD": 6.0, "USD": 2.0}[c]  # noqa: E731
    full = rc.fx_composite(days, s, carry)
    base = rc.fx_tsmom(days, s)
    firsts = [j for j in range(1, 2200) if days[j].month != days[j - 1].month]
    j = firsts[-5]
    changed = {k: np.r_[v[:j - 1], v[j - 1:] * 2.0] for k, v in s.items()}  # fixings j-1 onwards altered
    for fn, ref in ((lambda x: rc.fx_composite(days, x, carry), full), (lambda x: rc.fx_tsmom(days, x), base)):
        part = fn(changed)
        for k in s:
            assert np.array_equal(ref[k][:j + 1], part[k][:j + 1])
    assert any(full[k][j] != 0 for k in s)


def test_the_cot_filter_only_removes_crowded_positions():
    days = weekdays(60, start=date(2010, 1, 4))
    base = {"EUR": np.full(60, 0.2), "JPY": np.full(60, -0.2)}
    pct = lambda c, j: {"EUR": 0.95, "JPY": 0.5}[c]  # noqa: E731
    f = rc.cot_filter(days, base, pct, 0.9)
    assert np.all(f["EUR"] == 0) and np.all(f["JPY"] == -0.2)
    g = rc.cot_filter(days, base, lambda c, j: float("nan"), 0.9)
    assert np.array_equal(g["EUR"], base["EUR"])  # unknown positioning never changes a position


def test_cot_percentile_uses_only_reports_public_at_the_decision():
    weeks = np.arange(80)
    as_of = (1_200_000_000 + weeks * 7 * 86400).astype(np.int64)
    avail = as_of + 6 * 86400
    share = np.linspace(-1, 1, 80)
    t = int(avail[60])
    p = rc.cot_percentile(as_of, avail, share, t)
    assert p == 1.0  # a rising series: the newest report is above all 51 in its window
    share2 = share.copy()
    share2[61:] = -5.0
    assert rc.cot_percentile(as_of, avail, share2, t) == p


# ── rules: a planted effect is found, a random walk is not ──────────────

def test_a_planted_turn_of_month_effect_is_found_and_a_random_walk_is_not():
    days = weekdays(252 * 12, start=date(1995, 1, 2))
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 0.01, len(days))
    tom = rc.tom(days, {"A": np.ones(len(days))}, 1)["A"]
    drift = np.array([0.003 if tom[j - 1] > 0 else 0.0 for j in range(len(days))])
    inst = idx_inst("A")
    for planted, expect in ((True, True), (False, False)):
        c = {"A": 100 * np.exp(np.cumsum(noise + (drift if planted else 0.0)))}
        r = retail.simulate(days, c, rc.tom(days, c, 1), inst, FLAT, retail.Costs())
        s = retail.summarize(r, days[0], days[-1] + timedelta(days=1))
        assert ((s["t"] or 0) > 3.0) is expect
        assert s["trades"] == s["n"] - 1 and 0.15 < s["time_in_market"] < 0.25  # one window per month boundary


def test_the_ensemble_is_the_mean_of_its_parts():
    a = {"X": np.array([0.1, 0.0]), "Y": np.array([0.2, 0.2])}
    b = {"X": np.array([-0.1, 0.3])}
    m = rc.average(a, b)
    assert np.allclose(m["X"], [0.0, 0.15]) and np.allclose(m["Y"], [0.1, 0.1])


# ── the RC-EQ runner end to end, on synthetic data ──────────────────────

def _rc_eq(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import rc_eq
    from aitrader.data.rates import available_at
    raw = tmp_path / "raw"
    raw.mkdir()
    monkeypatch.setattr(rc_eq, "RAW", raw)
    days = weekdays(261 * 38, start=date(1986, 1, 1))
    for k, name in enumerate(rc_eq.UNIVERSE_A):
        p = _prices(len(days), 100 + k)
        raw.joinpath(f"{name}.csv").write_text("date,close\n" + "".join(f"{d},{float(v)!r}\n" for d, v in zip(days, p)))
    areas = {"US", "JP", "GB", "DE", "XM", "FR", "AU", "HK", "CA", "CH"}
    rows = [(a, d) for a in sorted(areas) for d in days[::3]]
    rp = tmp_path / "rates.csv"
    rp.write_text("area,effective_date,value_pct,available_at_epoch\n" +
                  "".join(f"{a},{d},3.0,{available_at('POLICY', d)}\n" for a, d in rows))
    return rc_eq, rc.Rates(rp)


def test_the_rc_eq_judge_runs_end_to_end_and_never_loads_2021(tmp_path, monkeypatch):
    rc_eq, rates = _rc_eq(tmp_path, monkeypatch)
    days, closes, report = rc_eq.load(rc_eq.UNIVERSE_A, rc_eq.JUDGE[1])
    assert max(days) < date(2021, 1, 1) and set(report) == set(rc_eq.UNIVERSE_A)
    sub = {"development": rc_eq.DEV, "validation": rc_eq.VAL, "modern": rc_eq.MODERN}
    for hid in rc_eq.HYPOTHESES:
        e = rc_eq.evaluate(hid, days, closes, rc_eq.UNIVERSE_A, rates, rc_eq.JUDGE, sub)
        res = e.pop("_res")
        e["regimes"] = rc_eq._regimes(res, days, closes)
        g = rc_eq.gates(e, 3.0)
        assert set(g) >= {"t", "development", "validation", "modern", "costs_x2", "delay", "leave_one_out", "top_year",
                          "drawdown"}
        assert not g["t"], hid  # a random walk passes nothing
        assert e["net"]["n"] >= 360 and e["before_broker"]["mean_monthly"] is not None
        if rc_eq.HYPOTHESES[hid][2]:
            assert len(e["grid"]) == len(rc_eq._grid(rc_eq.HYPOTHESES[hid][2]))
        assert (e["costs_x2"]["mean_monthly"] or 0) <= (e["net"]["mean_monthly"] or 0) + 1e-12


def test_the_rc_eq_design_is_frozen_once_registered():
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    import rc_eq
    spec = root / "research" / "specs" / "RC-EQ.json"
    if not spec.exists():
        pytest.skip("RC-EQ not yet specified")
    frozen = json.loads(spec.read_text())
    assert frozen["code_sha256"] == rc_eq.code_hash(), "RC-EQ code changed after its spec was frozen"
    assert frozen["sha256"] == rc_eq.spec_sha(frozen["spec"])


def test_the_rc_fx_judge_runs_end_to_end_on_synthetic_fixings(tmp_path):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import rc_fx
    from aitrader.data.rates import available_at
    days = weekdays(261 * 29, start=date(1988, 1, 4))
    usd = {c: _prices(len(days), 300 + k) / 100 for k, c in enumerate(rc_fx.FX)}
    usd["EUR"][: days.index(date(1999, 1, 4))] = np.nan
    rp = tmp_path / "rates.csv"
    lvl = {"US": 3.0, "XM": 2.0, "GB": 4.0, "JP": 0.5, "AU": 5.0, "NZ": 6.0, "CA": 3.5, "CH": 1.0}
    rp.write_text("area,effective_date,value_pct,available_at_epoch\n" +
                  "".join(f"{a},{d},{v},{available_at('POLICY', d)}\n" for a, v in lvl.items() for d in days[::2]))
    rates = rc.Rates(rp)
    pct = lambda c, j: 0.95 if (j // 40) % 3 == 0 else 0.5  # noqa: E731
    for hid, (rule, _, _) in rc_fx.HYPOTHESES.items():
        period = rc_fx.COT_JUDGE if rule == "cot_filter" else rc_fx.JUDGE
        e = rc_fx.evaluate(hid, days, usd, rates, period,
                           {"development": rc_fx.DEV, "validation": rc_fx.VAL, "modern": rc_fx.MODERN}, pct)
        e.pop("_res")
        g = rc_fx.gates(e, 3.0, rule)
        assert not g["t"] and e["net"]["n"] > 100 and e["net"]["trades"] > 0
        assert len(e["grid"]) == len(rc_fx._grid(rc_fx.HYPOTHESES[hid][2]))
        if rule == "cot_filter":
            assert "value_added" in g and e["unfiltered"]["n"] == e["net"]["n"]


def test_breakout_enters_on_a_new_high_and_leaves_on_a_new_low():
    days = weekdays(40)
    v = np.r_[np.full(10, 100.0) + np.arange(10) * 0.01 * (-1) ** np.arange(10), 101.0, 102.0, np.full(10, 101.5),
              95.0, np.full(17, 96.0)]
    t = rc.breakout(days, {"A": v}, 1, entry=10, exit_ratio=0.5)["A"]
    assert t[9] == 0 and t[10] == 1.0 and t[21] == 1.0 and t[22] == 0.0


# ── RC-EQ2 ──────────────────────────────────────────────────────────────

def test_halloween_holds_november_to_april_and_reads_no_price():
    from aitrader.research.discovery import rc2
    days = weekdays(600, start=date(2001, 1, 1))
    a = rc2.halloween(days, {"A": _prices(600, 1)}, 2)["A"]
    assert np.array_equal(a, rc2.halloween(days, {"A": _prices(600, 2)}, 2)["A"])
    on = [days[j] for j in range(1, 600) if a[j] > 0 and a[j - 1] == 0]
    off = [days[j] for j in range(1, 600) if a[j] == 0 and a[j - 1] > 0]
    assert on == [date(2001, 10, 31), date(2002, 10, 31)] and off[:2] == [date(2001, 4, 30), date(2002, 4, 30)]
    assert {days[j].month for j in range(600) if a[j] > 0 and days[j].day < 28} == {11, 12, 1, 2, 3, 4}
    assert set(a) == {0.0, 0.5}


def test_the_rc_eq2_halloween_evaluation_runs_on_synthetic_data(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    rc_eq, rates = _rc_eq(tmp_path, monkeypatch)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import rc_eq2
    days, closes, _ = rc_eq.load(rc_eq.UNIVERSE_A, rc_eq.JUDGE[1])
    e = rc_eq2.evaluate_e8(days, closes, rc_eq.UNIVERSE_A, rates, rc_eq.JUDGE,
                           {"development": rc_eq.DEV, "validation": rc_eq.VAL, "modern": rc_eq.MODERN})
    e.pop("_res")
    g = rc_eq.gates(e, 3.0)
    assert not g["t"] and len(e["grid"]) == 9 and 0.4 < e["net"]["time_in_market"] < 0.6
    assert e["net"]["trades_per_year"] == pytest.approx(10, abs=1.5)  # one round trip a year per index


def test_the_rc_eq2_design_is_frozen_once_registered():
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    import rc_eq2
    spec = root / "research" / "specs" / "RC-EQ2.json"
    if not spec.exists():
        pytest.skip("RC-EQ2 not yet specified")
    frozen = json.loads(spec.read_text())
    assert frozen["code_sha256"] == rc_eq2.code_hash(), "RC-EQ2 (or RC-EQ) code changed after its spec was frozen"
    assert frozen["sha256"] == rc_eq2.spec_sha(frozen["spec"])
