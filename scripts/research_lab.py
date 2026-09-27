"""The research lab from the command line (research machine only).

    python scripts/research_lab.py scan  --id SCAN-002 --fit 2007-04-01:2010-01-01 [--timeframe H1 --template T1]
    python scripts/research_lab.py register spec.json      # a HypothesisSpec as JSON; registers, runs nothing
    python scripts/research_lab.py run H-002               # runs a REGISTERED trial once and records its verdict

Every command writes to research/registry.jsonl. The data store truncates at
the sealed holdout, and the lab refuses any spec that reaches it. A scan
counts as exposure of its fit period; a run counts as a test on its judged
period. Nothing here changes production: a PASS writes an artifact under
research/artifacts/, and promotion is a separate, reviewed step.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.instruments import UNIVERSE_KEY  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.lab import HypothesisSpace, HypothesisSpec, ResearchLab  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
           "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY")


def _lab() -> tuple[ResearchLab, DataStore]:
    holdout = Holdout.load(ROOT / "research" / "holdout.json")
    reg = Registry.load(ROOT / "research" / "registry.jsonl", holdout)
    lab = ResearchLab(reg, HypothesisSpace(UNIVERSE_KEY, SYMBOLS), ROOT / "research" / "artifacts")
    return lab, DataStore(ROOT / "data" / "processed", holdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("scan")
    sc.add_argument("--id", required=True)
    sc.add_argument("--fit", required=True, help="START:END (END exclusive)")
    sc.add_argument("--timeframe", default="H1")
    sc.add_argument("--template", default="T1")
    rg = sub.add_parser("register")
    rg.add_argument("spec")
    rn = sub.add_parser("run")
    rn.add_argument("trial")
    a = ap.parse_args()
    lab, store = _lab()
    if a.cmd == "scan":
        f0, f1 = (date.fromisoformat(x) for x in a.fit.split(":"))
        series = {s: store.load(s, "H1") for s in SYMBOLS}
        res = lab.scan(a.id, series, universe=UNIVERSE_KEY, symbols=SYMBOLS, timeframe=a.timeframe,
                       template=a.template, fit_start=f0, fit_end=f1)
        print(json.dumps({k: res[k] for k in ("scan", "tests", "z_critical", "significant")}, indent=1))
    elif a.cmd == "register":
        spec = HypothesisSpec.from_json(json.loads(Path(a.spec).read_text()))
        print(json.dumps(lab.register(spec).to_json(), indent=1, default=str))
    else:
        spec = HypothesisSpec.from_json(lab.registry.get(a.trial).design["spec"])
        series = {s: store.load(s, "H1") for s in spec.symbols}
        res = lab.run(a.trial, series)
        out = ROOT / "research" / "results" / f"{a.trial}.json"
        out.write_text(json.dumps({k: v for k, v in res.items() if k != "random"} |
                                  {"random": res["random"]["stats"]}, indent=1, default=str))
        print(res["verdict"], json.dumps(res["checks"]), "->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
