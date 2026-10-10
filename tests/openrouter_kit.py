"""A scripted OpenRouter for tests: a catalog, a key record and chat replies, all known in advance.

No test ever reaches openrouter.ai. Each chat request is recorded (model, role, body) so a test can prove what
was sent, to which model, how often, and that nothing paid was ever asked.
"""

from __future__ import annotations

import json

from aitrader.llm.openrouter import OpenRouterClient, OpenRouterConfig

KEY = "sk-or-v1-TESTKEY-0123456789abcdefWXYZ"  # a fake key: the tests prove it never leaves the client


def model(mid, image=True, ii=None, price="0", outs=("text",), desc="", ctx=262144, params=("reasoning",), **extra):
    m = {"id": mid, "name": mid.split("/")[-1], "context_length": ctx, "created": 1_780_000_000, "description": desc,
         "architecture": {"input_modalities": ["text", "image"] if image else ["text"], "output_modalities": list(outs)},
         "pricing": {"prompt": price, "completion": price}, "supported_parameters": list(params), **extra}
    if ii is not None:
        m["benchmarks"] = {"artificial_analysis": {"intelligence_index": ii}}
    return m


VISION, TRADER, DEBATE = "seer/vision-a:free", "think/trader-b:free", "third/debate-c:free"
CATALOG = [
    model(VISION, image=True, ii=30),
    model(TRADER, image=False, ii=28),
    model(DEBATE, image=True, ii=15),
    model("paid/genius", image=True, ii=70, price="0.000002"),               # paid: never used
    model("promo/zero-no-suffix", image=True, ii=65),                        # $0 but not a :free variant
    model("music/song-maker:free", image=True, ii=60, outs=("audio",)),      # writes audio, billed per song
    model("guard/content-safety:free", image=True, ii=60),                   # a classifier, not a trader
]


def role_of(body) -> str:
    system = body["messages"][0]["content"]
    return "trader1" if "TRADER 1" in system else "trader2" if "TRADER 2" in system else (
        "debate" if "DESK HEAD" in system else "other")


def packet_of(body) -> dict:
    c = body["messages"][1]["content"]
    text = c if isinstance(c, str) else next(p["text"] for p in c if p.get("type") == "text")
    return json.loads(text)


def has_image(body) -> bool:
    c = body["messages"][1]["content"]
    return isinstance(c, list) and any(p.get("type") == "image_url" for p in c)


def ok(content, model_id, cost=0):
    return 200, {}, {"id": "gen-test", "model": model_id, "choices": [{"message": {"content": content}}],
                     "usage": {"total_tokens": 321, "cost": cost}}


class FakeOpenRouter:
    """transport(method, url, headers, body, timeout). `reply(role, body)` returns a dict (sent as JSON), a
    string (sent verbatim) or a full (status, headers, payload) tuple."""

    def __init__(self, reply, catalog=None, usage=0.0, free_tier=True):
        self.reply, self.catalog = reply, list(CATALOG if catalog is None else catalog)
        self.usage, self.free_tier = usage, free_tier
        self.calls: list[dict] = []
        self.headers: list[dict] = []

    def __call__(self, method, url, headers, body, timeout):
        self.headers.append(dict(headers))
        if url.endswith("/models"):
            return 200, {}, {"data": self.catalog}
        if url.endswith("/key"):
            return 200, {}, {"data": {"label": "test", "usage": self.usage, "is_free_tier": self.free_tier}}
        self.calls.append({"model": body["model"], "role": role_of(body), "body": body})
        out = self.reply(role_of(body), body)
        if isinstance(out, tuple):
            return out
        return ok(out if isinstance(out, str) else json.dumps(out), body["model"])


def client(fake, key=KEY, clock=None, **cfg):
    kw = {"sleep": lambda s: None}
    if clock is not None:
        kw["clock"] = clock
    return OpenRouterClient(OpenRouterConfig(api_key=key, **cfg), transport=fake, **kw)


def answer(direction, bid, ask, atr, confidence=80, stop_atr=1.0, target_atr=2.0, **extra):
    """A well-formed trader answer at the executable price."""
    side = 1 if direction == "BUY" else -1
    entry = ask if side > 0 else bid
    stop, target = entry - side * stop_atr * atr, entry + side * target_atr * atr
    return {"direction": direction, "entry": entry, "stop_loss": stop, "take_profit": target,
            "confidence": confidence, "risk_reward": round(target_atr / stop_atr, 2),
            "market_structure": "HH/HL", "liquidity": "equal highs above", "momentum": "rising",
            "trend": "up", "reversal_probability": 20, "invalidation": stop,
            "reason": f"scripted {direction}", **extra}
