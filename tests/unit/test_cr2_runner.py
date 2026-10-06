"""CR-2 runner on synthetic coins (never real data): with zero funding the always-on carry loses the costs and the
risk-free rate, so its excess return is negative; with a large funding premium it is positive."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _cr2():
    spec = importlib.util.spec_from_file_location("cr2_under_test", ROOT / "scripts" / "cr2.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["cr2_under_test"] = m
    spec.loader.exec_module(m)
    return m


def write(d: Path, syms, rate: float):
    t0 = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
    n = (5 * 366 + 10) * 24
    t = t0 + np.arange(n) * 3600
    rng = np.random.default_rng(0)
    for s in syms:
        spot = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
        ft = t0 + np.arange(n // 8) * 8 * 3600
        np.savez_compressed(d / f"{s}.npz", spot_t=t, spot_o=spot, perp_t=t.copy(), perp_o=spot.copy(), fund_t=ft,
                            fund_r=np.full(len(ft), rate))


def test_zero_funding_loses_to_cash_and_a_large_premium_beats_it(tmp_path):
    m = _cr2()
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    write(tmp_path / "a", m.SYMBOLS, 0.0)
    write(tmp_path / "b", m.SYMBOLS, 0.0003)
    win = [("2021-01-01", "2022-01-01"), ("2022-01-01", "2023-01-01")]
    s0 = m.excess_stats(*m.always_on(win, m.COSTS, tmp_path / "a")[::2])
    s1 = m.excess_stats(*m.always_on(win, m.COSTS, tmp_path / "b")[::2])
    assert s0["ann_return_pct"] < 0 and s0["ann_excess_pct"] < s0["ann_return_pct"]
    assert s1["ann_excess_pct"] > 5 and s1["positions"] == 2 * len(m.SYMBOLS)
