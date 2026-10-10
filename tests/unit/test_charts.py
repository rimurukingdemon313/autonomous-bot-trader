"""The chart Trader 1 reads: a valid PNG, the same bytes from the same bars, nothing from a bar after the
decision time, and marks found by walking forward (a swing exists only once its confirming bars closed)."""

from __future__ import annotations

import struct
import zlib

import numpy as np
import pytest

from aitrader.charts.annotate import annotate
from aitrader.charts.canvas import decode_png_size, encode_png
from aitrader.charts.render import HEIGHT, WIDTH, render_chart
from aitrader.data.resample import resample

from tests.integration.test_pipeline import START, market
from tests.unit.test_market_map import bars, flat


def h1():
    return market("EURUSD", START, 24 * 30, 7, 1.10)


def draw(series, t):
    return render_chart("EURUSD", series, resample(series, "H4", as_of=t), as_of=t, bid=1.1, ask=1.10008,
                        h1_atr=0.0015, levels={"previous_day": {"high": 1.105, "low": 1.095}})


def pixels(png: bytes) -> np.ndarray:
    """Decode our own PNG (8-bit RGB, filter 0) back to pixels."""
    w, h = decode_png_size(png)
    pos, idat = 8, b""
    while pos < len(png):
        n = struct.unpack(">I", png[pos:pos + 4])[0]
        kind = png[pos + 4:pos + 8]
        if kind == b"IDAT":
            idat += png[pos + 8:pos + 8 + n]
        pos += 12 + n
    raw = np.frombuffer(zlib.decompress(idat), dtype=np.uint8).reshape(h, 1 + 3 * w)
    assert (raw[:, 0] == 0).all()
    return raw[:, 1:].reshape(h, w, 3)


def test_the_chart_is_a_valid_png_of_the_declared_size_with_candles_drawn():
    s = h1()
    t = int(s.available_at[-1])
    ch = draw(s, t)
    assert ch.png[:8] == b"\x89PNG\r\n\x1a\n" and decode_png_size(ch.png) == (WIDTH, HEIGHT)
    px = pixels(ch.png)
    green = ((px[:, :, 0] == 38) & (px[:, :, 1] == 166) & (px[:, :, 2] == 91)).sum()
    red = ((px[:, :, 0] == 214) & (px[:, :, 1] == 48) & (px[:, :, 2] == 49)).sum()
    assert green > 500 and red > 500  # up and down candles are on it
    assert ch.data_url().startswith("data:image/png;base64,") and ch.meta["sha256"] and ch.meta["bytes"] == len(ch.png)
    assert ch.facts["execution_timeframe"] == "H1" and ch.facts["higher_timeframe"] == "H4"
    assert ch.facts["entry_zone"]["low"] < 1.1 < 1.10008 < ch.facts["entry_zone"]["high"]


def test_the_same_bars_give_the_same_bytes():
    s = h1()
    t = int(s.available_at[-1])
    assert draw(s, t).png == draw(s, t).png


def test_bars_after_the_decision_time_change_nothing():
    s = h1()
    t = int(s.available_at[-50])
    truncated = s.as_of(t)
    with_future = draw(s, t)  # the series holds 49 more bars that closed after t
    assert with_future.png == draw(truncated, t).png and with_future.facts == draw(truncated, t).facts
    assert with_future.meta["last_bar_available"] <= t


def test_too_few_completed_bars_is_refused_not_drawn():
    s = h1()
    with pytest.raises(ValueError):
        render_chart("EURUSD", s, None, as_of=int(s.available_at[10]), bid=1.1, ask=1.1001, h1_atr=0.001)


def test_a_swing_is_marked_only_once_its_confirming_bars_have_closed():
    up = [[1.1000 + 0.0002 * i, 1.1003 + 0.0002 * i, 1.0998 + 0.0002 * i, 1.1002 + 0.0002 * i] for i in range(10)]
    top = up[-1][1]
    down = [[top - 0.0004, top - 0.0002, top - 0.0008, top - 0.0006], [top - 0.0006, top - 0.0004, top - 0.0010, top - 0.0008]]
    series = bars("H1", flat(10) + up + down)
    one_after = annotate(series.take(slice(0, len(series) - 1)))  # only 1 confirming bar closed
    two_after = annotate(series)
    peak = len(flat(10)) + len(up) - 1
    assert not any(p["i"] == peak and p["kind"] == "high" for p in one_after["swings"])
    assert any(p["i"] == peak and p["kind"] == "high" and p["confirmed_at"] == peak + 2 for p in two_after["swings"])


def test_fvg_status_is_walked_forward_and_labelled_on_the_chart_facts():
    base = flat(20)
    gap = [[1.1000, 1.1004, 1.0998, 1.1002], [1.1002, 1.1030, 1.1001, 1.1028], [1.1028, 1.1034, 1.1012, 1.1030]]
    above = [[1.1030, 1.1036, 1.1020, 1.1030]] * 5
    a = annotate(bars("H1", base + gap + above))
    g = next(f for f in a["fvgs"] if f["side"] == "bullish")
    assert (round(g["low"], 4), round(g["high"], 4), g["status"]) == (1.1004, 1.1012, "open")
    filled = annotate(bars("H1", base + gap + above + [[1.1030, 1.1031, 1.0999, 1.1025]]))
    assert next(f for f in filled["fvgs"] if round(f["low"], 4) == 1.1004)["status"] == "filled"


def test_png_encoder_round_trips_exact_pixels():
    px = np.random.default_rng(1).integers(0, 256, size=(7, 5, 3), dtype=np.uint8)
    assert (pixels(encode_png(px)) == px).all()
