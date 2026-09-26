"""Regime model (training-only fit, familiarity) and point-in-time pattern memory."""

from __future__ import annotations

import numpy as np
import pytest

from aitrader.features.store import INDEX, NAMES
from aitrader.memory.patterns import ANALOG_FEATURES, PatternMemory
from aitrader.regime.model import RegimeModel, regime_report


def random_matrix(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    m = rng.normal(0, 1, (n, len(NAMES)))
    m[:, INDEX["vol_ratio"]] = np.abs(rng.normal(1, 0.2, n))
    m[:, INDEX["er120"]] = rng.uniform(0, 0.6, n)
    m[:, INDEX["spread_rel"]] = np.abs(rng.normal(0.05, 0.01, n))
    m[:, INDEX["ma_slope"]] = rng.normal(0, 1, n)
    return m


def values(row):
    return {n: float(row[i]) for i, n in enumerate(NAMES)}


def test_regime_fit_refuses_rows_after_its_training_cutoff():
    m = random_matrix()
    times = np.arange(len(m)) * 3600
    with pytest.raises(ValueError, match="look-ahead"):
        RegimeModel.fit(m, times, trained_until=int(times[-2]))
    model = RegimeModel.fit(m, times, trained_until=int(times[-1]))
    assert model.n_train == len(m)


def test_familiar_state_passes_and_extreme_state_is_unfamiliar():
    m = random_matrix()
    model = RegimeModel.fit(m, np.arange(len(m)), trained_until=len(m))
    ok = model.classify(values(np.median(m, axis=0)))
    assert ok.familiar
    weird = values(np.median(m, axis=0))
    weird["r120"] = 50.0
    st = model.classify(weird)
    assert not st.familiar and any("unfamiliar" in r for r in st.reasons)


def test_abnormal_spread_or_volatility_is_flagged_and_missing_inputs_fail_closed():
    m = random_matrix()
    model = RegimeModel.fit(m, np.arange(len(m)), trained_until=len(m))
    v = values(np.median(m, axis=0))
    v["spread_rel"] = 10.0
    assert model.classify(v).label == "ABNORMAL"
    v = values(np.median(m, axis=0))
    v["er120"] = float("nan")
    st = model.classify(v)
    assert st.abnormal and not st.familiar


def test_regime_model_round_trips_through_json():
    m = random_matrix()
    model = RegimeModel.fit(m, np.arange(len(m)), trained_until=len(m))
    back = RegimeModel.from_json(model.to_json())
    v = values(m[10])
    assert back.classify(v) == model.classify(v)


def test_regime_report_measures_persistence():
    labels = ["RANGING"] * 50 + ["TRENDING_UP"] * 50
    rep = regime_report(labels, np.r_[np.full(50, -0.1), np.full(50, 0.2)])
    assert rep["persistence"]["RANGING"] == pytest.approx(49 / 50)
    assert rep["mean_outcome"]["TRENDING_UP"]["mean"] == pytest.approx(0.2)


# ── pattern memory ──────────────────────────────────────────────────────


def _memory(n=400, seed=2):
    rng = np.random.default_rng(seed)
    m = rng.normal(0, 1, (n, len(NAMES)))
    mem = PatternMemory.fit_scaler(m, ("T1:BUY", "T1:SELL"))
    return mem, m


def test_an_outcome_is_invisible_until_it_has_resolved():
    mem, m = _memory()
    n = len(m)
    avail = np.where(np.arange(n) < n // 2, 1000, 5000)
    # Outcomes known early are +1; outcomes that resolve later are -1.
    out = np.column_stack([np.where(avail == 1000, 1.0, -1.0)] * 2)
    mem.add(m, out, avail, "EURUSD", np.arange(n))
    q = values(m[0])
    early = mem.query(q, t=2000, k=50)
    assert early is not None and early.available == n // 2
    assert early.actions["T1:BUY"].mean_r == pytest.approx(1.0)
    late = mem.query(q, t=6000, k=50)
    assert late.available == n


def test_query_refuses_to_answer_with_too_little_experience():
    mem, m = _memory(n=40)
    mem.add(m, np.ones((40, 2)), np.full(40, 100), "EURUSD", np.arange(40))
    assert mem.query(values(m[0]), t=1000, k=100) is None
    assert mem.query(values(m[0]), t=50, k=10) is None  # nothing resolved yet


def test_nearest_neighbour_is_exact_and_incomplete_rows_are_skipped():
    mem, m = _memory()
    m2 = m.copy()
    m2[5, INDEX["r24"]] = np.nan
    added = mem.add(m2, np.ones((len(m), 2)), np.full(len(m), 10), "EURUSD", np.arange(len(m)))
    assert added == len(m) - 1
    ev = mem.query(values(m[7]), t=100, k=20)
    assert ev.examples[0]["distance"] == pytest.approx(0.0, abs=1e-3)


def test_a_symbols_own_recent_patterns_can_be_excluded():
    mem, m = _memory()
    n = len(m)
    mem.add(m, np.full((n, 2), 1.0), np.full(n, 10), "EURUSD", np.arange(n))
    mem.add(m, np.full((n, 2), -1.0), np.full(n, 10), "GBPUSD", np.arange(n))
    ev = mem.query(values(m[3]), t=100, k=50, exclude_symbol="EURUSD", exclude_after=0)
    assert ev.actions["T1:BUY"].mean_r == pytest.approx(-1.0)


def test_memory_round_trips_through_a_file(tmp_path):
    mem, m = _memory()
    mem.add(m, np.ones((len(m), 2)), np.full(len(m), 10), "EURUSD", np.arange(len(m)))
    mem.save(tmp_path / "p.npz")
    back = PatternMemory.load(tmp_path / "p.npz")
    a = mem.query(values(m[1]), t=100, k=30)
    b = back.query(values(m[1]), t=100, k=30)
    assert a.actions["T1:BUY"].mean_r == b.actions["T1:BUY"].mean_r
    assert len(back) == len(mem)


def test_analog_features_all_exist_in_the_store():
    assert all(f in INDEX for f in ANALOG_FEATURES)
