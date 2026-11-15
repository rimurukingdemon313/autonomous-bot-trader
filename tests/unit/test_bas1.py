"""BAS-1 on markets built so that the answer is known: high funding followed by a planted rise pays the spot
buyer; high funding with nothing after it pays nothing; a coin that rises every day is not the arbitrage."""

from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.bas1 as S
import tests.unit.test_sqz1 as T
from aitrader.research.events import basis as B
from aitrader.research.events import squeeze as Q
from aitrader.research.registry import Registry, Trial, Use, Verdict

NOW = datetime(2026, 11, 15, 23, 0, tzinfo=timezone.utc)
C = 0.0015


def market(coins=12, start="2020-11-01", end="2023-07-20", squeeze=0.05, every=25, drift=None, crowd_on=None, seed=3, sign=1):
    """Daily spot closes and 8-hourly funding for `coins` coins. Every `every` days (staggered by coin) a coin's
    funding is -0.2% per settlement for the three days before day d; from the close of d-1 its price then gains
    `squeeze` over seven days. drift[k] adds a daily drift to coin k; crowd_on limits the episodes to those coins."""
    rng = random.Random(seed)
    days = [(date.fromisoformat(start) + timedelta(days=i)).isoformat()
            for i in range((date.fromisoformat(end) - date.fromisoformat(start)).days + 1)]
    settle, spot, eps = {}, {}, {}
    for k in range(coins):
        name = f"C{k:02d}USDT"
        ev = set(days[30 + k * 2::every]) if (crowd_on is None or k in crowd_on) else set()
        eps[name] = ev
        crowd = {Q.plus(d, -j) for d in ev for j in (1, 2, 3)}
        xs = []
        for d in days:
            for h in (0, 8, 16):
                xs.append((Q.day_ms(d) + h * Q.HOUR, (sign * 0.002) if d in crowd else 0.0001))
        settle[name] = xs
        lvl, closes, boost = 100.0, {}, {}
        for d in ev:
            for j in range(7):
                boost[Q.plus(d, j)] = (1 + squeeze) ** (1 / 7) - 1
        for d in days:
            lvl *= 1 + rng.gauss(0, 0.01) + boost.get(d, 0.0) + ((drift or {}).get(k, 0.0))
            closes[d] = lvl
        spot[name] = closes
    return settle, spot, eps


def judged(settle, spot, theta=0.001, a="2021-01-01", b="2023-06-30", min_events=300, min_weeks=52):
    fund = {s: Q.Funding(x) for s, x in settle.items()}
    seasoned = {s: "2020-08-01" for s in settle}
    bench = Q.Bench(spot, seasoned)
    evs = B.events(fund, spot, seasoned, bench, a, b, theta, C)
    late = B.events(fund, spot, seasoned, bench, a, b, theta, C, lag=1)
    plac = B.placebos(fund, spot, seasoned, bench, evs, theta, C)
    return Q.judge(evs, late, plac, 3.0, C, min_events, min_weeks, draws=200), evs


def test_high_funding_followed_by_a_rise_pays_the_spot_buyer():
    r, _ = judged(*market()[:2])
    assert r["verdict"] == "PASSED", r.get("gates")
    assert 0.015 < r["mean_excess"] < 0.05 and r["placebo_p95"] < 0.01


def test_high_funding_with_nothing_after_it_pays_nothing_and_negative_funding_is_not_bought():
    r, _ = judged(*market(squeeze=0.0)[:2])
    assert r["verdict"] == "FAILED" and r["mean_excess"] < 0
    _, evs = judged(*market(sign=-1)[:2])
    assert evs == []


def test_a_coin_that_rises_every_day_is_not_the_arbitrage():
    drift = {k: (0.004 if k < 6 else -0.004) for k in range(12)}
    r, _ = judged(*market(squeeze=0.0, drift=drift, crowd_on=set(range(6)), every=10)[:2])
    assert r["mean_excess"] > 0 and not r["gates"]["beats_placebo"] and r["verdict"] == "FAILED"


def test_every_stage_can_reach_its_own_minimum_and_follows_the_one_before():
    names = list(S.SPEC["stages"])
    for k, name in enumerate(names):
        st = S.SPEC["stages"][name]
        a, b = (date.fromisoformat(x) for x in st["entries"])
        assert ((b - a).days + 1) // 7 >= st["min_weeks"], name
        assert st.get("after") == (S.SPEC["stages"][names[k - 1]]["trial"] if k else None)
        if k:
            assert a > date.fromisoformat(S.SPEC["stages"][names[k - 1]]["entries"][1]) + timedelta(days=S.SPEC["hold_days"])
    assert S.SPEC["bar_floor"] >= 3.0 and S.SPEC["instrument"].startswith("spot")
    assert "aitrader/research/events/squeeze.py" in S.CODE and "scripts/sqz1.py" in S.CODE


def registered(tmp_path, stage="dev", code=None, passed=()):
    reg = Registry(tmp_path / "registry.jsonl")
    for name in list(S.SPEC["stages"])[: list(S.SPEC["stages"]).index(stage) + 1]:
        st = S.SPEC["stages"][name]
        a, b = st["entries"]
        reg.register(Trial(id=st["trial"], registered=NOW - timedelta(hours=1), title="t", hypothesis="h",
                           uses=(Use(S.UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
                           tests=st["tests"], configurations=st["tests"], preregistration=S.DOC,
                           design={"code_sha256": code or S.code_hash(), "spec_sha256": S.spec_sha(), "stage": name}))
        if st["trial"] in passed:
            reg.record_verdict(Verdict(st["trial"], NOW, "PASSED", {}))
    return reg


def test_a_stage_is_judged_once_and_reads_nothing_after_its_last_exit(tmp_path):
    settle, spot, _ = market(end="2025-03-20", every=20)
    for s in spot:  # a close after the last exit that would wreck every benchmark if it were read
        spot[s]["2025-03-12"] = 1e-9
    fetch, coins = T.archive(settle, spot)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": coins}))
    reg = registered(tmp_path)
    body = S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)
    assert body["verdict"] == "PASSED" and body["chosen_threshold"] in S.SPEC["thresholds"] and body["bar"] == 3.0
    assert body["last_day_read"] == "2025-03-08" and reg.status_of("BAS-1") == "PASSED"
    with pytest.raises(SystemExit, match="judged once"):
        S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)


def test_nothing_is_judged_unregistered_with_other_code_on_a_partial_archive_or_out_of_order(tmp_path):
    settle, spot, _ = market(coins=3, end="2021-03-31")
    fetch, coins = T.archive(settle, spot, broken="-1d-2021-02")
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": coins}))
    no = lambda u: pytest.fail("fetched")
    with pytest.raises(SystemExit, match="not registered"):
        S.run("dev", tmp_path / "d", NOW, fetch=no, reg=Registry(tmp_path / "r.jsonl"), probe_file=probe)
    (tmp_path / "x").mkdir()
    with pytest.raises(SystemExit, match="differs"):
        S.run("dev", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "x", code="0" * 64), probe_file=probe)
    (tmp_path / "y").mkdir()
    with pytest.raises(SystemExit, match="partial"):
        S.run("dev", tmp_path / "d", NOW, fetch=fetch, reg=registered(tmp_path / "y"), out_dir=tmp_path / "y", probe_file=probe)
    (tmp_path / "z").mkdir()
    with pytest.raises(SystemExit, match="only after BAS-1 passed"):
        S.run("validation", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "z", "validation"), probe_file=probe)
    (tmp_path / "w").mkdir()
    reg = registered(tmp_path / "w", "forward", passed=("BAS-1", "BAS-1-V"))
    with pytest.raises(SystemExit, match="on or after"):
        S.run("forward", tmp_path / "d", NOW, fetch=no, reg=reg, probe_file=probe)
