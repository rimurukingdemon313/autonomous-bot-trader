"""The radar runner end to end with faked venues: state persists across runs through the cache file, and the ledger
alone restores positions when the cache is gone (history restarts, nothing assumed)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from aitrader.radar import venues as V

ROOT = Path(__file__).resolve().parents[2]
T0 = 1_760_000_400


def _runner():
    spec = importlib.util.spec_from_file_location("radar_run_under_test", ROOT / "scripts" / "radar_run.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["radar_run_under_test"] = m
    spec.loader.exec_module(m)
    return m


def test_runs_persist_and_the_ledger_restores_after_cache_loss(tmp_path, monkeypatch):
    m = _runner()
    quotes = [V.Quote("hyperliquid", "ABC", 1.0, 0.6 / 8760, 100.0, 5e7), V.Quote("gate", "ABC", 1.0, 0.05 / 8760, 100.0, 5e7),
              V.Quote("mexc", "SOLO", 1.0, 0.0, 1.0, 5e7)]
    monkeypatch.setattr(m.V, "snapshot", lambda: (list(quotes), {}))
    state, pub = tmp_path / "s", tmp_path / "p"
    for k in range(80):
        monkeypatch.setattr(sys, "argv", ["x", "--state", str(state), "--publish", str(pub), "--now", str(T0 + k * 3600)])
        m.main()
    led = json.loads((pub / "ledger.json").read_text())
    assert len(led["open"]) == 1 and led["runs"] == 80
    assert "ABC" in (pub / "REPORT.md").read_text()
    (state / "state.json.gz").unlink()  # the cache was evicted
    monkeypatch.setattr(sys, "argv", ["x", "--state", str(state), "--publish", str(pub), "--now", str(T0 + 80 * 3600)])
    m.main()
    led2 = json.loads((pub / "ledger.json").read_text())
    assert led2["open"][0]["id"] == led["open"][0]["id"] and led2["runs"] == 81
    assert "history restarted" in (pub / "REPORT.md").read_text()
    m.main()  # a second run in the same hour changes nothing
    assert json.loads((pub / "ledger.json").read_text())["runs"] == 81


def test_the_look_is_frozen_once_and_never_rewritten(tmp_path):
    m = _runner()
    perf = {"days": 61, "closed_positions": 5}
    first = m.freeze_looks(tmp_path, perf, 100)
    assert first["status"] == "INCONCLUSIVE"
    assert m.freeze_looks(tmp_path, {**perf, "days": 90, "closed_positions": 50}, 200)["t"] == 100  # no second look yet
    good = {"days": 121, "closed_positions": 50, "ann_excess_deployed_pct": 20.0, "t_excess_daily": 2.4,
            "ann_excess_deployed_costs_x1.5_pct": 12.0, "book_excess_without_best_coin_pct": 1.0, "max_dd_pct": 2.0,
            "run_coverage": 0.97}
    second = m.freeze_looks(tmp_path, good, 300)
    assert second["status"] == "FAILED" and second["gates"]["t_excess_daily"] is False  # 2.4 < the extended 2.5
    assert m.freeze_looks(tmp_path, {**good, "t_excess_daily": 9.0}, 400)["t"] == 300
    early = tmp_path / "early"
    early.mkdir()
    assert m.freeze_looks(early, {"days": 10}, 1) is None and not list(early.iterdir())
