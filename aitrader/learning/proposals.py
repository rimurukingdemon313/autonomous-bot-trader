"""Experiment PROPOSALS from the running system's reflection and lessons.

Production code (the orchestrator) writes these to the immutable `experiments` table. A proposal
changes nothing: it is run, counted and judged only in the research lab, on a research machine.
This module lives here, outside `aitrader.research`, so that nothing that runs imports the
laboratory (tests/unit/test_architecture.py). `aitrader.research.hypotheses` re-exports it.
"""

from __future__ import annotations

import hashlib
import json

HYPOTHESES_VERSION = "hypotheses-1.0.0"


def _sig(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]


def proposals_from_reflection(reflection: dict, lessons: dict[str, list[dict]] | None = None) -> list[dict]:
    """Structured, deduplicable experiment proposals. Nothing here is registered or run."""
    out = []

    def add(kind: str, statement: str, test: str, **data):
        core = {"kind": kind, **data}
        out.append({"signature": f"{kind}:{_sig(core)}", "kind": kind, "status": "PROPOSED",
                    "statement": statement, "suggested_test": test, "data": data,
                    "source": "reflection", "version": HYPOTHESES_VERSION, "t": reflection.get("t")})

    for h in reflection.get("hypotheses", []):
        k = h.get("kind")
        if k == "OBJECTION_UNINFORMATIVE":
            add("OBJECTION_INFORMATION", f"objection {h['code']} may not predict worse outcomes",
                "lab: compare R of candidates flagged vs not flagged on fit data, then judge out of sample",
                code=h["code"])
        elif k == "OVER_FILTERING":
            add("FILTER_COST", "skipped candidates outperformed traded ones",
                "lab: a spec whose threshold admits the skipped set, judged against the current system")
        elif k == "REPEATED_MISTAKE":
            add("MISTAKE_FEATURE", f"loss cause {h['cause']} recurs",
                "feature lab: grammar candidates describing the cause, gated for leakage, judged incrementally",
                cause=h["cause"])
        elif k == "MODEL_DRIFT":
            add("DRIFT", "outcomes persistently below predictions",
                "lab: refit the estimator on recent data only vs expanding, judged out of sample")
    for group in ("by_family", "by_regime"):
        for name, st in (reflection.get(group) or {}).items():
            if st.get("n", 0) >= 30 and st.get("mean") is not None and st.get("se") \
                    and st["mean"] + 1.28 * st["se"] < 0:
                add("UNDERPERFORMING_CONTEXT", f"{group[3:]} {name} lost {st['mean']:+.3f}R over {st['n']} trades",
                    "lab: gate hypothesis on fit data, judged out of sample; a live lesson already covers acting on it",
                    group=group, name=name)
    for lid, versions in (lessons or {}).items():
        if versions and versions[-1].get("status") == "VALIDATED":
            add("LESSON_OFFLINE", f"validated lesson {lid} should hold on history it never saw",
                "lab: the lesson's context as a gate, judged on a period outside the lesson's evidence",
                lesson=lid)
    return out
