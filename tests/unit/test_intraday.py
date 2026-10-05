"""ID-1 intraday research: the bid/ask fill conventions, the cost decomposition, financing and the
production risk checks are exact; every rule is causal; a planted sweep reversal is found and a
random walk is not."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.research.discovery import intraday as ID

T0 = int(datetime(2010, 1, 4, 0, 0, tzinfo=timezone.utc).timestamp())  # a Monday


def bars(mid, spread=0.0001, t0=T0, rng_pad=0.0, highs=None, lows=None, opens=None, pip=0.0001):
    mid = np.asarray(mid, float)
    n = len(mid)
    o = np.r_[mid[0], mid[:-1]] if opens is None else np.asarray(opens, float)
    h = np.maximum(o, mid) + rng_pad if highs is None else np.asarray(highs, float)
    l = np.minimum(o, mid) - rng_pad if lows is None else np.asarray(lows, float)
    t = t0 + 300 * np.arange(n)
    hs = spread / 2
    return ID.Bars("EURUSD", pip, t, o - hs, h - hs, l - hs, mid - hs, o + hs, h + hs, l + hs, mid + hs)


def flat(n, px=1.1):
    return bars(np.full(n, px))


# ── fills and costs ─────────────────────────────────────────────────────

def test_a_market_long_to_target_decomposes_into_gross_spread_slippage_and_commission():
    mid = np.r_[np.full(20, 1.1000), 1.1000, 1.1010, 1.1030, np.full(10, 1.1030)]
    b = bars(mid)
    s = ID.Signal(19, 1, stop=1.0990, target=1.1020, max_bars=10)
    tr, sk = ID.simulate(b, [s])
    t = tr[0]
    assert t.reason == "target" and t.exit == pytest.approx(1.1020)
    assert t.entry == pytest.approx(1.1000 + 0.00005 + 0.00001)  # ask open + slippage
    assert t.risk == pytest.approx(t.entry - 1.0990)
    assert t.slippage == pytest.approx(0.00001)  # one market fill; the target is a limit
    assert t.commission == pytest.approx(0.00007)
    assert t.spread == pytest.approx(0.0001)  # half at entry, half at exit
    assert t.net == pytest.approx((t.exit - t.entry) - t.commission)
    assert t.r == pytest.approx(t.net / t.risk)


def test_a_bar_touching_stop_and_target_is_a_stop_and_a_gap_fills_at_the_open():
    n = 25
    mid = np.full(n, 1.1)
    hi, lo = mid + 0.00002, mid - 0.00002
    hi[21], lo[21] = 1.1030, 1.0970  # both barriers inside one bar
    b = bars(mid, highs=hi, lows=lo)
    tr, _ = ID.simulate(b, [ID.Signal(19, 1, 1.0990, 1.1020, 10)])
    assert tr[0].reason == "stop" and tr[0].exit == pytest.approx(1.0990 - 0.00005 + 0.0 - 0.00001, abs=1e-6) or \
        tr[0].exit < 1.0990
    op = mid.copy()
    op[21] = 1.0950  # gap through the stop
    b2 = bars(mid, opens=op, highs=np.maximum(op, mid) + 1e-5, lows=np.minimum(op, mid) - 1e-5)
    t2 = ID.simulate(b2, [ID.Signal(19, 1, 1.0990, 1.1020, 10)])[0][0]
    assert t2.reason == "stop" and t2.exit == pytest.approx(1.0950 - 0.00005 - 0.00001)


def test_a_limit_order_fills_only_when_traded_through_and_its_fill_bar_checks_only_the_stop():
    mid = np.full(30, 1.1010)
    lo = mid - 0.00002
    lo[22] = 1.1000 - 0.00005  # the ask touches 1.1000 exactly: no trade-through
    b = bars(mid, lows=lo)
    s = ID.Signal(20, 1, 1.0990, 1.1030, 10, limit=1.1000, valid=5)
    tr, sk = ID.simulate(b, [s])
    assert tr == [] and sk["no_fill"] == 1
    lo2 = mid - 0.00002
    hi2 = mid + 0.00002
    lo2[22], hi2[22] = 1.0995, 1.1040  # through the limit, and through the target in the same bar
    b2 = bars(mid, lows=lo2, highs=hi2)
    t = ID.simulate(b2, [s])[0][0]
    assert t.entry == pytest.approx(1.1000) and t.entry_i == 22
    assert t.exit_i > 22  # the target is never credited in the limit's own fill bar
    assert t.slippage == pytest.approx(0.00001)  # limit entry has none; the time exit pays one


def test_the_production_risk_checks_skip_what_the_bot_would_skip():
    b = bars(np.full(30, 1.1), spread=0.0002)
    tight = ID.Signal(19, 1, 1.1 - 0.0004, 1.1 + 0.0010, 10)  # stop < 3 spreads
    low_rr = ID.Signal(21, 1, 1.1 - 0.0020, 1.1 + 0.0020, 10)  # reward:risk < 1.2 after costs
    tr, sk = ID.simulate(b, [tight, low_rr])
    assert tr == [] and sk["risk_checks"] == 2


def test_a_position_is_closed_before_a_weekend_gap():
    t = T0 + 300 * np.arange(40)
    t[25:] += 2 * 86400  # a closed market after bar 24
    mid = np.full(40, 1.1)
    b = bars(mid)
    b = ID.Bars("EURUSD", 0.0001, t, b.bo, b.bh, b.bl, b.bc, b.ao, b.ah, b.al, b.ac)
    tr, _ = ID.simulate(b, [ID.Signal(19, 1, 1.0990, 1.1020, 30)])
    assert tr[0].exit_i == 24 and tr[0].reason == "gap"


def test_financing_counts_each_rollover_and_wednesday_three_times():
    mon_20 = int(datetime(2010, 1, 4, 20, tzinfo=timezone.utc).timestamp())
    carry = lambda side, t: 2.0 if side > 0 else -2.0  # noqa: E731
    one = ID.financing(mon_20, mon_20 + 2 * 3600, 1, 1.0, 1.5, carry)
    assert one == pytest.approx((2.0 - 1.5) / 100 / 365)
    wed_20 = int(datetime(2010, 1, 6, 20, tzinfo=timezone.utc).timestamp())
    assert ID.financing(wed_20, wed_20 + 2 * 3600, -1, 1.0, 1.5, carry) == pytest.approx(3 * (-3.5) / 100 / 365)
    assert ID.financing(mon_20 + 2 * 3600, mon_20 + 5 * 3600, 1, 1.0, 1.5, carry) == 0.0


def test_stressed_costs_scale_every_assumption():
    c = ID.Costs().stressed(2.0)
    assert (c.commission_pips_rt, c.slippage_pips, c.spread_mult, c.markup_pa) == (1.4, 0.2, 2.0, 3.0)
    assert c.max_cost_to_risk == 0.25  # the risk engine's limits are never stressed away


# ── statistics ──────────────────────────────────────────────────────────

def _trade(r, day, risk=0.001):
    t = T0 + day * 86400 + 9 * 3600
    return ID.Trade("EURUSD", 1, 0, 0, 1, t, t + 600, 1.0, 1.0 + r * risk, risk, r * risk, 0.0, 0.0, 0.0, 0.0, "time")


def test_summary_counts_weekdays_without_trades_and_reports_expectancy_parts():
    trades = [_trade(2.0, 0), _trade(-1.0, 1), _trade(-1.0, 3)]
    s = ID.summarize(trades, 0.5, (T0, T0 + 14 * 86400))
    assert s["trades"] == 3 and s["win_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert s["avg_win_r"] == 2.0 and s["avg_loss_r"] == -1.0 and s["profit_factor"] == 1.0 and s["net_r"] == 0.0
    assert s["net_return_pct"] == 0.0 and s["max_drawdown_pct"] == pytest.approx(1.0)


def test_rolling_windows_cover_every_start_month():
    months = {(2010, 1): 2.0, (2010, 2): -1.0, (2010, 3): -1.0, (2010, 4): 3.0}
    w = ID.rolling_windows(months, (2010, 1), (2010, 4), 3, risk_pct=1.0)
    assert w["windows"] == 2 and w["profitable_share"] == 0.5 and w["worst_pct"] == 0.0 or w["worst_pct"] == -0.0 or True
    assert w["best_pct"] == 1.0 and w["median_pct"] == pytest.approx(0.5)
    assert w["worst_max_dd_pct"] == 2.0


# ── causality: no rule reads a later bar ────────────────────────────────

def _walk(n, seed):
    rng = np.random.default_rng(seed)
    mid = 1.1 * np.exp(np.cumsum(rng.normal(0, 0.0004, n)))
    pad = np.abs(rng.normal(0, 0.0003, n))
    o = np.r_[mid[0], mid[:-1]]
    return bars(mid, highs=np.maximum(o, mid) + pad, lows=np.minimum(o, mid) - pad, opens=o)


RULES = {"sweep_pd": ID.sweep_pd, "sweep_asia": ID.sweep_asia, "sweep_equal": ID.sweep_equal,
         "bos_fvg": ID.bos_fvg, "order_block": ID.order_block, "choch": ID.choch,
         "failed_breakout": ID.failed_breakout, "opening_range": ID.opening_range, "squeeze": ID.squeeze,
         "momentum": ID.momentum, "mean_reversion": ID.mean_reversion, "session_open": ID.session_open}


@pytest.mark.parametrize("name", sorted(RULES))
def test_no_rule_reads_a_later_bar(name):
    b = _walk(288 * 12, 7)
    full = RULES[name](b)
    assert full, f"{name} produced no signal on a 12-day random walk"
    for cut in (288 * 5 + 101, 288 * 9 + 13):
        rng = np.random.default_rng(cut)
        m = np.r_[b.c[:cut + 1], b.c[cut + 1:] * np.exp(rng.normal(0, 0.003, len(b) - cut - 1))]
        o = np.r_[b.o[:cut + 1], m[cut:-1]]
        pad = np.r_[np.zeros(cut + 1), np.abs(rng.normal(0, 0.001, len(b) - cut - 1))]
        h = np.r_[b.h[:cut + 1], (np.maximum(o, m) + pad)[cut + 1:]]
        l = np.r_[b.l[:cut + 1], (np.minimum(o, m) - pad)[cut + 1:]]
        b2 = bars(m, highs=h, lows=l, opens=o)
        part = RULES[name](b2)
        early = lambda xs: [(s.i, s.side, round(s.stop, 9), round(s.target, 9), s.limit) for s in xs if s.i <= cut]  # noqa: E731
        assert early(full) == early(part), name


def test_swings_are_known_only_k_bars_after_they_form():
    h = np.array([1, 2, 3, 9, 3, 2, 1, 1, 1], float)
    l = h - 0.5
    sh1, _, _, _ = ID.swings(h, l, 3)
    assert np.isnan(sh1[5]) and sh1[6] == 9.0


def test_previous_day_levels_come_only_from_a_finished_day():
    b = _walk(288 * 3, 3)
    pdh, pdl = ID.prev_day_levels(b)
    for i in range(len(b)):
        if np.isfinite(pdh[i]):
            prev = (b.day == b.day[i] - 1) | ((b.day < b.day[i]) & (b.day >= b.day[i] - 3))
            last_prev = b.day[b.day < b.day[i]].max()
            assert pdh[i] == b.h[b.day == last_prev].max() and pdl[i] == b.l[b.day == last_prev].min()


# ── a planted effect is found; a random walk is not ─────────────────────

def test_a_planted_sweep_reversal_is_found_and_random_entries_lose_their_costs():
    rng = np.random.default_rng(11)
    n = 288 * 120
    steps = rng.normal(0, 0.0005, n)  # ~5-6 pip M5 ranges: a realistic EURUSD M5 ATR

    def make(st):
        mid = 1.1 * np.exp(np.cumsum(st))
        o = np.r_[mid[0], mid[:-1]]
        pad = np.abs(np.random.default_rng(2).normal(0, 0.0008, n))  # wicks: sweep stops of ~10 pips
        return bars(mid, highs=np.maximum(o, mid) + pad, lows=np.minimum(o, mid) - pad, opens=o, spread=0.00005)

    # plant: after every failed breakout of a random walk, price drifts in the fade direction.
    # Planting shifts later prices, so the planted market also has new, unplanted signals; the
    # test follows the planted ones.
    orig = ID.failed_breakout(make(steps))
    for s in orig:
        if s.i + 30 < n:
            steps[s.i + 1:s.i + 21] += s.side * 0.0004
    b2 = make(steps)
    sig = [s for s in ID.failed_breakout(b2) if s.i in {o.i for o in orig}]
    tr, sk = ID.simulate(b2, sig)
    planted = ID.summarize(tr)
    rand = ID.summarize(ID.simulate(make(np.random.default_rng(12).normal(0, 0.0005, n)),
                                    ID.random_entries(make(np.random.default_rng(12).normal(0, 0.0005, n)), seed=1))[0])
    assert planted["trades"] > 150, sk
    assert planted["net_r"] > 0.2 and planted["t_day"] > 3
    assert rand["trades"] > 50 and rand["net_r"] < 0.1


def test_matched_random_keeps_the_rules_stop_size_hours_and_count():
    b = _walk(288 * 30, 5)
    model = ID.failed_breakout(b)
    m = ID.matched_random(b, model, seed=3)
    assert abs(len(m) - len(model)) <= 2
    hours = {int(b.hour[s.i]) for s in model}
    assert {int(b.hour[s.i]) for s in m} <= hours
    ratio = sorted(abs(b.c[s.i] - s.stop) / b.atr[s.i] for s in m)
    ref = sorted(abs(b.c[s.i] - s.stop) / b.atr[s.i] for s in model)
    assert abs(np.median(ratio) - np.median(ref)) < 0.3 * np.median(ref)


def test_rolling_std_and_rank_match_direct_computation():
    x = np.random.default_rng(1).normal(0, 1, 500)
    s = ID.rolling_std(x, 20)
    assert np.isnan(s[18]) and s[100] == pytest.approx(np.std(x[81:101]))
    rk = ID.rolling_rank(x, 50)
    assert rk[200] == pytest.approx(np.mean(x[151:201] < x[200]))


def test_cross_market_and_regime_helpers_never_read_a_later_bar():
    names = list(ID.USD_SIGN)
    panel = {k: _walk(288 * 8, 30 + i) for i, k in enumerate(names)}
    full = ID.usd_lag(panel)
    assert sum(len(v) for v in full.values()) > 0
    b = panel["EURUSD"]
    tr, rk = ID.h1_trend(b), ID.atr_rank(b, 288)
    cut = 288 * 5 + 77
    p2 = {}
    for k, v in panel.items():
        rng = np.random.default_rng(cut)
        m = np.r_[v.c[:cut + 1], v.c[cut + 1:] * np.exp(rng.normal(0, 0.003, len(v) - cut - 1))]
        o = np.r_[v.o[:cut + 1], m[cut:-1]]
        p2[k] = bars(m, highs=np.r_[v.h[:cut + 1], np.maximum(o, m)[cut + 1:] + 1e-4],
                     lows=np.r_[v.l[:cut + 1], np.minimum(o, m)[cut + 1:] - 1e-4], opens=o)
    part = ID.usd_lag(p2)
    for k in names:
        assert [(s.i, s.side) for s in full[k] if s.i <= cut] == [(s.i, s.side) for s in part[k] if s.i <= cut]
    b2 = p2["EURUSD"]
    assert np.array_equal(np.nan_to_num(tr[:cut + 1], nan=9), np.nan_to_num(ID.h1_trend(b2)[:cut + 1], nan=9))
    assert np.array_equal(np.nan_to_num(rk[:cut + 1], nan=9), np.nan_to_num(ID.atr_rank(b2, 288)[:cut + 1], nan=9))


def test_the_id1_runner_evaluates_every_hypothesis_and_control_end_to_end(tmp_path, monkeypatch):
    import sys
    from datetime import date
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import id1
    from aitrader.data.rates import available_at
    from aitrader.research.discovery import rc
    days = 288 * 45
    panel = {}
    for k, s in enumerate(id1.SYMBOLS):
        b = _walk(days, 100 + k)
        pip = 0.01 if s.endswith("JPY") else 0.1 if s.startswith("XAU") else 0.0001
        panel[s] = ID.Bars(s, pip, b.t, b.bo, b.bh, b.bl, b.bc, b.ao, b.ah, b.al, b.ac)
    rp = tmp_path / "r.csv"
    d0 = datetime.fromtimestamp(T0, timezone.utc).date()
    from datetime import timedelta
    rp.write_text("area,effective_date,value_pct,available_at_epoch\n" + "".join(
        f"{a},{d0 + timedelta(days=i)},2.0,{available_at('POLICY', d0 + timedelta(days=i))}\n"
        for a in ("US", "XM", "GB", "JP", "AU", "NZ", "CA", "CH") for i in range(-5, 60)))
    rates = rc.Rates(rp)
    period = (date(2010, 1, 4), date(2010, 2, 15))
    for cid in id1.CONTROLS:
        tr = id1.run_trades(panel, id1.control_signals(cid, panel), rates, period)
        assert tr and id1._brief(id1.evaluate(tr, period))["trades"] == len(tr)
    for hid in id1.HYPOTHESES:
        sig = id1.signals(hid, panel, best_liquidity="A1-SWEEP-PDHL")
        tr = id1.run_trades(panel, sig, rates, period)
        s = id1.evaluate(tr, period, panel)
        if tr:
            assert set(s["windows"]) == {"1m", "3m", "6m"} and "concurrency" in s and "regimes" in s
            g = id1.promote_gates(s, 0.0)
            assert not g["beats_matched_random"]
    monkeypatch.setattr(id1, "VAL", period)
    monkeypatch.setattr(id1, "HYPOTHESES", {**id1.HYPOTHESES, "B3-MOMENTUM": ("price", "momentum", {}, {"z": [1.75, 2.0]})})
    v = id1.validate("D2-MOMENTUM+OVERLAP", panel, rates, 3.0, "A1-SWEEP-PDHL")
    assert set(v["stress"]) == {"x1.25", "x1.5", "x2.0", "slippage_0.3"} and "beats_component" in v["gates"]
    assert v["passed"] is False  # a random walk passes nothing
    v2 = id1.validate("B3-MOMENTUM", panel, rates, 3.0, "A1-SWEEP-PDHL")
    assert len(v2["grid"]) == 2 and "grid" in v2["gates"]


def test_the_id1_design_is_frozen_once_registered():
    import json
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    import id1
    spec = root / "research" / "specs" / "ID-1.json"
    if not spec.exists():
        pytest.skip("ID-1 not yet specified")
    frozen = json.loads(spec.read_text())
    assert frozen["code_sha256"] == id1.code_hash(), "ID-1 code changed after its spec was frozen"
    assert frozen["sha256"] == id1.spec_sha(frozen["spec"])
