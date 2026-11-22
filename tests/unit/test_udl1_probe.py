"""UDL-1's data probe (scripts/udl1.py): it finds Upbit's delisting notices wherever the list sits in the response,
reads their tickers and the termination time they state, keeps postponed or withdrawn notices apart, and reads no
price: only notice text and the archive's file names."""

import json
from datetime import datetime, timezone

from scripts import udl1 as U


def test_tickers_and_termination_times_are_read_from_the_title():
    t = "[거래] 메디블록(MED), 엑스알피(XRP2) 거래지원 종료 안내 (2024.01.15 15:00)"
    assert U.tickers(t) == ["MED", "XRP2"]
    assert U.termination(t) == "2024-01-15T15:00:00+09:00"
    assert U.tickers("일부 디지털 자산 거래지원 종료 (DMT, BTT, 2021)") == ["BTT", "DMT"]
    assert U.termination("거래지원 종료 안내") is None


def test_the_probe_reads_notice_text_and_file_names_only():
    asked = []
    page1 = {"success": True, "data": {"notices": [
        {"id": 1, "title": "[거래] 에이(AAA) 거래지원 종료 안내 (2023.05.02 15:00)", "listed_at": "2023-04-20T10:00:00"},
        {"id": 2, "title": "[거래] 비(BBB) 거래지원 종료 연기 안내", "listed_at": "2023-04-21T10:00:00"},
        {"id": 3, "title": "[거래] 씨(CCC) 거래지원 종료 안내", "listed_at": "2023-06-01T10:00:00"},
        {"id": 4, "title": "[이벤트] 신규 상장 이벤트", "listed_at": "2023-06-02T10:00:00"}]}}
    listing = ("<ListBucketResult xmlns='http://s3.amazonaws.com/doc/2006-03-01/'><Prefix>x</Prefix>"
               "<IsTruncated>false</IsTruncated>{keys}</ListBucketResult>")

    def fetch(url):
        asked.append(url)
        if "announcements?" in url and "category=trade" in url:
            return json.dumps(page1 if "page=1&" in url else {"data": {"notices": []}}).encode()
        if "announcements/3" in url:
            return json.dumps({"data": {"body": "거래지원 종료 일시 : 2023년 6월 12일 15:00"}}).encode()
        for c in ("AAA", "CCC"):
            if f"{c}USDT" in url:
                m = "2023-05" if c == "AAA" else "2023-06"
                return listing.format(keys=f"<Contents><Key>data/spot/monthly/klines/{c}USDT/1h/{c}USDT-1h-{m}.zip"
                                           "</Key></Contents>").encode()
        return listing.format(keys="").encode()
    body = U.probe(fetch, datetime(2026, 11, 22, tzinfo=timezone.utc), detail_pause=0)
    assert body["exit_notices"] == 3 and body["dated_exits"] == 2  # the postponed one is kept apart
    assert body["codes"] == ["AAA", "BBB", "CCC"] and body["usable_coin_exits"] == 2
    assert {e["id"]: e["termination_kst"] for e in body["exits"]}[3] == "2023-06-12T15:00:00+09:00"
    assert not any(u.endswith(".zip") or "candles" in u for u in asked)
