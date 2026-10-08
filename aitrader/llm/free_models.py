"""FREE OpenRouter model discovery and selection for the dual-AI trader (docs/DUAL_AI.md).

The catalog (`GET /api/v1/models`) is read; a model is FREE only when EVERY price it lists is exactly zero:
prompt, completion, request, image, web search, internal reasoning, cache. A missing pricing block, a
negative or variable price (routers such as `openrouter/auto` list -1), or any price above zero excludes it.
Router and meta models (`openrouter/...`) are excluded outright: they choose the serving model themselves.

Selection is an explicit, declared score, computed from the catalog's own fields; it is not tuned on trading
results:

    vision  (Agent 1, chart image analysis)   requires image input and text output, context >= 16k
            40 for vision + up to 10 size + up to 10 context + 5 structured output + 5 reasoning + 3 recent
    judge   (Agent 2, independent evaluation)  requires text output, context >= 16k
            up to 10 size + up to 10 context + 8 structured output + 8 reasoning + 3 recent
            + 10 when its family (the id's prefix) differs from the vision model's: two different minds
    verifier (optional one-shot)               a vision model other than Agent 1 when one exists

    size      parameter count read from the id/name ("27b", "70b", "235b-a22b"): 10 * log2(B) / log2(400)
    context   10 * min(1, log2(context / 8192) / 5)        (8k -> 0, 256k -> 10)
    recent    created within the last 365 days
    reliability  every score is reduced by 30 x the model's failure rate in this process (>= 3 calls)

A model that fails (404 "no endpoints", unavailable, repeated errors, or a response showing a cost above zero)
is put on cooldown or excluded, and the next-best FREE model of the same role is used. A paid model is never a
fallback: when no free model qualifies, the role has no model and the decision is NO_TRADE.
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field

FREE_MODELS_VERSION = "free-models-1.0.0"
MIN_CONTEXT = 16_384
EXCLUDED_PREFIXES = ("openrouter/",)


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
    return bool(mid) and not mid.startswith(EXCLUDED_PREFIXES)


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


def _size_score(model: dict) -> float:
    b = params_b(model)
    if b is None or b <= 0:
        return 5.0  # unstated: neither rewarded nor punished
    return 10.0 * min(1.0, max(0.0, math.log2(b) / math.log2(400)))


def _ctx_score(model: dict) -> float:
    c = context_length(model)
    return 0.0 if c <= 8192 else 10.0 * min(1.0, math.log2(c / 8192) / 5)


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
    return (40.0 + _size_score(model) + _ctx_score(model) + 5.0 * _structured(model) + 5.0 * _reasoning(model)
            + 3.0 * _recent(model, now))


def judge_score(model: dict, now: float, vision_family: str | None) -> float:
    s = (_size_score(model) + _ctx_score(model) + 8.0 * _structured(model) + 8.0 * _reasoning(model)
         + 3.0 * _recent(model, now))
    if vision_family is not None and family(model["id"]) != vision_family:
        s += 10.0
    return s


def free_candidates(catalog: list[dict]) -> dict[str, list[dict]]:
    """FREE models usable per role (unscored): vision needs image input; both need text output and context."""
    free = [m for m in catalog if isinstance(m, dict) and is_free(m) and context_length(m) >= MIN_CONTEXT
            and "text" in (modalities(m)[1] or {"text"})]
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
            "image": "image" in ins, "params_b": params_b(m), "structured": _structured(m),
            "reasoning": _reasoning(m), "family": family(m["id"])}


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
    # the verifier sees the chart: a vision model other than Agent 1 when one exists, else Agent 1 itself
    sel.verifier = [r for r in sel.vision if r["id"] != top_vision] or sel.vision[:1]
    if not sel.vision:
        sel.error = "no FREE vision model in the catalog"
    elif not sel.judge:
        sel.error = "no FREE text model for the judge"
    return sel


__all__ = ["FREE_MODELS_VERSION", "MIN_CONTEXT", "Selection", "family", "free_candidates", "is_free", "judge_score",
           "params_b", "select", "supports_image", "vision_score"]
