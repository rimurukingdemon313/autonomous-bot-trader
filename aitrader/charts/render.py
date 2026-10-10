"""The chart image Agent 1 (the vision analyst) reads: one PNG, two panels, every annotation labelled.

    header       instrument, timeframes, decision time, bid/ask/spread, trend per panel, ATR, volatility
    upper panel  the execution timeframe (M15 when the broker has enough of it, else H1): candles, confirmed
                 swings (HH/HL/LH/LL), BOS/CHoCH, the order block, fair value gaps, equal highs/lows,
                 sweeps, displacement candles, support/resistance, previous day/week levels, the price and
                 the entry zone
    lower panel  the higher timeframe (H4 from completed H1 bars): candles, swings, structure, S/R, price
    legend       what every colour and mark means

Built from completed bars only (`available_at <= as_of`): the same data the judge reads as numbers. The
same bars always give the same bytes (no randomness, no clock), and bars after `as_of` change nothing.
`facts` lists every drawn mark with its price, so no agent has to read a price off pixels.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from ..data.bars import BarSeries
from . import font
from .annotate import ANNOTATE_VERSION, annotate
from .canvas import Canvas

RENDER_VERSION = "chart-render-1.0.0"
WIDTH, HEIGHT = 1280, 1000
X0, XC, X1, AXIS = 12, 870, 1150, 1158  # candles X0..XC, labels XC..X1, price axis after X1
EXEC_TOP, EXEC_BOTTOM = 76, 640
HTF_TOP, HTF_BOTTOM = 690, 890
WINDOW = 300  # bars annotated per panel (structure needs history); fewer are shown

INK, MUTED, GRID = (20, 20, 20), (110, 110, 110), (232, 232, 232)
UP, DOWN = (38, 166, 91), (214, 48, 49)
BULL, BEAR = (25, 118, 210), (230, 115, 0)
FVG_BULL, FVG_BEAR = (0, 150, 136), (156, 39, 176)
OB_DEMAND, OB_SUPPLY = (46, 125, 50), (198, 40, 40)
LIQ, DISP, SR, LEVEL, SWEEP = (176, 128, 0), (255, 170, 0), (125, 125, 125), (13, 71, 161), (123, 31, 162)
ENTRY = (255, 224, 50)
WHITE = (255, 255, 255)


@dataclass(frozen=True)
class Chart:
    png: bytes
    facts: dict
    meta: dict = field(default_factory=dict)

    def data_url(self) -> str:
        return "data:image/png;base64," + base64.b64encode(self.png).decode()


def completed(bars: BarSeries | None, as_of: int) -> BarSeries | None:
    if bars is None or len(bars) == 0:
        return None
    n = int((bars.available_at <= as_of).sum())
    return bars.take(slice(max(0, n - WINDOW), n)) if n else None


def digits(price: float) -> int:
    return 2 if price >= 1000 else 3 if price >= 50 else 5


def _when(ts) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%d %H:%M")


class _Panel:
    def __init__(self, cv: Canvas, bars: BarSeries, show: int, top: int, bottom: int, extra: list[float]) -> None:
        self.cv, self.bars, self.top, self.bottom = cv, bars, top, bottom
        self.n = len(bars)
        self.start = max(0, self.n - show)
        self.slot = (XC - X0) / max(1, self.n - self.start)
        hi = float(bars.mid_high[self.start:].max())
        lo = float(bars.mid_low[self.start:].min())
        for p in extra:
            if p is not None and np.isfinite(p):
                hi, lo = max(hi, p), min(lo, p)
        pad = (hi - lo) * 0.06 or abs(hi) * 1e-4 or 1e-4
        self.hi, self.lo = hi + pad, lo - pad
        self.labels: list[tuple[float, str, tuple, tuple]] = []

    def x(self, i: float) -> float:
        return X0 + (i - self.start + 0.5) * self.slot

    def y(self, p: float) -> float:
        return self.top + (self.hi - p) / (self.hi - self.lo) * (self.bottom - self.top)

    def visible(self, p: float) -> bool:
        return self.lo <= p <= self.hi

    def label(self, p: float, text: str, fg, bg=WHITE) -> None:
        self.labels.append((self.y(p), text, fg, bg))

    def grid(self, d: int) -> None:
        cv = self.cv
        cv.frame(X0 - 1, self.top - 1, X1 + 1, self.bottom + 1, (200, 200, 200))
        for k in range(7):
            p = self.lo + (self.hi - self.lo) * k / 6
            y = self.y(p)
            cv.hline(y, X0, X1, GRID)
            cv.text(AXIS, y - 7, f"{p:.{d}f}", MUTED, 2)
        for k in range(6):
            i = self.start + int(round(k * (self.n - 1 - self.start) / 5))
            cv.vline(self.x(i), self.top, self.bottom, GRID)
            cv.text(min(max(X0, self.x(i) - 47), XC - 94), self.bottom + 6, _when(self.bars.open_time[i]), MUTED, 2)

    def candles(self) -> None:
        o, h, lo, c = self.bars.mid_open, self.bars.mid_high, self.bars.mid_low, self.bars.mid_close
        half = max(1.0, self.slot * 0.34)
        wick = 2 if self.slot >= 9 else 1
        for i in range(self.start, self.n):
            col = UP if c[i] >= o[i] else DOWN
            x = self.x(i)
            self.cv.vline(x - wick // 2, self.y(h[i]), self.y(lo[i]) + 1, col, wick)
            y0, y1 = sorted((self.y(o[i]), self.y(c[i])))
            self.cv.rect(x - half, y0, x + half + 1, max(y1, y0 + 1), col)

    def flush_labels(self) -> None:
        """Labels in the column right of the candles, pushed apart so none covers another or a candle."""
        placed: list[float] = []
        for y, text, fg, bg in sorted(self.labels, key=lambda z: z[0]):
            y = min(max(y - 7, self.top + 2), self.bottom - 16)
            while any(abs(y - q) < 17 for q in placed):
                y += 17
            if y > self.bottom - 14:
                continue
            placed.append(y)
            self.cv.text(XC + 8, y, text[:22], fg, 2, bg=bg)


def _draw_structure(pn: _Panel, ann: dict, full: bool) -> None:
    cv, s = pn.cv, pn.start
    for e in [e for e in ann["events"] if e["at"] >= s][-4 if full else -2:]:
        col = BULL if e["dir"] == "bullish" else BEAR
        xa, xb = pn.x(max(e["swing"], s)), pn.x(e["at"])
        y = pn.y(e["level"])
        cv.hline(y, xa, xb, col, 2, dash=4)
        tag = "BOS" if e["kind"] == "BOS" else "CHOCH"
        cv.text((xa + xb) / 2 - font.width(tag, 2) / 2, y - 18 if e["dir"] == "bullish" else y + 5, tag, col, 2,
                bg=WHITE, pad=1)
    shown = [p for p in ann["swings"] if p["i"] >= s]
    for p in shown:
        x = pn.x(p["i"])
        if p["kind"] == "high":
            cv.triangle(x, pn.y(p["price"]) - 4, 7, INK, up=False)
        else:
            cv.triangle(x, pn.y(p["price"]) + 4, 7, INK, up=True)
    for p in shown[-8 if full else -6:]:
        x = pn.x(p["i"])
        y = pn.y(p["price"]) - 28 if p["kind"] == "high" else pn.y(p["price"]) + 13
        cv.text(x - font.width(p["label"], 2) / 2, y, p["label"], INK, 2)


def render_chart(symbol: str, exec_bars: BarSeries, htf_bars: BarSeries | None, *, as_of: int, bid: float,
                 ask: float, h1_atr: float | None, levels: dict | None = None, show: int = 100,
                 htf_show: int = 60, entry_atr: float = 0.5) -> Chart:
    ex = completed(exec_bars, as_of)
    if ex is None or len(ex) < 20:
        raise ValueError(f"not enough completed {getattr(exec_bars, 'timeframe', '?')} bars for a chart")
    hx = completed(htf_bars, as_of) if htf_bars is not None else None
    if hx is not None and len(hx) < 12:
        hx = None
    d = digits(float(ex.mid_close[-1]))
    a_ex = annotate(ex)
    a_hx = annotate(hx) if hx is not None else None
    zone_atr = h1_atr if h1_atr and np.isfinite(h1_atr) and h1_atr > 0 else a_ex["atr"]
    zone = (bid - entry_atr * zone_atr, ask + entry_atr * zone_atr)
    cv = Canvas(WIDTH, HEIGHT)

    # header
    t_txt = datetime.fromtimestamp(int(as_of), timezone.utc).strftime("%Y-%m-%d %H:%M")
    htf_tf = hx.timeframe if hx is not None else "NONE"
    cv.text(X0, 10, f"{symbol}  {ex.timeframe} EXECUTION / {htf_tf} CONTEXT  {t_txt} UTC", INK, 3)
    spread = ask - bid
    cv.text(X0, 42, f"BID {bid:.{d}f}  ASK {ask:.{d}f}  SPREAD {spread:.{d}f}   TREND {ex.timeframe}: {a_ex['trend']}"
            + (f"  {htf_tf}: {a_hx['trend']}" if a_hx else ""), INK, 2)
    cv.text(X0, 60, f"ATR14 {ex.timeframe} {a_ex['atr']:.{d}f}" + (f"  ATR H1 {h1_atr:.{d}f}" if h1_atr else "")
            + f"   VOLATILITY {a_ex['volatility'] or 'N/A'}"
            + (f" (ATR PERCENTILE {a_ex['atr_percentile']})" if a_ex["atr_percentile"] is not None else ""), MUTED, 2)

    # execution panel
    pn = _Panel(cv, ex, show, EXEC_TOP, EXEC_BOTTOM, [bid, ask])
    pn.grid(d)
    cv.blend(X0, pn.y(zone[1]), X1, pn.y(zone[0]), ENTRY, 0.16)
    pn.label(zone[1], f"ENTRY {zone[0]:.{d}f}-{zone[1]:.{d}f}", INK, (255, 244, 170))
    live_fvgs = sorted([f for f in a_ex["fvgs"] if f["status"] != "filled"],
                       key=lambda f: abs((f["low"] + f["high"]) / 2 - bid))[:4]
    for f in live_fvgs:
        col = FVG_BULL if f["side"] == "bullish" else FVG_BEAR
        xa = pn.x(max(f["i"], pn.start)) - pn.slot / 2
        cv.blend(xa, pn.y(f["high"]), X1, pn.y(f["low"]), col, 0.20)
        if pn.visible((f["low"] + f["high"]) / 2):
            pn.label((f["low"] + f["high"]) / 2, f"FVG {'BULL' if f['side'] == 'bullish' else 'BEAR'} "
                     f"{f['status'].upper()}", col)
    ob = a_ex["order_block"]
    if ob is not None and ob["end"] >= pn.start:
        col = OB_DEMAND if ob["side"] == "demand" else OB_SUPPLY
        xa, xb = pn.x(max(ob["i"], pn.start)) - pn.slot / 2, (pn.x(ob["end"]) if ob["status"] == "broken" else X1)
        cv.blend(xa, pn.y(ob["high"]), xb, pn.y(ob["low"]), col, 0.22)
        cv.frame(xa, pn.y(ob["high"]), xb, pn.y(ob["low"]) + 1, col)
        if pn.visible((ob["low"] + ob["high"]) / 2):
            pn.label((ob["low"] + ob["high"]) / 2, f"OB {ob['side'].upper()} {ob['status'].upper()}", col)
    for s in sorted(a_ex["sr"], key=lambda z: abs(z["level"] - bid))[:4]:
        if pn.visible(s["level"]):
            cv.hline(pn.y(s["level"]), X0, X1, SR, 1)
            pn.label(s["level"], f"{'R' if s['level'] > bid else 'S'} {s['level']:.{d}f} X{s['touches']}", SR)
    for p in sorted(a_ex["pools"], key=lambda z: abs(z["level"] - bid))[:3]:
        if pn.visible(p["level"]):
            cv.hline(pn.y(p["level"]), pn.x(max(p["i"], pn.start)), X1, LIQ, 2, dash=6)
            pn.label(p["level"], f"{p['kind']} X{p['touches']} LIQUIDITY", LIQ)
    for key, tag in (("previous_day", "PD"), ("previous_week", "PW")):
        lv = (levels or {}).get(key) or {}
        for side, suffix in (("high", "H"), ("low", "L")):
            v = lv.get(side)
            if isinstance(v, (int, float)) and pn.visible(v):
                cv.hline(pn.y(v), X0, X1, LEVEL, 1, dash=3)
                pn.label(v, f"{tag}{suffix} {v:.{d}f}", LEVEL)
    pn.candles()
    for e in [e for e in a_ex["displacement"] if e["i"] >= pn.start]:
        x = pn.x(e["i"])
        cv.rect(x - pn.slot * 0.4, EXEC_BOTTOM - 7, x + pn.slot * 0.4 + 1, EXEC_BOTTOM - 2, DISP)
    _draw_structure(pn, a_ex, True)
    recent = [s for s in a_ex["sweeps"] if s["at"] >= pn.start][-3:]
    for k, sw in enumerate(recent):
        x, y = pn.x(sw["at"]), pn.y(sw["tip"])
        cv.line(x - 5, y - 5, x + 5, y + 5, SWEEP, 2)
        cv.line(x - 5, y + 5, x + 5, y - 5, SWEEP, 2)
        if k == len(recent) - 1:  # one label: the marks are explained by the legend
            cv.text(x - 30, y - 24 if sw["side"] == "highs" else y + 10, "SWEEP", SWEEP, 2, bg=WHITE, pad=1)
    cv.hline(pn.y(ask), X0, X1, MUTED, 1, dash=5)
    cv.hline(pn.y(bid), X0, X1, INK, 2)
    cv.text(AXIS, pn.y(bid) - 7, f"{bid:.{d}f}", WHITE, 2, bg=INK)
    pn.flush_labels()
    cv.text(X0 + 4, EXEC_TOP + 4, f"{ex.timeframe} (EXECUTION)", INK, 2, bg=WHITE)

    # higher-timeframe panel
    if hx is not None:
        hp = _Panel(cv, hx, htf_show, HTF_TOP, HTF_BOTTOM, [bid])
        hp.grid(d)
        for s in sorted(a_hx["sr"], key=lambda z: abs(z["level"] - bid))[:3]:
            if hp.visible(s["level"]):
                cv.hline(hp.y(s["level"]), X0, X1, SR, 1)
                hp.label(s["level"], f"{'R' if s['level'] > bid else 'S'} {s['level']:.{d}f}", SR)
        hp.candles()
        _draw_structure(hp, a_hx, False)
        cv.hline(hp.y(bid), X0, X1, INK, 1)
        hp.flush_labels()
        cv.text(X0, HTF_TOP - 20, f"{hx.timeframe} (HIGHER TIMEFRAME)  TREND {a_hx['trend']}", INK, 2)
    else:
        cv.text(X0, HTF_TOP + 60, "HIGHER TIMEFRAME: NOT ENOUGH COMPLETED BARS", MUTED, 2)

    legend = ["CANDLES GREEN/RED = UP/DOWN (COMPLETED BARS ONLY)  TRIANGLES = CONFIRMED SWINGS",
              "BOS/CHOCH = STRUCTURE BREAK (BLUE BULLISH, ORANGE BEARISH)  X = LIQUIDITY SWEEP",
              "TEAL/PURPLE = BULL/BEAR FVG  GREEN/RED BOX = ORDER BLOCK  GOLD DASH = EQUAL HIGHS/LOWS",
              "GOLD BAR = DISPLACEMENT  GRAY = S/R  BLUE DOTS = PREV DAY/WEEK  YELLOW = ENTRY ZONE"]
    for k, line in enumerate(legend):
        cv.text(X0, 918 + 19 * k, line, MUTED, 2)

    png = cv.png()

    def r(x):
        return None if x is None else round(float(x), d)

    s0 = pn.start
    facts = {
        "execution_timeframe": ex.timeframe, "higher_timeframe": hx.timeframe if hx is not None else None,
        "bars_shown": {"execution": ex.timeframe and len(ex) - s0, "higher": (len(hx) - hp.start) if hx is not None else 0},
        "last_completed_bar": _when(ex.open_time[-1]), "price": {"bid": r(bid), "ask": r(ask), "spread": r(spread)},
        "trend": {ex.timeframe: a_ex["trend"], **({hx.timeframe: a_hx["trend"]} if a_hx else {})},
        "atr14_execution": r(a_ex["atr"]), "atr_h1": r(h1_atr), "volatility": a_ex["volatility"],
        "atr_percentile": a_ex["atr_percentile"],
        "entry_zone": {"low": r(zone[0]), "high": r(zone[1]),
                       "rule": f"market order: an entry must be within {entry_atr} H1 ATR of the executable price"},
        "structure_breaks": [{"kind": e["kind"], "direction": e["dir"], "level": r(e["level"]),
                              "bars_ago": len(ex) - 1 - e["at"]} for e in a_ex["events"][-4:]],
        "swings": [{"label": p["label"], "price": r(p["price"]), "bars_ago": len(ex) - 1 - p["i"]}
                   for p in a_ex["swings"][-8:]],
        "order_block": (None if ob is None else {"side": ob["side"], "low": r(ob["low"]), "high": r(ob["high"]),
                                                 "status": ob["status"]}),
        "fair_value_gaps": [{"side": f["side"], "low": r(f["low"]), "high": r(f["high"]), "status": f["status"]}
                            for f in live_fvgs],
        "liquidity": [{"kind": p["kind"], "level": r(p["level"]), "touches": p["touches"]} for p in a_ex["pools"][:4]],
        "sweeps": [{"side": s["side"], "signal": s["signal"], "level": r(s["level"]), "bars_ago": len(ex) - 1 - s["at"]}
                   for s in a_ex["sweeps"][-3:]],
        "support_resistance": [{"level": r(s["level"]), "touches": s["touches"]}
                               for s in sorted(a_ex["sr"], key=lambda z: abs(z["level"] - bid))[:5]],
        "displacement": [{"direction": e["dir"], "bars_ago": len(ex) - 1 - e["i"]} for e in a_ex["displacement"][-3:]],
        "higher_timeframe_breaks": ([{"kind": e["kind"], "direction": e["dir"], "level": r(e["level"])}
                                     for e in a_hx["events"][-2:]] if a_hx else []),
        "levels": {k: v for k, v in (levels or {}).items() if k in ("previous_day", "previous_week", "today")},
    }
    meta = {"version": RENDER_VERSION, "annotate_version": ANNOTATE_VERSION, "width": WIDTH, "height": HEIGHT,
            "bytes": len(png), "sha256": hashlib.sha256(png).hexdigest(), "as_of": int(as_of),
            "execution_timeframe": ex.timeframe, "higher_timeframe": facts["higher_timeframe"],
            "last_bar_open": int(ex.open_time[-1]), "last_bar_available": int(ex.available_at[-1])}
    return Chart(png, facts, meta)
