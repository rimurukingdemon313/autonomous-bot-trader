"""OpenRouter: the one external AI provider of the dual-AI trader (docs/DUAL_AI.md). ONE key powers both agents.

Configuration, environment only (a local `.env` file is read by `python -m aitrader` too; see `.env.example`):

    OPENROUTER_API_KEY              the one key ("PASTE_MY_KEY_HERE" and empty count as not configured)
    OPENROUTER_BASE_URL             default https://openrouter.ai/api/v1
    OPENROUTER_TIMEOUT_S            per request, default 90 (vision models with an image can be slow)
    OPENROUTER_MAX_RETRIES          per request on a timeout / 429 / 5xx, default 3 (exponential backoff + jitter)
    OPENROUTER_DAILY_CALL_BUDGET    hard cap on requests per UTC day, default 900; never above the key's own free
                                    quota (OpenRouter: 50 a day on a key that never bought credits, 1000 after
                                    $10), read from GET /key, less a margin
    OPENROUTER_VISION_MODEL         optional pin for Agent 1; used only while the catalog lists it as FREE
    OPENROUTER_JUDGE_MODEL          optional pin for Agent 2; same rule

What this client guarantees:

- FREE ONLY. Models come from `free_models.select` (every listed price exactly zero). A reply whose `model`
  is not the requested model, or whose usage reports a cost above zero, is rejected and that model is
  excluded for the rest of the process. Never a paid fallback: no free model -> no call -> NO_TRADE.
- Bounded. Every request has a timeout; retries are bounded with exponential backoff and jitter; a 429
  honours Retry-After; a spent free daily quota stops all calls until the next UTC day; a daily call budget
  caps everything.
- Identified and deduplicated. Every request carries a request id (recorded with the decision); an
  identical request (same role, model, prompt and image) returns the cached result instead of a second call.
- Bounded in time. Each role has a wall-clock deadline across its retries and fallbacks, so a slow free model
  cannot hold the decision cycle (and the position monitor behind it) for long.
- Independent. A caller can name models to avoid: Agent 2 is never the model that answered as Agent 1, whatever
  fallback happened; the verifier avoids both when a third free model exists (`avoid_soft`: otherwise the
  strongest of them is reused).
- Images only where they can be read: an `image_url` part is sent to a model the catalog lists with image
  input; for any other model it is left out (the same chart's marks travel as numbers in the text).
- Paid usage stops everything. GET /key is read with the catalog; if the key's spent credit (`usage`) ever rises
  above what it was when this process first read it, no further request is made (PAID_USAGE). Use this key
  for this bot only, or that check will stop the bot when another application spends from it.
- Fails closed. Nothing raises to the caller: every outcome is a `CallResult`; `ok=False` means NO_TRADE.
- The key is never logged, returned or shown: `public()` gives only whether it is set and its last 4 characters.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from .free_models import Selection, select, supports_image
from .provider import extract_json

OPENROUTER_VERSION = "openrouter-1.2.0"
PLACEHOLDERS = {"", "PASTE_MY_KEY_HERE", "PASTE_YOUR_KEY_HERE", "YOUR_KEY", "changeme"}
#: cooldowns, seconds: a model the provider says it cannot serve rests long; a rate-limited one briefly
COOLDOWN_S = {"unavailable": 6 * 3600, "rate_limited": 300, "failing": 900}
#: the free daily request quota per key tier (OpenRouter's published limits), less a safety margin
FREE_TIER_DAILY, CREDIT_TIER_DAILY, QUOTA_MARGIN = 50, 1000, 2
KEY_CHECK_S = 1800

#: transport(method, url, headers, body | None, timeout) -> (status, headers, parsed JSON or None)
Transport = Callable[[str, str, dict, dict | None, float], tuple[int, dict, dict | None]]


def _http(method: str, url: str, headers: dict, body: dict | None, timeout: float) -> tuple[int, dict, dict | None]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - fixed https base URL
            raw = r.read()
            return r.status, dict(r.headers.items()), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read(8000)
            payload = json.loads(raw) if raw else None
        except Exception:  # noqa: BLE001
            payload = None
        return exc.code, dict(exc.headers.items()) if exc.headers else {}, payload


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str = field(default="", repr=False)
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_s: float = 90.0
    max_retries: int = 3
    daily_budget: int = 900
    vision_pin: str = ""
    judge_pin: str = ""
    app_name: str = "autonomous-bot-trader (paper forward)"

    @property
    def configured(self) -> bool:
        return self.api_key.strip().strip('"').strip("'") not in PLACEHOLDERS

    @classmethod
    def from_env(cls, env: dict | None = None) -> "OpenRouterConfig":
        e = os.environ if env is None else env

        def num(k, default, cast=float):
            try:
                return cast(e.get(k, default))
            except (TypeError, ValueError):
                return default
        return cls(api_key=(e.get("OPENROUTER_API_KEY") or "").strip().strip('"').strip("'"),
                   base_url=(e.get("OPENROUTER_BASE_URL") or cls.base_url).rstrip("/"),
                   timeout_s=max(5.0, num("OPENROUTER_TIMEOUT_S", 90.0)),
                   max_retries=max(0, min(6, num("OPENROUTER_MAX_RETRIES", 3, int))),
                   daily_budget=max(1, num("OPENROUTER_DAILY_CALL_BUDGET", 900, int)),
                   vision_pin=(e.get("OPENROUTER_VISION_MODEL") or "").strip(),
                   judge_pin=(e.get("OPENROUTER_JUDGE_MODEL") or "").strip())

    def public(self) -> dict:
        k = self.api_key
        return {"provider": "openrouter", "configured": self.configured, "base_url": self.base_url,
                "key_hint": ("…" + k[-4:]) if self.configured and len(k) >= 8 else None,
                "timeout_s": self.timeout_s, "max_retries": self.max_retries, "daily_budget": self.daily_budget,
                "vision_pin": self.vision_pin or None, "judge_pin": self.judge_pin or None}


@dataclass
class CallResult:
    ok: bool
    status: str  # OK | NOT_CONFIGURED | NO_FREE_MODEL | BUDGET | DAILY_QUOTA | RATE_LIMITED | TIMEOUT | UNAVAILABLE
    #               | KEY_REJECTED | HTTP_<n> | BAD_RESPONSE | NOT_FREE | WRONG_MODEL | INVALID: <why> | CACHED
    role: str
    model: str | None = None
    data: dict | None = None
    error: str | None = None
    request_id: str | None = None
    provider_id: str | None = None
    attempts: int = 0
    latency_ms: float = 0.0
    cached: bool = False
    tokens: int | None = None

    def record(self) -> dict:
        """What a decision keeps of the call: never the key, never the prompt."""
        return {"role": self.role, "model": self.model, "status": self.status, "ok": self.ok, "error": self.error,
                "request_id": self.request_id, "provider_id": self.provider_id, "attempts": self.attempts,
                "latency_ms": round(self.latency_ms, 1), "cached": self.cached, "tokens": self.tokens}


def _base(model_id: str) -> str:
    return model_id.split(":", 1)[0].lower()


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig, transport: Transport | None = None,
                 clock: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep,
                 catalog_refresh_s: float = 3600) -> None:
        self.config = config
        self.transport = transport or _http
        self.clock, self.sleep = clock, sleep
        self.catalog_refresh_s = catalog_refresh_s
        self._lock = threading.RLock()
        self._catalog: list[dict] = []
        self._selection = Selection(error="catalog not read yet")
        self._cooldown: dict[str, tuple[float, str]] = {}  # model -> (until, why)
        self._excluded: dict[str, str] = {}  # model -> why (never used again in this process)
        self._stats: dict[str, list[int]] = {}  # model -> [ok, failed]
        self._cache: OrderedDict[str, CallResult] = OrderedDict()
        self._inflight: dict[str, threading.Lock] = {}
        self._day, self._calls = "", 0
        self._quota_until = 0.0
        self.last: dict = {}
        self.key_info: dict = {"checked": None}
        self._usage0: float | None = None
        self._paid_usage: str | None = None
        self._key_checked_at = -1e18

    # ── the catalog and the FREE selection ───────────────────────────────

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json",
                "X-Title": self.config.app_name, "HTTP-Referer": "https://github.com/rimurukingdemon313/autonomous-bot-trader"}

    def refresh_models(self, force: bool = False) -> Selection:
        """Read the catalog (public; the key is not needed for it) and rank the FREE models per role."""
        with self._lock:
            now = self.clock()
            if not force and self._catalog and now - self._selection.refreshed < self.catalog_refresh_s:
                return self._reselect()
            try:
                status, _, payload = self.transport("GET", f"{self.config.base_url}/models",
                                                    {"Content-Type": "application/json"}, None, 30.0)
            except Exception as exc:  # noqa: BLE001
                status, payload = 0, {"error": f"{type(exc).__name__}: {exc}"}
            data = (payload or {}).get("data") if status == 200 and isinstance(payload, dict) else None
            if not isinstance(data, list):
                if not self._catalog:  # nothing known: no model, no call
                    self._selection = Selection(error=f"model catalog unavailable (HTTP {status})", refreshed=now)
                return self._selection
            self._catalog = data
            return self._reselect()

    def check_key(self, force: bool = False) -> dict:
        """The key's tier and spend (GET /key): sets the daily quota, and stops all calls if spend ever rises."""
        with self._lock:
            now = self.clock()
            if not self.config.configured or (not force and now - self._key_checked_at < KEY_CHECK_S):
                return self.key_info
            self._key_checked_at = now
            try:
                status, _, payload = self.transport("GET", f"{self.config.base_url}/key", self._headers(), None, 30.0)
            except Exception as exc:  # noqa: BLE001
                status, payload = 0, {"error": f"{type(exc).__name__}"}
            data = (payload or {}).get("data") if status == 200 and isinstance(payload, dict) else None
            if not isinstance(data, dict):
                self.key_info = {**self.key_info, "checked": int(now), "ok": False,
                                 "status": "KEY_REJECTED" if status in (401, 403) else f"HTTP_{status}"}
                return self.key_info
            usage = data.get("usage")
            usage = float(usage) if isinstance(usage, (int, float)) and not isinstance(usage, bool) else None
            if usage is not None:
                if self._usage0 is None:
                    self._usage0 = usage
                elif usage > self._usage0 + 1e-9:
                    self._paid_usage = (f"the key's spent credit rose from {self._usage0} to {usage} while this bot "
                                        "ran: no further request is made")
            free_tier = data.get("is_free_tier")
            quota = (FREE_TIER_DAILY if free_tier is True else CREDIT_TIER_DAILY if free_tier is False else FREE_TIER_DAILY)
            self.key_info = {"checked": int(now), "ok": True, "is_free_tier": free_tier if isinstance(free_tier, bool) else None,
                             "usage_at_start": self._usage0, "usage": usage, "daily_quota": quota - QUOTA_MARGIN,
                             "label_set": bool(data.get("label"))}
            return self.key_info

    @property
    def daily_budget(self) -> int:
        quota = self.key_info.get("daily_quota")
        return min(self.config.daily_budget, quota) if isinstance(quota, int) else self.config.daily_budget

    def _penalties(self) -> dict[str, float]:
        return {m: s[1] / (s[0] + s[1]) for m, s in self._stats.items() if s[0] + s[1] >= 3}

    def _reselect(self) -> Selection:
        now = self.clock()
        resting = {m for m, (until, _) in self._cooldown.items() if until > now}
        self._selection = select(self._catalog, now=now, penalties=self._penalties(),
                                 excluded=set(self._excluded) | resting)
        return self._selection

    def models_for(self, role: str) -> list[str]:
        """The ranked FREE models for a role, the configured pin first when the catalog lists it as FREE."""
        with self._lock:
            sel = self.refresh_models()
            self.check_key()
            ranked = [r["id"] for r in getattr(sel, {"vision": "vision", "judge": "judge"}.get(role, "verifier"))]
            pin = {"vision": self.config.vision_pin, "judge": self.config.judge_pin}.get(role, "")
            if pin and pin in ranked:
                ranked = [pin] + [m for m in ranked if m != pin]
            return ranked

    def selection(self) -> dict:
        with self._lock:
            d = self._selection.as_dict()
            now = self.clock()
            d["cooldown"] = {m: {"until": int(u), "why": w} for m, (u, w) in self._cooldown.items() if u > now}
            d["excluded"] = dict(self._excluded)
            return d

    # ── one chat request, bounded ────────────────────────────────────────

    def _budget_ok(self) -> bool:
        day = datetime.fromtimestamp(self.clock(), timezone.utc).strftime("%Y-%m-%d")
        if day != self._day:
            self._day, self._calls = day, 0
        return self._calls < self.daily_budget

    def _rest(self, model: str, why: str) -> None:
        self._cooldown[model] = (self.clock() + COOLDOWN_S[why], why)

    def _note(self, model: str, ok: bool) -> None:
        s = self._stats.setdefault(model, [0, 0])
        s[0 if ok else 1] += 1

    def sees_images(self, model: str) -> bool:
        with self._lock:
            m = next((x for x in self._catalog if isinstance(x, dict) and x.get("id") == model), None)
            return bool(m) and supports_image(m)

    def chat_json(self, role: str, messages: list[dict], validate: Callable[[dict], str | None],
                  dedupe_key: str, max_models: int = 3, max_tokens: int = 3000, avoid: tuple = (),
                  deadline_s: float = 240.0, avoid_soft: bool = False) -> CallResult:
        """One answer for `role`: the best FREE model first, the next FREE one when a model is unavailable.
        `validate(data)` returns None or why the reply is unusable (an unusable reply is not retried: NO_TRADE).
        `avoid`: models that must not answer (another agent's); `deadline_s`: wall clock for all attempts."""
        if not self.config.configured:
            return CallResult(False, "NOT_CONFIGURED", role, error="OPENROUTER_API_KEY is not set")
        if self._paid_usage:
            return CallResult(False, "PAID_USAGE", role, error=self._paid_usage)
        digest = hashlib.sha256(json.dumps([role, messages, sorted(avoid)], sort_keys=True).encode()).hexdigest()
        key = f"{dedupe_key}|{digest}"
        with self._lock:
            if key in self._cache:
                hit = self._cache[key]
                return CallResult(**{**hit.__dict__, "cached": True})
            gate = self._inflight.setdefault(key, threading.Lock())
        with gate:  # a concurrent identical request waits for the first one instead of calling again
            with self._lock:
                if key in self._cache:
                    hit = self._cache[key]
                    return CallResult(**{**hit.__dict__, "cached": True})
            res = self._call(role, messages, validate, max_models, max_tokens, tuple(avoid), deadline_s, avoid_soft)
            with self._lock:
                if res.ok or res.status.startswith("INVALID"):
                    self._cache[key] = res
                    while len(self._cache) > 512:
                        self._cache.popitem(last=False)
                self._inflight.pop(key, None)
                self.last = {"t": int(self.clock()), **res.record()}
            return res

    def _call(self, role, messages, validate, max_models, max_tokens, avoid=(), deadline_s=240.0,
              avoid_soft=False) -> CallResult:
        ranked = self.models_for(role)
        if self._paid_usage:  # the key check that refresh ran may have just found it
            return CallResult(False, "PAID_USAGE", role, error=self._paid_usage)
        models = [m for m in ranked if m not in avoid][:max_models]
        if not models and avoid_soft:  # no third model: the strongest of the avoided ones is reused
            models = ranked[:max_models]
        if not models:
            why = (f"no FREE {role} model other than {', '.join(avoid)}" if ranked else
                   self._selection.error or "no FREE model qualifies")
            return CallResult(False, "NO_FREE_MODEL", role, error=why)
        deadline = self.clock() + deadline_s
        last = CallResult(False, "UNAVAILABLE", role, error="no model answered")
        for model in models:
            if self.clock() >= deadline:
                return CallResult(False, "TIMEOUT", role, last.model, error=f"no answer within {deadline_s:.0f} s "
                                  f"(last: {last.status})", attempts=last.attempts)
            res = self._one_model(role, model, messages, validate, max_tokens, deadline)
            if res.ok or res.status.startswith("INVALID") or res.status in (
                    "NOT_CONFIGURED", "BUDGET", "DAILY_QUOTA", "KEY_REJECTED", "NOT_FREE", "WRONG_MODEL"):
                return res  # an answer, an unusable answer, or a reason no other model would fix
            last = res  # unavailable / rate-limited / timing out: the next FREE model may answer
        return last

    def _one_model(self, role, model, messages, validate, max_tokens, deadline=float("inf")) -> CallResult:
        rid = uuid.uuid4().hex
        if not self.sees_images(model):
            messages = _text_only(messages)
        body = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": max_tokens,
                "usage": {"include": True}}
        headers = {**self._headers(), "X-Request-Id": rid}
        t0 = time.perf_counter()
        attempts = 0
        status_txt = "UNAVAILABLE"
        err = None
        for attempt in range(self.config.max_retries + 1):
            with self._lock:
                if self.clock() < self._quota_until:
                    return CallResult(False, "DAILY_QUOTA", role, model, error="the free daily request quota is spent "
                                      "until the next UTC day", request_id=rid, attempts=attempts)
                if not self._budget_ok():
                    return CallResult(False, "BUDGET", role, model, error=f"daily call budget "
                                      f"{self.daily_budget} reached", request_id=rid, attempts=attempts)
                self._calls += 1
            attempts += 1
            try:
                code, hdrs, payload = self.transport("POST", f"{self.config.base_url}/chat/completions", headers, body,
                                                     self.config.timeout_s)
            except Exception as exc:  # noqa: BLE001 - timeouts and connection errors: retried, bounded
                code, hdrs, payload, err = -1, {}, None, f"{type(exc).__name__}: {str(exc)[:160]}"
            lat = (time.perf_counter() - t0) * 1000
            msg = _error_message(payload)
            if code == 200 and isinstance(payload, dict) and not payload.get("error"):
                return self._parse(role, model, payload, validate, rid, attempts, lat)
            if code in (401, 403):
                return CallResult(False, "KEY_REJECTED", role, model, error=f"HTTP {code}: {msg}", request_id=rid,
                                  attempts=attempts, latency_ms=lat)
            if code == 402:
                return CallResult(False, "BUDGET", role, model, error=f"HTTP 402 (credits): {msg}", request_id=rid,
                                  attempts=attempts, latency_ms=lat)
            if code in (404,) or (code == 400 and ("not a valid model" in msg.lower() or "no endpoints" in msg.lower())):
                with self._lock:
                    self._rest(model, "unavailable")
                    self._note(model, False)
                return CallResult(False, "UNAVAILABLE", role, model, error=f"HTTP {code}: {msg}", request_id=rid,
                                  attempts=attempts, latency_ms=lat)
            if code == 429:
                if "per-day" in msg.lower() or "per day" in msg.lower():
                    with self._lock:
                        now = self.clock()
                        self._quota_until = (now // 86400 + 1) * 86400
                    return CallResult(False, "DAILY_QUOTA", role, model, error=f"HTTP 429: {msg}", request_id=rid,
                                      attempts=attempts, latency_ms=lat)
                status_txt, err = "RATE_LIMITED", f"HTTP 429: {msg}"
                wait = _retry_after(hdrs)
            elif code == -1:
                status_txt = "TIMEOUT"
                wait = None
            elif code >= 500 or code == 408:
                status_txt, err = f"HTTP_{code}", f"HTTP {code}: {msg}"
                wait = None
            else:
                with self._lock:
                    self._note(model, False)
                return CallResult(False, f"HTTP_{code}", role, model, error=f"HTTP {code}: {msg}", request_id=rid,
                                  attempts=attempts, latency_ms=lat)
            if attempt < self.config.max_retries:
                backoff = min(60.0, wait if wait is not None else min(30.0, 2.0 ** attempt) + random.uniform(0, 0.5))
                if self.clock() + backoff >= deadline:
                    break  # no time left for another attempt on this model
                self.sleep(backoff)
        with self._lock:
            self._note(model, False)
            self._rest(model, "rate_limited" if status_txt == "RATE_LIMITED" else "failing")
        return CallResult(False, status_txt, role, model, error=err, request_id=rid, attempts=attempts,
                          latency_ms=(time.perf_counter() - t0) * 1000)

    def _parse(self, role, model, payload, validate, rid, attempts, lat) -> CallResult:
        served = str(payload.get("model") or "")
        usage = payload.get("usage") or {}
        cost = usage.get("cost")
        try:
            cost_v = float(cost) if cost is not None else 0.0
        except (TypeError, ValueError):
            cost_v = 0.0
        tokens = usage.get("total_tokens") if isinstance(usage.get("total_tokens"), int) else None
        if served and _base(served) != _base(model):
            with self._lock:
                self._excluded[model] = f"served by {served}, not the requested free model"
            return CallResult(False, "WRONG_MODEL", role, model, error=f"requested {model}, served {served}: "
                              "discarded, and this model is not used again", request_id=rid, attempts=attempts,
                              latency_ms=lat, provider_id=payload.get("id"), tokens=tokens)
        if cost_v > 0:
            with self._lock:
                self._excluded[model] = f"a reply reported cost {cost_v}"
            return CallResult(False, "NOT_FREE", role, model, error=f"the reply reported cost {cost_v}: discarded, "
                              "and this model is not used again", request_id=rid, attempts=attempts, latency_ms=lat,
                              provider_id=payload.get("id"), tokens=tokens)
        try:
            text = payload["choices"][0]["message"]["content"]
            if isinstance(text, list):  # some models return content parts
                text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
        except (KeyError, IndexError, TypeError):
            text = None
        data = extract_json(text or "")
        with self._lock:
            self._note(model, data is not None)
        if data is None:
            return CallResult(False, "INVALID: no JSON object in the reply", role, model, request_id=rid,
                              attempts=attempts, latency_ms=lat, provider_id=payload.get("id"), tokens=tokens)
        problem = validate(data)
        if problem:
            return CallResult(False, f"INVALID: {problem}", role, model, data=data, request_id=rid, attempts=attempts,
                              latency_ms=lat, provider_id=payload.get("id"), tokens=tokens)
        return CallResult(True, "OK", role, model, data=data, request_id=rid, attempts=attempts, latency_ms=lat,
                          provider_id=payload.get("id"), tokens=tokens)

    # ── status for the dashboard (never the key) ─────────────────────────

    def health(self) -> dict:
        with self._lock:
            self._budget_ok()
            sel = self.selection()
            return {**self.config.public(), "version": OPENROUTER_VERSION,
                    "status": ("NOT_CONFIGURED" if not self.config.configured else
                               "PAID_USAGE_STOPPED" if self._paid_usage else
                               "KEY_REJECTED" if self.key_info.get("status") == "KEY_REJECTED" else
                               "DAILY_QUOTA_SPENT" if self.clock() < self._quota_until else
                               "NO_FREE_MODEL" if not sel["vision"] or not sel["judge"] else "READY"),
                    "calls_today": self._calls, "daily_budget": self.daily_budget, "last_call": self.last,
                    "key": {k: v for k, v in self.key_info.items()}, "paid_usage": self._paid_usage,
                    "vision_model": sel["vision"][0]["id"] if sel["vision"] else None,
                    "judge_model": sel["judge"][0]["id"] if sel["judge"] else None,
                    "verifier_model": sel["verifier"][0]["id"] if sel["verifier"] else None,
                    "selection": {k: (v[:5] if isinstance(v, list) else v) for k, v in sel.items()},
                    "model_stats": {m: {"ok": s[0], "failed": s[1]} for m, s in self._stats.items()}}


def _text_only(messages: list[dict]) -> list[dict]:
    """The same messages without image parts, for a model that cannot read images."""
    out = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            parts = [x for x in c if not (isinstance(x, dict) and x.get("type") == "image_url")]
            c = "".join(x.get("text", "") for x in parts if isinstance(x, dict)) if all(
                isinstance(x, dict) and x.get("type") == "text" for x in parts) else parts
        out.append({**m, "content": c})
    return out


def _error_message(payload) -> str:
    if not isinstance(payload, dict):
        return ""
    err = payload.get("error")
    if isinstance(err, dict):
        meta = err.get("metadata") or {}
        raw = meta.get("raw") if isinstance(meta, dict) else None
        return " ".join(str(x) for x in (err.get("message"), raw) if x)[:300]
    return str(err or payload.get("message") or "")[:300]


def _retry_after(headers: dict) -> float | None:
    for k, v in (headers or {}).items():
        if k.lower() == "retry-after":
            try:
                return max(0.0, float(v))
            except (TypeError, ValueError):
                return None
    return None


__all__ = ["OPENROUTER_VERSION", "CallResult", "OpenRouterClient", "OpenRouterConfig", "Transport"]
