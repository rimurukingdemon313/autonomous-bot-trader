"""CR-5 static cross-venue carry on synthetic pairs: segments roll at a 25% move, funding is collected, a zero gap
earns less than cash, and 3x scales return but not the risk-free rate."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _cr5():
    spec = importlib.util.spec_from_file_location("cr5_under_test", ROOT / "scripts" / "cr5.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["cr5_under_test"] = m
    spec.loader.exec_module(m)
    return m


def write(d: Path, gap_per_day: float, trend: float = 0.0):
    t0 = int(datetime(2023, 5, 1, tzinfo=timezone.utc).timestamp())
    days = 800
    t = t0 + np.arange(days) * 86400
    for k, c in enumerate(("BTC", "ETH")):
        rng = np.random.default_rng(k)
        px = 100 * np.exp(np.cumsum(rng.normal(trend, 0.02, days)))
        hft = t0 + np.arange(days * 24) * 3600
        bft = t0 + np.arange(days * 3) * 8 * 3600
        np.savez_compressed(d / f"{c}.npz", hl_t=t, hl_o=px * (1 + rng.normal(0, 0.0005, days)), bn_t=t.copy(), bn_o=px,
                            hl_ft=hft, hl_fr=np.full(len(hft), 0.0001 / 8 + gap_per_day / 24), bn_ft=bft,
                            bn_fr=np.full(len(bft), 0.0001))


def test_a_steady_gap_beats_cash_at_3x_and_no_gap_does_not(tmp_path):
    m = _cr5()
    (tmp_path / "g").mkdir()
    (tmp_path / "z").mkdir()
    write(tmp_path / "g", 0.0003)  # 3 bp a day ~ 11% a year
    write(tmp_path / "z", 0.0)
    g = m.evaluate(tmp_path / "g", m.DEV)["summary"]
    z = m.evaluate(tmp_path / "z", m.DEV)["summary"]
    assert g["ann_excess_pct"] > 5 and g["funding_bp_total"] > 0
    assert z["ann_excess_pct"] < 0
    assert abs(g["ann_return_pct"] - 3 * g["ann_return_1x_pct"]) < 0.01  # both rounded to 3 decimals


def test_a_large_move_rolls_the_position(tmp_path):
    m = _cr5()
    write(tmp_path, 0.0003, trend=0.003)  # drifts far: several 25% moves
    s = m.evaluate(tmp_path, m.DEV)["summary"]
    assert s["rebalances"] >= 2 and s["cost_bp_total"] > 2 * 2 * (2 * (4.5 + 2) + 2 * (5 + 2))
