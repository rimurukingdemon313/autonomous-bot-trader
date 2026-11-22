"""SCX-1 (research/preregistrations/SCX-1.md) on markets built so the answer is known: the swap goes into the cheap
side, is decided at Sunday's 22:00 close and closed at Monday's 21:00 close; a weekend reversion that other hours do
not share passes every gate, and the same reversion on Wednesdays fails the mechanism's gate; nothing after the last
exit is read; a stage is refused unless registered, once, with its code; every stage can reach its minimum; the
probe reads file names only."""

import json
import math
from datetime import date, datetime, timedelta, timezone

import pytest

from aitrader.research.events import stablecoin as C
from aitrader.research.registry import Registry, Trial, Use
from scripts import scx1 as S

H = C.HOUR


def test_the_weekdays_and_the_swap_into_the_cheap_side():
    assert C.weekdays_in("2024-01-01", "2024-01-14", 6) == ["2024-01-07", "2024-01-14"]
    t = C.ms_of("2024-01-07") + 22 * H
    cheap = {t - H: 0.9990, t + 22 * H: 1.0}
    e = C.trade("USDCUSDT", cheap, t, 23, 0.0003, 0.0002)
    assert abs(e["gross"] - math.log(1 / 0.9990)) < 1e-12 and abs(e["net"] - (e["gross"] - 0.0002)) < 1e-12
    dear = {t - H: 1.0010, t + 22 * H: 1.0}
    e = C.trade("USDCUSDT", dear, t, 23, 0.0003, 0.0002)
    assert abs(e["gross"] - math.log(1.0010)) < 1e-12  # sold the dear coin from stock, bought it back at par
    assert C.trade("USDCUSDT", {t - H: 0.9999, t + 22 * H: 1.0}, t, 23, 0.0003, 0.0002) is None  # within theta
    assert C.trade("USDCUSDT", {t - H: 0.999}, t, 23, 0.0003, 0.0002)["missing"] is True  # no exit: not filled


def _market(weeks: int = 70, sunday_dev: float = -0.0008, wednesday_reverts: bool = False) -> dict[str, dict[int, float]]:
    """Two pairs at par, except: Sunday 21:00-22:00 at sunday_dev, back to par from 22:00; and from Wednesday 21:00
    a deviation of the same size held 60 hours (or one hour, if wednesday_reverts), then back to par."""
    t0 = C.ms_of("2021-01-03")  # a Sunday
    out = {}
    for pair in ("USDCUSDT", "TUSDUSDT"):
        b = {t0 + i * H: 1.0 for i in range(-30 * 24, weeks * 7 * 24 + 7 * 24)}
        for w in range(weeks):
            sun = t0 + w * 7 * C.DAY
            dev = sunday_dev * (1 + 0.25 * math.sin(w))  # sizes vary from week to week, so a t can be measured
            b[sun + 21 * H] = math.exp(dev)
            wed = sun + 3 * C.DAY + 21 * H
            for k in range(1 if wednesday_reverts else 60):
                b[wed + k * H] = math.exp(dev)
        out[pair] = b
    return out


def _hold_an_hour_longer(bars, wednesdays=False):
    for b in bars.values():
        for w in range(70):
            t = C.ms_of("2021-01-03") + w * 7 * C.DAY
            b[t + 22 * H] = b[t + 21 * H]
            if wednesdays:
                b[t + 3 * C.DAY + 22 * H] = b[t + 3 * C.DAY + 21 * H]
    return bars


def _run(bars, theta=0.0003, weeks=70):
    sundays = C.weekdays_in("2021-01-03", (date(2021, 1, 3) + timedelta(weeks=weeks - 1)).isoformat(), 6)
    wednesdays = C.weekdays_in("2021-01-03", (date(2021, 1, 3) + timedelta(weeks=weeks - 1)).isoformat(), 2)
    evs = C.entries(bars, sundays, 22, 23, theta, 0.0002)
    late = C.entries(bars, sundays, 22, 23, theta, 0.0002, lag_hours=1)
    contra = C.entries(bars, wednesdays, 22, 23, theta, 0.0002)
    window = (C.ms_of("2020-12-20"), C.ms_of(sundays[-1]) + 46 * H)
    plac = C.placebos(bars, evs, 23, theta, 0.0002, 14, 20, 7, window)
    return evs, late, contra, plac, C.judge(evs, late, contra, plac, 3.0, 0.0002, 40, 40, 7, 300)


def test_a_weekend_reversion_other_hours_do_not_share_passes_every_gate():
    evs, late, contra, plac, r = _run(_market())
    assert len(evs) == 140 and all(0.0005 < e["gross"] < 0.0011 for e in evs)
    # the late entry finds the pair already at par: nothing to do, so it is not an entry, and the gate needs one
    assert late == []
    assert r["verdict"] == "FAILED" and not r["gates"]["late_entry"]
    # with the deviation lasting into the next hour, the late entry is taken too, and every gate holds
    evs, late, contra, plac, r = _run(_hold_an_hour_longer(_market()))
    assert r["verdict"] == "PASSED" and all(r["gates"].values()), r["gates"]
    assert r["weekday_mean_net"] < r["mean_net"] and r["placebo_p95"] < r["mean_net"]


def test_a_reversion_the_wednesdays_share_is_not_the_weekend_mechanism():
    evs, late, contra, plac, r = _run(_hold_an_hour_longer(_market(wednesday_reverts=True), wednesdays=True))
    assert not r["gates"]["beats_weekdays"] and r["verdict"] == "FAILED"


def test_too_few_weeks_is_inconclusive_never_a_pass():
    evs, late, contra, plac, r = _run(_market(weeks=10), weeks=10)
    assert r["verdict"] == "INCONCLUSIVE"


def test_the_firewall_drops_every_bar_that_closes_after_the_last_exit():
    last = C.ms_of("2024-01-08") + 21 * H
    bars = {"USDCUSDT": {last - 2 * H: 1.0, last - H: 1.0, last: 0.5, last + H: 0.5}}
    got = S.firewall(bars, last)["USDCUSDT"]
    assert set(got) == {last - 2 * H, last - H}


def _registry(tmp_path, stage="dev", code=None):
    reg = Registry.load(tmp_path / "registry.jsonl")
    st = S.SPEC["stages"][stage]
    a, b = st["decisions"]
    reg.register(Trial(id=st["trial"], registered=datetime(2026, 11, 22, tzinfo=timezone.utc), title="t",
                       hypothesis="h", uses=(Use(S.UNIVERSE, date.fromisoformat(a), date.fromisoformat(b)
                                                 + timedelta(days=2), "judge"),),
                       tests=st["tests"], configurations=2, preregistration=S.DOC,
                       design={"code_sha256": code or S.code_hash(), "spec_sha256": S.spec_sha(), "stage": stage}))
    return reg


def test_a_stage_is_refused_unless_registered_with_this_code_and_judged_once(tmp_path):
    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    with pytest.raises(SystemExit, match="not registered"):
        S.run("dev", tmp_path / "d", now, reg=Registry.load(tmp_path / "none.jsonl"))
    with pytest.raises(SystemExit, match="differs"):
        S.run("dev", tmp_path / "d", now, reg=_registry(tmp_path / "a", code="0" * 64))
    with pytest.raises(SystemExit, match="only after"):
        S.run("validation", tmp_path / "d", now, reg=_registry(tmp_path / "b", stage="validation"))


def test_every_stage_can_reach_its_minimum():
    for name, st in S.SPEC["stages"].items():
        a, b = st["decisions"]
        n = len(C.weekdays_in(a, b, 6))
        assert n >= int(1.5 * st["min_weeks"]), name
        assert date.fromisoformat(a).weekday() == 6 and date.fromisoformat(b).weekday() == 6, name


def test_the_probe_reads_file_names_only():
    asked = []
    listing = ("<ListBucketResult xmlns='http://s3.amazonaws.com/doc/2006-03-01/'><Prefix>x</Prefix>"
               "<IsTruncated>false</IsTruncated>{keys}</ListBucketResult>")

    def fetch(url):
        asked.append(url)
        sym = next((p for p in C.PAIRS if p in url), None)
        keys = "".join(f"<Contents><Key>data/spot/monthly/klines/{sym}/1h/{sym}-1h-2024-0{m}.zip</Key></Contents>"
                       for m in (1, 2)) if sym == "USDCUSDT" else ""
        return listing.format(keys=keys).encode()
    body = S.probe(fetch, datetime(2026, 11, 22, tzinfo=timezone.utc))
    assert body["pairs"]["USDCUSDT"] == ["2024-01", "2024-02"] and body["pairs"]["TUSDUSDT"] == []
    assert all(".zip" not in u for u in asked)
    assert json.dumps(body)


def test_a_judged_stage_is_not_judged_again_and_a_partial_fetch_judges_nothing(tmp_path):
    from aitrader.research.registry import Verdict
    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    reg = _registry(tmp_path / "v")
    reg.record_verdict(Verdict("SCX-1", now, "FAILED", {}))
    with pytest.raises(SystemExit, match="already has a verdict"):
        S.run("dev", tmp_path / "d", now, reg=reg)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"pairs": {"USDCUSDT": ["2019-01"]}}))

    def bn(url):
        raise RuntimeError(f"{url}: timed out")
    with pytest.raises(SystemExit, match="did not arrive"):
        S.run("dev", tmp_path / "d", now, fetch=bn, reg=_registry(tmp_path / "p"), out_dir=tmp_path / "k",
              probe_file=probe)
    assert not (tmp_path / "k").exists()


def test_placebo_hours_stay_inside_the_stage_s_hours():
    bars = _hold_an_hour_longer(_market())
    sundays = C.weekdays_in("2021-01-03", "2022-05-01", 6)
    evs = C.entries(bars, sundays, 22, 23, 0.0003, 0.0002)
    wide = C.placebos(bars, evs, 23, 0.0003, 0.0002, 14, 1000, 7, (C.ms_of("2020-12-01"), C.ms_of("2022-06-01")))
    e = evs[20]  # a Sunday with deviations in the fortnight before it: a window starting on it excludes them
    narrow = C.placebos(bars, [e], 23, 0.0003, 0.0002, 14, 1000, 7, (e["t"], C.ms_of("2022-06-01")))
    assert len(narrow[(e["pair"], e["day"])]) < len(wide[(e["pair"], e["day"])])
