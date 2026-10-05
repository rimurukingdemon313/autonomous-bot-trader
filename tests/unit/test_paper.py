"""Paper broker financing (paper-1.1.0): swap nights follow the 21:00 UTC rollover convention of the research
simulators, with Wednesday's triple charge and no weekend nights."""

from __future__ import annotations

from datetime import datetime, timezone

from aitrader.broker.paper import rollovers
from aitrader.research.discovery import intraday as ID


def ts(y, m, d, h=0, mi=0):
    return int(datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp())


def test_an_intraday_position_closed_before_21_utc_pays_no_swap():
    assert rollovers(ts(2024, 3, 4, 8), ts(2024, 3, 4, 20, 55)) == 0  # Monday


def test_crossing_a_weekday_rollover_counts_once_and_wednesday_three_times():
    assert rollovers(ts(2024, 3, 4, 20), ts(2024, 3, 4, 22)) == 1  # Monday 21:00
    assert rollovers(ts(2024, 3, 6, 20), ts(2024, 3, 6, 22)) == 3  # Wednesday 21:00


def test_friday_to_monday_is_one_night_not_three():
    # Friday 21:00 counts; Saturday and Sunday have no rollover. The old count of UTC midnights said 3.
    assert rollovers(ts(2024, 3, 8, 20), ts(2024, 3, 11, 8)) == 1


def test_the_count_matches_the_research_financing_convention():
    for t0, t1 in [(ts(2024, 3, 4, 10), ts(2024, 3, 12, 10)), (ts(2024, 3, 6, 22), ts(2024, 3, 14, 3))]:
        # intraday.financing charges (earn - markup)/100 * price/365 per counted night: with earn 0,
        # markup 365 and price 100 every night is exactly -1.
        assert rollovers(t0, t1) == round(-ID.financing(t0, t1, 1, 100.0, 365.0, None))
