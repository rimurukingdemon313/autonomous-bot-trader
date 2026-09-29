"""External data: every value is dated by when it became public, and nothing later is ever served."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone

import numpy as np
import pytest

from aitrader.data.external import ExternalStore, available_at, parse
from aitrader.research.registry import Holdout


def utc(y, m, d, h=0, mi=0):
    return int(datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp())


def test_a_vix_close_is_public_before_the_new_york_close_in_summer_and_in_winter():
    # D1 bars close at 17:00 New York: 21:00 UTC in summer, 22:00 UTC in winter
    assert available_at("vix", date(2015, 7, 1)) == utc(2015, 7, 1, 20, 45) < utc(2015, 7, 1, 21)
    assert available_at("vix", date(2015, 1, 5)) == utc(2015, 1, 5, 21, 45) < utc(2015, 1, 5, 22)


def test_slower_series_wait_for_their_release():
    assert available_at("brent", date(2015, 3, 2)) == utc(2015, 3, 3, 22)  # one full day later
    assert available_at("us10y", date(2015, 3, 1)) == utc(2015, 4, 2, 21)  # the March average, after March
    assert available_at("cpi_us", date(2013, 9, 1)) == utc(2013, 10, 31, 21)  # later than the shutdown-delayed release
    assert available_at("cpi_us", date(2015, 12, 1)) == utc(2016, 1, 31, 22)


RAW = b"DATE,OPEN,HIGH,LOW,CLOSE\n2015-01-05,1,1,1,19.9\n2015-01-06,1,1,1,0\n2015-01-07,1,1,1,21.5\n"


def test_asof_never_serves_a_value_before_it_was_public():
    s = parse("vix", RAW)
    assert list(s.value) == [19.9, 21.5]  # a zero is "missing" upstream, not a level
    t = np.array([utc(2015, 1, 5, 21, 44), utc(2015, 1, 5, 21, 45), utc(2015, 1, 7, 12), utc(2015, 1, 7, 22)])
    got = s.asof(t)
    assert np.isnan(got[0]) and got[1] == 19.9 and got[2] == 19.9 and got[3] == 21.5
    assert np.isnan(s.asof_lag(t, 1)[2]) and s.asof_lag(t, 1)[3] == 19.9


def test_unverified_files_are_refused_and_the_holdout_is_sealed(tmp_path):
    raw = RAW + b"2017-01-03,1,1,1,12.8\n"
    (tmp_path / "vix.csv").write_bytes(raw)
    (tmp_path / "manifest.json").write_text(json.dumps({"vix": {"sha256": "0" * 64}}))
    with pytest.raises(ValueError):
        ExternalStore(tmp_path).load("vix")
    (tmp_path / "manifest.json").write_text(json.dumps({"vix": {"sha256": hashlib.sha256(raw).hexdigest()}}))
    h = Holdout("fx-majors", date(2017, 1, 1), datetime(2026, 9, 1, tzinfo=timezone.utc), "test")
    s = ExternalStore(tmp_path, h).load("vix")
    assert list(s.value) == [19.9, 21.5]
