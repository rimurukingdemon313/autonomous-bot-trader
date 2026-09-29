"""XS-001: does published cross-sectional currency momentum hold on the dollar legs of our universe?

    python scripts/xs001.py draft         # feature into the catalog, leakage test on real D1 bars, 2 DRAFT hypotheses
    python scripts/xs001.py preregister   # registry trial + document; each hypothesis PREREGISTERED
    python scripts/xs001.py run           # once

The rule is not mined here. Menkhoff, Sarno, Schmeling & Schrimpf, "Currency momentum
strategies", J. Financial Economics 106 (2012): rank currencies by their past return against
the dollar, buy the recent winners and sell the recent losers, hold about a month; their
headline portfolio forms on 1 month and holds 1 month. Published before the judged period
(2013-07 -> 2017-01) begins.

Our form, fixed before any judged data is read: on each D1 close, `xs_mom` is the pair's
currency's 24-day move against the dollar (ATR units) minus the median of the seven currencies,
signed to the pair; top tercile -> BUY the pair (long the strong currency), bottom tercile ->
SELL it (short the weak one); exit D4 (20 trading days, 3 ATR protective stop); the seven USD
pairs only. The long-short portfolio of the paper is the two legs together.

Stated in advance: the paper finds the effect strongest in minor currencies with high
transaction costs and weaker among majors. With seven majors and a threshold above t 3.2, the
smallest detectable net mean is about 0.15-0.2 R per trade at 300-500 trades.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
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
from aitrader.research.discovery.primitives import USD_SIGN  # noqa: E402
from aitrader.research.discovery.study import Segment  # noqa: E402
from aitrader.research.discovery.universe import leakage_checker, load_universe, xs_records  # noqa: E402
from aitrader.research.labels import CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
PID = "XS-001"
DOC = "research/preregistrations/XS-001-currency-momentum.md"
PAIRS = tuple(sorted(USD_SIGN))
LIT = ("Menkhoff, Sarno, Schmeling & Schrimpf, Currency momentum strategies, J. Financial Economics 106 (2012)")
MECH = ("under-reaction to currency-specific news and slow-moving capital make relative strength across currencies "
        "persist for about a month (published; conjectured to hold on majors here)")
RULES = BatteryRules(t_threshold=1.0).describe()
SPECS = (
    ("XS-001-L", "xs_mom=high", "BUY", "the pair's currency is among the strongest against the dollar over 24 days"),
    ("XS-001-S", "xs_mom=low", "SELL", "the pair's currency is among the weakest against the dollar over 24 days"),
)


def feature_id() -> str:
    return xs_records(PID)["xs_mom"].id


def hypotheses() -> list[Hypothesis]:
    return [Hypothesis(
        id=hid, statement=f"When {words} (relative to the other six) at a daily close, a {side} of the pair held "
                          "about a month (exit D4) has positive net expectancy.",
        rationale=f"published cross-sectional momentum ({LIT}); form fixed before any judged data was read",
        mechanism=MECH, features=(feature_id(),), condition=cond, side=side, instruments=PAIRS, timeframe="D1",
        exit="D4", expected_effect="mean net R per trade > 0 on 2013-07 .. 2017-01",
        falsification=tuple(f"{k}: {v}" for k, v in RULES.items() if k != "significance"),
        budget=1, origin="human", program=PID) for hid, cond, side, words in SPECS]


def program(reg: Registry) -> ConfirmatoryProgram:
    d = ConfirmDesign(
        id=PID, title="Published cross-sectional currency momentum, judged after its publication",
        question="Does buying the currencies that were strongest against the dollar over the last 24 days, and "
                 "selling the weakest, held about a month, have positive net expectancy on the seven USD pairs "
                 "from 2013-07 to 2017-01, all costs charged?",
        universe=UNIVERSE_KEY, instruments=PAIRS, hypotheses=tuple(s[0] for s in SPECS),
        fit=Segment("fit", "fit", date(2007, 6, 1), date(2013, 7, 1)),
        judge=Segment("confirmation", "judge", date(2013, 7, 11), date(2017, 1, 1)),
        rules=BatteryRules(t_threshold=1.0), holdout_start=reg.holdout.start,
        costs=CostModel(swap_atr_per_night=0.01), min_embargo_days=10, lookback_start=date(2007, 3, 30))
    if any(t.id == PID for t in reg.trials):
        frozen = reg.get(PID).design["confirmatory_program"]["rules"]["t_threshold"]
    else:
        frozen = reg.threshold_for_next(d.universe, d.judge.start, d.judge.end, new_tests=len(d.hypotheses))
    d = replace(d, rules=replace(d.rules, t_threshold=frozen))
    return ConfirmatoryProgram(d, reg, Ledger(R / "discovery" / "ledger.jsonl"),
                               FeatureCatalog(R / "discovery" / "features.jsonl"), R / "knowledge",
                               lambda: datetime.now(timezone.utc))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("draft", "preregister", "run"))
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    prog = program(reg)
    store = DataStore(ROOT / "data" / "processed", holdout)
    if a.cmd == "draft":
        cat = prog.catalog
        rec = xs_records(PID)["xs_mom"]
        if cat.budget(PID)[1] == 0:
            cat.open_program(PID, 1, now)
        cat.register(rec, now)
        if cat.leakage_status(rec.id) != "PASSED":
            series = {s: store.load(s, "D1") for s in PAIRS}
            bad, n, syms = leakage_checker(series)("xs_mom")
            print("leakage", cat.record_leakage(rec.id, bad, n, syms, now), f"{n} rows")
        for h in hypotheses():
            prog.ledger.draft(h, now)
        print("drafted", [h.id for h in hypotheses()])
    elif a.cmd == "preregister":
        t = prog.preregister(ROOT / DOC, DOC)
        print(f"registered {t.id}: tests {t.tests}, threshold t >= {prog.design.rules.t_threshold:.4f}")
    else:
        data, hashes = load_universe(store, symbols=PAIRS, timeframe="D1", extra=("xs_mom",))
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
