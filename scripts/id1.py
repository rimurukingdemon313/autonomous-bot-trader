"""ID-1: intraday M5 edge program (research/preregistrations/ID-1.md).

    python scripts/id1.py spec | preregister
    python scripts/id1.py run        # stage 1 development 2009-2013 (all), stage 2 validation 2014-2016 (promoted only)
    python scripts/id1.py holdout    # only for validation passers: fx-majors 2017-01 -> 2022-07, opened once

Data: data/m5/<SYMBOL>_M5_2009_2016.npz (branch id-data; scripts/ingest_dukascopy.py --timeframe M5).
The sealed period is never built until `holdout` (data/m5/<SYMBOL>_M5_2017_2022.npz).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data import instruments  # noqa: E402
from aitrader.data.bars import BarSeries  # noqa: E402
from aitrader.data.store import open_final_test  # noqa: E402
from aitrader.research.discovery import intraday as ID  # noqa: E402
from aitrader.research.discovery import rc  # noqa: E402
from aitrader.research.discovery.stats import welch_t  # noqa: E402
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict  # noqa: E402

R = ROOT / "research"
PID, HID = "ID-1", "ID-1-H"
DOC = "research/preregistrations/ID-1.md"
SPEC = R / "specs" / "ID-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "m5"
CODE = ("aitrader/research/discovery/intraday.py", "scripts/id1.py")
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "XAUUSD")
CCY = {"EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"), "USDJPY": ("USD", "JPY"), "AUDUSD": ("AUD", "USD"),
       "USDCAD": ("USD", "CAD"), "USDCHF": ("USD", "CHF"), "NZDUSD": ("NZD", "USD"), "XAUUSD": ("XAU", "USD")}
AREA = {"USD": "US", "EUR": "XM", "GBP": "GB", "JPY": "JP", "AUD": "AU", "NZD": "NZ", "CAD": "CA", "CHF": "CH"}


def _ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


DEV = (date(2009, 1, 1), date(2014, 1, 1))
VAL = (date(2014, 1, 1), date(2017, 1, 1))
HOLD = (date(2017, 1, 1), date(2022, 7, 9))
WARMUP_DAYS = 31
COSTS = ID.Costs()
RISK_PCT = 0.5
RISK_LEVELS = (0.25, 0.5, 1.0)
COST_GRID = (1.25, 1.5, 2.0)
SLIP_STRESS = 0.3  # pips per fill
RANDOM_SEEDS = (11, 12, 13)

#: id -> (family, rule, primary params, neighbourhood grid for robustness)
HYPOTHESES = {
    "A1-SWEEP-PDHL": ("liquidity", "sweep_pd", {}, {"pen": [0.05, 0.10, 0.15, 0.20], "r": [1.5, 2.0, 2.5]}),
    "A2-SWEEP-ASIA": ("liquidity", "sweep_asia", {}, {"pen": [0.05, 0.10, 0.15, 0.20], "r": [1.5, 2.0, 2.5]}),
    "A3-SWEEP-EQUAL": ("liquidity", "sweep_equal", {}, {"tol": [0.05, 0.10, 0.15], "r": [1.5, 2.0, 2.5]}),
    "A4-BOS-FVG": ("liquidity", "bos_fvg", {}, {"body": [1.0, 1.2, 1.4], "r": [1.5, 2.0, 2.5]}),
    "A5-CHOCH": ("liquidity", "choch", {}, {"k": [2, 3, 4], "r": [1.5, 2.0, 2.5]}),
    "A6-ORDER-BLOCK": ("liquidity", "order_block", {}, {"body": [1.0, 1.2, 1.4], "r": [1.5, 2.0, 2.5]}),
    "B1-OPENING-RANGE": ("price", "opening_range", {}, {"r": [1.5, 2.0, 2.5], "max_atr": [3.0, 4.0, 5.0]}),
    "B2-SQUEEZE": ("price", "squeeze", {}, {"pct": [0.05, 0.10, 0.15], "n": [15, 20, 25]}),
    "B3-MOMENTUM": ("price", "momentum", {}, {"n": [9, 12, 15], "z": [1.75, 2.0, 2.25]}),
    "B4-MEAN-REVERSION": ("price", "mean_reversion", {}, {"d": [2.0, 2.5, 3.0], "stop_atr": [1.25, 1.5, 1.75]}),
    "B5-FAILED-BREAKOUT": ("price", "failed_breakout", {}, {"look": [36, 42, 48, 54, 60], "r": [1.5, 2.0, 2.5]}),
    "B6-SESSION-OPEN": ("price", "session_open", {}, {"stop_atr": [1.25, 1.5, 1.75], "r": [1.5, 2.0, 2.5]}),
    "C1-USD-LAG": ("cross", "usd_lag", {}, {"z": [1.75, 2.0, 2.25], "lag": [0.25, 0.5, 0.75]}),
    "D1-BEST-SWEEP+HIGH-VOL": ("hybrid", "best_liquidity+atr_rank>=0.5", {}, {}),
    "D2-MOMENTUM+OVERLAP": ("hybrid", "momentum, entries 12:00-16:00 UTC only", {}, {}),
    "D3-SQUEEZE+H1-TREND": ("hybrid", "squeeze, only in the direction of the H1 EMA50 slope", {}, {}),
}
CONTROLS = {"E1-RANDOM": None, "E2-RANDOM-LONG": 1, "E3-RANDOM-SHORT": -1}
PROMOTE = {"min_trades": 300, "net_r": "> 0", "t_day": 2.0, "profit_factor": 1.10, "beats_matched_random_welch_t": 2.0,
           "symbols_positive_share": 0.6}
JUDGE = {"t_day": "max(3.0, registry Bonferroni)", "net_r": "> 0", "profit_factor": 1.20, "costs_x1.5_net_r": "> 0",
         "symbols_positive_share": 0.6, "three_month_windows_profitable": 0.6, "grid_positive_share": 0.75,
         "beats_matched_random_welch_t": 2.0, "hybrid_beats_component": "validation net_r above its component's"}
HOLDOUT_RULE = ("passers only, fx-majors 2017-01 -> 2022-07 (M5 built only then): t_day >= z(1-0.05/k) one-sided, "
                "net_r > 0, profit factor >= 1.1, costs x1.5 net_r > 0, three-month windows profitable >= 0.55")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def spec(reg: Registry) -> dict:
    t = reg.threshold_for_next("fx-majors", *VAL, new_tests=len(HYPOTHESES))
    return {"program": PID, "version": ID.INTRADAY_VERSION, "symbols": SYMBOLS, "hypotheses": HYPOTHESES,
            "controls": list(CONTROLS), "promote": PROMOTE, "judge": JUDGE, "holdout_rule": HOLDOUT_RULE,
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "costs": COSTS.__dict__, "cost_grid": COST_GRID, "slippage_stress_pips": SLIP_STRESS, "risk_pct": RISK_PCT,
            "risk_levels": RISK_LEVELS, "random_seeds": RANDOM_SEEDS, "t_required_validation": round(max(3.0, t), 4)}


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


# ── data ────────────────────────────────────────────────────────────────

def load(period: tuple[date, date], tag: str = "_2009_2016", key=None) -> dict[str, ID.Bars]:
    """Bars from WARMUP_DAYS before the period to its end. The sealed period needs the holdout key."""
    lo, hi = _ts(period[0]) - WARMUP_DAYS * 86400, _ts(period[1])
    if hi > _ts(HOLD[0]) and key is None:
        raise SystemExit("data from 2017 is the fx-majors holdout: a key from open_final_test is required")
    out = {}
    for s in SYMBOLS:
        f = DATA / f"{s}_M5{tag}.npz"
        if not f.exists():
            continue
        bs = BarSeries.load(f)
        m = (bs.open_time >= lo) & (bs.open_time < hi)
        if m.sum() < 1000:
            continue
        out[s] = ID.Bars(s, instruments.get(s).pip, bs.open_time[m], bs.bid_open[m], bs.bid_high[m], bs.bid_low[m],
                         bs.bid_close[m], bs.ask_open[m], bs.ask_high[m], bs.ask_low[m], bs.ask_close[m])
    return out


def carry_fn(symbol: str, rates: rc.Rates):
    base, quote = CCY[symbol]

    def carry(side: int, t: int) -> float:
        d = datetime.fromtimestamp(t, timezone.utc).date()
        rb = 0.0 if base == "XAU" else rates.at(AREA[base], d)
        rq = rates.at(AREA[quote], d)
        return side * (rb - rq)

    return carry


# ── signals ─────────────────────────────────────────────────────────────

def signals(hid: str, panel: dict, params: dict | None = None, best_liquidity: str | None = None) -> dict:
    fam, rule, prim, _ = HYPOTHESES[hid]
    p = {**prim, **(params or {})}
    if rule == "usd_lag":
        return ID.usd_lag(panel, **p)
    if hid == "D1-BEST-SWEEP+HIGH-VOL":
        base = signals(best_liquidity, panel)
        out = {}
        for k, sig in base.items():
            rk = ID.atr_rank(panel[k])
            out[k] = ID.filtered(sig, lambda s, rk=rk: rk[s.i] >= 0.5)
        return out
    if hid == "D2-MOMENTUM+OVERLAP":
        base = signals("B3-MOMENTUM", panel)
        return {k: ID.filtered(v, lambda s, b=panel[k]: 12 <= b.hour[s.i] < 16) for k, v in base.items()}
    if hid == "D3-SQUEEZE+H1-TREND":
        base = signals("B2-SQUEEZE", panel)
        out = {}
        for k, sig in base.items():
            tr = ID.h1_trend(panel[k])
            out[k] = ID.filtered(sig, lambda s, tr=tr: np.isfinite(tr[s.i]) and tr[s.i] == s.side)
        return out
    fn = getattr(ID, rule)
    return {k: fn(b, **p) for k, b in panel.items()}


def control_signals(cid: str, panel: dict) -> dict:
    side = CONTROLS[cid]
    return {k: ID.random_entries(b, seed=17 + i, side=side) for i, (k, b) in enumerate(sorted(panel.items()))}


def run_trades(panel: dict, sigs: dict, rates: rc.Rates, period, costs: ID.Costs = COSTS) -> list[ID.Trade]:
    lo, hi = _ts(period[0]), _ts(period[1])
    out = []
    for k, b in panel.items():
        tr, _ = ID.simulate(b, sigs.get(k, []), costs, carry_fn(k, rates))
        out += [t for t in tr if lo <= t.entry_t < hi]
    return sorted(out, key=lambda t: t.exit_t)


# ── evaluation ──────────────────────────────────────────────────────────

def _months(period):
    return (period[0].year, period[0].month), ((period[1].year if period[1].month > 1 else period[1].year - 1),
                                               (period[1].month - 1 or 12))


def evaluate(trades: list[ID.Trade], period, panel=None) -> dict:
    per = (_ts(period[0]), _ts(period[1]))
    s = ID.summarize(trades, RISK_PCT, per)
    if not trades:
        return s
    months = ID.monthly_r(trades)
    a, b = _months(period)
    s["windows"] = {f"{n}m": ID.rolling_windows(months, a, b, n, RISK_PCT) for n in (1, 3, 6)}
    s["monthly_r"] = {f"{y}-{m:02d}": round(v, 3) for (y, m), v in months.items()}
    s["by_symbol"] = {}
    for k in sorted({t.symbol for t in trades}):
        sub = [t for t in trades if t.symbol == k]
        s["by_symbol"][k] = {"trades": len(sub), "net_r": round(float(np.mean([t.r for t in sub])), 4)}
    s["by_year"] = {}
    for t in trades:
        y = datetime.fromtimestamp(t.entry_t, timezone.utc).year
        s["by_year"].setdefault(y, []).append(t.r)
    s["by_year"] = {y: {"trades": len(v), "net_r": round(float(np.mean(v)), 4), "total_r": round(float(np.sum(v)), 2)}
                    for y, v in sorted(s["by_year"].items())}
    sess = {"london_07_12": (7, 12), "overlap_12_16": (12, 16), "newyork_16_20": (16, 20), "other": (20, 31)}
    s["by_session"] = {}
    for name, (h0, h1) in sess.items():
        sub = [t.r for t in trades if h0 <= (t.entry_t // 3600) % 24 < h1 or (name == "other" and (t.entry_t // 3600) % 24 < 7)]
        if sub:
            s["by_session"][name] = {"trades": len(sub), "net_r": round(float(np.mean(sub)), 4)}
    s["risk_levels"] = {f"{x}%": {"net_return_pct": round(s["total_r"] * x, 2),
                                  "max_drawdown_pct": round(s["max_drawdown_pct"] * x / RISK_PCT, 2)} for x in RISK_LEVELS}
    if panel is not None:
        s["regimes"] = regimes(trades, panel)
        s["concurrency"] = concurrency(trades)
    return s


def regimes(trades, panel) -> dict:
    """Net R by the regime at the signal bar: ATR in the top or bottom half of its past week; trend or
    range by the 48-bar efficiency ratio (>= 0.3 trending). All computed from past bars only."""
    cache = {}
    out = {"high_vol": [], "low_vol": [], "trending": [], "ranging": []}
    for t in trades:
        b = panel[t.symbol]
        if t.symbol not in cache:
            c = b.c
            move = np.abs(np.r_[np.full(48, np.nan), c[48:] - c[:-48]])
            path = np.r_[np.full(48, np.nan), np.convolve(np.abs(np.diff(c)), np.ones(48), "valid")]
            cache[t.symbol] = (ID.atr_rank(b), move / np.where(path > 0, path, np.nan))
        rk, er = cache[t.symbol]
        i = t.signal_i
        if np.isfinite(rk[i]):
            out["high_vol" if rk[i] >= 0.5 else "low_vol"].append(t.r)
        if np.isfinite(er[i]):
            out["trending" if er[i] >= 0.3 else "ranging"].append(t.r)
    return {k: {"trades": len(v), "net_r": round(float(np.mean(v)), 4) if v else None} for k, v in out.items()}


def concurrency(trades) -> dict:
    ev = sorted([(t.entry_t, 1) for t in trades] + [(t.exit_t + 300, -1) for t in trades])
    cur = mx = 0
    over, last_t, span = 0, None, 0
    for tm, d in ev:
        if last_t is not None and cur > 3:
            over += tm - last_t
        if last_t is not None and cur > 0:
            span += tm - last_t
        cur += d
        mx = max(mx, cur)
        last_t = tm
    return {"max_simultaneous": mx, "share_of_exposed_time_above_3": round(over / span, 4) if span else 0.0}


def matched(panel, sigs, rates, period) -> list[ID.Trade]:
    out = []
    for seed in RANDOM_SEEDS:
        ms = {k: ID.matched_random(b, sigs.get(k, []), seed + i) for i, (k, b) in enumerate(sorted(panel.items()))}
        out += run_trades(panel, ms, rates, period)
    return out


def promote_gates(s: dict, vs_random: float | None) -> dict:
    sym = [v for v in s.get("by_symbol", {}).values() if v["trades"] >= 30]
    return {"min_trades": s.get("trades", 0) >= PROMOTE["min_trades"], "net_r": (s.get("net_r") or 0) > 0,
            "t_day": (s.get("t_day") or 0) >= PROMOTE["t_day"],
            "profit_factor": (s.get("profit_factor") or 0) >= PROMOTE["profit_factor"],
            "beats_matched_random": (vs_random or 0) >= PROMOTE["beats_matched_random_welch_t"],
            "symbols_positive": bool(sym) and np.mean([v["net_r"] > 0 for v in sym]) >= PROMOTE["symbols_positive_share"]}


def _brief(s: dict) -> dict:
    keys = ("trades", "trades_per_month", "win_rate", "avg_win_r", "avg_loss_r", "gross_r", "spread_r", "commission_r",
            "slippage_r", "financing_r", "net_r", "t_day", "profit_factor", "net_return_pct", "annual_return_pct",
            "sharpe", "max_drawdown_pct", "top10pct_share")
    out = {k: s.get(k) for k in keys}
    w = s.get("windows", {}).get("3m", {})
    out["three_month_profitable"] = w.get("profitable_share")
    return out


def _grid(g: dict) -> list[dict]:
    cells = [{}]
    for k, vals in g.items():
        cells = [{**c, k: v} for c in cells for v in vals]
    return cells


def _check_frozen(reg, trial_id):
    frozen = json.loads(SPEC.read_text())
    if reg.get(trial_id).design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def _write(name, body):
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


def cmd_spec():
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    s = spec(reg)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "t_required_validation", s["t_required_validation"])


def cmd_preregister(now):
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    if spec_sha(spec(reg)) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256")
    reg.register(Trial(id=PID, registered=now, title="ID-1: intraday M5 edge program (liquidity/SMC, price, cross-market, hybrids)",
                       hypothesis="Does any precisely defined M5 rule earn a significant net expectancy after measured "
                                  "bid/ask spreads, commission, slippage and financing, beyond matched random entries?",
                       uses=(Use("fx-majors", DEV[0], DEV[1], "select"), Use("fx-majors", VAL[0], VAL[1], "judge")),
                       tests=len(HYPOTHESES), configurations=sum(max(1, len(_grid(h[3]))) for h in HYPOTHESES.values()),
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"]}))
    print("registered", PID)


def cmd_run(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    t_req = frozen["spec"]["t_required_validation"]
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    body: dict = {"program": PID, "spec_sha256": frozen["sha256"], "t_required_validation": t_req,
                  "development": {}, "controls": {}, "validation": {}}
    # ── stage 1: development, every hypothesis and control ──
    dev = load(DEV)
    dev_sigs, dev_trades = {}, {}
    for cid in CONTROLS:
        tr = run_trades(dev, control_signals(cid, dev), rates, DEV)
        body["controls"][cid] = {"development": _brief(evaluate(tr, DEV))}
        print(cid, "dev", json.dumps(_brief(evaluate(tr, DEV))), flush=True)
    liquidity = [h for h, v in HYPOTHESES.items() if v[0] == "liquidity"]
    order = [h for h in HYPOTHESES if not h.startswith("D1")] + ["D1-BEST-SWEEP+HIGH-VOL"]
    best_liq = None
    for hid in order:
        if hid == "D1-BEST-SWEEP+HIGH-VOL":
            ranked = [(body["development"][h]["summary"]["net_r"] or -9, h) for h in liquidity
                      if (body["development"][h]["summary"]["trades"] or 0) >= PROMOTE["min_trades"]]
            best_liq = max(ranked)[1] if ranked else liquidity[0]
            body["d1_component"] = best_liq
        sig = signals(hid, dev, best_liquidity=best_liq)
        tr = run_trades(dev, sig, rates, DEV)
        s = evaluate(tr, DEV, dev)
        mr = matched(dev, sig, rates, DEV)
        vs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in mr])) if tr and mr else None
        g = promote_gates(s, vs)
        body["development"][hid] = {"summary": _brief(s), "detail": s, "matched_random": _brief(evaluate(mr, DEV)),
                                    "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None,
                                    "gates": g, "promoted": all(g.values())}
        dev_sigs[hid], dev_trades[hid] = sig, tr
        print(hid, "dev", json.dumps(_brief(s)), "vsR", vs, "promoted", all(g.values()), flush=True)
    promoted = [h for h in HYPOTHESES if body["development"][h]["promoted"]]
    body["promoted"] = promoted
    # ── stage 2: validation, promoted hypotheses only (controls for reference) ──
    val = load(VAL)
    for cid in CONTROLS:
        tr = run_trades(val, control_signals(cid, val), rates, VAL)
        body["controls"][cid]["validation"] = _brief(evaluate(tr, VAL))
    for hid in promoted:
        body["validation"][hid] = validate(hid, val, rates, t_req, best_liq)
        print(hid, "val", json.dumps(body["validation"][hid]["summary"]), "passed", body["validation"][hid]["passed"], flush=True)
    passers = [h for h in promoted if body["validation"][h]["passed"]]
    body["passers"], body["verdict"] = passers, ("PASSED" if passers else "FAILED")
    art = _write(PID, body)
    reg.record_verdict(Verdict(PID, now, art["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                          "artifact_sha256": art["sha256"]}))
    print("verdict", art["verdict"], "promoted", promoted, "passers", passers)


def validate(hid, val, rates, t_req, best_liq) -> dict:
    sig = signals(hid, val, best_liquidity=best_liq)
    tr = run_trades(val, sig, rates, VAL)
    s = evaluate(tr, VAL, val)
    mr = matched(val, sig, rates, VAL)
    vs = welch_t(np.array([t.r for t in tr]), np.array([t.r for t in mr])) if tr and mr else None
    stress = {f"x{k}": _brief(evaluate(run_trades(val, sig, rates, VAL, COSTS.stressed(k)), VAL)) for k in COST_GRID}
    slip = ID.Costs(slippage_pips=SLIP_STRESS)
    stress["slippage_0.3"] = _brief(evaluate(run_trades(val, sig, rates, VAL, slip), VAL))
    grid = []
    g = HYPOTHESES[hid][3]
    for cell in _grid(g) if g else []:
        gs = evaluate(run_trades(val, signals(hid, val, cell, best_liq), rates, VAL), VAL)
        grid.append({"params": cell, "trades": gs.get("trades"), "net_r": gs.get("net_r"), "t_day": gs.get("t_day")})
    sym = [v for v in s.get("by_symbol", {}).values() if v["trades"] >= 30]
    gates = {"t_day": (s.get("t_day") or 0) >= t_req, "net_r": (s.get("net_r") or 0) > 0,
             "profit_factor": (s.get("profit_factor") or 0) >= 1.2,
             "costs_x1.5": (stress["x1.5"].get("net_r") or 0) > 0,
             "symbols_positive": bool(sym) and np.mean([v["net_r"] > 0 for v in sym]) >= 0.6,
             "three_month_windows": (s.get("windows", {}).get("3m", {}).get("profitable_share") or 0) >= 0.6,
             "beats_matched_random": (vs or 0) >= 2.0}
    if grid:
        gates["grid"] = np.mean([(c["net_r"] or 0) > 0 for c in grid]) >= 0.75
    if hid.startswith("D"):
        comp = {"D1-BEST-SWEEP+HIGH-VOL": best_liq, "D2-MOMENTUM+OVERLAP": "B3-MOMENTUM",
                "D3-SQUEEZE+H1-TREND": "B2-SQUEEZE"}[hid]
        cs = evaluate(run_trades(val, signals(comp, val), rates, VAL), VAL)
        gates["beats_component"] = (s.get("net_r") or -9) > (cs.get("net_r") or 0)
    return {"summary": _brief(s), "detail": s, "matched_random": _brief(evaluate(mr, VAL)),
            "vs_matched_random_welch_t": round(vs, 3) if vs is not None else None, "stress": stress, "grid": grid,
            "gates": gates, "passed": all(gates.values())}


def cmd_holdout(now):
    reg = _registry()
    frozen = _check_frozen(reg, PID)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    passers = judged["passers"]
    if not passers:
        raise SystemExit("nothing passed validation: the fx-majors holdout stays sealed")
    reg.register(Trial(id=HID, registered=now, title="ID-1 holdout: fx-majors 2017-01 -> 2022-07 (M5)",
                       hypothesis=", ".join(passers), uses=(Use("fx-majors", HOLD[0], date(2100, 1, 1), "judge"),),
                       tests=len(passers), configurations=len(passers), preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "candidates": passers}))
    key = open_final_test(reg, HID)
    rates = rc.Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    data = load(HOLD, tag="_2017_2022", key=key)
    z = NormalDist().inv_cdf(1 - 0.05 / len(passers))
    out = {}
    for hid in passers:
        sig = signals(hid, data, best_liquidity=judged.get("d1_component"))
        tr = run_trades(data, sig, rates, HOLD)
        s = evaluate(tr, HOLD, data)
        x15 = evaluate(run_trades(data, sig, rates, HOLD, COSTS.stressed(1.5)), HOLD)
        g = {"t_day": (s.get("t_day") or 0) >= z, "net_r": (s.get("net_r") or 0) > 0,
             "profit_factor": (s.get("profit_factor") or 0) >= 1.1, "costs_x1.5": (x15.get("net_r") or 0) > 0,
             "three_month_windows": (s.get("windows", {}).get("3m", {}).get("profitable_share") or 0) >= 0.55}
        out[hid] = {"summary": _brief(s), "detail": s, "costs_x1.5": _brief(x15), "gates": g,
                    "verdict": "VALIDATED" if all(g.values()) else "REJECTED"}
    verdict = "PASSED" if any(v["verdict"] == "VALIDATED" for v in out.values()) else "FAILED"
    art = _write(HID, {"program": HID, "holdout_of": PID, "results": out, "verdict": verdict, "t_required": round(z, 4)})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json", "artifact_sha256": art["sha256"]}))
    print("holdout verdict", verdict)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)
    {"spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "run": lambda: cmd_run(now),
     "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    sys.exit(main())
