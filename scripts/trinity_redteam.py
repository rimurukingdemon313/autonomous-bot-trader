"""Red team of the owner's TRINITY-OMEGA package (2026-11-21, docs/TRINITY.md). Research only: nothing here trades.

    python3 -B scripts/trinity_redteam.py research/external/trinity/trinity_omega_suite.py <history_dir> <out.json>

<history_dir> is the history/ folder of the trinity-desk-data branch (scripts/trinity_data.py). With "-" in its place
only the tests on the package's own data run (T0, T6, T7, T8). The result written on 2026-11-21 is
research/results/TRINITY-MASTER-redteam.json.

Every test runs the package's OWN weight functions, unchanged, through a copy of its own audit loop, so any difference
from its table comes from the data or the accounting, never from a re-implementation of the rules:

T1  its hard-coded prices against the real closes on the same dates;
T2  the same 288 dates with the real VIX, TLT and UUP of those dates;
T3  every one of the 15 regular 15-trading-day grids (the spec's daily rebalance) over the same span;
T4  each grid marked to market every day, with the intraday lows, and judged by a prop firm's two rules
    (10% maximum loss from the start, 5% daily loss), from every start date;
T5  as the spec would trade it: the order adapter's caps and a 3.2% stop below each rebalance close, on daily
    high/low/open; on the ETFs, and on the CFD prices the spec maps them to;
T6  every hand-set constant in the four weight functions moved by +-10% (one at a time, and 300 joint draws);
T7  a fixed mix holding the strategy's own average weights all the time;
T8  the deflated Sharpe ratio for a range of numbers of trials;
T9  on each of the 15 real grids, the strategy against a fixed mix holding its own average weights.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PKG, HIST, OUT = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
spec = importlib.util.spec_from_file_location("trinity_pkg", PKG)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
ASSETS = M.ASSETS
COST = M.COST_BPS_DEFAULT
FUNCS = {"TRND-1 PRO": "weights_trnd1_pro", "NEXUS-ALPHA-4 PRO": "weights_nexus4_pro",
         "OMEGA-APEX-1": "weights_omega_apex", "TRINITY-MASTER": "weights_trinity_master"}
R = {"package": PKG, "tests": {}}


# ── data ────────────────────────────────────────────────────────────────────

def load(sym: str) -> pd.DataFrame:
    name = sym.replace("^", "_").replace("=", "_")
    d = json.loads((HIST / f"{name}.json").read_text())
    df = pd.DataFrame.from_dict(d, orient="index")
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


REAL = str(HIST) != "-"  # "-": only the tests on the package's own data (T0, T6, T7, T8)
if REAL:
    RAW = {s: load(s) for s in ("QQQ", "SPY", "GLD", "DBC", "UUP", "TLT", "^VIX", "^NDX", "^GSPC", "USO")}
    CLOSE = pd.DataFrame({s.replace("^", ""): RAW[s]["c"] for s in ("QQQ", "SPY", "GLD", "DBC", "UUP", "TLT", "^VIX")})
    CLOSE = CLOSE.dropna()
    DAYS = CLOSE.index


# ── T1: the package's prices against the real closes ───────────────────────

def t1():
    P = M.FULL_PANEL
    out = {}
    for col in ("QQQ", "SPY", "GLD", "DBC", "UUP", "TLT", "VIX"):
        dev, missing = [], []
        for d, v in zip(P["date"], P[col]):
            if d in CLOSE.index:
                dev.append((str(d.date()), float(v), float(CLOSE.at[d, col]), float(v / CLOSE.at[d, col] - 1)))
            else:
                missing.append(str(d.date()))
        a = np.array([x[3] for x in dev])
        seg = {}
        for lo, hi in (("2007", "2013-12-31"), ("2014", "2020-12-31"), ("2021", "2026-12-31")):
            sub = [x for x in dev if lo <= x[0] <= hi]
            seg[f"{lo}..{hi[:4]}"] = {"dates": len(sub), "within_0.5pct": sum(abs(x[3]) < 0.005 for x in sub),
                                      "max_abs_dev_pct": round(100 * max((abs(x[3]) for x in sub), default=0), 2)}
        out[col] = {"dates": len(dev), "not_a_trading_day": missing, "within_0.5pct": int((abs(a) < 0.005).sum()),
                    "max_abs_dev_pct": round(float(100 * abs(a).max()), 2), "by_segment": seg,
                    "worst": sorted(dev, key=lambda x: -abs(x[3]))[:5]}
    R["tests"]["T1_prices_against_real_closes"] = out


# ── the package's features and audit, on any panel ─────────────────────────

def features(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The package's build_20yr_panel feature block, verbatim, on a panel with date, QQQ, SPY, GLD, DBC, UUP, TLT,
    VIX columns."""
    panel = base.sort_values("date").reset_index(drop=True).copy()
    for col in ["QQQ", "SPY", "GLD", "DBC", "UUP", "TLT"]:
        panel[f"{col}_r1"] = panel[col].pct_change(1)
        panel[f"{col}_r3"] = panel[col].pct_change(3)
        panel[f"{col}_r6"] = panel[col].pct_change(6)
        panel[f"{col}_ma3"] = panel[col].rolling(3).mean()
        panel[f"{col}_ma4"] = panel[col].rolling(4).mean()
        panel[f"{col}_ma5"] = panel[col].rolling(5).mean()
        panel[f"{col}_ma8"] = panel[col].rolling(8).mean()
        panel[f"{col}_ma10"] = panel[col].rolling(10).mean()
        panel[f"{col}_vol6"] = panel[f"{col}_r1"].rolling(6).std().clip(lower=0.015)
        panel[f"{col}_stretch"] = panel[col] / panel[f"{col}_ma8"] - 1.0
        panel[f"{col}_ram"] = (0.5 * panel[f"{col}_r3"] + 0.5 * panel[f"{col}_r6"]) / panel[f"{col}_vol6"]
        panel[f"{col}_sharpe6"] = panel[f"{col}_r6"] / (panel[f"{col}_vol6"] * math.sqrt(6))
    panel["VIX_ma3"] = panel["VIX"].rolling(3).mean()
    panel["VIX_ma5"] = panel["VIX"].rolling(5).mean()
    panel["VIX_prev"] = panel["VIX"].shift(1)
    panel["GLD_above_ma8_prev"] = (panel["GLD"].shift(1) > panel["GLD_ma8"].shift(1)).astype(float)
    panel["DBC_above_ma8_prev"] = (panel["DBC"].shift(1) > panel["DBC_ma8"].shift(1)).astype(float)
    for col in ASSETS:
        panel[f"fwd_{col}"] = panel[f"{col}_r1"].shift(-1)
    return panel, panel.iloc[10:-1].copy().reset_index(drop=True)


def weights_path(v20: pd.DataFrame, fn) -> list[dict]:
    """The package's loop: weights at each row from the drawdown of its own additive equity, 0 delay."""
    cum = pk = 0.0
    out = []
    prev = {a: 0.0 for a in ASSETS}
    for _, row in v20.iterrows():
        w = fn(row, cum - pk)
        cost = sum(abs(w[a] - prev[a]) for a in ASSETS) * COST
        nr = sum(w[a] * row[f"fwd_{a}"] for a in ASSETS) - cost
        cum += nr
        pk = max(pk, cum)
        prev = dict(w)
        out.append(w)
    return out


def audit(v20: pd.DataFrame, fn, cost: float = COST, delay: int = 0) -> dict:
    """run_strict_20yr_audit, on any panel (the same arithmetic, the same additive equity)."""
    rows, prev, cum, pk, hist = [], {a: 0.0 for a in ASSETS}, 0.0, 0.0, []
    for idx, row in v20.iterrows():
        w = fn(row, cum - pk)
        hist.append(w)
        ew = hist[idx - delay] if idx >= delay else {a: 0.0 for a in ASSETS}
        c = sum(abs(ew[a] - prev[a]) for a in ASSETS) * cost
        nr = sum(ew[a] * row[f"fwd_{a}"] for a in ASSETS) - c
        cum += nr
        pk = max(pk, cum)
        prev = dict(ew)
        rows.append((row["date"], nr, cum, cum - pk, 1 if sum(ew.values()) > 0 else 0))
    df = pd.DataFrame(rows, columns=["date", "r", "cum", "dd", "active"])
    n = len(df)
    mid = n // 2
    r = df["r"].values

    def tstat(x):
        return float(np.mean(x) / (np.std(x, ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and np.std(x) > 0 else None

    sf = tf = 0
    starts = n - 15
    for s in range(starts):
        e = p = 0.0
        f1 = f2 = False
        for j in range(s, n):
            e += r[j]
            p = max(p, e)
            f1 = f1 or e <= -0.10
            f2 = f2 or (e - p) <= -0.10
            if f1 and f2:
                break
        sf += f1
        tf += f2
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    r21 = df[df["date"] >= "2021-01-01"]
    months21 = (r21["date"].iloc[-1] - r21["date"].iloc[0]).days / 30.4375 if len(r21) > 1 else None
    return {"n": n, "t": tstat(r), "t_h1": tstat(r[:mid]), "t_h2": tstat(r[mid:]),
            "pf": float(pos / neg) if neg > 0 else None,
            "win_active_pct": float((df.loc[df["active"] == 1, "r"] > 0).mean() * 100),
            "mdd_pct": float(df["dd"].min() * 100), "total_pct": float(r.sum() * 100),
            "total_200k": float(r.sum() * 200_000), "worst_bar_pct": float(r.min() * 100),
            "prop_fail_start": f"{sf}/{starts}", "prop_fail_trailing": f"{tf}/{starts}",
            "monthly_200k_2021_on": float(r21["r"].sum() * 200_000 / months21) if months21 else None}


def check_reproduction():
    base = M.FULL_PANEL[["date", "QQQ", "SPY", "GLD", "UUP", "TLT", "VIX", "DBC"]]
    _, v20 = features(base)
    out = {}
    for name, f in FUNCS.items():
        a = audit(v20, getattr(M, f))
        b = M.run_strict_20yr_audit(name, getattr(M, f))
        out[name] = {"ours_t": round(a["t"], 2), "package_t": b["t_stat_20yr"],
                     "same": abs(round(a["t"], 2) - b["t_stat_20yr"]) < 1e-9 and
                     abs(round(a["mdd_pct"], 2) - b["max_dd_20yr_pct"]) < 1e-9}
    R["tests"]["T0_reproduction_of_the_package_table"] = out
    assert all(v["same"] for v in out.values()), out


# ── T2: the same dates, the real sensors ───────────────────────────────────

def t2():
    P = M.FULL_PANEL
    real = P[["date"]].copy()
    ok = real["date"].isin(CLOSE.index)
    real = real[ok].copy()
    for col in ("QQQ", "SPY", "GLD", "DBC", "UUP", "TLT", "VIX"):
        real[col] = [float(CLOSE.at[d, col]) for d in real["date"]]
    _, v20 = features(real)
    out = {"dates_used": int(ok.sum()), "dates_not_trading_days": [str(d.date()) for d in P["date"][~ok]]}
    for name, f in FUNCS.items():
        out[name] = audit(v20, getattr(M, f))
    # the package's own prices with only the VIX replaced by the real VIX of each date
    pv = P[ok][["date", "QQQ", "SPY", "GLD", "UUP", "TLT", "DBC"]].copy()
    pv["VIX"] = [float(CLOSE.at[d, "VIX"]) for d in pv["date"]]
    _, v20v = features(pv)
    out["only_the_vix_corrected"] = {name: audit(v20v, getattr(M, f)) for name, f in FUNCS.items()}
    R["tests"]["T2_same_dates_real_data"] = out


# ── T3: the 15 regular grids ───────────────────────────────────────────────

FIRST, LAST = pd.Timestamp("2007-03-02"), pd.Timestamp("2026-11-13")


def grid(phase: int, step: int = 15) -> pd.DatetimeIndex:
    days = DAYS[(DAYS >= FIRST) & (DAYS <= LAST)]
    return days[phase::step]


def grid_panel(g: pd.DatetimeIndex) -> pd.DataFrame:
    base = CLOSE.loc[g].copy()
    base.insert(0, "date", base.index)
    return base.reset_index(drop=True)


def t3():
    out = {}
    for name, f in FUNCS.items():
        rows = []
        for ph in range(15):
            _, v20 = features(grid_panel(grid(ph)))
            a = audit(v20, getattr(M, f))
            a2 = audit(v20, getattr(M, f), cost=COST * 2)
            ad = audit(v20, getattr(M, f), delay=1)
            rows.append({"phase": ph, **{k: a[k] for k in ("n", "t", "t_h1", "t_h2", "pf", "mdd_pct", "total_200k",
                                                            "prop_fail_start", "prop_fail_trailing",
                                                            "monthly_200k_2021_on")},
                         "t_costs_x2": a2["t"], "t_delay_1": ad["t"]})
        ts = [r["t"] for r in rows]
        out[name] = {"phases": rows, "t_min": min(ts), "t_median": float(np.median(ts)), "t_max": max(ts),
                     "phases_t_ge_3": sum(t >= 3 for t in ts),
                     "monthly_2021_on_median": float(np.median([r["monthly_200k_2021_on"] for r in rows]))}
    R["tests"]["T3_fifteen_regular_grids"] = out


# ── T4/T5: daily marking, prop rules, stops ────────────────────────────────

def ohlc(sym: str) -> dict:
    df = RAW[sym][["o", "h", "l", "c"]].astype(float)
    return {d: (float(o), float(h), float(lo), float(c)) for d, o, h, lo, c in
            zip(df.index, df["o"], df["h"], df["l"], df["c"])}


if REAL:
    ETF_PX = {a: ohlc(a) for a in ASSETS}
    CFD_PX = {"QQQ": ohlc("^NDX"), "SPY": ohlc("^GSPC"), "GLD": ohlc("GLD"), "DBC": ohlc("USO")}


def daily_book(g: pd.DatetimeIndex, fn, px: dict, stops: bool, caps: bool) -> pd.DataFrame:
    """Weights decided at each grid close (the package's rule on the grid panel), held to the next grid close and
    marked every day. Equity is the package's additive kind: fractions of the starting balance. With `caps`, the
    order adapter's caps apply (1.5% at the stop per position, 4% open). With `stops`, each position stops 3.2% below
    its rebalance close on the day's low (a gap fills at the open) and stays flat to the next rebalance. Each change
    of weight, a stop's exit included, costs the package's 8 bp per unit."""
    panel, v20 = features(grid_panel(g))
    w_path = weights_path(v20, fn)
    dates = list(panel["date"].iloc[10:])  # each v20 row's own close, and the close its forward return ends at
    eq = 0.0
    rows = []
    prev_w = {a: 0.0 for a in ASSETS}
    for k in range(len(v20)):
        d0, d1 = dates[k], dates[k + 1]
        w = dict(w_path[k])
        if caps:
            pack = M.build_hard_gate_orders(w, {a: px[a][d0][3] if d0 in px[a] else 1.0 for a in ASSETS},
                                            equity_usd=200_000.0)
            w = {a: 0.0 for a in ASSETS}
            for o in pack["orders"]:
                w[o["etf_proxy"]] = o["notional_usd"] / 200_000.0
        eq -= sum(abs(w[a] - prev_w[a]) for a in ASSETS) * COST
        entry = {a: px[a][d0][3] for a in ASSETS if w[a] > 0 and d0 in px[a]}
        live = dict.fromkeys(entry, True)
        realized = 0.0
        for d in DAYS[(DAYS > d0) & (DAYS <= d1)]:
            mark = low = 0.0
            for a in entry:
                if not live[a] or d not in px[a]:
                    continue
                o, h, lo, c = px[a][d]
                stop = entry[a] * (1 - 0.032)
                if stops and lo <= stop:
                    fill = min(o, stop)  # a gap through the stop fills at the open
                    realized += w[a] * (fill / entry[a] - 1) - w[a] * COST
                    live[a] = False  # closed at the fill: later prices no longer move this position
                    continue
                mark += w[a] * (c / entry[a] - 1)
                low += w[a] * (lo / entry[a] - 1)
            rows.append({"date": d, "eq_close": eq + realized + mark, "eq_low": eq + realized + low})
        for a in entry:
            if live[a] and d1 in px[a]:
                realized += w[a] * (px[a][d1][3] / entry[a] - 1)
        eq += realized
        prev_w = {a: (w[a] if live.get(a, False) else 0.0) for a in ASSETS}
    return pd.DataFrame(rows).set_index("date")


def prop_checks(book: pd.DataFrame, horizon_days: int | None = None) -> dict:
    """From each trading day as a start: fails if equity at a low ever falls 10% below the start, or more than 5%
    below the previous day's closing equity (both in fractions of the starting balance)."""
    e_close = book["eq_close"].values
    e_low = book["eq_low"].values
    n = len(book)
    fails = fails_daily = fails_total = 0
    starts = list(range(0, n - 20, 5))
    for s in starts:
        base = e_close[s]
        end = n if horizon_days is None else min(n, s + horizon_days)
        f_total = f_daily = False
        for j in range(s + 1, end):
            if e_low[j] - base <= -0.10:
                f_total = True
            if e_low[j] - e_close[j - 1] <= -0.05:
                f_daily = True
            if f_total or f_daily:
                break
        fails += f_total or f_daily
        fails_total += f_total
        fails_daily += f_daily
    dd_close = (book["eq_close"] - book["eq_close"].cummax()).min()
    dd_low = (book["eq_low"] - book["eq_close"].cummax()).min()
    day = book["eq_close"].diff()
    return {"starts": len(starts), "failed": fails, "failed_max_loss": fails_total, "failed_daily_loss": fails_daily,
            "max_dd_daily_close_pct": round(float(dd_close * 100), 2), "max_dd_intraday_pct": round(float(dd_low * 100), 2),
            "worst_day_pct": round(float(day.min() * 100), 2)}


def summarize_book(book: pd.DataFrame) -> dict:
    e = book["eq_close"]
    m = e.resample("ME").last().diff().dropna()
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    t = float(m.mean() / (m.std() / math.sqrt(len(m)))) if len(m) > 2 else None
    r21 = e[e.index >= "2021-01-01"]
    months21 = (r21.index[-1] - r21.index[0]).days / 30.4375
    return {"total_200k": round(float(e.iloc[-1] * 200_000), 0), "per_year_pct": round(float(e.iloc[-1] / yrs * 100), 2),
            "t_monthly": round(t, 2) if t is not None else None,
            "monthly_200k_2021_on": round(float((r21.iloc[-1] - r21.iloc[0]) * 200_000 / months21), 0)}


def t4_t5():
    out = {}
    for name in ("TRINITY-MASTER", "NEXUS-ALPHA-4 PRO", "OMEGA-APEX-1", "TRND-1 PRO"):
        fn = getattr(M, FUNCS[name])
        res = {}
        # self-check: with no stops and no caps, the daily book ends where the package's own audit ends
        for ph in (0, 7):
            _, v20 = features(grid_panel(grid(ph)))
            b = daily_book(grid(ph), fn, ETF_PX, False, False)
            a = audit(v20, fn)
            gap = abs(b["eq_close"].iloc[-1] * 100 - a["total_pct"])
            assert gap < 1e-6, (name, ph, b["eq_close"].iloc[-1] * 100, a["total_pct"])
        for label, px, stops, caps in (("as_backtested_no_stops", ETF_PX, False, False),
                                        ("adapter_caps_and_3.2pct_stops_on_etfs", ETF_PX, True, True),
                                        ("adapter_caps_and_3.2pct_stops_on_cfd_prices", CFD_PX, True, True)):
            per = []
            for ph in range(15):
                b = daily_book(grid(ph), fn, px, stops, caps)
                per.append({"phase": ph, **summarize_book(b), **prop_checks(b), "one_year": prop_checks(b, 252)})
            res[label] = {"phases": per,
                          "median_total_200k": float(np.median([p["total_200k"] for p in per])),
                          "median_t_monthly": float(np.median([p["t_monthly"] for p in per])),
                          "median_monthly_200k_2021_on": float(np.median([p["monthly_200k_2021_on"] for p in per])),
                          "worst_intraday_dd_pct": min(p["max_dd_intraday_pct"] for p in per),
                          "phases_with_any_prop_failure": sum(p["failed"] > 0 for p in per),
                          "prop_failures_all_phases": sum(p["failed"] for p in per),
                          "prop_starts_all_phases": sum(p["starts"] for p in per)}
        out[name] = res
    R["tests"]["T4_T5_daily_marking_prop_rules_stops"] = out


# ── T6: the hand-set constants ─────────────────────────────────────────────

def perturbable(fn_names):
    """The float constants in the four weight functions and the drawdown brake, other than 0 and 1."""
    found = []
    for fname in fn_names:
        src = inspect.getsource(getattr(M, fname))
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float) and node.value not in (0.0, 1.0):
                found.append((fname, node.lineno, node.col_offset, node.value))
    return found


ALL_FNS = ["_apply_dd_brake", "weights_trnd1_pro", "weights_nexus4_pro", "weights_omega_apex", "weights_trinity_master"]


def perturbed_module(scale: dict):
    """A copy of the package's weight functions with chosen constants scaled: scale[(fname, line, col)] = factor."""
    ns = dict(vars(M))
    for fname in ALL_FNS:
        src = inspect.getsource(getattr(M, fname))
        tree = ast.parse(src)

        class T(ast.NodeTransformer):
            def visit_Constant(self, node):
                k = (fname, node.lineno, node.col_offset)
                if k in scale and isinstance(node.value, float):
                    return ast.copy_location(ast.Constant(node.value * scale[k]), node)
                return node

        tree = ast.fix_missing_locations(T().visit(tree))
        exec(compile(tree, f"<perturbed {fname}>", "exec"), ns)
    return ns


def t6():
    consts = perturbable(ALL_FNS)
    base_panel = M.FULL_PANEL[["date", "QQQ", "SPY", "GLD", "UUP", "TLT", "VIX", "DBC"]]
    _, v20 = features(base_panel)
    base_t = audit(v20, M.weights_trinity_master)["t"]
    one = []
    for (fname, line, col, val) in consts:
        for f in (0.9, 1.1):
            ns = perturbed_module({(fname, line, col): f})
            a = audit(v20, ns["weights_trinity_master"])
            one.append({"function": fname, "line": line, "value": val, "factor": f, "t": round(a["t"], 3),
                        "mdd_pct": round(a["mdd_pct"], 2), "prop_fail_start": a["prop_fail_start"]})
    rng = np.random.default_rng(20261121)
    joint = []
    for _ in range(300):
        sc = {(fn, ln, co): float(rng.uniform(0.9, 1.1)) for (fn, ln, co, _) in consts}
        ns = perturbed_module(sc)
        a = audit(v20, ns["weights_trinity_master"])
        joint.append({"t": a["t"], "mdd_pct": a["mdd_pct"], "fails": int(a["prop_fail_start"].split("/")[0]),
                      "monthly": a["monthly_200k_2021_on"]})
    jt = np.array([j["t"] for j in joint])
    R["tests"]["T6_hand_set_constants"] = {
        "constants": len(consts), "lookbacks_and_windows": "r1 r3 r6 ma3 ma4 ma5 ma8 ma10 vol6, VIX ma3 ma5, a "
        "0.015 floor on vol, the 10-row warm-up: about 12 more choices",
        "base_t_on_the_package_data": round(base_t, 3),
        "one_at_a_time": {"runs": len(one), "t_min": min(o["t"] for o in one), "t_max": max(o["t"] for o in one),
                          "largest_drops": sorted(one, key=lambda o: o["t"])[:8],
                          "runs_with_prop_failures": sum(int(o["prop_fail_start"].split("/")[0]) > 0 for o in one)},
        "joint_300_draws_each_constant_x_U(0.9,1.1)": {
            "t_p05": float(np.percentile(jt, 5)), "t_median": float(np.median(jt)), "t_p95": float(np.percentile(jt, 95)),
            "share_t_below_3": float((jt < 3).mean()), "share_with_prop_failures": float(np.mean([j["fails"] > 0 for j in joint])),
            "mdd_p05_pct": float(np.percentile([j["mdd_pct"] for j in joint], 5))}}


# ── T7: a fixed mix of the same average weights ────────────────────────────

def t7():
    base_panel = M.FULL_PANEL[["date", "QQQ", "SPY", "GLD", "UUP", "TLT", "VIX", "DBC"]]
    _, v20 = features(base_panel)
    out = {}
    for name, f in FUNCS.items():
        wp = weights_path(v20, getattr(M, f))
        avg = {a: float(np.mean([w[a] for w in wp])) for a in ASSETS}
        fixed = audit(v20, lambda row, dd, avg=avg: dict(avg))
        strat = audit(v20, getattr(M, f))
        rs = np.array([sum(w[a] * r[f"fwd_{a}"] for a in ASSETS) for w, (_, r) in zip(wp, v20.iterrows())])
        rf = np.array([sum(avg[a] * r[f"fwd_{a}"] for a in ASSETS) for _, r in v20.iterrows()])
        out[name] = {"average_weights": {a: round(v, 3) for a, v in avg.items()},
                     "strategy": {k: strat[k] for k in ("t", "mdd_pct", "total_200k", "prop_fail_start")},
                     "fixed_mix": {k: fixed[k] for k in ("t", "mdd_pct", "total_200k", "prop_fail_start")},
                     "corr_with_fixed_mix": float(np.corrcoef(rs, rf)[0, 1])}
    R["tests"]["T7_fixed_mix_of_the_average_weights"] = out


# ── T8: the deflated Sharpe ratio ──────────────────────────────────────────

def t8():
    from statistics import NormalDist
    Z = NormalDist()
    base_panel = M.FULL_PANEL[["date", "QQQ", "SPY", "GLD", "UUP", "TLT", "VIX", "DBC"]]
    _, v20 = features(base_panel)
    wp = weights_path(v20, M.weights_trinity_master)
    prev = {a: 0.0 for a in ASSETS}
    r = []
    for w, (_, row) in zip(wp, v20.iterrows()):
        c = sum(abs(w[a] - prev[a]) for a in ASSETS) * COST
        r.append(sum(w[a] * row[f"fwd_{a}"] for a in ASSETS) - c)
        prev = dict(w)
    r = np.array(r)
    T = len(r)
    sr = r.mean() / r.std(ddof=1)
    g3 = float(pd.Series(r).skew())
    g4 = float(pd.Series(r).kurt() + 3)
    gamma = 0.5772156649
    out = {"periods": T, "sharpe_per_period": round(float(sr), 4), "skew": round(g3, 3), "kurtosis": round(g4, 3)}
    for N in (10, 50, 100, 500, 1000):
        sr0 = math.sqrt(1.0 / T) * ((1 - gamma) * Z.inv_cdf(1 - 1 / N) + gamma * Z.inv_cdf(1 - 1 / (N * math.e)))
        dsr = Z.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
        out[f"trials_{N}"] = {"sr0": round(sr0, 4), "deflated_sharpe_probability": round(dsr, 4)}
    R["tests"]["T8_deflated_sharpe"] = out


# ── T9: the fixed mix on each real grid ────────────────────────────────────

def t9():
    out = []
    for ph in range(15):
        _, v20 = features(grid_panel(grid(ph)))
        wp = weights_path(v20, M.weights_trinity_master)
        avg = {a: float(np.mean([w[a] for w in wp])) for a in ASSETS}
        s = audit(v20, M.weights_trinity_master)
        f = audit(v20, lambda row, dd, avg=avg: dict(avg))
        out.append({"phase": ph, "avg_gross": round(sum(avg.values()), 3), "strategy_t": round(s["t"], 2),
                    "fixed_t": round(f["t"], 2), "strategy_total": round(s["total_200k"]),
                    "fixed_total": round(f["total_200k"]), "strategy_mdd": round(s["mdd_pct"], 2),
                    "fixed_mdd": round(f["mdd_pct"], 2)})
    R["tests"]["T9_fixed_mix_on_the_fifteen_real_grids"] = out


if __name__ == "__main__":
    check_reproduction()
    t7()
    t8()
    if REAL:
        t1()
        t2()
        t3()
        t9()
        t4_t5()
    t6()
    Path(OUT).write_text(json.dumps(R, indent=1, default=str))
    print("written", OUT)
