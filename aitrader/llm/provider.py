"""Provider-agnostic language-model access, fail-closed.

One protocol: the OpenAI-compatible chat-completions API, which covers most
of the practical options with one client — Google Gemini (its OpenAI-compatible
endpoint), Groq, OpenRouter, Cerebras, Mistral, DeepSeek, and local servers
(Ollama, llama.cpp, vLLM). Configuration comes only from environment
variables; the key is never logged, echoed, or returned.

One provider (the original form):

    AI_PROVIDER        none | openai_compatible          (default none)
    AI_BASE_URL        e.g. https://api.groq.com/openai/v1
    AI_API_KEY         secret; may be empty for a local server
    AI_MODEL           default model for every agent
    AI_MODEL_<AGENT>   per-agent override, e.g. AI_MODEL_ADVERSARY
    AI_FALLBACK_MODELS comma-separated, tried in order after failures

Several providers, each with its own key, tried IN ORDER (when one fails,
is rate-limited, gives an invalid reply or runs out of its own daily
budget, the next one answers):

    AI_PROVIDERS               e.g. openrouter,groq,gemini,xai,bytez
    AI_<NAME>_API_KEY          secret, per provider
    AI_<NAME>_MODEL            the model id at that provider
    AI_<NAME>_BASE_URL         optional for the known names below
    AI_<NAME>_FALLBACK_MODELS  optional, same provider
    AI_<NAME>_DAILY_BUDGET     optional cap for that provider (free tiers)

Common:

    AI_TIMEOUT_S          per-call timeout (default 60)
    AI_DAILY_CALL_BUDGET  hard cap on calls per UTC day, all providers (default 500)
    AI_MAX_TOKENS         per reply (default 1500)

Failure never produces an answer: a timeout, an HTTP error, malformed JSON
or a schema violation returns an LLMResult with ok=False, and the caller
treats that agent's LLM layer as unavailable (NO_TRADE if it is required).
Calls are READS (no side effects), so one retry on 429/5xx is permitted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

PROMPT_VERSION = "prompt-1.0.0"


#: Base URLs of known OpenAI-compatible providers, from their official documentation.
KNOWN_PROVIDERS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
    "xai": "https://api.x.ai/v1",  # Grok
    "grok": "https://api.x.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "bytez": "https://api.bytez.com/models/v2/openai/v1",
}


@dataclass(frozen=True)
class Endpoint:
    name: str
    base_url: str
    api_key: str = field(default="", repr=False)
    model: str = ""
    fallback: tuple[str, ...] = ()
    daily_budget: int | None = None

    @property
    def usable(self) -> bool:
        return bool(self.base_url) and bool(self.model)

    def public(self) -> dict:
        host = re.sub(r"^https?://", "", self.base_url).split("/")[0] if self.base_url else ""
        return {"name": self.name, "host": host, "model": self.model, "fallback": list(self.fallback),
                "key_configured": bool(self.api_key), "daily_budget": self.daily_budget}


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "none"
    base_url: str = ""
    api_key: str = field(default="", repr=False)
    model: str = ""
    per_agent: dict = field(default_factory=dict)
    fallback: tuple[str, ...] = ()
    timeout_s: float = 20.0
    daily_budget: int = 500
    max_tokens: int = 1500  # room for a trader's reasoning; a cut-off reply is rejected, not repaired
    providers: tuple[Endpoint, ...] = ()  # several providers, in order (AI_PROVIDERS)

    def endpoints(self) -> tuple[Endpoint, ...]:
        """Every provider to try, in order. The single-provider form is one endpoint named 'default'."""
        if self.providers:
            return tuple(e for e in self.providers if e.usable)
        if self.provider == "openai_compatible" and self.base_url and self.model:
            return (Endpoint("default", self.base_url, self.api_key, self.model, self.fallback),)
        return ()

    @property
    def enabled(self) -> bool:
        return bool(self.endpoints())

    def model_for(self, agent: str) -> str:
        return self.per_agent.get(agent.upper(), self.model)

    def public(self) -> dict:
        """Safe to display: no key, and the host only."""
        host = re.sub(r"^https?://", "", self.base_url).split("/")[0] if self.base_url else ""
        eps = self.endpoints()
        return {"provider": self.provider if not self.providers else "multi", "enabled": self.enabled,
                "host": host, "model": self.model or (eps[0].model if eps else ""),
                "per_agent": dict(self.per_agent), "fallback": list(self.fallback),
                "key_configured": bool(self.api_key) or any(e.api_key for e in eps),
                "providers": [e.public() for e in eps], "timeout_s": self.timeout_s,
                "daily_budget": self.daily_budget}

    @classmethod
    def from_env(cls, env: dict | None = None) -> "LLMConfig":
        e = os.environ if env is None else env
        per_agent = {k[len("AI_MODEL_"):]: v for k, v in e.items() if k.startswith("AI_MODEL_") and v}
        providers = []
        for name in (n.strip().lower() for n in e.get("AI_PROVIDERS", "").split(",") if n.strip()):
            up = name.upper()
            budget = e.get(f"AI_{up}_DAILY_BUDGET", "").strip()
            providers.append(Endpoint(
                name=name,
                base_url=(e.get(f"AI_{up}_BASE_URL", "").strip() or KNOWN_PROVIDERS.get(name, "")).rstrip("/"),
                api_key=e.get(f"AI_{up}_API_KEY", "").strip(),
                model=e.get(f"AI_{up}_MODEL", "").strip(),
                fallback=tuple(m.strip() for m in e.get(f"AI_{up}_FALLBACK_MODELS", "").split(",") if m.strip()),
                daily_budget=int(budget) if budget else None))
        return cls(
            providers=tuple(providers),
            provider=e.get("AI_PROVIDER", "none").strip().lower(),
            base_url=e.get("AI_BASE_URL", "").strip().rstrip("/"),
            api_key=e.get("AI_API_KEY", "").strip(),
            model=e.get("AI_MODEL", "").strip(),
            per_agent=per_agent,
            fallback=tuple(m.strip() for m in e.get("AI_FALLBACK_MODELS", "").split(",") if m.strip()),
            timeout_s=float(e.get("AI_TIMEOUT_S", "60")),
            daily_budget=int(e.get("AI_DAILY_CALL_BUDGET", "500")),
            max_tokens=int(e.get("AI_MAX_TOKENS", "1500")),
        )


@dataclass
class LLMResult:
    ok: bool
    agent: str
    model: str | None
    status: str  # OK | DISABLED | TIMEOUT | HTTP_ERROR | INVALID_JSON | SCHEMA | BUDGET | ERROR
    data: dict | None = None
    latency_ms: float = 0.0
    tokens: dict | None = None
    error: str | None = None
    cached: bool = False

    def as_dict(self) -> dict:
        return {"ok": self.ok, "agent": self.agent, "model": self.model, "status": self.status,
                "data": self.data, "latency_ms": round(self.latency_ms, 1), "tokens": self.tokens,
                "error": self.error, "cached": self.cached, "prompt_version": PROMPT_VERSION}


Transport = Callable[[str, dict, dict, float], dict]


def _http_transport(url: str, headers: dict, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - https URL from config
        return json.loads(resp.read().decode())


def extract_json(text: str) -> dict | None:
    """The first complete JSON object in `text`, or None. Never repairs content."""
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = [fence.group(1)] if fence else []
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                esc = (ch == "\\") and not esc
                if ch == '"' and not esc:
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:i + 1])
                    break
        start = text.find("{", start + 1) if not candidates else -1
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


class LLMClient:
    def __init__(self, config: LLMConfig, transport: Transport | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self.config = config
        self._transport = transport or _http_transport
        self._clock = clock
        self._lock = threading.Lock()
        self._calls: dict[str, int] = {}
        self._cache: dict[str, LLMResult] = {}
        self._ep_day: dict[tuple[str, str], int] = {}  # (UTC day, provider) -> calls
        self.stats = {"calls": 0, "ok": 0, "failed": 0, "retries": 0, "cache_hits": 0}

    def _day(self) -> str:
        return datetime.fromtimestamp(self._clock(), timezone.utc).strftime("%Y-%m-%d")

    def _budget_ok(self) -> bool:
        with self._lock:
            return self._calls.get(self._day(), 0) < self.config.daily_budget

    def _spend(self) -> None:
        with self._lock:
            d = self._day()
            self._calls = {d: self._calls.get(d, 0) + 1}

    def complete_json(self, agent: str, system: str, packet: dict, validate: Callable[[dict], str | None],
                      *, cache_key: str | None = None) -> LLMResult:
        """Ask for a JSON object; return it only if `validate` returns None."""
        cfg = self.config
        if not cfg.enabled:
            return LLMResult(False, agent, None, "DISABLED", error="AI_PROVIDER is not configured")
        user = json.dumps(packet, sort_keys=True, separators=(",", ":"), default=str)
        key = hashlib.sha256(f"{agent}|{cfg.model_for(agent)}|{system}|{user}|{cache_key}".encode()).hexdigest()
        if cache_key is not None and key in self._cache:
            self.stats["cache_hits"] += 1
            hit = self._cache[key]
            return LLMResult(hit.ok, hit.agent, hit.model, hit.status, hit.data, 0.0, hit.tokens, hit.error, True)

        last = LLMResult(False, agent, None, "ERROR", error="no model attempted")
        for ep in cfg.endpoints():
            first = cfg.model_for(agent) if ep.name == "default" else ep.model
            models = [first, *[m for m in ep.fallback if m != first]]
            if ep.daily_budget is not None and self._ep_calls(ep.name) >= ep.daily_budget:
                last = LLMResult(False, agent, None, "BUDGET", error=f"{ep.name}: its daily budget is used up")
                continue  # that provider's free quota is spent: the next provider answers
            for model in models:
                last = self._try_model(agent, ep, model, system, user, validate)
                if last.ok or last.status == "BUDGET":
                    break
            if last.ok or (last.status == "BUDGET" and last.error == "daily call budget exhausted"):
                break  # answered, or the overall budget is spent: no provider may be called
        if cache_key is not None and last.ok:
            self._cache[key] = last
            if len(self._cache) > 2000:
                self._cache.pop(next(iter(self._cache)))
        return last

    def _ep_calls(self, name: str) -> int:
        with self._lock:
            return self._ep_day.get((self._day(), name), 0)

    def _try_model(self, agent, ep: "Endpoint", model, system, user, validate) -> LLMResult:
        cfg = self.config
        label = model if ep.name == "default" else f"{ep.name}:{model}"
        headers = {"Content-Type": "application/json"}
        if ep.api_key:
            headers["Authorization"] = f"Bearer {ep.api_key}"
        body = {
            "model": model, "temperature": 0.2, "max_tokens": cfg.max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
        }
        url = f"{ep.base_url}/chat/completions"
        retried = False
        for attempt in range(3):  # a read: one retry on throttling/server error, one without response_format
            if not self._budget_ok():
                return LLMResult(False, agent, label, "BUDGET", error="daily call budget exhausted")
            if ep.daily_budget is not None and self._ep_calls(ep.name) >= ep.daily_budget:
                return LLMResult(False, agent, label, "BUDGET", error=f"{ep.name}: its daily budget is used up")
            self._spend()
            with self._lock:
                k = (self._day(), ep.name)
                self._ep_day = {kk: v for kk, v in self._ep_day.items() if kk[0] == k[0]}
                self._ep_day[k] = self._ep_day.get(k, 0) + 1
            self.stats["calls"] += 1
            t0 = time.perf_counter()
            try:
                resp = self._transport(url, headers, body, cfg.timeout_s)
            except urllib.error.HTTPError as exc:
                if exc.code == 400 and "response_format" in body:
                    body = {k2: v for k2, v in body.items() if k2 != "response_format"}
                    continue  # some providers reject JSON mode; the reply is validated here anyway
                if exc.code in (429, 500, 502, 503, 504) and not retried:
                    retried = True
                    self.stats["retries"] += 1
                    time.sleep(0.5)
                    continue
                self.stats["failed"] += 1
                return LLMResult(False, agent, label, "HTTP_ERROR", latency_ms=(time.perf_counter() - t0) * 1000,
                                 error=f"HTTP {exc.code}")
            except (TimeoutError, urllib.error.URLError, OSError) as exc:
                self.stats["failed"] += 1
                status = "TIMEOUT" if "timed out" in str(exc).lower() or isinstance(exc, TimeoutError) else "ERROR"
                return LLMResult(False, agent, label, status, latency_ms=(time.perf_counter() - t0) * 1000,
                                 error=type(exc).__name__)
            except Exception as exc:  # malformed response bodies and the like
                self.stats["failed"] += 1
                return LLMResult(False, agent, label, "ERROR", latency_ms=(time.perf_counter() - t0) * 1000,
                                 error=type(exc).__name__)
            latency = (time.perf_counter() - t0) * 1000
            try:
                text = resp["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                self.stats["failed"] += 1
                return LLMResult(False, agent, label, "INVALID_JSON", latency_ms=latency, error="no message content")
            data = extract_json(text or "")
            if data is None:
                self.stats["failed"] += 1
                return LLMResult(False, agent, label, "INVALID_JSON", latency_ms=latency, error="no JSON object")
            problem = validate(data)
            if problem:
                self.stats["failed"] += 1
                return LLMResult(False, agent, label, "SCHEMA", latency_ms=latency, error=problem)
            self.stats["ok"] += 1
            return LLMResult(True, agent, label, "OK", data, latency, resp.get("usage"))
        self.stats["failed"] += 1
        return LLMResult(False, agent, label, "HTTP_ERROR", error="retries exhausted")

    def health(self) -> dict:
        day = self._day()
        return {**self.config.public(), **self.stats, "calls_today": self._calls.get(day, 0),
                "calls_today_by_provider": {n: c for (d, n), c in self._ep_day.items() if d == day}}
