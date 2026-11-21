"""The TRINITY data fetcher (scripts/trinity_data.py): bars are stored as served, by the exchange's own date, final
only, never filled."""

import json
from datetime import date, datetime, timezone

from scripts import trinity_data as td


def _res(rows, tz="America/New_York", adj=True):
    """A Yahoo chart result: rows of (utc datetime, o, h, l, c, v, adj)."""
    r = {"meta": {"exchangeTimezoneName": tz}, "timestamp": [int(t.timestamp()) for t, *_ in rows],
         "indicators": {"quote": [{"open": [x[1] for x in rows], "high": [x[2] for x in rows],
                                   "low": [x[3] for x in rows], "close": [x[4] for x in rows],
                                   "volume": [x[5] for x in rows]}]}}
    if adj:
        r["indicators"]["adjclose"] = [{"adjclose": [x[6] for x in rows]}]
    return r


NOW = datetime(2026, 11, 20, 3, 0, tzinfo=timezone.utc)


def test_bars_are_filed_by_the_exchange_date_and_the_open_day_is_left_out():
    rows = [(datetime(2026, 11, 18, 14, 30, tzinfo=timezone.utc), 10, 11, 9, 10.5, 100, 10.4),
            # 03:30 UTC on the 19th is 22:30 on the 18th in New York: the 18th's date, a second row for it
            (datetime(2026, 11, 19, 3, 30, tzinfo=timezone.utc), 10.5, 12, 10, 11.0, 50, 10.9),
            (datetime(2026, 11, 19, 14, 30, tzinfo=timezone.utc), 11, 12, 10, 11.5, 70, 11.4),
            (datetime(2026, 11, 20, 14, 30, tzinfo=timezone.utc), 12, 13, 11, 12.5, 90, 12.4)]
    out, problems = td.parse(_res(rows), NOW)
    # the 03:30 UTC row is still 2026-11-18 in New York: a second row for that day, named, the first kept
    assert sorted(out) == ["2026-11-18", "2026-11-19"]
    assert out["2026-11-18"]["c"] == 10.5 and out["2026-11-19"]["adj"] == 11.4
    assert any("second row" in p for p in problems)
    assert "2026-11-20" not in out  # not final at NOW


def test_a_missing_close_is_left_out_and_named_never_filled():
    rows = [(datetime(2026, 11, 16, 14, 30, tzinfo=timezone.utc), 10, 11, 9, None, 100, None),
            (datetime(2026, 11, 17, 14, 30, tzinfo=timezone.utc), None, None, None, None, None, None),
            (datetime(2026, 11, 18, 14, 30, tzinfo=timezone.utc), 10, 11, 9, float("nan"), 1, 1.0),
            (datetime(2026, 11, 19, 14, 30, tzinfo=timezone.utc), 10, 11, 9, 10.2, 1, None)]
    out, problems = td.parse(_res(rows), NOW)
    assert list(out) == ["2026-11-19"]
    assert out["2026-11-19"]["adj"] is None  # absent stays absent
    assert len(problems) == 2  # the empty holiday row is not a problem; the two rows with prices but no close are


def test_no_adjclose_block_reads_as_absent():
    rows = [(datetime(2026, 11, 18, 14, 30, tzinfo=timezone.utc), 10, 11, 9, 10.5, 100, None)]
    out, _ = td.parse(_res(rows, adj=False), NOW)
    assert out["2026-11-18"]["adj"] is None


def test_write_names_a_failed_series_and_writes_nothing_for_it(tmp_path):
    good = _res([(datetime(2026, 11, 18, 14, 30, tzinfo=timezone.utc), 10, 11, 9, 10.5, 100, 10.4)])

    def fetch(sym, first, now):
        if sym == "TLT":
            raise OSError("refused")
        return good

    man = td.write(tmp_path, NOW, date(2026, 11, 1), fetch=fetch)
    assert man["failed"] == {"TLT": "OSError: refused"}
    assert not (tmp_path / "history" / "TLT.json").exists()
    assert (tmp_path / "history" / "_VIX.json").exists() and (tmp_path / "history" / "GC_F.json").exists()
    on_disk = json.loads((tmp_path / "history" / "manifest.json").read_text())
    assert on_disk["series"]["SPY"]["rows"] == 1 and on_disk["series"]["SPY"]["first"] == "2026-11-18"
    assert set(on_disk["series"]) == set(td.SYMBOLS) - {"TLT"}
