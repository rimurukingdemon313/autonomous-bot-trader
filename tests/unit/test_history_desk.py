"""The history desk: what the most similar past situations did, stated honestly.

The memory is built with known outcomes, so every rate and count is known by
construction.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from aitrader.memory.history import HistoryDesk
from aitrader.memory.patterns import ANALOG_FEATURES, PatternMemory
from aitrader.orchestrator.tracker import ACTIONS

DAY = 86400


def memory(n_days=40, per_day=10, buy_wins=0.7):
    """Situations near the origin; T1:BUY wins in `buy_wins` of the days, every other trade loses 1R.
    `per_day` consecutive hours share their day's outcome, like real overlapping hours."""
    rng = np.random.default_rng(1)
    mem = PatternMemory(np.zeros(len(ANALOG_FEATURES)), np.ones(len(ANALOG_FEATURES)), ACTIONS)
    rows, out, times = [], [], []
    for d in range(n_days):
        win = d < n_days * buy_wins
        for h in range(per_day):
            rows.append(rng.normal(0, 0.1, len(ANALOG_FEATURES)))
            out.append([1.5 if (a == "T1:BUY" and win) else -1.0 for a in ACTIONS])
            times.append(d * DAY + h * 3600)
    t = np.array(times)
    mem.add(np.array(rows), np.array(out), t + 3600, "EURUSD", t)
    return mem


Q = {f: 0.0 for f in ANALOG_FEATURES}


def test_it_reports_what_each_trade_did_in_similar_situations():
    b = HistoryDesk(memory(), "test", k=300).brief(Q, 10**9)
    buy = b["trades"]["T1:BUY"]
    assert b["available"] and b["neighbours"] == 300 and b["situations"] == 400 and b["trades"] and len(b["trades"]) == 4
    assert abs(buy["win_rate"] - 0.7) < 0.08 and buy["avg_R"] > 0.5
    assert b["trades"]["T1:SELL"]["win_rate"] == 0.0
    assert "stop 1 ATR" in buy["what"] and "BUY" in buy["what"]
    assert "not a forecast" in b["note"]


def test_overlapping_hours_are_counted_as_episodes_and_widen_the_bound():
    b = HistoryDesk(memory(), "test", k=300).brief(Q, 10**9)
    assert b["distinct_episodes"] <= 40  # 300 neighbours, but at most 40 distinct days
    buy = b["trades"]["T1:BUY"]
    naive_se = np.std([1.5] * 28 + [-1.0] * 12, ddof=1) / np.sqrt(300)
    assert buy["avg_R_lower_bound"] < buy["avg_R"] - 1.28 * naive_se  # wider than if every hour were independent


def test_only_outcomes_known_at_the_decision_time_are_used():
    mem = memory()
    early = HistoryDesk(mem, "test", k=300).brief(Q, 5 * DAY)  # only ~50 outcomes resolved by then
    assert early["available"] is False


def test_no_comparable_situation_is_said_plainly():
    b = HistoryDesk(memory(), "test", k=300).brief({f: float("nan") for f in ANALOG_FEATURES}, 10**9)
    assert b["available"] is False and b["reason"]


def test_the_service_loads_the_history_only_if_it_matches_its_card(tmp_path):
    from tests.integration.test_service import _write_kb, build

    _write_kb(tmp_path / "kb")
    mem = memory()
    mem.save(tmp_path / "kb" / "history.npz", compact=True)
    digest = hashlib.sha256((tmp_path / "kb" / "history.npz").read_bytes()).hexdigest()
    (tmp_path / "kb" / "history_card.json").write_text(json.dumps({"sha256": digest, "version": "history-test"}))
    rt, _ = build(tmp_path / "a", knowledge_dir=tmp_path / "kb")
    assert rt.history_meta["integrity"] == "VERIFIED" and rt.history_meta["situations"] == 400
    assert rt.orch.history is rt.history

    (tmp_path / "kb" / "history_card.json").write_text(json.dumps({"sha256": "0" * 64}))
    rt, _ = build(tmp_path / "b", knowledge_dir=tmp_path / "kb")
    assert rt.history_meta["integrity"] == "MISMATCH" and rt.history is None  # empty base: nothing to fall back on

    kb = tmp_path / "kb"  # a verified base WITH patterns: the desk falls back to it, never to the unverified file
    memory(n_days=10).save(kb / "memory.npz", compact=True)
    digest = hashlib.sha256((kb / "memory.npz").read_bytes() + (kb / "regime.json").read_bytes()).hexdigest()
    (kb / "knowledge_card.json").write_text(json.dumps({"id": "kb-test", "hash": digest[:16], "sha256": digest}))
    rt, _ = build(tmp_path / "c", knowledge_dir=kb)
    assert rt.history_meta["integrity"] == "FALLBACK (history.npz MISMATCH)" and rt.history_meta["situations"] == 100
    assert rt.history.source.startswith("knowledge base memory")
