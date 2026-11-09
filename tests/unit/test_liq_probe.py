"""The LIQ-1 data probe (scripts/liq_probe.py) reports dates and column names only."""

from __future__ import annotations

import io
import zipfile

import scripts.liq_probe as P


def test_it_reads_keys_dates_and_gaps_from_a_listing():
    xml = ("<ListBucketResult><IsTruncated>true</IsTruncated>"
           "<Contents><Key>data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2021-12-01.zip</Key></Contents>"
           "<Contents><Key>data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2021-12-01.zip.CHECKSUM</Key>"
           "</Contents><Contents><Key>data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2021-12-04.zip</Key>"
           "</Contents></ListBucketResult>")
    keys, more = P.keys_from_listing(xml)
    assert more and len(keys) == 3
    st = P.stamps(keys)
    assert st == ["2021-12-01", "2021-12-04"] and P.gaps(st) == ["2021-12-02", "2021-12-03"]
    assert P.gaps(["2023-11", "2024-02"]) == ["2023-12", "2024-01"] and P.gaps([]) == []


def test_a_header_keeps_names_and_hides_numbers():
    def z(text):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as f:
            f.writestr("x.csv", text)
        return b.getvalue()
    assert P.header(z("create_time,symbol,sum_open_interest\n2024-01-01 00:05:00,BTCUSDT,1234.5\n")) == [
        "create_time", "symbol", "sum_open_interest"]
    assert P.header(z("1704067200000,42000.1,42100.0\n")) == ["<a number>", "<a number>", "<a number>"]
