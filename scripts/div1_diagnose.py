"""DIV-1 diagnosis (descriptive, NOT a test): where did the net return go?

Runs on the same data and period as `div1.py judge` (2008-01..2020-12; the 2021+ holdout stays
sealed: no key is ever requested). It changes nothing in DIV-1 and records no verdict. It
decomposes the monthly cost into turnover, leverage financing and short borrow, and counts trades.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import div1  # noqa: E402
from aitrader.research.discovery import trend  # noqa: E402


def decompose(panel, rule):
    c = trend.TrendCosts()
    only_turn = trend.backtest(panel, rule, trend.TrendCosts(c.trade_bps, 0.0, 0.0), *div1.JUDGE)
    only_fin = trend.backtest(panel, rule, trend.TrendCosts(0.0, c.financing_pa, 0.0), *div1.JUDGE)
    only_borrow = trend.backtest(panel, rule, trend.TrendCosts(0.0, 0.0, c.borrow_pa), *div1.JUDGE)
    full = trend.backtest(panel, rule, c, *div1.JUDGE)
    ann = lambda rows, k: round(float(np.mean([r[k] for r in rows]) * 12), 5)  # noqa: E731
    # trades: every month each held asset is re-weighted; a "trade" is any change of weight, a
    # "position change" is an entry, exit or direction flip
    mdates, mc, vol = panel.monthly()
    flips = entries = 0
    prev = {}
    months = [k for k in range(len(mdates) - 1) if div1.JUDGE[0] <= mdates[k + 1] < div1.JUDGE[1]]
    asset_months = 0
    for k in months:
        for s in mc:
            sg = trend.signal(mc[s], k, rule)
            sg = 0.0 if not np.isfinite(sg) else sg
            if sg != 0:
                asset_months += 1
            p = prev.get(s, 0.0)
            if sg != p:
                if p == 0 or sg == 0:
                    entries += 1
                else:
                    flips += 1
            prev[s] = sg
    gross_dev = [r["gross"] for r in full if r["date"] < div1.DEV[1]]
    gross_val = [r["gross"] for r in full if r["date"] >= div1.VAL[0]]
    return {"months": len(full), "asset_months_held": asset_months, "direction_flips": flips,
            "entries_or_exits": entries,
            "gross_annual": ann(full, "gross"), "cost_annual": ann(full, "cost"), "net_annual": ann(full, "net"),
            "cost_annual_turnover": ann(only_turn, "cost"), "cost_annual_financing": ann(only_fin, "cost"),
            "cost_annual_borrow": ann(only_borrow, "cost"),
            "avg_gross_exposure": round(float(np.mean([r["gross_exposure"] for r in full])), 3),
            "gross_annual_development": round(float(np.mean(gross_dev) * 12), 5),
            "gross_annual_validation": round(float(np.mean(gross_val) * 12), 5),
            "worst_months": sorted(((str(r["date"]), round(r["net"], 4)) for r in full), key=lambda x: x[1])[:5]}


def main():
    panel = div1.load_panel()  # sealed: no key
    out = {"note": "descriptive diagnosis of the judged period; not a test, no verdict recorded",
           "results": {h: decompose(panel, rule) for h, rule in div1.HYPOTHESES.items()}}
    (ROOT / "research" / "results" / "DIV-1-diagnosis.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
