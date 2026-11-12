"""The lab's memory, its priorities and its feeds. The queue never runs a task twice and recovers from a run that
died; the allocation follows the record and still explores; a feed fills nothing in, refuses a file that fails its
checksum, and fetches only what it does not hold. Canned samples only: no test touches the network."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import date, datetime, timedelta, timezone

import pytest

from aitrader.research.dlab import brain as B
from aitrader.research.dlab import feeds as F
from aitrader.research.dlab import store as S

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc)


# ── the queue ───────────────────────────────────────────────────────────────

def test_a_task_is_queued_once_and_a_finished_task_never_runs_again(tmp_path):
    st = S.Store(tmp_path)
    assert S.enqueue(st, "scan:a", "scan", {"run": "R-1"}, 2.0, NOW)
    assert not S.enqueue(st, "scan:a", "scan", {"run": "R-2"}, 9.0, NOW)  # the same id: not queued again
    assert S.tasks(st)["scan:a"]["args"] == {"run": "R-1"} and [t["task"] for t in S.runnable(st, NOW)] == ["scan:a"]
    S.mark(st, "scan:a", "STARTED", NOW)
    assert S.runnable(st, NOW) == []  # running now, on this or another machine
    S.mark(st, "scan:a", "DONE", NOW, {"verdict": "FAILED"})
    t = S.tasks(st)["scan:a"]
    assert t["status"] == "DONE" and t["result"] == {"verdict": "FAILED"} and t["attempts"] == 1
    assert S.runnable(st, NOW + timedelta(days=30)) == [] and not S.enqueue(st, "scan:a", "scan", {}, 1.0, NOW)
    with pytest.raises(ValueError):
        S.mark(st, "scan:a", "QUEUED", NOW)
    with pytest.raises(ValueError):
        st.path("nonsense")


def test_a_run_that_died_is_taken_up_again_and_a_task_that_keeps_failing_is_reported(tmp_path):
    st = S.Store(tmp_path)
    S.enqueue(st, "data:x", "data", {}, 4.0, NOW)
    S.mark(st, "data:x", "STARTED", NOW)
    assert S.runnable(st, NOW + timedelta(hours=S.STALE_HOURS - 1)) == []  # it may still be running
    late = NOW + timedelta(hours=S.STALE_HOURS)
    assert [t["task"] for t in S.runnable(st, late)] == ["data:x"]  # its machine is gone: nothing was marked after it
    S.mark(st, "data:x", "STARTED", late)
    S.mark(st, "data:x", "FAILED", late, {"error": "timeout"})
    assert [t["task"] for t in S.runnable(st, late)] == ["data:x"] and S.abandoned(st) == []  # attempts 2 of 3
    S.mark(st, "data:x", "STARTED", late)
    S.mark(st, "data:x", "FAILED", late, {"error": "timeout"})
    assert S.runnable(st, late + timedelta(days=9)) == []  # three attempts: no more
    lost = S.abandoned(st)
    assert [t["task"] for t in lost] == ["data:x"] and lost[0]["attempts"] == S.MAX_ATTEMPTS and lost[0]["result"] == {"error": "timeout"}
    # the memory is a file of lines: a restart reads the same state back
    assert S.tasks(S.Store(tmp_path)) == S.tasks(st)
    assert all(json.loads(x) for x in (tmp_path / "queue.jsonl").read_text().splitlines())


def test_the_queue_is_ordered_by_priority_and_priorities_can_change(tmp_path):
    st = S.Store(tmp_path)
    for name, p in (("a", 1.0), ("b", 3.0), ("c", 2.0), ("d", 2.0)):
        S.enqueue(st, name, "scan", {}, p, NOW)
    assert [t["task"] for t in S.runnable(st, NOW)] == ["b", "c", "d", "a"]
    S.mark(st, "b", "STARTED", NOW)
    S.mark(st, "b", "DONE", NOW)
    n = len(st.read("queue"))
    S.reprioritize(st, {"a": 5.0, "b": 9.0, "c": 2.0, "zzz": 7.0}, NOW)  # b is done, c is unchanged, zzz is unknown
    assert len(st.read("queue")) == n + 1 and [t["task"] for t in S.runnable(st, NOW)] == ["a", "c", "d"]
    assert S.tasks(st)["a"]["status"] == "QUEUED"  # a change of priority is not a change of state


def test_sources_and_hypotheses_can_be_searched(tmp_path):
    st = S.Store(tmp_path)
    st.append("sources", [{"id": "arxiv:1", "title": "Transfer Entropy in Crypto Markets", "status": "UNREAD"},
                          {"id": "arxiv:2", "title": "Momentum crashes", "status": "UNREAD"}])
    st.append("hypotheses", [{"id": "h1", "parents": ["arxiv:1"], "idea": "entropy of funding leads returns"}])
    hits = st.search("entropy crypto")
    assert [h["id"] for h in hits] == ["arxiv:1"] and hits[0]["table"] == "sources"
    assert {h["id"] for h in st.search("ENTROPY")} == {"arxiv:1", "h1"} and st.search("nothing here") == []
    assert st.append("sources", []) == 0


# ── what the record teaches ─────────────────────────────────────────────────

def rule(run, i, family, cls, reason=""):
    return {"run": run, "id": f"{run}-{i}", "family": family, "class": cls, "reason": reason}


LEDGER = ([rule("S1", i, "regime", "OVERFIT") for i in range(10)]
          + [rule("S1", 10 + i, "regime", "NEGATIVE_EXPECTANCY", "positive before costs on the check rows") for i in range(4)]
          + [rule("S1", 20 + i, "cross-sectional", "INSUFFICIENT_POWER") for i in range(3)]
          + [rule("S1", 30, "cross-sectional", "PROMISING_UNCONFIRMED"), rule("S1", 31, "cross-sectional", "PROMISING_UNCONFIRMED")]
          + [{"run": "S1", "event": "VALIDATION", "id": "S1-30", "class": "VALIDATED_ON_UNREAD_ROWS"},
             {"run": "S1", "event": "VALIDATION", "id": "S1-31", "class": "REJECTED_BY_VALIDATION"}]
          + [rule("S9", 0, "anomaly", "OVERFIT")])  # a run of no known market: left out


def test_the_record_is_counted_by_market_and_family():
    t = B.arms(LEDGER, {"S1": "mkt-a"})
    assert set(t) == {"mkt-a"} and set(t["mkt-a"]) == {"regime", "cross-sectional"}
    r, x = t["mkt-a"]["regime"], t["mkt-a"]["cross-sectional"]
    assert (r["rules"], r["overfit"], r["negative"], r["negative_after_costs_only"], r["positive"]) == (14, 10, 4, 4, 0)
    assert (x["rules"], x["positive"], x["promising"], x["validated"], x["rejected_by_validation"]) == (5, 5, 2, 1, 1)
    assert B.usefulness({}) == 0.5 and B.usefulness(x) > 0.5 > B.usefulness(r)
    text = " ".join(B.lessons(t, {"mkt-a": {"A": {"features": 20, "z_at_least_2": 1, "non_linear_only": 0}}}))
    assert "19 rules" in text and "1 passed validation and 1 failed it" in text
    assert "regime rules overfit most often (10 of 14)" in text and "4 regime rules were positive before costs" in text
    assert "1 of 20 feature-instrument pairs" in text


def test_effort_follows_the_record_and_no_family_is_dropped():
    t = B.arms(LEDGER, {"S1": "mkt-a"})["mkt-a"]
    draws = [B.allocation(t, seed) for seed in range(40)]
    for a in draws:
        assert set(a) == set(B.METHOD_OF.values()) and all(B.FLOOR <= v <= B.CEILING for v in a.values())
    mean = {m: sum(a[m] for a in draws) / len(draws) for m in draws[0]}
    assert mean["breadth"] > mean["regimes"] + 8  # what validated gets room; what overfitted gets less
    assert mean["regimes"] >= B.FLOOR  # and is still tried
    assert len({json.dumps(a, sort_keys=True) for a in draws}) > 5  # it explores: the draws differ
    assert B.allocation(t, 3) == B.allocation(t, 3)  # and a seed gives the same draw again


def test_an_unscanned_broad_market_is_scanned_first():
    t = B.arms(LEDGER, {"S1": "mkt-a"})["mkt-a"]
    barren = {"regime": {**t["regime"]}}
    assert B.dataset_priority(50, None) > B.dataset_priority(2, None) > B.dataset_priority(50, barren)
    assert B.dataset_priority(50, t) > B.dataset_priority(50, barren)  # a market whose rules survived, before one whose did not


# ── the feeds ───────────────────────────────────────────────────────────────

def zipped(text: str) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("file.csv", text)
    return b.getvalue()


KLINES = ("open_time,open,high,low,close,volume,close_time\n"
          "1577836800000,7189.4,7260.4,7170.1,7197.5,56801,1577923199999\n"
          "1577923200000,7197.5,7209.5,6922.0,6962.3,81000,1578009599999\n"
          "1578009600000,1,1,1,abc,1,1578095999999\n"  # unreadable: skipped, never repaired
          "1578096000000,1,1,1,0,1,1578182399999\n"  # a zero close: not a price
          "1735689600000000,93500,95000,93000,94500,1,1735775999999999\n")  # microseconds, as the newer files use


def test_a_month_of_klines_and_of_funding_is_read_without_repairing_anything():
    assert F.parse_daily_klines(zipped(KLINES)) == {"2020-01-01": 7197.5, "2020-01-02": 6962.3, "2025-01-01": 94500.0}
    funding = ("calc_time,funding_interval_hours,last_funding_rate\n1577836800000,8,0.0001\n1577865600000,8,0.0002\n"
               "1577894400000,8,-0.00005\n1577923200000,8,0.0001\n1577952000000,8,oops\n"
               "1578009600000.0,8,0.0003\n")  # a timestamp written as a float, as some files have it
    out = F.parse_funding(zipped(funding))
    assert out["2020-01-01"] == pytest.approx(0.00025) and out["2020-01-02"] == pytest.approx(0.0001)
    assert out["2020-01-03"] == pytest.approx(0.0003) and len(out) == 3
    assert F.months(date(2019, 11, 15), date(2020, 2, 1)) == ["2019-11", "2019-12", "2020-01", "2020-02"]


def test_a_file_that_fails_its_checksum_stops_the_fetch(monkeypatch):
    raw = zipped(KLINES)
    good = (hashlib.sha256(raw).hexdigest() + "  BTCUSDT-1d-2020-01.zip\n").encode()
    served = {"u": raw, "u.CHECKSUM": good}
    monkeypatch.setattr(F, "get", lambda url: served.get(url))
    assert F.checked("u") == raw
    assert F.checked("absent") is None  # a month that does not exist is not an error
    served["u.CHECKSUM"] = b"0" * 64 + b"  x.zip\n"
    with pytest.raises(SystemExit, match="CHECKSUM"):
        F.checked("u")
    del served["u.CHECKSUM"]
    with pytest.raises(RuntimeError, match="no CHECKSUM"):
        F.checked("u")


def test_the_crypto_feed_fetches_only_what_it_does_not_hold(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        sym = url.split("/")[-1].split("-")[0]
        month = url[-11:-4]
        if sym == "DEADUSDT" and month >= "2020-02":
            return None  # delisted: no file
        ms = int(datetime(int(month[:4]), int(month[5:]), 1, tzinfo=timezone.utc).timestamp() * 1000)
        if "fundingRate" in url:
            return zipped(f"calc_time,h,rate\n{ms},8,0.0001\n{ms + 28800000},8,0.0001\n")
        return zipped(f"{ms},1,1,1,{100 + int(month[5:])},1,0\n{ms + 86400000},1,1,1,{101 + int(month[5:])},1,0\n")
    now = datetime(2020, 4, 10, tzinfo=timezone.utc)
    man = F.crypto_daily(tmp_path, now, first=date(2020, 1, 1), symbols=("BTCUSDT", "DEADUSDT"), fetch=fetch, workers=2)
    # the last COMPLETE month is March: January to March, two kinds, two symbols
    assert len(calls) == 12 and man["fetched_now"] == 8 and man["absent_now"] == 4
    close = json.loads((tmp_path / "close.json").read_text())
    assert close["BTCUSDT"]["2020-03-02"] == 104.0 and sorted(close["DEADUSDT"]) == ["2020-01-01", "2020-01-02"]
    assert json.loads((tmp_path / "funding.json").read_text())["BTCUSDT"]["2020-02-01"] == pytest.approx(0.0002)
    assert man["months"]["BTCUSDT:klines"] == ["2020-01", "2020-02", "2020-03"] and man["months"]["DEADUSDT:klines"] == ["2020-01"]
    assert man["files"]["close"]["sha256"] == hashlib.sha256((tmp_path / "close.json").read_bytes()).hexdigest()
    assert man["quality"]["BTCUSDT"]["rows"] == 6 and man["quality"]["BTCUSDT"]["missing_days"] > 50  # two days a month held
    calls.clear()
    F.crypto_daily(tmp_path, now, first=date(2020, 1, 1), symbols=("BTCUSDT", "DEADUSDT"), fetch=fetch, workers=2)
    assert len(calls) == 4 and all("DEADUSDT" in u for u in calls)  # only the months that were not there are asked again
    calls.clear()
    man = F.crypto_daily(tmp_path, now + timedelta(days=30), first=date(2020, 1, 1), symbols=("BTCUSDT",), fetch=fetch)
    assert sorted(calls) == sorted(u for u in calls if "2020-04" in u) and len(calls) == 2  # the new month only
    assert json.loads((tmp_path / "close.json").read_text())["BTCUSDT"]["2020-04-01"] == 104.0
    assert man["failed_count"] == 0


def test_a_file_the_archive_did_not_answer_for_is_counted_kept_apart_and_asked_for_again(tmp_path):
    down = {"on": True}
    calls = []

    def fetch(url):
        calls.append(url)
        month = url[-11:-4]
        if down["on"] and month == "2020-02" and "klines" in url:
            raise RuntimeError("the archive timed out")
        ms = int(datetime(int(month[:4]), int(month[5:]), 1, tzinfo=timezone.utc).timestamp() * 1000)
        return zipped(f"{ms},8,0.0001\n") if "fundingRate" in url else zipped(f"{ms},1,1,1,{100 + int(month[5:])},1,0\n")
    now = datetime(2020, 4, 10, tzinfo=timezone.utc)
    man = F.crypto_daily(tmp_path, now, first=date(2020, 1, 1), symbols=("BTCUSDT",), fetch=fetch, workers=2)
    assert man["failed_count"] == 1 and man["failed_now"] == ["BTCUSDT:klines:2020-02"] and man["fetched_now"] == 5
    close = json.loads((tmp_path / "close.json").read_text())["BTCUSDT"]
    assert sorted(close) == ["2020-01-01", "2020-03-01"]  # what arrived is kept; the missing month is not filled
    assert "2020-02" not in man["months"]["BTCUSDT:klines"]
    calls.clear()
    down["on"] = False
    man = F.crypto_daily(tmp_path, now, first=date(2020, 1, 1), symbols=("BTCUSDT",), fetch=fetch, workers=2)
    assert len(calls) == 1 and "2020-02" in calls[0] and man["failed_count"] == 0  # only the missing file is asked for
    assert sorted(json.loads((tmp_path / "close.json").read_text())["BTCUSDT"]) == ["2020-01-01", "2020-02-01", "2020-03-01"]


def test_data_quality_is_measured_and_nothing_is_removed():
    q = F.quality({"A": {"2024-01-01": 10.0, "2024-01-02": 10.5, "2024-01-05": 17.0, "2024-01-06": 17.1}, "B": {}})
    assert q["A"] == {"rows": 4, "first": "2024-01-01", "last": "2024-01-06", "missing_days": 2, "moves_beyond_50pct": 1}
    assert q["B"] == {"rows": 0}
    weekdays = {(date(2024, 1, 1) + timedelta(days=i)).isoformat(): 1.0 for i in range(70)
                if (date(2024, 1, 1) + timedelta(days=i)).weekday() < 5}
    assert F.quality({"W": weekdays})["W"]["missing_days"] == 0  # an instrument that never trades a weekend misses none


def yahoo(days_closes: list[tuple[str, float | None]]) -> bytes:
    ts = [int(datetime.fromisoformat(d + "T14:30:00+00:00").timestamp()) for d, _ in days_closes]
    return json.dumps({"chart": {"result": [{"meta": {"exchangeTimezoneName": "America/New_York"}, "timestamp": ts,
                                             "indicators": {"quote": [{"close": [c for _, c in days_closes]}],
                                                            "adjclose": [{"adjclose": [c for _, c in days_closes]}]}}]}}).encode()


def test_the_etf_feed_keeps_finished_days_only_and_says_what_was_not_served(tmp_path):
    now = datetime(2024, 1, 5, 18, 0, tzinfo=timezone.utc)

    def fetch(url):
        if "/SPY?" in url:
            return yahoo([("2024-01-02", 470.0), ("2024-01-03", None), ("2024-01-04", 468.0), ("2024-01-05", 469.0)])
        if "%5EVIX" in url:
            return yahoo([("2024-01-02", 13.2), ("2024-01-04", 14.1)])
        return b"{}" if "/BAD?" in url else None
    man = F.etf_daily(tmp_path, now, first=date(2024, 1, 1), symbols=("SPY", "BAD", "GONE"), fetch=fetch)
    close = json.loads((tmp_path / "close.json").read_text())
    assert close["SPY"] == {"2024-01-02": 470.0, "2024-01-04": 468.0}  # the missing close stays missing; today is not final
    assert close["^VIX"] == {"2024-01-02": 13.2, "2024-01-04": 14.1} and man["not_served"] == ["BAD", "GONE"]
    assert man["quality"]["SPY"]["missing_days"] == 1 and man["files"]["close"]["sha256"]


ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2611.01234v2</id><title>Information  flow in
 perpetual futures</title><summary> We  measure transfer entropy. </summary><published>2026-11-03T10:00:00Z</published>
<author><name>A. One</name></author><author><name>B. Two</name></author></entry>
<entry><id></id><title>no id</title></entry></feed>"""
ALEX = json.dumps({"results": [
    {"id": "https://openalex.org/W99", "display_name": "Regimes and  returns", "publication_date": "2025-05-01",
     "doi": "https://doi.org/10.1/x", "cited_by_count": 7, "authorships": [{"author": {"display_name": "C. Three"}}],
     "primary_location": {"landing_page_url": "https://example.org/p"},
     "abstract_inverted_index": {"markets": [1], "Hidden": [0], "switch": [2]}},
    {"id": None, "display_name": "broken"}]}).encode()


def test_sources_are_recorded_as_unread_with_their_link_and_date_and_never_twice():
    a = F.parse_arxiv(ATOM, "q", "2026-11-11T00:00:00+00:00")
    assert len(a) == 1 and a[0]["id"] == "arxiv:2611.01234" and a[0]["title"] == "Information flow in perpetual futures"
    assert a[0]["published"] == "2026-11-03" and a[0]["authors"] == ["A. One", "B. Two"] and a[0]["url"].endswith("2611.01234v2")
    assert a[0]["status"] == "UNREAD" and a[0]["reproducibility"] == "not attempted"  # nothing is claimed about it
    o = F.parse_openalex(ALEX, "regimes", "now")
    assert len(o) == 1 and o[0]["id"] == "openalex:W99" and o[0]["abstract"] == "Hidden markets switch"
    assert o[0]["url"] == "https://example.org/p" and o[0]["title"] == "Regimes and returns" and o[0]["status"] == "UNREAD"
    asked = []

    def fetch(url):
        asked.append(url)
        return ATOM if "arxiv" in url else ALEX
    new = F.papers({"openalex:W99"}, NOW, week=3, fetch=fetch)
    assert [s["id"] for s in new] == ["arxiv:2611.01234"]  # the one already on file is not recorded again
    assert len(asked) == 2 and F.QUERIES[3].split()[0] in asked[1] and "2023-01-01" in asked[1]
    assert F.papers({"openalex:W99", "arxiv:2611.01234"}, NOW, week=3, fetch=fetch) == []
    assert F.papers(set(), NOW, week=0, fetch=lambda url: None) == []  # a source that does not answer adds nothing
