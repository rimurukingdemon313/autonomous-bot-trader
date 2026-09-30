"""Round 4's information-value report (descriptive; the verdicts are research/knowledge/R4.json).

    python scripts/r4_report.py      # -> research/results/R4-report.json

For every hypothesis, on the exact judged trades:
- P(direction correct) = share of trades whose price move BEFORE costs went the traded way
- gross R, the cost split (spread / commission / slippage / swap), net R at lower / normal / higher cost
- the PRICE-ONLY CONTROL: the own-move condition alone, same pairs, side and exit -- the information
  value of the outside source is the hypothesis minus its control
- net R without the single best trade and without the best 5% of trades (outlier dependence)
- by regime at entry (VIX state, trend er120 and volatility atr_pctile split at their medians),
  best and worst regime with >= 20 trades; by instrument; by year
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aitrader.data.external import ExternalStore  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.exits import EXIT_BY_KEY  # noqa: E402
from aitrader.research.discovery.macro import macro_primitives  # noqa: E402
from aitrader.research.discovery.study import Condition, Study, fit_binning, stressed_costs  # noqa: E402
from aitrader.research.discovery.universe import load_universe  # noqa: E402
from aitrader.research.labels import BUY, SELL, CostModel  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402

R = ROOT / "research"


def _m(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return round(float(x.mean()), 4) if len(x) else None


def _t(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3 or x.std(ddof=1) == 0:
        return None
    return round(float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))), 2)


def main() -> int:
    import round4
    holdout = Holdout.load(R / "holdout.json")
    store = DataStore(ROOT / "data" / "processed", holdout)
    ext, gold, prims = round4.primitives(holdout, store)
    vix = ExternalStore(ROOT / "data" / "external", holdout).load("vix")
    extra = {"vix_state": macro_primitives({"vix": vix})["vix_state"]}
    insts = tuple(sorted({i for s in round4.SPECS for i in s.instruments}))
    data, _ = load_universe(store, symbols=insts, timeframe="D1", bound=tuple(prims.values()) + tuple(extra.values()))
    judged = {c["id"]: c for c in json.loads((R / "knowledge" / "R4.json").read_text())["judged"]}
    binn = {f: fit_binning(f, {}, groups=round4.GROUPS3) for f in list(prims) + ["vix_state"]}
    base = round4.COSTS
    variants = {"normal": base, "lower": CostModel(0.0, base.commission_pips_rt, base.swap_atr_per_night, 0.5),
                "higher": stressed_costs(base), "spread_only": CostModel(0.0, 0.0, 0.0, 1.0),
                "spread_commission": CostModel(0.0, base.commission_pips_rt, 0.0, 1.0),
                "spread_slippage": CostModel(base.slippage_pips, 0.0, 0.0, 1.0)}
    studies = {k: Study(data, round4.JUDGE, binn, c) for k, c in variants.items()}
    out = {"note": "descriptive; the verdicts are research/knowledge/R4.json", "hypotheses": {}}
    for s in round4.SPECS:
        side = BUY if s.side == "BUY" else SELL
        ex = EXIT_BY_KEY[s.exit]
        sub = {k: Study({i: data[i] for i in s.instruments}, round4.JUDGE, binn, c) for k, c in variants.items()}
        cond = Condition.parse(s.condition)
        tr = {k: st.trades(st.masks(cond), ex, side) for k, st in sub.items()}
        t = tr["normal"]
        want = judged[s.hid]["battery"]["checks"]["min_trades"]["n"]
        # the program (confirm-1.0.0) judged every hypothesis on ALL its instruments: reproduce that population
        # to prove the diagnosis, and report the REGISTERED population (the hypothesis's own pairs)
        as_judged = studies["normal"].trades(studies["normal"].masks(cond), ex, side).n
        if as_judged != want:
            raise SystemExit(f"{s.hid}: reproduced {as_judged} trades on the program's instruments, judged {want}")
        population_defect = t.n != want
        correct_battery = None
        if population_defect:
            from aitrader.research.discovery.battery import BatteryRules, regime_binnings, run_battery  # noqa: E402
            from aitrader.research.discovery.program import REGIME_FEATURES  # noqa: E402
            from aitrader.research.discovery.study import Study as _S  # noqa: E402
            fitst = _S({i: data[i] for i in s.instruments}, round4.FIT, {}, base)
            ctx = regime_binnings({f: {i: data[i].columns[f][fitst.rows[i]] for i in s.instruments}
                                   for f in REGIME_FEATURES})
            jst = _S({i: data[i] for i in s.instruments}, round4.JUDGE, binn, base, context=ctx)
            thr = judged[s.hid]["battery"]["checks"]["significance"]["threshold"]
            res = run_battery(jst, cond, side, s.exit, BatteryRules(t_threshold=thr), perturbed=[], kind="opportunity",
                              trials=len(round4.SPECS), key=s.hid)
            correct_battery = {"verdict": res["verdict"], "failed": res["failed"],
                               "n": res["checks"]["min_trades"]["n"], "mean_R": res["checks"]["significance"]["mean_R"],
                               "t": res["checks"]["significance"]["t"],
                               "note": "the battery on the REGISTERED instruments, run after the defect was found; "
                                       "descriptive, not a registry verdict"}
        gross = t.r + t.cost
        same = {k: bool(np.array_equal(v.row, t.row)) for k, v in tr.items()}
        spread = tr["spread_only"].cost if same["spread_only"] else None
        comm = tr["spread_commission"].cost - spread if spread is not None and same["spread_commission"] else None
        slip = tr["spread_slippage"].cost - spread if spread is not None and same["spread_slippage"] else None
        swap = t.cost - spread - comm - slip if all(x is not None for x in (spread, comm, slip)) else None
        own = [p for p in s.condition.split("&") if p.startswith("own5=")]
        ctrl = sub["normal"].trades(sub["normal"].masks(Condition.parse(own[0])), ex, side) if own else None
        order = np.argsort(-t.r)
        k5 = max(1, int(round(0.05 * t.n)))
        regime = {}
        for name in ("vix_state",):
            vals = [data[sym].columns[name][int(row)] for sym, row in zip(t.symbol, t.row)]
            keys = [None if not np.isfinite(v) else {0: "VIX<20", 1: "VIX 20-30", 2: "VIX>=30"}[int(v)] for v in vals]
            regime[name] = {k: {"n": sum(1 for x in keys if x == k), "net_R": _m(t.r[np.array([x == k for x in keys])])}
                            for k in sorted({x for x in keys if x})}
        for name in ("er120", "atr_pctile"):
            vals = np.array([data[sym].columns[name][int(row)] for sym, row in zip(t.symbol, t.row)])
            med = float(np.nanmedian(vals))
            hi = vals >= med
            regime[name] = {"above_median": {"n": int(hi.sum()), "net_R": _m(t.r[hi])},
                            "below_median": {"n": int((~hi).sum()), "net_R": _m(t.r[~hi])}}
        cells = [(f"{g}:{k}", v) for g, d in regime.items() for k, v in d.items() if v["n"] >= 20 and v["net_R"] is not None]
        h = {
            "condition": s.condition, "side": s.side, "exit": s.exit, "instruments": list(s.instruments), "n": int(t.n),
            "judged_population_n": int(want), "population_defect": bool(population_defect),
            "battery_on_registered_instruments": correct_battery,
            "t": judged[s.hid]["battery"]["checks"]["significance"]["t"],
            "t_required": judged[s.hid]["battery"]["checks"]["significance"]["threshold"],
            "p_direction_correct": round(float(np.mean(gross > 0)), 4),
            "gross_R": _m(gross), "cost_R": _m(t.cost),
            "cost_split_R": {"spread": _m(spread) if spread is not None else None,
                             "commission": _m(comm) if comm is not None else None,
                             "slippage": _m(slip) if slip is not None else None,
                             "swap_financing": _m(swap) if swap is not None else None},
            "net_R": _m(t.r), "net_R_by_cost": {k: _m(tr[k].r) for k in ("lower", "normal", "higher")},
            "without_best_trade_R": _m(t.r[order[1:]]), "without_best_5pct_R": _m(t.r[order[k5:]]),
            "price_only_control": ({"condition": own[0], "n": int(ctrl.n), "net_R": _m(ctrl.r), "t": _t(ctrl.r),
                                    "p_direction_correct": round(float(np.mean((ctrl.r + ctrl.cost) > 0)), 4)}
                                   if ctrl is not None else None),
            "information_value_net_R": (round(_m(t.r) - _m(ctrl.r), 4) if ctrl is not None and ctrl.n else None),
            "mfe_R_mean": _m(t.mfe), "mae_R_mean": _m(t.mae), "mae_R_worst": round(float(np.nanmin(t.mae)), 3),
            "bars_held_mean": _m(t.bars), "by_regime_at_entry": regime,
            "best_regime": max(cells, key=lambda c: c[1]["net_R"]) if cells else None,
            "worst_regime": min(cells, key=lambda c: c[1]["net_R"]) if cells else None,
            "by_instrument": {i: {"n": int((t.symbol == i).sum()), "net_R": _m(t.r[t.symbol == i])}
                              for i in sorted(set(t.symbol))},
            "by_year": {int(y): {"n": int((t.years() == y).sum()), "net_R": _m(t.r[t.years() == y])}
                        for y in sorted(set(t.years()))},
        }
        out["hypotheses"][s.hid] = h
        print(s.hid, h["n"], "P", h["p_direction_correct"], "gross", h["gross_R"], "cost", h["cost_R"], h["cost_split_R"],
              "net", h["net_R"], h["net_R_by_cost"], "noBest", h["without_best_trade_R"], "no5%", h["without_best_5pct_R"])
        print("   control", h["price_only_control"], "IV", h["information_value_net_R"])
        if population_defect:
            print("   DEFECT: judged on", want, "trades (all program pairs); registered population", t.n, correct_battery)
        print("   best", h["best_regime"], "worst", h["worst_regime"])
        print("   inst", {k: (v["n"], v["net_R"]) for k, v in h["by_instrument"].items()})
        print("   year", {k: (v["n"], v["net_R"]) for k, v in h["by_year"].items()})
    (R / "results" / "R4-report.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
