"""The owner's one funded test of paid models (docs/DUAL_AI.md, "The paid trial").

On 2026-10-23 the owner put $10 on the OpenRouter key: "you can use it for the models, but make it last a week;
pick something cheap, but not stupid". This module declares that test. Nothing else may make the client spend.

- WHO. One paid model per trading seat (Trader 1, Trader 2) is asked first, and the FREE models stay its
  fallbacks. The debate (shadow measurement only) and Trader 1's numbers fallback stay FREE.
- WHEN. From `starts` to `ends` (UTC). Outside that window the client is FREE ONLY, as before.
- HOW MUCH. At most `total_usd` in all and `daily_usd` per UTC day. Both are read from the key's own spend (GET /key
  `usage` and `usage_daily`), plus what this process has spent since that read, plus the most the next call could
  cost. When either reading is missing, the paid model is not asked: absence of evidence spends nothing.
- AT WHAT PRICE. A paid model is used only while the catalog lists it at or below the prices declared here. A reply
  that costs more than `max_call_usd` is discarded, and it ends the trial for the process.
- STOPS. A 402 (credits spent) or `OPENROUTER_PAID_TRIAL=off` ends it. Spend on the key beyond what this process's
  paid replies account for still stops every request (PAID_USAGE), as it always has.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

#: 1.1.0 (live, 2026-10-26): a price for a feature the client never uses (NEVER_USED: web search) no longer keeps a
#:        model out. Trader 2's anthropic/claude-haiku-5.5 lists web_search at $0.01 a search, charged only when a
#:        search is asked for; the client never asks for one, and the seat ran on the free models all Monday morning.
PAID_TRIAL_VERSION = "paid-trial-1.1.0"
#: the seats a paid model may take: the two traders. The debate and the numbers fallback are never paid.
PAID_ROLES = ("vision", "judge")
#: a call is reserved at this many prompt tokens (the traders' prompts measured 8k-26k, chart included) plus its
#: max_tokens of output, so a cap is never crossed by the call that reaches it
PROMPT_TOKENS_RESERVE = 30_000
#: catalog prices charged per token; every other listed price is charged per item (request, image, web search)
PER_TOKEN = frozenset({"prompt", "completion", "internal_reasoning", "input_cache_read", "input_cache_write",
                       "input_audio", "audio"})
#: catalog prices for features the client never uses, so a call can never be charged them: web search is billed per
#: search only when the request asks for one (a `plugins` / `web_search_options` field, or an ":online" model), and
#: no request this client builds ever does
NEVER_USED = frozenset({"web_search"})
#: the key's spend may run ahead of what this process's paid replies reported by at most this before every request
#: stops (a reply lost to a timeout is still billed; it is reserved at its most until the next key read)
UNACCOUNTED_TOLERANCE_USD = 0.05


@dataclass(frozen=True)
class PaidModel:
    id: str
    max_in_per_m: float     # USD per million prompt tokens, at most
    max_out_per_m: float    # USD per million completion tokens, at most
    max_item_usd: float = 0.0  # every per-item price it lists (request, image, web search), at most

    def priced_as_declared(self, catalog_model: dict | None) -> str | None:
        """None when the catalog lists this model at or below the declared prices; else why it is not."""
        if not isinstance(catalog_model, dict):
            return f"{self.id} is not in the catalog"
        pricing = catalog_model.get("pricing")
        if not isinstance(pricing, dict) or "prompt" not in pricing or "completion" not in pricing:
            return f"{self.id} lists no prompt and completion price"
        for k, v in pricing.items():
            if k in NEVER_USED:
                continue
            try:
                p = float(v)
            except (TypeError, ValueError):
                return f"{self.id} lists an unreadable {k} price {v!r}"
            if p < 0 or p != p:
                return f"{self.id} lists a variable {k} price {v!r}"
            limit = (self.max_in_per_m / 1e6 if k == "prompt" else
                     self.max_out_per_m / 1e6 if k in PER_TOKEN else self.max_item_usd)
            if k in PER_TOKEN and k not in ("prompt", "completion"):
                limit = max(self.max_in_per_m, self.max_out_per_m) / 1e6
            if p > limit + 1e-15:
                return f"{self.id} lists {k} at {p:g}, above the declared {limit:g}"
        return None


def call_reserve(catalog_model: dict, max_tokens: int) -> float:
    """The most one call can cost, in USD: PROMPT_TOKENS_RESERVE prompt tokens, max_tokens out, every item price."""
    pricing = catalog_model.get("pricing") or {}
    f = lambda k: float(pricing.get(k) or 0.0)  # noqa: E731
    items = sum(float(v or 0.0) for k, v in pricing.items() if k not in PER_TOKEN and k not in NEVER_USED)
    return PROMPT_TOKENS_RESERVE * f("prompt") + max_tokens * max(f("completion"), f("internal_reasoning")) + items


@dataclass(frozen=True)
class PaidTrial:
    name: str
    models: dict = field(default_factory=dict)  # role -> PaidModel
    starts: str = ""  # ISO 8601 UTC
    ends: str = ""
    total_usd: float = 0.0
    daily_usd: float = 0.0
    max_call_usd: float = 0.0
    #: the key's `usage` (USD) when the trial began: what it spends is `usage` minus this
    usage_baseline: float = 0.0

    def __post_init__(self) -> None:
        # declared once, checked rather than trusted: a cap that is not a small positive amount is a typo
        assert set(self.models) <= set(PAID_ROLES), f"paid seats are only {PAID_ROLES}"
        assert len({m.id for m in self.models.values()}) == len(self.models), "two seats, two different models"
        if self.models:
            assert 0 < self.daily_usd <= self.total_usd <= 10.0, "caps: 0 < daily <= total <= the owner's $10"
            assert 0 < self.max_call_usd <= self.daily_usd, "one call can never cost more than a day"
            assert self.window()[0] < self.window()[1], "the trial ends after it starts"

    def window(self) -> tuple[float, float]:
        ts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()  # noqa: E731
        return ts(self.starts), ts(self.ends)

    def active(self, t: float) -> bool:
        if not self.models:
            return False
        a, b = self.window()
        return a <= t < b

    def public(self) -> dict:
        return {"name": self.name, "version": PAID_TRIAL_VERSION, "starts": self.starts, "ends": self.ends,
                "total_usd": self.total_usd, "daily_usd": self.daily_usd, "max_call_usd": self.max_call_usd,
                "models": {r: m.id for r, m in self.models.items()}}


#: no trial: FREE ONLY
NO_TRIAL = PaidTrial(name="none")

#: The owner's funded week, declared 2026-10-23. Chosen on the live catalog that day (the Artificial Analysis
#: intelligence index OpenRouter lists, and one real trading question each: dai-check results, c0bfa28): the two
#: strongest cheap models that read the chart, from two different labs, each several times as able as the free
#: models that traded (nemotron-3-ultra 22.9, inkling-small 25.7):
#:   Trader 1 xiaomi/mimo-v2.6-pro       index 46.3, $0.435 / $0.87 per million tokens, about $0.007 a call
#:   Trader 2 anthropic/claude-haiku-5.5 index 43.4, $0.10 / $0.50, about $0.002 a call
#: At up to 100 decisions a day that is about $0.90 a day: $1.80 a day and $9 in all are the caps, of the $10.
#: The trading week is Monday 26 to Friday 30 October; the trial ends as Saturday begins.
PAID_TRIAL = PaidTrial(
    name="paid-trial-2026-10-26",
    models={"vision": PaidModel("xiaomi/mimo-v2.6-pro", max_in_per_m=0.50, max_out_per_m=1.00),
            "judge": PaidModel("anthropic/claude-haiku-5.5", max_in_per_m=0.12, max_out_per_m=0.60)},
    starts="2026-10-23T14:00:00Z", ends="2026-10-31T00:00:00Z",
    total_usd=9.00, daily_usd=1.80, max_call_usd=0.03,
    usage_baseline=0.0,  # everything this key ever spent counts against the $9 (the $0.008 diagnostic included)
)


__all__ = ["NEVER_USED", "NO_TRIAL", "PAID_ROLES", "PAID_TRIAL", "PAID_TRIAL_VERSION", "PROMPT_TOKENS_RESERVE",
           "UNACCOUNTED_TOLERANCE_USD", "PaidModel", "PaidTrial", "call_reserve"]
