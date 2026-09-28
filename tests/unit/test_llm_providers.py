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
