"""The SOVEREIGN red team's harness (scripts/sovereign_redteam.py), on markets built so the answer is known: it runs
the owner's own engines exactly as their own entry point does, books a close's decision on the next day only,
charges every unit traded, keeps the backtest's shield apart from the live layer, and its look-ahead check can see a
leak when there is one."""

import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import sovereign_redteam as rt

PKG = Path(__file__).resolve().parents[2] / "research" / "external" / "sovereign" / "sovereign_top3_suite.py"
M = rt.load_package(str(PKG))
ASSETS = list(M.SECTORS)


def _px(closes: dict, opens=None, highs=None, lows=None) -> dict:
    n = len(next(iter(closes.values())))
    return {"days": [f"2020-01-{i + 1:02d}" if i < 31 else f"d{i:04d}" for i in range(n)], "c": closes,
            "o": opens or closes, "h": highs or closes, "l": lows or closes, "live": {a: [True] * n for a in closes}}


def _random_market(n=260, seed=5):
    rng = np.random.default_rng(seed)
    return {a: list(100 * np.cumprod(1 + rng.normal(0.0004, 0.014, n))) for a in ASSETS}


def test_raw_weights_are_the_package_s_own_entry_point_day_after_day():
    ph = _random_market()
    px = {"days": [str(i) for i in range(260)], "c": ph}
    for name in M.STRATEGY_REGISTRY:
        W = rt.raw_weights(M, name, px, ASSETS)
        for t in (150, 259):
            mine = {a: round(float(W[t, j]), 4) for j, a in enumerate(ASSETS)}
            theirs = M.get_live_target_weights(name, {a: v[: t + 1] for a, v in ph.items()})
            assert mine == theirs, (name, t)


def test_ibit_is_flat_before_its_admission_and_never_held_there():
    rng = np.random.default_rng(2)
    days = [f"2024-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 29)]
    raw = {}
    for a in ASSETS:
        dd = days if a != "IBIT" else [d for d in days if d >= "2024-03-01"]
        c = 50 * np.cumprod(1 + rng.normal(0, 0.02, len(dd)))
        raw[a] = {d: {"o": x, "h": x, "l": x, "c": x, "adj": x} for d, x in zip(dd, c)}
    px = rt.panel(raw, ASSETS, ibit_from="2024-06-01", last="2024-12-31")
    i_adm = px["days"].index("2024-06-01")
    ib = px["c"]["IBIT"]
    assert len(set(ib[: i_adm + 1])) == 1 and ib[i_adm] == raw["IBIT"]["2024-06-01"]["c"]
    assert not any(px["live"]["IBIT"][:i_adm]) and all(px["live"]["IBIT"][i_adm:])
    for name in M.STRATEGY_REGISTRY:
        W = rt.raw_weights(M, name, px, ASSETS)
        assert np.all(W[: i_adm + 1, ASSETS.index("IBIT")] == 0.0), name


def test_a_day_one_core_fund_missed_is_dropped_for_every_fund():
    raw = {a: {d: {"o": 1, "h": 1, "l": 1, "c": 1.0, "adj": 1.0} for d in ("2024-11-01", "2024-11-04", "2024-11-05")}
           for a in ASSETS}
    del raw["GLD"]["2024-11-04"]
    px = rt.panel(raw, ASSETS, ibit_from="2024-11-01", last="2024-12-31")
    assert px["days"] == ["2024-11-01", "2024-11-05"]


def test_the_target_set_at_a_close_earns_the_next_day_only():
    n, k = 12, 6
    a_px = [100.0] * n
    for i in range(k, n):
        a_px[i] = 110.0  # +10% on day k only
    px = _px({"A": a_px, "B": [100.0] * n})
    W = np.zeros((n, 2))
    W[k:, 0] = 1.0  # decided at day k's close: it has seen the jump, so it must not earn it
    book = rt.replay(M, W, px, ["A", "B"], 0, n - 1, 0.0)
    assert all(abs(r["equity"] - rt.CAPITAL) < 1e-6 for r in book["rows"])
    W2 = np.zeros((n, 2))
    W2[k - 1:, 0] = 1.0  # decided at day k-1's close: it earns day k
    book2 = rt.replay(M, W2, px, ["A", "B"], 0, n - 1, 0.0)
    assert abs(book2["rows"][k - 1]["equity"] - rt.CAPITAL * 1.1) < 1e-6
    # with one day's delay the same decision earns nothing of day k
    book3 = rt.replay(M, W2, px, ["A", "B"], 0, n - 1, 0.0, delay=1)
    assert abs(book3["rows"][-1]["equity"] - rt.CAPITAL) < 1e-6


def test_every_unit_of_weight_traded_is_charged():
    n = 6
    px = _px({"A": [100.0] * n, "B": [100.0] * n})
    W = np.zeros((n, 2))
    W[:, 0], W[3:, 1] = 0.5, -0.25
    book = rt.replay(M, W, px, ["A", "B"], 0, n - 1, 8.0)
    costs = [round(r["cost"], 10) for r in book["rows"]]
    assert costs == [round(0.5 * 8e-4, 10), 0.0, 0.0, round(0.25 * 8e-4, 10), 0.0]
    assert abs(book["rows"][-1]["equity"] - rt.CAPITAL * (1 - 0.5 * 8e-4) * (1 - 0.25 * 8e-4)) < 1e-6


def test_the_backtest_throttles_on_the_last_close_and_never_stops_the_live_layer_stops_for_good():
    n = 12
    a_px = [100.0, 100.0, 94.0, 88.0, 88.0, 88.0, 92.0, 96.0, 100.0, 100.0, 100.0, 100.0]
    px = _px({"A": a_px, "B": [100.0] * n})
    W = np.zeros((n, 2))
    W[:, 0] = 1.0
    book = rt.replay(M, W, px, ["A", "B"], 0, n - 1, 0.0)
    g = [r["gross"] for r in book["rows"]]
    # the -6% close of day 2 halves day 3; the -9% close of day 3 leaves a quarter, never zero, while it recovers
    assert g[:2] == [1.0, 1.0] and g[2] == 0.5 and g[3] == 0.25 and min(g) > 0
    live = rt.replay(M, W, px, ["A", "B"], 0, n - 1, 0.0, live_layer=True)
    gl = [r["gross"] for r in live["rows"]]
    assert gl[3] == 0.0 and all(x == 0.0 for x in gl[3:]) and live["rows"][-1]["stopped"]


def test_the_live_layer_leaves_at_the_open_or_at_minus_four():
    px = _px({"A": [100.0, 100.0, 100.0, 100.0], "B": [100.0] * 4},
             opens={"A": [100.0, 95.0, 100.0, 100.0], "B": [100.0] * 4},
             highs={"A": [100.0, 96.0, 101.0, 100.0], "B": [100.0] * 4},
             lows={"A": [100.0, 94.0, 94.0, 100.0], "B": [100.0] * 4})
    px["c"]["A"] = [100.0, 96.0, 97.0, 97.0]
    W = np.zeros((4, 2))
    W[:, 0] = 1.0
    book = rt.replay(M, W, px, ["A", "B"], 0, 3, 0.0, live_layer=True)
    r1, r2 = book["rows"][0], book["rows"][1]
    assert r1["killed"] == "open" and abs(r1["ret"] - (-0.05)) < 1e-12
    # re-entered at day 1's close at half (the -5% drawdown); day 2's low of 94 is -1.0% of the equity: no stop
    assert r2["killed"] is None
    px["l"]["A"][2] = 88.0  # half held (the -5% close halves it): -8.3% from 96 is -4.2% of the equity at worst
    book = rt.replay(M, W, px, ["A", "B"], 0, 3, 0.0, live_layer=True)
    assert book["rows"][1]["killed"] == "intraday" and abs(book["rows"][1]["ret"] - (-0.04)) < 1e-12
    # without the live layer the same day books its close
    plain = rt.replay(M, W, px, ["A", "B"], 0, 3, 0.0)
    assert plain["rows"][1]["killed"] is None and abs(plain["rows"][1]["ret"] - (97 / 96 - 1)) < 1e-12


def test_prop_counts_the_daily_loss_from_the_day_s_start_and_the_total_from_the_first_balance():
    rows = [{"day": "a", "start": 200_000, "worst_eq": 191_000, "equity": 195_000},
            {"day": "b", "start": 195_000, "worst_eq": 184_000, "equity": 186_000},
            {"day": "c", "start": 186_000, "worst_eq": 179_000, "equity": 181_000}]
    p = rt.prop({"rows": rows, "capital": 200_000})
    assert p["daily_loss_5pct_days"] == 1 and p["below_90pct_of_start_days"] == 1 and p["first_failure"] == "b"


def test_the_five_regimes_follow_one_another_and_the_last_two_hold_252_days():
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2007-01-01", "2026-11-20")]
    reg = rt.regimes(days)
    spans = list(reg.values())
    assert all(spans[i][1] == spans[i + 1][0] for i in range(len(spans) - 1))
    assert spans[-1][1] == len(days) - 1 and spans[-1][1] - spans[-1][0] == 252 and spans[-2][1] - spans[-2][0] == 252
    assert days[spans[0][0]] >= rt.START and days[spans[1][0] + 1] >= "2014-01-01"


def test_the_look_ahead_check_sees_a_leak_when_there_is_one():
    def leaky_factory(risk_mode="funded"):
        def engine(ds, rets, assets, t, dpb, st):
            nxt = min(t + 1, len(ds[assets[0]]) - 1)
            return {a: (0.1 if ds[a][nxt] > ds[a][t] else -0.1) for a in assets}
        return engine
    leaky = types.SimpleNamespace(**{k: getattr(M, k) for k in ("SECTORS", "TAIL_CAPS", "apply_prop_shield",
                                                                 "get_live_target_weights")})
    leaky.STRATEGY_REGISTRY = {"LEAKY": leaky_factory}
    out = rt.t0_checklist(leaky, {}, {"days": [], "c": {}}, ASSETS)
    assert out["look_ahead"]["LEAKY"]["days_before_k_changed"] > 0
    clean = rt.t0_checklist(M, {}, {"days": [], "c": {}}, ASSETS)
    assert all(v["days_before_k_changed"] == 0 for v in clean["look_ahead"].values())


@pytest.mark.parametrize("name", list(M.STRATEGY_REGISTRY))
def test_no_weight_ever_passes_its_cap_on_a_violent_market(name):
    rng = np.random.default_rng(9)
    ph = {a: list(100 * np.cumprod(1 + rng.normal(0, 0.06, 300))) for a in ASSETS}
    W = rt.raw_weights(M, name, {"days": [str(i) for i in range(300)], "c": ph}, ASSETS)
    cm = 0.95 if name == "SEC-TSMOM-4" else 1.10
    caps = np.array([M.TAIL_CAPS[a] * cm for a in ASSETS])
    assert np.all(np.abs(W) <= caps + 1e-9)
