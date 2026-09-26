"""Data layer: tick aggregation, availability, resampling, validation.

Every scenario is built so the right answer is known by construction.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from aitrader.data import instruments
from aitrader.data.bars import BarSeries
from aitrader.data.resample import bucket_start, resample
from aitrader.data.ticks import aggregate, week_openings
from aitrader.data.validate import validate


def ts(*args) -> int:
    return int(datetime(*args, tzinfo=timezone.utc).timestamp())


def series_from_mid(times, mids, spread=0.0002, symbol="EURUSD", tf="M15"):
    mids = np.asarray(mids, dtype=float)
    half = spread / 2
    return BarSeries.from_columns(
        symbol, tf, "test",
        open_time=np.asarray(times, dtype=np.int64),
        bid_open=mids - half, bid_high=mids - half + 0.0005, bid_low=mids - half - 0.0005, bid_close=mids - half,
        ask_open=mids + half, ask_high=mids + half + 0.0005, ask_low=mids + half - 0.0005, ask_close=mids + half,
        ticks=np.full(len(mids), 10), spread_mean=np.full(len(mids), spread), spread_max=np.full(len(mids), spread),
    )


# ── ticks ───────────────────────────────────────────────────────────────


def test_aggregate_builds_known_bars_and_leaves_gaps_empty():
    base = ts(2010, 1, 4, 8, 0) * 1000
    t = np.array([base, base + 1000, base + 899_000,           # bar 08:00
                  base + 1800_000 + 5])                          # bar 08:30 (08:15 empty)
    bid = np.array([1.0, 1.2, 0.9, 1.1])
    ask = bid + 0.0001
    out = aggregate(t, bid, ask, 900).columns
    assert list(out["open_time"]) == [ts(2010, 1, 4, 8, 0), ts(2010, 1, 4, 8, 30)]
    assert list(out["bid_open"]) == [1.0, 1.1]
    assert list(out["bid_high"]) == [1.2, 1.1]
    assert list(out["bid_low"]) == [0.9, 1.1]
    assert list(out["bid_close"]) == [0.9, 1.1]
    assert list(out["ticks"]) == [3, 1]
    assert out["spread_mean"][0] == pytest.approx(0.0001)


def test_invalid_ticks_are_dropped_and_counted_never_repaired():
    t = np.array([0, 1000, 2000, 3000, 4000])
    bid = np.array([1.0, np.nan, -1.0, 1.2, 1.0])
    ask = np.array([1.1, 1.1, 1.1, 1.1, 1.1])  # tick 3 is crossed (ask < bid)
    res = aggregate(t, bid, ask, 900)
    a = res.audit
    assert (a.received, a.non_finite, a.non_positive, a.crossed, a.kept) == (5, 1, 1, 1, 2)
    assert res.columns["ticks"].sum() == 2


def test_out_of_order_ticks_are_sorted_and_counted():
    t = np.array([2000, 1000, 3000])
    res = aggregate(t, np.array([1.0, 2.0, 3.0]), np.array([1.1, 2.1, 3.1]), 900)
    assert res.audit.out_of_order == 1
    assert res.columns["bid_open"][0] == 2.0 and res.columns["bid_close"][0] == 3.0


def test_week_openings_measure_the_clock():
    fri = ts(2010, 1, 8, 21, 59) * 1000
    sun = ts(2010, 1, 10, 22, 0) * 1000
    opens = week_openings(np.array([fri - 1000, fri, sun, sun + 1000]))
    assert list(opens) == [ts(2010, 1, 10, 22, 0)]


# ── availability ────────────────────────────────────────────────────────


def test_a_bar_is_available_at_its_close_not_its_open():
    t0 = ts(2015, 3, 2, 10, 0)
    s = series_from_mid([t0, t0 + 900, t0 + 1800], [1.1, 1.2, 1.3])
    assert len(s.as_of(t0 + 900)) == 1          # first bar closed at t0+900
    assert len(s.as_of(t0 + 899)) == 0          # nothing closed yet
    assert len(s.as_of(t0 + 1800)) == 2


def test_series_is_read_only():
    s = series_from_mid([0, 900], [1.1, 1.2])
    with pytest.raises(ValueError):
        s.bid_close[0] = 5.0


def test_save_load_round_trip_and_stable_hash(tmp_path):
    s = series_from_mid([0, 900, 1800], [1.1, 1.2, 1.3])
    h = s.save(tmp_path / "x.npz")
    back = BarSeries.load(tmp_path / "x.npz")
    assert back.content_hash() == h
    assert np.array_equal(back.ask_close, s.ask_close)


# ── resampling ──────────────────────────────────────────────────────────


def _m15_block(start, n, mid=1.1):
    times = [start + 900 * i for i in range(n)]
    mids = [mid + 0.0001 * i for i in range(n)]
    return series_from_mid(times, mids)


def test_resample_h1_emits_only_complete_hours():
    start = ts(2015, 3, 2, 10, 0)
    s = _m15_block(start, 6)  # 10:00..11:15 -> hour 10 complete, hour 11 forming
    h1 = resample(s, "H1", as_of=start + 6 * 900)
    assert list(h1.open_time) == [start]
    assert h1.bid_open[0] == s.bid_open[0] and h1.bid_close[0] == s.bid_close[3]
    assert h1.bid_high[0] == s.bid_high[:4].max()


def test_resample_does_not_leak_a_forming_bar_even_if_later_data_exists():
    start = ts(2015, 3, 2, 10, 0)
    s = _m15_block(start, 8)
    # as_of 10:45 close: hour 10 still forming -> nothing
    assert len(resample(s, "H1", as_of=start + 3 * 900)) == 0


def test_d1_boundary_is_the_new_york_close_and_follows_dst():
    # Winter: NY close 17:00 EST = 22:00 UTC.
    assert bucket_start(np.array([ts(2015, 1, 14, 21, 45)]), "D1")[0] == ts(2015, 1, 13, 22, 0)
    assert bucket_start(np.array([ts(2015, 1, 14, 22, 0)]), "D1")[0] == ts(2015, 1, 14, 22, 0)
    # Summer: NY close 17:00 EDT = 21:00 UTC.
    assert bucket_start(np.array([ts(2015, 7, 14, 21, 0)]), "D1")[0] == ts(2015, 7, 14, 21, 0)
    assert bucket_start(np.array([ts(2015, 7, 14, 20, 45)]), "D1")[0] == ts(2015, 7, 13, 21, 0)
    # H4 is aligned to the same close.
    assert bucket_start(np.array([ts(2015, 7, 15, 1, 30)]), "H4")[0] == ts(2015, 7, 15, 1, 0)


def test_resample_refuses_a_downsample():
    with pytest.raises(ValueError):
        resample(_m15_block(0, 4).take(slice(0, 4)).__class__.from_columns(
            "EURUSD", "H1", "t", **{f: np.array([0]) for f in (
                "open_time", "bid_open", "bid_high", "bid_low", "bid_close",
                "ask_open", "ask_high", "ask_low", "ask_close", "ticks", "spread_mean", "spread_max")}),
            "M15", as_of=10**9)


# ── validation ──────────────────────────────────────────────────────────


def test_validation_passes_clean_data_and_reports_spread():
    s = _m15_block(ts(2015, 3, 2, 10, 0), 20)
    rep = validate(s, instruments.get("EURUSD"))
    assert rep.usable, rep.hard
    assert rep.soft["spread_pips_median"] == pytest.approx(2.0)


def test_validation_refuses_a_wrong_scale():
    s = series_from_mid([0, 900], [109305.0, 109306.0], spread=10)
    rep = validate(s, instruments.get("EURUSD"))
    assert not rep.usable
    assert any("scale" in h for h in rep.hard)


def test_validation_refuses_crossed_and_disordered_bars():
    s = series_from_mid([900, 0], [1.1, 1.2], spread=-0.0002)
    rep = validate(s, instruments.get("EURUSD"))
    assert any("increasing" in h for h in rep.hard)
    assert any("ask_" in h for h in rep.hard)


def test_validation_refuses_off_grid_timestamps():
    s = series_from_mid([0, 901], [1.1, 1.2])
    assert any("grid" in h for h in validate(s, instruments.get("EURUSD")).hard)


def test_unknown_instrument_is_refused_by_name():
    with pytest.raises(KeyError, match="unknown instrument"):
        instruments.get("FOOBAR")


def test_price_scale_is_derived_and_must_be_unique():
    assert instruments.price_scale("USDJPY", 0.772) == 100.0
    assert instruments.price_scale("XAUUSD", 16.2) == 100.0
    assert instruments.price_scale("EURUSD", 1.09) == 1.0
    assert instruments.price_scale("EURUSD", 109305.0) == 1e-5
    with pytest.raises(ValueError, match="refusing"):
        instruments.price_scale("EURUSD", 3.5)  # 0.35 is below the band, 3.5 above it
