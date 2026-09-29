"""New feature primitives are causal (other instruments included) and the catalog keeps every
feature's provenance, budget, leakage status, uses and results — permanently."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.data.resample import bucket_start
from aitrader.research.discovery.catalog import (BudgetExceeded, CatalogError, FeatureCatalog, FeatureRecord,
                                                 LeakyFeature, truncation_leaks)
from aitrader.research.discovery.primitives import (PRIMITIVE_BY_NAME, PRIMITIVES, USD_SIGN, Others, _aligned,
                                                    primitive_leakage)

T0 = 1_300_003_200 // 86400 * 86400 + 86400 * 1  # a Monday 00:00 UTC (2011-03-14)
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
N = 900
ROWS = list(range(0, N, 41)) + [N - 1]


def series_from_mid(symbol, mid, seed=0, open_time=None):
    rng = np.random.default_rng(seed)
    n = len(mid)
    o = np.concatenate(([mid[0]], mid[:-1]))
    wick = np.abs(rng.normal(0, 0.0004, n)) * mid
    hi, lo = np.maximum(o, mid) + wick, np.minimum(o, mid) - wick
    half = 0.00004 * mid
    ot = T0 + 3600 * np.arange(n) if open_time is None else open_time
    return BarSeries.from_columns(symbol, "H1", "synthetic", open_time=ot,
                                  bid_open=o - half, bid_high=hi - half, bid_low=lo - half, bid_close=mid - half,
                                  ask_open=o + half, ask_high=hi + half, ask_low=lo + half, ask_close=mid + half,
                                  ticks=rng.integers(50, 500, n), spread_mean=2 * half, spread_max=4 * half)


def market(n=N, seed=11, dollar=None):
    """Seven USD pairs driven by one dollar factor plus their own noise, and EURJPY."""
    rng = np.random.default_rng(seed)
    usd = np.cumsum(rng.normal(0, 0.0007, n)) if dollar is None else dollar
    out = {}
    for k, (sym, sign) in enumerate(USD_SIGN.items()):
        own = np.cumsum(rng.normal(0, 0.0004, n))
        out[sym] = series_from_mid(sym, (110.0 if sym.endswith("JPY") else 1.2) * np.exp(sign * usd + own), seed + k)
    eurjpy = out["EURUSD"].mid_close * out["USDJPY"].mid_close
    out["EURJPY"] = series_from_mid("EURJPY", eurjpy, seed + 99)
    return out


def split(mkt, symbol):
    return mkt[symbol], {k: v for k, v in mkt.items() if k != symbol}


# ── primitives ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", [p.name for p in PRIMITIVES])
def test_every_primitive_is_causal_including_the_other_instruments(name):
    own, others = split(market(), "EURJPY")
    assert primitive_leakage(PRIMITIVE_BY_NAME[name], own, others, ROWS) == []
    col = PRIMITIVE_BY_NAME[name].column(own, None, others)
    assert np.isfinite(col[-100:]).all(), "the primitive never produces a value on 900 bars of history"


def test_the_truncation_test_catches_a_leak_through_another_instrument():
    own, others = split(market(), "EURJPY")

    def peeks(s, o):  # USDJPY's NEXT close, aligned to this bar: a one-bar leak through a second series
        u = o["USDJPY"]
        return _aligned(s, u, np.concatenate((u.mid_close[1:], [np.nan])))

    assert truncation_leaks(peeks, own, others, ROWS[1:-1])


def test_sessions_and_weekdays_follow_the_bar_close_in_utc():
    s = series_from_mid("EURUSD", np.full(24 * 7, 1.1))
    sess = PRIMITIVE_BY_NAME["session"].column(s)
    close_hour = (np.arange(24) + 1) % 24
    expect = [0 if h < 7 else 1 if h < 12 else 2 if h < 16 else 3 if h < 21 else 4 for h in close_hour]
    assert sess[:24].tolist() == expect
    wd = PRIMITIVE_BY_NAME["weekday"].column(s)
    assert wd[0] == 0 and wd[23] == 1 and wd[24 * 6 + 5] == 6  # the bar closing at 00:00 Tuesday is Tuesday's


def test_the_dollar_basket_is_positive_when_the_dollar_strengthens():
    n = 200
    mkt = market(n, dollar=np.linspace(0, 0.03, n))  # a steadily stronger dollar
    own, others = split(mkt, "EURJPY")
    basket = PRIMITIVE_BY_NAME["usd_basket"].column(own, None, others)
    assert np.nanmean(basket[60:]) > 1.0
    eur, rest = split(market(400, seed=5), "EURUSD")
    corr = PRIMITIVE_BY_NAME["usd_corr"].column(eur, None, rest)
    assert np.nanmean(corr[-50:]) < -0.5  # EURUSD falls when the dollar rises: it is part of the dollar


def test_the_basket_leaves_a_missing_hour_missing_rather_than_filling_it():
    mkt = market(300)
    own, others = split(mkt, "EURJPY")
    keep = np.ones(300, bool)
    keep[150] = False
    thin = {k: (v.take(keep) if k in ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD") else v)
            for k, v in others.items()}
    b = PRIMITIVE_BY_NAME["usd_basket"].column(own, None, thin)
    assert np.isnan(b[150]) and np.isfinite(b[149]) and np.isfinite(b[151])  # 2 of 7 pairs < the minimum 3


def test_a_higher_timeframe_value_uses_only_buckets_that_have_closed():
    own, _ = split(market(), "EURUSD")
    h4 = PRIMITIVE_BY_NAME["h4_trend"]
    b = bucket_start(own.open_time, "H4")
    i = next(k for k in range(700, N - 1) if b[k - 1] == b[k] == b[k + 1])  # inside an H4 bucket still forming
    base = h4.column(own)[i]

    def bumped(rows):
        cols = {f: getattr(own, f).astype(float).copy() for f in ("bid_open", "bid_high", "bid_low", "bid_close",
                                                                  "ask_open", "ask_high", "ask_low", "ask_close")}
        for f in cols:
            cols[f][rows] *= 1.01
        return BarSeries.from_columns("EURUSD", "H1", "synthetic", open_time=own.open_time, ticks=own.ticks,
                                      spread_mean=own.spread_mean, spread_max=own.spread_max, **cols)

    forming = np.flatnonzero(b == b[i])
    forming = forming[forming <= i]
    assert h4.column(bumped(forming))[i] == pytest.approx(base)  # the H4 bar still forming is invisible
    closed = np.flatnonzero(b == b[forming[0] - 1])
    assert h4.column(bumped(closed))[i] != pytest.approx(base)  # the last closed one is not


def test_others_caches_matrices_without_changing_values():
    own, others = split(market(), "EURJPY")
    p = PRIMITIVE_BY_NAME["usd_basket"]
    np.testing.assert_array_equal(p.column(own, None, others), p.column(own, None, Others(others)))


# ── the catalog ────────────────────────────────────────────────────────


def rec(name="f1", definition="close / close[24] - 1", program="P-1", version="1", **kw):
    base = dict(name=name, definition=definition, dimension="momentum", kind="continuous", timeframe="H1",
                requires=("own bars",), provenance="tests", version=version,
                point_in_time="bars closed at or before the decision bar", hypothesis="does it sort outcomes?",
                program=program)
    return FeatureRecord(**(base | kw))


def test_a_record_needs_every_provenance_field(tmp_path):
    cat = FeatureCatalog(tmp_path / "f.jsonl")
    cat.open_program("P-1", 5, NOW)
    for field in ("definition", "hypothesis", "point_in_time", "provenance"):
        with pytest.raises(CatalogError):
            cat.register(rec(**{field: " "}), NOW)
    with pytest.raises(CatalogError):
        cat.register(rec(requires=()), NOW)
    with pytest.raises(CatalogError):
        cat.register(rec(kind="magic"), NOW)


def test_the_budget_is_declared_once_and_enforced(tmp_path):
    cat = FeatureCatalog(tmp_path / "f.jsonl")
    with pytest.raises(CatalogError):
        cat.register(rec(), NOW)  # no budget declared
    cat.open_program("P-1", 2, NOW)
    with pytest.raises(CatalogError):
        cat.open_program("P-1", 50, NOW)  # cannot be raised afterwards
    cat.register(rec("a"), NOW)
    cat.register(rec("b"), NOW)
    cat.register(rec("a"), NOW)  # the same record again is not a new feature
    with pytest.raises(BudgetExceeded):
        cat.register(rec("c"), NOW)
    assert cat.budget("P-1") == (2, 2)


def test_a_registered_definition_cannot_change_under_the_same_version(tmp_path):
    cat = FeatureCatalog(tmp_path / "f.jsonl")
    cat.open_program("P-1", 5, NOW)
    cat.register(rec(), NOW)
    with pytest.raises(CatalogError):
        cat.register(rec(definition="close / close[12] - 1"), NOW)
    assert cat.register(rec(definition="close / close[12] - 1", version="2"), NOW).id == "f1@2"


def test_only_a_feature_that_passed_the_truncation_test_can_be_used(tmp_path):
    cat = FeatureCatalog(tmp_path / "f.jsonl")
    cat.open_program("P-1", 5, NOW)
    good, bad = cat.register(rec("good"), NOW), cat.register(rec("bad"), NOW)
    with pytest.raises(LeakyFeature):
        cat.mark_used(good.id, "EXP-1", NOW)  # unchecked is not passed
    own, others = split(market(), "EURJPY")
    leak = truncation_leaks(lambda s, o: np.concatenate((s.mid_close[1:], [np.nan])), own, others, ROWS[1:-1])
    assert cat.record_leakage(bad.id, leak, len(ROWS) - 2, ["EURJPY"], NOW) == "FAILED"
    ok = primitive_leakage(PRIMITIVE_BY_NAME["up_persistence"], own, others, ROWS)
    assert cat.record_leakage(good.id, ok, len(ROWS), ["EURJPY"], NOW) == "PASSED"
    with pytest.raises(LeakyFeature):
        cat.mark_used(bad.id, "EXP-1", NOW)
    with pytest.raises(CatalogError):
        cat.record_leakage(good.id, [], 0, [], NOW)  # checking nothing is not a check
    cat.mark_used(good.id, "EXP-1", NOW)
    with pytest.raises(CatalogError):
        cat.record_result(good.id, "EXP-2", {"x": 1}, NOW)  # EXP-2 never declared its use
    cat.record_result(good.id, "EXP-1", {"verdict": "REJECTED"}, NOW)


def test_the_catalog_survives_a_restart_and_keeps_what_failed_searchable(tmp_path):
    path = tmp_path / "f.jsonl"
    cat = FeatureCatalog(path)
    cat.open_program("P-1", 5, NOW)
    a, b = cat.register(rec("a"), NOW), cat.register(rec("b", hypothesis="a leaky idea"), NOW)
    cat.record_leakage(a.id, [], 10, ["EURUSD"], NOW)
    cat.record_leakage(b.id, [3, 4], 10, ["EURUSD"], NOW + timedelta(seconds=1))
    cat.mark_used(a.id, "EXP-1", NOW)
    cat.record_result(a.id, "EXP-1", {"verdict": "REJECTED", "t": 0.4}, NOW)
    again = FeatureCatalog(path)
    assert again.entry(a.id) == cat.entry(a.id)
    assert again.leakage_status(b.id) == "FAILED" and again.budget("P-1") == (2, 5)
    assert [e["id"] for e in again.search("leaky")] == ["b@1"]
    assert [e["id"] for e in again.search(leakage="PASSED")] == ["a@1"]
    assert again.results(a.id)[0]["result"]["verdict"] == "REJECTED"


def test_a_tampered_catalog_line_is_refused_on_load(tmp_path):
    path = tmp_path / "f.jsonl"
    cat = FeatureCatalog(path)
    cat.open_program("P-1", 5, NOW)
    cat.register(rec(), NOW)
    lines = path.read_text().splitlines()
    raw = json.loads(lines[1])
    raw["record"]["definition"] = "something that was never registered"
    path.write_text(lines[0] + "\n" + json.dumps(raw) + "\n")
    with pytest.raises(CatalogError):
        FeatureCatalog(path)
