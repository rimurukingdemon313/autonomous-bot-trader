"""Why the judged trades lost: loss forensics on every hypothesis a confirmatory program judged.

    python scripts/loss_forensics.py      # -> research/results/LOSS-FORENSICS.json

DESCRIPTIVE, not a test: it re-derives the exact trades each program judged (same design,
same binnings fitted on the fit segment, same judged segment, same costs) and classifies each
loss by counterfactuals on the same bars (aitrader/research/discovery/forensics.py). Nothing
here is a verdict, and nothing is charged to the registry: a counterfactual that "would have
won" is a hypothesis for a future preregistered test, never a rule to adopt.

Every reproduced trade must match the recorded outcome exactly, or the script stops.
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
from aitrader.research.discovery.forensics import FORENSICS_VERSION, breakdown, classify  # noqa: E402
from aitrader.research.discovery.study import Condition, Study, fit_binning  # noqa: E402
from aitrader.research.discovery.universe import load_universe  # noqa: E402
from aitrader.research.labels import BUY, SELL  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"


def programs(reg: Registry):
    import cp001
    import strategy_library as sl
    from dataclasses import fields
    from aitrader.research.discovery.hypothesis import Hypothesis
    names = {f.name for f in fields(Hypothesis)}
    hs = []  # the drafts as registered: the library's pending list is empty once they are judged
    for line in (R / "discovery" / "ledger.jsonl").read_text().splitlines():
        e = json.loads(line)
        if e.get("event") == "DRAFT" and e["hypothesis"].get("program") in sl.PROGRAMS:
            h = {k: v for k, v in e["hypothesis"].items() if k in names}
            hs.append(Hypothesis(**{k: tuple(v) if isinstance(v, list) else v for k, v in h.items()}))
    yield "CP-001", "D1", cp001.program(reg), cp001.hypotheses()
    for pid, tf in sl.PROGRAMS.items():
        mine = [h for h in hs if h.program == pid]
        yield pid, tf, sl.program(reg, pid, mine), mine


def main() -> int:
    holdout = Holdout.load(R / "holdout.json")
    reg = Registry.load(R / "registry.jsonl", holdout)
    store = DataStore(ROOT / "data" / "processed", holdout)
    out = {"version": FORENSICS_VERSION, "note": "descriptive; not a test and not a rule", "hypotheses": {}}
    cache = {}
    pooled: dict[str, list] = {}
    for pid, tf, prog, hs in programs(reg):
        if tf not in cache:
            cache[tf] = load_universe(store, timeframe=tf)[0]
        d = prog.design
        data = {s: cache[tf][s] for s in d.instruments}
        judged = {c["id"]: c for c in json.loads((R / "knowledge" / f"{pid}.json").read_text())["judged"]}
        groups = {f: g for f, g in d.groups}
        feats = sorted({f for h in hs for f in Condition.parse(h.condition).features})
        base = Study(data, d.fit, {}, d.costs)
        binn = {f: fit_binning(f, {s: data[s].columns[f][base.rows[s]] for s in base.symbols}, groups=groups.get(f))
                for f in feats}
        judge = Study(data, d.judge, binn, d.costs)
        for h in hs:
            side = BUY if h.side == "BUY" else SELL
            tr = judge.trades(judge.masks(Condition.parse(h.condition)), h.exit, side)
            want = judged[h.id]["battery"]["checks"]["min_trades"]["n"]
            if tr.n != want:
                raise SystemExit(f"{h.id}: reproduced {tr.n} trades, the program judged {want}")
            ex = EXIT_BY_KEY[h.exit]
            res = []
            for s, row, r in zip(tr.symbol, tr.row, tr.r):
                sd = data[s]
                c = classify(sd.series, int(row), side, ex, sd.pip, d.costs, atr=sd.atr)
                if not np.isclose(c["r"], r, atol=1e-9):
                    raise SystemExit(f"{h.id} {s} row {row}: forensics r {c['r']} != judged r {r}")
                res.append(c)
            b = breakdown(res)
            pooled.setdefault(tf, []).extend(res)
            out["hypotheses"][h.id] = {"program": pid, "timeframe": tf, "side": h.side, "condition": h.condition,
                                       "exit": h.exit, **b}
            print(h.id, b["trades"], b["mean_R"], {k: v["share_of_R_lost"] for k, v in b["causes"].items()})
    # pooled over every judged trade, per timeframe: where the R went
    out["pooled"] = {tf: breakdown(v) for tf, v in sorted(pooled.items())}
    print("pooled", {tf: {k: c["share_of_R_lost"] for k, c in v["causes"].items()} for tf, v in out["pooled"].items()})
    (ROOT / "research" / "results" / "LOSS-FORENSICS.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
