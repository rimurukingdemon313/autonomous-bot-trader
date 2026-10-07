"""The CR-4 runner on synthetic pairs (never real data): no funding gap promotes nothing; a persistent gap on some
coins is found and beats cash."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def _cr4():
    spec = importlib.util.spec_from_file_location("cr4_under_test", ROOT / "scripts" / "cr4.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["cr4_under_test"] = m
    spec.loader.exec_module(m)
    return m


def write(d: Path, n: int, gap: dict[int, float], seed: int):
    t0 = int(datetime(2023, 5, 1, tzinfo=timezone.utc).timestamp())
    days = 440
    t = t0 + np.arange(days) * 86400
    for i in range(n):
        rng = np.random.default_rng(seed + i)
        px = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, days)))
        hl = px * (1 + rng.normal(0, 0.001, days))
        hft = t0 + np.arange(days * 24) * 3600
        bft = t0 + np.arange(days * 3) * 8 * 3600
        bfr = rng.normal(0.0001, 0.0001, len(bft))
        hfr = rng.normal(0.0001 / 8 + gap.get(i, 0.0) / 24, 0.00002, len(hft))
        np.savez_compressed(d / f"C{i}.npz", hl_t=t, hl_o=hl, bn_t=t.copy(), bn_o=px, hl_ft=hft, hl_fr=hfr, bn_ft=bft,
                            bn_fr=bfr)


def test_no_gap_promotes_nothing_and_a_planted_gap_beats_cash(tmp_path):
    m = _cr4()
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    write(tmp_path / "a", 12, {}, 1)
    write(tmp_path / "b", 12, {i: 0.002 for i in range(10)}, 2)  # 20 bp a day of extra HL funding on 10 coins
    noise = m.evaluate(m.DEV, list(m.CONFIGS), tmp_path / "a")
    assert not m.gates(noise, "dev")["passed"]
    planted = m.evaluate(m.DEV, [m.PRIMARY], tmp_path / "b")
    s = planted[m.PRIMARY]["summary"]
    assert s["ann_excess_pct"] > 5 and s["t_excess"] > 2 and s["pos_funding_bp"] > 0
