"""The permanent Round 2 research ledger, generated from the committed evidence.

    python scripts/round2_ledger.py     # -> research/knowledge/round2_ledger.json + docs/ROUND2_LEDGER.md

One row per Round 2 hypothesis with every field the research plan asks for, read from:
the family design (scripts/round2.py), the source manifest (data/external/manifest.json), the
program's verdict (research/knowledge/R2?.json), the direction-and-cost report
(research/results/R2?-report.json) and the strategy library. A field the evidence does not hold is
null. Duplicate research is prevented upstream: the discovery ledger refuses a hypothesis whose
substance (condition, side, exit, instruments, timeframe) was already drafted, whatever its name.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aitrader.data.external import SOURCES  # noqa: E402
from aitrader.research.discovery.library import LIBRARY  # noqa: E402
from aitrader.research.discovery.study import Condition  # noqa: E402

R = ROOT / "research"
FEATURE_SOURCE = {"vix_state": "vix", "vix_trend": "vix", "usd_rate": "us10y", "oil_pull": "brent", "trend_sign": None}
FAMILY_METHOD = {"R2A": "SL-CARRY", "R2B": "SL-FORWARD-PREMIUM", "R2C": "SL-COMMODITY-FX", "R2D": "SL-MOMENTUM-CRASH"}


def main() -> int:
    import round2
    methods = {m.strategy_id: m for m in LIBRARY}
    rows = []
    for fam in round2.FAMILIES.values():
        art_p, rep_p = R / "knowledge" / f"{fam.pid}.json", R / "results" / f"{fam.pid}-report.json"
        art = json.loads(art_p.read_text()) if art_p.exists() else None
        rep = json.loads(rep_p.read_text())["hypotheses"] if rep_p.exists() else {}
        judged = {c["id"]: c for c in (art or {}).get("judged", [])}
        m = methods[FAMILY_METHOD[fam.pid]]
        for s in fam.specs:
            feats = Condition.parse(s.condition).features
            srcs = sorted({FEATURE_SOURCE[f] for f in feats if FEATURE_SOURCE[f]})
            c = judged.get(s.hid)
            ch = c["battery"]["checks"] if c else {}
            r = rep.get(s.hid, {})
            status = ("NOT RUN" if c is None else "VALIDATED" if s.hid in (art.get("validated") or [])
                      else "REJECTED")
            rows.append({
                "hypothesis_id": s.hid, "research_family": f"{fam.pid}: {fam.title}",
                "economic_rationale": s.mechanism, "family_rationale": fam.rationale,
                "data_sources": ["Dukascopy bid/ask D1 bars (data/manifest.json)"]
                                + [SOURCES[k].publisher for k in srcs],
                "data_timestamp_availability": {k: SOURCES[k].availability for k in srcs},
                "features": list(feats), "signal": s.condition, "direction": s.side,
                "entry": "market order at the next D1 open after a close where the condition holds; one position per "
                         "instrument at a time",
                "exit": s.exit, "risk": "sized by the Risk Engine only; the hypothesis carries no size",
                "instruments": list(s.instruments), "cost_assumptions": fam.cost_note,
                "training_period": f"{round2.FIT.start} -> {round2.FIT.end} (regime medians only; states are fixed)",
                "validation_period": f"{round2.JUDGE.start} -> {round2.JUDGE.end} (judged once, out of sample)",
                "out_of_sample_result": ({"n": ch["min_trades"]["n"], "net_R": ch["significance"]["mean_R"],
                                          "gross_R": r.get("gross_R"), "p_direction_correct": r.get("p_direction_correct"),
                                          "net_R_by_cost": r.get("net_R_by_cost")} if c else None),
                "statistical_result": ({"t": ch["significance"]["t"], "t_required": ch["significance"]["threshold"],
                                        "beats_random": ch["beats_random"]["pass"],
                                        "permutation_p": ch.get("permutation", {}).get("p")} if c else None),
                "robustness": ({k: ch[k]["pass"] for k in ("costs_stress", "delay_stress", "perturbation", "years",
                                                          "instruments", "leave_one_out", "regimes", "outliers")
                                if k in ch} if c else None),
                "failure_reason": (c["battery"]["failed"] + [f"board: {b}" for b in c["board"].get("blocked_by", [])]
                                   if c and status == "REJECTED" else None),
                "status": status, "source_methodology": "; ".join(src.citation for src in m.sources) + f" ({s.sources})",
                "evidence_quality": m.evidence_quality, "library_method": m.strategy_id,
            })
    (R / "knowledge" / "round2_ledger.json").write_text(json.dumps(rows, indent=1, sort_keys=True) + "\n")
    md = ["# Round 2 research ledger", "",
          "Generated by `python scripts/round2_ledger.py` from the committed evidence; do not edit by hand. The "
          "full record of every field is `research/knowledge/round2_ledger.json`.", "",
          "| ID | Family | Signal | Side | Exit | Data | n | P(dir) | Gross R | Net R (low / normal / high cost) | t "
          "(required) | Robustness passed | Status | Evidence |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        o, st, rb = x["out_of_sample_result"] or {}, x["statistical_result"] or {}, x["robustness"] or {}
        nc = o.get("net_R_by_cost") or {}
        md.append(f"| {x['hypothesis_id']} | {x['research_family'].split(':')[0]} | `{x['signal']}` | {x['direction']} | "
                  f"{x['exit']} | {', '.join(FEATURE_SOURCE[f] or 'bars' for f in x['features'])} | {o.get('n', '—')} | "
                  f"{o.get('p_direction_correct', '—')} | {o.get('gross_R', '—')} | "
                  f"{nc.get('lower', '—')} / {o.get('net_R', '—')} / {nc.get('higher', '—')} | "
                  f"{st.get('t', '—')} ({st.get('t_required', '—')}) | {sum(bool(v) for v in rb.values())}/{len(rb)} | "
                  f"**{x['status']}** | {x['evidence_quality']} |")
    (ROOT / "docs" / "ROUND2_LEDGER.md").write_text("\n".join(md) + "\n")
    print(len(rows), "rows", {x["hypothesis_id"]: x["status"] for x in rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
