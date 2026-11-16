"""SPL-1 on markets built so that the answer is known: a rally led by spot that keeps going pays the spot buyer; one
that fades does not; a rally led by the perpetual is not bought; a market-wide rally is no coin's own demand."""

from __future__ import annotations

import csv
import io
import json
import random
import zipfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

import scripts.spl1 as S
from aitrader.research.events import cascade as K
from aitrader.research.events import rally as P
from aitrader.research.registry import Registry, Trial, Use, Verdict

NOW = datetime(2026, 11, 16, 6, 0, tzinfo=timezone.utc)
C = 0.0025
H = K.HOUR


def _ms(d):
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)


def market(coins=10, start="2023-06-01", end="2025-03-05", follow=0.06, every=80, lev_led=4, lev_follow=0.0,
           only=None, seed=5, drift=0.0, together=False, giveback=True, follow_hours=24, rise_hours=4):
    """Hourly spot and perpetual closes. Every `every` hours (staggered by coin, or all at once when `together`) a
    coin's spot rises 12% over four hours, moves `follow` over the next 24, and gives all of it back over the 36
    after, so that prices do not trend. On the first `coins` contracts the perpetual stays 0.1% below spot through
    the rise (spot leads); on `lev_led` more it is 1% above (the perpetual leads), and they move `lev_follow`."""
    rng = random.Random(seed)
    t0, n = _ms(start), (_ms(end) - _ms(start)) // H
    spot, perp = {}, {}
    plan = [(f"C{k:02d}USDT", -0.001, follow, only is None or k in only) for k in range(coins)]
    plan += [(f"D{k:02d}USDT", +0.01, lev_follow, True) for k in range(lev_led)]
    for k, (name, prem, fol, rises) in enumerate(plan):
        starts = list(range(200 + (0 if together else 7 * k), n - 40, every)) if rises else []
        step, rise = {}, set()
        for h0 in starts:
            for j in range(rise_hours):
                step[h0 + j] = (1.12 ** (1 / rise_hours)) - 1
                rise.add(h0 + j)
            for j in range(rise_hours, rise_hours + follow_hours):
                step[h0 + j] = (1 + fol) ** (1 / follow_hours) - 1
            for j in range(rise_hours + 24, rise_hours + 60) if giveback else ():  # after the hold
                step[h0 + j] = (1 / (1.12 * (1 + fol))) ** (1 / 36) - 1
        lvl, s, p = 100.0, {}, {}
        for i in range(n):
            lvl *= 1 + rng.gauss(0, 0.002) + step.get(i, 0.0) + drift
            s[t0 + i * H] = lvl
            p[t0 + i * H] = lvl * (1 + (prem if i in rise else 0.0))
        spot[name], perp[name] = s, p
    return t0, n, spot, perp


def panel(t0, n, spot, perp):
    p = K.Panel(sorted(spot), t0, n, {c: _ms("2020-08-01") for c in spot})
    for c in spot:
        p.put("spot", c, spot[c])
        p.put("perp", c, perp[c])
    return p


def judged(t0, n, spot, perp, rise=0.08, first="2023-07-01", last="2025-02-28", min_events=150, min_days=40, cost=C):
    p = panel(t0, n, spot, perp)
    a, b = (_ms(first) - t0) // H, (_ms(last) + 86_400_000 - t0) // H - 1
    evs = P.events(p, a, b, rise, 0.005, cost)
    late = P.events(p, a, b, rise, 0.005, cost, lag=1)
    con = P.contrast(p, a, b, rise, 0.005, cost)
    plac = P.placebos(p, evs, rise, cost, draws=20)
    return P.judge(p, evs, late, con, plac, 3.0, cost, min_events, min_days, draws=200), evs


def test_a_spot_led_rally_that_keeps_going_pays_the_spot_buyer():
    r, evs = judged(*market())
    assert r["verdict"] == "PASSED", r.get("gates")
    # +6% planted after the rise, less 0.5% of fills, plus the rise's last hour: the rule enters once 8% is reached
    # the perpetual-led rallies are caught before their top too: they keep the rise's last hour, nothing more
    assert 0.01 < r["mean_net"] < 0.10 and r["mean_excess_vs_market"] > 0.01 and r["leverage_led_mean_net"] < 0.03
    assert "beats_spot_led_falls" not in r["gates"] and "spot_led_mean_net" not in r


def test_a_rally_that_fades_pays_nothing():
    r, _ = judged(*market(follow=-0.03))
    assert r["verdict"] == "FAILED" and r["mean_net"] < 0


def test_a_rally_led_by_the_perpetual_is_not_bought():
    r, evs = judged(*market(coins=0, lev_led=6))
    assert evs == [] and r["verdict"] == "INCONCLUSIVE"


def test_when_perpetual_led_rallies_keep_going_as_far_the_mechanism_gate_refuses():
    r, _ = judged(*market(lev_follow=0.09))
    assert r["leverage_led_rallies"] > 0 and not r["gates"]["beats_leverage_led_rallies"] and r["verdict"] == "FAILED"


def test_a_rally_of_the_whole_market_is_no_coin_s_own_demand():
    # every coin rises together and keeps going: each trade pays, but none beats the market it moved with
    r, _ = judged(*market(coins=12, lev_led=0, together=True))
    assert r["mean_net"] > 0 and not r["gates"]["beats_market"] and r["verdict"] == "FAILED"


def test_a_market_that_rises_at_every_hour_is_no_continuation():
    # rare rallies entered at their top (a 10% bar on a 12% rise), and a drift that pays every hour alike
    r, _ = judged(*market(follow=0.0, drift=0.001, lev_follow=0.03, every=400, giveback=False), rise=0.10)
    assert r["mean_net"] > 0 and not r["gates"]["beats_placebo"] and r["verdict"] == "FAILED"


def test_a_follow_through_that_is_over_within_the_hour_is_not_tradable():
    # a two-hour rise is caught at its top; all of its follow-through comes in the next hour, before a late entry
    r, _ = judged(*market(rise_hours=2, follow_hours=1))
    assert r["mean_net"] > 0.03 and r["late_mean"] < 0 and not r["gates"]["late_entry"] and r["verdict"] == "FAILED"


def test_the_placebo_is_drawn_only_at_hours_without_a_rise():
    t0, n, spot, perp = market(coins=3)
    p = panel(t0, n, spot, perp)
    evs = [e for e in P.events(p, 0, n - 1, 0.08, 0.005, C) if not e.get("missing")]
    for e in evs[:30]:
        k, h = p.idx[e["coin"]], e["hour"]
        hs = P.placebo_hours(p, k, h, 0.08)
        S = p.spot[k]
        assert hs and all(S[x] / S[x - P.LOOK] - 1 < 0.08 / 3 and abs(x - h) >= P.HOLD for x in hs)
        assert not set(hs) & {x["hour"] for x in evs if x["coin"] == e["coin"]}


def test_an_edge_on_one_coin_alone_does_not_pass_and_too_few_is_inconclusive():
    r, _ = judged(*market(only={0}, every=70), min_events=50, min_days=20)
    assert r["mean_net"] > 0 and not r["gates"]["without_best_coin"] and r["verdict"] == "FAILED"
    r2, _ = judged(*market(), last="2023-07-20")
    assert r2["verdict"] == "INCONCLUSIVE"


def test_one_position_per_coin_and_nothing_after_the_exit_changes_a_trade():
    t0, n, spot, perp = market(coins=3)
    p = panel(t0, n, spot, perp)
    evs = P.events(p, 0, n - 1, 0.08, 0.005, C)
    by = {}
    for e in evs:
        by.setdefault(e["coin"], []).append(e["hour"])
    assert all(y - x >= P.HOLD for v in by.values() for x, y in zip(v, v[1:]))
    e = next(x for x in evs if not x.get("missing"))
    p.spot[p.idx[e["coin"]], e["hour"] + P.HOLD + 1:] *= 5
    again = next(x for x in P.events(p, 0, n - 1, 0.08, 0.005, C) if x["coin"] == e["coin"] and x["hour"] == e["hour"])
    assert abs(again["ret"] - e["ret"]) < 1e-12


def test_a_missing_close_is_counted_not_filled_and_a_missing_premium_is_not_spot_led():
    t0, n, spot, perp = market(coins=2)
    p = panel(t0, n, spot, perp)
    e = next(x for x in P.events(p, 0, n - 1, 0.08, 0.005, C) if not x.get("missing"))
    p.spot[p.idx[e["coin"]], e["hour"] + P.HOLD] = np.nan
    again = next(x for x in P.events(p, 0, n - 1, 0.08, 0.005, C) if x["coin"] == e["coin"] and x["hour"] == e["hour"])
    assert again.get("missing") and "ret" not in again
    p.perp[p.idx[e["coin"]], e["hour"] - 2] = np.nan  # an hour of the rise without the perpetual: not shown spot-led
    assert not any(x["coin"] == e["coin"] and x["hour"] == e["hour"] for x in P.events(p, 0, n - 1, 0.08, 0.005, C))


def test_every_stage_can_reach_its_own_minimum_and_follows_the_one_before():
    names = list(S.SPEC["stages"])
    for k, name in enumerate(names):
        st = S.SPEC["stages"][name]
        a, b = (date.fromisoformat(x) for x in st["decisions"])
        assert (b - a).days + 1 >= st["min_days"], name
        assert st.get("after") == (S.SPEC["stages"][names[k - 1]]["trial"] if k else None)
        if k:
            assert a > date.fromisoformat(S.SPEC["stages"][names[k - 1]]["decisions"][1]) + timedelta(days=2)
    assert S.SPEC["bar_floor"] >= 3.0 and S.SPEC["instrument"].startswith("spot") and "scripts/casc1.py" in S.CODE
    assert "crypto-spot-liquidation-falls" in S.COUNTED  # CASC-1 read the same panel: its tests count


def _zip(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        s = io.StringIO()
        csv.writer(s).writerows(rows)
        z.writestr("f.csv", s.getvalue())
    return b.getvalue()


def archive(spot, perp, broken=None):
    import scripts.casc1 as CA
    by = {}
    for kind, series in (("spot", spot), ("perp", perp)):
        for c, xs in series.items():
            for t, v in xs.items():
                m = datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m")
                by.setdefault((kind, c, m), []).append([str(t), str(v), str(v), str(v), str(v)])
    urls = {CA.url(k, c, m): _zip(v) for (k, c, m), v in by.items()}

    def fetch(u):
        if broken and broken in u:
            raise RuntimeError("timed out")
        return urls.get(u)
    coins = {c: {"spot": c, "seasoned": "2020-08-01", "spot_1h": sorted({m for k, x, m in by if k == "spot" and x == c}),
                 "perp_1h": sorted({m for k, x, m in by if k == "perp" and x == c})} for c in spot}
    return fetch, coins


def registered(tmp_path, stage="dev", code=None, passed=(), casc=0):
    reg = Registry(tmp_path / "registry.jsonl")
    if casc:
        reg.register(Trial(id="CASC-X", registered=NOW - timedelta(days=1), title="t", hypothesis="h",
                           uses=(Use("crypto-spot-liquidation-falls", date(2023, 7, 1), date(2025, 3, 1), "judge"),),
                           tests=casc, configurations=casc, preregistration="x", design={}))
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
    t0, n, spot, perp = market(coins=6)
    late = _ms("2025-03-03")
    for c in spot:  # a bar after the last exit that would wreck every trade if it were read
        spot[c][late] = 1e-6
    fetch, coins = archive(spot, perp)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": coins}))
    reg = registered(tmp_path)
    body = S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)
    assert body["verdict"] == "PASSED" and body["chosen_rise"] in S.SPEC["rises"] and body["bar"] == 3.0
    assert body["last_moment_read"].startswith("2025-03-02") and reg.status_of("SPL-1") == "PASSED"
    with pytest.raises(SystemExit, match="judged once"):
        S.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)


def test_the_bar_counts_casc_1_s_tests_on_the_same_panel(tmp_path):
    from aitrader.research.registry import bonferroni_t
    reg = registered(tmp_path, casc=40)
    assert S.bar_for(reg, "2023-07-01", "2025-02-28") == pytest.approx(bonferroni_t(42)) and bonferroni_t(42) > 3.0
    (tmp_path / "b").mkdir()
    assert S.bar_for(registered(tmp_path / "b"), "2023-07-01", "2025-02-28") == 3.0


def test_nothing_is_judged_unregistered_with_other_code_on_a_partial_archive_or_out_of_order(tmp_path):
    t0, n, spot, perp = market(coins=2, end="2023-09-01")
    fetch, coins = archive(spot, perp, broken="-1h-2023-08")
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": coins}))
    no = lambda u: pytest.fail("fetched")  # noqa: E731
    o = tmp_path / "o"
    with pytest.raises(SystemExit, match="not registered"):
        S.run("dev", tmp_path / "d", NOW, fetch=no, reg=Registry(tmp_path / "r.jsonl"), out_dir=o, probe_file=probe)
    (tmp_path / "x").mkdir()
    with pytest.raises(SystemExit, match="differs"):
        S.run("dev", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "x", code="0" * 64), out_dir=o, probe_file=probe)
    (tmp_path / "y").mkdir()
    with pytest.raises(SystemExit, match="partial"):
        S.run("dev", tmp_path / "d", NOW, fetch=fetch, reg=registered(tmp_path / "y"), out_dir=tmp_path / "y", probe_file=probe)
    (tmp_path / "z").mkdir()
    with pytest.raises(SystemExit, match="only after SPL-1 passed"):
        S.run("validation", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "z", "validation"), out_dir=o,
              probe_file=probe)
    (tmp_path / "w").mkdir()
    reg = registered(tmp_path / "w", "forward", passed=("SPL-1", "SPL-1-V"))
    with pytest.raises(SystemExit, match="on or after"):
        S.run("forward", tmp_path / "d", NOW, fetch=no, reg=reg, out_dir=o, probe_file=probe)
