"""OpenRouter, mocked: FREE models only, discovered and ranked from the catalog; bounded, deduplicated calls;
a failing model falls back to the next FREE one, never to a paid one; the key never leaves the client."""

from __future__ import annotations

import json

import pytest

from aitrader.llm import free_models as fm
from aitrader.llm.openrouter import OpenRouterConfig

from tests.openrouter_kit import CATALOG, DEBATE, KEY, TRADER, VISION, FakeOpenRouter, client, model, ok


def good(role, body):
    return {"x": 1}


def accept(d):
    return None


MSG = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]


# ── discovery and filtering ─────────────────────────────────────────────

@pytest.mark.parametrize("m,free", [
    (model("a/b:free"), True),
    (model("a/b:free", price="0.000001"), False),                  # any price above zero
    (model("a/b"), False),                                         # $0 without the :free variant suffix
    (model("a/b:free", outs=("audio",)), False),                   # audio output, billed per item
    (model("a/b:free", outs=("text", "image")), False),            # writes images
    (model("a/b:free", desc="Costs $0.08 per song"), False),       # a price in its description
    (model("a/guard:free"), False), (model("a/x-safety:free"), False),
    (model("a/embed-vl:free"), False), (model("a/rerank-1b:free"), False),
    (model("openrouter/auto:free"), False),                         # a router
    ({**model("a/b:free"), "pricing": {"prompt": "0"}}, False),    # completion price missing
    ({**model("a/b:free"), "pricing": {"prompt": "0", "completion": "0", "request": "-1"}}, False),  # variable
    ({**model("a/b:free"), "pricing": None}, False),
])
def test_only_explicit_free_text_models_qualify(m, free):
    assert fm.is_free(m) is free


def test_discovery_ranks_roles_and_never_lists_a_paid_or_unsuitable_model():
    sel = fm.select(CATALOG, now=1_790_000_000)
    ids = {r["id"] for role in (sel.vision, sel.judge, sel.verifier) for r in role}
    assert ids <= {VISION, TRADER, DEBATE} and sel.free_total == 3 and sel.catalog_total == len(CATALOG)
    assert sel.vision[0]["id"] == VISION and all(r["image"] for r in sel.vision)  # Agent 1 must see the chart
    assert sel.judge[0]["id"] == TRADER          # a different model (and family) from Agent 1
    assert sel.verifier[0]["id"] == DEBATE       # a third model for the debate


def test_selection_prefers_measured_capability_then_a_different_family():
    cat = [model("x/small-vision:free", ii=10), model("x/strong-vision:free", ii=35),
           model("x/sibling:free", image=False, ii=30), model("y/other:free", image=False, ii=24)]
    sel = fm.select(cat, now=1_790_000_000)
    assert sel.vision[0]["id"] == "x/strong-vision:free"
    assert sel.judge[0]["id"] == "y/other:free"  # 24 + a different family beats a 30 sibling of Agent 1


def test_with_only_two_models_the_strongest_reasoner_is_reused_for_the_debate():
    sel = fm.select([model("x/v:free", ii=20), model("y/t:free", image=False, ii=25)], now=1_790_000_000)
    assert [r["id"] for r in sel.verifier] == ["y/t:free"]


def test_expiring_soon_is_excluded_and_failures_lower_a_rank():
    soon = model("x/leaving:free", ii=50, expiration_date="2026-10-12")
    sel = fm.select([soon, model("x/v:free", ii=20)], now=1_791_590_400)  # 2026-10-10: 2 days left
    assert [r["id"] for r in sel.vision] == ["x/v:free"]
    early = fm.select([soon, model("x/v:free", ii=20)], now=1_783_000_000)  # 2026-07-02: months left
    assert early.vision[0]["id"] == "x/leaving:free"  # the injected clock decides, not the wall clock
    cat = [model("x/a:free", ii=30), model("x/b:free", ii=25)]
    assert fm.select(cat, penalties={"x/a:free": 1.0}).vision[0]["id"] == "x/b:free"


def test_no_free_model_means_no_model_never_a_paid_fallback():
    sel = fm.select([model("paid/x", price="0.00001", ii=90)], now=1_790_000_000)
    assert sel.vision == [] and sel.judge == [] and sel.error
    fake = FakeOpenRouter(good, catalog=[model("paid/x", price="0.00001", ii=90)])
    res = client(fake).chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.status == "NO_FREE_MODEL" and fake.calls == []


# ── connection, key, configuration ──────────────────────────────────────

def test_the_placeholder_and_an_empty_key_are_not_configured_and_nothing_is_sent():
    for k in ("", "PASTE_MY_KEY_HERE", '"PASTE_MY_KEY_HERE"'):
        cfg = OpenRouterConfig.from_env({"OPENROUTER_API_KEY": k})
        assert not cfg.configured
    fake = FakeOpenRouter(good)
    res = client(fake, key="PASTE_MY_KEY_HERE").chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.status == "NOT_CONFIGURED" and fake.calls == [] and fake.headers == []


def test_the_key_is_sent_only_as_a_bearer_header_and_shown_only_as_its_last_four():
    fake = FakeOpenRouter(good)
    c = client(fake)
    assert c.chat_json("vision", MSG, accept, dedupe_key="k").ok
    assert any(h.get("Authorization") == f"Bearer {KEY}" for h in fake.headers)
    pub, health = c.config.public(), c.health()
    blob = json.dumps([pub, health, c.last, c.selection(), repr(c.config)], default=str)
    assert KEY not in blob and KEY[:-4] not in blob and pub["key_hint"] == "…" + KEY[-4:]
    assert "Bearer" not in json.dumps(c.last)


def test_connection_check_reads_the_free_tier_and_caps_the_daily_budget():
    fake = FakeOpenRouter(good, free_tier=True)
    c = client(fake, daily_budget=900)
    info = c.check_key(force=True)
    assert info["ok"] and info["is_free_tier"] is True and c.daily_budget == 48  # 50 a day, less a margin
    fake2 = FakeOpenRouter(good, free_tier=False)
    c2 = client(fake2, daily_budget=900)
    c2.check_key(force=True)
    assert c2.daily_budget == 900


def test_a_rejected_key_is_reported_and_not_retried():
    fake = FakeOpenRouter(lambda r, b: (401, {}, {"error": {"message": "No auth credentials found"}}))
    res = client(fake).chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.status == "KEY_REJECTED" and len(fake.calls) == 1


def test_paid_usage_on_the_key_stops_every_further_request():
    fake = FakeOpenRouter(good, usage=0.0)
    now = [1_790_000_000.0]
    c = client(fake, clock=lambda: now[0])
    assert c.chat_json("vision", MSG, accept, dedupe_key="a").ok
    fake.usage = 0.02  # something spent credit
    now[0] += 3600
    res = c.chat_json("vision", MSG, accept, dedupe_key="b")
    assert res.status == "PAID_USAGE" and len(fake.calls) == 1 and c.health()["status"] == "PAID_USAGE_STOPPED"


# ── bounded calls, fallback, rate limits ────────────────────────────────

def test_an_unavailable_model_falls_back_to_the_next_free_one():
    def reply(role, body):
        if body["model"] == VISION:
            return 404, {}, {"error": {"message": "No endpoints found for seer/vision-a:free"}}
        return {"x": 1}
    fake = FakeOpenRouter(reply)
    c = client(fake)
    res = c.chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.ok and res.model == DEBATE and [x["model"] for x in fake.calls] == [VISION, DEBATE]
    assert VISION in c.selection()["cooldown"]  # rests, then is used again later


def test_rate_limit_honours_retry_after_and_is_bounded():
    waits = []
    fake = FakeOpenRouter(lambda r, b: (429, {"Retry-After": "7"}, {"error": {"message": "Rate limit exceeded"}}))
    c = client(fake, max_retries=2)
    c.sleep = waits.append
    res = c.chat_json("vision", MSG, accept, dedupe_key="k", max_models=1)
    assert res.status == "RATE_LIMITED" and len(fake.calls) == 3 and waits == [7.0, 7.0]


def test_a_spent_free_daily_quota_stops_all_calls_until_the_next_utc_day():
    fake = FakeOpenRouter(lambda r, b: (429, {}, {"error": {"message": "Rate limit exceeded: free-models-per-day"}}))
    now = [1_790_000_000.0]
    c = client(fake, clock=lambda: now[0])
    assert c.chat_json("vision", MSG, accept, dedupe_key="a").status == "DAILY_QUOTA"
    n = len(fake.calls)
    assert c.chat_json("judge", MSG, accept, dedupe_key="b").status == "DAILY_QUOTA" and len(fake.calls) == n
    assert c.health()["status"] == "DAILY_QUOTA_SPENT"


def test_timeouts_are_retried_with_backoff_then_stop_at_the_deadline():
    now = [1_790_000_000.0]

    def slow(role, body):
        now[0] += 100  # each attempt takes 100 s of the clock
        raise TimeoutError("timed out")
    fake = FakeOpenRouter(slow)
    c = client(fake, clock=lambda: now[0], max_retries=5)
    res = c.chat_json("vision", MSG, accept, dedupe_key="k", deadline_s=250)
    assert res.status == "TIMEOUT" and 1 <= len(fake.calls) <= 3


def test_malformed_json_is_invalid_and_never_retried_or_repaired():
    fake = FakeOpenRouter(lambda r, b: "I think BUY, maybe")
    res = client(fake).chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.status.startswith("INVALID") and len(fake.calls) == 1 and not res.ok


def test_a_reply_from_another_model_or_with_a_cost_is_discarded_and_that_model_excluded():
    fake = FakeOpenRouter(lambda r, b: ok('{"x": 1}', "paid/genius"))
    c = client(fake)
    assert c.chat_json("vision", MSG, accept, dedupe_key="k").status == "WRONG_MODEL"
    assert VISION in c.selection()["excluded"]
    fake2 = FakeOpenRouter(lambda r, b: ok('{"x": 1}', b["model"], cost=0.0004))
    c2 = client(fake2)
    assert c2.chat_json("vision", MSG, accept, dedupe_key="k").status == "NOT_FREE"
    assert VISION in c2.selection()["excluded"]


def test_an_identical_request_is_answered_once_duplicate_protection():
    fake = FakeOpenRouter(good)
    c = client(fake)
    a = c.chat_json("vision", MSG, accept, dedupe_key="EURUSD|t")
    b = c.chat_json("vision", MSG, accept, dedupe_key="EURUSD|t")
    assert a.ok and b.ok and b.cached and len(fake.calls) == 1 and a.request_id == b.request_id


def test_every_request_has_its_own_request_id_and_the_daily_budget_is_enforced():
    fake = FakeOpenRouter(good)
    c = client(fake, daily_budget=2)
    ids = [c.chat_json("vision", MSG, accept, dedupe_key=str(i)).request_id for i in range(3)]
    assert len(fake.calls) == 2 and len(set(ids)) == 3
    assert c.chat_json("vision", MSG, accept, dedupe_key="x").status == "BUDGET"


def test_avoid_keeps_the_second_trader_off_the_first_traders_model_and_soft_avoid_reuses():
    fake = FakeOpenRouter(good)
    c = client(fake)
    assert c.chat_json("judge", MSG, accept, dedupe_key="k", avoid=(TRADER,)).model != TRADER
    only = FakeOpenRouter(good, catalog=[model("x/v:free", ii=20), model("y/t:free", image=False, ii=25)])
    c2 = client(only)
    assert c2.chat_json("verifier", MSG, accept, dedupe_key="k", avoid=("x/v:free", "y/t:free")).status == "NO_FREE_MODEL"
    assert c2.chat_json("verifier", MSG, accept, dedupe_key="k2", avoid=("x/v:free", "y/t:free"), avoid_soft=True).ok


def test_the_image_goes_only_to_a_model_that_can_read_it():
    fake = FakeOpenRouter(good)
    c = client(fake)
    msg = [{"role": "system", "content": "s"},
           {"role": "user", "content": [{"type": "text", "text": "{}"},
                                        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAA"}}]}]
    c.chat_json("vision", msg, accept, dedupe_key="v")
    c.chat_json("judge", msg, accept, dedupe_key="j")
    sent = {x["model"]: x["body"]["messages"][1]["content"] for x in fake.calls}
    assert isinstance(sent[VISION], list) and any(p["type"] == "image_url" for p in sent[VISION])
    assert sent[TRADER] == "{}"  # a text model gets the text alone


# ── errors a new key commonly meets ─────────────────────────────────────

def test_an_account_privacy_setting_that_blocks_free_models_is_named_and_not_blamed_on_a_model():
    msg = "No endpoints found matching your data policy (Free model publication). Configure: https://openrouter.ai/settings/privacy"
    fake = FakeOpenRouter(lambda r, b: (404, {}, {"error": {"message": msg}}))
    c = client(fake)
    res = c.chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.status == "DATA_POLICY" and "settings/privacy" in res.error
    assert len(fake.calls) == 1  # every free model would answer the same: no fallback round, nothing rested
    assert c.selection()["cooldown"] == {} and c.health()["status"] == "DATA_POLICY_BLOCKED"


def test_a_reply_cut_at_max_tokens_is_named_as_such():
    fake = FakeOpenRouter(lambda r, b: (200, {}, {"id": "g", "model": b["model"], "usage": {"cost": 0},
                                                  "choices": [{"finish_reason": "length",
                                                               "message": {"content": "", "reasoning": "thinking..."}}]}))
    res = client(fake).chat_json("vision", MSG, accept, dedupe_key="k")
    assert res.status.startswith("INVALID") and "max_tokens" in res.status


def test_the_key_check_falls_back_to_the_older_path():
    seen = []

    class Old(FakeOpenRouter):
        def __call__(self, method, url, headers, body, timeout):
            seen.append(url.rsplit("/api/v1", 1)[-1])
            if url.endswith("/api/v1/key"):
                return 404, {}, {"error": {"message": "Not Found"}}
            if url.endswith("/auth/key"):
                return 200, {}, {"data": {"usage": 0, "is_free_tier": True}}
            return super().__call__(method, url, headers, body, timeout)

    c = client(Old(good))
    assert c.check_key(force=True)["is_free_tier"] is True and seen == ["/key", "/auth/key"]
