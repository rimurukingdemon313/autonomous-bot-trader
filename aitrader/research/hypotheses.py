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

import json
from datetime import date

from ..learning.proposals import HYPOTHESES_VERSION, proposals_from_reflection  # noqa: F401  (re-export)
from .lab import HypothesisSpace, HypothesisSpec, LabError


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
