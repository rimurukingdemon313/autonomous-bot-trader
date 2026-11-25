"""The SOVEREIGN 'everything' run (scripts/sovereign_everything.py), on markets built so the answer is known: its
engines are the package's own factories, a later start shifts only the tranche phase, an added market reads no bar
dated after the day and is never held before its first bar, and the package's module is extended only in a fresh
copy."""

import hashlib
from pathlib import Path

import numpy as np
import pytest

from scripts import sovereign_everything as ev
from scripts import sovereign_redteam as rt

PKG = Path(__file__).resolve().parents[2] / "research" / "external" / "sovereign" / "sovereign_top3_suite.py"
M = rt.load_package(str(PKG))
ASSETS = list(M.SECTORS)


def _market(n=240, seed=4, assets=ASSETS):
    rng = np.random.default_rng(seed)
    return {"days": [f"d{i:04d}" for i in range(n)],
            "c": {a: list(100 * np.cumprod(1 + rng.normal(0.0004, 0.015, n))) for a in assets}}


def test_the_engines_are_the_spec_s_settings_built_by_its_own_factories():
    eng = dict(ev.engines(M))
    assert len(eng) == 11 and sum(k.startswith("SOVEREIGN-TITAN-MAX") for k in eng) == 7
    px = _market()
    for row, mode in (("SOVEREIGN-TITAN-MAX 15d/35d/0.0175", "funded"), ("SOVEREIGN-TITAN-MAX 15d/35d/0.0155", "eval")):
        mine = ev.weights_of(eng[row], px, ASSETS)
        theirs = rt.raw_weights(M, "SOVEREIGN-TITAN-MAX", px, ASSETS, risk_mode=mode)
        assert np.array_equal(mine, theirs), row
    for name in ("SOVEREIGN-TITAN-7", "SEC-TSMOM-4"):
        for mode in ("funded", "eval"):
            assert np.array_equal(ev.weights_of(eng[f"{name} {mode}"], px, ASSETS),
                                  rt.raw_weights(M, name, px, ASSETS, risk_mode=mode))


def test_a_later_start_leaves_earlier_rows_empty_and_runs_the_engine_on_what_follows():
    px = _market()
    factory = dict(ev.engines(M))["SEC-TSMOM-4 funded"]
    W3 = ev.weights_of(factory, px, ASSETS, offset=3)
    assert np.all(W3[:3] == 0.0)
    sliced = {"days": px["days"][3:], "c": {a: v[3:] for a, v in px["c"].items()}}
    assert np.array_equal(W3[3:], ev.weights_of(factory, sliced, ASSETS))
    assert not np.array_equal(W3[60:], ev.weights_of(factory, px, ASSETS)[60:])  # the tranche phase did move


def test_a_market_reads_only_bars_on_or_before_the_day_and_is_flat_before_its_first():
    raw = {"2020-01-02": {"o": 9.0, "h": 11.0, "l": 8.0, "c": 10.0, "adj": 10.0},
           "2020-01-04": {"o": 12.0, "h": 13.0, "l": 11.0, "c": 12.0, "adj": 6.0}}  # adj halves the 4th's bar
    days = ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"]
    c, o, h, lo, own = ev.aligned(raw, days)
    assert c == [10.0, 10.0, 10.0, 6.0, 6.0]
    assert own == [False, True, False, True, False]
    assert (o[3], h[3], lo[3]) == (6.0, 6.5, 5.5) and (o[2], h[2], lo[2]) == (10.0, 10.0, 10.0)


def test_each_step_extends_a_fresh_copy_and_the_package_file_is_untouched():
    before = hashlib.sha256(PKG.read_bytes()).hexdigest()
    with_eth = ev.extended_module(str(PKG), ("ETH", "GER40"))
    plain = ev.extended_module(str(PKG), ())
    assert with_eth.SECTORS["ETH"] == "CRYPTO" and with_eth.TAIL_CAPS["GER40"] == 0.55
    assert "ETH" not in plain.SECTORS and "GER40" not in plain.TAIL_CAPS
    assert "ETH" not in M.SECTORS
    assert hashlib.sha256(PKG.read_bytes()).hexdigest() == before


def test_bitcoin_takes_ibits_place_and_an_added_market_is_never_held_before_its_first_bar():
    rng = np.random.default_rng(8)
    days = [f"2020-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 29)]

    def series(dd, scale=0.02):
        c = 50 * np.cumprod(1 + rng.normal(0.001, scale, len(dd)))
        return {d: {"o": x, "h": x * 1.01, "l": x * 0.99, "c": x, "adj": x} for d, x in zip(dd, c)}

    raw_core = {a: series(days) for a in ev.CORE}
    del raw_core["GLD"]["2020-03-03"]  # a day one core fund missed is dropped for every market
    raw_extra = {"BTC-USD": series(days, 0.04), "ETH-USD": series([d for d in days if d >= "2020-06-01"], 0.05)}
    px, assets = ev.wide_panel(raw_core, raw_extra, ("ETH",), last="2020-12-31")
    assert "2020-03-03" not in px["days"] and assets == list(ev.CORE) + ["IBIT", "ETH"]
    assert px["c"]["IBIT"] == ev.aligned(raw_extra["BTC-USD"], px["days"])[0]
    first = px["days"].index("2020-06-01")
    assert len(set(px["c"]["ETH"][: first + 1])) == 1 and not any(px["live"]["ETH"][:first])
    Mx = ev.extended_module(str(PKG), ("ETH",))
    for name in Mx.STRATEGY_REGISTRY:
        W = ev.weights_of(lambda name=name: Mx.STRATEGY_REGISTRY[name](risk_mode="funded"), px, assets)
        assert np.all(W[: first + 1, assets.index("ETH")] == 0.0), name


def test_the_split_separates_the_crypto_positions_from_the_rest():
    px = _market(n=300, seed=6)
    px["o"], px["h"], px["l"] = px["c"], px["c"], px["c"]
    W = np.zeros((300, len(ASSETS)))
    W[:, ASSETS.index("IBIT")] = 0.2
    out = ev.split(M, W, px, ASSETS, 10, 290)
    assert out["without crypto"]["profit"] == 0.0
    only = rt.summary(rt.replay(M, W, px, ASSETS, 10, 290, 8.0))["profit"]
    assert out["crypto only"]["profit"] == only


def _flat_market(spy: list[float]) -> dict:
    n = len(spy)
    c = {a: ([float(x) for x in spy] if a == "SPY" else [100.0] * n) for a in ASSETS}
    return {"days": [f"d{i:04d}" for i in range(n)], "c": c, "o": c, "h": c, "l": c}


def test_the_brake_diagnostic_counts_the_days_the_brake_held_and_holds_off_only_the_brake():
    n, k, cap = 60, 10, rt.CAPITAL
    W = np.zeros((n, len(ASSETS)))
    W[:, ASSETS.index("SPY")] = 0.5
    # a market that only rises: the brake never engages, and holding it off changes nothing
    up = ev.brake(M, W, _flat_market([100.0 * 1.001 ** i for i in range(n)]), ASSETS, 0, n - 1)
    on = rt.summary(rt.replay(M, W, _flat_market([100.0 * 1.001 ** i for i in range(n)]), ASSETS, 0, n - 1, 8.0))
    assert up["days_at_half_or_less"] == 0.0 and up["brake_off"]["8bp"]["profit"] == pytest.approx(on["profit"])
    # SPY falls 20% on day k and stays there: half the book loses 10%, and from the next close the brake holds a quarter
    b = ev.brake(M, W, _flat_market([100.0] * k + [80.0] * (n - k)), ASSETS, 0, n - 1)
    assert b["days_at_half_or_less"] == b["days_at_a_quarter"] == pytest.approx((n - 1 - k) / (n - 1))
    assert b["mean_gross_with_brake"] == pytest.approx((k * 0.5 + (n - 1 - k) * 0.125) / (n - 1))
    off8, off16 = b["brake_off"]["8bp"], b["brake_off"]["16bp"]
    assert off8["mean_gross"] == pytest.approx(0.5)  # held off, the book never shrinks
    assert off8["profit"] == pytest.approx(cap * (1 - 0.5 * 8e-4) * 0.9 - cap)
    assert off16["profit"] == pytest.approx(cap * (1 - 0.5 * 16e-4) * 0.9 - cap)
    assert b["brake_off_prop_one_year_windows"]["share"] is None  # too short for a one-year window


def test_holding_the_brake_off_leaves_the_package_and_its_intraday_exit_as_they_are():
    N = ev.unbraked(M)
    assert N.apply_prop_shield({"X": 1.0}, -0.08)["X"] == 1.0
    assert N.apply_prop_shield({"X": 1.0}, 0.0, -0.05)["X"] == 0.0  # the intraday exit is the package's own
    assert M.apply_prop_shield({"X": 1.0}, -0.08)["X"] == 0.25 and M.apply_prop_shield({"X": 1.0}, -0.06)["X"] == 0.5
