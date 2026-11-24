"""Red team of the owner's SOVEREIGN package (2026-11-24, research/external/sovereign/, docs/SOVEREIGN.md). Research
only: nothing here trades, sizes an order or reaches a broker.

    python3 -B scripts/sovereign_redteam.py <package.py> <history_dir> <out.json>

<history_dir> is the history/ folder of the sovereign-data branch (scripts/sovereign_data.py). Every test runs the
package's OWN engines and its own shield, unchanged and imported from the file the owner sent, so a difference from
its section 3 comes from the data or the accounting, never from a re-implementation of its rules. What this file
adds is only what a backtest needs around them, each choice stated:

- one row a trading day (the spec's own section 6 asks for daily bars; its section 3 used bars of 12 to 15 days
  before 2025, by its caveat 1); returns and signals on Yahoo's adjusted closes (a CFD pays or charges the
  dividends an ETF pays, so the total return is the economic one);
- the weights decided at day t's close earn day t+1's return (with --delay, day t+2's); costs are the spec's 8 bps
  (and 16) for each unit of weight traded, sum |w_t - w_t-1|; no financing (swap-free) and no borrow fee on shorts;
- IBIT is admitted from 2024-11-01, as the spec says; before that its series is held at its first admitted close, so
  the engines see zero momentum in it and never select it (no return is invented: a zero weight earns nothing);
- the spec's 2-step shield reads the drawdown from the equity peak at the previous close; the live layer the spec
  asks for (section 1 and caveat 2) is replayed apart: the day flattens at the open if the open is already 4% down,
  else at -4% if the day's adverse extremes reach it (every asset at its worst at once: a bound, not a path), and
  the account stops for good at -8.5% from the peak;
- a prop firm's two rules are counted on the day's adverse extremes: a 5% daily loss from the start-of-day equity,
  and a 10% loss from the starting balance.

T0  the spec's own checklist (section 6, item 3) on built markets and on the real path: look-ahead, caps, the
    90-day short guards of SOVEREIGN-TITAN-MAX, the shield's steps;
T1  the weights each rule holds after 2026-11-20 against the ones the spec prints;
T2  the five regimes of the spec's table, each from $200,000, at 8 and 16 bps and with one day's delay;
T3  one account from 2008 to 2026, continuous, with and without the live layer; every losing year;
T4  from every start date: how often a $200,000 account fails a prop firm's rules within a year;
T5  200 placebos holding the same weights with each fund's sign drawn at random every five days;
T6  against holding SPY.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

CAPITAL = 200_000.0
COSTS_BP = (8.0, 16.0)
IBIT_FROM = "2024-11-01"
START = "2008-01-04"
LAST = "2026-11-20"
LABEL = "RED TEAM, RESEARCH ONLY: a replay of the owner's own code on real daily bars; it validates nothing"


def load_package(path: str):
    spec = importlib.util.spec_from_file_location("sovereign_pkg", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── data ──────────────────────────────────────────────────────────────

def load_history(hist: Path, symbols) -> dict:
    """{symbol: {day: {o, h, l, c, adj}}} as served."""
    return {s: json.loads((hist / f"{s}.json").read_text()) for s in symbols}


def panel(raw: dict, assets: list[str], ibit_from: str = IBIT_FROM, last: str = LAST) -> dict:
    """Aligned arrays on the days every core fund traded (IBIT excepted), up to `last`. Adjusted OHLC: o, h, l scaled
    by the day's adj/close factor. IBIT before `ibit_from` (or before its first bar) is held flat at its first
    admitted adjusted close, so its momentum and return are exactly zero there."""
    core = [a for a in assets if a != "IBIT"]
    days = sorted(set.intersection(*(set(raw[a]) for a in core)))
    days = [d for d in days if d <= last]
    out = {"days": days, "c": {}, "o": {}, "h": {}, "l": {}, "live": {}}
    for a in assets:
        c, o, h, lo, live = [], [], [], [], []
        first = None
        if a == "IBIT":
            adm = [d for d in days if d >= ibit_from and d in raw[a]]
            first = adm[0] if adm else None
        for d in days:
            row = raw[a].get(d)
            ok = row is not None and (a != "IBIT" or (first is not None and d >= first))
            if ok:
                f = (row["adj"] / row["c"]) if row.get("adj") else 1.0
                c.append(row["c"] * f)
                o.append((row["o"] or row["c"]) * f)
                h.append((row["h"] or row["c"]) * f)
                lo.append((row["l"] or row["c"]) * f)
                live.append(True)
            else:
                c.append(None)
                o.append(None)
                h.append(None)
                lo.append(None)
                live.append(False)
        if a == "IBIT":
            base = next((x for x in c if x is not None), None)
            if base is None:
                raise SystemExit("IBIT has no bar on or after its admission date")
            c = [base if x is None else x for x in c]
            o = [base if x is None else x for x in o]
            h = [base if x is None else x for x in h]
            lo = [base if x is None else x for x in lo]
        else:
            missing = [days[i] for i, x in enumerate(c) if x is None]
            if missing:
                raise SystemExit(f"{a} has no bar on {missing[:3]}")
        for k, v in (("c", c), ("o", o), ("h", h), ("l", lo), ("live", live)):
            out[k][a] = v
    return out


# ── the engines' weights, as the package computes them ────────────────

def raw_weights(M, name: str, px: dict, assets: list[str], risk_mode: str = "funded") -> np.ndarray:
    """The package's engine for `name`, run day by day: row t is what it returns at day t's close."""
    ds = {a: px["c"][a] for a in assets}
    n = len(px["days"])
    rets = {a: [0.0] + [ds[a][i] / ds[a][i - 1] - 1.0 for i in range(1, n)] for a in assets}
    eng = M.STRATEGY_REGISTRY[name](risk_mode=risk_mode)
    st: dict = {}
    W = np.zeros((n, len(assets)))
    for t in range(n):
        w = eng(ds, rets, assets, t, 1.0, st)
        W[t] = [w[a] for a in assets]
    return W


# ── the account ───────────────────────────────────────────────────────

def replay(M, W: np.ndarray, px: dict, assets: list[str], i0: int, i1: int, cost_bp: float, delay: int = 0,
           live_layer: bool = False, capital: float = CAPITAL) -> dict:
    """One account from day i0's close to day i1's close. At each close t the package's shield turns W[t - delay] into
    the target with the drawdown known at that close; the target earns day t+1. Returns the daily book."""
    C = np.array([px["c"][a] for a in assets], dtype=float).T
    O = np.array([px["o"][a] for a in assets], dtype=float).T
    H = np.array([px["h"][a] for a in assets], dtype=float).T
    L = np.array([px["l"][a] for a in assets], dtype=float).T
    eq, peak, w_prev = capital, capital, np.zeros(len(assets))
    stopped = False
    rows = []
    for t in range(i0, i1):
        dd = eq / peak - 1.0
        src = W[t - delay] if t - delay >= 0 else np.zeros(len(assets))
        # the package's own shield. Its backtest (sections 3 and 4) throttles only: past -7.5% it holds a quarter. The
        # -8.5% stop is its live layer's (section 1, caveat 2), replayed when asked; so without the live layer the
        # drawdown handed to the shield is held at -8%, where the shield's answer is the quarter, never zero.
        seen = dd if live_layer else max(dd, -0.08)
        target = M.apply_prop_shield({a: float(src[j]) for j, a in enumerate(assets)}, current_drawdown=seen)
        w = np.array([target[a] for a in assets])
        if live_layer and (stopped or dd <= -0.085):
            stopped, w = True, np.zeros(len(assets))  # the shield already returned zero; the stop is for good
        cost = float(np.abs(w - w_prev).sum()) * cost_bp / 1e4
        r_close = C[t + 1] / C[t] - 1.0
        r_open = O[t + 1] / C[t] - 1.0
        adverse = np.where(w >= 0, L[t + 1] / C[t] - 1.0, H[t + 1] / C[t] - 1.0)
        pnl_close = float(w @ r_close)
        pnl_open = float(w @ r_open)
        pnl_worst = min(float(w @ adverse), pnl_open, pnl_close)
        killed = None
        pnl = pnl_close
        w_end = w
        if live_layer and not stopped:
            if pnl_open <= -0.04:
                killed, pnl, w_end = "open", pnl_open, np.zeros(len(assets))
            elif pnl_worst <= -0.04:
                killed, pnl, w_end = "intraday", -0.04, np.zeros(len(assets))
            if killed:
                cost += float(np.abs(w).sum()) * cost_bp / 1e4
                pnl_worst = pnl
        start = eq
        eq = eq * (1.0 + pnl - cost)
        worst_eq = start * (1.0 + pnl_worst - cost)
        peak = max(peak, eq)
        rows.append({"day": px["days"][t + 1], "equity": eq, "start": start, "worst_eq": worst_eq,
                     "ret": pnl - cost, "cost": cost, "gross": float(np.abs(w).sum()), "net": float(w.sum()),
                     "short": float(-w[w < 0].sum()), "killed": killed, "stopped": stopped})
        w_prev = w_end
    return {"rows": rows, "capital": capital}


def prop(book: dict) -> dict:
    """A prop firm's two rules on the day's adverse extremes."""
    cap = book["capital"]
    daily = [r for r in book["rows"] if r["worst_eq"] - r["start"] <= -0.05 * r["start"]]
    total = [r for r in book["rows"] if r["worst_eq"] <= 0.9 * cap]
    first = min([r["day"] for r in daily] + [r["day"] for r in total], default=None)
    return {"daily_loss_5pct_days": len(daily), "below_90pct_of_start_days": len(total), "first_failure": first}


def summary(book: dict) -> dict:
    rows = book["rows"]
    if not rows:
        return {"days": 0}
    cap = book["capital"]
    eq = np.array([cap] + [r["equity"] for r in rows])
    rets = np.array([r["ret"] for r in rows])
    peak = np.maximum.accumulate(eq)
    worst = np.array([r["worst_eq"] for r in rows])
    dd_close = float((eq / peak - 1.0).min())
    dd_low = float(min((worst / peak[:-1] - 1.0).min(), dd_close))
    sd = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
    sharpe = float(rets.mean() / sd * math.sqrt(252)) if sd > 0 else None
    years = len(rows) / 252.0
    return {"days": len(rows), "from": rows[0]["day"], "to": rows[-1]["day"], "profit": float(eq[-1] - cap),
            "final": float(eq[-1]), "cagr": float((eq[-1] / cap) ** (1 / years) - 1) if years > 0 and eq[-1] > 0
            else None, "sharpe": sharpe, "t": sharpe * math.sqrt(years) if sharpe is not None else None,
            "max_dd_close": dd_close, "max_dd_intraday": dd_low, "worst_day": float(rets.min()),
            "costs": float(sum(r["cost"] * r["start"] for r in rows)),
            "mean_gross": float(np.mean([r["gross"] for r in rows])),
            "max_gross": float(max(r["gross"] for r in rows)),
            "short_share_of_days": float(np.mean([r["short"] > 1e-9 for r in rows])),
            "kills": sum(1 for r in rows if r["killed"]),
            "stopped_from": next((r["day"] for r in rows if r["stopped"]), None), **prop(book)}


def by_year(book: dict) -> dict:
    out, prev = {}, book["capital"]
    for r in book["rows"]:
        y = r["day"][:4]
        out.setdefault(y, {"start": prev})
        out[y]["end"] = r["equity"]
        prev = r["equity"]
    return {y: {"profit": v["end"] - v["start"], "return": v["end"] / v["start"] - 1.0} for y, v in out.items()}


# ── the tests ─────────────────────────────────────────────────────────

def regimes(days: list[str]) -> dict:
    """The spec's five periods (its section 3.1), as day indices [i0, i1): the last 252 days to 2026-11-20, the 252
    before them, 2020 up to those, 2014-2019, 2008-01-04 to 2013."""
    n = len(days)
    i_last = n - 1
    i5 = i_last - 252
    i4 = i5 - 252
    i3 = next(i for i, d in enumerate(days) if d >= "2020-01-01")
    i2 = next(i for i, d in enumerate(days) if d >= "2014-01-01")
    i1 = next(i for i, d in enumerate(days) if d >= START)
    return {"2008-2013": (i1, i2 - 1), "2014-2019": (i2 - 1, i3 - 1), "2020-2024": (i3 - 1, i4),
            "2024-2025": (i4, i5), "2025-2026": (i5, i_last)}


SPEC_TABLE = {  # the spec's section 3.1 and 3.2, base 8 bps, $200,000 a period
    "SOVEREIGN-TITAN-MAX": {"2008-2013": 75369, "2014-2019": 31271, "2020-2024": 117417, "2024-2025": 7996,
                            "2025-2026": 82238},
    "SOVEREIGN-TITAN-7": {"2008-2013": 66874, "2014-2019": -12220, "2020-2024": 112376, "2024-2025": 4516,
                          "2025-2026": 54467},
    "SEC-TSMOM-4": {"2008-2013": 34544, "2014-2019": -13702, "2020-2024": 96900, "2024-2025": 12836,
                    "2025-2026": 46590},
}
SPEC_WEIGHTS = {  # the spec's "Live Target Weights (2026-11-20 Close, 0% DD)"
    "SOVEREIGN-TITAN-MAX": {"QQQ": -0.3282, "SPY": 0.0, "IWM": 0.0, "GLD": 0.0, "SLV": -0.132, "USO": -0.244,
                            "IBIT": -0.275},
    "SOVEREIGN-TITAN-7": {"QQQ": -0.3282, "SPY": 0.0, "IWM": 0.0, "GLD": 0.0, "SLV": -0.132, "USO": -0.244,
                          "IBIT": -0.275},
    "SEC-TSMOM-4": {"QQQ": -0.3044, "SPY": 0.0, "IWM": 0.0, "GLD": 0.0, "SLV": -0.114, "USO": -0.2263,
                    "IBIT": -0.2375},
}


def t0_checklist(M, W_by: dict, px: dict, assets: list[str], seed: int = 7) -> dict:
    """The spec's section 6 item 3, run as stated, on built random markets and on the real path (from START)."""
    rng = np.random.default_rng(seed)
    i_start = next((i for i, d in enumerate(px["days"]) if d >= START), 0)
    out = {}
    # look-ahead: a close moved by half at day k changes no weight decided before day k
    n, k = 300, 200
    base = {"days": [str(i) for i in range(n)],
            "c": {a: list(100 * np.cumprod(1 + rng.normal(0.0003, 0.015, n))) for a in assets}}
    moved = {"days": base["days"], "c": {a: v[:k] + [v[k] * 1.5] + v[k + 1:] for a, v in base["c"].items()}}
    leaks = {}
    for name in M.STRATEGY_REGISTRY:
        w0, w1 = raw_weights(M, name, base, assets), raw_weights(M, name, moved, assets)
        leaks[name] = {"days_before_k_changed": int(np.any(w0[:k] != w1[:k], axis=1).sum()),
                       "day_k_changed": bool(np.any(w0[k] != w1[k]))}
    out["look_ahead"] = leaks
    # caps and the short guards on the real path
    rows = {}
    C = {a: px["c"][a] for a in assets} if W_by else {}
    for name, W in W_by.items():
        cm = 0.95 if name == "SEC-TSMOM-4" else 1.10
        over = int(sum(abs(W[t, j]) > M.TAIL_CAPS[a] * cm + 1e-9 for t in range(len(W)) for j, a in enumerate(assets)))
        guard = {}
        if name == "SOVEREIGN-TITAN-MAX":
            for j, a in enumerate(assets):
                sec = M.SECTORS[a]
                if sec not in ("EQUITY", "METALS"):
                    continue
                bar = -0.05 if sec == "EQUITY" else 0.0
                held = [t for t in range(max(90, i_start), len(W)) if W[t, j] < -1e-9]
                bad = [t for t in held if C[a][t] / C[a][t - 90] - 1.0 >= bar]
                guard[a] = {"short_days": len(held), "short_while_guard_says_no": len(bad),
                            "first": px["days"][bad[0]] if bad else None}
        rows[name] = {"weights_over_their_cap": over, "guards": guard}
    out["real_path"] = rows
    s = M.apply_prop_shield({"X": 1.0}, -0.05)["X"], M.apply_prop_shield({"X": 1.0}, -0.075)["X"], \
        M.apply_prop_shield({"X": 1.0}, 0.0, -0.04)["X"], M.apply_prop_shield({"X": 1.0}, -0.085)["X"]
    out["shield_steps"] = {"at -5%": s[0], "at -7.5%": s[1], "intraday -4%": s[2], "at -8.5%": s[3]}
    return out


def t5_placebo(M, W: np.ndarray, px: dict, assets: list[str], i0: int, i1: int, k: int = 200, seed: int = 11) -> dict:
    """The same weights with each fund's sign drawn at random every five days: does the direction add anything? Both
    the rule and its placebos are run before costs: a sign drawn every five days trades far more than a trend does,
    and charging that would flatter the rule."""
    rng = np.random.default_rng(seed)
    real = summary(replay(M, W, px, assets, i0, i1, 0.0))["sharpe"]
    sh = []
    for _ in range(k):
        blocks = rng.choice([-1.0, 1.0], size=(len(W) // 5 + 1, len(assets)))
        S = np.repeat(blocks, 5, axis=0)[: len(W)]
        sh.append(summary(replay(M, np.abs(W) * S, px, assets, i0, i1, 0.0))["sharpe"] or 0.0)
    sh = np.array(sh)
    return {"before_costs": True, "real_sharpe": real, "placebo_median": float(np.median(sh)), "placebo_p95": float(np.quantile(sh, 0.95)),
            "share_of_placebos_at_or_above": float(np.mean(sh >= (real or 0.0))), "placebos": k}


def run(pkg: str, hist: Path) -> dict:
    M = load_package(pkg)
    assets = list(M.SECTORS)
    raw = load_history(hist, assets)
    px = panel(raw, assets)
    days = px["days"]
    man = json.loads((hist / "manifest.json").read_text())
    R = {"label": LABEL, "package": pkg, "data": {s: {k: man["series"][s][k] for k in ("rows", "first", "last",
                                                                                      "sha256")}
                                                  for s in assets}, "days": len(days), "first": days[0],
         "last": days[-1], "ibit_admitted": IBIT_FROM, "tests": {}}
    W_by = {name: raw_weights(M, name, px, assets) for name in M.STRATEGY_REGISTRY}
    R["tests"]["T0"] = t0_checklist(M, W_by, px, assets)
    # T1: the weights held after the last close against the spec's printed ones
    R["tests"]["T1"] = {name: {"replay": {a: round(float(W_by[name][-1, j]), 4) for j, a in enumerate(assets)},
                               "spec": SPEC_WEIGHTS[name], "last_day": days[-1]} for name in W_by}
    reg = regimes(days)
    t2 = {}
    for name, W in W_by.items():
        t2[name] = {}
        for p, (i0, i1) in reg.items():
            t2[name][p] = {"spec_profit_8bp": SPEC_TABLE[name][p],
                           **{f"{int(c)}bp": summary(replay(M, W, px, assets, i0, i1, c)) for c in COSTS_BP},
                           "delay_1_day_8bp": summary(replay(M, W, px, assets, i0, i1, COSTS_BP[0], delay=1))}
    R["tests"]["T2"] = t2
    i0, i1 = reg["2008-2013"][0], reg["2025-2026"][1]
    t3 = {}
    for name, W in W_by.items():
        base = replay(M, W, px, assets, i0, i1, COSTS_BP[0])
        livel = replay(M, W, px, assets, i0, i1, COSTS_BP[0], live_layer=True)
        t3[name] = {"8bp": summary(base), "16bp": summary(replay(M, W, px, assets, i0, i1, COSTS_BP[1])),
                    "8bp_with_live_layer": summary(livel), "years_8bp": by_year(base)}
    R["tests"]["T3"] = t3
    t4 = {}
    for name, W in W_by.items():
        starts = list(range(i0, i1 - 252, 21))
        fails = 0
        for s in starts:
            if prop(replay(M, W, px, assets, s, s + 252, COSTS_BP[0]))["first_failure"]:
                fails += 1
        t4[name] = {"starts": len(starts), "failed_within_a_year": fails, "share": fails / len(starts)}
    R["tests"]["T4"] = t4
    R["tests"]["T5"] = {name: t5_placebo(M, W, px, assets, i0, i1) for name, W in W_by.items()}
    R["tests"]["T6"] = {"SPY held from the same close, no shield, no cost": buy_and_hold(px, "SPY", i0, i1),
                        "by regime": {p: buy_and_hold(px, "SPY", a, b) for p, (a, b) in reg.items()}}
    W = raw_weights(M, "SOVEREIGN-TITAN-MAX", px, assets, risk_mode="eval")
    R["tests"]["T3"]["SOVEREIGN-TITAN-MAX (risk_mode eval)"] = {"8bp": summary(replay(M, W, px, assets, i0, i1,
                                                                                     COSTS_BP[0]))}
    return R


def buy_and_hold(px: dict, sym: str, i0: int, i1: int, capital: float = CAPITAL) -> dict:
    c = np.array(px["c"][sym][i0:i1 + 1], dtype=float)
    eq = capital * c / c[0]
    r = c[1:] / c[:-1] - 1.0
    sd = float(r.std(ddof=1))
    years = len(r) / 252.0
    return {"from": px["days"][i0 + 1], "to": px["days"][i1], "profit": float(eq[-1] - capital),
            "sharpe": float(r.mean() / sd * math.sqrt(252)) if sd > 0 else None,
            "max_dd_close": float((eq / np.maximum.accumulate(eq) - 1.0).min()), "worst_day": float(r.min()),
            "cagr": float((eq[-1] / capital) ** (1 / years) - 1) if years > 0 else None}


def main(argv: list[str]) -> int:
    pkg, hist, out = argv[0], Path(argv[1]), Path(argv[2])
    R = run(pkg, hist)
    out.write_text(json.dumps(R, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({n: {p: {"spec": v["spec_profit_8bp"], "8bp": round(v["8bp"]["profit"]),
                              "16bp": round(v["16bp"]["profit"])} for p, v in d.items()}
                      for n, d in R["tests"]["T2"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
