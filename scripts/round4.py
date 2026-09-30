"""Round 4: is there information OUTSIDE the FX pair that predicts its direction beyond its own price?

    python scripts/round4.py draft          # catalog + leakage tests on real data + DRAFTs
    python scripts/round4.py preregister    # registry trial (threshold from the registry); commit before run
    python scripts/round4.py run            # once

Sources (docs/ROUND4_AUDIT.md): gold (never tested), VIX spikes as a lead for the safe havens (VIX was
only a regime filter before), US CPI (unrevised; never tested). Positioning (COT), consensus surprises,
decision surprises and first-release macro are DATA-BLOCKED here and are not approximated.

Every hypothesis pairs the outside information with the OPPOSITE own-price move (own5): the pair has
not yet moved the way the outside information says. A positive result therefore means the outside
source LEADS the pair -- information its own recent price did not contain. The price-only control
(own5 alone, same pairs, side and exit) is reported beside each result by scripts/r4_report.py.
Fixed levels, nothing fitted; judged once on 2008-07-11 -> 2017-01-01 (gold exists from 2011-05);
standard D1 costs; the full battery at the registry's threshold.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.external import ExternalStore  # noqa: E402
from aitrader.data.instruments import UNIVERSE_KEY  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.battery import BatteryRules  # noqa: E402
from aitrader.research.discovery.catalog import FeatureCatalog, FeatureRecord, truncation_leaks  # noqa: E402
from aitrader.research.discovery.confirm import ConfirmatoryProgram, ConfirmDesign  # noqa: E402
from aitrader.research.discovery.crossasset import CROSSASSET_VERSION, crossasset_primitives  # noqa: E402
from aitrader.research.discovery.hypothesis import Hypothesis, Ledger  # noqa: E402
from aitrader.research.discovery.study import Segment  # noqa: E402
from aitrader.research.discovery.universe import load_universe  # noqa: E402
from aitrader.research.labels import CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
PID = "R4"
DOC = "research/preregistrations/R4-directional-information.md"
FIT = Segment("fit", "fit", date(2007, 4, 2), date(2008, 7, 1))
JUDGE = Segment("confirmation", "judge", date(2008, 7, 11), date(2017, 1, 1))
GROUPS3 = ((0.0,), (1.0,), (2.0,))
COSTS = CostModel(swap_atr_per_night=0.01)
USD_PAIRS = ("AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY")
SAFE_HAVEN = ("EURCHF", "EURJPY", "GBPJPY", "USDCHF", "USDJPY")  # JPY or CHF is the quote, base is not a carry ccy
AUD_BASE = ("AUDJPY", "AUDUSD")


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


SPECS = (
    Spec("R4-XA-GOLD-A", "gold_pull=high&own5=low", "BUY", AUD_BASE, "D3",
         "After gold rose >= 2% over 5 days while the AUD pair FELL, buying the AUD pair and holding a week (D3) has "
         "positive net expectancy.",
         "Australia is a major gold exporter; if FX absorbs terms-of-trade news more slowly than the gold market, AUD "
         "catches up with gold",
         "Chen & Rogoff, Commodity currencies, JIE 60 (2003) (link); AGAINST a lead: Chen, Rogoff & Rossi, Can "
         "exchange rates forecast commodity prices?, QJE 125 (2010) find FX leads commodities, not the reverse"),
    Spec("R4-XA-GOLD-B", "gold_pull=low&own5=high", "SELL", AUD_BASE, "D3",
         "After gold fell >= 2% over 5 days while the AUD pair ROSE, selling it and holding a week (D3) has positive "
         "net expectancy.", "the mirror of R4-XA-GOLD-A", "as R4-XA-GOLD-A"),
    Spec("R4-XA-VIX-A", "vix_jump=high&own5=high", "SELL", SAFE_HAVEN, "D3",
         "After VIX jumped >= 20% over 5 closes while a JPY- or CHF-quoted pair still ROSE, selling it (buying the safe "
         "haven) and holding a week (D3) has positive net expectancy.",
         "safe-haven demand after a risk shock is met with a lag (repatriation, hedge adjustments), so the haven "
         "currency catches up with the shock",
         "Ranaldo & Soederlind, Safe haven currencies, Review of Finance 14 (2010) (contemporaneous haven moves; the "
         "lag is INFERRED); Habib & Stracca, Getting beyond carry trade, JIE 87 (2012)"),
    Spec("R4-MACRO-CPI-A", "usd_infl=high", "BUY", USD_PAIRS, "D4",
         "When the latest US CPI shows 12-month inflation >= 0.3pp higher than 3 months earlier, buying the pair "
         "whose USD leg that favours (and when it decelerates, the pair that sells USD) and holding about a month "
         "(D4) has positive net expectancy.",
         "accelerating inflation raises expected Fed tightening, which the market prices over weeks after the print",
         "Taylor-rule exchange-rate models: Molodtsova & Papell, Out-of-sample exchange rate predictability with "
         "Taylor rule fundamentals, JIE 77 (2009) (with both countries' inflation; only the US side is observable "
         "here)"),
    Spec("R4-MACRO-CPI-B", "usd_infl=low", "SELL", USD_PAIRS, "D4",
         "When the US inflation change disfavours the pair's USD leg by >= 0.3pp, selling the pair and holding about "
         "a month (D4) has positive net expectancy.", "the mirror of R4-MACRO-CPI-A", "as R4-MACRO-CPI-A"),
)
RULES = BatteryRules(t_threshold=1.0).describe()


def features() -> tuple[str, ...]:
    return tuple(sorted({p.split("=")[0] for s in SPECS for p in s.condition.split("&")}))


def primitives(holdout, store):
    st = ExternalStore(ROOT / "data" / "external", holdout)
    ext = {k: st.load(k) for k in ("vix", "cpi_us")}
    gold = store.load("XAUUSD", "D1")
    return ext, gold, crossasset_primitives(ext, gold)


def records(prims) -> dict[str, FeatureRecord]:
    return {n: FeatureRecord(
        f"{n}.D1", f"on D1 bars: {p.definition}", p.dimension, "categorical", "D1", p.requires,
        f"aitrader/research/discovery/crossasset.py ({CROSSASSET_VERSION}); research only", CROSSASSET_VERSION,
        "gold bars at the same close; VIX as public at 16:45 New York; CPI from the last day of the following month; "
        "fixed levels, nothing fitted; NaN when unavailable", "does outside information lead the pair's direction?",
        PID) for n, p in prims.items() if n in features()}


def program(reg: Registry) -> ConfirmatoryProgram:
    insts = tuple(sorted({i for s in SPECS for i in s.instruments}))
    d = ConfirmDesign(PID, "Directional information from outside the FX pair",
                      "Does gold, a VIX spike or US inflation acceleration predict an FX pair's direction BEYOND "
                      "its own recent price, after costs, out of sample?", UNIVERSE_KEY, insts,
                      tuple(s.hid for s in SPECS), FIT, JUDGE, BatteryRules(t_threshold=1.0), reg.holdout.start,
                      groups=tuple((f, GROUPS3) for f in features()), costs=COSTS, min_embargo_days=10,
                      lookback_start=date(2007, 3, 30))
    if any(t.id == PID for t in reg.trials):
        thr = reg.get(PID).design["confirmatory_program"]["rules"]["t_threshold"]
    else:
        thr = reg.threshold_for_next(d.universe, d.judge.start, d.judge.end, new_tests=len(SPECS))
    d = replace(d, rules=replace(d.rules, t_threshold=thr))
    return ConfirmatoryProgram(d, reg, Ledger(R / "discovery" / "ledger.jsonl"),
                               FeatureCatalog(R / "discovery" / "features.jsonl"), R / "knowledge",
                               lambda: datetime.now(timezone.utc))


def hypotheses(recs) -> list[Hypothesis]:
    return [Hypothesis(
        id=s.hid, statement=s.statement, rationale=f"{s.sources}. Controlled for the pair's own 5-day move (own5).",
        mechanism=s.mechanism, features=tuple(recs[p.split('=')[0]].id for p in s.condition.split("&")),
        condition=s.condition, side=s.side, instruments=s.instruments, timeframe="D1", exit=s.exit,
        expected_effect="mean net R per trade > 0 on 2008-07 .. 2017-01",
        falsification=tuple(f"{k}: {v}" for k, v in RULES.items() if k != "significance"), budget=1,
        origin="human", program=PID, evidence={"round": 4}) for s in SPECS]


def leaks(name, series, ext, gold, rows) -> list[int]:
    def col(s_, o_):
        t = int(s_.available_at[-1])
        e = {k: v.truncated(t) for k, v in ext.items()}
        g = gold.take(slice(0, int(np.searchsorted(gold.available_at, t, side="right"))))
        return crossasset_primitives(e, g)[name].column(s_, None, o_)
    return truncation_leaks(col, series, {}, rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("draft", "preregister", "run"))
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    store = DataStore(ROOT / "data" / "processed", holdout)
    ext, gold, prims = primitives(holdout, store)
    prims = {k: v for k, v in prims.items() if k in features()}
    recs = records(prims)
    prog = program(reg)
    if a.cmd == "draft":
        cat = prog.catalog
        if cat.budget(PID)[1] == 0:
            cat.open_program(PID, len(recs), now)
        for name, rec in recs.items():
            rec = cat.register(rec, now)
            if cat.leakage_status(rec.id) == "PASSED":
                continue
            bad, n = [], 0
            for sym in prog.design.instruments:
                ser = store.load(sym, "D1")
                rows = list(range(300, len(ser), max(1, (len(ser) - 300) // 10)))
                bad += leaks(name, ser, ext, gold, rows)
                n += len(rows)
            print(name, cat.record_leakage(rec.id, bad, n, list(prog.design.instruments), now), f"{n} rows")
        for h in hypotheses(recs):
            prog.ledger.draft(h, now)
        print("drafted", [s.hid for s in SPECS])
    elif a.cmd == "preregister":
        t = prog.preregister(ROOT / DOC, DOC)
        print(f"registered {t.id}: {t.tests} tests, t >= {prog.design.rules.t_threshold:.4f}")
    else:
        data, hashes = load_universe(store, symbols=prog.design.instruments, timeframe="D1",
                                     bound=tuple(prims.values()))
        art = prog.run(data, hashes)
        print(json.dumps({"verdict": art["verdict"], "judged": [
            {"id": c["id"], "n": c["battery"]["checks"]["min_trades"]["n"],
             "mean_R": c["battery"]["checks"]["significance"]["mean_R"], "t": c["battery"]["checks"]["significance"]["t"],
             "failed": c["battery"]["failed"], "board": c["board"]["verdict"]} for c in art["judged"]]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
