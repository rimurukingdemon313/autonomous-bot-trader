"""Several providers, one after another: failover, per-provider budgets, and keys that never leak."""

from __future__ import annotations

import json
import urllib.error

from aitrader.llm.provider import KNOWN_PROVIDERS, LLMClient, LLMConfig
from aitrader.observability import log_event

ENV = {"AI_PROVIDERS": "openrouter,groq,gemini,xai,bytez",
       "AI_OPENROUTER_API_KEY": "or-secret-key-1", "AI_OPENROUTER_MODEL": "some/model",
       "AI_GROQ_API_KEY": "gq-secret-key-2", "AI_GROQ_MODEL": "llama-x", "AI_GROQ_DAILY_BUDGET": "1",
       "AI_GEMINI_API_KEY": "gm-secret-key-3", "AI_GEMINI_MODEL": "gemini-flash",
       "AI_XAI_API_KEY": "xa-secret-key-4", "AI_XAI_MODEL": "grok-x",
       "AI_BYTEZ_API_KEY": "bz-secret-key-5", "AI_BYTEZ_MODEL": "bytez/model"}
OK = json.dumps({"ok": True})


def ok_validate(d):
    return None if d.get("ok") is True else "not ok"


def http_error(url, code):
    return urllib.error.HTTPError(url, code, "err", {}, None)


def router(behaviour, calls):
    def t(url, headers, body, timeout):
        host = url.split("/")[2]
        calls.append((host, headers.get("Authorization"), "response_format" in body))
        b = behaviour.get(host, OK)
        if isinstance(b, int):
            raise http_error(url, b)
        return {"choices": [{"message": {"content": b(body) if callable(b) else b}}]}
    return t


def test_known_providers_need_only_a_key_and_a_model_and_the_order_is_kept():
    cfg = LLMConfig.from_env(ENV)
    eps = cfg.endpoints()
    assert [e.name for e in eps] == ["openrouter", "groq", "gemini", "xai", "bytez"]
    assert eps[2].base_url == KNOWN_PROVIDERS["gemini"] and eps[3].base_url == "https://api.x.ai/v1"
    assert cfg.enabled
    shown = json.dumps(cfg.public())
    assert "secret-key" not in shown and '"key_configured": true' in shown


def test_when_a_provider_fails_the_next_one_answers():
    calls = []
    cfg = LLMConfig.from_env(ENV)
    client = LLMClient(cfg, router({"openrouter.ai": 429, "api.groq.com": "not json"}, calls))
    res = client.complete_json("trader", "s", {}, ok_validate)
    assert res.ok and res.model == "gemini:gemini-flash"
    hosts = [c[0] for c in calls]
    assert hosts[:2] == ["openrouter.ai", "openrouter.ai"]  # one retry on 429, then move on
    assert "api.groq.com" in hosts and hosts[-1] == "generativelanguage.googleapis.com"
    assert all(c[1] and c[1].startswith("Bearer ") for c in calls)  # each provider gets ITS key
    assert {c[1] for c in calls if c[0] == "api.groq.com"} == {"Bearer gq-secret-key-2"}


def test_a_provider_whose_free_quota_is_spent_is_skipped():
    calls = []
    env = {**ENV, "AI_PROVIDERS": "groq,gemini"}
    client = LLMClient(LLMConfig.from_env(env), router({}, calls))
    assert client.complete_json("a", "s", {"n": 1}, ok_validate).model == "groq:llama-x"
    assert client.complete_json("a", "s", {"n": 2}, ok_validate).model == "gemini:gemini-flash"  # groq budget = 1
    assert client.health()["calls_today_by_provider"] == {"groq": 1, "gemini": 1}


def test_a_provider_that_rejects_json_mode_is_asked_again_without_it():
    calls = []

    def t(url, headers, body, timeout):
        calls.append("response_format" in body)
        if "response_format" in body:
            raise http_error(url, 400)
        return {"choices": [{"message": {"content": OK}}]}

    client = LLMClient(LLMConfig.from_env({**ENV, "AI_PROVIDERS": "bytez"}), t)
    assert client.complete_json("a", "s", {}, ok_validate).ok and calls == [True, False]


def test_the_overall_budget_stops_every_provider():
    calls = []
    env = {**ENV, "AI_DAILY_CALL_BUDGET": "1"}
    client = LLMClient(LLMConfig.from_env(env), router({"openrouter.ai": 500}, calls))
    res = client.complete_json("a", "s", {}, ok_validate)
    assert not res.ok and len(calls) == 1  # the one allowed call was spent; nobody else is called


def test_every_provider_key_is_redacted_from_logs(monkeypatch, capsys):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    log_event("TEST", "provider said: bad key gm-secret-key-3 and or-secret-key-1")
    out = capsys.readouterr().out
    assert "gm-secret-key-3" not in out and "or-secret-key-1" not in out


def test_each_providers_failures_are_counted_and_the_last_reason_kept_without_the_key():
    import urllib.error

    from aitrader.llm.provider import Endpoint, LLMClient, LLMConfig

    def transport(url, headers, body, timeout):
        if "bad.test" in url:
            raise urllib.error.HTTPError(url, 404, "model not found", {}, None)
        return {"choices": [{"message": {"content": '{"x": 1}'}}]}

    cfg = LLMConfig(providers=(Endpoint("bad", "https://bad.test/v1", "sk-SECRET-123", "no-such-model"),
                               Endpoint("good", "https://good.test/v1", "k2", "m")))
    c = LLMClient(cfg, transport)
    for _ in range(3):
        assert c.complete_json("a", "s", {}, lambda d: None).ok  # the good provider answers
    h = c.health()["by_provider"]
    # asked once: a model the provider does not have then rests instead of failing every call
    assert h["bad"]["failed"] == 1 and h["bad"]["ok"] == 0 and "HTTP 404" in h["bad"]["last_error"]
    assert h["bad"]["last_error_model"] == "bad:no-such-model" and h["good"]["ok"] == 3
    assert "SECRET" not in str(h)


def test_every_request_names_itself_so_a_cloudflare_front_does_not_refuse_it():
    """Groq answered 403 (Cloudflare 1010) to every call: Python's default User-Agent is refused
    before the key is read. Each request carries its own."""
    calls = []

    def t(url, headers, body, timeout):
        calls.append(headers)
        return {"choices": [{"message": {"content": OK}}]}

    LLMClient(LLMConfig.from_env(ENV), t).complete_json("trader", "s", {}, ok_validate)
    ua = calls[0].get("User-Agent", "")
    assert ua and "urllib" not in ua.lower()


def test_the_providers_own_reason_is_shown_without_the_key():
    """"HTTP 404" alone cannot tell a wrong model name from a wrong URL; the provider's message can."""
    import io

    from aitrader.llm.provider import Endpoint

    def body(msg):
        return io.BytesIO(json.dumps({"error": {"message": msg, "code": 404}}).encode())

    def transport(url, headers, b, timeout):
        if "bad.test" in url:
            raise urllib.error.HTTPError(url, 404, "nf", {}, body(
                "No endpoints found for some/model:free. key sk-SECRET-123 Bearer abcdefghijklmnopqrstuvwxyz0123"))
        if "raw.test" in url:
            raise urllib.error.HTTPError(url, 403, "f", {}, io.BytesIO(b"error code: 1010"))
        return {"choices": [{"message": {"content": OK}}]}

    cfg = LLMConfig(providers=(Endpoint("bad", "https://bad.test/v1", "sk-SECRET-123", "some/model:free"),
                               Endpoint("raw", "https://raw.test/v1", "k", "m"),
                               Endpoint("good", "https://good.test/v1", "k2", "m")))
    c = LLMClient(cfg, transport)
    assert c.complete_json("a", "s", {}, ok_validate).ok
    h = c.health()["by_provider"]
    assert "HTTP 404" in h["bad"]["last_error"] and "No endpoints found for some/model:free" in h["bad"]["last_error"]
    assert "SECRET" not in str(h) and "abcdefghijklmnop" not in str(h)
    assert h["raw"]["last_error"].endswith("HTTP 403 error code: 1010")


def _clocked(behaviour):
    """A client over two providers whose first model answers per `behaviour(call_no)`."""
    from aitrader.llm.provider import Endpoint

    clock = {"t": 1_700_000_000.0}
    calls = []

    def transport(url, headers, b, timeout):
        calls.append((url.split("/")[2], b["model"]))
        if "a.test" in url and b["model"] == "big":
            code = behaviour(len([c for c in calls if c[1] == "big"]))
            if code:
                raise urllib.error.HTTPError(url, code, "x", {}, None)
        return {"choices": [{"message": {"content": OK}}]}

    cfg = LLMConfig(providers=(Endpoint("a", "https://a.test/v1", "k1", "big", ("small",)),
                               Endpoint("b", "https://b.test/v1", "k2", "m")))
    return LLMClient(cfg, transport, clock=lambda: clock["t"]), clock, calls


def test_a_spent_quota_is_not_asked_again_every_minute():
    """Groq's free tier is counted in tokens per day; once it says 429 the model was asked again
    every minute all day (366 failures). It now rests, the next model answers, and nothing is spent."""
    c, clock, calls = _clocked(lambda n: 429)
    assert c.complete_json("a", "s", {}, ok_validate).model == "a:small"
    asked = len([x for x in calls if x[1] == "big"])  # the refusal, and its one retry
    for _ in range(8):  # eight more minutes
        clock["t"] += 60
        assert c.complete_json("a", "s", {}, ok_validate).ok
    assert len([x for x in calls if x[1] == "big"]) == asked  # not asked while resting
    assert c.health()["by_provider"]["a"]["resting"] == {"a:big": 2}
    clock["t"] += 3 * 60  # rest over: asked once more; a second refusal rests twice as long
    c.complete_json("a", "s", {}, ok_validate)
    assert len([x for x in calls if x[1] == "big"]) > asked
    assert c.health()["by_provider"]["a"]["resting"]["a:big"] == 20


def test_a_model_name_the_provider_does_not_have_rests_for_hours_and_a_success_clears_it():
    state = {"code": 404}
    c, clock, calls = _clocked(lambda n: state["code"])
    c.complete_json("a", "s", {}, ok_validate)
    assert c.health()["by_provider"]["a"]["resting"] == {"a:big": 360}
    errs = c.health()["by_provider"]["a"]["errors"]
    assert "a:big" in errs and "HTTP 404" in errs["a:big"]  # each model's own failure is kept
    clock["t"] += 6 * 3600
    state["code"] = None
    assert c.complete_json("a", "s", {}, ok_validate).model == "a:big"
    h = c.health()["by_provider"]["a"]
    assert h["resting"] == {} and "a:big" not in h["errors"]


def test_an_ordinary_server_error_does_not_make_a_model_rest():
    c, clock, calls = _clocked(lambda n: 500)
    c.complete_json("a", "s", {}, ok_validate)
    assert c.health()["by_provider"]["a"]["resting"] == {}


def test_a_per_minute_limit_rests_as_long_as_the_provider_says_not_the_blind_doubling():
    """Groq's per-minute token limit says "Please try again in 14.2s" far into a long message; the
    model was resting 19 minutes. It now rests what the provider asked for, at least a minute."""
    import io

    from aitrader.llm.provider import Endpoint, retry_after_s

    long = ("Rate limit reached for model `openai/gpt-oss-120b` in organization `org_x` service tier `on_demand` "
            "on tokens per minute (TPM): Limit 8000, Used 6500, Requested 3400. Please try again in 14.2s. "
            "Need more tokens? Upgrade to Dev Tier today.")
    clock = {"t": 1_700_000_000.0}

    def transport(url, headers, b, timeout):
        if "a.test" in url:
            raise urllib.error.HTTPError(url, 429, "x", {}, io.BytesIO(json.dumps({"error": {"message": long}}).encode()))
        return {"choices": [{"message": {"content": OK}}]}

    c = LLMClient(LLMConfig(providers=(Endpoint("a", "https://a.test/v1", "k", "big"),
                                       Endpoint("b", "https://b.test/v1", "k", "m"))), transport, clock=lambda: clock["t"])
    c.complete_json("x", "s", {}, ok_validate)
    assert c.health()["by_provider"]["a"]["resting"] == {"a:big": 1}
    e = urllib.error.HTTPError("u", 429, "x", {}, None)
    assert retry_after_s(e, "please try again in 2m59.5s") == 179.5
    assert retry_after_s(e, "Please try again in 1h2m3s") == 3723
    assert retry_after_s(e, "try again in 250ms") == 0.25
    assert retry_after_s(e, "quota exceeded") is None
    assert retry_after_s(urllib.error.HTTPError("u", 429, "x", {"Retry-After": "30"}, None), "") == 30


def test_a_provider_can_have_its_own_reply_budget():
    """Groq's per-minute limit counts the reply budget in the request; a smaller one for that provider
    keeps the request under it, without shrinking every other provider's."""
    sent = []

    def t(url, headers, body, timeout):
        sent.append((url.split("/")[2], body["max_tokens"]))
        return {"choices": [{"message": {"content": OK}}]}

    env = {**ENV, "AI_OPENROUTER_MAX_TOKENS": "900", "AI_MAX_TOKENS": "1500"}
    c = LLMClient(LLMConfig.from_env(env), t)
    c.complete_json("trader", "s", {}, ok_validate, only="openrouter")
    c.complete_json("trader", "s", {}, ok_validate, only="gemini")
    assert sent == [("openrouter.ai", 900), ("generativelanguage.googleapis.com", 1500)]


# ── request size: a provider with a small per-request limit gets a shortened view, not nothing ──

import io  # noqa: E402

from aitrader.agents.llm_trader import compact_packet  # noqa: E402

GROQ = {"AI_PROVIDERS": "groq", "AI_GROQ_API_KEY": "gq-key", "AI_GROQ_MODEL": "gpt-oss", "AI_GROQ_MAX_TOKENS": "800"}
BIG = {"instrument": "EURUSD", "decision_time": "2026-09-29T11:00:00+00:00",
       "quote": {"bid": 1.1, "ask": 1.1001}, "account": {"equity": 20000},
       "discussion": [{"member": "gemini", "thesis": "x" * 900}],
       "strategy_desk": {"best": "trend", "table": [[i, i * 0.1] for i in range(3000)]},
       "history": {"n": 5, "rows": list(range(3000))}, "market_map": {"levels": list(range(2000)), "bias": "up"},
       "timeframes": {"M1": {"bars": list(range(400))}, "H1": {"bars": list(range(50))}}}


def sent_packets(calls_body):
    return [json.loads(b["messages"][1]["content"]) for b in calls_body]


def capture(reply=OK, fail_first=None):
    bodies = []

    def t(url, headers, body, timeout):
        bodies.append(body)
        if fail_first and len(bodies) == 1:
            raise urllib.error.HTTPError(url, 413, "too large", {}, io.BytesIO(fail_first.encode()))
        return {"choices": [{"message": {"content": reply}}]}
    return t, bodies


def test_groq_gets_a_shortened_packet_that_fits_instead_of_a_413():
    t, bodies = capture()
    client = LLMClient(LLMConfig.from_env(GROQ), t)
    assert LLMConfig.from_env(GROQ).endpoints()[0].max_request_tokens == 7000  # the groq default
    res = client.complete_json("room:groq", "system", BIG, ok_validate, shrink=compact_packet)
    assert res.ok and len(bodies) == 1
    sent = sent_packets(bodies)[0]
    assert "shortened view" in sent["packet_note"]
    assert sent["quote"] == BIG["quote"] and sent["account"] == BIG["account"]  # kept, unaltered
    assert len(json.dumps(sent)) / 3 + 800 <= 7000


def test_without_a_way_to_shorten_an_oversized_request_is_not_sent():
    t, bodies = capture()
    client = LLMClient(LLMConfig.from_env(GROQ), t)
    res = client.complete_json("room:groq", "system", BIG, ok_validate)
    assert not res.ok and res.status == "TOO_LARGE" and bodies == []


def test_a_413_that_states_its_sizes_is_answered_with_a_shorter_view_at_once():
    env = GROQ | {"AI_GROQ_MAX_REQUEST_TOKENS": "100000"}  # configured too high: only the 413 tells the truth
    msg = json.dumps({"error": {"message": "Request too large for model `gpt-oss` on tokens per minute (TPM): "
                                           "Limit 8000, Requested 30000, please reduce your message size"}})
    t, bodies = capture(fail_first=msg)
    client = LLMClient(LLMConfig.from_env(env), t)
    res = client.complete_json("room:groq", "system", BIG, ok_validate, shrink=compact_packet)
    assert res.ok and len(bodies) == 2  # the same model, asked again shortened: no 10-minute rest
    assert "packet_note" not in sent_packets(bodies)[0] and "packet_note" in sent_packets(bodies)[1]
    assert client._resting("groq:gpt-oss") is None
    t2, bodies2 = capture()
    client._transport = t2
    assert client.complete_json("room:groq", "system2", BIG, ok_validate, shrink=compact_packet).ok
    assert "packet_note" in sent_packets(bodies2)[0]  # the learned limit applies from the first try next time


def test_providers_without_a_limit_still_get_the_full_packet():
    t, bodies = capture()
    env = {"AI_PROVIDERS": "gemini", "AI_GEMINI_API_KEY": "k", "AI_GEMINI_MODEL": "flash"}
    assert LLMClient(LLMConfig.from_env(env), t).complete_json("x", "s", BIG, ok_validate, shrink=compact_packet).ok
    assert sent_packets(bodies)[0] == json.loads(json.dumps(BIG))


def test_shortening_only_cuts_and_gets_shorter_level_by_level():
    sizes = [len(json.dumps(compact_packet(BIG, lv))) for lv in (1, 2, 3)]
    assert len(json.dumps(BIG)) > sizes[0] >= sizes[1] >= sizes[2]
    for lv in (1, 2, 3):
        c = compact_packet(BIG, lv)
        assert c["instrument"] == "EURUSD" and c["quote"] == BIG["quote"] and c["discussion"]
    assert compact_packet(BIG, 1)["strategy_desk"] == {"best": "trend"}  # headline kept, table cut
    assert "strategy_desk" not in compact_packet(BIG, 3)
