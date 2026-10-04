"""RV-1: does cross-sectional, currency-relative information predict which currencies outperform?

    python scripts/rv1.py spec          # freeze research/specs/RV-1.json (+ a point-in-time check, no outcome read)
    python scripts/rv1.py preregister   # registry trial RV-1 (Stage 1); the document must quote the spec sha256
    python scripts/rv1.py stage1        # once: six tests on 2000-01 .. 2007-03 (H.10), the frozen gate
    python scripts/rv1.py stage2        # only for Stage-1 passers: 2008-07 .. 2016 on bid/ask with costs
    python scripts/rv1.py holdout       # only for ONE candidate that passed everything else: sealed 2017

Everything is frozen in the spec and the code hash before any outcome is computed; each stage refuses
to run unless the previous stage's recorded decision allows it. See
research/preregistrations/RV-1.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data import instruments  # noqa: E402
from aitrader.data.h10 import H10Store  # noqa: E402
from aitrader.data.instruments import UNIVERSE_KEY  # noqa: E402
from aitrader.data.rates import RateStore  # noqa: E402
from aitrader.data.store import DataStore, open_final_test  # noqa: E402
from aitrader.research.discovery.program import _dump, code_sha256  # noqa: E402
from aitrader.research.discovery.rv import (CURRENCIES, MIN_CROSS_SECTION, MOM_DAYS, NON_USD, PAIR, RV_VERSION,  # noqa: E402
                                            SIGNALS, Book, Costs, Quote, forward_relative, fridays, global_vol,
                                            ny_epoch, ols_alpha_t, panel_from_h10, rank_weights, raw_dispersion,
                                            regimes, scores, spearman, t_stat, week, welch_t)
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

R = ROOT / "research"
PID, S2ID, HID = "RV-1", "RV-1-S2", "RV-1-H"
DOC = "research/preregistrations/RV-1.md"
SPEC = R / "specs" / "RV-1.json"
OUT = R / "knowledge"
EXTRA_CODE = ("aitrader/data/h10.py", "aitrader/data/rates.py", "aitrader/data/store.py", "scripts/rv1.py")

HISTORY_START = date(1999, 1, 8)  # first Friday with H.10 for all eight currencies (lookbacks, regime history)
S1 = (date(2000, 1, 1), date(2007, 3, 30))  # every Stage-1 forward window ends before 2007-03-30
S1_USES = ((date(1999, 1, 1), date(2000, 1, 1), "fit"), (date(2000, 1, 1), date(2007, 3, 30), "judge"))
S2 = (date(2008, 7, 1), date(2017, 1, 1))
S2_HALVES = (date(2008, 7, 1), date(2012, 7, 1), date(2017, 1, 1))
HOLD = (date(2017, 1, 1), date(2018, 1, 1))
S1_THRESHOLD = 2.807  # agreed in the design; verified against the registry at registration
MIN_WEEKS, MIN_REGIME_WEEKS = 100, 50
PROMISING_T, HOLDOUT_T, INCREMENT_T = 2.0, 1.645, 2.0
NULL_DRAWS, NULL_PCTL, SEED = 1000, 95.0, 20261004
BEST_WEEKS_REMOVED, YEAR_MIN_WEEKS, YEAR_SHARE, CONCENTRATION = 5, 26, 0.6, 0.5
NOON = (12, 0)
QUOTE_TOLERANCE_MIN = 60
HYPOTHESES = {
    "RV1-H1-CARRY": {"kind": "signal", "signal": "carry", "price_based": False,
                     "text": "Currencies with higher policy rates outperform lower-rate ones over the next week "
                             "(cross-sectional carry)."},
    "RV1-H2-MOMENTUM": {"kind": "signal", "signal": "momentum", "price_based": True,
                        "text": "Currencies with higher 3- and 12-month relative returns (skipping the last week) "
                                "outperform over the next week (relative momentum)."},
    "RV1-H3-REVERSAL": {"kind": "signal", "signal": "reversal", "price_based": True,
                        "text": "Last week's relative losers outperform last week's winners over the next week."},
    "RV1-H4-VALUE": {"kind": "signal", "signal": "value", "price_based": True,
                     "text": "Currencies that fell most against the others over five years outperform over the next "
                             "week (five-year reversal as a value proxy)."},
    "RV1-H5-CARRY-VOL": {"kind": "regime", "signal": "carry", "price_based": False,
                         "text": "Carry's information differs between low and high global FX volatility."},
    "RV1-H6-MOMENTUM-VOL": {"kind": "regime", "signal": "momentum", "price_based": True,
                            "text": "Momentum's information differs between low and high global FX volatility."},
}


def code_hash() -> str:
    h = hashlib.sha256(code_sha256().encode())
    for p in EXTRA_CODE:
        h.update(p.encode() + b"\0" + (ROOT / p).read_bytes() + b"\0")
    return h.hexdigest()


def _r(x, nd=6):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def spec(reg: Registry) -> dict:
    thr = reg.threshold_for_next(UNIVERSE_KEY, S1_USES[1][0], S1_USES[1][1], new_tests=len(HYPOTHESES))
    h10 = json.loads((ROOT / "data" / "h10" / "manifest.json").read_text())
    return {
        "id": PID, "version": RV_VERSION,
        "question": "Does a cross-sectional ranking of eight currencies (carry, relative momentum, one-week reversal, "
                    "five-year reversal, and carry/momentum by global FX volatility) predict the next week's "
                    "RELATIVE returns -- and, if so, does a currency-neutral book survive realistic costs, "
                    "robustness and the sealed holdout?",
        "universe": list(CURRENCIES),
        "data": {"h10": {"primary_vintage": h10["primary_vintage"], "files": {k: v["sha256"] for k, v in
                                                                             h10["files"].items()}},
                 "policy_rates": "BIS WS_CBPOL via aitrader/data/rates.py (point in time, staleness rule)",
                 "execution": "Dukascopy M15 bid/ask (data/manifest.json); AUDUSD synthesised from AUDJPY/USDJPY"},
        "transformations": "value of each currency in USD (USD = 1); log; relative return = return minus the mean of "
                           "the eight; only dates on which all seven H.10 rates exist",
        "timing": {"decision": "Friday 17:00 New York", "information": "H.10 rates with available_at <= decision "
                   "(the next business day 17:00 New York after their date); policy rates public at the decision",
                   "forward": "from the first H.10 fixing after the Friday to the first fixing >= 7 days later "
                              "(<= 10 days, else the week is skipped)"},
        "signals": {"carry": "policy rate (percent); a currency without one is excluded that week, never filled",
                    "momentum": f"mean of the cross-sectional ranks of the log change over {MOM_DAYS[0]} and "
                                f"{MOM_DAYS[1]} days ending at the last fixing >= 7 days before the last usable "
                                "fixing (skip one week)",
                    "reversal": "minus the log change over the last 7 days to the last usable fixing",
                    "value": "minus the log change over the last 1820 days (five years) to the last usable fixing"},
        "regime": "global FX volatility = mean |daily log change| of the seven currencies against USD over the last "
                  "20 changes usable at the decision; HIGH if above the median of the previous (up to 156, at least "
                  "52) weekly values, else LOW",
        "hypotheses": HYPOTHESES,
        "stage1": {
            "period": [S1[0].isoformat(), S1[1].isoformat()], "sampling": "weekly, Fridays",
            "statistic": "weekly Spearman IC between the score (literature sign: + = expected to outperform) and "
                         "the next week's relative returns, >= 6 currencies; t = mean IC / (sd / sqrt(weeks)); "
                         "H5/H6: Welch t of mean IC in LOW minus HIGH",
            "threshold": S1_THRESHOLD, "threshold_registry": round(thr, 4),
            "multiple_testing": "Bonferroni at 5% two-sided over the registry's 4 earlier tests on 2000-01..2007-03 "
                                "plus these 6",
            "gate_signal": f"|t| >= {S1_THRESHOLD}, >= {MIN_WEEKS} weeks, the mean IC has the same sign in both "
                           "halves of the period, leaving out any one currency never flips the sign, and the "
                           "currency-neutral book's gross mean has the same sign",
            "gate_regime": f"|t| >= {S1_THRESHOLD}, >= {MIN_REGIME_WEEKS} weeks in each regime, the LOW-minus-HIGH "
                           "difference has the same sign in both halves",
            "candidate": "signal hypothesis: its signal in the direction of its mean IC; regime hypothesis: its "
                         "signal traded only in the regime with the higher mean IC (in that IC's direction), no "
                         "position in the other",
            "reported": "weeks, mean/sd IC, t, IC by year and half, leave-one-currency-out, without the most "
                        "favourable week, 1%-trimmed mean, book gross mean/t/Sharpe, contribution by currency, "
                        "book without its 5 best weeks"},
        "book": "weights = centred cross-sectional ranks scaled to sum 0 with gross 2 (one unit long, one short), "
                "over the currencies with a score; fewer than 6: no position",
        "stage2": {
            "period": [S2[0].isoformat(), S2[1].isoformat()], "halves": [d.isoformat() for d in S2_HALVES],
            "execution": "rebalance at the H.10 entry fixing time (noon New York, first business day after the "
                         "Friday) on Dukascopy M15 bid/ask (the bar closing then, else the nearest within 60 "
                         "minutes; any missing pair -> no rebalance that week); AUDUSD = AUDJPY/USDJPY (bid = "
                         "AUDJPY bid / USDJPY ask, ask = AUDJPY ask / USDJPY bid)",
            "universe_rule": "a currency without a policy rate at the decision is excluded from every Stage-2 book "
                             "that week (its financing cannot be priced; never filled)",
            "costs": asdict(Costs()) | {"spread": "measured at the execution bar, half paid on every change of "
                                                  "position", "financing": "position x (its policy rate - USD "
                                                  "policy rate) x days/360, minus the markup on gross exposure"},
            "threshold": "bonferroni over the registry's tests on 2008-07..2017-01 plus the number of candidates, "
                         "computed when RV-1-S2 is registered",
            "controls": {"always_trade": "the candidate rebalanced every week (primary)",
                         "abstention": "hold the book only when the signal's raw cross-sectional dispersion is >= "
                                       "the median of its previous (up to 156, >= 52) weekly values; else flat",
                         "price_only_for_carry": "the momentum book (H2 definition) under the same regime gating: "
                                                 f"OLS alpha of the candidate's gross weekly return on it, t >= "
                                                 f"{INCREMENT_T}",
                         "null_for_price_signals": f"{NULL_DRAWS} random rank books (weekly permutations, seed "
                                                   f"{SEED}): candidate gross mean > their {NULL_PCTL:.0f}th "
                                                   "percentile"},
            "robustness": {"R1_halves": "net mean > 0 in both halves",
                           "R2_years": f">= {YEAR_SHARE:.0%} of years with >= {YEAR_MIN_WEEKS} weeks net positive",
                           "R3_concentration": f"no currency carries > {CONCENTRATION:.0%} of the gross P&L, and "
                                               "leaving out any one currency keeps the net mean > 0",
                           "R4_outliers": f"net mean > 0 without the {BEST_WEEKS_REMOVED} best weeks",
                           "R5_costs": "net mean > 0 with spread, slippage and commission x2",
                           "R6_execution": "net mean > 0 when every rebalance is one business day later",
                           "R7_regimes": "net mean not significantly negative (t > -2) in either volatility regime",
                           "R8_incremental": "the control test above"},
            "pass": "net mean > 0 with t >= the Stage-2 threshold and R1..R8 -> holdout eligible (the best by t only); "
                    f"net mean > 0, t >= {PROMISING_T} and R1..R8 -> PROMISING; else REJECTED"},
        "holdout": {"period": [HOLD[0].isoformat(), HOLD[1].isoformat()],
                    "policy": "RESEARCH_PROTOCOL.md section 2: one candidate that passed everything else, once",
                    "pass": f"net mean > 0 with t >= {HOLDOUT_T}, and net mean > 0 with costs x2"},
        "classification": {"VALIDATED": "Stage 1 gate, Stage 2 at its threshold with R1..R8, and the holdout",
                           "PROMISING": "Stage 1 gate and Stage 2 net t >= 2 with R1..R8, short of validation",
                           "REJECTED": "anything else"},
        "aud": "the repository's Dukascopy AUDUSD is defective in 2008-01..09 and 2009-04..09 (H.10 audit); RV-1 never "
               "reads it: Stage 1 uses H.10, Stage 2 and the holdout use AUDJPY/USDJPY",
        "no_sizing": "weights are fractions of a notional; sizing, limits and execution remain the Risk Engine's",
    }


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


# ── data ─────────────────────────────────────────────────────────────────────────────────────────

def load(holdout, key=None):
    panel = panel_from_h10(H10Store(ROOT / "data" / "h10", holdout).load(key=key))
    rs = RateStore(ROOT / "data" / "rates", holdout).load(key=key)
    rates = [rs[(c, "POLICY")] for c in CURRENCIES]
    return panel, rates


def rates_at(rates, t: int) -> np.ndarray:
    return np.array([float(s.asof(np.array([t]))[0]) for s in rates])


def calendar(panel, start: date, end: date):
    """Decision weeks with their information, signals and forward relative returns (history from 1999)."""
    rows = []
    for f in fridays(HISTORY_START, end):
        w = week(panel, f)
        if w is None or panel.dates[w.x] >= end:
            continue
        rows.append(w)
    return rows


# ── Stage 1 ──────────────────────────────────────────────────────────────────────────────────────

def stage1_table(panel, rates):
    weeks = calendar(panel, S1[0], S1[1])
    gv = [global_vol(panel, w) for w in weeks]
    reg = regimes(gv)
    out = []
    for w, g, rg in zip(weeks, gv, reg):
        if w.friday < S1[0]:
            continue
        rn = rates_at(rates, ny_epoch(w.friday, 17))
        out.append({"week": w, "scores": scores(panel, w, rn), "rr": forward_relative(panel, w), "regime": rg,
                    "gv": g})
    return out


def _ic_series(table, signal, exclude=None):
    ics = []
    for row in table:
        s = row["scores"][signal].copy()
        rr = row["rr"].copy()
        if exclude is not None:
            s[CURRENCIES.index(exclude)] = np.nan
        ics.append(spearman(s, rr))
    return np.array(ics)


def _book_series(table, signal, sign=1.0):
    ret, contrib = [], np.zeros(len(CURRENCIES))
    for row in table:
        w = sign * rank_weights(row["scores"][signal])
        ret.append(float(w @ row["rr"]) if np.any(w) else np.nan)
        contrib += w * row["rr"]
    return np.array(ret), contrib


def _summary_signal(table, signal):
    ics = _ic_series(table, signal)
    ok = np.isfinite(ics)
    rows = [r for r, k in zip(table, ok) if k]
    x = ics[ok]
    n = len(x)
    t = t_stat(x)
    mean = float(x.mean()) if n else float("nan")
    sign = 1.0 if mean >= 0 else -1.0
    years = {}
    for r, v in zip(rows, x):
        years.setdefault(r["week"].friday.year, []).append(v)
    half = n // 2
    halves = [x[:half], x[half:]]
    loo = {c: _r(np.nanmean(_ic_series(rows, signal, exclude=c))) for c in CURRENCIES}
    fav = np.argmax(sign * x) if n else None
    no_best = np.delete(x, fav) if n else x
    lo, hi = (np.percentile(x, [1, 99]) if n else (np.nan, np.nan))
    trimmed = x[(x >= lo) & (x <= hi)] if n else x
    book, contrib = _book_series(rows, signal)
    b = book[np.isfinite(book)]
    best5 = np.sort(sign * b)[::-1][BEST_WEEKS_REMOVED:] if len(b) > BEST_WEEKS_REMOVED else b
    res = {
        "weeks": n, "mean_ic": _r(mean), "sd_ic": _r(x.std(ddof=1) if n > 1 else np.nan), "t": _r(t, 4),
        "ic_by_year": {str(y): {"weeks": len(v), "mean_ic": _r(np.mean(v))} for y, v in sorted(years.items())},
        "halves": [{"weeks": len(h), "mean_ic": _r(h.mean()), "t": _r(t_stat(h), 4)} for h in halves],
        "first_half_end": rows[half - 1]["week"].friday.isoformat() if n > 1 else None,
        "leave_one_currency_out_mean_ic": loo,
        "t_without_most_favourable_week": _r(t_stat(no_best), 4), "mean_ic_trimmed_1pct": _r(trimmed.mean()),
        "book": {"weeks": int(len(b)), "gross_mean": _r(b.mean()), "t": _r(t_stat(b), 4),
                 "sharpe_annual": _r(b.mean() / b.std(ddof=1) * np.sqrt(52)) if len(b) > 2 else None,
                 "total": _r(b.sum()), "mean_without_5_best_weeks_signed": _r(best5.mean()),
                 "contribution_by_currency": {c: _r(v) for c, v in zip(CURRENCIES, contrib)}},
    }
    gates = {"weeks": n >= MIN_WEEKS, "t": bool(np.isfinite(t) and abs(t) >= S1_THRESHOLD),
             "halves_same_sign": all(len(h) and np.sign(h.mean()) == np.sign(mean) for h in halves),
             "leave_one_out_same_sign": all(v is not None and np.sign(v) == np.sign(mean) for v in loo.values()),
             "book_same_sign": bool(len(b) and np.sign(b.mean()) == np.sign(mean))}
    res["gates"] = gates
    res["passed"] = all(gates.values())
    res["direction"] = int(sign)
    return res


def _summary_regime(table, signal):
    ics = _ic_series(table, signal)
    rows = [(r, v) for r, v in zip(table, ics) if np.isfinite(v) and r["regime"] is not None]
    lo = np.array([v for r, v in rows if r["regime"] == "LOW"])
    hi = np.array([v for r, v in rows if r["regime"] == "HIGH"])
    t = welch_t(lo, hi)
    diff = (lo.mean() - hi.mean()) if len(lo) and len(hi) else float("nan")
    half = len(rows) // 2
    hd = []
    for part in (rows[:half], rows[half:]):
        a = [v for r, v in part if r["regime"] == "LOW"]
        b = [v for r, v in part if r["regime"] == "HIGH"]
        hd.append(_r(np.mean(a) - np.mean(b)) if a and b else None)
    better = "LOW" if (np.nanmean(lo) if len(lo) else -np.inf) >= (np.nanmean(hi) if len(hi) else -np.inf) else "HIGH"
    better_ic = lo.mean() if better == "LOW" else hi.mean()
    gates = {"weeks_each_regime": len(lo) >= MIN_REGIME_WEEKS and len(hi) >= MIN_REGIME_WEEKS,
             "t": bool(np.isfinite(t) and abs(t) >= S1_THRESHOLD),
             "halves_same_sign": all(h is not None and np.sign(h) == np.sign(diff) for h in hd)}
    return {"weeks_low": int(len(lo)), "weeks_high": int(len(hi)), "mean_ic_low": _r(lo.mean() if len(lo) else np.nan),
            "mean_ic_high": _r(hi.mean() if len(hi) else np.nan), "t_low": _r(t_stat(lo), 4),
            "t_high": _r(t_stat(hi), 4), "difference_low_minus_high": _r(diff), "t": _r(t, 4),
            "difference_by_half": hd, "gates": gates, "passed": all(gates.values()),
            "candidate_regime": better, "direction": int(1 if better_ic >= 0 else -1)}


# ── Stage 2 ──────────────────────────────────────────────────────────────────────────────────────

def quote_source(store, key=None):
    syms = sorted({p for p in PAIR.values() if p != "AUDUSD"} | {"AUDJPY"})
    src = {}
    for s in syms:
        b = store.load(s, "M15", key=key) if key else store.load(s, "M15")
        src[s] = (np.asarray(b.available_at, np.int64), np.asarray(b.bid_close, float), np.asarray(b.ask_close, float))
    return src


def _bar(src, sym, t):
    at, bid, ask = src[sym]
    k = int(np.searchsorted(at, t))
    best = None
    for j in (k - 1, k, k + 1, k - 2, k + 2):
        if 0 <= j < len(at) and abs(int(at[j]) - t) <= QUOTE_TOLERANCE_MIN * 60:
            if best is None or abs(int(at[j]) - t) < abs(int(at[best]) - t) or (
                    abs(int(at[j]) - t) == abs(int(at[best]) - t) and at[j] < at[best]):
                best = j
    return None if best is None else (bid[best], ask[best])


def quotes_at(src, t: int) -> dict | None:
    out = {}
    for c, pair in PAIR.items():
        if pair == "AUDUSD":
            a, u = _bar(src, "AUDJPY", t), _bar(src, "USDJPY", t)
            if a is None or u is None:
                return None
            bid, ask = a[0] / u[1], a[1] / u[0]
        else:
            q = _bar(src, pair, t)
            if q is None:
                return None
            bid, ask = q
        mid = (bid + ask) / 2.0
        pip = instruments.get(pair).pip
        out[c] = Quote(mid, (ask - bid) / 2.0 / mid, pip / mid)
    return out


def _dispersion_gate(values: list[float]) -> list[bool | None]:
    out, hist = [], []
    for v in values:
        prev = [x for x in hist[-156:] if np.isfinite(x)]
        out.append(None if (not np.isfinite(v) or len(prev) < 52) else bool(v >= np.median(prev)))
        hist.append(v)
    return out


def stage2_weeks(panel, rates, start, end):
    weeks = calendar(panel, start, end)
    gv = [global_vol(panel, w) for w in weeks]
    reg = regimes(gv)
    rows = []
    for w, rg in zip(weeks, reg):
        rn = rates_at(rates, ny_epoch(w.friday, 17))
        sc = scores(panel, w, rn)
        missing_rate = ~np.isfinite(rn)
        for k in sc:  # universe rule: no financing rate -> excluded from every Stage-2 book that week
            sc[k] = np.where(missing_rate, np.nan, sc[k])
        rows.append({"week": w, "scores": sc, "rates": rn, "regime": rg,
                     "dispersion": raw_dispersion(panel, w, np.where(missing_rate, np.nan, rn))})
    for k in SIGNALS:
        for row, g in zip(rows, _dispersion_gate([r["dispersion"][k] for r in rows])):
            row.setdefault("disp_ok", {})[k] = g
    return [r for r in rows if r["week"].friday >= start - timedelta(days=7) and panel.dates[r["week"].e] >= start]


def run_book(rows, panel, src, cand, costs=Costs(), delay=0, exclude=None, abstain=False, signal=None):
    """Weekly net returns of a candidate book. `cand`: {"signal", "direction", "regime" or None}."""
    sig = signal or cand["signal"]
    book = Book(costs)
    out = []
    for row in rows:
        w = row["week"]
        e = min(w.e + delay, len(panel.dates) - 1)
        t = ny_epoch(panel.dates[e], *NOON)
        q = quotes_at(src, t)
        if q is None:
            continue
        s = row["scores"][sig].copy()
        if exclude is not None:
            s[CURRENCIES.index(exclude)] = np.nan
        target = cand["direction"] * rank_weights(s)
        if cand.get("regime") and row["regime"] != cand["regime"]:
            target = np.zeros(len(CURRENCIES))
        if abstain and not row["disp_ok"].get(sig):
            target = np.zeros(len(CURRENCIES))
        res = book.step(panel.dates[e], q, target, row["rates"])
        res["date"] = panel.dates[e]
        res["regime"] = row["regime"]
        res["weights"] = target
        out.append(res)
    return out[1:]  # the first step only opens positions


def _series(res, key="net"):
    return np.array([r[key] for r in res], float)


def _stats(x):
    x = x[np.isfinite(x)]
    return {"weeks": int(len(x)), "mean": _r(x.mean() if len(x) else np.nan), "t": _r(t_stat(x), 4),
            "sharpe_annual": _r(x.mean() / x.std(ddof=1) * np.sqrt(52)) if len(x) > 2 and x.std() > 0 else None,
            "total": _r(x.sum())}


def null_gross(rows, panel, src, cand):
    """Gross weekly returns of random rank books (same eligible currencies, same regime gating)."""
    rng = np.random.default_rng(SEED)
    rel = []
    prev = None
    for row in rows:
        w = row["week"]
        q = quotes_at(src, ny_epoch(panel.dates[w.e], *NOON))
        if q is None:
            continue
        v = np.array([0.0] + [np.log(1 / q[c].mid if c in ("JPY", "CHF", "CAD") else q[c].mid) for c in NON_USD])
        if prev is not None:
            r = v - prev[0]
            rel.append((prev[1], r - r.mean()))
        prev = (v, row)
    means = []
    for _ in range(NULL_DRAWS):
        tot, n = 0.0, 0
        for row, rr in rel:
            s = row["scores"][cand["signal"]]
            ok = np.isfinite(s)
            if cand.get("regime") and row["regime"] != cand["regime"]:
                continue
            if ok.sum() < MIN_CROSS_SECTION:
                continue
            perm = s.copy()
            perm[ok] = rng.permutation(s[ok])
            tot += float(rank_weights(perm) @ rr)
            n += 1
        means.append(tot / n if n else np.nan)
    return np.array(means)


def evaluate_candidate(hid, cand, rows, panel, src, s2_threshold, price_based):
    base = run_book(rows, panel, src, cand)
    net, gross = _series(base), _series(base, "gross")
    dates = [r["date"] for r in base]
    st = _stats(net)
    halves = [net[[(S2_HALVES[i] <= d < S2_HALVES[i + 1]) for d in dates]] for i in range(2)]
    years = {}
    for d, v in zip(dates, net):
        years.setdefault(d.year, []).append(v)
    yrs = {str(y): _r(np.mean(v)) for y, v in sorted(years.items()) if len(v) >= YEAR_MIN_WEEKS}
    contrib = {c: float(sum(r["contrib"][c] for r in base)) for c in CURRENCIES}
    tot = sum(contrib.values())
    loo = {c: _r(_series(run_book(rows, panel, src, cand, exclude=c)).mean()) for c in CURRENCIES}
    x2 = _series(run_book(rows, panel, src, cand, costs=Costs().stressed(2.0)))
    late = _series(run_book(rows, panel, src, cand, delay=1))
    abst = _series(run_book(rows, panel, src, cand, abstain=True))
    by_reg = {g: net[[r["regime"] == g for r in base]] for g in ("LOW", "HIGH")}
    if price_based:
        nul = null_gross(rows, panel, src, cand)
        inc = {"kind": "random-rank null", "null_pctl": _r(np.nanpercentile(nul, NULL_PCTL)),
               "candidate_gross_mean": _r(gross.mean()), "pass": bool(gross.mean() > np.nanpercentile(nul, NULL_PCTL))}
    else:
        ctrl = run_book(rows, panel, src, {"signal": "momentum", "direction": 1, "regime": cand.get("regime")})
        cg = {r["date"]: r["gross"] for r in ctrl}
        y = [g for d, g in zip(dates, gross) if d in cg]
        xx = [cg[d] for d in dates if d in cg]
        a, at = ols_alpha_t(y, xx)
        inc = {"kind": "OLS alpha over the price-only momentum book", "alpha": _r(a), "t": _r(at, 4),
               "control_gross_mean": _r(np.mean(list(cg.values()))), "pass": bool(np.isfinite(at) and at >= INCREMENT_T)}
    no5 = np.sort(net)[::-1][BEST_WEEKS_REMOVED:]
    robust = {
        "R1_halves": {"means": [_r(h.mean()) for h in halves], "pass": all(len(h) and h.mean() > 0 for h in halves)},
        "R2_years": {"by_year": yrs, "pass": bool(yrs) and sum(v > 0 for v in yrs.values()) / len(yrs) >= YEAR_SHARE},
        "R3_concentration": {"contribution": {c: _r(v) for c, v in contrib.items()},
                             "max_share": _r(max(contrib.values()) / tot) if tot > 0 else None,
                             "leave_one_out_net_mean": loo,
                             "pass": tot > 0 and max(contrib.values()) / tot <= CONCENTRATION
                             and all(v is not None and v > 0 for v in loo.values())},
        "R4_outliers": {"mean_without_5_best": _r(no5.mean()), "pass": bool(no5.mean() > 0)},
        "R5_costs": {"net_mean_costs_x2": _r(x2.mean()), "pass": bool(x2.mean() > 0)},
        "R6_execution": {"net_mean_one_day_later": _r(late.mean()), "pass": bool(late.mean() > 0)},
        "R7_regimes": {g: _stats(v) for g, v in by_reg.items()} | {
            "pass": not any(np.isfinite(t_stat(v)) and t_stat(v) <= -2 for v in by_reg.values())},
        "R8_incremental": inc,
    }
    all_r = all(v["pass"] for v in robust.values())
    if st["mean"] and st["mean"] > 0 and st["t"] is not None and st["t"] >= s2_threshold and all_r:
        status = "HOLDOUT_ELIGIBLE"
    elif st["mean"] and st["mean"] > 0 and st["t"] is not None and st["t"] >= PROMISING_T and all_r:
        status = "PROMISING"
    else:
        status = "REJECTED"
    return {"id": hid, "candidate": cand, "net": st, "gross": _stats(gross),
            "financing_mean": _r(_series(base, "financing").mean()), "cost_mean": _r(_series(base, "cost").mean()),
            "turnover_mean": _r(np.mean([np.abs(r["weights"]).sum() for r in base])),
            "abstention": _stats(abst), "robustness": robust, "threshold": round(s2_threshold, 4), "status": status}


# ── commands ─────────────────────────────────────────────────────────────────────────────────────

def pit_check(panel, rates, n=40) -> dict:
    """Signals at sampled decisions are unchanged when every H.10 date and rate unusable then is removed."""
    from aitrader.research.discovery.rv import Panel, Week
    weeks = calendar(panel, S1[0], S2[1])
    idx = np.linspace(60, len(weeks) - 1, n).astype(int)
    bad = 0
    for i in idx:
        w = weeks[i]
        t = ny_epoch(w.friday, 17)
        keep = panel.available <= t
        cut = Panel(tuple(d for d, k in zip(panel.dates, keep) if k), panel.available[keep],
                    {c: v[keep] for c, v in panel.logv.items()})
        d2 = cut.last_available(t)  # recomputed from the truncated data alone
        if d2 != w.d:
            bad += 1
            continue
        w2 = Week(w.friday, d2, w.e, w.x)  # forward indices are not used by any signal
        rn = rates_at([s.truncated(t) for s in rates], t)
        a, b = scores(panel, w, rates_at(rates, t)), scores(cut, w2, rn)
        for k in SIGNALS:
            if not np.allclose(np.nan_to_num(a[k], nan=-9e9), np.nan_to_num(b[k], nan=-9e9)):
                bad += 1
        if global_vol(panel, w) != global_vol(cut, w2) and np.isfinite(global_vol(panel, w)):
            bad += 1
    return {"decisions_checked": int(len(idx)), "differences": bad}


def cmd_spec():
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    if abs(s["stage1"]["threshold_registry"] - S1_THRESHOLD) > 5e-4:
        raise SystemExit(f"the registry requires t >= {s['stage1']['threshold_registry']}, not {S1_THRESHOLD}")
    panel, rates = load(holdout)
    pit = pit_check(panel, rates)
    if pit["differences"]:
        raise SystemExit(f"LOOK-AHEAD: {pit}")
    sha = spec_sha(s)
    SPEC.write_text(json.dumps({"spec": s, "sha256": sha, "code_sha256": code_hash(), "pit_check": pit}, indent=1,
                               sort_keys=True) + "\n")
    print(sha, "stage-1 threshold", s["stage1"]["threshold_registry"], "pit", pit)


def cmd_preregister(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    sha = spec_sha(s)
    if sha != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if sha not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {sha}")
    t = reg.register(Trial(id=PID, registered=now, title="RV-1 Stage 1: cross-sectional currency information",
                           hypothesis=s["question"], uses=tuple(Use(UNIVERSE_KEY, a, b, r) for a, b, r in S1_USES),
                           tests=len(HYPOTHESES), configurations=len(HYPOTHESES), preregistration=DOC,
                           design={"spec_sha256": sha, "code_sha256": frozen["code_sha256"], "spec": s}))
    print(f"registered {t.id}: {t.tests} tests, |t| >= {S1_THRESHOLD}")


def _check_frozen(reg, trial_id):
    trial = reg.get(trial_id)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def _write(name, body):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def cmd_stage1(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict; Stage 1 runs once")
    frozen = _check_frozen(reg, PID)
    panel, rates = load(holdout)
    table = stage1_table(panel, rates)
    results = {}
    for hid, h in HYPOTHESES.items():
        results[hid] = _summary_signal(table, h["signal"]) if h["kind"] == "signal" else _summary_regime(table, h["signal"])
        r = results[hid]
        print(f"{hid:22} t={r['t']} passed={r['passed']} gates={r['gates']}")
    passing = [k for k, v in results.items() if v["passed"]]
    verdict = "PASSED" if passing else "FAILED"
    body = _write(PID, {"program": PID, "kind": "cross_sectional", "stage": 1, "version": RV_VERSION,
                        "design_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                        "threshold": S1_THRESHOLD, "period": [S1[0].isoformat(), S1[1].isoformat()],
                        "weeks_in_table": len(table), "results": results, "passing": passing,
                        "verdict": verdict,
                        "classification": {k: ("STAGE2" if k in passing else "REJECTED") for k in HYPOTHESES}})
    reg.record_verdict(Verdict(PID, now, verdict, {"artifact": f"research/knowledge/{PID}.json",
                                                   "artifact_sha256": body["sha256"], "passing": passing}))
    print(verdict, passing)


def cmd_stage2(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    s1 = json.loads((OUT / f"{PID}.json").read_text())
    if not s1["passing"]:
        raise SystemExit("Stage 1 FAILED: there is no Stage 2")
    if any(t.id == S2ID for t in reg.trials):
        raise SystemExit(f"{S2ID} already exists; Stage 2 runs once")
    frozen = _check_frozen(reg, PID)
    n = len(s1["passing"])
    thr = reg.threshold_for_next(UNIVERSE_KEY, S2[0], S2[1], new_tests=n)
    reg.register(Trial(id=S2ID, registered=now, title="RV-1 Stage 2: realistic currency-neutral books",
                       hypothesis="Stage-1 passers on bid/ask with costs, 2008-07..2016",
                       uses=(Use(UNIVERSE_KEY, S2[0], S2[1], "judge"),), tests=n, configurations=n, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": s1["passing"], "threshold_t": thr}))
    panel, rates = load(holdout)
    store = DataStore(ROOT / "data" / "processed", holdout)
    src = quote_source(store)
    rows = stage2_weeks(panel, rates, S2[0], S2[1])
    out = {}
    for hid in s1["passing"]:
        h, r1 = HYPOTHESES[hid], s1["results"][hid]
        cand = {"signal": h["signal"], "direction": r1["direction"], "regime": r1.get("candidate_regime")}
        out[hid] = evaluate_candidate(hid, cand, rows, panel, src, thr, h["price_based"])
        print(hid, out[hid]["status"], out[hid]["net"])
    eligible = sorted((k for k, v in out.items() if v["status"] == "HOLDOUT_ELIGIBLE"), key=lambda k: -out[k]["net"]["t"])
    for k in eligible[1:]:
        out[k]["status"] = "PROMISING"  # one candidate opens the holdout (RESEARCH_PROTOCOL section 2)
    verdict = "PASSED" if eligible else "FAILED"
    body = _write(S2ID, {"program": S2ID, "kind": "cross_sectional", "stage": 2, "design_sha256": frozen["sha256"],
                         "code_sha256": frozen["code_sha256"], "threshold": round(thr, 4), "results": out,
                         "holdout_candidate": eligible[0] if eligible else None, "verdict": verdict,
                         "classification": {k: v["status"] for k, v in out.items()}})
    reg.record_verdict(Verdict(S2ID, now, verdict, {"artifact": f"research/knowledge/{S2ID}.json",
                                                    "artifact_sha256": body["sha256"]}))


def cmd_holdout(now):
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    s2 = json.loads((OUT / f"{S2ID}.json").read_text())
    hid = s2.get("holdout_candidate")
    if not hid:
        raise SystemExit("no candidate passed everything else: the sealed holdout stays sealed")
    frozen = _check_frozen(reg, PID)
    reg.register(Trial(id=HID, registered=now, title=f"RV-1 sealed holdout: {hid}", hypothesis=HYPOTHESES[hid]["text"],
                       uses=(Use(UNIVERSE_KEY, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "candidate": hid}))
    key = open_final_test(reg, HID)
    panel, rates = load(holdout, key)
    src = quote_source(DataStore(ROOT / "data" / "processed", holdout), key)
    rows = stage2_weeks(panel, rates, HOLD[0], HOLD[1])
    cand = s2["results"][hid]["candidate"]
    net = _series(run_book(rows, panel, src, cand))
    x2 = _series(run_book(rows, panel, src, cand, costs=Costs().stressed(2.0)))
    st = _stats(net)
    ok = bool(st["mean"] and st["mean"] > 0 and st["t"] is not None and st["t"] >= HOLDOUT_T and x2.mean() > 0)
    body = _write(HID, {"program": HID, "kind": "cross_sectional", "holdout_of": S2ID, "candidate": hid, "net": st,
                        "net_mean_costs_x2": _r(x2.mean()), "verdict": "PASSED" if ok else "FAILED",
                        "classification": {hid: "VALIDATED" if ok else "REJECTED"}})
    reg.record_verdict(Verdict(HID, now, body["verdict"], {"artifact": f"research/knowledge/{HID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(json.dumps(body["net"]), body["verdict"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("spec", "preregister", "stage1", "stage2", "holdout"))
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "stage1": lambda: cmd_stage1(now),
     "stage2": lambda: cmd_stage2(now), "holdout": lambda: cmd_holdout(now)}[a.cmd]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
