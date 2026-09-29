"""The strategy desk: the classic indicators, sixteen well-known strategies checked on the last
completed bar, and a scoreboard of how each one did on this pair's own recent history.

Information for the team, never an instruction. The team may use any of it, all of it, or none.

- Indicators: EMA 20/50/200, RSI 14, MACD 12/26/9, ADX 14 (+DI/-DI), Bollinger 20/2, Keltner
  20/1.5, Stochastic 14/3/3, Ichimoku 9/26/52, Donchian 20/55, ATR 14.
- Signals: each strategy is a rule evaluated at every bar from that bar and earlier bars only
  (windows are shifted, swings wait for their confirming bars), so "firing now" is the rule at
  the last completed bar and the scoreboard replays exactly the same rule on the past.
- Scoreboard: every past signal becomes one fixed trade (entry at the signal bar's close, paying
  the bar's spread; stop 1 x ATR, target 1.5 x ATR, closed after MAX_HOLD bars), walked forward
  bar by bar, stop first when a bar touches both. Only trades that had closed by `as_of` count;
  one trade at a time per strategy. Fewer than 30 trades is labelled insufficient: a win rate
  over a handful says nothing.

Nothing here knows the future, and nothing here is a forecast: a strategy that did well over the
last weeks may stop working this hour. The numbers say what happened, not what will.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from ..data.bars import BarSeries

DESK_VERSION = "strategy-desk-1.0.0"
STOP_ATR, TARGET_ATR = 1.0, 1.5
MAX_HOLD = {"M5": 36, "M15": 32, "H1": 24}  # bars: 3 h, 8 h, 24 h
K = 2  # swing confirmation, as in the market map

STRATEGIES = {  # name -> (family, one-line rule)
    "ema_trend_pullback": ("trend", "EMA50 above EMA200, price dips to EMA20 and closes back above it (mirror for sells)"),
    "donchian20_breakout": ("breakout", "close beyond the previous 20 bars' high/low (Turtle system 1)"),
    "donchian55_breakout": ("breakout", "close beyond the previous 55 bars' high/low (Turtle system 2)"),
    "bollinger_reversion": ("mean reversion", "close outside the 20/2 band with RSI beyond 30/70"),
    "rsi_divergence": ("reversal", "a new swing low/high that RSI does not confirm"),
    "macd_cross": ("momentum", "MACD crosses its signal line on the far side of zero"),
    "adx_di_cross": ("trend", "+DI/-DI cross while ADX is above 25"),
    "stochastic_reversal": ("mean reversion", "%K crosses %D below 20 / above 80"),
    "squeeze_breakout": ("volatility", "Bollinger inside Keltner for 5+ bars, then a close outside Bollinger"),
    "inside_bar_breakout": ("price action", "the bar after an inside bar closes beyond the mother bar"),
    "engulfing_at_extreme": ("price action", "an engulfing candle at the 20-bar low/high"),
    "pin_bar_at_extreme": ("price action", "a long-wick rejection candle at the 20-bar low/high"),
    "liquidity_sweep": ("SMC/ICT", "a wick through the previous 20 bars' low/high that closes back inside (turtle soup)"),
    "ichimoku_tk_cross": ("trend", "Tenkan crosses Kijun with price on the same side of the cloud"),
    "pivot_rejection": ("levels", "a touch of the daily S1/R1 pivot that closes back toward the pivot"),
    "fib_pullback": ("trend", "a pullback into 50-61.8% of the last swing leg that closes back with the leg"),
}


# ── indicators (causal: the value at i uses bars 0..i) ─────────────────────

def _ema(x: np.ndarray, n: int) -> np.ndarray:
    out, a = np.full(len(x), np.nan), 2 / (n + 1)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def _wilder(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = np.nanmean(x[:n])
    for i in range(n, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def _roll(x: np.ndarray, n: int, fn) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = fn(np.lib.stride_tricks.sliding_window_view(x, n), axis=1)
    return out


def _prev(x: np.ndarray) -> np.ndarray:
    return np.concatenate(([np.nan], x[:-1]))


def indicators(b: BarSeries) -> dict:
    o, h, lo, c = b.mid_open, b.mid_high, b.mid_low, b.mid_close
    pc = _prev(c)
    tr = np.nanmax(np.vstack([h - lo, np.abs(h - pc), np.abs(lo - pc)]), axis=0)
    atr = _wilder(tr, 14)
    up, dn = np.maximum(np.diff(c, prepend=c[0]), 0), np.maximum(-np.diff(c, prepend=c[0]), 0)
    ru, rd = _wilder(up, 14), _wilder(dn, 14)
    rsi = 100 - 100 / (1 + np.divide(ru, rd, out=np.full(len(c), np.inf), where=rd > 0))
    ema12, ema26 = _ema(c, 12), _ema(c, 26)
    macd = ema12 - ema26
    sig = np.full(len(c), np.nan)
    ok = ~np.isnan(macd)
    if ok.sum() >= 9:
        sig[ok] = _ema(macd[ok], 9)
    hp, lp = h - _prev(h), _prev(lo) - lo
    pdm = np.where((hp > lp) & (hp > 0), hp, 0.0)
    mdm = np.where((lp > hp) & (lp > 0), lp, 0.0)
    pdi = 100 * np.divide(_wilder(pdm, 14), atr, out=np.full(len(c), np.nan), where=atr > 0)
    mdi = 100 * np.divide(_wilder(mdm, 14), atr, out=np.full(len(c), np.nan), where=atr > 0)
    dx = 100 * np.abs(pdi - mdi) / np.where((pdi + mdi) > 0, pdi + mdi, np.nan)
    dxv = np.nan_to_num(dx, nan=0.0)
    adx = _wilder(dxv, 14)
    mid, sd = _roll(c, 20, np.mean), _roll(c, 20, np.std)
    hh14, ll14 = _roll(h, 14, np.max), _roll(lo, 14, np.min)
    k_raw = 100 * (c - ll14) / np.where(hh14 > ll14, hh14 - ll14, np.nan)
    k = _roll(np.nan_to_num(k_raw, nan=50.0), 3, np.mean)
    d = _roll(np.nan_to_num(k, nan=50.0), 3, np.mean)
    tenkan = (_roll(h, 9, np.max) + _roll(lo, 9, np.min)) / 2
    kijun = (_roll(h, 26, np.max) + _roll(lo, 26, np.min)) / 2
    span_a = np.concatenate((np.full(26, np.nan), ((tenkan + kijun) / 2)[:-26])) if len(c) > 26 else np.full(len(c), np.nan)
    span_b_raw = (_roll(h, 52, np.max) + _roll(lo, 52, np.min)) / 2
    span_b = np.concatenate((np.full(26, np.nan), span_b_raw[:-26])) if len(c) > 26 else np.full(len(c), np.nan)
    return {"open": o, "high": h, "low": lo, "close": c, "atr": atr, "rsi": rsi, "macd": macd, "macd_signal": sig,
            "adx": adx, "pdi": pdi, "mdi": mdi, "ema20": _ema(c, 20), "ema50": _ema(c, 50), "ema200": _ema(c, 200),
            "bb_mid": mid, "bb_up": mid + 2 * sd, "bb_lo": mid - 2 * sd, "kc_up": _ema(c, 20) + 1.5 * atr,
            "kc_lo": _ema(c, 20) - 1.5 * atr, "stoch_k": k, "stoch_d": d, "tenkan": tenkan, "kijun": kijun,
            "span_a": span_a, "span_b": span_b,
            "dc20_hi": _prev(_roll(h, 20, np.max)), "dc20_lo": _prev(_roll(lo, 20, np.min)),
            "dc55_hi": _prev(_roll(h, 55, np.max)), "dc55_lo": _prev(_roll(lo, 55, np.min))}


# ── signals: +1 buy, -1 sell, 0 none, for every bar, from that bar and earlier only ──

def _swing_series(h, lo, k=K):
    """For each bar i: index of the last swing low / high CONFIRMED by i (the swing at j is known at j+k)."""
    n = len(h)
    last_lo, last_hi = np.full(n, -1), np.full(n, -1)
    prev_lo, prev_hi = np.full(n, -1), np.full(n, -1)
    lows = [j for j in range(k, n - k) if lo[j] < lo[j - k:j].min() and lo[j] <= lo[j + 1:j + k + 1].min()]
    highs = [j for j in range(k, n - k) if h[j] > h[j - k:j].max() and h[j] >= h[j + 1:j + k + 1].max()]
    for arr, last, prev in ((lows, last_lo, prev_lo), (highs, last_hi, prev_hi)):
        a, b = -1, -1
        idx = 0
        for i in range(n):
            while idx < len(arr) and arr[idx] + k <= i:
                a, b = arr[idx], a
                idx += 1
            last[i], prev[i] = a, b
    return last_lo, prev_lo, last_hi, prev_hi


def signals(ind: dict, times: np.ndarray) -> dict[str, np.ndarray]:
    o, h, lo, c, atr, rsi = (ind[k] for k in ("open", "high", "low", "close", "atr", "rsi"))
    n = len(c)
    pc, ph, pl, po = _prev(c), _prev(h), _prev(lo), _prev(o)
    s: dict[str, np.ndarray] = {}

    def sig(buy, sell):
        return np.where(np.nan_to_num(buy, nan=0).astype(bool), 1, np.where(np.nan_to_num(sell, nan=0).astype(bool), -1, 0))

    e20, e50, e200 = ind["ema20"], ind["ema50"], ind["ema200"]
    s["ema_trend_pullback"] = sig((e50 > e200) & (lo <= e20) & (c > e20), (e50 < e200) & (h >= e20) & (c < e20))
    s["donchian20_breakout"] = sig(c > ind["dc20_hi"], c < ind["dc20_lo"])
    s["donchian55_breakout"] = sig(c > ind["dc55_hi"], c < ind["dc55_lo"])
    s["bollinger_reversion"] = sig((c < ind["bb_lo"]) & (rsi < 30), (c > ind["bb_up"]) & (rsi > 70))
    m, ms = ind["macd"], ind["macd_signal"]
    s["macd_cross"] = sig((m > ms) & (_prev(m) <= _prev(ms)) & (m < 0), (m < ms) & (_prev(m) >= _prev(ms)) & (m > 0))
    pdi, mdi, adx = ind["pdi"], ind["mdi"], ind["adx"]
    s["adx_di_cross"] = sig((pdi > mdi) & (_prev(pdi) <= _prev(mdi)) & (adx > 25),
                            (pdi < mdi) & (_prev(pdi) >= _prev(mdi)) & (adx > 25))
    k, d = ind["stoch_k"], ind["stoch_d"]
    s["stochastic_reversal"] = sig((k > d) & (_prev(k) <= _prev(d)) & (k < 20), (k < d) & (_prev(k) >= _prev(d)) & (k > 80))
    squeeze = (ind["bb_up"] < ind["kc_up"]) & (ind["bb_lo"] > ind["kc_lo"])
    sq5 = _roll(np.nan_to_num(squeeze.astype(float)), 5, np.min)
    was = _prev(sq5) == 1
    s["squeeze_breakout"] = sig(was & (c > ind["bb_up"]), was & (c < ind["bb_lo"]))
    inside_prev = (ph < _prev(ph)) & (pl > _prev(pl))  # bar i-1 inside bar i-2
    s["inside_bar_breakout"] = sig(inside_prev & (c > _prev(ph)), inside_prev & (c < _prev(pl)))
    lo20, hi20 = _prev(_roll(lo, 20, np.min)), _prev(_roll(h, 20, np.max))
    near_lo, near_hi = lo <= lo20 + 0.3 * atr, h >= hi20 - 0.3 * atr
    bull_eng = (c > o) & (pc < po) & (c >= po) & (o <= pc)
    bear_eng = (c < o) & (pc > po) & (c <= po) & (o >= pc)
    s["engulfing_at_extreme"] = sig(bull_eng & near_lo, bear_eng & near_hi)
    body, rng = np.abs(c - o), h - lo
    low_wick, up_wick = np.minimum(o, c) - lo, h - np.maximum(o, c)
    s["pin_bar_at_extreme"] = sig((low_wick >= 2 * body) & (c >= lo + 2 / 3 * rng) & near_lo & (rng > 0),
                                  (up_wick >= 2 * body) & (c <= lo + 1 / 3 * rng) & near_hi & (rng > 0))
    s["liquidity_sweep"] = sig((lo < lo20) & (c > lo20), (h > hi20) & (c < hi20))
    tk, kj, sa, sb = ind["tenkan"], ind["kijun"], ind["span_a"], ind["span_b"]
    top, bot = np.fmax(sa, sb), np.fmin(sa, sb)
    s["ichimoku_tk_cross"] = sig((tk > kj) & (_prev(tk) <= _prev(kj)) & (c > top),
                                 (tk < kj) & (_prev(tk) >= _prev(kj)) & (c < bot))
    # daily classic pivots from the previous UTC day's high/low/close, known from the day's first bar on
    day = (times // 86400).astype(np.int64)
    s1, r1, piv = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    days = np.unique(day)
    for di in range(1, len(days)):
        prev_m, cur_m = day == days[di - 1], day == days[di]
        H, L, C = h[prev_m].max(), lo[prev_m].min(), c[prev_m][-1]
        p = (H + L + C) / 3
        piv[cur_m], s1[cur_m], r1[cur_m] = p, 2 * p - H, 2 * p - L
    s["pivot_rejection"] = sig((lo <= s1) & (c > s1), (h >= r1) & (c < r1))
    last_lo, prev_lo, last_hi, prev_hi = _swing_series(h, lo)
    div_b, div_s, fib_b, fib_s = (np.zeros(n, bool) for _ in range(4))
    for i in range(n):
        a, b = last_lo[i], prev_lo[i]
        if a >= 0 and b >= 0 and a + K == i and lo[a] < lo[b] and rsi[a] > rsi[b]:
            div_b[i] = True  # the swing low just confirmed is lower, its RSI higher
        a, b = last_hi[i], prev_hi[i]
        if a >= 0 and b >= 0 and a + K == i and h[a] > h[b] and rsi[a] < rsi[b]:
            div_s[i] = True
        lo_i, hi_i = last_lo[i], last_hi[i]
        if lo_i >= 0 and hi_i >= 0:
            leg = h[hi_i] - lo[lo_i]
            if hi_i > lo_i and leg > 0:  # an up-leg; pullback zone below its high
                z_hi, z_lo = h[hi_i] - 0.5 * leg, h[hi_i] - 0.618 * leg
                fib_b[i] = lo[i] <= z_hi and lo[i] >= z_lo and c[i] > o[i]
            elif lo_i > hi_i and leg > 0:  # a down-leg
                z_lo, z_hi = lo[lo_i] + 0.5 * leg, lo[lo_i] + 0.618 * leg
                fib_s[i] = h[i] >= z_lo and h[i] <= z_hi and c[i] < o[i]
    s["rsi_divergence"] = sig(div_b, div_s)
    s["fib_pullback"] = sig(fib_b, fib_s)
    return s


# ── the scoreboard: every past signal as one fixed trade, walked forward ─────

def scoreboard(b: BarSeries, sig: dict[str, np.ndarray], atr: np.ndarray, max_hold: int) -> list[dict]:
    bh, bl, bc = b.bid_high, b.bid_low, b.bid_close
    ah, al, ac = b.ask_high, b.ask_low, b.ask_close
    n, rows = len(b), []
    for name, s in sig.items():
        rs, busy_until = [], -1
        for i in np.flatnonzero(s[:-1]):
            if i <= busy_until or not np.isfinite(atr[i]) or atr[i] <= 0:
                continue
            side = int(s[i])
            entry = ac[i] if side > 0 else bc[i]  # the spread is paid on entry
            stop = entry - side * STOP_ATR * atr[i]
            target = entry + side * TARGET_ATR * atr[i]
            r = None
            for j in range(i + 1, min(n, i + 1 + max_hold)):
                lo_, hi_ = (bl[j], bh[j]) if side > 0 else (al[j], ah[j])
                hit_stop = lo_ <= stop if side > 0 else hi_ >= stop
                hit_target = hi_ >= target if side > 0 else lo_ <= target
                if hit_stop:  # stop first when a bar touches both
                    r = -1.0
                elif hit_target:
                    r = TARGET_ATR / STOP_ATR
                elif j == i + max_hold:
                    exit_ = bc[j] if side > 0 else ac[j]
                    r = (exit_ - entry) * side / (STOP_ATR * atr[i])
                if r is not None:
                    busy_until = j
                    break
            if r is not None:  # still open at the last completed bar: not counted
                rs.append(r)
        m = len(rs)
        rows.append({"strategy": name, "trades": m,
                     "win_rate": round(float(np.mean(np.array(rs) > 0)), 3) if m else None,
                     "avg_R": round(float(np.mean(rs)), 3) if m else None,
                     "sample": "insufficient" if m < 30 else "limited" if m < 100 else "adequate"})
    return sorted(rows, key=lambda r: (r["avg_R"] is None, -(r["avg_R"] or 0)))


def _brief_indicators(ind: dict, d: int) -> dict:
    def v(k, nd=d):
        x = ind[k][-1]
        return None if not np.isfinite(x) else round(float(x), nd)
    c = ind["close"][-1]
    cloud_top, cloud_bot = np.fmax(ind["span_a"][-1], ind["span_b"][-1]), np.fmin(ind["span_a"][-1], ind["span_b"][-1])
    return {"ema20": v("ema20"), "ema50": v("ema50"), "ema200": v("ema200"), "rsi14": v("rsi", 1),
            "macd_hist": v("macd", d + 1) if not np.isfinite(ind["macd_signal"][-1])
            else round(float(ind["macd"][-1] - ind["macd_signal"][-1]), d + 1),
            "adx14": v("adx", 1), "plus_di": v("pdi", 1), "minus_di": v("mdi", 1),
            "bollinger": {"upper": v("bb_up"), "lower": v("bb_lo")},
            "stoch": {"k": v("stoch_k", 1), "d": v("stoch_d", 1)},
            "ichimoku": {"tenkan": v("tenkan"), "kijun": v("kijun"),
                         "price_vs_cloud": None if not np.isfinite(cloud_top) else
                         "above" if c > cloud_top else "below" if c < cloud_bot else "inside"},
            "donchian20": {"high": v("dc20_hi"), "low": v("dc20_lo")}, "atr14": v("atr", d + 1)}


_CACHE: dict = {}


def strategy_desk(symbol: str, frames: dict, as_of: int) -> dict | None:
    """The desk for `symbol` from `frames` ({"M5": BarSeries, "H1": ...}), completed bars only."""
    d = 3 if symbol.endswith("JPY") else 5
    out: dict = {"version": DESK_VERSION, "strategies": {k: f"{f}: {rule}" for k, (f, rule) in STRATEGIES.items()},
                 "indicators": {}, "firing_now": [], "scoreboard": {},
                 "note": ("scoreboard = each past signal of the rule as one fixed trade on this pair (entry at the "
                          f"signal close after spread, stop {STOP_ATR:g} ATR, target {TARGET_ATR:g} ATR, time exit), "
                          "only trades closed before now; what happened, not a forecast")}
    for tf in ("M5", "M15", "H1"):
        b = frames.get(tf)
        if b is None or len(b) == 0:
            continue
        b = b.take(slice(0, int((b.available_at <= as_of).sum())))
        if len(b) < 60:
            continue
        key = (symbol, tf, int(b.open_time[-1]), len(b), float(b.mid_close[-1]))
        hit = _CACHE.get(key)
        if hit is None:
            ind = indicators(b)
            sig = signals(ind, b.open_time)
            board = scoreboard(b, sig, ind["atr"], MAX_HOLD[tf]) if tf in ("M5", "H1") else None
            hit = (ind, sig, board)
            _CACHE[key] = hit
            if len(_CACHE) > 64:
                _CACHE.pop(next(iter(_CACHE)))
        ind, sig, board = hit
        out["indicators"][tf] = _brief_indicators(ind, d)
        for name, s in sig.items():
            if s[-1]:
                out["firing_now"].append({"strategy": name, "tf": tf, "signal": "BUY" if s[-1] > 0 else "SELL",
                                          "bar_utc": datetime.fromtimestamp(int(b.open_time[-1]), timezone.utc)
                                          .strftime("%d %H:%M")})
        if board is not None:
            span_days = round((int(b.open_time[-1]) - int(b.open_time[0])) / 86400, 1)
            out["scoreboard"][tf] = {"history_days": span_days, "bars": len(b), "max_hold_bars": MAX_HOLD[tf],
                                     "fields": ["strategy", "trades", "win_rate", "avg_R", "sample"],
                                     "rows": [[r["strategy"], r["trades"], r["win_rate"], r["avg_R"], r["sample"]]
                                              for r in board]}
    return out if out["indicators"] else None
