"""FREE OpenRouter model discovery and selection for the dual-AI trading desk (docs/DUAL_AI.md).

The catalog (`GET /api/v1/models`) is read. A model is FREE only when all of these hold:
- It is one of OpenRouter's explicit free variants: its id ends in ":free". A model that merely lists a zero
  price without that suffix is a promotion that can end between two catalog reads, and OpenRouter's own
  "Free" filter does not list it; it is never used.
- EVERY price it lists is exactly zero: prompt, completion, request, image, web search, internal reasoning,
  cache. A missing pricing block, a negative or variable price, or any price above zero excludes it.
- It writes text only. Generators of audio or images are billed outside the token prices (Google's Lyria lists
  $0 prompt/completion while its description says "$0.08 per song"), and embedding or rerank models write
  vectors and scores, not answers.
- Its description states no price ("$0.04 per clip").
- It is not a router (`openrouter/...`), a safety/guard classifier, an embedding, rerank or speech model.

Selection is an explicit, declared score computed from the catalog's own fields. It is never tuned on trading
results:

    capability  the catalog's independent benchmark, the Artificial Analysis intelligence index, one point per
                index point (capped at 60); without it, from the parameter count in the id, at most 12
                (nothing stated: 4)
    context     5 x min(1, log2(context / 8192) / 5)
    vision      (Agent 1, reads the chart) needs image input:
                40 + capability + context + 3 reasoning + 2 recent
    trader      (Agent 2, independent) any FREE text model except Agent 1's:
                capability + context + 6 reasoning + 2 recent + 3 image input
                + 10 when its family (the id's prefix) differs from Agent 1's: two different minds
    verifier    (the debate) any FREE model except the two agents':
                capability + context + 6 reasoning + 4 image input (it can then see the chart) + 2 recent
                + 10 when its family differs from both agents'; with no third model, the strongest
                reasoning model of the two is reused
    (structured-output support is shown but not scored: the client asks for JSON in the prompt and never sends
    `response_format`, so that capability is not used)
    penalties   -10 for a single-domain specialist (code, health, medicine); a model expiring within 7 days is
                excluded, within 30 days it scores -10; 30 x its failure rate in this process (from 3 calls)

A model that fails is put on cooldown or excluded, and the next-best FREE model of the same role is used:
- a 404 "no endpoints", or unavailability;
- repeated errors;
- a reply showing a cost above zero, or one served by another model.

A paid model is never a fallback. When no free model qualifies, the role has no model and the decision is
NO_TRADE (the AI is unavailable; that is not a market judgement).
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

FREE_MODELS_VERSION = "free-models-1.2.0"
MIN_CONTEXT = 16_384
EXCLUDED_PREFIXES = ("openrouter/",)
FREE_SUFFIX = ":free"
CLASSIFIER_WORDS = ("safety", "guard", "moderation", "embed", "rerank", "tts", "speech", "whisper")
SPECIALIST_WORDS = ("code", "coder", "coding", "sante", "medical", "medicine", "health", "math")
PRICE_IN_TEXT = re.compile(r"\$\s?\d")


def _price(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def is_free(model: dict) -> bool:
    """Every listed price is exactly zero; prompt and completion must be listed."""
    pricing = model.get("pricing")
    if not isinstance(pricing, dict) or "prompt" not in pricing or "completion" not in pricing:
        return False
    for v in pricing.values():
        p = _price(v)
        if p is None or p != 0.0:
            return False
    mid = str(model.get("id") or "")
    if not mid or mid.startswith(EXCLUDED_PREFIXES) or not mid.endswith(FREE_SUFFIX):
        return False
    _, outs = modalities(model)
    if outs and outs != {"text"}:  # audio/image generation is billed outside the token prices
        return False
    if PRICE_IN_TEXT.search(str(model.get("description") or "")):
        return False
    words = f"{mid} {model.get('name', '')}".lower()
    return not any(w in words for w in CLASSIFIER_WORDS)


def modalities(model: dict) -> tuple[set, set]:
    arch = model.get("architecture") or {}
    ins = {str(x).lower() for x in (arch.get("input_modalities") or [])}
    outs = {str(x).lower() for x in (arch.get("output_modalities") or [])}
    if not ins and isinstance(arch.get("modality"), str) and "->" in arch["modality"]:  # older "text+image->text"
        a, b = arch["modality"].split("->", 1)
        ins, outs = set(a.split("+")), set(b.split("+"))
    return ins, outs


def supports_image(model: dict) -> bool:
    ins, outs = modalities(model)
    return "image" in ins and "text" in (outs or {"text"})


def context_length(model: dict) -> int:
    c = model.get("context_length") or (model.get("top_provider") or {}).get("context_length") or 0
    try:
        return int(c)
    except (TypeError, ValueError):
        return 0


def family(model_id: str) -> str:
    return model_id.split("/", 1)[0].lower() if "/" in model_id else model_id.lower()


def params_b(model: dict) -> float | None:
    """Total parameter count in billions, from the id or name ("70b", "235b-a22b", "8x7b"); None if unstated."""
    text = f"{model.get('id', '')} {model.get('name', '')}".lower()
    m = re.search(r"(\d+)x(\d+(?:\.\d+)?)b", text)
    if m:
        return float(m.group(1)) * float(m.group(2))
    sizes = [float(x) for x in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)b(?![a-z])", text)]
    return max(sizes) if sizes else None


def intelligence(model: dict) -> float | None:
    """The catalog's independent benchmark (Artificial Analysis intelligence index), when present."""
    aa = ((model.get("benchmarks") or {}).get("artificial_analysis") or {}) if isinstance(model.get("benchmarks"), dict) else {}
    v = aa.get("intelligence_index")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def capability(model: dict) -> float:
    ii = intelligence(model)
    if ii is not None:
        return min(60.0, max(0.0, ii))
    b = params_b(model)
    if b is None or b <= 0:
        return 4.0  # nothing measured, nothing stated
    return min(12.0, 12.0 * max(0.0, math.log2(b) / math.log2(400)))


def _ctx_score(model: dict) -> float:
    c = context_length(model)
    return 0.0 if c <= 8192 else 5.0 * min(1.0, math.log2(c / 8192) / 5)


def _expiry_days(model: dict, now: float) -> float | None:
    exp = model.get("expiration_date")
    if not exp:
        return None
    try:
        t = datetime.fromisoformat(str(exp)).replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None
    return (t - now) / 86400


def _penalty(model: dict, now: float) -> float:
    words = f"{model.get('id', '')} {model.get('name', '')}".lower()
    p = 10.0 if any(w in words for w in SPECIALIST_WORDS) else 0.0
    days = _expiry_days(model, now)
    if days is not None and days <= 30:
        p += 10.0
    return p


def _params(model: dict) -> set:
    return {str(p).lower() for p in (model.get("supported_parameters") or [])}


def _structured(model: dict) -> bool:
    return bool(_params(model) & {"response_format", "structured_outputs"})


def _reasoning(model: dict) -> bool:
    return bool(_params(model) & {"reasoning", "include_reasoning"})


def _recent(model: dict, now: float) -> bool:
    created = model.get("created")
    return isinstance(created, (int, float)) and now - created <= 365 * 86400


def vision_score(model: dict, now: float) -> float:
    return (40.0 + capability(model) + _ctx_score(model) + 3.0 * _reasoning(model) + 2.0 * _recent(model, now)
            - _penalty(model, now))


def judge_score(model: dict, now: float, vision_family: str | None) -> float:
    """Agent 2, the independent trader."""
    s = (capability(model) + _ctx_score(model) + 6.0 * _reasoning(model) + 2.0 * _recent(model, now)
         + 3.0 * supports_image(model) - _penalty(model, now))
    if vision_family is not None and family(model["id"]) != vision_family:
        s += 10.0
    return s


def verifier_score(model: dict, now: float, families: set[str]) -> float:
    """The debate: reasoning first; seeing the chart helps; a third family is the most independent."""
    s = (capability(model) + _ctx_score(model) + 6.0 * _reasoning(model) + 4.0 * supports_image(model)
         + 2.0 * _recent(model, now) - _penalty(model, now))
    if family(model["id"]) not in families:
        s += 10.0
    return s


def free_candidates(catalog: list[dict]) -> dict[str, list[dict]]:
    """FREE models usable per role (unscored): vision needs image input; both need text output and context."""
    now = time.time()
    free = [m for m in catalog if isinstance(m, dict) and is_free(m) and context_length(m) >= MIN_CONTEXT
            and (_expiry_days(m, now) is None or _expiry_days(m, now) > 7)]
    return {"vision": [m for m in free if supports_image(m)], "text": free}


@dataclass
class Selection:
    vision: list[dict] = field(default_factory=list)  # ranked [{"id", "score", "context", ...}]
    judge: list[dict] = field(default_factory=list)
    verifier: list[dict] = field(default_factory=list)
    free_total: int = 0
    catalog_total: int = 0
    refreshed: float = 0.0
    error: str | None = None

    def as_dict(self) -> dict:
        return {"vision": self.vision, "judge": self.judge, "verifier": self.verifier, "free_total": self.free_total,
                "catalog_total": self.catalog_total, "refreshed": self.refreshed, "error": self.error,
                "version": FREE_MODELS_VERSION}


def _row(m: dict, score: float) -> dict:
    ins, _ = modalities(m)
    return {"id": m["id"], "name": m.get("name"), "score": round(score, 2), "context": context_length(m),
            "image": "image" in ins, "intelligence_index": intelligence(m), "params_b": params_b(m),
            "structured": _structured(m), "reasoning": _reasoning(m), "family": family(m["id"]),
            "expires": m.get("expiration_date")}


def select(catalog: list[dict], now: float | None = None, penalties: dict[str, float] | None = None,
           excluded: set[str] | frozenset = frozenset()) -> Selection:
    """Rank FREE models per role. `penalties` (model -> failure rate) lower a score; `excluded` are skipped."""
    now = time.time() if now is None else now
    penalties = penalties or {}
    cands = free_candidates(catalog)
    sel = Selection(free_total=len(cands["text"]), catalog_total=len(catalog), refreshed=now)

    def pen(mid: str) -> float:
        return 30.0 * penalties.get(mid, 0.0)

    vis = sorted(((vision_score(m, now) - pen(m["id"]), m) for m in cands["vision"] if m["id"] not in excluded),
                 key=lambda x: (-x[0], x[1]["id"]))
    sel.vision = [_row(m, s) for s, m in vis]
    vfam = family(sel.vision[0]["id"]) if sel.vision else None
    top_vision = sel.vision[0]["id"] if sel.vision else None
    jud = sorted(((judge_score(m, now, vfam) - pen(m["id"]), m) for m in cands["text"]
                  if m["id"] not in excluded and m["id"] != top_vision),
                 key=lambda x: (-x[0], x[1]["id"]))
    sel.judge = [_row(m, s) for s, m in jud]
    top_judge = sel.judge[0]["id"] if sel.judge else None
    fams = {f for f in (vfam, family(top_judge) if top_judge else None) if f}
    ver = sorted(((verifier_score(m, now, fams) - pen(m["id"]), m) for m in cands["text"]
                  if m["id"] not in excluded and m["id"] not in (top_vision, top_judge)),
                 key=lambda x: (-x[0], x[1]["id"]))
    sel.verifier = [_row(m, s) for s, m in ver]
    if not sel.verifier:  # only two suitable models: the strongest reasoning one of them is reused
        both = [m for m in cands["text"] if m["id"] in (top_vision, top_judge)]
        both.sort(key=lambda m: (-(capability(m) + 6.0 * _reasoning(m)), m["id"]))
        sel.verifier = [_row(m, verifier_score(m, now, set())) for m in both[:1]]
    if not sel.vision:
        sel.error = "no FREE vision model in the catalog"
    elif not sel.judge:
        sel.error = "no FREE text model for the judge"
    return sel


__all__ = ["FREE_MODELS_VERSION", "FREE_SUFFIX", "MIN_CONTEXT", "Selection", "capability", "family",
           "free_candidates", "intelligence", "is_free", "judge_score", "params_b", "select", "supports_image",
           "verifier_score", "vision_score"]
