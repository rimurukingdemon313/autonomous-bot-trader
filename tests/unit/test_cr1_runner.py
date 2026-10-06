"""The CR-1 runner end to end on synthetic coins (never the real data): every configuration is judged, nothing is
promoted when funding is mean-zero noise, and a planted funding premium is found. This is how the runner was
proven before it was frozen, without looking at any CR result."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _cr1():
    spec = importlib.util.spec_from_file_location("cr1_under_test", ROOT / "scripts" / "cr1.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["cr1_under_test"] = m
    spec.loader.exec_module(m)
    return m


def write(d: Path, syms, mean_rate: float, seed: int):
    t0 = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
    n = (3 * 365 + 10) * 24
    t = t0 + np.arange(n) * 3600
    for k, s in enumerate(syms):
        rng = np.random.default_rng(seed + k)
        spot = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
        perp = spot * (1 + np.cumsum(rng.normal(0, 0.00003, n)) * 0.0 + rng.normal(0, 0.0002, n))
        ft = t0 + np.arange(n // 8) * 8 * 3600
        fr = rng.normal(mean_rate, 0.0002, len(ft))
        np.savez_compressed(d / f"{s}.npz", spot_t=t, spot_o=spot, perp_t=t.copy(), perp_o=perp, fund_t=ft, fund_r=fr)


@pytest.fixture(scope="module")
def noise(tmp_path_factory):
    m = _cr1()
    d = tmp_path_factory.mktemp("cr")
    write(d, m.SYMBOLS, 0.0, 7)
    m.DATA = d
    return m


def test_every_configuration_is_judged_and_noise_promotes_nothing(noise):
    m = noise
    res = m.evaluate(m.DEV, list(m.CONFIGS))
    assert set(m.CONFIGS) <= set(res)
    for name in m.CONFIGS:
        s = res[name]["summary"]
        assert s["days"] >= 1000 and s["positions"] > 0
        assert {"x1.25", "x1.5", "x2.0", "latency"} <= set(res[name]["stress"])
    for fam in m.PRIMARY:
        assert not m.dev_gates(res, fam)["promoted"]


def test_a_planted_funding_premium_is_found(tmp_path):
    m = _cr1()
    write(tmp_path, m.SYMBOLS, 0.0003, 11)
    m.DATA = tmp_path
    res = m.evaluate(m.DEV, ["CARRY-k3-in1.0"])
    s = res["CARRY-k3-in1.0"]["summary"]
    assert s["ann_net_pct"] > 5 and s["t_day"] > 2 and s["pos_funding_bp"] > 0
