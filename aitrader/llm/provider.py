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
    Two seats at one provider: name the second e.g. groq2 or gemini2 and give it its own
    AI_GROQ2_MODEL (a different model is a different mind); the address, key and limits of
    `groq` are reused unless AI_GROQ2_* sets them.
    AI_<NAME>_MAX_REQUEST_TOKENS  optional: the most one request may count (prompt + reply budget).
                               Groq's free tier refuses more than its per-minute limit in one request
                               (HTTP 413), so `groq` defaults to 7000. A caller that can shorten its
                               packet (`shrink`) sends that provider a shortened view instead of nothing;
                               a 413 that states "Limit L, Requested R" recalibrates the size estimate.

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


def provider_family(name: str) -> str:
    """The provider behind a seat name: "groq2" / "groq_b" -> "groq" when "groq" is a known provider.
    A second seat reuses the family's address, key and request limit unless it sets its own."""
    base = re.sub(r"(?:[_-]?[a-z]|[_-]?\d+)$", "", name) if name not in KNOWN_PROVIDERS else name
    return base if base in KNOWN_PROVIDERS else name


@dataclass(frozen=True)
class Endpoint:
    name: str
    base_url: str
    api_key: str = field(default="", repr=False)
    model: str = ""
    fallback: tuple[str, ...] = ()
    daily_budget: int | None = None
    max_tokens: int | None = None  # AI_<NAME>_MAX_TOKENS: a smaller reply budget for a provider whose
                                   # per-minute limit counts the reply budget in the request (Groq)
    max_request_tokens: int | None = None  # AI_<NAME>_MAX_REQUEST_TOKENS (groq: 7000 by default)

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
            fam = provider_family(name)  # "groq2" is a second seat at groq: same address, key and limits
            fup = fam.upper()
            budget = e.get(f"AI_{up}_DAILY_BUDGET", "").strip()
            providers.append(Endpoint(
                name=name,
                base_url=(e.get(f"AI_{up}_BASE_URL", "").strip() or e.get(f"AI_{fup}_BASE_URL", "").strip()
                          or KNOWN_PROVIDERS.get(fam, "")).rstrip("/"),
                api_key=e.get(f"AI_{up}_API_KEY", "").strip() or e.get(f"AI_{fup}_API_KEY", "").strip(),
                model=e.get(f"AI_{up}_MODEL", "").strip(),
                fallback=tuple(m.strip() for m in e.get(f"AI_{up}_FALLBACK_MODELS", "").split(",") if m.strip()),
                daily_budget=int(budget) if budget else None,
                max_tokens=int(e[f"AI_{up}_MAX_TOKENS"]) if e.get(f"AI_{up}_MAX_TOKENS", "").strip() else None,
                max_request_tokens=(int(e[f"AI_{up}_MAX_REQUEST_TOKENS"])
                                    if e.get(f"AI_{up}_MAX_REQUEST_TOKENS", "").strip()
                                    else DEFAULT_MAX_REQUEST_TOKENS.get(fam))))
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


#: Sent on every model request. Groq sits behind Cloudflare, which refuses Python's default
#: "Python-urllib/3.x" with HTTP 403 (error 1010) before the key is even read.
USER_AGENT = "aitrader/1.0 (paper trading research; python)"


def retry_after_s(exc: urllib.error.HTTPError, message: str = "") -> float | None:
    """How long the provider itself asked us to wait, from its Retry-After header or its message
    ("Please try again in 7.66s", "in 2m59.5s", "in 250ms"); None when it did not say."""
    try:
        ra = exc.headers.get("Retry-After") if exc.headers is not None else None
        if ra is not None:
            return max(0.0, float(ra))
    except (TypeError, ValueError, AttributeError):
        pass
    m = re.search(r"try again in\s+(?:(\d+)h)?(?:(\d+)m(?!s))?(?:([\d.]+)s)?(?:([\d.]+)ms)?", message or "", re.I)
    if not m or not any(m.groups()):
        return None
    h, mi, sec, ms = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + float(sec or 0) + float(ms or 0) / 1000


def provider_message(exc: urllib.error.HTTPError, api_key: str = "", limit: int = 140) -> str:
    """The provider's own explanation of a refusal ("model not found", "quota exceeded"...), short
    and with the key and anything key-shaped removed. Empty when the body cannot be read."""
    from ..observability import redact

    try:
        raw = exc.read(4000).decode("utf-8", "replace") if exc.fp is not None else ""
    except Exception:
        return ""
    msg = raw
    try:
        data = json.loads(raw)
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            msg = str(err.get("message") or err.get("code") or raw)
        elif isinstance(err, str):
            msg = err
        elif isinstance(data, dict) and data.get("message"):
            msg = str(data["message"])
    except (ValueError, AttributeError):
        pass
    if api_key:
        msg = msg.replace(api_key, "[redacted]")
    return " ".join(redact(msg).split())[:limit]


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


#: How long a model is left alone after its provider refuses it for a reason that asking again a
#: minute later will not fix. A spent free quota (429) waits 10 minutes, doubling on each refusal
#: in a row up to an hour; a model name the provider does not have (404) waits 6 hours; a refused
#: key (401/403) waits 30 minutes; an oversized request (413) 10 minutes (a smaller one may fit sooner). When a 429 says how long to wait
#: (Retry-After, or "try again in 7.6s"), that is used instead, at least a minute. Nothing is spent while waiting,
#: and the next model or provider answers instead. A success clears it.
COOLDOWN_S = {429: 600, 404: 6 * 3600, 401: 1800, 403: 1800, 413: 600}
#: providers whose free tier refuses a single request above its per-minute token limit
DEFAULT_MAX_REQUEST_TOKENS = {"groq": 7000}
CHARS_PER_TOKEN = 3.0  # conservative for JSON full of numbers; recalibrated by a 413 that states its sizes
SHRINK_LEVELS = 3
MAX_QUOTA_COOLDOWN_S = 3600


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
        self._ep_stats: dict[str, dict] = {}  # provider -> ok / failed / last error (no secrets: status + message)
        self._cool: dict[str, tuple[float, str, int]] = {}  # "provider:model" -> (until, why, refusals in a row)
        self._cpt: dict[str, float] = {}  # provider -> chars per token, learned from a 413 that states its sizes
        self._limits: dict[str, int] = {}  # provider -> request limit learned from a 413 (lower than configured)
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
                      *, cache_key: str | None = None, only: str | None = None,
                      shrink: Callable[[dict, int], dict] | None = None) -> LLMResult:
        """Ask for a JSON object; return it only if `validate` returns None.

        `only` restricts the call to one named provider (and its own fallback models): a
        trading-room member speaks with its own model, and never borrows another's voice.
        `shrink(packet, level)` (level 1..3) returns a shorter view of the packet for a provider
        whose request limit the full one exceeds; without it such a provider is skipped (TOO_LARGE).
        """
        cfg = self.config
        if not cfg.enabled:
            return LLMResult(False, agent, None, "DISABLED", error="AI_PROVIDER is not configured")
        endpoints = [ep for ep in cfg.endpoints() if only is None or ep.name == only]
        if not endpoints:
            return LLMResult(False, agent, None, "DISABLED", error=f"provider {only!r} is not configured")
        user = json.dumps(packet, sort_keys=True, separators=(",", ":"), default=str)
        key = hashlib.sha256(f"{agent}|{cfg.model_for(agent)}|{only}|{system}|{user}|{cache_key}".encode()).hexdigest()
        if cache_key is not None and key in self._cache:
            self.stats["cache_hits"] += 1
            hit = self._cache[key]
            return LLMResult(hit.ok, hit.agent, hit.model, hit.status, hit.data, 0.0, hit.tokens, hit.error, True)

        last = LLMResult(False, agent, None, "ERROR", error="no model attempted")
        for ep in endpoints:
            first = cfg.model_for(agent) if ep.name == "default" else ep.model
            models = [first, *[m for m in ep.fallback if m != first]]
            if ep.daily_budget is not None and self._ep_calls(ep.name) >= ep.daily_budget:
                last = LLMResult(False, agent, None, "BUDGET", error=f"{ep.name}: its daily budget is used up")
                continue  # that provider's free quota is spent: the next provider answers
            for model in models:
                label = model if ep.name == "default" else f"{ep.name}:{model}"
                resting = self._resting(label)
                if resting:
                    last = LLMResult(False, agent, label, "COOLDOWN", error=resting)
                    continue  # not asked, nothing spent: the next model or provider answers
                level, ep_user = self._fit(ep, system, packet, user, shrink, 0)
                while True:
                    if ep_user is None:
                        last = LLMResult(False, agent, label, "TOO_LARGE",
                                         error=f"the request exceeds {ep.name}'s limit of {self._limit(ep)} "
                                               "tokens even shortened: not sent")
                        break
                    last = self._try_model(agent, ep, model, system, ep_user, validate)
                    size = re.search(r"Limit (\d+), Requested (\d+)", last.error or "") if not last.ok else None
                    if size and (last.error or "").startswith("HTTP 413"):
                        self._calibrate(ep, system, ep_user, int(size.group(1)), int(size.group(2)))
                        if shrink is not None and level < SHRINK_LEVELS:
                            level, ep_user = self._fit(ep, system, packet, user, shrink, level + 1)
                            continue  # the same model, a shorter view: no rest needed for a size problem
                    break
                self._note(ep.name, last)
                self._after(label, last)
                if last.ok or last.status == "BUDGET":
                    break
            if last.ok or (last.status == "BUDGET" and last.error == "daily call budget exhausted"):
                break  # answered, or the overall budget is spent: no provider may be called
        if cache_key is not None and last.ok:
            self._cache[key] = last
            if len(self._cache) > 2000:
                self._cache.pop(next(iter(self._cache)))
        return last

    def _tokens(self, ep: "Endpoint", system: str, user: str) -> float:
        cpt = self._cpt.get(ep.name, CHARS_PER_TOKEN)
        return (len(system) + len(user)) / cpt + (ep.max_tokens or self.config.max_tokens)

    def _fit(self, ep: "Endpoint", system: str, packet: dict, user: str, shrink, start: int):
        """(level, user text) within the endpoint's request limit, starting at `start`; (level, None)
        when even the shortest view does not fit."""
        limit = self._limit(ep)
        if limit is None:
            return start, user
        level, text = start, user if start == 0 else json.dumps(shrink(packet, start), sort_keys=True,
                                                                  separators=(",", ":"), default=str)
        while self._tokens(ep, system, text) > limit:
            if shrink is None or level >= SHRINK_LEVELS:
                return level, None
            level += 1
            text = json.dumps(shrink(packet, level), sort_keys=True, separators=(",", ":"), default=str)
        return level, text

    def _calibrate(self, ep: "Endpoint", system: str, user: str, limit: int, requested: int) -> None:
        """A 413 that states its sizes tells us how this provider counts: learn its chars per token and,
        if it is lower than configured, its limit."""
        prompt = requested - (ep.max_tokens or self.config.max_tokens)
        if prompt > 0:
            with self._lock:
                self._cpt[ep.name] = max(1.0, (len(system) + len(user)) / prompt)
        known = self._limit(ep)
        if known is None or limit * 0.9 < known:
            with self._lock:
                self._limits[ep.name] = int(limit * 0.9)

    def _limit(self, ep: "Endpoint") -> int | None:
        return self._limits.get(ep.name, ep.max_request_tokens)

    def _resting(self, label: str) -> str | None:
        with self._lock:
            c = self._cool.get(label)
        if c is None or self._clock() >= c[0]:
            return None
        return f"resting {max(1, round((c[0] - self._clock()) / 60))} min after: {c[1]}"

    def _after(self, label: str, res: "LLMResult") -> None:
        if res.ok:
            with self._lock:
                self._cool.pop(label, None)
            return
        m = re.match(r"HTTP (\d{3})", res.error or "") if res.status == "HTTP_ERROR" else None
        code = int(m.group(1)) if m else None
        if code not in COOLDOWN_S:
            return
        hint = re.search(r"\[retry in (\d+)s\]", res.error or "")
        with self._lock:
            n = self._cool.get(label, (0.0, "", 0))[2] + 1
            if code == 429 and hint:
                # The provider said how long (a per-minute token limit clears in seconds; a daily one
                # in hours): wait that, at least a minute, never the blind doubling.
                wait = min(max(60, int(hint.group(1)) + 5), 24 * 3600)
            else:
                wait = min(COOLDOWN_S[code] * 2 ** (n - 1), MAX_QUOTA_COOLDOWN_S) if code == 429 else COOLDOWN_S[code]
            self._cool[label] = (self._clock() + wait, (res.error or "")[:120], n)

    def _note(self, name: str, res: "LLMResult") -> None:
        """Per-provider outcome counts and the last failure, so a key or model name that keeps
        failing is visible on the dashboard instead of silently shrinking the team."""
        with self._lock:
            s = self._ep_stats.setdefault(name, {"ok": 0, "failed": 0, "last_error": None, "last_error_model": None,
                                                 "errors": {}})
            if res.ok:
                s["ok"] += 1
                s["errors"].pop(res.model, None)
            else:
                s["failed"] += 1
                s["last_error"] = f"{res.status}: {res.error}"[:200] if res.error else res.status
                s["last_error_model"] = res.model
                s["errors"][res.model or "?"] = s["last_error"]  # each model's own last failure

    def _ep_calls(self, name: str) -> int:
        with self._lock:
            return self._ep_day.get((self._day(), name), 0)

    def _try_model(self, agent, ep: "Endpoint", model, system, user, validate) -> LLMResult:
        cfg = self.config
        label = model if ep.name == "default" else f"{ep.name}:{model}"
        headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
        if ep.api_key:
            headers["Authorization"] = f"Bearer {ep.api_key}"
        body = {
            "model": model, "temperature": 0.2, "max_tokens": ep.max_tokens or cfg.max_tokens,
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
                full = provider_message(exc, ep.api_key, limit=4000)
                wait = retry_after_s(exc, full)  # "try again in" often sits past the shown part
                why = full[:140]
                return LLMResult(False, agent, label, "HTTP_ERROR", latency_ms=(time.perf_counter() - t0) * 1000,
                                 error=f"HTTP {exc.code}" + (f" [retry in {wait:.0f}s]" if wait is not None else "")
                                 + (f" {why}" if why else ""))
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

    def _resting_for(self, provider: str) -> dict:
        """Models of `provider` that are resting now, with the minutes left."""
        now = self._clock()
        with self._lock:
            items = list(self._cool.items())
        return {label: max(1, round((until - now) / 60)) for label, (until, _, _) in items
                if until > now and (label.startswith(provider + ":") or provider == "default")}

    def health(self) -> dict:
        day = self._day()
        return {**self.config.public(), **self.stats, "calls_today": self._calls.get(day, 0),
                "by_provider": {k: {**v, "errors": dict(v.get("errors", {})), "resting": self._resting_for(k)}
                                for k, v in self._ep_stats.items()},
                "calls_today_by_provider": {n: c for (d, n), c in self._ep_day.items() if d == day}}
