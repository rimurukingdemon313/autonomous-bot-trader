"""The discovery engine from the command line (research machine only).

    python scripts/discover.py design        # the DP-001 design and its frozen threshold; writes nothing
    python scripts/discover.py preregister   # catalog every feature, leakage-test it on real bars, register
                                             # the trial and write the preregistration document
    python scripts/discover.py run           # run DP-001 ONCE; refused if the design or the code changed
    python scripts/discover.py status        # registry, ledger and catalog state
    python scripts/discover.py search TEXT   # hypotheses and features, rejected ones included

Nothing here changes production. Results go to research/knowledge/; a VALIDATED hypothesis is a
research finding whose next step is a prospective paper test.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.discovery.catalog import FeatureCatalog  # noqa: E402
from aitrader.research.discovery.hypothesis import Ledger  # noqa: E402
from aitrader.research.discovery.program import DiscoveryProgram  # noqa: E402
from aitrader.research.discovery.universe import (FX, dp001, dp001_as_registered, feature_records,  # noqa: E402
                                                  leakage_checker, load_universe)
from aitrader.research.registry import Holdout, Registry  # noqa: E402

RESEARCH = ROOT / "research"
DOC = "research/preregistrations/DP-001-discovery.md"


def _clock() -> datetime:
    return datetime.now(timezone.utc)  # the edge of the system: everything below takes this clock injected


def _program() -> tuple[DiscoveryProgram, DataStore]:
    holdout = Holdout.load(RESEARCH / "holdout.json")
    reg = Registry.load(RESEARCH / "registry.jsonl", holdout)
    design = dp001_as_registered(reg) if any(t.id == "DP-001" for t in reg.trials) else dp001(reg)
    prog = DiscoveryProgram(design, reg, Ledger(RESEARCH / "discovery" / "ledger.jsonl"),
                            FeatureCatalog(RESEARCH / "discovery" / "features.jsonl"), RESEARCH / "knowledge", _clock,
                            feature_records("DP-001"))
    return prog, DataStore(ROOT / "data" / "processed", holdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("design", "preregister", "run", "status"):
        sub.add_parser(name)
    se = sub.add_parser("search")
    se.add_argument("text")
    a = ap.parse_args()
    prog, store = _program()
    if a.cmd == "design":
        d = prog.design
        print(json.dumps(d.to_json(), indent=1))
        print(f"sha256 {d.sha256()}  threshold t >= {d.rules.t_threshold:.4f}  judged tests {d.judged_tests()}  "
              f"configurations {d.configurations()}")
    elif a.cmd == "preregister":
        series = {s: store.load(s, "H1") for s in FX}
        trial = prog.preregister(ROOT / DOC, DOC, leakage_checker(series))
        print(f"registered {trial.id}: tests {trial.tests}, configurations {trial.configurations}, "
              f"threshold t >= {prog.design.rules.t_threshold:.4f}; document {DOC}")
    elif a.cmd == "run":
        data, hashes = load_universe(store)
        art = prog.run(data, hashes)
        print(json.dumps({k: art[k] for k in ("verdict", "validated", "follow_up_drafts", "next_experiment")} |
                         {"screen": {k: art["screen"][k] for k in ("tests", "testable", "discoveries")},
                          "finalists": art["validation"]["finalists"],
                          "judged": [(c["id"], c["board"]["verdict"], c["battery"]["failed"])
                                     for c in art["confirmation"]]}, indent=1))
    elif a.cmd == "status":
        reg = prog.registry
        print(json.dumps({"DP-001": reg.status_of("DP-001") if any(t.id == "DP-001" for t in reg.trials) else "not registered",
                          "ledger": prog.ledger.counts(),
                          "catalog": {r.id: prog.catalog.leakage_status(r.id) for r in prog.catalog.records()}},
                         indent=1))
    else:
        print(json.dumps({"hypotheses": prog.ledger.search(a.text), "features": prog.catalog.search(a.text)},
                         indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
