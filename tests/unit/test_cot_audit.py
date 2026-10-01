"""The COT publication rule never lets an observation be used before it could have been public."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import cot_audit  # noqa: E402


def test_a_tuesday_report_is_usable_only_from_the_monday_after_its_friday_release():
    tue = date(2015, 3, 3)
    assert cot_audit.available_on(tue) == date(2015, 3, 9)  # Monday; the Friday release was 2015-03-06


def test_every_as_of_weekday_lands_on_a_weekday_after_the_latest_normal_release():
    d = date(2008, 1, 1)
    while d < date(2017, 1, 1):
        a = cot_audit.available_on(d)
        if a is not None:
            assert a.weekday() < 5
            # a holiday-delayed release is the business day after the Friday: never later than as_of + 6
            assert a >= d + timedelta(days=6)
        d += timedelta(days=1)


def test_shutdown_reports_have_no_release_date_and_are_never_given_one():
    assert cot_audit.available_on(date(2013, 10, 1)) is None
    assert cot_audit.available_on(date(2013, 12, 24)) is None
    assert cot_audit.available_on(date(2013, 9, 24)) == date(2013, 9, 30)


def test_the_committed_manifest_records_a_clean_futures_only_audit():
    m = json.loads((ROOT / "data" / "cot" / "manifest.json").read_text())
    assert all(f["report_type"] == ["FutOnly"] for f in m["files"].values())
    assert m["publication_rule"]["release_dates_in_file"] is False
    for c in m["contracts"].values():
        assert not any(c["checks"].values())
    assert m["missing_weeks_vs_union"] == {"NZD": ["2006-06-20", "2006-06-27", "2006-07-03"]}
