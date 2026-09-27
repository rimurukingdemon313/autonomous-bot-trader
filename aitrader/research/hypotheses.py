"""Where hypotheses come from, and the rule that none of them acts by itself.

Three sources, one path:

1. OBSERVATION. `ResearchLab.scan` measures, on FIT data only, whether any
   declared feature carries information about outcomes. It uses a Bonferroni
   correction over everything scanned and is recorded in the registry as
   exposure (role fit). A significant observation becomes a DRAFT spec.
2. EXPERIENCE. The running system's reflection and lessons become
   structured experiment PROPOSALS (`proposals_from_reflection`). They are
   journalled in the immutable `experiments` table as PROPOSED and shown on
   the dashboard.
3. A LANGUAGE MODEL, if configured (`llm_drafts`). It may draft specs from
   a closed vocabulary (the declared features, models and templates). The
   lab refuses to fit or judge them on data before the model's training
   cutoff.

A draft or a proposal changes nothing. It becomes evidence only by being
registered in the lab, run walk-forward, and judged against the registry's
threshold. It reaches production only through a reviewed promotion. "A loss
creates evidence, not a rule" (PROJECT_SPEC §6).
"""

from __future__ import annotations

import hashlib
import json
from datetime import date

from .lab import HypothesisSpace, HypothesisSpec, LabError

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


def llm_drafts(client, space: HypothesisSpace, observations: dict, *, id_prefix: str, fit_start: date,
               judge_start: date, judge_end: date, cutoff: date, max_drafts: int = 3) -> list[HypothesisSpec]:
    """Ask a language model for up to `max_drafts` specs from the closed vocabulary.

    Invalid or out-of-space replies are dropped, never repaired. Drafts are
    returned UNREGISTERED; the lab applies the cutoff rule when one is
    registered.
    """
    vocab = {"features": list(space.base_features), "models": list(space.models),
             "templates": list(space.templates), "timeframes": list(space.timeframes),
             "symbols": list(space.symbols)}

    def validate(d: dict) -> str | None:
        items = d.get("hypotheses")
        if not isinstance(items, list) or not items or len(items) > max_drafts:
            return f"hypotheses must be a list of 1..{max_drafts}"
        for h in items:
            if not isinstance(h, dict) or not isinstance(h.get("statement"), str):
                return "each hypothesis needs a statement"
            if not h.get("features") or any(f not in vocab["features"] for f in h["features"]):
                return "features must come from the declared list"
            if h.get("model") not in vocab["models"] or h.get("template") not in vocab["templates"]:
                return "model and template must be declared values"
        return None

    system = ("You propose testable trading-research hypotheses. Use ONLY the observations given, "
              "stated as of the end of the fit period. Reply with ONE JSON object: "
              '{"hypotheses": [{"statement": "...", "features": [...], "model": "...", "template": "..."}]}. '
              f"Allowed values: {json.dumps(vocab)}")
    res = client.complete_json("research", system, {"observations": observations}, validate)
    if not res.ok:
        return []
    drafts = []
    for i, h in enumerate(res.data["hypotheses"]):
        try:
            spec = HypothesisSpec(f"{id_prefix}-{i + 1}", h["statement"][:400], "llm", space.universe,
                                  space.symbols, space.timeframes[0], tuple(h["features"]), h["model"],
                                  h["template"], fit_start, judge_start, judge_end, llm_cutoff=cutoff)
            space.check(spec)
        except LabError:
            continue
        drafts.append(spec)
    return drafts
