"""DP-002's daily horizon: daily exits charge swap per night, daily features stay causal, the
design is the registry's, and the whole program runs on D1 bars exactly as on H1."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from aitrader.research.discovery.battery import BatteryRules
from aitrader.research.discovery.catalog import FeatureCatalog, FeatureRecord
from aitrader.research.discovery.exits import DAILY_EXITS, EXIT_BY_KEY, EXIT_MENU, simulate
from aitrader.research.discovery.hypothesis import Ledger
from aitrader.research.discovery.primitives import PRIMITIVE_BY_NAME, primitive_leakage
from aitrader.research.discovery.program import DiscoveryProgram, ModelPlan, ProgramDesign
from aitrader.research.discovery.study import Segment
from aitrader.research.discovery.universe import (DAILY_FEATURES, DAILY_PRIMITIVES, DESIGNS, as_registered, dp002,
                                                  feature_records_daily)
from aitrader.research.labels import BUY, CostModel
from aitrader.research.registry import Holdout, Registry
from tests.unit.discovery_market import planted, series

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def test_the_daily_menu_is_declared_beside_the_hourly_one():
    assert [e.key for e in DAILY_EXITS] == ["D1", "D2", "D3", "D4", "D5"]
    assert [e.key for e in EXIT_MENU] == [f"E{i}" for i in range(1, 9)]  # unchanged
    assert set(EXIT_BY_KEY) == {e.key for e in EXIT_MENU + DAILY_EXITS}


def test_a_daily_time_exit_pays_swap_for_every_night_held():
    s = series("EURUSD", np.full(40, 1.1), np.random.default_rng(0), wick=0.0, half=0.0, timeframe="D1")
    atr = np.full(len(s), 0.0080)
    o = simulate(s, np.array([10]), BUY, EXIT_BY_KEY["D3"], 0.0001, CostModel(0.0, 0.0, 0.01), atr=atr)
    # flat prices, 5 daily bars (entry at bar 11, exit at the close of bar 15): 4 nights x 0.01 ATR on a 2 ATR stop
    assert o.reason[0] == 0 and o.bars_held[0] == 5
    assert float(o.r[0]) == pytest.approx(-4 * 0.01 / 2.0)


@pytest.mark.parametrize("name", DAILY_PRIMITIVES)
def test_daily_primitives_are_causal_on_daily_bars(name):
    rng = np.random.default_rng(3)
    usd = np.cumsum(rng.normal(0, 0.006, 700))
    mk = {}
    for k, (sym, sign) in enumerate((("EURUSD", -1), ("GBPUSD", -1), ("AUDUSD", -1), ("USDJPY", 1), ("USDCAD", 1))):
        mid = (110.0 if sym.endswith("JPY") else 1.2) * np.exp(sign * usd + np.cumsum(rng.normal(0, 0.004, 700)))
        mk[sym] = series(sym, mid, np.random.default_rng(k), wick=0.004, half=0.00004, timeframe="D1")
    own, others = mk["EURUSD"], {k: v for k, v in mk.items() if k != "EURUSD"}
    rows = list(range(300, 700, 37)) + [699]
    assert primitive_leakage(PRIMITIVE_BY_NAME[name], own, others, rows) == []


def test_dp002_is_the_declared_daily_design_and_its_threshold_is_the_registrys():
    h = Holdout.load(ROOT / "research" / "holdout.json")
    reg = Registry.load(ROOT / "research" / "registry.jsonl", h)
    d = dp002(reg) if not any(t.id == "DP-002" for t in reg.trials) else as_registered(reg, "DP-002")
    d.validate()
    assert d.timeframe == "D1" and d.grid.size() == 966 and d.judged_tests() == 6
    assert set(d.exits) == {e.key for e in DAILY_EXITS} and d.screen_exit == "D1"
    assert set(d.features()) <= set(feature_records_daily("DP-002")) and len(DAILY_FEATURES) == 29
    assert "hour_sin" not in d.features() and "session" not in d.features()
    assert d.costs.swap_atr_per_night == 0.01
    if any(t.id == "DP-002" for t in reg.trials):
        if reg.status_of("DP-002") == "PENDING":
            assert reg.get("DP-002").design["design_sha256"] == d.sha256()
    else:
        judge = d.segments[2]
        assert d.rules.t_threshold == reg.threshold_for_next(d.universe, judge.start, judge.end, new_tests=6)
    assert set(DESIGNS) == {"DP-001", "DP-002"}


def test_a_daily_program_finds_a_planted_edge_end_to_end(tmp_path):
    syms = tuple(f"S{i}" for i in range(8))
    data = planted(symbols=syms, n=2500, every=30, drift=0.004, noise=0.004, timeframe="D1")
    for sd in data.values():
        assert sd.series.timeframe == "D1"
    hold = Holdout("synthetic", date(2016, 12, 1), datetime(2026, 1, 1, tzinfo=timezone.utc), "test")
    reg = Registry.load(tmp_path / "r.jsonl", hold)
    d = ProgramDesign(
        id="DP-TD", title="daily test", question="does A=high predict a daily rise?", universe="synthetic",
        instruments=syms, segments=(Segment("discovery", "fit", date(2010, 1, 11), date(2012, 1, 1)),
                                    Segment("validation", "select", date(2012, 1, 11), date(2014, 1, 1)),
                                    Segment("confirmation", "judge", date(2014, 1, 11), date(2016, 9, 1))),
        states=("B",), triggers=("A",), groups=(("A", ((0.0,), (1.0,), (2.0,))),), exits=("D1", "D2"),
        rules=BatteryRules(t_threshold=1.0, min_trades=50, permutations=40, random_draws=4),
        holdout_start=hold.start, screen_exit="D1", screen_min_n=30, screen_keep=4, validation_min_n=30,
        finalists=2, model=ModelPlan(features=("A", "B"), quantiles=(0.95,), stride=1, target_exit="D1"),
        feature_budget=6, timeframe="D1")
    d = replace(d, rules=replace(d.rules, t_threshold=reg.threshold_for_next("synthetic", d.segments[2].start,
                                                                             d.segments[2].end, new_tests=3)))
    recs = {f: FeatureRecord(f"{f}.D1", f"synthetic {f}", "test", "continuous", "D1", ("synthetic",), "tests", "1",
                             "by construction", "planted or noise", "DP-TD") for f in ("A", "B", "er120", "vol_ratio")}
    prog = DiscoveryProgram(d, reg, Ledger(tmp_path / "l.jsonl"), FeatureCatalog(tmp_path / "f.jsonl"),
                            tmp_path / "k", lambda: NOW, recs)
    prog.preregister(tmp_path / "doc.md", "doc.md", lambda name: ([], 10, list(syms)))
    assert "D1 bid/ask bars" in (tmp_path / "doc.md").read_text()
    art = prog.run(data)
    assert art["verdict"] == "PASSED", [(c["id"], c["battery"]["failed"]) for c in art["confirmation"]]
    led = Ledger(tmp_path / "l.jsonl")
    for hid in art["validated"]:
        assert led.get(hid).timeframe == "D1" and led.get(hid).side == "BUY"
    judged = {c["id"]: c["exit"] for c in art["confirmation"]}
    assert all(judged[h] in ("D1", "D2") for h in art["validated"])  # the exit frozen at validation
