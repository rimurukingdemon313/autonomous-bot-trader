"""The strategy library's untested methods, judged by our own evidence once.

    python scripts/strategy_library.py export        # library, knowledge graph, priorities -> research/knowledge
    python scripts/strategy_library.py draft         # each pending test -> a DRAFT hypothesis (origin human)
    python scripts/strategy_library.py preregister   # SL-001 (daily forms) and SL-002 (hourly forms)
    python scripts/strategy_library.py run           # each once

A documented method is a reason to test a principle, never evidence that it works on our
instruments: the confirmatory program judges each form with the full battery and the board.
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
from aitrader.research.discovery.library import (conflicts, knowledge_graph, pending_tests,  # noqa: E402
                                                 principle_priority, to_json)
from aitrader.research.discovery.study import Segment  # noqa: E402
from aitrader.research.discovery.universe import FX, load_universe  # noqa: E402
from aitrader.research.labels import CostModel  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
PROGRAMS = {"SL-001": "D1", "SL-002": "H1"}
DOCS = {"SL-001": "research/preregistrations/SL-001-library-daily.md",
        "SL-002": "research/preregistrations/SL-002-library-hourly.md"}
GROUPS = {"H1": (("session", ((0.0,), (1.0, 2.0), (3.0, 4.0))),), "D1": ()}
COSTS = {"D1": CostModel(swap_atr_per_night=0.01), "H1": CostModel()}
RULES = BatteryRules(t_threshold=1.0).describe()


def feature_id(name: str, tf: str) -> str:
    from aitrader.research.discovery.universe import feature_records, feature_records_daily
    return (feature_records_daily("SL") if tf == "D1" else feature_records("SL"))[name].id


def drafts() -> list[Hypothesis]:
    out = []
    for m, t in pending_tests():
        prog = "SL-001" if t["timeframe"] == "D1" else "SL-002"
        k = sum(1 for h in out if h.program == prog) + 1
        feats = tuple(feature_id(p.split("=")[0], t["timeframe"]) for p in t["condition"].split("&"))
        out.append(Hypothesis(
            id=f"{prog}-{k:02d}", statement=f"{m.name}: {t['condition']} {t['side']} (exit {t['exit']}) has positive "
                                            "net expectancy on our FX data",
            rationale=(f"documented approach {m.strategy_id} ({'; '.join(s.citation for s in m.sources)}); evidence "
                       f"quality {m.evidence_quality}. Principles: {', '.join(m.principles)}. Tested because it is "
                       "documented, not believed because it is famous."),
            mechanism=f"{m.decision_process.get('assumptions', m.market_conditions)} (as documented; conjectured here)",
            features=feats, condition=t["condition"], side=t["side"], instruments=tuple(t.get("instruments", FX)),
            timeframe=t["timeframe"], exit=t["exit"], expected_effect="mean net R per trade > 0 on 2013-07 .. 2017-01",
            falsification=tuple(f"{k2}: {v}" for k2, v in RULES.items() if k2 != "significance"), budget=1,
            origin="human", program=prog, evidence={"library": m.strategy_id}))
    return out


def program(reg: Registry, pid: str, hs: list[Hypothesis]) -> ConfirmatoryProgram:
    tf = PROGRAMS[pid]
    insts = tuple(sorted({i for h in hs for i in h.instruments}))
    d = ConfirmDesign(pid, f"Strategy library, {tf} forms", "Do documented trading principles, in their testable "
                      f"{tf} forms, have positive net expectancy on our FX data after costs?", UNIVERSE_KEY, insts,
                      tuple(h.id for h in hs), Segment("fit", "fit", date(2007, 6, 1), date(2013, 7, 1)),
                      Segment("confirmation", "judge", date(2013, 7, 11), date(2017, 1, 1)), BatteryRules(t_threshold=1.0),
                      reg.holdout.start, groups=GROUPS[tf], costs=COSTS[tf], min_embargo_days=10,
                      lookback_start=date(2007, 3, 30))
    if any(t.id == pid for t in reg.trials):
        thr = reg.get(pid).design["confirmatory_program"]["rules"]["t_threshold"]
    else:
        thr = reg.threshold_for_next(d.universe, d.judge.start, d.judge.end, new_tests=len(hs))
    d = replace(d, rules=replace(d.rules, t_threshold=thr))
    return ConfirmatoryProgram(d, reg, Ledger(R / "discovery" / "ledger.jsonl"),
                               FeatureCatalog(R / "discovery" / "features.jsonl"), R / "knowledge",
                               lambda: datetime.now(timezone.utc))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("export", "draft", "preregister", "run"))
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    if a.cmd == "export":
        (R / "knowledge").mkdir(parents=True, exist_ok=True)
        (R / "knowledge" / "strategy_library.json").write_text(json.dumps(
            {"methods": to_json(), "conflicts": conflicts(), "principle_priority": principle_priority()},
            indent=1, sort_keys=True) + "\n")
        (R / "knowledge" / "knowledge_graph.json").write_text(json.dumps(knowledge_graph(), indent=1, sort_keys=True) + "\n")
        print("exported", len(to_json()), "methods")
        return 0
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    hs = drafts()
    if a.cmd == "draft":
        led = Ledger(R / "discovery" / "ledger.jsonl")
        for h in hs:
            led.draft(h, now)
        print("drafted", [h.id for h in hs])
        return 0
    store = DataStore(ROOT / "data" / "processed", holdout)
    for pid, tf in PROGRAMS.items():
        mine = [h for h in hs if h.program == pid]
        prog = program(reg, pid, mine)
        if a.cmd == "preregister":
            t = prog.preregister(ROOT / DOCS[pid], DOCS[pid])
            print(f"registered {t.id}: {t.tests} tests, t >= {prog.design.rules.t_threshold:.4f}")
            reg = Registry.load(R / "registry.jsonl", holdout)
        else:
            data, hashes = load_universe(store, timeframe=tf)
            art = prog.run({s: data[s] for s in prog.design.instruments}, hashes)
            print(pid, art["verdict"], json.dumps([{"id": c["id"], "cond": c["condition"], "side": c["side"],
                                                    "n": c["battery"]["checks"]["min_trades"]["n"],
                                                    "mean_R": c["battery"]["checks"]["significance"]["mean_R"],
                                                    "t": c["battery"]["checks"]["significance"]["t"],
                                                    "failed": c["battery"]["failed"]} for c in art["judged"]]))
            reg = Registry.load(R / "registry.jsonl", holdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
