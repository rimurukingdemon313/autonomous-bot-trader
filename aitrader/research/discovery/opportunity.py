"""ID-2: an opportunity engine for active intraday trading (research only).

The question ID-1 could not answer: single rules have no edge after costs, but does any
COMBINATION of market information select the minority of moments where a short-term trade has a
positive expected value after costs? This module is the machine that asks it at every M5 bar,
for both sides, and lets the data decide which information matters:

    scanner (every M5 bar 07:00-19:55 UTC, BUY and SELL)
      -> causal features (momentum, reversion, breakout, structure, liquidity/SMC, volatility,
         cost, session, higher timeframes, cross-market, tick activity, memory of resolved trades)
      -> statistical edge estimate (expected NET R of a standard trade, walk-forward)
      -> selection: trade only when the estimate exceeds a declared threshold
      -> the production risk engine's entry checks and account limits
      -> EXECUTE or NO TRADE

Trade frequency is an output: the scanner proposes ~300 candidates an hour across the panel and
the estimate decides how many are worth taking, from none upwards.

Standard trade at exit scale S (S5, S15, S60: the ATR of 5-, 15- or 60-minute bars):
- decided at an M5 bar's close, entered at the next M5 open on the correct side of the quote
  (+ slippage), exactly as `intraday.simulate` fills a market signal;
- stop 1.5 x ATR_S from the signal close, target 2R, stop before target in every bar;
- flat by 20:55 UTC every day (no overnight exposure, so no financing in practice; it is still
  computed for any position that crosses the 21:00 rollover), a gap of more than an hour, or
  the scale's maximum holding (48 / 96 / 144 M5 bars).

`label` is a vectorised re-implementation of `intraday.simulate` for these trades; a test
requires the two to agree to 1e-12 on every field.

Causality: every feature at bar i uses bars <= i of its instrument and, for cross-market
features, other instruments' bars that closed by bar i's close. Higher-timeframe quantities use
completed higher-timeframe bars only. Memory features use only candidates whose exit bar is
BEFORE bar i. A truncation test enforces all of this.

Nothing here sizes a live trade: the risk engine remains the only sizing authority.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np

from aitrader.research.discovery import intraday as ID

OPP_VERSION = "opp-1.0.0"
M5 = ID.M5
STOP_ATR = 1.5
RR = 2.0
EXIT_BY = 20 * 3600 + 55 * 60  # seconds after UTC midnight: flat by 20:55 UTC
ENTRY_HOURS = (7, 20)  # decisions on bars opening 07:00-19:55 UTC, Monday to Friday
SCALES = {"S5": (5, 48), "S15": (15, 96), "S60": (60, 144)}  # ATR timeframe (minutes), max bars held
EVENT_BARS = 6  # an event counts as "recent" for this many bars (the event bar included)
MEMORY_N = 50  # resolved candidates in the memory window
MEMORY_HOUR_N = 60
GRID = 3  # memory and training use every GRID-th bar (minute % 15 == 0): overlapping labels are not new evidence
REASONS = ("target", "stop", "time", "gap")
CCY_OF = lambda s: (s[:3], s[3:])  # noqa: E731  (the risk engine's own split)


# ── higher timeframes ───────────────────────────────────────────────────

def tf_atr(b: ID.Bars, minutes: int, n: int = 14) -> np.ndarray:
    """ATR(n) of `minutes` bars built from the M5 mids, as known at each M5 bar's close: only
    higher-timeframe bars whose end time is <= this bar's close are used."""
    if minutes == 5:
        return b.atr.copy()
    sec = minutes * 60
    g = b.t // sec
    ug, start = np.unique(g, return_index=True)
    hi = np.maximum.reduceat(b.h, start)
    lo = np.minimum.reduceat(b.l, start)
    cl = b.c[np.r_[start[1:] - 1, len(b) - 1]]
    a = ID.atr(hi, lo, cl, n)
    end_t = (ug + 1) * sec
    k = np.searchsorted(end_t, b.t + M5, side="right") - 1
    return np.where(k >= 0, a[np.maximum(k, 0)], np.nan)


def tf_trend(b: ID.Bars, minutes: int, n: int = 50, slope: int = 3) -> np.ndarray:
    """`intraday.h1_trend` for any timeframe: the sign of the slope of an EMA(n) of COMPLETED
    `minutes` closes over `slope` bars; only bars that ended before this bar's own one began."""
    gid = b.t // (minutes * 60)
    groups, first = np.unique(gid, return_index=True)
    last_idx = np.r_[first[1:] - 1, len(b) - 1]
    e = ID.ema(b.c[last_idx], n)
    sl = np.full(len(groups), np.nan)
    sl[slope:] = np.sign(e[slope:] - e[:-slope])
    sl[:n] = np.nan
    k = np.searchsorted(groups, gid) - 1
    return np.where(k >= 0, sl[np.maximum(k, 0)], np.nan)


# ── small causal helpers ────────────────────────────────────────────────

def rolling_mean(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        c = np.cumsum(np.r_[0.0, x])
        out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def lag(x: np.ndarray, k: int) -> np.ndarray:
    return np.r_[np.full(k, np.nan), x[:-k]] if k else x.copy()


def recent(events: np.ndarray, k: int = EVENT_BARS) -> np.ndarray:
    """Side (+1/-1) of the most recent non-zero event in bars t-k+1..t, else 0."""
    idx = np.where(events != 0, np.arange(len(events)), -1)
    np.maximum.accumulate(idx, out=idx)
    ok = (idx >= 0) & (np.arange(len(events)) - idx < k)
    return np.where(ok, events[np.maximum(idx, 0)], 0.0)


def event_array(n: int, signals: list) -> np.ndarray:
    ev = np.zeros(n)
    for s in signals:
        ev[s.i] = s.side
    return ev


def _safe_div(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(np.isfinite(b) & (b != 0), a / b, np.nan)


# ── features ────────────────────────────────────────────────────────────

# name -> (group, kind). kind: "signed" (flips for a SELL), "plain", or "pair:<name>" (a SELL reads
# the named partner instead: distance to the high for a BUY is distance to the low for a SELL).
FEATURES: dict[str, tuple[str, str]] = {
    "mom1": ("momentum", "signed"), "mom3": ("momentum", "signed"), "mom12": ("momentum", "signed"),
    "mom48": ("momentum", "signed"), "z12": ("momentum", "signed"),
    "dev20": ("reversion", "signed"), "dev100": ("reversion", "signed"),
    "pos48": ("breakout", "signed"), "brk20": ("breakout", "signed"), "fb6": ("breakout", "signed"),
    "room_up": ("breakout", "pair:room_dn"), "room_dn": ("breakout", "pair:room_up"),
    "trend_sw": ("structure", "signed"), "bos6": ("structure", "signed"), "choch6": ("structure", "signed"),
    "d_sh": ("structure", "pair:d_sl"), "d_sl": ("structure", "pair:d_sh"),
    "sw_pd6": ("liquidity", "signed"), "sw_asia6": ("liquidity", "signed"), "sw_eq6": ("liquidity", "signed"),
    "bosfvg6": ("liquidity", "signed"), "ob6": ("liquidity", "signed"),
    "d_pdh": ("liquidity", "pair:d_pdl"), "d_pdl": ("liquidity", "pair:d_pdh"),
    "atr_rank": ("volatility", "plain"), "bbw_rank": ("volatility", "plain"), "atr_ratio": ("volatility", "plain"),
    "rng1": ("volatility", "plain"), "body1": ("volatility", "signed"),
    "hsin": ("session", "plain"), "hcos": ("session", "plain"), "dow": ("session", "plain"),
    "open30": ("session", "plain"),
    "h1tr": ("mtf", "signed"), "h4tr": ("mtf", "signed"), "d1ret": ("mtf", "signed"), "dpos": ("mtf", "signed"),
    "s60mom": ("mtf", "signed"), "s60mom4": ("mtf", "signed"),
    "usdz": ("cross", "signed"), "rel12": ("cross", "signed"), "corr288": ("cross", "plain"),
    "riskz": ("cross", "signed"),
    "tick_rel": ("volume", "plain"), "tick_mom": ("volume", "signed"),
}
# per-scale features (computed in `design`)
SCALE_FEATURES: dict[str, tuple[str, str]] = {
    "cost_r": ("cost", "plain"),
    "mem_own": ("memory", "plain"), "mem_other": ("memory", "plain"), "mem_hour": ("memory", "plain"),
    "side": ("identity", "plain"),
}
GROUPS = ("momentum", "reversion", "breakout", "structure", "liquidity", "volatility", "cost", "session", "mtf",
          "cross", "volume", "memory", "identity")


def base_features(b: ID.Bars, ticks: np.ndarray, ctx: dict | None = None) -> dict[str, np.ndarray]:
    """Every scale-independent feature, oriented for a BUY, at each bar's close. `ctx` holds the
    cross-market series aligned to this instrument (see `cross_context`); None = all NaN."""
    n = len(b)
    c, a = b.c, b.atr
    f: dict[str, np.ndarray] = {}
    for k in (1, 3, 12, 48):
        f[f"mom{k}"] = _safe_div(c - lag(c, k), a)
    f["z12"] = ID._zmove(c, 12)
    f["dev20"] = _safe_div(c - ID.ema(c, 20), a)
    f["dev100"] = _safe_div(c - ID.ema(c, 100), a)
    hi48, lo48 = ID.rolling_max(b.h, 48), ID.rolling_min(b.l, 48)
    f["pos48"] = 2 * _safe_div(c - lo48, hi48 - lo48) - 1
    ph20, pl20 = lag(ID.rolling_max(b.h, 20), 1), lag(ID.rolling_min(b.l, 20), 1)
    f["brk20"] = np.where(c > ph20, 1.0, np.where(c < pl20, -1.0, 0.0))
    f["fb6"] = recent(event_array(n, ID.failed_breakout(b)))
    hi288, lo288 = ID.rolling_max(b.h, 288), ID.rolling_min(b.l, 288)
    f["room_up"], f["room_dn"] = _safe_div(hi288 - c, a), _safe_div(c - lo288, a)
    sh1, sh2, sl1, sl2 = ID.swings(b.h, b.l, 3)
    with np.errstate(invalid="ignore"):
        f["trend_sw"] = np.where((sh1 > sh2) & (sl1 > sl2), 1.0, np.where((sh1 < sh2) & (sl1 < sl2), -1.0, 0.0))
        pc = lag(c, 1)
        up_x = (c > sh1) & (pc <= sh1)
        dn_x = (c < sl1) & (pc >= sl1)
    f["bos6"] = recent(np.where(up_x, 1.0, np.where(dn_x, -1.0, 0.0)))
    f["choch6"] = recent(event_array(n, ID.choch(b)))
    f["d_sh"], f["d_sl"] = _safe_div(sh1 - c, a), _safe_div(c - sl1, a)
    f["sw_pd6"] = recent(event_array(n, ID.sweep_pd(b)))
    f["sw_asia6"] = recent(event_array(n, ID.sweep_asia(b)))
    f["sw_eq6"] = recent(event_array(n, ID.sweep_equal(b)))
    f["bosfvg6"] = recent(event_array(n, ID.bos_fvg(b)))
    f["ob6"] = recent(event_array(n, ID.order_block(b)))
    pdh, pdl = ID.prev_day_levels(b)
    f["d_pdh"], f["d_pdl"] = _safe_div(pdh - c, a), _safe_div(c - pdl, a)
    f["atr_rank"] = ID.atr_rank(b)
    width = _safe_div(ID.rolling_std(c, 20), c)
    f["bbw_rank"] = ID.rolling_rank(np.nan_to_num(width, nan=-np.inf), 1000)
    f["bbw_rank"][~np.isfinite(width)] = np.nan
    a60 = tf_atr(b, 60)
    f["atr_ratio"] = _safe_div(a, a60)
    f["rng1"] = _safe_div(b.h - b.l, a)
    f["body1"] = _safe_div(c - b.o, a)
    hr = b.hour + b.minute / 60.0
    f["hsin"], f["hcos"] = np.sin(2 * np.pi * hr / 24), np.cos(2 * np.pi * hr / 24)
    f["dow"] = b.weekday.astype(float)
    f["open30"] = (((b.hour == 7) | (b.hour == 12)) & (b.minute < 30)).astype(float)
    f["h1tr"] = tf_trend(b, 60)
    f["h4tr"] = tf_trend(b, 240)
    days, start = np.unique(b.day, return_index=True)
    first_o = b.o[start]
    last_c = b.c[np.r_[start[1:] - 1, n - 1]]
    pdo, pdc = np.full(n, np.nan), np.full(n, np.nan)
    for k in range(1, len(days)):
        if days[k] - days[k - 1] <= 3:
            end = start[k + 1] if k + 1 < len(days) else n
            pdo[start[k]:end], pdc[start[k]:end] = first_o[k - 1], last_c[k - 1]
    f["d1ret"] = _safe_div(pdc - pdo, pdh - pdl)
    f["dpos"] = 2 * _safe_div(c - pdl, pdh - pdl) - 1
    f["s60mom"] = _safe_div(c - lag(c, 12), a60)
    f["s60mom4"] = _safe_div(c - lag(c, 48), a60)
    for k in ("usdz", "rel12", "corr288", "riskz"):
        f[k] = ctx[k] if ctx is not None and k in ctx else np.full(n, np.nan)
    tk = np.asarray(ticks, float)
    f["tick_rel"] = _safe_div(tk, rolling_mean(tk, 288))
    f["tick_mom"] = f["mom1"] * f["tick_rel"]
    assert set(f) == set(FEATURES), set(FEATURES) ^ set(f)
    return {k: v.astype(np.float32) for k, v in f.items()}


def cross_context(panel: dict[str, ID.Bars], n: int = 12) -> dict[str, dict[str, np.ndarray]]:
    """Cross-market series for every instrument, aligned to its own bars:

    - usdz: the USD index's n-bar move z (the mean USD-signed log price of the USD pairs, each
      forward-filled from its own past), signed so that + means the USD move favours a BUY of
      this instrument;
    - rel12: the instrument's own n-bar z minus the move the USD index implies for it;
    - corr288: rolling correlation (288 bars) of its one-bar moves with the implied USD moves;
    - riskz: the n-bar z of AUDJPY (log AUDUSD + log USDJPY), a risk-on/off proxy.

    Values at a bar use, for every series, the last close at or before that bar's open time:
    another instrument's bar that opens at the same time closes at the same time, so it is known."""
    sign = dict(ID.USD_SIGN)
    sign["XAUUSD"] = -1
    usd_names = [k for k in panel if k in ID.USD_SIGN]
    if len(usd_names) < 4:
        return {}
    grid = np.unique(np.concatenate([panel[k].t for k in panel]))

    def ffill(k, values):
        row = np.full(len(grid), np.nan)
        row[np.searchsorted(grid, panel[k].t)] = values
        idx = np.where(np.isfinite(row), np.arange(len(grid)), -1)
        np.maximum.accumulate(idx, out=idx)
        return np.where(idx >= 0, row[np.maximum(idx, 0)], np.nan)

    lp = np.vstack([ffill(k, ID.USD_SIGN[k] * np.log(panel[k].c)) for k in usd_names])
    present = np.isfinite(lp).sum(axis=0)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        d_n = np.nanmean(lp[:, n:] - lp[:, :-n], axis=0)
        d_1 = np.nanmean(lp[:, 1:] - lp[:, :-1], axis=0)
    mv, r1 = np.full(len(grid), np.nan), np.full(len(grid), np.nan)
    mv[n:], r1[1:] = d_n, d_1
    sd = ID.rolling_std(np.nan_to_num(r1), 288)
    usd_z = mv / (sd * math.sqrt(n))
    usd_z[present < 4] = np.nan
    risk = None
    if "AUDUSD" in panel and "USDJPY" in panel:
        lr = ffill("AUDUSD", np.log(panel["AUDUSD"].c)) + ffill("USDJPY", np.log(panel["USDJPY"].c))
        rr1 = np.r_[0.0, np.diff(lr)]
        rsd = ID.rolling_std(np.nan_to_num(rr1), 288)
        risk = np.r_[np.full(n, np.nan), lr[n:] - lr[:-n]] / (rsd * math.sqrt(n))
    out = {}
    for k, b in panel.items():
        pos = np.searchsorted(grid, b.t)
        implied = sign[k] * usd_z[pos]
        own = ID._zmove(b.c, n)
        x = np.r_[np.nan, np.diff(np.log(b.c))]
        y = sign[k] * r1[pos]
        ok = np.isfinite(x) & np.isfinite(y)
        x0, y0 = np.where(ok, x, 0.0), np.where(ok, y, 0.0)
        m = 288
        cnt = rolling_mean(ok.astype(float), m) * m
        sx, sy = rolling_mean(x0, m) * m, rolling_mean(y0, m) * m
        sxx, syy, sxy = rolling_mean(x0 * x0, m) * m, rolling_mean(y0 * y0, m) * m, rolling_mean(x0 * y0, m) * m
        with np.errstate(divide="ignore", invalid="ignore"):
            cov = sxy - sx * sy / cnt
            vx, vy = sxx - sx * sx / cnt, syy - sy * sy / cnt
            corr = np.where((cnt >= 100) & (vx > 0) & (vy > 0), cov / np.sqrt(vx * vy), np.nan)
        out[k] = {"usdz": implied, "rel12": own - implied, "corr288": corr,
                  "riskz": risk[pos] if risk is not None else np.full(len(b), np.nan)}
    return out


def candidates(b: ID.Bars) -> np.ndarray:
    """Bars the scanner evaluates: opening 07:00-19:55 UTC, Monday to Friday, with a finite ATR."""
    return np.flatnonzero(ID._window(b, *ENTRY_HOURS))


# ── labels: the standard trade, vectorised ─────────────────────────────

@dataclass
class Labels:
    """Outcome of the standard trade for each (bar i, side). status 0 = tradable and resolved;
    1 = no next bar / gap after the signal bar; 2 = no valid stop (wrong side, or no ATR yet); 3 = the risk engine's
    entry checks reject it."""

    i: np.ndarray
    side: np.ndarray
    status: np.ndarray
    entry_i: np.ndarray
    exit_i: np.ndarray
    entry: np.ndarray
    exit_px: np.ndarray
    risk: np.ndarray
    gross: np.ndarray
    spread: np.ndarray
    slippage: np.ndarray
    commission: np.ndarray
    financing: np.ndarray
    reason: np.ndarray  # index into REASONS, -1 when not traded

    @property
    def r(self) -> np.ndarray:
        with np.errstate(divide="ignore", invalid="ignore"):
            return (self.gross - self.spread - self.slippage - self.commission + self.financing) / self.risk

    def take(self, m) -> "Labels":
        return Labels(*(getattr(self, k)[m] for k in self.__dataclass_fields__))


def label(b: ID.Bars, idx: np.ndarray, side: np.ndarray, stop_dist: np.ndarray, max_bars: int,
          costs: ID.Costs = ID.Costs(), carry=None) -> Labels:
    """The standard trade for every (idx, side), filled exactly as `intraday.simulate` fills a
    market Signal(i, side, stop = c - side*stop_dist, target = c + side*RR*stop_dist, max_bars,
    deadline at EXIT_BY) on its own (no position conflicts: those belong to `portfolio`)."""
    idx = np.asarray(idx, np.int64)
    side = np.asarray(side, np.int64)
    m = len(idx)
    n = len(b)
    slip, comm = costs.slippage_pips * b.pip, costs.commission_pips_rt * b.pip
    k = costs.spread_mult - 1.0
    stop = b.c[idx] - side * stop_dist
    target = b.c[idx] + side * RR * stop_dist
    status = np.zeros(m, np.int8)
    j0 = idx + 1
    status[(j0 >= n) | b.gap_after[idx]] = 1
    j0c = np.minimum(j0, n - 1)
    w0 = (b.ao[j0c] - b.bo[j0c]) / 2 * k
    entry = np.where(side > 0, b.ao[j0c] + w0 + slip, b.bo[j0c] - w0 - slip)
    mid_in = (b.ao[j0c] + b.bo[j0c]) / 2
    risk = (entry - stop) * side
    with np.errstate(invalid="ignore"):
        status[(status == 0) & ~(risk > 0)] = 2
        spread_now = (b.ao[j0c] - b.bo[j0c]) * costs.spread_mult
        rt = spread_now + comm + 2 * slip
        reward = (target - entry) * side
        bad = ((risk < costs.min_stop_spreads * spread_now) | (spread_now > costs.max_spread_to_stop * risk)
               | (rt > costs.max_cost_to_risk * risk) | (reward < costs.min_reward_risk * risk))
    status[(status == 0) & bad] = 3
    ei = j0c
    deadline = b.utc_day[ei] * 86400 + EXIT_BY
    last = np.minimum(n - 1, ei + max_bars - 1)
    exit_px = np.full(m, np.nan)
    xi = np.full(m, -1, np.int64)
    reason = np.full(m, -1, np.int8)
    act = np.flatnonzero(status == 0)
    step = 0
    while act.size:
        j = ei[act] + step
        s = side[act]
        lg = s > 0
        w = (b.ao[j] - b.bo[j]) / 2 * k
        lo = np.where(lg, b.bl[j] - w, b.al[j] + w)
        hi = np.where(lg, b.bh[j] - w, b.ah[j] + w)
        op = np.where(lg, b.bo[j] - w, b.ao[j] + w)
        cl = np.where(lg, b.bc[j] - w, b.ac[j] + w)
        st, tg = stop[act], target[act]
        hit_s = np.where(lg, lo <= st, hi >= st)
        hit_t = ~hit_s & np.where(lg, hi >= tg, lo <= tg)
        out = (b.t[j] + M5 >= deadline[act]) | (j == last[act]) | b.gap_after[j]
        done = hit_s | hit_t | out
        px = np.where(hit_s, np.where(lg, np.minimum(op, st) - slip, np.maximum(op, st) + slip),
                      np.where(hit_t, tg, cl - s * slip))
        rs = np.where(hit_s, 1, np.where(hit_t, 0, np.where(b.gap_after[j] & (j != last[act]), 3, 2)))
        d = act[done]
        exit_px[d], xi[d], reason[d] = px[done], j[done], rs[done]
        act = act[~done]
        step += 1
    traded = status == 0
    market_exit = traded & (reason != 0)
    hx = np.maximum(xi, 0)
    half = ((b.ao[hx] - b.bo[hx]) + (b.ac[hx] - b.bc[hx])) / 4 + (b.ao[hx] - b.bo[hx]) / 2 * k
    mid_out = exit_px + side * (half + np.where(market_exit, slip, 0.0))
    gross = (mid_out - mid_in) * side
    pnl = (exit_px - entry) * side
    slippage = (1 + market_exit) * slip
    spread = gross - pnl - slippage
    fin = np.zeros(m)
    roll = b.utc_day[ei] * 86400 + ID.ROLLOVER_HOUR * 3600
    cross = np.flatnonzero(traded & (b.t[hx] + M5 >= roll))
    for q in cross:  # rare: only a position whose exit bar closes at/after 21:00 UTC
        fin[q] = ID.financing(int(b.t[ei[q]]), int(b.t[xi[q]] + M5), int(side[q]), float(entry[q]),
                              costs.markup_pa, carry)
    nan = np.where(traded, 1.0, np.nan)
    return Labels(idx, side, status, np.where(traded, ei, -1), xi, entry * nan, exit_px, risk * nan, gross * nan,
                  spread * nan, slippage * nan, np.where(traded, comm, np.nan), fin * nan, reason)


def scale_stop(b: ID.Bars, scale: str) -> np.ndarray:
    return STOP_ATR * tf_atr(b, SCALES[scale][0])


def label_scale(b: ID.Bars, idx: np.ndarray, scale: str, costs: ID.Costs = ID.Costs(), carry=None) -> Labels:
    """Both sides of every candidate bar: rows [0:len(idx)] are BUYs, [len(idx):] SELLs."""
    sd = scale_stop(b, scale)[idx]
    ii = np.r_[idx, idx]
    ss = np.r_[np.ones(len(idx), np.int64), -np.ones(len(idx), np.int64)]
    return label(b, ii, ss, np.r_[sd, sd], SCALES[scale][1], costs, carry)


# ── memory: what resolved trades taught, as known at each bar ──────────

def memory(b: ID.Bars, lab: Labels, n_own: int = MEMORY_N, n_hour: int = MEMORY_HOUR_N) -> dict[str, np.ndarray]:
    """Per bar and side: the mean net R of the last `n_own` RESOLVED grid candidates of this
    instrument on that side (exit bar strictly before the bar), and of the last `n_hour` resolved
    ones in the same UTC hour. Only tradable candidates on the GRID count."""
    n = len(b)
    r = lab.r
    grid = (b.minute[lab.i] % (5 * GRID) == 0) & (lab.status == 0)
    out = {}
    for sd, name in ((1, "long"), (-1, "short")):
        sel = np.flatnonzero(grid & (lab.side == sd))
        order = sel[np.argsort(lab.exit_i[sel], kind="stable")]
        ex, rv = lab.exit_i[order], r[order]
        cs = np.r_[0.0, np.cumsum(rv)]
        cnt = np.searchsorted(ex, np.arange(n), side="left")  # resolved strictly before bar t
        mem = np.where(cnt >= n_own, (cs[cnt] - cs[np.maximum(cnt - n_own, 0)]) / n_own, np.nan)
        out[f"mem_{name}"] = mem.astype(np.float32)
        mh = np.full(n, np.nan, np.float32)
        hrs = b.hour[lab.i[order]]
        for h in np.unique(b.hour):
            o2 = hrs == h
            ex2, cs2 = ex[o2], np.r_[0.0, np.cumsum(rv[o2])]
            bars = np.flatnonzero(b.hour == h)
            c2 = np.searchsorted(ex2, bars, side="left")
            mh[bars] = np.where(c2 >= n_hour, (cs2[c2] - cs2[np.maximum(c2 - n_hour, 0)]) / n_hour, np.nan)
        out[f"memh_{name}"] = mh
    return out


def design(base: dict[str, np.ndarray], idx: np.ndarray, side: int, cost_r: np.ndarray, mem: dict[str, np.ndarray],
           inst: int, n_inst: int, drop: tuple[str, ...] = (), only: tuple[str, ...] = ()) -> tuple[np.ndarray, list[str]]:
    """The feature matrix for candidates (idx, side), oriented to the side. `drop` / `only` remove
    or keep feature GROUPS (ablations). Instrument identity is one-hot in the identity group."""
    cols, names = [], []
    allf = {**FEATURES, **SCALE_FEATURES}

    def use(group):
        return group not in drop and (not only or group in only)

    for name, (group, kind) in FEATURES.items():
        if not use(group):
            continue
        if kind == "signed":
            cols.append(base[name][idx] * side)
        elif kind.startswith("pair:"):
            cols.append(base[name if side > 0 else kind[5:]][idx])
        else:
            cols.append(base[name][idx])
        names.append(name)
    own, other = ("long", "short") if side > 0 else ("short", "long")
    extra = {"cost_r": cost_r[idx], "mem_own": mem[f"mem_{own}"][idx], "mem_other": mem[f"mem_{other}"][idx],
             "mem_hour": mem[f"memh_{own}"][idx], "side": np.full(len(idx), float(side))}
    for name, v in extra.items():
        if use(allf[name][0]):
            cols.append(v)
            names.append(name)
    if use("identity"):
        for q in range(n_inst):
            cols.append(np.full(len(idx), float(q == inst)))
            names.append(f"inst{q}")
    return np.column_stack(cols).astype(np.float32) if cols else np.zeros((len(idx), 0), np.float32), names


def cost_ratio(b: ID.Bars, scale: str, costs: ID.Costs = ID.Costs()) -> np.ndarray:
    """Round-trip cost (the bar's closing spread + commission + 2 slippage) over the standard stop."""
    sp = (b.ac - b.bc) * costs.spread_mult
    return _safe_div(sp + (costs.commission_pips_rt + 2 * costs.slippage_pips) * b.pip, scale_stop(b, scale))


# ── the model: boosted depth-3 trees (a new declared family) ───────────

@dataclass
class Trees:
    base: float
    median: np.ndarray
    cuts: list
    trees: list  # each: (feat[7], thr_code[7], leaf[8])
    depth: int

    def codes(self, X: np.ndarray) -> np.ndarray:
        Xf = np.where(np.isnan(X), self.median, X)
        return np.vstack([np.searchsorted(self.cuts[j], Xf[:, j], side="right") for j in range(X.shape[1])]
                         ).astype(np.uint8) if X.shape[1] else np.zeros((0, len(X)), np.uint8)

    def predict(self, X: np.ndarray) -> np.ndarray:
        C = self.codes(np.asarray(X, np.float32))
        out = np.full(C.shape[1], self.base)
        rows = np.arange(C.shape[1])
        for feat, thr, leaf in self.trees:
            node = np.zeros(C.shape[1], np.int64)
            for _ in range(self.depth):
                f = feat[node]
                go = C[f, rows] > thr[node]
                node = 2 * node + 1 + go
            out += leaf[node - (2 ** self.depth - 1)]
        return out


def fit_trees(X: np.ndarray, y: np.ndarray, depth: int = 3, rounds: int = 150, shrink: float = 0.1,
              bins: int = 32, min_leaf: int = 1000) -> Trees:
    """Gradient-boosted regression trees of FIXED shape (squared error, depth 3, 150 rounds,
    shrinkage 0.1, 32 quantile bins, >= 1000 rows per leaf); deterministic. Missing inputs take the
    training median. Depth 3 lets the model express context x trigger interactions that ID-1's
    single rules and the existing stumps family cannot."""
    X = np.asarray(X, np.float32)
    y = np.asarray(y, float)
    ok = np.isfinite(y)
    X, y = X[ok], y[ok]
    n, p = X.shape
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(X, axis=0) if n else np.zeros(p)
    med = np.where(np.isfinite(med), med, 0.0).astype(np.float32)
    Xf = np.where(np.isnan(X), med, X)
    qs = np.linspace(0, 1, bins + 1)[1:-1]
    sample = Xf[:: max(1, n // 200000)]
    cuts = []
    for j in range(p):
        u = np.unique(sample[:, j])
        cuts.append(((u[:-1] + u[1:]) / 2) if len(u) <= bins else np.unique(np.quantile(sample[:, j], qs)))
    model = Trees(float(y.mean()) if n else 0.0, med, cuts, [], depth)
    C = model.codes(Xf)
    B = bins
    n_int = 2 ** depth - 1
    pred = np.full(n, model.base)
    for _ in range(rounds):
        g = y - pred
        node = np.zeros(n, np.int64)
        feat = np.zeros(n_int, np.int64)
        thr = np.full(n_int, B, np.int64)  # B = "everything goes left"
        for d in range(depth):
            lo_id = 2 ** d - 1
            nn = 2 ** d
            rel = node - lo_id
            best_gain = np.full(nn, 0.0)
            tot_s = np.bincount(rel, weights=g, minlength=nn)
            tot_c = np.bincount(rel, minlength=nn).astype(float)
            for j in range(p):
                key = rel * B + C[j]
                s = np.bincount(key, weights=g, minlength=nn * B).reshape(nn, B)
                cnt = np.bincount(key, minlength=nn * B).reshape(nn, B).astype(float)
                cs, cc = np.cumsum(s, axis=1)[:, :-1], np.cumsum(cnt, axis=1)[:, :-1]
                rs, rc = tot_s[:, None] - cs, tot_c[:, None] - cc
                valid = (cc >= min_leaf) & (rc >= min_leaf)
                with np.errstate(divide="ignore", invalid="ignore"):
                    gain = np.where(valid, cs ** 2 / cc + rs ** 2 / rc - (tot_s ** 2 / np.maximum(tot_c, 1))[:, None],
                                    -np.inf)
                bb = np.argmax(gain, axis=1)
                gb = gain[np.arange(nn), bb]
                better = gb > best_gain + 1e-12
                best_gain[better] = gb[better]
                feat[lo_id + np.flatnonzero(better)] = j
                thr[lo_id + np.flatnonzero(better)] = bb[better]
            f = feat[node]
            go = C[f, np.arange(n)] > thr[node]
            node = 2 * node + 1 + go
        leaf_id = node - n_int
        ls = np.bincount(leaf_id, weights=g, minlength=n_int + 1)
        lc = np.bincount(leaf_id, minlength=n_int + 1)
        leaf = shrink * np.where(lc > 0, ls / np.maximum(lc, 1), 0.0)
        pred += leaf[leaf_id]
        model.trees.append((feat.copy(), thr.copy(), leaf))
    return model


@dataclass
class Ridge:
    median: np.ndarray
    mean: np.ndarray
    std: np.ndarray
    w: np.ndarray
    b0: float

    def predict(self, X: np.ndarray) -> np.ndarray:
        Z = (np.where(np.isnan(X), self.median, X) - self.mean) / self.std
        return Z @ self.w + self.b0


def fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 10.0) -> Ridge:
    """`models.fit_ridge` with missing inputs set to the training median (it drops such rows,
    and most rows here have some feature undefined)."""
    X = np.asarray(X, np.float64)
    y = np.asarray(y, float)
    ok = np.isfinite(y)
    X, y = X[ok], y[ok]
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(X, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    Xf = np.where(np.isnan(X), med, X)
    mu, sd = Xf.mean(axis=0), Xf.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (Xf - mu) / sd
    b0 = float(y.mean())
    w = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (y - b0))
    return Ridge(med, mu, sd, w, b0)


FAMILIES = {"ridge": fit_ridge, "trees": fit_trees}


# ── walk-forward ────────────────────────────────────────────────────────

def walk_forward(t_entry: np.ndarray, t_exit: np.ndarray, train_mask: np.ndarray, y: np.ndarray, X_of,
                 folds: list[tuple[int, int]], fit, embargo: int = 86400, min_train: int = 1000, log=None) -> np.ndarray:
    """Predictions for rows entering in each fold [lo, hi), from a model fitted on `train_mask`
    rows whose trade EXITED before lo - embargo. `X_of(rows)` builds the design matrix of those
    rows (lazily: a fold's matrix exists only while it is used). Rows outside every fold, and
    folds with fewer than `min_train` training rows, stay NaN."""
    pred = np.full(len(y), np.nan)
    for lo, hi in folds:
        tr = np.flatnonzero(train_mask & (t_exit < lo - embargo) & np.isfinite(y))
        te = np.flatnonzero((t_entry >= lo) & (t_entry < hi))
        if len(tr) < min_train or not len(te):
            continue
        model = fit(X_of(tr), y[tr])
        pred[te] = model.predict(X_of(te))
        if log:
            log(lo, len(tr), len(te))
    return pred


# ── the portfolio: account limits of the production risk engine ────────

@dataclass(frozen=True)
class Limits:
    max_open: int = 3  # RiskLimits.max_open_positions
    max_per_currency: int = 2  # RiskLimits.max_positions_per_currency
    daily_stop_r: float = 4.0  # daily_loss_limit_pct 2.0 / risk_per_trade_pct 0.5


def portfolio(sym: np.ndarray, t_dec: np.ndarray, t_free: np.ndarray, day: np.ndarray, r: np.ndarray,
              priority: np.ndarray, eligible: np.ndarray, symbols: list[str], limits: Limits = Limits()) -> np.ndarray:
    """Greedy, chronological selection of eligible candidates under the account limits: one
    position per instrument, at most `max_open` open, at most `max_per_currency` sharing a
    currency, and no new entry on a trading day whose CLOSED trades already lost `daily_stop_r`.
    Candidates deciding at the same time are taken in descending priority. `t_dec` is the decision
    time (signal bar close = entry), `t_free` the time the position is flat (exit bar close).
    Returns the chosen row indices in decision order."""
    order = np.flatnonzero(eligible)
    order = order[np.lexsort((-priority[order], t_dec[order]))]
    ccys = [CCY_OF(s) for s in symbols]
    open_: list[tuple[int, int]] = []  # (t_free, row)
    closed: list[tuple[int, int, float]] = []  # (t_free, day, r) pending into the day's tally
    day_r: dict[int, float] = {}
    chosen = []
    for q in order:
        now = t_dec[q]
        still = []
        for tf, row in open_:
            if tf <= now:
                closed.append((tf, int(day[row]), float(r[row])))
            else:
                still.append((tf, row))
        open_ = still
        for tf, d, rv in closed:
            day_r[d] = day_r.get(d, 0.0) + rv
        closed = []
        if day_r.get(int(day[q]), 0.0) <= -limits.daily_stop_r:
            continue
        if len(open_) >= limits.max_open or any(sym[row] == sym[q] for _, row in open_):
            continue
        cq = ccys[sym[q]]
        if any(sum(1 for _, row in open_ if c in ccys[sym[row]]) >= limits.max_per_currency for c in cq):
            continue
        open_.append((int(t_free[q]), int(q)))
        chosen.append(int(q))
    return np.array(chosen, np.int64)


def to_trades(symbol: str, b: ID.Bars, lab: Labels, rows: np.ndarray) -> list[ID.Trade]:
    out = []
    r_reason = np.array(REASONS + ("",))
    for q in rows:
        ei, xi = int(lab.entry_i[q]), int(lab.exit_i[q])
        out.append(ID.Trade(symbol, int(lab.side[q]), int(lab.i[q]), ei, xi, int(b.t[ei]), int(b.t[xi]),
                            float(lab.entry[q]), float(lab.exit_px[q]), float(lab.risk[q]), float(lab.gross[q]),
                            float(lab.spread[q]), float(lab.slippage[q]), float(lab.commission[q]),
                            float(lab.financing[q]), str(r_reason[lab.reason[q]])))
    return out


# ── the decision record an AI layer would read ─────────────────────────

@dataclass(frozen=True)
class Opportunity:
    """One scanner decision, with the evidence behind it. This is the structured packet a later
    AI layer is given: it may veto (NO TRADE); it can never change the numbers, which come from the
    model and the risk engine."""

    symbol: str
    bar_time: int
    side: int  # +1 BUY, -1 SELL, 0 NO TRADE
    expected_r: float | None  # the model's net-R estimate (None = no estimate)
    entry_ref: float
    stop: float
    target: float
    max_hold_bars: int
    exit_by_utc: str
    scale: str
    reasons: tuple[str, ...]  # the largest feature contributions, for the record
    invalidation: str  # the stop, stated as the condition that ends the trade


__all__ = ["EXIT_BY", "FAMILIES", "FEATURES", "GROUPS", "Labels", "Limits", "OPP_VERSION", "Opportunity", "SCALES",
           "SCALE_FEATURES", "Trees", "base_features", "candidates", "cost_ratio", "cross_context", "design",
           "fit_ridge", "fit_trees", "label", "label_scale", "memory", "portfolio", "scale_stop", "tf_atr",
           "tf_trend", "to_trades", "walk_forward"]
