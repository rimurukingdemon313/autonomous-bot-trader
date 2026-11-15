"""NEWL-1 (aitrader/research/events/listings.py, scripts/newl1.py) on markets built so the answer is known. Built
prices test the software only: they are never evidence about any market."""

from __future__ import annotations

import csv
import io
import json
import math
import random
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.newl1 as N
from aitrader.research.events import listings as L
from aitrader.research.registry import Registry, Trial, Use

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


# ── what is a listing ───────────────────────────────────────────────────────

def test_the_coin_behind_a_contract():
    assert L.base_of("BTCUSDT") == "BTC" and L.base_of("1000PEPEUSDT") == "PEPE" and L.base_of("1000000MOGUSDT") == "MOG"
    assert L.base_of("1MBABYDOGEUSDT") == "BABYDOGE" and L.base_of("ETHUSDC") == "ETH" and L.base_of("SOLBUSD") == "SOL"
    assert L.base_of("BTCUSDT_230331") is None and L.base_of("BTCEUR") is None and L.base_of("USDT") is None


def test_only_the_first_contract_on_a_coin_is_a_listing():
    c = L.classify({"BTCUSDT": "2019-09", "BTCBUSD": "2022-01", "1000SHIBUSDT": "2021-05", "SHIBUSDC": "2024-01",
                    "BTCDOMUSDT": "2021-06", "USDCUSDT": "2022-03", "ETHUSDT_230630": "2023-01", "PEPEUSDT": "2023-05",
                    "1000PEPEUSDT": "2023-05"})
    assert c["eligible"] == {"BTCUSDT": "2019-09", "1000SHIBUSDT": "2021-05", "1000PEPEUSDT": "2023-05"}
    assert "already had a contract (BTCUSDT)" in c["excluded"]["BTCBUSD"] and "(1000SHIBUSDT)" in c["excluded"]["SHIBUSDC"]
    assert "index or basket" in c["excluded"]["BTCDOMUSDT"] and "dollar-pegged" in c["excluded"]["USDCUSDT"]
    assert "not a perpetual" in c["excluded"]["ETHUSDT_230630"] and "(1000PEPEUSDT)" in c["excluded"]["PEPEUSDT"]


# ── one position ────────────────────────────────────────────────────────────

def days(start, n):
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=k)).isoformat() for k in range(n)]


def test_a_short_earns_the_fall_receives_positive_funding_and_pays_two_fills():
    ds = days("2022-03-01", 40)
    closes = {d: 100.0 * (1 - 0.01 * k) for k, d in enumerate(ds)}
    funding = {d: 0.0003 for d in ds}
    s = L.leg(closes, funding, ds[1], ds[31], -1, 0.0015)
    assert s["move"] == pytest.approx(closes[ds[31]] / closes[ds[1]] - 1)
    expect_fund = sum(0.0003 * closes[ds[k - 1]] / closes[ds[1]] for k in range(2, 32))
    assert s["funding"] == pytest.approx(expect_fund)
    assert s["gross"] == pytest.approx(-s["move"] + expect_fund) and s["net"] == pytest.approx(s["gross"] - 0.003)
    lg = L.leg(closes, funding, ds[1], ds[31], +1, 0.0015)
    assert lg["gross"] == pytest.approx(s["move"] - expect_fund) and not s["stopped_early"]


def test_a_contract_that_stops_trading_is_closed_at_its_last_price_and_kept():
    ds = days("2022-03-01", 12)
    closes = {d: 50.0 - k for k, d in enumerate(ds)}
    s = L.leg(closes, {}, ds[1], (date.fromisoformat(ds[1]) + timedelta(days=30)).isoformat(), -1, 0.0)
    assert s["stopped_early"] and s["exit"] == ds[-1] and s["net"] == pytest.approx(1 - closes[ds[-1]] / closes[ds[1]])
    assert L.leg(closes, {}, "2021-01-01", "2021-02-01", -1, 0.0) is None


# ── a built market ──────────────────────────────────────────────────────────

def market(planted: float, seed: int = 7, every: int = 9, start="2019-09-01", end="2024-03-15"):
    """A coin listed every `every` days; a common market factor and noise of their own; coins aged 2 to 31 days drift
    by `planted` a day on top. Funding is a small constant."""
    rng = random.Random(seed)
    cal = days(start, (date.fromisoformat(end) - date.fromisoformat(start)).days + 1)
    mkt = {d: rng.gauss(0, 0.03) for d in cal}
    closes, funding, first = {}, {}, {}
    for k, born in enumerate(cal[::every]):
        s = f"C{k:03d}USDT"
        p, series = 10.0, {}
        b0 = cal.index(born)
        for i, d in enumerate(cal[b0:]):
            if i > 0:
                age = i
                drift = planted if 2 <= age <= 31 else 0.0
                p *= math.exp(mkt[d] + rng.gauss(0, 0.03) + drift)
            series[d] = p
        closes[s] = series
        funding[s] = {d: 0.0001 for d in series}
        first[s] = born[:7]
    return closes, funding, first


def stage(closes, funding, first, a="2021-01-01", b="2023-12-31", cost=0.0015):
    listed = {s: True for s in closes}
    evs = L.events(listed, closes, funding, a, b, lag=1, cost=cost)
    late = L.events(listed, closes, funding, a, b, lag=2, cost=cost)
    return L.judge(evs, late, 3.0, cost, placebos=300), evs


def test_a_planted_first_month_decline_is_found_and_passes_every_gate():
    closes, funding, first = market(planted=-0.01)
    res, evs = stage(closes, funding, first)
    assert res["hedged_events"] >= 100 and res["months"] == 36
    assert res["verdict"] == "PASSED" and all(res["gates"].values()), res.get("gates")
    assert res["mean_cohort_x"] > 0.2 and res["t"] > 3.0 and res["placebo_share_above_actual"] == 0
    # the basket is made of coins aged 181..365 days at entry, never the event itself
    e = evs[10]
    assert e["pool"] >= 3 and e["symbol"] not in []


def test_a_market_without_the_effect_does_not_pass():
    closes, funding, first = market(planted=0.0)
    res, _ = stage(closes, funding, first)
    assert res["verdict"] == "FAILED" and not res["gates"]["t"]
    assert res["mean_cohort_x"] < 0.05 and res["gross_mean_cohort_x"] - res["mean_cohort_x"] == pytest.approx(0.006, abs=1e-9)


def test_a_rise_is_found_as_a_loss_not_as_an_edge():
    closes, funding, first = market(planted=+0.01)
    res, _ = stage(closes, funding, first)
    assert res["verdict"] == "FAILED" and res["mean_cohort_x"] < -0.2


def test_an_event_without_an_entry_price_is_counted_not_dropped():
    closes, funding, first = market(planted=-0.01)
    victim = sorted(closes)[150]  # listed 2023-05: inside the stage
    born = min(closes[victim])
    del closes[victim][(date.fromisoformat(born) + timedelta(days=1)).isoformat()]
    res, evs = stage(closes, funding, first)
    hole = [e for e in evs if e["symbol"] == victim]
    assert len(hole) == 1 and hole[0]["no_entry_price"] and res["no_entry_price"] == 1 and "x" not in hole[0]
    assert res["events"] == res["no_entry_price"] + res["unhedged_events"] + res["hedged_events"]


def test_too_few_events_is_inconclusive_never_a_pass():
    closes, funding, first = market(planted=-0.01)
    res, _ = stage(closes, funding, first, a="2023-06-01", b="2023-12-31")
    assert res["verdict"] == "INCONCLUSIVE" and "needed" in res["why"] and "gates" not in res


def test_newey_west_t():
    xs = [0.1, -0.05, 0.2, 0.0, 0.15, -0.1, 0.05]
    m, t0 = L.nw_t(xs, lag=0)
    n = len(xs)
    sd_pop = math.sqrt(sum((x - m) ** 2 for x in xs) / n)
    assert m == pytest.approx(sum(xs) / n) and t0 == pytest.approx(m / (sd_pop / math.sqrt(n)))
    assert L.nw_t([0.1, 0.1, 0.1])[1] is None and L.nw_t([0.2])[1] is None
    alternating = [1.0, -1.0] * 10
    assert L.nw_t([x + 0.1 for x in alternating], lag=1)[1] > L.nw_t([x + 0.1 for x in alternating], lag=0)[1]


# ── the script: the probe, the firewall, the refusals, one stage end to end ─

def test_an_s3_listing_is_read_page_by_page():
    ns = "http://s3.amazonaws.com/doc/2006-03-01/"
    page1 = (f'<ListBucketResult xmlns="{ns}"><Prefix>data/x/</Prefix><IsTruncated>true</IsTruncated>'
             f'<NextMarker>data/x/BBB/</NextMarker><CommonPrefixes><Prefix>data/x/AAA/</Prefix></CommonPrefixes>'
             f'<CommonPrefixes><Prefix>data/x/BBB/</Prefix></CommonPrefixes></ListBucketResult>').encode()
    page2 = (f'<ListBucketResult xmlns="{ns}"><Prefix>data/x/</Prefix><IsTruncated>false</IsTruncated>'
             f'<Contents><Key>data/x/f.zip</Key></Contents><CommonPrefixes><Prefix>data/x/CCC/</Prefix></CommonPrefixes>'
             f'</ListBucketResult>').encode()
    asked = []

    def fetch(url):
        asked.append(url)
        return page2 if "marker=" in url else page1
    p, k = N.listing("data/x/", fetch)
    assert p == ["data/x/AAA/", "data/x/BBB/", "data/x/CCC/"] and k == ["data/x/f.zip"]
    assert asked[1].endswith("&marker=data/x/BBB/")


def test_a_contract_named_outside_ascii_is_asked_for_by_an_encoded_address():
    asked = []

    def fetch(url):
        asked.append(url)
        url.encode("ascii")  # what the runner's HTTP client requires
        return b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>false</IsTruncated></ListBucketResult>'
    N.listing("data/futures/um/monthly/klines/\u54c8\u57fa\u7c73USDT/1d/", fetch)
    assert "%E5%93%88%E5%9F%BA%E7%B1%B3USDT/1d/" in asked[0]
    got = []
    N.fetch_stage(Path(tmp_dir()) / "d", {"\u54c8\u57fa\u7c73USDT": ["2025-06"]}, fetch=lambda u: (got.append(u.encode("ascii")), None)[1])
    assert got and all(b"%E5%93%88" in u for u in got)


def tmp_dir():
    import tempfile
    return tempfile.mkdtemp()


def test_a_stage_fetches_nothing_past_its_last_day():
    eligible = {"OLDUSDT": "2019-10", "SEASUSDT": "2020-02", "AUSDT": "2020-06", "BUSDT": "2023-11", "LATEUSDT": "2024-02"}
    want = N.needed(eligible, "dev")
    # a coin listed in 2019-10 was 181..365 days old only before the first entry of 2021: no use to this stage
    assert "LATEUSDT" not in want and "OLDUSDT" not in want and "SEASUSDT" in want
    assert max(m for ms in want.values() for m in ms) <= "2024-01" and want["BUSDT"][-1] == "2024-01"
    assert want["AUSDT"] == N._months("2020-06", "2021-08")
    v = N.needed(eligible, "validation")
    assert "LATEUSDT" in v and "OLDUSDT" not in v and max(m for ms in v.values() for m in ms) <= "2026-11"


def test_the_firewall_keeps_later_prices_out():
    s = {"X": {"2023-12-30": 1.0, "2024-01-31": 2.0, "2024-02-01": 3.0}}
    assert N.firewall(s, "2024-01-31") == {"X": {"2023-12-30": 1.0, "2024-01-31": 2.0}}


def zipped(rows):
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("f.csv", buf.getvalue())
    return out.getvalue()


def archive(closes, funding):
    """The archive's monthly files for the built market, served by URL."""
    def ms(d):
        return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)

    def fetch(url):
        part = url.rsplit("/", 1)[1].removesuffix(".zip")
        if "/klines/" in url:
            s, m = part.split("-1d-")
            rows = [[ms(d), 0, 0, 0, c, 0, 0] for d, c in sorted(closes.get(s, {}).items()) if d[:7] == m]
        else:
            s, m = part.split("-fundingRate-")
            rows = [[ms(d), 8, r] for d, r in sorted(funding.get(s, {}).items()) if d[:7] == m]
        return zipped(rows) if rows else None
    return fetch


def registered(tmp_path, stage="dev", code=None):
    reg = Registry(tmp_path / "registry.jsonl")
    st = N.SPEC["stages"][stage]
    a, b, end = N.horizon(stage)
    reg.register(Trial(id=st["trial"], registered=NOW - timedelta(hours=1), title="t", hypothesis="h",
                       uses=(Use(N.UNIVERSE, date.fromisoformat(a), date.fromisoformat(end) + timedelta(days=1), "judge"),),
                       tests=1, configurations=1, preregistration=N.DOC,
                       design={"code_sha256": code or N.code_hash(), "spec_sha256": N.spec_sha(), "stage": stage}))
    return reg


def test_a_stage_is_registered_judged_once_and_recorded(tmp_path):
    closes, funding, first = market(planted=-0.01)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"eligible": first}))
    reg = registered(tmp_path)
    body = N.run("dev", tmp_path / "data", NOW, fetch=archive(closes, funding), reg=reg, out_dir=tmp_path, probe_file=probe)
    assert body["verdict"] == "PASSED" and reg.status_of("NEWL-1") == "PASSED"
    assert body["last_day_read"] == "2024-01-31" and body["result"]["months"] == 36
    saved = json.loads((tmp_path / "NEWL-1.json").read_text())
    assert saved["spec_sha256"] == N.spec_sha() and saved["events"] and "placebo_shorts" not in saved["events"][0]
    # nothing past the stage's last day was fetched, and a second look is refused
    man = json.loads((tmp_path / "data" / "manifest.json").read_text())
    assert max(m for ms in man["have"].values() for m in ms) <= "2024-01"
    with pytest.raises(SystemExit, match="judged once"):
        N.run("dev", tmp_path / "data", NOW, fetch=archive(closes, funding), reg=reg, out_dir=tmp_path, probe_file=probe)


def test_nothing_is_fetched_or_judged_before_registration_or_with_other_code(tmp_path):
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"eligible": {"AUSDT": "2021-01"}}))
    with pytest.raises(SystemExit, match="not registered"):
        N.run("dev", tmp_path / "data", NOW, fetch=lambda u: pytest.fail("fetched"), reg=Registry(tmp_path / "r.jsonl"), probe_file=probe)
    with pytest.raises(SystemExit, match="differs from what was registered"):
        N.run("dev", tmp_path / "d2", NOW, fetch=lambda u: pytest.fail("fetched"), reg=registered(tmp_path / "x", code="0" * 64)
              if (tmp_path / "x").mkdir() is None else None, probe_file=probe)
    assert not (tmp_path / "data").exists()


def test_the_validation_stage_waits_for_the_development_stage_to_pass(tmp_path):
    reg = registered(tmp_path, "validation")
    with pytest.raises(SystemExit, match="only after NEWL-1 passed"):
        N.run("validation", tmp_path / "data", NOW, fetch=lambda u: pytest.fail("fetched"), reg=reg, probe_file=tmp_path / "p.json")


def test_a_partial_archive_is_never_judged(tmp_path):
    closes, funding, first = market(planted=-0.01)
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"eligible": first}))
    base = archive(closes, funding)

    def flaky(url):
        if "C040USDT-1d-2020-09" in url:
            raise RuntimeError("connection reset")
        return base(url)
    reg = registered(tmp_path)
    with pytest.raises(SystemExit, match="did not arrive"):
        N.run("dev", tmp_path / "data", NOW, fetch=flaky, reg=reg, out_dir=tmp_path, probe_file=probe)
    assert reg.status_of("NEWL-1") == "PENDING" and not (tmp_path / "NEWL-1.json").exists()
    N.run("dev", tmp_path / "data", NOW, fetch=base, reg=reg, out_dir=tmp_path, probe_file=probe)  # the next run completes it
    assert reg.status_of("NEWL-1") == "PASSED"


def test_the_workflow_runs_only_the_three_commands_and_pushes_records_and_data_only():
    import re
    from pathlib import Path
    wf = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "newl1.yml").read_text()
    assert "secrets." not in wf and 'COMMAND: ${{ github.event.inputs.command }}' in wf
    assert re.search(r'case "\$COMMAND" in\s*\n\s*probe\) python scripts/newl1.py probe ;;\s*\n\s*dev\|validation\) '
                     r'python scripts/newl1.py run "\$COMMAND" --data pub/data ;;\s*\n\s*\*\) echo', wf)
    pushes = re.findall(r"git push[^\n]*", wf)
    assert sorted({p.split("HEAD:")[1].split()[0] for p in pushes}) == ["refs/heads/main", "refs/heads/newl-data"]
    assert "research/results/NEWL-1-probe.json 'research/knowledge/NEWL-1*.json' research/registry.jsonl" in wf
