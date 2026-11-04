"""The owner's funded use of paid models (docs/DUAL_AI.md, "The paid trial" and "The senior trader").

On 2026-10-23 the owner put $10 on the OpenRouter key: "you can use it for the models, but make it last a week;
pick something cheap, but not stupid". This module declares that test. Nothing else may make the client spend.

- WHO. One paid model per declared seat. A trader's seat (Trader 1, Trader 2) asks its paid model first, the FREE
  models after it. The senior's seat (1.3.0) has no FREE model at all (PAID_ONLY_ROLES): its paid model or nobody.
  The debate (shadow measurement only) is never paid.
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

#: 1.1.0 (live, 2026-10-26): a price for a feature the client never uses (web search) no longer keeps a model out.
#:        Trader 2's anthropic/claude-haiku-5.5 lists web_search at $0.01 a search; the seat ran on the free models
#:        all Monday morning.
#: 1.2.0 (live, the same day): the next price it lists, input_cache_write_1h, kept it out again; a list of the prices
#:        never used was the wrong way round. Only the prices a request from this client can be charged are checked
#:        (CHARGED_*). Every other price is for a feature no request asks for, such as web search, prompt-cache writes,
#:        or image or audio output, so it neither keeps a model out nor counts in a call's reserve. What a reply really
#:        cost is still checked on every reply (max_call_usd) and against the key's own spend.
#: 1.3.0 (owner, 2026-11-02: "use stronger models if you want, but please make them know"): a third paid seat, the
#:        SENIOR TRADER (dual-ai 1.18.0), and the only one with no FREE model (PAID_ONLY_ROLES). The first trial's
#:        declaration stays as TRIAL_2026_10_26; PAID_TRIAL is now the senior's.
#: 1.4.0 (owner, 2026-11-04: "change everything if you must; the most important thing is a profit; you can make the
#:        budget $100, it is there"): the owner's cap on the key is $100 (OWNER_CAP_USD; it was $10). The senior's
#:        funded period is SENIOR_2026_11B: $95 in all and $7.50 a day, enough for the senior to judge every H1
#:        agreement the desk makes, below the floor in shadow too (dual-ai 1.20.0, research/preregistrations/CONF-2.md).
#:        The same window and baseline as SENIOR_2026_11, so no decision is ever left without its senior. What the key
#:        holds still bounds every call: a 402 ends the trial, and the desk then takes no trade a senior must review.
PAID_TRIAL_VERSION = "paid-trial-1.4.0"
#: the seats a paid model may take: the two traders and the senior. The debate is never paid.
PAID_ROLES = ("vision", "judge", "senior")
#: the seats with no FREE model: when the paid one cannot be asked, nobody is (dual-ai 1.18.0: then no trade is taken)
PAID_ONLY_ROLES = ("senior",)
#: a call is reserved at this many prompt tokens (the traders' prompts measured 8k-26k, chart included) plus its
#: max_tokens of output, so a cap is never crossed by the call that reaches it
PROMPT_TOKENS_RESERVE = 30_000
#: the prices a request from this client can be charged. Per token in: the prompt, and a provider's own automatic
#: prompt-cache read (never dearer than the prompt). Per token out: the completion and its reasoning. Per item: the
#: request, and each image sent (the chart). Nothing else is ever asked for: no web search (no `plugins`, no
#: `web_search_options`, no ":online" model), no cache_control breakpoints (so no cache writes), no image or audio out.
CHARGED_PER_IN_TOKEN = frozenset({"prompt", "input_cache_read"})
CHARGED_PER_OUT_TOKEN = frozenset({"completion", "internal_reasoning"})
CHARGED_PER_ITEM = frozenset({"request", "image"})
CHARGED = CHARGED_PER_IN_TOKEN | CHARGED_PER_OUT_TOKEN | CHARGED_PER_ITEM
#: the key's spend may run ahead of what this process's paid replies reported by at most this before every request
#: stops (a reply lost to a timeout is still billed; it is reserved at its most until the next key read)
UNACCOUNTED_TOLERANCE_USD = 0.05
#: the most the owner allows the key to spend on paid models, in all (owner, 2026-11-04; $10 before)
OWNER_CAP_USD = 100.0


@dataclass(frozen=True)
class PaidModel:
    id: str
    max_in_per_m: float     # USD per million prompt tokens, at most
    max_out_per_m: float    # USD per million completion tokens, at most
    max_item_usd: float = 0.0  # each per-item price a request can be charged (the request, an image), at most

    def priced_as_declared(self, catalog_model: dict | None) -> str | None:
        """None when the catalog lists every price a request can be charged at or below the declared ones; else why."""
        if not isinstance(catalog_model, dict):
            return f"{self.id} is not in the catalog"
        pricing = catalog_model.get("pricing")
        if not isinstance(pricing, dict) or "prompt" not in pricing or "completion" not in pricing:
            return f"{self.id} lists no prompt and completion price"
        for k, v in pricing.items():
            if k not in CHARGED:
                continue  # a feature no request from this client asks for: it cannot be charged
            try:
                p = float(v)
            except (TypeError, ValueError):
                return f"{self.id} lists an unreadable {k} price {v!r}"
            if p < 0 or p != p:
                return f"{self.id} lists a variable {k} price {v!r}"
            limit = (self.max_in_per_m / 1e6 if k in CHARGED_PER_IN_TOKEN else
                     self.max_out_per_m / 1e6 if k in CHARGED_PER_OUT_TOKEN else self.max_item_usd)
            if p > limit + 1e-15:
                return f"{self.id} lists {k} at {p:g}, above the declared {limit:g}"
        return None


def call_reserve(catalog_model: dict, max_tokens: int) -> float:
    """The most one call can cost, in USD: PROMPT_TOKENS_RESERVE tokens in and max_tokens out, each at the dearest
    price it can be charged, and every per-item price a request can be charged."""
    pricing = catalog_model.get("pricing") or {}

    def f(k):
        try:
            return max(0.0, float(pricing.get(k) or 0.0))
        except (TypeError, ValueError):
            return 0.0
    return (PROMPT_TOKENS_RESERVE * max(f(k) for k in CHARGED_PER_IN_TOKEN)
            + max_tokens * max(f(k) for k in CHARGED_PER_OUT_TOKEN) + sum(f(k) for k in CHARGED_PER_ITEM))


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
            assert 0 < self.daily_usd <= self.total_usd <= OWNER_CAP_USD, "caps: 0 < daily <= total <= the owner's cap"
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

#: The owner's first funded week, declared 2026-10-23 (history: its window closed as Saturday 31 October began; it
#: spent $0.958). Chosen on the live catalog that day (the Artificial Analysis
#: intelligence index OpenRouter lists, and one real trading question each: dai-check results, c0bfa28): the two
#: strongest cheap models that read the chart, from two different labs, each several times as able as the free
#: models that traded (nemotron-3-ultra 22.9, inkling-small 25.7):
#:   Trader 1 xiaomi/mimo-v2.6-pro       index 46.3, $0.435 / $0.87 per million tokens, about $0.007 a call
#:   Trader 2 anthropic/claude-haiku-5.5 index 43.4, $0.10 / $0.50, about $0.002 a call
#: At up to 100 decisions a day that is about $0.90 a day: $1.80 a day and $9 in all are the caps, of the $10.
#: The trading week is Monday 26 to Friday 30 October; the trial ends as Saturday begins.
TRIAL_2026_10_26 = PaidTrial(
    name="paid-trial-2026-10-26",
    models={"vision": PaidModel("xiaomi/mimo-v2.6-pro", max_in_per_m=0.50, max_out_per_m=1.00),
            "judge": PaidModel("anthropic/claude-haiku-5.5", max_in_per_m=0.12, max_out_per_m=0.60)},
    starts="2026-10-23T14:00:00Z", ends="2026-10-31T00:00:00Z",
    total_usd=9.00, daily_usd=1.80, max_call_usd=0.03,
    usage_baseline=0.0,  # everything this key ever spent counts against the $9 (the $0.008 diagnostic included)
)

#: The owner, 2026-11-02: "if you want to use stronger models, that's fine, but please make them know". The strongest
#: model the live catalog lists that reads the chart takes the desk's SENIOR seat (dual-ai 1.18.0). It reviews only the
#: trades both traders agree on at the confidence floor, with everything the desk knows, and can only refuse them.
#: Chosen on the catalog of 2026-11-02 10:48 UTC (dual-ai-check-results 255b36f), on the Artificial Analysis
#: intelligence index OpenRouter lists:
#:   anthropic/claude-opus-5.5   index 58.4, the highest listed; $4 / $20 per million tokens; about $0.17 a review
#: It is an Anthropic model, chosen by a Claude model: on the index, where it is first, and from a third lab, neither
#: trader's. In a trader's seat (about 150 questions a day) it would cost about $27 a day; as the senior it is asked a
#: handful of times a day. Of the owner's $10 the first trial spent $0.958 (usage_baseline): $8.50 in all and $1.50 a
#: day are the caps.
SENIOR_2026_11 = PaidTrial(
    name="senior-2026-11-02",
    models={"senior": PaidModel("anthropic/claude-opus-5.5", max_in_per_m=4.0, max_out_per_m=20.0)},
    starts="2026-11-02T15:00:00Z", ends="2026-12-01T00:00:00Z",
    total_usd=8.50, daily_usd=1.50, max_call_usd=0.40,
    usage_baseline=0.958,
)
#: The owner, 2026-11-04: "you can make the budget $100, it is there; I rely on you". The same senior, now funded to
#: judge every H1 agreement the desk makes: the trade candidates as before, and the agreements below the confidence
#: floor in shadow (dual-ai 1.20.0), so CONF-2 can measure whether its judgement picks the trades that win. A review
#: cost about $0.10 on 2026-11-04 (two for $0.21); about 60 agreements a day is about $6.30. $7.50 a day and $95 in all,
#: of the $100, with what the senior spent since 2 November inside the $95 (the same baseline).
SENIOR_2026_11B = PaidTrial(
    name="senior-2026-11-04",
    models={"senior": PaidModel("anthropic/claude-opus-5.5", max_in_per_m=4.0, max_out_per_m=20.0)},
    starts="2026-11-02T15:00:00Z", ends="2026-12-01T00:00:00Z",
    total_usd=95.0, daily_usd=7.50, max_call_usd=0.40,
    usage_baseline=0.958,
)
#: the funded period declared now: the client's default
PAID_TRIAL = SENIOR_2026_11B


__all__ = ["CHARGED", "NO_TRIAL", "OWNER_CAP_USD", "PAID_ONLY_ROLES", "PAID_ROLES", "PAID_TRIAL", "PAID_TRIAL_VERSION",
           "PROMPT_TOKENS_RESERVE", "SENIOR_2026_11", "SENIOR_2026_11B", "TRIAL_2026_10_26", "UNACCOUNTED_TOLERANCE_USD",
           "PaidModel", "PaidTrial", "call_reserve"]
