"""DIV-2: excess-return arithmetic by hand, rates that are never carried across a publisher's gap,
FX excluded (never substituted) without a rate, and the frozen design."""

from __future__ import annotations

import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from aitrader.research.discovery import excess

ROOT = Path(__file__).resolve().parents[2]


def days(n, start=date(2000, 1, 3)):
    return [start + timedelta(days=i) for i in range(n)]


def test_equity_excess_return_by_hand():
    ds = days(3)
    ix = excess.equity_index(ds, [100.0, 101.0, 101.0], [math.nan, 5.0, 5.0])
    # day 1: +1% price, minus (5% - 2% dividend) / 252 funding
    assert ix[1] / ix[0] - 1 == pytest.approx(0.01 - 0.03 / 252)
    assert ix[2] / ix[1] - 1 == pytest.approx(-0.03 / 252)


def test_bond_excess_return_is_carry_minus_duration_times_yield_change():
    ds = days(3)
    ix = excess.bond_index(ds, [4.0, 4.1, 4.1], [math.nan, 2.0, 2.0], 8.0)
    assert ix[1] / ix[0] - 1 == pytest.approx((4.0 - 2.0) / 100 / 252 - 8.0 * 0.001)
    assert ix[2] / ix[1] - 1 == pytest.approx((4.1 - 2.0) / 100 / 252)


def test_fx_excess_return_adds_the_rate_differential_and_a_missing_rate_excludes_the_day():
    ds = days(3)
    ix = excess.fx_index(ds, [1.0, 1.01, 1.01], [math.nan, 5.0, math.nan], [math.nan, 1.0, 1.0])
    assert ix[1] / ix[0] - 1 == pytest.approx(0.01 + 0.04 / 365)
    assert np.isnan(ix[2])  # no foreign rate in force: not substituted, not held


def test_rates_are_never_carried_across_a_publishers_gap(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import div2
    f = tmp_path / "r.csv"
    f.write_text("currency,effective_date,value_pct,available_at_epoch\n"
                 "JPY,2000-01-03,0.5,946944000\n")  # published 2000-01-04
    r = div2.Rates(f)
    assert np.isnan(r.at("JPY", date(2000, 1, 3)))  # not yet public at that close
    assert r.at("JPY", date(2000, 1, 5)) == 0.5
    assert np.isnan(r.at("JPY", date(2000, 2, 1)))  # more than 7 days old: a gap, not a value


def test_yield_scale_rule_was_fixed_in_advance():
    sys.path.insert(0, str(ROOT / "scripts"))
    import div2
    assert np.allclose(div2.normalise_yield(np.array([42.5, 43.0]), "x"), [4.25, 4.3])
    assert np.allclose(div2.normalise_yield(np.array([4.25, 4.3]), "x"), [4.25, 4.3])
    with pytest.raises(SystemExit):
        div2.normalise_yield(np.array([500.0, 600.0]), "x")


def test_the_policy_rate_extract_matches_its_manifest():
    import hashlib
    man = json.loads((ROOT / "data" / "div2" / "manifest.json").read_text())["policy_rates.csv"]
    body = (ROOT / "data" / "div2" / "policy_rates.csv").read_bytes()
    assert hashlib.sha256(body).hexdigest() == man["sha256"]


def test_the_whole_pipeline_runs_on_synthetic_prices(tmp_path, monkeypatch):
    """Smoke test before freezing: every asset class is built, the 2021+ data is sealed without a key,
    and a judgement is produced. Prices are synthetic random walks (no market data is read)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import div2
    if not (ROOT / "data" / "h10" / "daily_2018-10-17_8a6dec2.csv").exists():
        pytest.skip("the H.10 vintage is not present in this checkout")
    rng = np.random.default_rng(0)
    monkeypatch.setattr(div2, "RAW", tmp_path)
    d0 = date(1988, 1, 4)
    ds = [d0 + timedelta(days=i) for i in range(int(365.25 * 35)) if (d0 + timedelta(days=i)).weekday() < 5]
    for name in (*div2.EQUITY, *div2.COMMODITY_YAHOO, *div2.COMMODITY_DATAHUB):
        p = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(ds))))
        (tmp_path / f"{name}.csv").write_text("date,value\n" + "".join(f"{d},{v}\n" for d, v in zip(ds, p)))
    for name in div2.BONDS:
        y = 5 + np.cumsum(rng.normal(0, 0.03, len(ds)))
        (tmp_path / f"{name}.csv").write_text("date,value\n" + "".join(f"{d},{v}\n" for d, v in zip(ds, y)))
    panel = div2.build_indices()
    assert max(panel.dates) < div2.HOLD_START
    assert set(panel.closes) == set(div2.ASSETS)
    r = div2.judge_one(panel, "tsmom12")
    assert r["net"]["n"] == 216 and r["seen_period_2008_2020_descriptive"]["net"]["n"] > 100
    assert r["avg_assets"] > 10


def test_the_div2_design_is_frozen():
    sys.path.insert(0, str(ROOT / "scripts"))
    import div2
    frozen = json.loads(div2.SPEC.read_text())
    assert div2.spec_sha(frozen["spec"]) == frozen["sha256"]
    assert div2.code_hash() == frozen["code_sha256"], "DIV-2 study code changed after registration"
