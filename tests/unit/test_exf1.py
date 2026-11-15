"""EXF-1 on markets built so that the answer is known: a premium that passes the funding on in full leaves nothing
to earn; one that ignores it pays the receiving side; a trend that pays at every hour is not a settlement effect."""

from __future__ import annotations

import csv
import io
import json
import random
import zipfile
from datetime import date, datetime, timedelta, timezone

import pytest

import scripts.exf1 as E
from aitrader.research.events import exfunding as X
from aitrader.research.registry import Registry, Trial, Use, Verdict

NOW = datetime(2026, 11, 15, 20, 0, tzinfo=timezone.utc)
H8 = 8 * X.HOUR
C = 0.0010


def _t(d: str) -> int:
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)


def market(days: int, F=0.003, beta: float = 0.0, start: str = "2021-01-01", noise: float = 0.0002, drift: float = 0.0,
           seed: int = 1):
    """One contract: settlements every 8 hours paying F (a number, or a function of the settlement's number), a
    random-walk index, and a premium that jumps by beta * F at each settlement and drifts back over the interval."""
    rng = random.Random(seed)
    t0 = _t(start) - X.HOUR * 24
    n = (days + 2) * 288
    fs = {}
    settle = []
    for k in range(-3, days * 3 + 3):
        T = _t(start) + k * H8
        f = F(k) if callable(F) else F
        fs[T] = f
        settle.append((T, f))
    perp, index, lvl = {}, {}, 100.0
    for i in range(n):
        o = t0 + i * X.M5
        end = o + X.M5
        lvl *= 1 + drift + rng.gauss(0, noise)
        e1 = end - 1  # a bar's close is the last price before its end: a settlement at its end is not in it yet
        last = e1 - (e1 - _t(start)) % H8 if e1 >= _t(start) else _t(start) - H8
        f = fs.get(last, F if not callable(F) else 0.0)
        u = (end - last) / H8
        prem = beta * f * (1 - u)
        index[o] = (lvl, 0.0)
        perp[o] = (lvl * (1 + prem), 1e6)
    return settle, perp, index


def evs_of(days=420, **kw):
    """Two contracts built alike (an edge on one contract alone cannot pass the gate that removes the best one)."""
    out = []
    for k, sym in enumerate(("AAAUSDT", "BBBUSDT")):
        s, p, i = market(days, seed=1 + k, **kw)
        out += X.events(sym, s, p, i, _t("2021-01-01"), _t("2021-01-01") + days * 86_400_000 - 1)
    return out


def judged(evs, theta=0.002, cost=C):
    return X.judge(X.trades(evs, theta, cost, 1e5), 3.0, cost, min_events=300, min_weeks=52, placebos=200)


def bucket(m, lo=0.002):
    return next(b for b in m["buckets"] if b["abs_F_from"] == lo)


def test_a_payment_passed_on_in_full_leaves_nothing_to_earn():
    r = judged(evs_of(beta=1.0))
    assert r["verdict"] == "FAILED" and r["mean"] < 0 and not r["gates"]["t"]
    assert abs(bucket(X.mechanism(evs_of(days=60, beta=1.0)))["pass_through"] - 1.0) < 0.05  # fully priced


def test_a_payment_the_market_ignores_is_earned_by_the_receiving_side_and_nowhere_else():
    r = judged(evs_of(F=0.0045, beta=0.0))  # 45 bp received against 20 bp of fills: it survives costs doubled
    assert r["verdict"] == "PASSED", r.get("gates")
    assert abs(r["mean"] - (0.0045 - 2 * C)) < 0.0002 and r["placebo_p95"] < 0
    assert abs(bucket(X.mechanism(evs_of(days=60, beta=0.0)))["pass_through"]) < 0.05
    assert not judged(evs_of(beta=0.0))["gates"]["costs_x2"]  # 30 bp does not: 30 - 40 < 0


def test_the_pass_through_is_measured_where_it_lies_between():
    b = bucket(X.mechanism(evs_of(days=60, beta=0.5)))
    assert 0.4 < b["pass_through"] < 0.55 and b["post"] > b["pre"]


def test_when_shorts_pay_the_long_receives():
    ts = X.trades(evs_of(days=30, F=-0.003, beta=0.0), 0.002, C, 1e5)
    assert ts and all(x["side"] == 1 for x in ts) and sum(x["net"] for x in ts) / len(ts) > 0.0009


def test_the_side_is_chosen_by_the_previous_rate_and_pays_the_actual_one():
    F = lambda k: 0.003 if k % 2 == 0 else -0.003  # the sign flips every settlement: the prediction is always wrong
    ts = X.trades(evs_of(days=30, F=F, beta=0.0), 0.002, C, 1e5)
    assert ts and all(x["funding"] < 0 for x in ts) and all(x["net"] < 0 for x in ts)  # it pays what is paid


def test_a_settlement_too_thin_to_trade_is_not_traded():
    evs = evs_of(days=10, beta=0.0)
    thin = [{**e, "qv": 10.0} if k == 7 and e.get("complete") else e for k, e in enumerate(evs)]
    assert len(X.trades(thin, 0.002, C, 1e5)) == len(X.trades(evs, 0.002, C, 1e5)) - 1


def test_a_trend_that_pays_at_every_hour_is_not_a_settlement_effect():
    r = judged(evs_of(beta=1.0, drift=-0.00002, noise=0.0001), cost=0.0)  # the price falls all day: a short always earns
    assert r["mean"] > 0 and not r["gates"]["beats_placebo"] and r["verdict"] == "FAILED"


def test_too_few_trades_or_weeks_is_inconclusive_never_a_pass():
    assert judged(evs_of(days=40, beta=0.0))["verdict"] == "INCONCLUSIVE"


def test_a_missing_bar_marks_the_settlement_incomplete_and_a_stale_prediction_is_none():
    s, p, i = market(3)
    T = s[5][0]
    del p[T - 2 * X.M5]  # the bar ending at T-5m
    ev = {e["T"]: e for e in X.events("A", s, p, i, _t("2021-01-01"), _t("2021-01-04"))}
    assert ev[T].get("incomplete") and "r" not in ev[T]
    gap = [s[0], (s[0][0] + 10 * X.HOUR, 0.01)]
    assert X.events("A", gap, p, i, 0, 10**14)[0].get("no_prediction")


def test_nothing_after_the_exit_or_the_actual_rate_decides_what_is_traded():
    s, p, i = market(5)
    a, b = _t("2021-01-01"), _t("2021-01-05")
    base = X.events("A", s, p, i, a, b)
    late = {o: ((v[0] * 3, v[1]) if any(0 < o - (e["T"] + X.M5) < X.HOUR for e in base) else v) for o, v in p.items()}
    again = X.events("A", s, late, i, a, b)
    assert [round(e.get("r", 0), 12) for e in base] == [round(e.get("r", 0), 12) for e in again]
    keep = [(t, f) if k < 4 else (t, 0.05) for k, (t, f) in enumerate(s)]  # change only the actual rates after #4
    ts1 = {x["T"]: x["side"] for x in X.trades(X.events("A", s, p, i, a, b), 0.002, C, 1e5)}
    ts2 = {x["T"]: x["side"] for x in X.trades(X.events("A", keep, p, i, a, b), 0.002, C, 1e5)}
    assert ts1[s[4][0]] == ts2[s[4][0]]  # settlement #4 is chosen on #3's rate, which did not change


def test_files_are_read_as_published():
    rs = [["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume"],
          ["1609459200000000", "1", "1", "1", "2.5", "0", "0", "123"], ["bad", "x"]]
    assert X.parse_bars(rs) == {1609459200000: (2.5, 123.0)}
    fr = [["calc_time", "funding_interval_hours", "last_funding_rate"], ["1609459200004", "8", "0.0001"],
          ["1609488000000", "8", "-0.0003"]]
    assert X.parse_settlements(fr) == [(1609459200000, 0.0001), (1609488000000, -0.0003)]
    assert X.placebo_times(_t("2021-01-01"), H8) == [_t("2021-01-01") - k * 2 * X.HOUR for k in (1, 2, 3)]


def test_every_stage_can_reach_its_own_minimum_and_follows_the_one_before():
    names = list(E.SPEC["stages"])
    for k, name in enumerate(names):
        st = E.SPEC["stages"][name]
        a, b = (date.fromisoformat(x) for x in st["settlements"])
        assert ((b - a).days + 1) // 7 >= st["min_weeks"], name  # NEWL-1-F could not have reached its own
        assert st.get("after") == (E.SPEC["stages"][names[k - 1]]["trial"] if k else None)
    assert E.SPEC["bar_floor"] >= 3.0 and E.url("cm", "index", "BTCUSD_PERP", "2021-01").endswith("BTCUSD/5m/BTCUSD-5m-2021-01.zip")


def _zip(rows_):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        s = io.StringIO()
        csv.writer(s).writerows(rows_)
        z.writestr("f.csv", s.getvalue())
    return b.getvalue()


def archive(settle, perp, index, sym="AAAUSDT", broken=None):
    by = {}
    for t, f in settle:
        by.setdefault(("fundingRate", E._month_of(t)), []).append([str(t), "8", str(f)])
    for kind, bars in (("klines", perp), ("index", index)):
        for o, (c, q) in bars.items():
            by.setdefault((kind, E._month_of(o)), []).append([str(o), str(c), str(c), str(c), str(c), "0", "0", str(q)])
    urls = {E.url("um", k, sym, m): _zip(v) for (k, m), v in by.items()}

    def fetch(u):
        if broken and broken in u:
            raise RuntimeError("timed out")
        return urls.get(u)
    return fetch, {sym: {"funding": sorted({m for k, m in by if k == "fundingRate"}),
                         "klines": sorted({m for k, m in by if k == "klines"}),
                         "index": sorted({m for k, m in by if k == "index"})}}


def registered(tmp_path, stage="dev", code=None, passed=()):
    reg = Registry(tmp_path / "registry.jsonl")
    for name in list(E.SPEC["stages"])[: list(E.SPEC["stages"]).index(stage) + 1]:
        st = E.SPEC["stages"][name]
        a, b = st["settlements"]
        reg.register(Trial(id=st["trial"], registered=NOW - timedelta(hours=1), title="t", hypothesis="h",
                           uses=(Use(E.UNIVERSES[st["venue"]], date.fromisoformat(a), date.fromisoformat(b) + timedelta(days=1), "judge"),),
                           tests=st["tests"], configurations=st["tests"], preregistration=E.DOC,
                           design={"code_sha256": code or E.code_hash(), "spec_sha256": E.spec_sha(), "stage": name}))
        if st["trial"] in passed:
            reg.record_verdict(Verdict(st["trial"], NOW, "PASSED", {}))
    return reg


def test_a_stage_is_judged_once_on_its_own_window_and_recorded(tmp_path):
    fa, ca = archive(*market(400, F=0.0045, beta=0.0, seed=1), sym="AAAUSDT")
    fb, cb = archive(*market(400, F=0.0045, beta=0.0, seed=2), sym="BBBUSDT")
    fetch, cons = (lambda u: fa(u) or fb(u)), {**ca, **cb}
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"um": cons, "cm": {}}))
    reg = registered(tmp_path)
    body = E.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)
    assert body["verdict"] == "PASSED" and body["chosen_threshold"] in (0.0005, 0.001, 0.002) and body["bar"] == 3.0
    assert reg.status_of("EXF-1") == "PASSED" and (tmp_path / "data" / "EXF-1-events.json.gz").exists()
    assert body["results"]["0.005"]["verdict"] == "INCONCLUSIVE"  # no prediction reaches it
    with pytest.raises(SystemExit, match="judged once"):
        E.run("dev", tmp_path / "data", NOW, fetch=fetch, reg=reg, out_dir=tmp_path, probe_file=probe)


def test_nothing_is_judged_unregistered_with_other_code_on_a_partial_archive_or_out_of_order(tmp_path):
    s, p, i = market(60, beta=0.0)
    fetch, cons = archive(s, p, i, broken="-5m-2021-01")
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"um": cons, "cm": {}}))
    no = lambda u: pytest.fail("fetched")
    with pytest.raises(SystemExit, match="not registered"):
        E.run("dev", tmp_path / "d", NOW, fetch=no, reg=Registry(tmp_path / "r.jsonl"), probe_file=probe)
    (tmp_path / "x").mkdir()
    with pytest.raises(SystemExit, match="differs"):
        E.run("dev", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "x", code="0" * 64), probe_file=probe)
    (tmp_path / "y").mkdir()
    with pytest.raises(SystemExit, match="partial"):
        E.run("dev", tmp_path / "d", NOW, fetch=fetch, reg=registered(tmp_path / "y"), out_dir=tmp_path / "y", probe_file=probe)
    (tmp_path / "z").mkdir()
    with pytest.raises(SystemExit, match="only after EXF-1 passed"):
        E.run("validation", tmp_path / "d", NOW, fetch=no, reg=registered(tmp_path / "z", "validation"), probe_file=probe)
    (tmp_path / "w").mkdir()
    reg = registered(tmp_path / "w", "forward", passed=("EXF-1", "EXF-1-V", "EXF-1-H", "EXF-1-R"))
    with pytest.raises(SystemExit, match="on or after"):
        E.run("forward", tmp_path / "d", NOW, fetch=no, reg=reg, probe_file=probe)


def test_a_stage_reads_no_bar_after_its_last_day():
    s, p, i = market(10, beta=0.0, start="2023-12-25")
    need = E.plan({"A": s}, *E.horizon("dev"), 0.0005)
    assert need["A"] and max(need["A"]) == "2023-12"
    later = [x for x in X.events("A", s, p, i, *E.horizon("dev")) if x["T"] > E.horizon("dev")[1]]
    assert later == []
