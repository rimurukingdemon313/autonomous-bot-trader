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
    assert h["bad"]["failed"] == 3 and h["bad"]["ok"] == 0 and "HTTP 404" in h["bad"]["last_error"]
    assert h["bad"]["last_error_model"] == "bad:no-such-model" and h["good"]["ok"] == 3
    assert "SECRET" not in str(h)
