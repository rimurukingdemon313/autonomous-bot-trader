"""Experiment registry and the holdout seal in the data loader."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from aitrader.data.bars import BarSeries
from aitrader.data.store import DataStore, open_final_test
from aitrader.research.registry import (
    Holdout, HoldoutSpent, Registry, RegistryError, Trial, Use, Verdict, bonferroni_t, holm,
)

ROOT = Path(__file__).resolve().parents[2]
SEAL = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
H = Holdout("u", date(2017, 1, 1), SEAL, "test")


def trial(tid, at, uses, tests=1, cfg=1, prereg="docs/p.md"):
    return Trial(tid, at, tid, "h", tuple(uses), tests, cfg, "PENDING", prereg)


def hold_use():
    return Use("u", date(2017, 1, 1), date(2019, 1, 1), "judge")


def test_bonferroni_and_holm_known_answers():
    assert bonferroni_t(13) == pytest.approx(2.89, abs=0.005)
    assert holm([0.01, 0.04, 0.03, 0.005]) == [True, False, False, True]


def test_append_only_rules(tmp_path):
    reg = Registry(tmp_path / "r.jsonl", H)
    reg.register(trial("a", SEAL, [Use("u", date(2010, 1, 1), date(2011, 1, 1), "fit")]))
    with pytest.raises(RegistryError, match="never reused"):
        reg.register(trial("a", SEAL + timedelta(1), []))
    with pytest.raises(RegistryError, match="back-filling"):
        reg.register(trial("b", SEAL - timedelta(1), []))
    reg.record_verdict(Verdict("a", SEAL + timedelta(hours=1), "FAILED"))
    with pytest.raises(RegistryError, match="final status"):
        reg.record_verdict(Verdict("a", SEAL + timedelta(hours=2), "PASSED"))
    again = Registry.load(tmp_path / "r.jsonl", H)
    assert again.status_of("a") == "FAILED"


def test_exposure_before_the_seal_is_declared_not_blocking(tmp_path):
    reg = Registry(tmp_path / "r.jsonl", H)
    reg.register(trial("old", SEAL - timedelta(days=3), [hold_use()], tests=5, cfg=5, prereg=None))
    assert not reg.holdout_spent()
    assert [t.id for t in reg.prior_exposure_of_holdout()] == ["old"]
    # ...and it still counts toward the threshold of the final test.
    assert reg.tests_on("u", date(2017, 1, 1), date.max) == 5


def test_post_seal_use_needs_preregistration_and_is_single_use(tmp_path):
    reg = Registry(tmp_path / "r.jsonl", H)
    with pytest.raises(RegistryError, match="pre-registered"):
        reg.register(trial("casual", SEAL + timedelta(1), [hold_use()], prereg=None))
    reg.register(trial("final", SEAL + timedelta(1), [hold_use()]))
    assert reg.holdout_spent()
    with pytest.raises(HoldoutSpent):
        reg.register(trial("again", SEAL + timedelta(2), [hold_use()]))
    # A fresh process reading the file refuses too.
    with pytest.raises(HoldoutSpent):
        Registry.load(tmp_path / "r.jsonl", H).register(trial("again", SEAL + timedelta(2), [hold_use()]))


def test_committed_registry_and_seal_are_consistent():
    h = Holdout.load(ROOT / "research" / "holdout.json")
    reg = Registry.load(ROOT / "research" / "registry.jsonl", h)
    assert reg.tests_on(h.universe) >= 16
    # The archive never touched 2007 .. 2012-10 (this project's own registered
    # experiments may, and are counted like any other).
    archive = [t for t in reg.touching(h.universe, date(2007, 1, 1), date(2012, 11, 1))
               if t.registered < h.sealed_at]
    assert archive == []
    # Nothing registered after the seal may have touched the holdout except
    # a final test (none exists yet).
    post = [t for t in reg.touching(h.universe, h.start, date.max) if t.registered >= h.sealed_at]
    assert all(t.design.get("final_test") for t in post)


# ── the loader enforces the seal ────────────────────────────────────────


def _store(tmp_path: Path, holdout: Holdout) -> DataStore:
    t0 = int(datetime(2016, 12, 30, tzinfo=timezone.utc).timestamp())
    n = 4 * 24 * 4  # four days of M15
    times = t0 + 900 * np.arange(n)
    mid = 1.05 + 0.0001 * np.sin(np.arange(n) / 7)
    s = BarSeries.from_columns(
        "EURUSD", "M15", "t", open_time=times,
        bid_open=mid - 1e-5, bid_high=mid + 2e-4, bid_low=mid - 2e-4, bid_close=mid - 1e-5,
        ask_open=mid + 1e-5, ask_high=mid + 2.2e-4, ask_low=mid - 1.8e-4, ask_close=mid + 1e-5,
        ticks=np.full(n, 5), spread_mean=np.full(n, 2e-5), spread_max=np.full(n, 3e-5))
    proc = tmp_path / "processed"
    digest = s.save(proc / "EURUSD_M15.npz")
    (tmp_path / "manifest.json").write_text(json.dumps(
        {"datasets": {"EURUSD": {"file": "EURUSD_M15.npz", "content_sha256": digest}}}))
    return DataStore(proc, holdout)


def test_loader_truncates_at_the_seal_without_a_key(tmp_path):
    store = _store(tmp_path, H)
    cutoff = H.start_epoch()
    m15 = store.load("EURUSD")
    assert len(m15) > 0 and int(m15.open_time.max()) < cutoff
    h1 = store.load("EURUSD", "H1")
    assert int(h1.available_at.max()) <= cutoff


def test_only_a_sole_preregistered_final_test_gets_a_key(tmp_path):
    store = _store(tmp_path, H)
    reg = Registry(tmp_path / "r.jsonl", H)
    reg.register(trial("final", SEAL + timedelta(1), [hold_use()]))
    key = open_final_test(reg, "final")
    assert int(store.load("EURUSD", key=key).open_time.max()) >= H.start_epoch()
    reg.record_verdict(Verdict("final", SEAL + timedelta(2), "FAILED"))
    with pytest.raises(RegistryError, match="not pending"):
        open_final_test(reg, "final")


def test_a_tampered_file_is_refused(tmp_path):
    store = _store(tmp_path, H)
    path = tmp_path / "processed" / "EURUSD_M15.npz"
    s = BarSeries.load(path)
    bumped = BarSeries.from_columns("EURUSD", "M15", "t", **{
        f: (getattr(s, f) * (1.0001 if f == "bid_close" else 1)) for f in (
            "open_time", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high",
            "ask_low", "ask_close", "ticks", "spread_mean", "spread_max")})
    bumped.save(path)
    store._raw.cache_clear()
    from aitrader.data.store import DataUnavailable
    with pytest.raises(DataUnavailable, match="hash"):
        store.load("EURUSD")
