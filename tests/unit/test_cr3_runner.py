"""The CR-3 runner on synthetic universes (never real data): noise promotes nothing; a few coins paying a large,
persistent funding premium are found and beat cash."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _cr3():
    spec = importlib.util.spec_from_file_location("cr3_under_test", ROOT / "scripts" / "cr3.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["cr3_under_test"] = m
    spec.loader.exec_module(m)
    return m


def write(d: Path, n_coins: int, premium: dict[int, float], seed: int):
    t0 = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
    n = (3 * 366 + 10) * 24
    t = t0 + np.arange(n) * 3600
    for i in range(n_coins):
        rng = np.random.default_rng(seed + i)
        spot = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
        perp = spot * (1 + rng.normal(0, 0.0003, n))
        ft = t0 + np.arange(n // 8) * 8 * 3600
        fr = rng.normal(premium.get(i, 0.0), 0.0002, len(ft))
        np.savez_compressed(d / f"C{i}USDT.npz", spot_t=t, spot_o=spot, perp_t=t.copy(), perp_o=perp, fund_t=ft,
                            fund_r=fr)


def test_noise_promotes_nothing_and_a_planted_premium_beats_cash(tmp_path):
    m = _cr3()
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    write(tmp_path / "a", 12, {}, 1)
    write(tmp_path / "b", 12, {0: 0.0004, 1: 0.0004, 2: 0.0004, 3: 0.0004, 4: 0.0004}, 2)
    noise = m.evaluate(m.DEV, list(m.CONFIGS), tmp_path / "a")
    assert not m.gates(noise, "dev")["passed"]
    planted = m.evaluate(m.DEV, [m.PRIMARY], tmp_path / "b")
    s = planted[m.PRIMARY]["summary"]
    assert s["ann_excess_pct"] > 5 and s["t_excess"] > 2
