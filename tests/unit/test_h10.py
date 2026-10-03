"""H.10 loader and audit: provenance transformations undone exactly, the no-rate calendar as observed,
point-in-time use from the next business day, and the committed audit's conclusions."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from aitrader.data.h10 import (H10Error, H10Store, PRIMARY, SERIES, available_at, fed_holidays, next_business_day,
                               official_series, official_value, on_grid, parse_mirror, vintage_file)
from aitrader.research.registry import Holdout

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import h10_audit  # noqa: E402

NY = ZoneInfo("America/New_York")


def _long(rows, header="Date,Country,Exchange rate") -> bytes:
    return ("\r\n".join([header] + [f"{d},{c},{v}" for d, c, v in rows]) + "\r\n").encode()


def test_the_three_mirror_formats_parse_to_the_same_values_and_missing_stays_missing():
    long_ = _long([("2015-12-24", "Euro", "0.9128"), ("2015-12-25", "Euro", ""), ("2015-12-24", "Japan", "120.32")])
    value = _long([("2015-12-24", "Euro", "0.9128"), ("2015-12-25", "Euro", "."), ("2015-12-24", "Japan", "120.32")],
                  header="Date,Country,Value")
    wide = b"Data,Euro,Japan\r\n2015-12-24,0.9128,120.32\r\n2015-12-25,,\r\n"
    for raw in (long_, value, wide):
        p = parse_mirror(raw)
        assert p["EUR"][date(2015, 12, 24)] == "0.9128" and p["EUR"][date(2015, 12, 25)] == ""
        assert p["JPY"][date(2015, 12, 24)] == "120.32"
    with pytest.raises(H10Error):
        parse_mirror(_long([("2015-12-24", "Euro", "0.9128"), ("2015-12-24", "Euro", "0.9129")]))
    with pytest.raises(H10Error):
        parse_mirror(b"when,where\r\n")


def test_the_mirror_inversion_is_undone_exactly_and_a_rounded_vintage_is_refused():
    # FRED DEXUSEU 1.5778; the 2018 vintage stored str(1/1.5778), later vintages round(1/1.5778, 4) = 0.6338
    assert official_value(str(1 / 1.5778), "EUR") == pytest.approx(1.5778, abs=1e-12)
    assert on_grid(official_value(str(1 / 1.5778), "EUR"), 4)
    assert not on_grid(official_value("0.6338", "EUR"), 4)  # 1/0.6338 = 1.57778...: the official value is lost
    assert official_value("120.32", "JPY") == 120.32  # not inverted by the mirror
    s = official_series(_long([("2015-06-01", "Euro", str(1 / 1.0950))]))
    assert s["EUR"].value[0] == 1.095 and s["EUR"].pair == "EURUSD"
    with pytest.raises(H10Error):
        official_series(_long([("2015-06-01", "Euro", "0.9132")]))


def test_the_no_rate_calendar_is_the_one_observed_in_the_data():
    assert date(2015, 7, 3) in fed_holidays(2015)  # Saturday July 4: no rate on the Friday, from 2010
    assert date(2009, 7, 3) not in fed_holidays(2009)  # ... but H.10 had a rate on that Friday before
    assert {date(2010, 12, 24), date(2010, 12, 31)} <= fed_holidays(2010)  # incl. the next year's New Year
    assert date(2016, 12, 26) in fed_holidays(2016)  # Sunday Christmas -> Monday
    assert date(2001, 9, 11) in fed_holidays(2001) and date(2014, 12, 26) in fed_holidays(2014)
    assert date(2007, 11, 22) in fed_holidays(2007)  # Thanksgiving


def test_a_value_on_a_no_rate_day_is_a_carried_copy_and_is_dropped():
    raw = _long([("2007-11-21", "Japan", "108.54"), ("2007-11-22", "Japan", "108.54"),
                 ("2007-11-23", "Japan", "108.17")])
    assert official_series(raw)["JPY"].dates == (date(2007, 11, 21), date(2007, 11, 23))


def test_a_rate_is_used_only_from_17h_new_york_on_the_next_business_day():
    assert next_business_day(date(2015, 7, 2)) == date(2015, 7, 6)  # Friday 3 July had no rate
    assert available_at(date(2015, 7, 2)) == int(datetime(2015, 7, 6, 17, tzinfo=NY).timestamp())
    assert available_at(date(2016, 3, 9)) == int(datetime(2016, 3, 10, 17, tzinfo=NY).timestamp())
    assert available_at(date(2016, 3, 11)) == int(datetime(2016, 3, 14, 17, tzinfo=NY).timestamp())  # Friday


def test_the_store_verifies_the_primary_vintage_and_seals_the_holdout(tmp_path):
    rows = [("2016-12-29", "Euro", str(1 / 1.0466)), ("2016-12-30", "Euro", str(1 / 1.0552))]
    raw = _long(rows)
    (tmp_path / vintage_file(PRIMARY)).write_bytes(raw)
    (tmp_path / "manifest.json").write_text(json.dumps({"files": {vintage_file(PRIMARY): {
        "sha256": hashlib.sha256(raw).hexdigest()}}}))
    h = Holdout("fx-majors", date(2017, 1, 1), datetime(2026, 1, 1, tzinfo=timezone.utc), "test")
    eur = H10Store(tmp_path, h).load()["EUR"]
    assert eur.dates == (date(2016, 12, 29),)  # 30 Dec is usable only from 3 Jan 2017: inside the seal
    assert len(H10Store(tmp_path, h).load(key=object())["EUR"].dates) == 2
    (tmp_path / "manifest.json").write_text(json.dumps({"files": {vintage_file(PRIMARY): {"sha256": "0" * 64}}}))
    with pytest.raises(H10Error):
        H10Store(tmp_path, h).load()


def test_the_revision_check_compares_through_the_mirrors_own_rounding():
    prim = parse_mirror(_long([("2005-03-01", "Euro", str(1 / 1.3205)), ("2005-03-01", "Japan", "104.71")]))
    same = parse_mirror(_long([("2005-03-01", "Euro", str(round(1 / 1.3205, 4))), ("2005-03-01", "Japan", "104.71")]))
    revised = parse_mirror(_long([("2005-03-01", "Euro", "0.7574"), ("2005-03-01", "Japan", "104.72")]))
    res = h10_audit.revisions({PRIMARY: prim, "a": same, "b": revised})
    assert res[f"{PRIMARY} vs a"]["EUR"]["different"] == 0 and res[f"{PRIMARY} vs a"]["JPY"]["different"] == 0
    assert res[f"{PRIMARY} vs b"]["EUR"]["different"] == 1 and res[f"{PRIMARY} vs b"]["JPY"]["different"] == 1


def test_the_committed_audit_supports_its_verdict():
    m = json.loads((ROOT / "data" / "h10" / "manifest.json").read_text())
    assert m["primary_vintage"] == PRIMARY and m["value_window"][1] == "2017-01-01"
    assert all(v["off_grid"] == 0 and v["checked"] > 4000 for v in m["transformation_check"].values())
    for comparison in m["revisions"].values():
        assert all(v["different"] == 0 for v in comparison.values())
    g = m["gaps"][PRIMARY]
    assert g["missing_on_all_not_holiday"] == [] and g["missing_on_some_only"] == {}
    for d, v in g["no_rate_days_with_a_value"].items():
        assert v["identical_to_previous_rate"] == v["currencies"], d  # every such value is a carried copy
    xs = m["cross_source"]
    for ccy in SERIES:
        if ccy != "AUD":  # AUD's Dukascopy series is the faulty side in 2008-2009 (triangulation below)
            assert xs[ccy]["best_matching_time_ny"] == "12:00"
            assert xs[ccy]["weekly_returns"]["corr_vs_noon"] > 0.997
    for ccy, years in m["third_source"]["triangulation"].items():
        assert all(y["h10_vs_implied_median_abs_bp"] < 2.0 for y in years.values()), ccy
    assert m["third_source"]["triangulation"]["AUD"]["2008"]["dukascopy_direct_vs_implied_median_abs_bp"] > 5.0
