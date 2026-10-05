"""RV-1: cross-sectional signals, point-in-time timing, currency-neutral books and costs, on synthetic
markets whose answer is known by construction."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from aitrader.data.h10 import available_at
from aitrader.research.discovery import rv
from aitrader.research.discovery.edges import build
from aitrader.research.discovery.rv import (CURRENCIES, NON_USD, Book, Costs, Panel, Quote, forward_relative,
                                            global_vol, rank_weights, ranks, regimes, scores, spearman, week)

ROOT = Path(__file__).resolve().parents[2]


def weekdays(a: date, b: date) -> list[date]:
    out, d = [], a
    while d < b:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def panel(drift: dict | None = None, seed: int = 1, start=date(1999, 1, 4), end=date(2001, 6, 1),
          noise=0.004) -> Panel:
    """Daily log values; currency c drifts by drift[c] per day on top of noise."""
    rng = np.random.default_rng(seed)
    ds = weekdays(start, end)
    logv = {"USD": np.zeros(len(ds))}
    for c in NON_USD:
        steps = rng.normal(0, noise, len(ds)) + (drift or {}).get(c, 0.0)
        logv[c] = np.cumsum(steps)
    return Panel(tuple(ds), np.array([available_at(d) for d in ds], np.int64), logv)


def test_average_ranks_and_spearman_known_answers():
    assert list(ranks(np.array([10.0, 30.0, 20.0, 20.0, np.nan]))[:4]) == [1.0, 4.0, 2.5, 2.5]
    a = np.arange(8, dtype=float)
    assert spearman(a, a) == pytest.approx(1.0) and spearman(a, -a) == pytest.approx(-1.0)
    assert np.isnan(spearman(a[:5], a[:5]))  # fewer than six currencies: no IC


def test_the_book_is_currency_neutral_with_gross_two():
    w = rank_weights(np.array([0.5, 1.0, np.nan, 3.0, 2.0, -1.0, 4.0, 0.0]))
    assert w.sum() == pytest.approx(0.0) and np.abs(w).sum() == pytest.approx(2.0) and w[2] == 0.0
    assert not rank_weights(np.array([1.0, 2.0, 3.0, np.nan, np.nan, np.nan, 4.0, 5.0])).any()  # five: no book


def test_the_decision_uses_thursdays_rate_and_the_week_runs_monday_to_monday():
    p = panel()
    w = week(p, date(2000, 3, 10))  # a Friday
    assert p.dates[w.d] == date(2000, 3, 9)  # Thursday's rate is usable Friday 17:00; Friday's is not
    assert p.dates[w.e] == date(2000, 3, 13) and p.dates[w.x] == date(2000, 3, 20)
    rr = forward_relative(p, w)
    assert rr.sum() == pytest.approx(0.0)  # relative returns: the common move cancels


def test_no_signal_changes_when_everything_unusable_at_the_decision_is_removed():
    p = panel(seed=3)
    rates = np.array([5.0, 3.0, 0.5, 4.5, 1.5, 4.0, 6.0, 7.0])
    for f in (date(2000, 2, 4), date(2000, 9, 15), date(2001, 3, 2)):
        w = week(p, f)
        t = rv.ny_epoch(f, 17)
        keep = p.available <= t
        cut = Panel(tuple(d for d, k in zip(p.dates, keep) if k), p.available[keep],
                    {c: v[keep] for c, v in p.logv.items()})
        w2 = rv.Week(f, cut.last_available(t), w.e, w.x)
        assert w2.d == w.d
        a, b = scores(p, w, rates), scores(cut, w2, rates)
        for k in rv.SIGNALS:
            assert np.array_equal(np.nan_to_num(a[k], nan=-1), np.nan_to_num(b[k], nan=-1)), k
        assert global_vol(p, w) == global_vol(cut, w2)


def test_a_planted_carry_effect_is_found_and_a_null_world_is_not():
    rates = np.array([5.0, 3.0, 0.5, 4.5, 1.5, 4.0, 6.0, 7.0])  # USD, EUR, JPY, GBP, CHF, CAD, AUD, NZD
    drift = {c: 0.0004 * (rates[i + 1] - rates.mean()) for i, c in enumerate(NON_USD)}
    for world, expect in ((panel(drift, seed=5, noise=0.0015), "strong"), (panel(None, seed=5, noise=0.0015), "none")):
        ics = []
        for f in rv.fridays(date(2000, 1, 7), date(2001, 5, 1)):
            w = week(world, f)
            ics.append(spearman(scores(world, w, rates)["carry"], forward_relative(world, w)))
        m = float(np.nanmean(ics))
        assert (m > 0.5) if expect == "strong" else (abs(m) < 0.15), (expect, m)


def test_regimes_use_only_earlier_weeks():
    gv = list(np.linspace(1, 2, 80))
    a = regimes(gv)
    b = regimes(gv[:60] + [100.0] * 20)  # a change in the future
    assert a[:60] == b[:60] and a[51] is None and a[52] == "HIGH"


def test_book_costs_and_financing_by_hand():
    q0 = {c: Quote(1.0, 0.0001, 0.0001) for c in NON_USD}
    q1 = dict(q0)
    q1["EUR"] = Quote(1.01, 0.0001, 0.0001)  # EUR +1% against USD
    target = np.zeros(len(CURRENCIES))
    target[CURRENCIES.index("EUR")], target[CURRENCIES.index("USD")] = 1.0, -1.0
    rates = np.array([1.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    b = Book(Costs(slippage_pips=0.1, commission_pips_rt=0.7, financing_markup=0.0))
    first = b.step(date(2010, 1, 4), q0, target, rates)
    assert first["cost"] == pytest.approx(1.0 * (0.0001 + (0.1 + 0.35) * 0.0001))  # half-spread + slip + half comm
    second = b.step(date(2010, 1, 11), q1, target, rates)
    assert second["gross"] == pytest.approx(0.01)
    assert second["financing"] == pytest.approx(1.0 * (3.0 - 1.0) / 100 * 7 / 360)
    assert sum(second["contrib"].values()) == pytest.approx(second["gross"])  # attribution adds up
    assert second["cost"] == 0.0  # no change in position, no cost


def test_a_usd_quoted_currency_is_valued_as_the_inverse_of_its_pair():
    b = Book(Costs(slippage_pips=0, commission_pips_rt=0, spread_multiple=0, financing_markup=0))
    q0 = {c: Quote(1.0, 0.0, 0.0) for c in NON_USD}
    q0["JPY"] = Quote(100.0, 0.0, 0.0)
    q1 = dict(q0)
    q1["JPY"] = Quote(98.0, 0.0, 0.0)  # USDJPY falls: JPY rises
    target = np.zeros(len(CURRENCIES))
    target[CURRENCIES.index("JPY")], target[CURRENCIES.index("USD")] = 1.0, -1.0
    b.step(date(2010, 1, 4), q0, target, np.zeros(8))
    assert b.step(date(2010, 1, 11), q1, target, np.zeros(8))["gross"] == pytest.approx(100 / 98 - 1)


def test_the_edge_registry_takes_the_latest_stage_classification(tmp_path):
    (tmp_path / "discovery").mkdir()
    (tmp_path / "discovery" / "ledger.jsonl").write_text("")
    k = tmp_path / "knowledge"
    k.mkdir()
    res = {"weeks": 300, "t": 3.1, "ic_by_year": {"2001": {"mean_ic": 0.1}}, "gates": {"t": True, "weeks": True}}
    (k / "XS-9.json").write_text(json.dumps({"program": "XS-9", "kind": "cross_sectional", "stage": 1,
                                             "threshold": 2.807, "results": {"A": res, "B": res | {"t": 0.4}},
                                             "verdict": "PASSED", "classification": {"A": "STAGE2", "B": "REJECTED"}}))
    two = {"net": {"mean": 0.001}, "gross": {"mean": 0.0015}, "robustness": {"R5_costs": {"net_mean_costs_x2": 0.0005}}}
    (k / "XS-9-S2.json").write_text(json.dumps({"program": "XS-9-S2", "kind": "cross_sectional", "stage": 2,
                                                "results": {"A": two}, "verdict": "FAILED",
                                                "classification": {"A": "PROMISING"}}))
    reg = build(tmp_path)
    got = {e["edge_id"]: (e["status"], e["net_expectancy"]) for e in reg["edges"]}
    assert got == {"A": ("PROMISING", 0.001), "B": ("REJECTED", None)}
    assert reg["programs"]["XS-9"]["verdict"] == "FAILED"
    for e in reg["edges"]:
        assert not any(f in e for f in ("size", "lots", "risk_pct", "risk_amount"))


def test_the_research_never_reaches_risk_execution_or_the_broker():
    src = (ROOT / "aitrader" / "research" / "discovery" / "rv.py").read_text()
    runner = (ROOT / "scripts" / "rv1.py").read_text()
    for forbidden in ("aitrader.risk", "aitrader.broker", "aitrader.execution", "tradelocker"):
        assert forbidden not in src and forbidden not in runner
    for word in ("lots", "position_size", "risk_amount", "leverage"):
        assert word not in src


def test_the_frozen_spec_is_intact_when_present():
    p = ROOT / "research" / "specs" / "RV-1.json"
    if not p.exists():
        pytest.skip("RV-1 not yet frozen")
    sys.path.insert(0, str(ROOT / "scripts"))
    import rv1
    frozen = json.loads(p.read_text())
    assert rv1.spec_sha(frozen["spec"]) == frozen["sha256"]
    assert frozen["spec"]["stage1"]["threshold"] == 2.807 and frozen["pit_check"]["differences"] == 0
    assert frozen["spec"]["universe"] == list(CURRENCIES)
