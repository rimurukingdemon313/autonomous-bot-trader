"""SQZ-1 on markets built so that the answer is known: crowded shorts that are squeezed pay the spot buyer; crowded
shorts that are not squeezed pay nothing; a coin that rises every day is not a squeeze."""

from __future__ import annotations

import csv
import io
import json
import random
import zipfile
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.sqz1 as S
from aitrader.research.events import squeeze as Q
from aitrader.research.registry import Registry, Trial, Use, Verdict

NOW = datetime(2026, 11, 15, 22, 0, tzinfo=timezone.utc)
H8 = 8 * Q.HOUR
C = 0.0015


def market(coins=12, start="2020-11-01", end="2023-07-20", squeeze=0.05, every=25, drift=None, crowd_on=None, seed=3):
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
                xs.append((Q.day_ms(d) + h * Q.HOUR, -0.002 if d in crowd else 0.0001))
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


def judged(settle, spot, theta=0.001, a="2021-01-01", b="2023-06-30", min_events=300, min_weeks=52, cost=C):
    fund = {s: Q.Funding(x) for s, x in settle.items()}
    seasoned = {s: "2020-08-01" for s in settle}
    bench = Q.Bench(spot, seasoned)
    evs = Q.events(fund, spot, seasoned, bench, a, b, theta, cost)
    late = Q.events(fund, spot, seasoned, bench, a, b, theta, cost, lag=1)
    plac = Q.placebos(fund, spot, seasoned, bench, evs, theta, cost)
    return Q.judge(evs, late, plac, 3.0, cost, min_events, min_weeks, draws=200), evs


def test_crowded_shorts_that_are_squeezed_pay_the_spot_buyer_and_nothing_else_does():
    r, evs = judged(*market()[:2])
    assert r["verdict"] == "PASSED", r.get("gates")
    # +5% planted, less the benchmark (which holds the coin and the other coins' squeezes running then) and 0.3%
    assert 0.015 < r["mean_excess"] < 0.05 and r["placebo_p95"] < 0.01


def test_crowded_shorts_that_are_not_squeezed_pay_nothing():
    r, _ = judged(*market(squeeze=0.0)[:2])
    assert r["verdict"] == "FAILED" and r["mean_excess"] < 0


def test_a_coin_that_rises_every_day_is_not_a_squeeze():
    drift = {k: (0.004 if k < 6 else -0.004) for k in range(12)}
    r, _ = judged(*market(squeeze=0.0, drift=drift, crowd_on=set(range(6)), every=10)[:2])  # only risers crowded
    assert r["mean_excess"] > 0 and not r["gates"]["beats_placebo"] and r["verdict"] == "FAILED"


def test_an_edge_on_one_coin_alone_does_not_pass():
    r, _ = judged(*market(crowd_on={0}, every=8)[:2], min_events=50, min_weeks=20)
    assert r["mean_excess"] > 0 and not r["gates"]["without_best_coin"] and r["verdict"] == "FAILED"


def test_too_few_entries_is_inconclusive_never_a_pass():
    r, _ = judged(*market()[:2], b="2021-03-31")
    assert r["verdict"] == "INCONCLUSIVE"


def test_the_signal_reads_only_settlements_before_the_day_and_needs_their_cover():
    d = Q.day_ms("2021-03-10")
    xs = sorted([(d - k * H8, -0.003) for k in range(1, 10)] + [(d, 5.0)])  # the one at d itself must not count
    assert abs(Q.Funding(xs).signal(d) - (-0.003)) < 1e-12
    sparse = [(d - 70 * Q.HOUR, -0.003), (d - 2 * Q.HOUR, -0.003)]
    assert Q.Funding(sparse).signal(d) is None


def test_one_position_per_coin_at_a_time_and_a_missing_close_is_counted_not_filled():
    settle, spot, _ = market(coins=3)
    allcrowd = {s: [(t, -0.002) for t, _ in xs] for s, xs in settle.items()}
    fund = {s: Q.Funding(x) for s, x in allcrowd.items()}
    seasoned = {s: "2020-08-01" for s in settle}
    evs = Q.events(fund, spot, seasoned, Q.Bench(spot, seasoned), "2021-01-01", "2021-03-31", 0.001, C)
    by = {}
    for e in evs:
        by.setdefault(e["coin"], []).append(e["day"])
    assert all((date.fromisoformat(y) - date.fromisoformat(x)).days >= 7 for v in by.values() for x, y in zip(v, v[1:]))
    gap = dict(spot)
    gap["C00USDT"] = {d: v for d, v in spot["C00USDT"].items() if d != evs[0]["exit"]}
    again = Q.events(fund, gap, seasoned, Q.Bench(gap, seasoned), "2021-01-01", "2021-03-31", 0.001, C)
    assert any(e.get("missing") for e in again if e["coin"] == "C00USDT")


def test_nothing_after_the_exit_or_after_the_decision_changes_a_trade():
    settle, spot, _ = market(coins=4)
    fund = {s: Q.Funding(x) for s, x in settle.items()}
    seasoned = {s: "2020-08-01" for s in settle}
    base = Q.events(fund, spot, seasoned, Q.Bench(spot, seasoned), "2021-01-01", "2021-06-30", 0.001, C)
    e = next(x for x in base if not x.get("missing"))
    later = {s: {d: (v * 7 if d > e["exit"] else v) for d, v in xs.items()} for s, xs in spot.items()}
    fut = {s: Q.Funding([(t, (9.0 if t >= Q.day_ms(e["day"]) else f)) for t, f in x]) for s, x in settle.items()}
    again = Q.events(fut, later, seasoned, Q.Bench(later, seasoned), "2021-01-01", e["day"], 0.001, C)
    same = next(x for x in again if x["coin"] == e["coin"] and x["day"] == e["day"])
    assert abs(same["ret"] - e["ret"]) < 1e-12 and abs(same["signal"] - e["signal"]) < 1e-12


def test_a_scaled_contract_is_bought_as_its_coin_and_seasoning_is_counted_in_months():
    assert S.spot_of("1000PEPEUSDT", {"PEPEUSDT"}) == "PEPEUSDT" and S.spot_of("BTCUSDT", {"BTCUSDT"}) == "BTCUSDT"
    assert S.spot_of("BTCDOMUSDT", {"BTCUSDT"}) is None and S.seasoned_from("2020-01", 7) == "2020-08-01"
    assert S.seasoned_from("2020-11", 7) == "2021-06-01"


def test_every_stage_can_reach_its_own_minimum_and_follows_the_one_before():
    names = list(S.SPEC["stages"])
    for k, name in enumerate(names):
        st = S.SPEC["stages"][name]
        a, b = (date.fromisoformat(x) for x in st["entries"])
        assert ((b - a).days + 1) // 7 >= st["min_weeks"], name
        assert st.get("after") == (S.SPEC["stages"][names[k - 1]]["trial"] if k else None)
        if k:  # a later stage starts after the earlier one's last exit
            prev = date.fromisoformat(S.SPEC["stages"][names[k - 1]]["entries"][1])
            assert a > prev + timedelta(days=S.SPEC["hold_days"])
    assert S.SPEC["bar_floor"] >= 3.0 and S.SPEC["instrument"].startswith("spot")


def test_no_close_after_the_last_exit_and_no_funding_after_the_last_entry_is_read():
    settle = {"A": [(Q.day_ms("2023-06-30") + 16 * Q.HOUR, -0.01), (Q.day_ms("2023-07-01"), -0.01)]}
    spot = {"A": {"2023-07-08": 1.0, "2023-07-09": 99.0}}
    f, s = S.firewall(settle, spot, "2023-06-30", "2023-07-08")
    assert f["A"] == [(Q.day_ms("2023-06-30") + 16 * Q.HOUR, -0.01)] and s["A"] == {"2023-07-08": 1.0}


def _zip(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        s = io.StringIO()
        csv.writer(s).writerows(rows)
        z.writestr("f.csv", s.getvalue())
    return b.getvalue()


def archive(settle, spot, broken=None):
    by = {}
    for s, xs in settle.items():
        for t, f in xs:
            by.setdefault(("fundingRate", s, Q.iso(t)[:7]), []).append([str(t), "8", str(f)])
    for s, xs in spot.items():
        for d, c in xs.items():
            by.setdefault(("spot", s, d[:7]), []).append([str(Q.day_ms(d)), str(c), str(c), str(c), str(c)])
    urls = {S.url(k, s, m): _zip(v) for (k, s, m), v in by.items()}

    def fetch(u):
        if broken and broken in u:
            raise RuntimeError("timed out")
        return urls.get(u)
    coins = {s: {"spot": s, "seasoned": "2020-08-01", "funding": sorted({m for k, x, m in by if k == "fundingRate" and x == s}),
                 "klines": sorted({m for k, x, m in by if k == "spot" and x == s})} for s in settle}
    return fetch, coins


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


def test_a_stage_is_judged_once_and_recorded(tmp_path):
    settle, spot, _ = market()
    fetch, coins = archive(settle, spot)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": coins}))
    reg = registered(tmp_path)
    body = S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)
    assert body["verdict"] == "PASSED" and body["chosen_threshold"] in S.SPEC["thresholds"] and body["bar"] == 3.0
    assert reg.status_of("SQZ-1") == "PASSED" and (tmp_path / "data" / "SQZ-1-events.json.gz").exists()
    assert body["last_day_read"] == "2023-07-08"
    with pytest.raises(SystemExit, match="judged once"):
        S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)


def test_nothing_is_judged_unregistered_with_other_code_on_a_partial_archive_or_out_of_order(tmp_path):
    settle, spot, _ = market(coins=3, end="2021-03-31")
    fetch, coins = archive(settle, spot, broken="-1d-2021-02")
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
    with pytest.raises(SystemExit, match="only after SQZ-1 passed"):
        S.run("validation", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "z", "validation"), probe_file=probe)
    (tmp_path / "w").mkdir()
    reg = registered(tmp_path / "w", "forward", passed=("SQZ-1", "SQZ-1-V", "SQZ-1-H"))
    with pytest.raises(SystemExit, match="on or after"):
        S.run("forward", tmp_path / "d", NOW, fetch=no, reg=reg, probe_file=probe)
