"""CASC-1 on markets built so that the answer is known: a liquidation-led fall that is bought back pays the spot
buyer; one that is not pays nothing; a fall led by spot that is bought back just as much is no liquidation effect."""

from __future__ import annotations

import csv
import io
import json
import random
import zipfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.casc1 as S
from aitrader.research.events import cascade as K
from aitrader.research.registry import Registry, Trial, Use, Verdict

NOW = datetime(2026, 11, 15, 23, 0, tzinfo=timezone.utc)
C = 0.0025
H = K.HOUR


def _ms(d):
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)


def market(coins=10, start="2023-06-01", end="2025-03-05", rebound=0.06, every=60, spot_led=4, spot_rebound=0.0,
           only=None, seed=5):
    """Hourly spot and perpetual closes. Every `every` hours (staggered by coin) a coin's spot falls 12% over four
    hours, then recovers `rebound` over the next 24. On the first `coins` contracts the perpetual is 1% below spot
    through the fall (liquidations); on `spot_led` more it is 1% above (spot leads), and they recover `spot_rebound`."""
    rng = random.Random(seed)
    t0, n = _ms(start), (_ms(end) - _ms(start)) // H
    spot, perp = {}, {}
    plan = [(f"C{k:02d}USDT", -0.01, rebound, only is None or k in only) for k in range(coins)]
    plan += [(f"D{k:02d}USDT", +0.01, spot_rebound, True) for k in range(spot_led)]
    for k, (name, prem, reb, falls) in enumerate(plan):
        starts = list(range(200 + 7 * k, n - 40, every)) if falls else []
        step, fall = {}, set()
        for h0 in starts:
            for j in range(4):
                step[h0 + j] = (0.88 ** 0.25) - 1
                fall.add(h0 + j)
            for j in range(4, 28):
                step[h0 + j] = (1 + reb) ** (1 / 24) - 1
        lvl, s, p = 100.0, {}, {}
        for i in range(n):
            lvl *= 1 + rng.gauss(0, 0.002) + step.get(i, 0.0)
            s[t0 + i * H] = lvl
            p[t0 + i * H] = lvl * (1 + (prem if i in fall else 0.0))
        spot[name], perp[name] = s, p
    return t0, n, spot, perp


def panel(t0, n, spot, perp):
    p = K.Panel(sorted(spot), t0, n, {c: _ms("2020-08-01") for c in spot})
    for c in spot:
        p.put("spot", c, spot[c])
        p.put("perp", c, perp[c])
    return p


def judged(t0, n, spot, perp, drop=0.08, first="2023-07-01", last="2025-02-28", min_events=150, min_days=40, cost=C):
    p = panel(t0, n, spot, perp)
    a, b = (_ms(first) - t0) // H, (_ms(last) + 86_400_000 - t0) // H - 1
    evs = K.events(p, a, b, drop, 0.005, cost)
    late = K.events(p, a, b, drop, 0.005, cost, lag=1)
    con = K.contrast(p, a, b, drop, 0.005, cost)
    plac = K.placebos(p, evs, drop, cost, draws=20)
    return K.judge(p, evs, late, con, plac, 3.0, cost, min_events, min_days, draws=200), evs


def test_a_liquidation_led_fall_that_is_bought_back_pays_the_spot_buyer():
    r, evs = judged(*market())
    assert r["verdict"] == "PASSED", r.get("gates")
    # +6% planted less 0.5% of fills, and less the fall's last hour when the rule enters before the low
    assert 0.01 < r["mean_net"] < 0.07 and r["placebo_p95"] < 0.01 and r["spot_led_mean_net"] < 0


def test_a_fall_that_is_not_bought_back_pays_nothing():
    r, _ = judged(*market(rebound=0.0))
    assert r["verdict"] == "FAILED" and r["mean_net"] < 0


def test_a_fall_led_by_spot_is_not_bought():
    r, evs = judged(*market(coins=0, spot_led=6))  # the perpetual stays above spot: no entry at all
    assert evs == [] and r["verdict"] == "INCONCLUSIVE"


def test_when_spot_led_falls_are_bought_back_as_much_the_mechanism_gate_refuses():
    r, _ = judged(*market(spot_rebound=0.09))  # falls led by spot are bought back even more
    assert r["spot_led_falls"] > 0 and not r["gates"]["beats_spot_led_falls"]


def test_an_edge_on_one_coin_alone_does_not_pass_and_too_few_is_inconclusive():
    r, _ = judged(*market(only={0}, every=30), min_events=50, min_days=20)
    assert r["mean_net"] > 0 and not r["gates"]["without_best_coin"] and r["verdict"] == "FAILED"
    r2, _ = judged(*market(), last="2023-07-20")
    assert r2["verdict"] == "INCONCLUSIVE"


def test_one_position_per_coin_and_nothing_after_the_exit_changes_a_trade():
    t0, n, spot, perp = market(coins=3)
    p = panel(t0, n, spot, perp)
    evs = K.events(p, 0, n - 1, 0.08, 0.005, C)
    by = {}
    for e in evs:
        by.setdefault(e["coin"], []).append(e["hour"])
    assert all(y - x >= K.HOLD for v in by.values() for x, y in zip(v, v[1:]))
    e = next(x for x in evs if not x.get("missing"))
    p.spot[p.idx[e["coin"]], e["hour"] + K.HOLD + 1:] *= 5
    again = next(x for x in K.events(p, 0, n - 1, 0.08, 0.005, C) if x["coin"] == e["coin"] and x["hour"] == e["hour"])
    assert abs(again["ret"] - e["ret"]) < 1e-12


def test_a_missing_close_is_counted_not_filled():
    t0, n, spot, perp = market(coins=2)
    p = panel(t0, n, spot, perp)
    e = next(x for x in K.events(p, 0, n - 1, 0.08, 0.005, C) if not x.get("missing"))
    p.spot[p.idx[e["coin"]], e["hour"] + K.HOLD] = np.nan
    again = next(x for x in K.events(p, 0, n - 1, 0.08, 0.005, C) if x["coin"] == e["coin"] and x["hour"] == e["hour"])
    assert again.get("missing") and "ret" not in again


def test_every_stage_can_reach_its_own_minimum_and_follows_the_one_before():
    names = list(S.SPEC["stages"])
    for k, name in enumerate(names):
        st = S.SPEC["stages"][name]
        a, b = (date.fromisoformat(x) for x in st["decisions"])
        assert (b - a).days + 1 >= st["min_days"], name
        assert st.get("after") == (S.SPEC["stages"][names[k - 1]]["trial"] if k else None)
        if k:
            assert a > date.fromisoformat(S.SPEC["stages"][names[k - 1]]["decisions"][1]) + timedelta(days=2)
    assert S.SPEC["bar_floor"] >= 3.0 and S.SPEC["instrument"].startswith("spot") and "scripts/sqz1.py" in S.CODE


def _zip(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        s = io.StringIO()
        csv.writer(s).writerows(rows)
        z.writestr("f.csv", s.getvalue())
    return b.getvalue()


def archive(spot, perp, broken=None):
    by = {}
    for kind, series in (("spot", spot), ("perp", perp)):
        for c, xs in series.items():
            for t, v in xs.items():
                m = datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m")
                by.setdefault((kind, c, m), []).append([str(t), str(v), str(v), str(v), str(v)])
    urls = {S.url(k, c, m): _zip(v) for (k, c, m), v in by.items()}

    def fetch(u):
        if broken and broken in u:
            raise RuntimeError("timed out")
        return urls.get(u)
    coins = {c: {"spot": c, "seasoned": "2020-08-01", "spot_1h": sorted({m for k, x, m in by if k == "spot" and x == c}),
                 "perp_1h": sorted({m for k, x, m in by if k == "perp" and x == c})} for c in spot}
    return fetch, coins


def registered(tmp_path, stage="dev", code=None, passed=()):
    reg = Registry(tmp_path / "registry.jsonl")
    for name in list(S.SPEC["stages"])[: list(S.SPEC["stages"]).index(stage) + 1]:
        st = S.SPEC["stages"][name]
        a, b = st["decisions"]
        reg.register(Trial(id=st["trial"], registered=NOW - timedelta(hours=1), title="t", hypothesis="h",
                           uses=(Use(S.UNIVERSE, date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
                           tests=st["tests"], configurations=st["tests"], preregistration=S.DOC,
                           design={"code_sha256": code or S.code_hash(), "spec_sha256": S.spec_sha(), "stage": name}))
        if st["trial"] in passed:
            reg.record_verdict(Verdict(st["trial"], NOW, "PASSED", {}))
    return reg


def test_a_stage_is_judged_once_and_reads_no_bar_after_its_last_exit(tmp_path):
    t0, n, spot, perp = market(coins=6, every=40)
    late = _ms("2025-03-03")
    for c in spot:  # a bar after the last exit that would wreck every trade if it were read
        spot[c][late] = 1e-6
    fetch, coins = archive(spot, perp)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": coins}))
    reg = registered(tmp_path)
    body = S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)
    assert body["verdict"] == "PASSED" and body["chosen_drop"] in S.SPEC["drops"] and body["bar"] == 3.0
    assert body["last_moment_read"].startswith("2025-03-02") and reg.status_of("CASC-1") == "PASSED"
    with pytest.raises(SystemExit, match="judged once"):
        S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)


def test_nothing_is_judged_unregistered_with_other_code_on_a_partial_archive_or_out_of_order(tmp_path):
    t0, n, spot, perp = market(coins=2, end="2023-09-01")
    fetch, coins = archive(spot, perp, broken="-1h-2023-08")
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
    with pytest.raises(SystemExit, match="only after CASC-1 passed"):
        S.run("validation", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "z", "validation"), probe_file=probe)
    (tmp_path / "w").mkdir()
    reg = registered(tmp_path / "w", "forward", passed=("CASC-1", "CASC-1-V"))
    with pytest.raises(SystemExit, match="on or after"):
        S.run("forward", tmp_path / "d", NOW, fetch=no, reg=reg, probe_file=probe)
