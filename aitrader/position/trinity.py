"""TRINITY-MASTER, the owner's package of 2026-11-21, as a strategy that proposes (docs/TRINITY.md).

The source is kept as received in research/external/trinity/ (trinity_omega_suite.py, sha256 de0d1596...). Its four
weight functions and its drawdown brake are copied here VERBATIM: only their names changed, and the module's own
names they read (ASSETS, math). tests/unit/test_trinity.py checks, row by row, that these return exactly what the
package's own functions return on the package's own panel, so the rules cannot drift from what the owner sent.

What it is, by the record (research/results/TRINITY-MASTER-redteam.json): a backtest on 288 three-weekly closes the
package chose, with 119 hand-set constants. Nothing about it was preregistered or judged on data its author had not
seen. Its status is EXPERIMENTAL: it may trade only on paper, sized by the risk engine like any unvalidated rule.

What this module adds, each item from the package's own handoff spec:
- the grid: every 15th trading day from an anchor (the spec's "1 bar = 15 trading days");
- the sensors (the VIX, TLT, UUP) at the close of the trading day BEFORE each grid day (the spec's "t-1"); the
  package read them on the grid day itself;
- the map from the package's assets to the CFDs an account would trade (QQQ -> NAS100, SPY -> US500, GLD -> XAUUSD,
  DBC -> USOIL).

A weight is a proposal, never a size (CLAUDE.md rules 2 and 14): the desk turns a weight above the package's own
threshold (1e-4) into a BUY with the package's 3.2% stop, and the risk engine sizes it. The weights at their own size
are measured as the design book (`design_book`), which is never traded.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Dict

TRINITY_VERSION = "trinity-1.0.0"
SOURCE_SHA256 = "de0d1596b0cf69ba92fd93a610607ec1b18e1d17bca4430c87269b0390eebd1b"
ASSETS = ("QQQ", "SPY", "GLD", "DBC")
SENSORS = ("VIX", "TLT", "UUP")
#: the package's CTRADER_SYMBOL_MAP, canonical names only
CFD_OF = {"QQQ": "NAS100", "SPY": "US500", "GLD": "XAUUSD", "DBC": "USOIL"}
STEP = 15  # trading days per grid bar (the package's DAILY_LOOKBACK_EQUIVALENTS)
WARMUP = 10  # rows before the first decision (the package's panel.iloc[10:])
STOP_REL = 0.032  # the package's protective stop (build_hard_gate_orders)
MIN_WEIGHT = 1e-4  # the package's adapter ignores weights at or below this
COST = 0.0008  # the package's cost per unit of weight changed (COST_BPS_DEFAULT)


# ── the grid and its features ──────────────────────────────────────────────

def grid(days: list[date], anchor: date, step: int = STEP) -> list[date]:
    """Every `step`-th trading day of `days` (sorted, unique) that is `anchor` or a multiple of `step` trading days
    before or after it. The anchor must be one of the days."""
    if anchor not in days:
        raise ValueError(f"the anchor {anchor} is not a trading day of the series")
    i0 = days.index(anchor)
    return [d for i, d in enumerate(days) if (i - i0) % step == 0]


def rows_at(grid_days: list[date], closes: dict[str, dict[date, float]], days: list[date]) -> list[dict]:
    """The package's base panel on the grid: each asset's close on the grid day, each sensor's close on the trading
    day before it (t-1). A grid day without every value is not a row: an incomplete row is never filled."""
    pos = {d: i for i, d in enumerate(days)}
    out = []
    for g in grid_days:
        i = pos[g]
        if i == 0:
            continue
        prev = days[i - 1]
        row = {"date": g}
        ok = True
        for a in ASSETS:
            v = closes.get(a, {}).get(g)
            ok = ok and isinstance(v, float) and math.isfinite(v) and v > 0
            row[a] = v
        for s in SENSORS:
            v = closes.get(s, {}).get(prev)
            ok = ok and isinstance(v, float) and math.isfinite(v) and v > 0
            row[s] = v
        if not ok:
            raise ValueError(f"{g}: a close is missing for the grid row (assets on {g}, sensors on {prev})")
        out.append(row)
    return out


def _nan_list(n: int) -> list[float]:
    return [math.nan] * n


def _pct(x: list[float], k: int) -> list[float]:
    """pandas' pct_change(k): x[t] / x[t-k] - 1, NaN before k."""
    return [math.nan if t < k else x[t] / x[t - k] - 1.0 for t in range(len(x))]


def _mean(x: list[float], n: int) -> list[float]:
    """pandas' rolling(n).mean(): NaN until n values, NaN if any of them is NaN."""
    out = _nan_list(len(x))
    for t in range(n - 1, len(x)):
        w = x[t - n + 1:t + 1]
        if not any(math.isnan(v) for v in w):
            out[t] = sum(w) / n
    return out


def _std(x: list[float], n: int) -> list[float]:
    """pandas' rolling(n).std(): the sample standard deviation (ddof 1), NaN until n values or if any is NaN."""
    out = _nan_list(len(x))
    for t in range(n - 1, len(x)):
        w = x[t - n + 1:t + 1]
        if any(math.isnan(v) for v in w):
            continue
        m = sum(w) / n
        out[t] = math.sqrt(sum((v - m) ** 2 for v in w) / (n - 1))
    return out


def features(rows: list[dict]) -> list[dict]:
    """The package's feature block (build_20yr_panel), the same definitions, without pandas: each row gains the
    columns the weight functions read. Row i reads rows 0..i only."""
    n = len(rows)
    out = [dict(r) for r in rows]
    for col in ("QQQ", "SPY", "GLD", "DBC", "UUP", "TLT"):
        x = [float(r[col]) for r in rows]
        r1, r3, r6 = _pct(x, 1), _pct(x, 3), _pct(x, 6)
        mas = {k: _mean(x, k) for k in (3, 4, 5, 8, 10)}
        vol6 = [v if math.isnan(v) else max(v, 0.015) for v in _std(r1, 6)]
        for i in range(n):
            o = out[i]
            o[f"{col}_r1"], o[f"{col}_r3"], o[f"{col}_r6"] = r1[i], r3[i], r6[i]
            for k, s in mas.items():
                o[f"{col}_ma{k}"] = s[i]
            o[f"{col}_vol6"] = vol6[i]
            o[f"{col}_stretch"] = x[i] / mas[8][i] - 1.0
            o[f"{col}_ram"] = (0.5 * r3[i] + 0.5 * r6[i]) / vol6[i]
            o[f"{col}_sharpe6"] = r6[i] / (vol6[i] * math.sqrt(6))
    vix = [float(r["VIX"]) for r in rows]
    vma3, vma5 = _mean(vix, 3), _mean(vix, 5)
    for i in range(n):
        o = out[i]
        o["VIX_ma3"], o["VIX_ma5"] = vma3[i], vma5[i]
        o["VIX_prev"] = vix[i - 1] if i > 0 else math.nan
        for col in ("GLD", "DBC"):
            prev_px = rows[i - 1][col] if i > 0 else math.nan
            prev_ma = out[i - 1][f"{col}_ma8"] if i > 0 else math.nan
            o[f"{col}_above_ma8_prev"] = 1.0 if (i > 0 and prev_px > prev_ma) else 0.0
    return out


# ── the package's weight functions, verbatim (trinity_omega_suite.py v1.0.0) ─────────────────────────
# Only the annotation `pd.Series` reads `dict` here: production code imports no pandas (requirements.txt).


def _apply_dd_brake(w: Dict[str, float], current_dd: float, start: float = -0.035, floor: float = 0.40) -> Dict[str, float]:
    if current_dd <= start:
        taper = max(floor, 1.0 - (abs(current_dd) - abs(start)) / 0.055)
        return {k: v * taper for k, v in w.items()}
    return w


def weights_trnd1_pro(row: dict, current_dd: float = 0.0) -> Dict[str, float]:
    w = {a: 0.0 for a in ASSETS}
    vol_ok = (row["VIX"] < 19.0) or (row["VIX"] < row["VIX_ma5"]) or (row["VIX"] <= row["VIX_prev"] * 0.90 and row["VIX"] < 28.0)
    panic_rec = ((row["VIX_prev"] > 24.0) or (row["VIX"] > 24.0)) and (row["VIX"] < row["VIX_prev"]) and (row["TLT"] >= row["TLT_ma5"] * 0.97)
    dual_drain = (row["TLT"] < row["TLT_ma4"]) and (row["UUP"] > row["UUP_ma4"])
    acute_shock = dual_drain and ((row["TLT_r1"] < -0.015) or (row["UUP_r1"] > 0.012))

    if panic_rec:
        w["QQQ"] = 0.62
        w["SPY"] = 0.42
    elif (row["SPY"] > row["SPY_ma10"]) and vol_ok and (not acute_shock):
        m = 0.30 if dual_drain else 1.0
        w["SPY"] = 0.55 * m * (0.55 if row["SPY_stretch"] > 0.075 else 1.0)
        if row["QQQ"] > row["QQQ_ma8"]:
            w["QQQ"] = 0.68 * m * (0.55 if row["QQQ_stretch"] > 0.085 else 1.0)

    tv = 0.030
    w["QQQ"] *= min(tv / row["QQQ_vol6"], 1.35)
    w["SPY"] *= min(tv / row["SPY_vol6"], 1.35)
    eq = w["QQQ"] + w["SPY"]
    if eq > 0.95:
        s = 0.95 / eq
        w["QQQ"] *= s
        w["SPY"] *= s
    return _apply_dd_brake(w, current_dd, start=-0.035, floor=0.40)


def weights_nexus4_pro(row: dict, current_dd: float = 0.0) -> Dict[str, float]:
    w = {a: 0.0 for a in ASSETS}
    vol_ok = (row["VIX"] < 19.0) or (row["VIX"] < row["VIX_ma5"]) or (row["VIX"] <= row["VIX_prev"] * 0.90 and row["VIX"] < 28.0)
    panic_rec = ((row["VIX_prev"] > 24.0) or (row["VIX"] > 24.0)) and (row["VIX"] < row["VIX_prev"]) and (row["TLT"] >= row["TLT_ma5"] * 0.97)
    dual_drain = (row["TLT"] < row["TLT_ma4"]) and (row["UUP"] > row["UUP_ma4"])
    acute_shock = dual_drain and ((row["TLT_r1"] < -0.015) or (row["UUP_r1"] > 0.012))

    if panic_rec:
        w["QQQ"] = 1.15
        w["SPY"] = 0.70
    else:
        if (row["QQQ"] > row["QQQ_ma8"]) and (row["SPY"] > row["SPY_ma10"]) and vol_ok and (not acute_shock):
            w["QQQ"] = 0.35 if dual_drain else (1.45 if (row["VIX"] < row["VIX_ma3"] and row["TLT"] >= row["TLT_ma5"]) else 1.20)
            if row["QQQ_stretch"] > 0.085:
                w["QQQ"] *= 0.55
        if (row["SPY"] > row["SPY_ma10"]) and vol_ok and (not acute_shock):
            w["SPY"] = 0.25 if dual_drain else 0.85
            if row["SPY_stretch"] > 0.075:
                w["SPY"] *= 0.55

    if (row["GLD"] > row["GLD_ma8"]) and (row["GLD_stretch"] < 0.105):
        if (row["VIX"] > 19.5) and (row["GLD"] > row["GLD_ma5"]):
            w["GLD"] = 1.15
        elif (row["UUP"] <= row["UUP_ma5"]) and (row["GLD"] > row["GLD_ma4"]):
            w["GLD"] = 0.95
        elif (row["QQQ_r1"] < 0.0) and (row["GLD"] > row["GLD_ma5"]) and (not acute_shock):
            w["GLD"] = 0.80

    tv = 0.026
    w["QQQ"] *= min(tv / row["QQQ_vol6"], 1.35)
    w["SPY"] *= min(tv / row["SPY_vol6"], 1.35)
    w["GLD"] *= min(tv / row["GLD_vol6"], 1.35)

    # Correlated Equity Cap + Gold Cap + Momentum Leader Tilt
    eq = w["QQQ"] + w["SPY"]
    if eq > 0.75:
        s = 0.75 / eq
        w["QQQ"] *= s
        w["SPY"] *= s
    w["GLD"] = min(w["GLD"], 0.65)

    if w["QQQ"] > 0 and w["GLD"] > 0:
        if row["GLD_sharpe6"] > row["QQQ_sharpe6"] + 0.30:
            w["GLD"] = min(w["GLD"] * 1.12, 0.68)
            w["QQQ"] *= 0.90
        elif row["QQQ_sharpe6"] > row["GLD_sharpe6"] + 0.30:
            w["QQQ"] *= 1.08
            w["GLD"] *= 0.90

    gross = sum(w.values())
    if gross > 1.10:
        s = 1.10 / gross
        w = {k: v * s for k, v in w.items()}
    return _apply_dd_brake(w, current_dd, start=-0.035, floor=0.40)


def weights_omega_apex(row: dict, current_dd: float = 0.0) -> Dict[str, float]:
    w = {a: 0.0 for a in ASSETS}
    vol_ok = (row["VIX"] < 19.0) or (row["VIX"] < row["VIX_ma5"]) or (row["VIX"] <= row["VIX_prev"] * 0.90 and row["VIX"] < 28.0)
    panic_rec = ((row["VIX_prev"] > 24.0) or (row["VIX"] > 24.0)) and (row["VIX"] < row["VIX_prev"]) and (row["TLT"] >= row["TLT_ma5"] * 0.97)
    dual_drain = (row["TLT"] < row["TLT_ma4"]) and (row["UUP"] > row["UUP_ma4"])
    acute_shock = dual_drain and ((row["TLT_r1"] < -0.015) or (row["UUP_r1"] > 0.012))

    if panic_rec:
        w["QQQ"] = 0.55 * min(0.025 / row["QQQ_vol6"], 1.30)
        w["SPY"] = 0.30 * min(0.025 / row["SPY_vol6"], 1.30)
    else:
        candidates = []
        if (row["QQQ"] > row["QQQ_ma8"]) and (row["SPY"] > row["SPY_ma10"]) and vol_ok and (not acute_shock):
            ram_q = row["QQQ_ram"] * (0.60 if row["QQQ_stretch"] > 0.085 else 1.0)
            if dual_drain: ram_q *= 0.35
            if ram_q > 0:
                candidates.append(("QQQ", ram_q, row["QQQ_vol6"], 0.60))
        if (row["SPY"] > row["SPY_ma10"]) and vol_ok and (not acute_shock):
            ram_s = row["SPY_ram"] * (0.60 if row["SPY_stretch"] > 0.075 else 1.0)
            if dual_drain: ram_s *= 0.35
            if ram_s > 0:
                candidates.append(("SPY", ram_s, row["SPY_vol6"], 0.50))
        if (row["GLD"] > row["GLD_ma8"]) and (row["GLD_above_ma8_prev"] == 1.0) and (row["GLD_stretch"] < 0.105) and (row["GLD_ram"] > 0):
            g_boost = 1.25 if ((row["VIX"] > 19.5) or (row["UUP"] <= row["UUP_ma5"])) else 0.85
            candidates.append(("GLD", row["GLD_ram"] * g_boost, row["GLD_vol6"], 0.68))
        if (row["DBC"] > row["DBC_ma8"]) and (row["DBC_above_ma8_prev"] == 1.0) and (row["DBC_r3"] > 0.035) and (row["DBC_stretch"] < 0.12) and (row["DBC_ram"] > 0.8):
            candidates.append(("DBC", row["DBC_ram"] * 0.90, row["DBC_vol6"], 0.52))

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_k = candidates[:2]
            rank_mults = [0.80, 0.55] if len(top_k) == 2 else [0.85]
            for i_c, (sym, _, vol, cap) in enumerate(top_k):
                raw_w = rank_mults[i_c] * min(0.026 / vol, 1.30)
                if sym in ("QQQ", "SPY") and dual_drain:
                    raw_w *= 0.40
                w[sym] = min(raw_w, cap)

    eq = w["QQQ"] + w["SPY"]
    if eq > 0.75:
        s = 0.75 / eq
        w["QQQ"] *= s
        w["SPY"] *= s
    gross = sum(w.values())
    if gross > 1.15:
        s = 1.15 / gross
        w = {k: v * s for k, v in w.items()}
    return _apply_dd_brake(w, current_dd, start=-0.030, floor=0.40)


def weights_trinity_master(row: dict, current_dd: float = 0.0) -> Dict[str, float]:
    w1 = weights_trnd1_pro(row, current_dd=0.0)
    w2 = weights_nexus4_pro(row, current_dd=0.0)
    w3 = weights_omega_apex(row, current_dd=0.0)
    # Diversification bonus allows 1.12x clean scaling while keeping Max DD < -9.0% and 0/273 failures!
    w = {a: (0.20 * w1[a] + 0.40 * w2[a] + 0.40 * w3[a]) * 1.14 for a in ASSETS}
    return _apply_dd_brake(w, current_dd, start=-0.035, floor=0.42)


# ── the decisions, and the design book ─────────────────────────────────────

COMPONENTS = {"TRND-1 PRO": weights_trnd1_pro, "NEXUS-ALPHA-4 PRO": weights_nexus4_pro,
              "OMEGA-APEX-1": weights_omega_apex}


def decide(feat_rows: list[dict], book_start: int = WARMUP) -> list[dict]:
    """The package's own loop (run_strict_20yr_audit at zero delay) over grid rows with features. From row
    `book_start` on: each row's TRINITY-MASTER weights, read with the drawdown of the design book's own additive
    equity (the package's), the cost of changing to them, and the period's return once the next row's closes exist
    (None for the last row). The design book is these weights at their own size: measured, never traded."""
    if book_start < WARMUP:
        raise ValueError(f"a decision needs {WARMUP} grid rows before it (asked from row {book_start})")
    out, cum, pk = [], 0.0, 0.0
    prev = {a: 0.0 for a in ASSETS}
    for i in range(book_start, len(feat_rows)):
        row = feat_rows[i]
        dd = cum - pk
        w = weights_trinity_master(row, dd)
        cost = sum(abs(w[a] - prev[a]) for a in ASSETS) * COST
        ret = None
        if i + 1 < len(feat_rows):
            nxt = feat_rows[i + 1]
            ret = sum(w[a] * (nxt[a] / row[a] - 1.0) for a in ASSETS) - cost
            cum += ret
            pk = max(pk, cum)
        out.append({"date": row["date"], "weights": w, "dd_before": dd, "cost": cost, "ret": ret,
                    "cum": cum if ret is not None else None,
                    "components": {k: f(row, 0.0) for k, f in COMPONENTS.items()},
                    "buy": [CFD_OF[a] for a in ASSETS if w[a] > MIN_WEIGHT]})
        prev = dict(w)
    return out


__all__ = ["ASSETS", "CFD_OF", "COMPONENTS", "COST", "MIN_WEIGHT", "SENSORS", "SOURCE_SHA256", "STEP", "STOP_REL",
           "TRINITY_VERSION", "WARMUP", "decide", "features", "grid", "rows_at", "weights_nexus4_pro",
           "weights_omega_apex", "weights_trinity_master", "weights_trnd1_pro"]
