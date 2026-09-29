"""The direction-and-cost report for every hypothesis a Round 2 family judged.

    python scripts/r2_report.py R2A        # -> research/results/R2A-report.json

DESCRIPTIVE, not a test and not a verdict (the verdict is the program's). It re-derives the exact
judged trades (same design, same fixed states, same judged segment) and reports what the
research plan asks of every candidate:

- P(direction correct): the share of trades whose GROSS result (before any cost) is positive
- expected R before costs, the costs split into spread / commission / slippage / swap, and after costs
- net R at lower (spread x0.5, no slippage) / normal / higher (the battery's stress) costs
- mean MFE, mean MAE, the worst adverse excursion, mean holding time
- the result by regime at entry (every Round 2 state + trend/range and volatility), by instrument
  and by year

Every reproduced trade count must equal the judged one, or the script stops.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.exits import EXIT_BY_KEY  # noqa: E402
from aitrader.research.discovery.macro import macro_primitives  # noqa: E402
from aitrader.research.discovery.study import Condition, Study, fit_binning, stressed_costs  # noqa: E402
from aitrader.research.discovery.universe import load_universe  # noqa: E402
from aitrader.research.labels import BUY, SELL, CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
STATES = ("vix_state", "vix_trend", "usd_rate", "oil_pull", "trend_sign")


def _m(x) -> float | None:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return round(float(x.mean()), 4) if len(x) else None


def _group(keys, r) -> dict:
    out = {}
    for k in sorted(set(keys), key=str):
        sel = np.array([kk == k for kk in keys])
        out[str(k)] = {"n": int(sel.sum()), "mean_R": _m(r[sel])}
    return out


def main() -> int:
    import round2
    fam = round2.FAMILIES[sys.argv[1]]
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    ext = round2.external(holdout)
    prims = macro_primitives(ext)
    prog = round2.program(reg, fam)
    d = prog.design
    store = DataStore(ROOT / "data" / "processed", holdout)
    data, _ = load_universe(store, symbols=d.instruments, timeframe="D1", bound=tuple(prims.values()))
    judged = {c["id"]: c for c in json.loads((R / "knowledge" / f"{fam.pid}.json").read_text())["judged"]}
    groups = {f: g for f, g in d.groups}
    feats = round2.features(fam)
    binn = {f: fit_binning(f, {}, groups=groups[f]) for f in feats}
    base = d.costs
    variants = {
        "normal": base,
        "lower": CostModel(slippage_pips=0.0, commission_pips_rt=base.commission_pips_rt,
                           swap_atr_per_night=base.swap_atr_per_night, spread_multiple=0.5),
        "higher": stressed_costs(base),
        "gross": CostModel(0.0, 0.0, 0.0, 0.0),
        "spread_only": CostModel(0.0, 0.0, 0.0, 1.0),
        "spread_commission": CostModel(0.0, base.commission_pips_rt, 0.0, 1.0),
        "spread_slippage": CostModel(base.slippage_pips, 0.0, 0.0, 1.0),
        "standard_swap": CostModel(base.slippage_pips, base.commission_pips_rt, 0.01, 1.0),
    }
    studies = {k: Study(data, d.judge, binn, c) for k, c in variants.items()}
    out = {"program": fam.pid, "note": "descriptive; the verdict is the program's", "hypotheses": {}}
    for s in fam.specs:
        side = BUY if s.side == "BUY" else SELL
        cond = Condition.parse(s.condition)
        tr = {k: st.trades(st.masks(cond), EXIT_BY_KEY[s.exit], side) for k, st in studies.items()}
        n = tr["normal"].n
        want = judged[s.hid]["battery"]["checks"]["min_trades"]["n"]
        if n != want:
            raise SystemExit(f"{s.hid}: reproduced {n} trades, the program judged {want}")
        if n == 0:
            out["hypotheses"][s.hid] = {"n": 0}
            continue
        # entries are identical across cost variants only if the position schedule is; check it
        same = {k: bool(np.array_equal(v.row, tr["normal"].row)) for k, v in tr.items()}
        t = tr["normal"]
        gross = tr["gross"].r if same["gross"] else t.r + t.cost
        spread = tr["spread_only"].cost if same["spread_only"] else None
        comm = (tr["spread_commission"].cost - spread) if same["spread_commission"] and spread is not None else None
        slip = (tr["spread_slippage"].cost - spread) if same["spread_slippage"] and spread is not None else None
        swap = t.cost - (spread + comm + slip) if None not in (spread, comm, slip) else None
        regime = {}
        for st_name in STATES:
            if st_name not in data[t.symbol[0]].columns:
                continue
            vals = [data[sym].columns[st_name][int(row)] for sym, row in zip(t.symbol, t.row)]
            regime[st_name] = _group([None if not np.isfinite(v) else int(v) for v in vals], t.r)
        for st_name, edges in (("er120", (0.3,)), ("atr_pctile", (0.5,))):
            vals = np.array([data[sym].columns[st_name][int(row)] for sym, row in zip(t.symbol, t.row)])
            regime[st_name] = _group([None if not np.isfinite(v) else ("high" if v >= edges[0] else "low")
                                      for v in vals], t.r)
        out["hypotheses"][s.hid] = {
            "condition": s.condition, "side": s.side, "exit": s.exit, "n": int(n),
            "p_direction_correct": round(float(np.mean(gross > 0)), 4),
            "gross_R": _m(gross), "net_R": _m(t.r), "cost_R": _m(t.cost),
            "cost_split_R": {"spread": _m(spread) if spread is not None else None,
                             "commission": _m(comm) if comm is not None else None,
                             "slippage": _m(slip) if slip is not None else None,
                             "swap": _m(swap) if swap is not None else None},
            "net_R_by_cost": {k: _m(tr[k].r) for k in ("lower", "normal", "higher", "standard_swap")},
            "same_positions_across_cost_variants": same,
            "mfe_R_mean": _m(t.mfe), "mae_R_mean": _m(t.mae), "mae_R_worst": round(float(np.nanmin(t.mae)), 4),
            "bars_held_mean": _m(t.bars),
            "by_regime_at_entry": regime,
            "by_instrument": _group(list(t.symbol), t.r),
            "by_year": _group([int(y) for y in t.years()], t.r),
        }
        h = out["hypotheses"][s.hid]
        print(s.hid, n, "P(dir)", h["p_direction_correct"], "gross", h["gross_R"], "net", h["net_R"],
              "cost", h["net_R_by_cost"])
    (R / "results" / f"{fam.pid}-report.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
