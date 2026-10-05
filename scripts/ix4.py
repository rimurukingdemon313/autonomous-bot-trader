"""IX-4: the NASDAQ opening-candle EMA(12) signal (research/preregistrations/IX-4.md).

    python scripts/ix4.py spec          # freeze the design
    python scripts/ix4.py preregister   # register the development trial (after the document quotes the hash)
    python scripts/ix4.py develop       # development 2012-2016, once: all 10 exits, baselines, stress
    python scripts/ix4.py validate      # validation 2017-2020, once, promoted exits only
    python scripts/ix4.py holdout       # 2021-2024, once, validation passers only (bars fetched only then)

The video that motivated this reported +982%. That number is never used here: it is not a target, a
filter or a benchmark.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.bars import BarSeries  # noqa: E402
from aitrader.research.discovery import ixopen as O  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

PID, VID, HID = "IX-4", "IX-4-V", "IX-4-H"
R = ROOT / "research"
DOC = "research/preregistrations/IX-4.md"
SPEC = R / "specs" / "IX-4.json"
OUT_DEV, OUT_VAL, OUT_HOLD = (R / "knowledge" / f for f in ("IX-4-dev.json", "IX-4-val.json", "IX-4-H.json"))
CODE = ("aitrader/research/discovery/ixopen.py", "scripts/ix4.py")
DATA = ROOT / "data" / "ix"
UNIVERSE = "index-cfd-intraday"
SYMBOL = "USATECHIDXUSD"
DEV = ("2012-01-01", "2017-01-01")
VAL = ("2017-01-01", "2021-01-01")
HOLD = ("2021-01-01", "2025-01-01")
EMA_N = 12
EMA_ROBUST = (8, 10, 14, 16)
SEEDS = (1, 2, 3)
SLIP_SPREAD_FRACTION = 0.25
PROMOTE = {"min_trades": 300, "net_bps": "> 0", "t_day": 2.0, "costs_x1.5": "> 0",
           "vs_random_direction_welch_t": 2.0}
GATES = {"net_bps": "> 0", "t_day": ">= Bonferroni over every registered test", "costs_x1.5": "> 0",
         "costs_x2": "> 0 (else FRAGILE)", "delay": "> 0 with entry one bar (5 min) later",
         "halves": "both > 0", "profit_factor": ">= 1.05 on R", "top_year_share": "<= 0.5",
         "vs_random_direction_welch_t": ">= 2.0"}
HOLDOUT_RULE = "validation passers only, once: net > 0, t >= z(1 - 0.05 / k), costs x1.5 > 0, delay > 0"


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()


def spec() -> dict:
    return {"program": PID, "version": O.IXO_VERSION, "symbol": SYMBOL, "universe": UNIVERSE,
            "session": {"tz": "America/New_York", "signal_bar_opens": "09:30", "session_close": "16:00"},
            "ema": {"n": EMA_N, "of": "mid close", "series": "full continuous M5 (primary)",
                    "variant_reported": "regular-session bars only", "robustness_reported": list(EMA_ROBUST)},
            "entry": "open of the next bar (09:35), bid/ask + slippage; delay stress: one bar later",
            "exits": list(O.EXITS), "development": list(DEV), "validation": list(VAL), "holdout": list(HOLD),
            "costs": {"spread": "bar bid/ask", "slippage_per_fill": f"{SLIP_SPREAD_FRACTION} x median spread "
                      "of the development bars at 09:35", "commission": 0.0, "financing": "none (flat by 16:00)"},
            "baselines": ["random direction, same bars (3 seeds)", "random 09:35-15:00 bar with the EMA side "
                          "(3 seeds)", "random bar and side (3 seeds)", "first-candle direction, no EMA",
                          "session long 09:35 -> 16:00"],
            "promote": PROMOTE, "gates": GATES, "holdout_rule": HOLDOUT_RULE, "dev_tests": len(O.EXITS),
            "code_sha256": code_hash()}


def _epoch(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load(period: tuple[str, str]) -> O.OBars:
    parts = [BarSeries.load(p) for p in sorted(DATA.glob(f"{SYMBOL}_M5_*.npz"))]
    if not parts:
        raise FileNotFoundError(f"no {SYMBOL} M5 bars in {DATA}")
    s = BarSeries.concat(parts)
    s = s.take(np.argsort(s.open_time, kind="stable"))
    s = s.take(np.r_[True, np.diff(s.open_time) > 0])
    s = s.take((s.open_time >= _epoch(period[0])) & (s.open_time < _epoch(period[1])) & (s.ask_open >= s.bid_open))
    return O.OBars.from_series(s)


def slippage() -> float:
    b = load(DEV)
    sig = O.signals(b)
    return float(SLIP_SPREAD_FRACTION * np.median([b.ao[i + 1] - b.bo[i + 1] for _, i, _ in sig if i + 1 < len(b.t)]))


def stats_block(b: O.OBars, sigs, rule: str, slip: float, rnd: list) -> dict:
    base = O.simulate(b, sigs, rule, slip=slip)
    s = O.summary(base)
    days = sorted({x.day for x in base})
    mid = days[len(days) // 2] if days else None
    halves = [O.summary([x for x in base if x.day < mid]), O.summary([x for x in base if x.day >= mid])] if mid else []
    rnd_net = [x.net_bps for x in rnd]
    w = O.welch_t([x.net_bps for x in base], rnd_net)
    gross_book: dict = {}
    for x in base:
        gross_book[x.day] = gross_book.get(x.day, 0.0) + x.gross_bps
    g = np.array(list(gross_book.values()))
    t_gross = float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 and g.std() > 0 else None
    yearly: dict = {}
    for x in base:
        yearly[x.day.year] = yearly.get(x.day.year, 0.0) + x.net_bps
    tot = sum(yearly.values())
    return {"base": s, "q1_gross_t_day": round(t_gross, 3) if t_gross is not None else None,
            "x1.5": O.summary(O.simulate(b, sigs, rule, slip=slip, cost_mult=1.5)),
            "x2": O.summary(O.simulate(b, sigs, rule, slip=slip, cost_mult=2.0)),
            "delay": O.summary(O.simulate(b, sigs, rule, slip=slip, delay=1)),
            "halves": halves, "vs_random_direction_welch_t": round(w, 3) if w is not None else None,
            "top_year_share": round(max(yearly.values()) / tot, 3) if tot > 0 else None}


def regimes(b: O.OBars, sigs, rule: str, slip: float, cut: tuple[float, float]) -> dict:
    atr = O.atr14(b)
    mid = b.mid("c")
    rel = {d: atr[i] / mid[i] for d, i, _ in sigs}
    out = {}
    for name, lo, hi in (("low", -np.inf, cut[0]), ("mid", cut[0], cut[1]), ("high", cut[1], np.inf)):
        sub = [s for s in sigs if lo <= rel[s[0]] < hi]
        out[name] = {k: O.summary(O.simulate(b, sub, rule, slip=slip)).get(k) for k in ("trades", "net_bps", "t_day")}
    return out


def evaluate(period, slip: float, rules, cut=None) -> dict:
    b = load(period)
    sigs = O.signals(b, EMA_N)
    rnd_dir = [O.random_signals(b, sigs, s, "dir") for s in SEEDS]
    rnd_time = [O.random_signals(b, sigs, s, "time", EMA_N) for s in SEEDS]
    rnd_both = [O.random_signals(b, sigs, s, "both") for s in SEEDS]
    first = O.signals(b, how="first")
    res = {"signal_days": len(sigs), "long_share": round(float(np.mean([s > 0 for _, _, s in sigs])), 3), "exits": {}}
    for rule in rules:
        rd = [x for r in rnd_dir for x in O.simulate(b, r, rule, slip=slip)]
        blk = stats_block(b, sigs, rule, slip, rd)
        blk["baselines"] = {
            "random_direction": O.summary(rd),
            "random_time_ema_side": O.summary([x for r in rnd_time for x in O.simulate(b, r, rule, slip=slip)]),
            "random_time_random_side": O.summary([x for r in rnd_both for x in O.simulate(b, r, rule, slip=slip)]),
            "first_candle_no_ema": O.summary(O.simulate(b, first, rule, slip=slip)),
        }
        blk["ema_robustness"] = {str(n): {k: O.summary(O.simulate(b, O.signals(b, n), rule, slip=slip)).get(k)
                                          for k in ("trades", "net_bps", "t_day")} for n in EMA_ROBUST}
        blk["ema_rth_variant"] = {k: O.summary(O.simulate(b, O.signals(b, EMA_N, rth=True), rule, slip=slip)).get(k)
                                  for k in ("trades", "net_bps", "t_day")}
        if cut is not None:
            blk["volatility_regimes"] = regimes(b, sigs, rule, slip, cut)
        res["exits"][rule] = blk
        print(rule, {k: blk["base"].get(k) for k in ("trades", "gross_bps", "cost_bps", "net_bps", "t_day", "profit_factor")},
              "q1_gross_t", blk["q1_gross_t_day"], "vs_rand", blk["vs_random_direction_welch_t"], flush=True)
    res["session_long_benchmark"] = O.summary(O.simulate(b, O.session_long(sigs), "TCLOSE", slip=slip))
    return res


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if spec_sha(f["spec"]) != f["sha256"] or f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("spec or code changed after freezing")
    return f


def main(cmd: str) -> int:
    reg = Registry.load(R / "registry.jsonl")
    if cmd == "spec":
        s = spec()
        SPEC.write_text(json.dumps({"spec": s, "sha256": spec_sha(s)}, indent=1, default=str) + "\n")
        print("spec", spec_sha(s))
        return 0
    f = _frozen()
    if cmd == "preregister":
        if f["sha256"] not in (ROOT / DOC).read_text():
            raise SystemExit(f"{DOC} must quote {f['sha256']}")
        reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                           title="IX-4: NASDAQ opening-candle EMA(12) signal, development (10 preregistered exits)",
                           hypothesis="The 09:30 New York 5-minute candle's close relative to EMA(12) predicts the "
                                      "Nasdaq-100 CFD's subsequent intraday return, after real costs.",
                           uses=(Use(UNIVERSE, date.fromisoformat(DEV[0]), date.fromisoformat(DEV[1]), "select"),),
                           tests=len(O.EXITS), configurations=len(O.EXITS), preregistration=DOC,
                           design={"spec_sha256": f["sha256"], "code_sha256": code_hash()}))
        print("registered", PID)
        return 0
    if cmd == "develop":
        if reg.status_of(PID) != "PENDING":
            raise SystemExit("development is run once")
        slip = slippage()
        b = load(DEV)
        rel = [O.atr14(b)[i] / b.mid("c")[i] for _, i, _ in O.signals(b)]
        cut = (float(np.quantile(rel, 1 / 3)), float(np.quantile(rel, 2 / 3)))
        res = evaluate(DEV, slip, O.EXITS, cut)
        promoted = []
        for rule, blk in res["exits"].items():
            s = blk["base"]
            ok = {"min_trades": s.get("trades", 0) >= PROMOTE["min_trades"], "net_bps": s.get("net_bps", -1) > 0,
                  "t_day": (s.get("t_day") or 0) >= PROMOTE["t_day"], "costs_x1.5": blk["x1.5"].get("net_bps", -1) > 0,
                  "vs_random_direction_welch_t": (blk["vs_random_direction_welch_t"] or 0) >= 2.0}
            blk["promotion"] = {"gates": ok, "promoted": all(ok.values())}
            if all(ok.values()):
                promoted.append(rule)
        out = {"program": PID, "stage": "development", "spec_sha256": f["sha256"], "slippage_pts": slip,
               "atr_regime_cuts": cut, "results": res, "promoted": promoted}
        OUT_DEV.write_text(json.dumps(out, indent=1, default=str) + "\n")
        reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), "PASSED" if promoted else "FAILED",
                                   {"promoted": promoted,
                                    "net_bps": {k: v["base"].get("net_bps") for k, v in res["exits"].items()},
                                    "t_day": {k: v["base"].get("t_day") for k, v in res["exits"].items()}}))
        print("promoted:", promoted)
        return 0
    if cmd == "validate":
        dev = json.loads(OUT_DEV.read_text())
        promoted = dev["promoted"]
        if not promoted:
            raise SystemExit("nothing was promoted: validation is not run")
        if VID in [t.id for t in reg.trials]:
            raise SystemExit("validation is run once")
        k = len(promoted)
        t_req = round(max(3.0, bonferroni_t(sum(t.tests for t in reg.trials) + k)), 4)
        reg.register(Trial(id=VID, registered=datetime.now(timezone.utc), title="IX-4 validation 2017-2020",
                           hypothesis="IX-4 promoted exits hold on 2017-2020",
                           uses=(Use(UNIVERSE, date.fromisoformat(VAL[0]), date.fromisoformat(VAL[1]), "judge"),),
                           tests=k, configurations=k, preregistration=DOC, design={"promoted": promoted, "t_required": t_req}))
        res = evaluate(VAL, dev["slippage_pts"], promoted, tuple(dev["atr_regime_cuts"]))
        passers = []
        for rule, blk in res["exits"].items():
            s = blk["base"]
            g = {"net_bps": s.get("net_bps", -1) > 0, "t_day": (s.get("t_day") or 0) >= t_req,
                 "costs_x1.5": blk["x1.5"].get("net_bps", -1) > 0, "costs_x2": blk["x2"].get("net_bps", -1) > 0,
                 "delay": blk["delay"].get("net_bps", -1) > 0,
                 "halves": all(h.get("net_bps", -1) > 0 for h in blk["halves"]),
                 "profit_factor": (s.get("profit_factor") or 0) >= 1.05,
                 "top_year_share": blk["top_year_share"] is not None and blk["top_year_share"] <= 0.5,
                 "vs_random_direction_welch_t": (blk["vs_random_direction_welch_t"] or 0) >= 2.0}
            blk["gates"] = g
            blk["failed"] = [x for x, v in g.items() if not v]
            if all(g.values()):
                passers.append(rule)
        out = {"program": VID, "t_required": t_req, "results": res, "passers": passers,
               "verdict": "PASSED" if passers else "FAILED"}
        OUT_VAL.write_text(json.dumps(out, indent=1, default=str) + "\n")
        reg.record_verdict(Verdict(VID, datetime.now(timezone.utc), out["verdict"], {"passers": passers}))
        print("validation:", out["verdict"], passers)
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) == 2 else ""))
