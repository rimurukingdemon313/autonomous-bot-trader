"""The NE-1 runner end to end on synthetic US index CFD hours (never the real data): it evaluates every
configuration, applies every gate, promotes nothing on a driftless random walk, and finds a planted overnight
premium. This is how the runner was proven to work before it was frozen, without looking at any NE result."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.research.canon.engine import NY

ROOT = Path(__file__).resolve().parents[2]


def _ne1():
    spec = importlib.util.spec_from_file_location("ne1_under_test", ROOT / "scripts" / "ne1.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["ne1_under_test"] = m
    spec.loader.exec_module(m)
    return m


def synth(dir_: Path, sym: str, seed: int, overnight_bp: float = 0.0, start=date(2013, 9, 2), end=date(2017, 1, 1)):
    rng = np.random.default_rng(seed)
    rows = []
    px = 2000.0
    d = start
    while d < end:
        if d.weekday() < 5:
            for h in range(24):
                if h == 17:
                    continue
                t = int(datetime(d.year, d.month, d.day, h, tzinfo=NY).timestamp())
                step = rng.normal(0, 0.0025 * px)
                if overnight_bp and (h >= 16 or h < 9):
                    step += px * overnight_bp / 1e4 / 16  # spread over the 16 overnight hours
                rows.append((t, px, px + step))
                px += step
        d += timedelta(days=1)
    rows.sort()
    t = np.array([r[0] for r in rows], np.int64)
    o = np.array([r[1] for r in rows])
    c = np.array([r[2] for r in rows])
    h, lo = np.maximum(o, c) * 1.0004, np.minimum(o, c) * 0.9996
    hs = 0.00008 * o  # ~1.6 bp spread
    s = BarSeries.from_columns(sym, "H1", "synthetic", open_time=t, bid_open=o - hs, bid_high=h - hs, bid_low=lo - hs,
                               bid_close=c - hs, ask_open=o + hs, ask_high=h + hs, ask_low=lo + hs, ask_close=c + hs,
                               ticks=np.ones(len(t)), spread_mean=2 * hs, spread_max=2 * hs)
    s.save(dir_ / f"{sym}_H1_synth.npz")


@pytest.fixture(scope="module")
def ne1_noise(tmp_path_factory):
    m = _ne1()
    d = tmp_path_factory.mktemp("ix")
    for k, sym in enumerate(m.SYMBOLS):
        synth(d, sym, seed=10 + k)
    m.DATA = d
    return m


def test_the_runner_judges_every_configuration_and_promotes_nothing_on_noise(ne1_noise):
    m = ne1_noise
    res = m.evaluate(m.DEV, list(m.CONFIGS))
    assert set(m.CONFIGS) <= set(res)
    for name in m.CONFIGS:
        s = res[name]["summary"]
        assert s["trades"] > 100
        assert s["cost_bp"] > 0 and abs(s["gross_bp"] - s["net_bp"] - s["cost_bp"]) < 1e-3
        assert "x1.5" in res[name]["stress"] and "latency_1bar" in res[name]["stress"]
    on = res["ON-16-09"]["summary"]
    assert on["fin_bp"] > 0  # an overnight long pays financing
    for fam in m.PRIMARY:
        assert not m.dev_gates(res, fam)["promoted"]


def test_the_runner_sees_a_planted_overnight_premium(tmp_path):
    m = _ne1()
    for k, sym in enumerate(m.SYMBOLS):
        synth(tmp_path, sym, seed=20 + k, overnight_bp=25.0)
    m.DATA = tmp_path
    res = m.evaluate(m.DEV, ["ON-16-09"])
    s = res["ON-16-09"]["summary"]
    assert s["gross_bp"] > 15 and s["net_bp"] > 0 and s["t_day"] > 2
    assert res["ON-16-09"]["mechanism"]["overnight_minus_intraday_gross_bp"] > 0
