"""The ENG-1 data probe (scripts/eng_probe.py) reports dates only and keeps no value."""

from __future__ import annotations

from datetime import date, timedelta

import scripts.eng_probe as P


def serial(d: date) -> int:
    return (d - P.EXCEL_EPOCH).days


def test_only_dated_numeric_rows_count_and_no_value_is_kept():
    rows = [(("other", "Back to Contents"), ("other", "Data 1")),
            (("other", "Sourcekey"), ("other", "RCLC1")),
            (("date", serial(date(1983, 3, 30))), ("number", 29.4)),
            (("date", serial(date(1983, 3, 31))), ("other", "")),  # no price that day
            (("number", serial(date(1983, 4, 4))), ("number", 30.6)),
            (("date", serial(date(1983, 4, 4))), ("number", 30.6))]  # a duplicate is one day
    days = P.priced_days(rows)
    assert days == [date(1983, 3, 30), date(1983, 4, 4)]
    assert all(isinstance(d, date) for d in days)  # dates only: the prices 29.4 and 30.6 are not returned
    assert set(P.describe(days)) == {"rows", "first", "last", "missing_weekdays", "missing_weekdays_per_year",
                                     "longest_gap_days", "per_decade"}  # counts and dates, nothing from a price
    assert "29.4" not in repr(P.describe(days)) and "30.6" not in repr(P.common([days]))


def test_it_describes_dates_gaps_and_the_days_all_contracts_share():
    days = [date(2024, 1, 1) + timedelta(days=i) for i in range(40) if (date(2024, 1, 1) + timedelta(days=i)).weekday() < 5]
    gap = [d for d in days if not date(2024, 1, 10) <= d <= date(2024, 1, 16)]
    d = P.describe(gap)
    assert d["first"] == "2024-01-01" and d["last"] == str(days[-1])
    assert d["missing_weekdays"] == 5 and d["longest_gap_days"] == 8 and d["per_decade"] == {"2020s": len(gap)}
    c = P.common([days, gap, days[3:]])
    assert c["first"] == str(days[3]) and c["rows"] == len([x for x in gap if x >= days[3]])
    assert P.common([days, []]) == {"rows": 0} and P.describe([]) == {"rows": 0}
