"""Round 2 of edge discovery: conditional hypotheses on information the bars do not contain.

    python scripts/round2.py draft R2A          # features into the catalog, leakage tests on real data, DRAFTs
    python scripts/round2.py preregister R2A    # registry trial + document (commit before running)
    python scripts/round2.py run R2A            # once; then STOP and evaluate the family

Families, in the priority the research plan fixes (docs/ROUND2_PLAN.md):

  R2A  carry, conditional on the risk regime   (VIX; documented policy-rate signs)
  R2B  US rate-differential changes            (Fed H.15 10y)
  R2C  cross-asset: oil and the Canadian dollar (EIA Brent)
  R2D  regime-conditioned time-series momentum (VIX; the pair's own trend)

Design, identical for every family and fixed before any judged data is read:
- every condition is a categorical state at a FIXED level (aitrader/research/discovery/macro.py):
  nothing is fitted, so the fit segment only supplies the battery's regime medians;
- judged on 2008-07-11 -> 2017-01-01 (8.5 years, including 2008, 2011 and 2015 stress), bins and
  regime medians from 2007-04 -> 2008-07; the holdout (2017-) stays sealed;
- the registry threshold counts every test ever run on these outcomes (Round 1 included);
- the full 12-check battery and the board judge each hypothesis once.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.external import ExternalStore  # noqa: E402
from aitrader.data.instruments import UNIVERSE_KEY  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.battery import BatteryRules  # noqa: E402
from aitrader.research.discovery.catalog import FeatureCatalog, truncation_leaks  # noqa: E402
from aitrader.research.discovery.confirm import ConfirmatoryProgram, ConfirmDesign  # noqa: E402
from aitrader.research.discovery.hypothesis import Hypothesis, Ledger  # noqa: E402
from aitrader.research.discovery.macro import GROUPS3, external_leaks, macro_primitives, macro_records  # noqa: E402
from aitrader.research.discovery.primitives import USD_SIGN  # noqa: E402
from aitrader.research.discovery.study import Condition, Segment  # noqa: E402
from aitrader.research.discovery.universe import FX, load_universe  # noqa: E402
from aitrader.research.labels import CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
EXTERNAL = ("vix", "us10y", "brent")
FIT = Segment("fit", "fit", date(2007, 4, 2), date(2008, 7, 1))
JUDGE = Segment("confirmation", "judge", date(2008, 7, 11), date(2017, 1, 1))
RULES = BatteryRules(t_threshold=1.0).describe()
USD_PAIRS = tuple(sorted(USD_SIGN))
CARRY = ("AUDJPY", "AUDUSD", "NZDUSD")
POLICY_RATES = ("DOCUMENTED FACT (prior knowledge; the primary sources are refused by this environment's network "
                "policy): from 2008-07 to 2016-12 the RBA cash rate never fell below 1.50% and the RBNZ OCR never "
                "below 1.75%, while the Fed funds target never exceeded 2.00% and the BoJ rate 0.50%; so AUD and "
                "NZD out-yielded USD and JPY at every date judged. Only the SIGN of the differential is used; its "
                "size is not, because no historical series of it is available here.")


@dataclass(frozen=True)
class Spec:
    hid: str
    condition: str
    side: str
    instruments: tuple[str, ...]
    exit: str
    statement: str
    mechanism: str
    sources: str


@dataclass(frozen=True)
class Family:
    pid: str
    title: str
    question: str
    specs: tuple[Spec, ...]
    costs: CostModel
    cost_note: str
    rationale: str


D1_COSTS = CostModel(swap_atr_per_night=0.01)
FAMILIES: dict[str, Family] = {f.pid: f for f in (
    Family("R2A", "Carry, conditional on the risk regime",
           "Do the positive-carry legs (long AUDJPY, AUDUSD, NZDUSD) earn a positive spot return net of costs "
           "while the risk regime is calm, and lose while risk is rising?",
           (Spec("R2A-1", "vix_state=low", "BUY", CARRY, "D4",
                 "While VIX closes below 20, buying the high-yield currency against USD or JPY and holding about a "
                 "month (exit D4) has positive net expectancy from the spot move alone.",
                 "carry is compensation for crash risk: in calm markets carry currencies drift up as capital "
                 "seeks yield, and they crash when risk appetite collapses",
                 "Brunnermeier, Nagel & Pedersen, Carry trades and currency crashes, NBER Macro Annual 23 (2008); "
                 "Menkhoff, Sarno, Schmeling & Schrimpf, Carry trades and global FX volatility, J. Finance 67 "
                 "(2012)"),
            Spec("R2A-2", "vix_trend=high", "SELL", CARRY, "D3",
                 "When VIX has risen more than 10% over five closes, selling the high-yield currency against USD or "
                 "JPY and holding a week (exit D3) has positive net expectancy.",
                 "carry unwinds are forced deleveraging that continues for days once volatility starts rising",
                 "Brunnermeier, Nagel & Pedersen (2008); Menkhoff et al. (2012)")),
           CostModel(swap_atr_per_night=0.0),
           "swap is NOT charged on these legs: the historical broker swap on a long high-yield position was a "
           "credit, and its size is unknown here. The spot move alone is judged, so the carry income itself is "
           "left out, which biases the test AGAINST the long leg (R2A-1) and in favour of the short leg (R2A-2), "
           "whose true swap was a cost; R2A-2 is also reported with the standard swap charged",
           POLICY_RATES),
    Family("R2B", "US rate-differential changes",
           "Does last month's change in US 10-year yields predict the next month's move of the USD pairs, in the "
           "direction the changed differential favours?",
           (Spec("R2B-1", "usd_rate=high", "BUY", USD_PAIRS, "D4",
                 "When last month's US 10y average moved more than 10bp in the direction that favours buying the "
                 "pair (yields up for USDxxx, down for xxxUSD), buying it and holding about a month (exit D4) has "
                 "positive net expectancy.",
                 "rate differentials attract capital slowly; the currency whose relative yield rose keeps "
                 "appreciating (the forward-premium anomaly: high-yield currencies do not depreciate as UIP says)",
                 "Fama, Forward and spot exchange rates, J. Monetary Economics 14 (1984); Engel, The forward "
                 "discount anomaly and the risk premium, J. Empirical Finance 3 (1996)"),
            Spec("R2B-2", "usd_rate=low", "SELL", USD_PAIRS, "D4",
                 "When last month's US 10y average moved more than 10bp in the direction that favours selling the "
                 "pair, selling it and holding about a month (exit D4) has positive net expectancy.",
                 "the mirror of R2B-1", "Fama (1984); Engel (1996)")),
           D1_COSTS, "standard D1 costs (swap 0.01 x ATR24(D1) per night charged)",
           "only the US side of the differential is observable here; the foreign rates of the six other "
           "currencies moved far less than US yields over 2008-2016 (most were at or near their floors), so the "
           "US change is taken as the change of the differential: an INFERRED assumption, stated"),
    Family("R2C", "Cross-asset: oil and the Canadian dollar",
           "Does a 20-day move in Brent of more than 5% predict the next week's move of USDCAD, in the direction "
           "oil favours?",
           (Spec("R2C-1", "oil_pull=high", "BUY", ("USDCAD",), "D3",
                 "After Brent fell more than 5% over 20 observations, buying USDCAD and holding a week (exit D3) has "
                 "positive net expectancy.",
                 "Canada's terms of trade move with oil; if FX absorbs oil news slowly, the CAD follows oil with a lag",
                 "Chen & Rogoff, Commodity currencies, J. International Economics 60 (2003); against: Ferraro, "
                 "Rogoff & Rossi, Can oil prices forecast exchange rates?, J. Int. Money and Finance 54 (2015): "
                 "the link is contemporaneous and daily, not lagged"),
            Spec("R2C-2", "oil_pull=low", "SELL", ("USDCAD",), "D3",
                 "After Brent rose more than 5% over 20 observations, selling USDCAD and holding a week (exit D3) has "
                 "positive net expectancy.", "the mirror of R2C-1", "Chen & Rogoff (2003); Ferraro et al. (2015)")),
           D1_COSTS, "standard D1 costs",
           "the documented evidence is AGAINST a lagged effect (Ferraro et al. 2015): this family is tested because "
           "cross-asset information is new here, with a low prior stated in advance"),
    Family("R2D", "Regime-conditioned time-series momentum",
           "Does time-series momentum, rejected unconditionally in CP-001, have positive net expectancy when "
           "restricted in advance to calm risk regimes?",
           (Spec("R2D-1", "trend_sign=high&vix_state=low", "BUY", FX, "D4",
                 "While VIX is below 20, buying a pair whose 120-day move is up and holding about a month (exit D4) "
                 "has positive net expectancy.",
                 "momentum crashes happen in high-volatility panic states and rebounds; excluding them in advance "
                 "should remove the crashes that erase momentum's premium",
                 "Daniel & Moskowitz, Momentum crashes, J. Financial Economics 122 (2016); Moskowitz, Ooi & "
                 "Pedersen, Time series momentum, JFE 104 (2012)"),
            Spec("R2D-2", "trend_sign=low&vix_state=low", "SELL", FX, "D4",
                 "While VIX is below 20, selling a pair whose 120-day move is down and holding about a month (exit "
                 "D4) has positive net expectancy.", "the mirror of R2D-1",
                 "Daniel & Moskowitz (2016); Moskowitz et al. (2012)")),
           D1_COSTS, "standard D1 costs",
           "a pre-registered CONDITIONAL hypothesis that explains why the unconditional rule failed (crash "
           "states); not a re-run of CP-001, whose sign rule and period differ"),
)}


def features(f: Family) -> tuple[str, ...]:
    return tuple(sorted({x for s in f.specs for x in Condition.parse(s.condition).features}))


def hypotheses(f: Family, prims: dict) -> list[Hypothesis]:
    recs = macro_records(f.pid, prims)
    out = []
    for s in f.specs:
        feats = tuple(recs[x].id for x in Condition.parse(s.condition).features)
        out.append(Hypothesis(
            id=s.hid, statement=s.statement,
            rationale=f"{s.sources}. {f.rationale}. Costs: {f.cost_note}.", mechanism=s.mechanism,
            features=feats, condition=s.condition, side=s.side, instruments=s.instruments, timeframe="D1",
            exit=s.exit, expected_effect="mean net R per trade > 0 on 2008-07 .. 2017-01",
            falsification=tuple(f"{k}: {v}" for k, v in RULES.items() if k != "significance"),
            budget=1, origin="human", program=f.pid, evidence={"round": 2, "family": f.pid}))
    return out


def program(reg: Registry, f: Family) -> ConfirmatoryProgram:
    insts = tuple(sorted({i for s in f.specs for i in s.instruments}))
    d = ConfirmDesign(f.pid, f.title, f.question, UNIVERSE_KEY, insts, tuple(s.hid for s in f.specs), FIT, JUDGE,
                      BatteryRules(t_threshold=1.0), reg.holdout.start,
                      groups=tuple((x, GROUPS3) for x in features(f)), costs=f.costs, min_embargo_days=10,
                      lookback_start=date(2007, 3, 30))
    if any(t.id == f.pid for t in reg.trials):
        thr = reg.get(f.pid).design["confirmatory_program"]["rules"]["t_threshold"]
    else:
        thr = reg.threshold_for_next(d.universe, d.judge.start, d.judge.end, new_tests=len(f.specs))
    d = replace(d, rules=replace(d.rules, t_threshold=thr))
    return ConfirmatoryProgram(d, reg, Ledger(R / "discovery" / "ledger.jsonl"),
                               FeatureCatalog(R / "discovery" / "features.jsonl"), R / "knowledge",
                               lambda: datetime.now(timezone.utc))


def external(holdout) -> dict:
    st = ExternalStore(ROOT / "data" / "external", holdout)
    return {k: st.load(k) for k in EXTERNAL}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("draft", "preregister", "run"))
    ap.add_argument("family", choices=tuple(FAMILIES))
    a = ap.parse_args()
    f = FAMILIES[a.family]
    now = datetime.now(timezone.utc)
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    ext = external(holdout)
    prims = {k: v for k, v in macro_primitives(ext).items() if k in features(f)}
    prog = program(reg, f)
    store = DataStore(ROOT / "data" / "processed", holdout)
    doc = f"research/preregistrations/{f.pid}-round2.md"
    if a.cmd == "draft":
        cat = prog.catalog
        if cat.budget(f.pid)[1] == 0:
            cat.open_program(f.pid, len(prims), now)
        for name, rec in macro_records(f.pid, prims).items():
            rec = cat.register(rec, now)
            if cat.leakage_status(rec.id) == "PASSED":
                continue
            bad, n, syms = [], 0, []
            for sym in prog.design.instruments:
                ser = store.load(sym, "D1")
                rows = list(range(300, len(ser), max(1, (len(ser) - 300) // 12)))
                if name == "trend_sign":
                    bad += truncation_leaks(lambda s_, o_: prims[name].column(s_, None, o_), ser, {}, rows)
                else:
                    bad += external_leaks(name, ser, ext, rows)
                n += len(rows)
                syms.append(sym)
            print(name, cat.record_leakage(rec.id, bad, n, syms, now), f"{n} rows")
        for h in hypotheses(f, prims):
            prog.ledger.draft(h, now)
        print("drafted", [s.hid for s in f.specs])
    elif a.cmd == "preregister":
        t = prog.preregister(ROOT / doc, doc)
        print(f"registered {t.id}: {t.tests} tests, t >= {prog.design.rules.t_threshold:.4f}")
    else:
        data, hashes = load_universe(store, symbols=prog.design.instruments, timeframe="D1", bound=tuple(prims.values()))
        art = prog.run(data, hashes)
        print(json.dumps({"verdict": art["verdict"], "judged": [
            {"id": c["id"], "n": c["battery"]["checks"]["min_trades"]["n"],
             "mean_R": c["battery"]["checks"]["significance"]["mean_R"], "t": c["battery"]["checks"]["significance"]["t"],
             "failed": c["battery"]["failed"], "board": c["board"]["verdict"]} for c in art["judged"]]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
