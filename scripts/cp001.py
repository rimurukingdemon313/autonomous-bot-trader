"""CP-001: does the published FX trend-following rule hold on a period after its publication?

    python scripts/cp001.py draft         # the four hypotheses into the ledger (DRAFT)
    python scripts/cp001.py preregister   # registry trial + document; each hypothesis PREREGISTERED
    python scripts/cp001.py run           # once

The rule is not mined here: time-series momentum and moving-average trend in currencies are
documented by Moskowitz, Ooi & Pedersen, "Time series momentum", J. Financial Economics 104
(2012) and Menkhoff, Sarno, Schmeling & Schrimpf, "Currency momentum strategies", J. Financial
Economics 106 (2012) — both published before the judged period (2013-07 -> 2017-01) begins.
The only choices made here are the declared daily features that express the rule (r120: the
120-day move; ma_slope: 48-day vs 240-day average, both in their top/bottom tercile) and one
exit declared in advance (D4: hold 20 trading days, about a month, with a 3-ATR protective stop).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.instruments import UNIVERSE_KEY  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.battery import BatteryRules  # noqa: E402
from aitrader.research.discovery.catalog import FeatureCatalog  # noqa: E402
from aitrader.research.discovery.confirm import ConfirmatoryProgram, ConfirmDesign  # noqa: E402
from aitrader.research.discovery.hypothesis import Hypothesis, Ledger  # noqa: E402
from aitrader.research.discovery.study import Segment  # noqa: E402
from aitrader.research.discovery.universe import FX, load_universe  # noqa: E402
from aitrader.research.labels import CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
DOC = "research/preregistrations/CP-001-trend-following.md"
LIT = ("Moskowitz, Ooi & Pedersen, Time series momentum, JFE 104 (2012); Menkhoff, Sarno, Schmeling & "
       "Schrimpf, Currency momentum strategies, JFE 106 (2012)")
MECH = ("continuation (published): slow-moving capital, central-bank policy cycles and investor under-reaction "
        "make currency trends persist over weeks to months")
RULES = BatteryRules(t_threshold=1.0).describe()
SPECS = (
    ("CP-001-T1", "r120=high", "BUY", "the 120-day move is in its top tercile (a strong uptrend)"),
    ("CP-001-T2", "r120=low", "SELL", "the 120-day move is in its bottom tercile (a strong downtrend)"),
    ("CP-001-T3", "ma_slope=high", "BUY", "the 48-day average is well above the 240-day average"),
    ("CP-001-T4", "ma_slope=low", "SELL", "the 48-day average is well below the 240-day average"),
)


def hypotheses() -> list[Hypothesis]:
    out = []
    for hid, cond, side, words in SPECS:
        f = cond.split("=")[0]
        out.append(Hypothesis(
            id=hid, statement=f"When {words} at a daily close, a {side} held about a month (exit D4) has positive "
                              "net expectancy.",
            rationale=f"published trend-following rule ({LIT}); fixed before any judged data was read",
            mechanism=MECH, features=(f"{f}.D1@feat-1.0.0",), condition=cond, side=side, instruments=FX,
            timeframe="D1", exit="D4", expected_effect="mean net R per trade > 0 on 2013-07 .. 2017-01",
            falsification=tuple(f"{k}: {v}" for k, v in RULES.items() if k != "significance"),
            budget=1, origin="human", program="CP-001"))
    return out


def program(reg: Registry) -> ConfirmatoryProgram:
    d = ConfirmDesign(
        id="CP-001", title="Published FX trend following, judged after its publication",
        question="Do the published time-series momentum and moving-average trend rules have positive net "
                 "expectancy on 12 FX pairs from 2013-07 to 2017-01, one month holds, all costs charged?",
        universe=UNIVERSE_KEY, instruments=FX, hypotheses=tuple(s[0] for s in SPECS),
        fit=Segment("fit", "fit", date(2007, 6, 1), date(2013, 7, 1)),
        judge=Segment("confirmation", "judge", date(2013, 7, 11), date(2017, 1, 1)),
        rules=BatteryRules(t_threshold=1.0), holdout_start=reg.holdout.start,
        costs=CostModel(swap_atr_per_night=0.01), min_embargo_days=10, lookback_start=date(2007, 3, 30))
    if any(t.id == "CP-001" for t in reg.trials):
        frozen = reg.get("CP-001").design["confirmatory_program"]["rules"]["t_threshold"]
    else:
        frozen = reg.threshold_for_next(d.universe, d.judge.start, d.judge.end, new_tests=len(d.hypotheses))
    from dataclasses import replace
    d = replace(d, rules=replace(d.rules, t_threshold=frozen))
    return ConfirmatoryProgram(d, reg, Ledger(R / "discovery" / "ledger.jsonl"),
                               FeatureCatalog(R / "discovery" / "features.jsonl"), R / "knowledge",
                               lambda: datetime.now(timezone.utc))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("draft", "preregister", "run"))
    a = ap.parse_args()
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    prog = program(reg)
    if a.cmd == "draft":
        for h in hypotheses():
            prog.ledger.draft(h, datetime.now(timezone.utc))
        print("drafted", [h.id for h in hypotheses()])
    elif a.cmd == "preregister":
        t = prog.preregister(ROOT / DOC, DOC)
        print(f"registered {t.id}: tests {t.tests}, threshold t >= {prog.design.rules.t_threshold:.4f}")
    else:
        data, hashes = load_universe(DataStore(ROOT / "data" / "processed", holdout), timeframe="D1")
        art = prog.run(data, hashes)
        print(json.dumps({"verdict": art["verdict"], "validated": art["validated"],
                          "judged": [{"id": c["id"], "n": c["battery"]["checks"]["min_trades"]["n"],
                                      "mean_R": c["battery"]["checks"]["significance"]["mean_R"],
                                      "t": c["battery"]["checks"]["significance"]["t"],
                                      "failed": c["battery"]["failed"], "board": c["board"]["verdict"]}
                                     for c in art["judged"]]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
