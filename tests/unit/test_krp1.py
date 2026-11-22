"""KRP-1 (research/preregistrations/KRP-1.md) on markets built so the answer is known: the relative premium cancels
the exchange rate; only a fresh spike is an entry; the trade starts an hour after the close and reads nothing it
could not have known; the judge passes a built edge and fails noise; a stage is refused unless registered, once,
with its code; every stage can reach its minimum; the probe reads names only."""

import copy
import json
import math
from datetime import date, datetime, timedelta, timezone

import pytest

from aitrader.research.events import korea as K
from aitrader.research.registry import Registry, Trial, Use
from scripts import krp1 as S

FX = 1400.0
T0 = "2024-01-01"
DAYS = 130
SPIKE = "2024-03-01"  # 60 days after T0: a month of ordinary days before it


def _panel(spike_rho: float = 0.08, rise: float = 0.03, persistent: bool = False, coin_turnover: float = 1e10,
           first_upbit: str = "2023-11-01") -> K.Panel:
    t0 = K.ms_of(T0)
    p = K.Panel(["AAA", "BBB"], t0, DAYS * 24)
    t_in = K.ms_of(SPIKE) + K.DAY  # the bar opening at 00:00 the next day closes at 01:00: the entry
    t_out = t_in + 24 * K.HOUR
    for c, base in (("AAA", 10.0), ("BBB", 2.0), ("BTC", 50_000.0)):
        bars = {}
        for i in range(DAYS * 24):
            t = t0 + i * K.HOUR
            px = base
            if c == "AAA" and t_in < t <= t_out:  # AAA rises against bitcoin after the entry, inside the trade
                px = base * (1 + rise)
            if c == "AAA" and t > t_out:
                px = base * (1 + rise)
            bars[t] = (px, 100_000.0)
        p.put_hourly(c, bars)
        p.first_binance[c] = K.ms_of("2023-10-01")
    for c in ("AAA", "BBB", "BTC"):
        candles = {}
        for d in K.days_between(first_upbit, (date.fromisoformat(T0) + timedelta(days=DAYS - 2)).isoformat()):
            close = p.day_close(c, d) if d >= T0 else {"AAA": 10.0, "BBB": 2.0, "BTC": 50_000.0}[c]
            r = 0.0
            if c == "AAA" and (d == SPIKE or (persistent and d >= "2024-01-20")):
                r = spike_rho
            candles[d] = (close * FX * math.exp(r) * 1.25, coin_turnover)  # a 25% premium common to every coin
        p.put_upbit(c, candles)
    return p


def _days():
    return K.days_between("2024-02-05", "2024-04-30")


def test_the_relative_premium_cancels_the_exchange_rate_and_bitcoin_s_own_premium():
    a = K.relative_premium(10 * 1300 * 1.08, 50_000 * 1300 * 1.02, 10, 50_000)
    b = K.relative_premium(10 * 1500 * 1.08, 50_000 * 1500 * 1.02, 10, 50_000)
    assert abs(a - b) < 1e-12 and abs(a - math.log(1.08 / 1.02)) < 1e-12
    assert K.relative_premium(None, 1, 1, 1) is None and K.relative_premium(0, 1, 1, 1) is None


def test_a_fresh_spike_is_bought_an_hour_after_the_close_and_earns_the_rise_against_bitcoin():
    p = _panel()
    evs = K.entries(p, _days(), 0.05, +1, S.SPEC)
    assert [e["day"] for e in evs] == [SPIKE] and evs[0]["coin"] == "AAA"
    e = evs[0]
    assert abs(e["rho"] - 0.08) < 1e-9 and abs(e["excess"] - 0.03) < 1e-9
    assert abs(e["net"] - (0.03 - S.SPEC["cost_round_trip"])) < 1e-9
    # the Korean discount contrast finds nothing here, and the other coin never spiked
    assert K.entries(p, _days(), 0.05, -1, S.SPEC) == []


def test_a_persistent_gap_a_renamed_asset_and_thin_turnover_are_not_entries():
    assert K.entries(_panel(persistent=True), _days(), 0.05, +1, S.SPEC) == []  # the median stayed above theta/2
    assert K.entries(_panel(spike_rho=math.log(1000)), _days(), 0.05, +1, S.SPEC) == []  # |rho| above the cap
    assert K.entries(_panel(coin_turnover=1e8), _days(), 0.05, +1, S.SPEC) == []  # below Upbit's KRW floor
    assert K.entries(_panel(first_upbit="2024-02-20"), _days(), 0.05, +1, S.SPEC) == []  # listed under 30 days


def test_the_trade_reads_nothing_after_its_exit_and_the_signal_nothing_after_its_close():
    p = _panel()
    base = K.entries(p, _days(), 0.05, +1, S.SPEC)[0]
    q = _panel()
    t_out = K.ms_of(SPIKE) + K.DAY + 24 * K.HOUR
    later = {t: (999.0, 1.0) for t in range(t_out + K.HOUR, q.t0 + q.n * K.HOUR, K.HOUR)}
    q.put_hourly("AAA", later)
    q.put_hourly("BTC", later)
    for d in K.days_between("2024-03-02", "2024-05-01"):  # Upbit's later candles change too
        q.upbit["AAA"][d] = (1.0, 1e10)
    got = [e for e in K.entries(q, _days(), 0.05, +1, S.SPEC) if e["day"] == SPIKE][0]
    assert got == base
    # and the hour the entry is priced at is the close of 00:00-01:00 UTC: a later lag moves it, never earlier
    late = K.entries(p, _days(), 0.05, +1, S.SPEC, lag_hours=2)[0]
    assert late["day"] == SPIKE and abs(late["excess"] - 0.0) < 1e-9  # the rise was already in by 02:00


def test_one_position_per_coin_at_a_time():
    p = _panel()
    nxt = (date.fromisoformat(SPIKE) + timedelta(days=1)).isoformat()
    u, ub = p.upbit["AAA"], p.upbit["BTC"]
    u[nxt] = (p.day_close("AAA", nxt) * FX * math.exp(0.08) * 1.25, 1e10)
    s = {c: K.rho_series(p, c, K.days_with_lookback(_days(), 30)) for c in p.coins}
    spec = copy.deepcopy(S.SPEC)
    spec["hold_hours"] = 48  # a two-day hold: the next day's spike falls inside the open trade
    evs = K.entries(p, _days(), 0.05, +1, spec, series=s)
    assert [e["day"] for e in evs] == [SPIKE] and ub


def test_placebos_are_ordinary_days_inside_the_stage_window():
    p = _panel()
    s = {c: K.rho_series(p, c, K.days_with_lookback(_days(), 30)) for c in p.coins}
    evs = K.entries(p, _days(), 0.05, +1, S.SPEC, series=s)
    plac = K.placebos(p, evs, 0.05, S.SPEC, s, 7, window=("2024-02-20", "2024-03-10"))
    # 2024-02-20..28 and 2024-03-03..10: the day itself and the days either side are never placebos
    assert len(plac[("AAA", SPIKE)]) == 17
    assert all(abs(x + S.SPEC["cost_round_trip"]) < 1e-9 for x in plac[("AAA", SPIKE)])  # ordinary days: flat
    # with the window ending on the spike day, no placebo day after it is read: 28 candidates, 20 drawn
    narrow = K.placebos(p, evs, 0.05, S.SPEC, s, 7, window=("2024-02-01", SPIKE))
    assert len(narrow[("AAA", SPIKE)]) == S.SPEC["placebo_draws_per_entry"]
    tight = K.placebos(p, evs, 0.05, S.SPEC, s, 7, window=("2024-02-27", SPIKE))
    assert len(tight[("AAA", SPIKE)]) == 2  # 2024-02-27 and 2024-02-28 only


def _evs(n_days: int, per_day: int, mean: float, sd: float, seed: int = 1) -> list[dict]:
    import random
    rng, out = random.Random(seed), []
    d0 = date(2020, 1, 1)
    for i in range(n_days):
        for j in range(per_day):
            x = rng.gauss(mean, sd)
            out.append({"coin": f"C{(i * per_day + j) % 37}", "day": (d0 + timedelta(days=i)).isoformat(), "net": x,
                        "ret": x + 0.01, "excess": x + 0.006})
    return out


def _plac(evs, mean, sd, seed=2):
    import random
    rng = random.Random(seed)
    return {(e["coin"], e["day"]): [rng.gauss(mean, sd) for _ in range(10)] for e in evs}


def test_the_judge_passes_a_built_edge_fails_noise_and_calls_too_few_inconclusive():
    edge = _evs(120, 3, 0.02, 0.02)
    late = _evs(120, 3, 0.015, 0.02, seed=3)
    contra = _evs(60, 2, -0.01, 0.02, seed=4)
    r = K.judge(edge, late, contra, _plac(edge, -0.006, 0.02), 3.0, 0.006, 150, 60, 11, 300)
    assert r["verdict"] == "PASSED" and all(r["gates"].values())
    noise = _evs(120, 3, 0.0, 0.02, seed=5)
    r = K.judge(noise, noise, contra, _plac(noise, 0.0, 0.02), 3.0, 0.006, 150, 60, 11, 300)
    assert r["verdict"] == "FAILED" and not r["gates"]["t"]
    few = _evs(20, 2, 0.05, 0.01)
    assert K.judge(few, few, contra, _plac(few, 0, 0.01), 3.0, 0.006, 150, 60, 11, 300)["verdict"] == "INCONCLUSIVE"
    # an edge that the Korean discounts match is not the mechanism
    same = _evs(60, 2, 0.03, 0.02, seed=6)
    r = K.judge(edge, late, same, _plac(edge, -0.006, 0.02), 3.0, 0.006, 150, 60, 11, 300)
    assert r["verdict"] == "FAILED" and not r["gates"]["beats_korean_discounts"]


def test_upbit_pagination_asks_nothing_after_the_last_day_and_stops_at_the_first():
    asked = []

    def fetch(url):
        asked.append(url)
        to = url.split("to=")[1].replace("%3A", ":")
        end = date.fromisoformat(to[:10])
        rows = [{"candle_date_time_utc": (end - timedelta(days=k)).isoformat() + "T00:00:00", "trade_price": 1.0 + k,
                 "candle_acc_trade_price": 5.0} for k in range(1, 201)]
        return json.dumps(rows).encode()
    got = S.upbit_daily("KRW-AAA", "2024-01-01", "2024-12-31", fetch, pause=0)
    assert "to=2025-01-01T00" in asked[0]
    assert min(got) == "2024-01-01" and max(got) == "2024-12-31" and len(got) == 366
    assert len(asked) == 2


def test_upbit_without_the_market_is_absent_not_a_failure():
    def fetch(url):
        raise RuntimeError(f"{url}: HTTP Error 404: Not Found")
    assert S.upbit_daily("KRW-GONE", "2024-01-01", "2024-01-31", fetch, pause=0) is None


def _registry(tmp_path, stage="dev", code=None, spec=None):
    reg = Registry.load(tmp_path / "registry.jsonl")
    st = S.SPEC["stages"][stage]
    a, b = st["decisions"]
    reg.register(Trial(id=st["trial"], registered=datetime(2026, 11, 22, tzinfo=timezone.utc), title="t",
                       hypothesis="h", uses=(Use(S.UNIVERSE, date.fromisoformat(a), date.fromisoformat(b)
                                                 + timedelta(days=1), "judge"),),
                       tests=st["tests"], configurations=2, preregistration=S.DOC,
                       design={"code_sha256": code or S.code_hash(), "spec_sha256": spec or S.spec_sha(),
                               "stage": stage}))
    return reg


def test_a_stage_is_refused_unless_registered_with_this_code_and_judged_once(tmp_path):
    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    empty = Registry.load(tmp_path / "none.jsonl")
    with pytest.raises(SystemExit, match="not registered"):
        S.run("dev", tmp_path / "d", now, reg=empty)
    with pytest.raises(SystemExit, match="differs"):
        S.run("dev", tmp_path / "d", now, reg=_registry(tmp_path / "a", code="0" * 64))
    with pytest.raises(SystemExit, match="only after"):
        S.run("validation", tmp_path / "d", now, reg=_registry(tmp_path / "b", stage="validation"))
    reg = _registry(tmp_path / "c", stage="forward")
    with pytest.raises(SystemExit):
        S.run("forward", tmp_path / "d", now, reg=reg)


def test_every_stage_can_reach_its_minimum():
    for name, st in S.SPEC["stages"].items():
        a, b = st["decisions"]
        n = (date.fromisoformat(b) - date.fromisoformat(a)).days + 1
        assert n >= 3 * st["min_days"], name  # a third of the window's days holding an entry would be enough
        assert st["min_events"] <= st["min_days"] * 10, name


def test_the_probe_reads_names_and_file_names_only():
    asked = []
    listing = ("<ListBucketResult xmlns='http://s3.amazonaws.com/doc/2006-03-01/'><Prefix>{p}</Prefix>"
               "<IsTruncated>false</IsTruncated>{keys}</ListBucketResult>")

    def fetch(url):
        asked.append(url)
        if "market/all" in url:
            return json.dumps([{"market": "KRW-AAA"}, {"market": "KRW-USDT"}, {"market": "BTC-AAA"},
                               {"market": "KRW-BTC"}]).encode()
        sym = "AAAUSDT" if "AAAUSDT" in url else "BTCUSDT" if "BTCUSDT" in url else None
        keys = "".join(f"<Contents><Key>data/spot/monthly/klines/{sym}/1h/{sym}-1h-2024-0{m}.zip</Key></Contents>"
                       for m in (1, 2)) if sym else ""
        return listing.format(p="x", keys=keys).encode()
    body = S.probe(fetch, datetime(2026, 11, 22, tzinfo=timezone.utc))
    assert set(body["coins"]) == {"AAA"} and body["coins"]["AAA"]["binance_1h"] == ["2024-01", "2024-02"]
    assert body["btc_1h"] == ["2024-01", "2024-02"]
    assert not any("candles" in u or "/klines/" in u and u.endswith(".zip") for u in asked)


def test_a_judged_stage_is_not_judged_again_and_a_partial_fetch_judges_nothing(tmp_path):
    from aitrader.research.registry import Verdict
    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    reg = _registry(tmp_path / "v")
    reg.record_verdict(Verdict("KRP-1", now, "FAILED", {}))
    with pytest.raises(SystemExit, match="already has a verdict"):
        S.run("dev", tmp_path / "d", now, reg=reg)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"coins": {"AAA": {"binance_1h": ["2018-01"], "upbit_listed_now": True}},
                                 "btc_1h": ["2018-01"]}))

    def up(url):  # Upbit answers, bitcoin included: only Binance's archive fails
        return json.dumps([{"candle_date_time_utc": "2018-01-05T00:00:00", "trade_price": 1.0,
                            "candle_acc_trade_price": 1e10}]).encode()

    def bn(url):
        raise RuntimeError(f"{url}: timed out")
    with pytest.raises(SystemExit, match="archive files"):
        S.run("dev", tmp_path / "d", now, fetch_up=up, fetch_bn=bn, reg=_registry(tmp_path / "p"),
              out_dir=tmp_path / "k", probe_file=probe)
    assert not (tmp_path / "k").exists()  # nothing was written, nothing judged
