"""Round 3's return decomposition for every judged hypothesis (descriptive; the verdict is the program's).

    python scripts/r3_report.py        # -> research/results/R3-report.json

Re-derives the exact judged trades of the frozen design and reports per hypothesis:
spot (price move net of spread/commission/slippage), gross spot (before those costs), the
RATE-DIFFERENTIAL CARRY PROXY, financing (declared markup), gross = gross spot + carry, net,
P(direction correct) = share of trades whose price move (before costs) went the traded way, MFE, MAE,
holding, net R at lower/normal/higher costs and at markup 0 / 0.5 / 1.0 %, and by instrument / year.
The trade count must equal the judged one, or the script stops.
"""

from __future__ import annotations

import json
import sys
from functools import partial
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.carry import CarryStudy  # noqa: E402
from aitrader.research.discovery.exits import EXIT_BY_KEY  # noqa: E402
from aitrader.research.discovery.study import Condition, fit_binning, stressed_costs  # noqa: E402
from aitrader.research.discovery.universe import load_universe  # noqa: E402
from aitrader.research.labels import BUY, SELL, CostModel  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402

R = ROOT / "research"


def _m(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return round(float(x.mean()), 4) if len(x) else None


def main() -> int:
    import round3
    holdout = Holdout.load(R / "holdout.json")
    pairs, _ = round3.gate(holdout)
    rates, prims, _, prog, _, _ = round3.components(holdout, pairs)
    d = prog.design
    data, _ = load_universe(DataStore(ROOT / "data" / "processed", holdout), symbols=tuple(pairs), timeframe="D1",
                            bound=tuple(prims.values()))
    judged = {c["id"]: c for c in json.loads((R / "knowledge" / "R3.json").read_text())["judged"]}
    binn = {f: fit_binning(f, {}, groups=g) for f, g in d.groups}
    base = d.costs
    mk = round3.SPEC["costs"]["financing_markup_pct_per_year"]
    variants = {"normal": (base, mk), "lower": (CostModel(0.0, base.commission_pips_rt, 0.0, 0.5), mk),
                "higher": (stressed_costs(base), mk), "markup_0": (base, 0.0), "markup_1": (base, 1.0)}
    studies = {k: CarryStudy(data, d.judge, binn, c, rates=rates, rate_type="POLICY", markup_pct=m)
               for k, (c, m) in variants.items()}
    ex = EXIT_BY_KEY["D4"]
    out = {"note": "descriptive; the verdict is research/knowledge/R3.json", "carry_label": "RATE-DIFFERENTIAL CARRY PROXY",
           "financing_markup_pct": mk, "pairs": pairs, "hypotheses": {}}
    for h in round3.SPEC["hypotheses"]:
        side = BUY if h["side"] == "BUY" else SELL
        cond = Condition.parse(h["condition"])
        st = studies["normal"]
        tr = st.trades(st.masks(cond), ex, side)
        want = judged[h["id"]]["battery"]["checks"]["min_trades"]["n"]
        if tr.n != want:
            raise SystemExit(f"{h['id']}: reproduced {tr.n} trades, the program judged {want}")
        comp = {k: [] for k in ("spot", "carry", "financing", "cost")}
        for sym, row in zip(tr.symbol, tr.row):
            o = st.outcome(sym, ex, side)
            i = int(np.searchsorted(st.rows[sym], row))
            for k in comp:
                comp[k].append(float(o[k][i]))
        c = {k: np.array(v) for k, v in comp.items()}
        gross_spot = c["spot"] + c["cost"]
        by_cost = {k: _m(s.trades(s.masks(cond), ex, side).r) for k, s in studies.items() if k != "normal"}
        out["hypotheses"][h["id"]] = {
            "condition": h["condition"], "side": h["side"], "n": int(tr.n),
            "p_direction_correct": round(float(np.mean(gross_spot > 0)), 4) if tr.n else None,
            "gross_spot_R": _m(gross_spot), "carry_R": _m(c["carry"]), "gross_R": _m(gross_spot + c["carry"]),
            "costs_R": _m(c["cost"]), "financing_R": _m(c["financing"]), "spot_net_of_costs_R": _m(c["spot"]),
            "net_R": _m(tr.r), "net_R_by_cost": {"lower": by_cost["lower"], "normal": _m(tr.r), "higher": by_cost["higher"]},
            "net_R_by_markup": {"0.0": by_cost["markup_0"], str(mk): _m(tr.r), "1.0": by_cost["markup_1"]},
            "mfe_R_mean": _m(tr.mfe), "mae_R_mean": _m(tr.mae),
            "mae_R_worst": round(float(np.nanmin(tr.mae)), 4) if tr.n else None, "bars_held_mean": _m(tr.bars),
            "by_instrument": {s: {"n": int((tr.symbol == s).sum()), "net_R": _m(tr.r[tr.symbol == s]),
                                  "carry_R": _m(c["carry"][tr.symbol == s])} for s in sorted(set(tr.symbol))},
            "by_year": {int(y): {"n": int((tr.years() == y).sum()), "net_R": _m(tr.r[tr.years() == y])}
                        for y in sorted(set(tr.years()))},
        }
        x = out["hypotheses"][h["id"]]
        print(h["id"], x["n"], "P(dir)", x["p_direction_correct"], "grossSpot", x["gross_spot_R"], "carry", x["carry_R"],
              "costs", x["costs_R"], "fin", x["financing_R"], "net", x["net_R"], "cost", x["net_R_by_cost"],
              "markup", x["net_R_by_markup"])
    (R / "results" / "R3-report.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
