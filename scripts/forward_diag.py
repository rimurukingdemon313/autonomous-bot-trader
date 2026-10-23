"""One-off diagnostic (side branch only): choosing a cheap paid trader for a one-week paper test the owner funded
($10 on the OpenRouter key). It reads the public catalog with its benchmarks and prices, the key's spend fields
(numbers only, never the key), and asks each shortlisted model ONE trading-style question to measure its real
tokens, cost and latency. A few cents in all. Never trades."""
import json, math, os, random, sys, time, urllib.error, urllib.request
from pathlib import Path

BASE = "https://openrouter.ai/api/v1"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
KEY = (os.environ.get("OPENROUTER_API_KEY") or "").strip().strip('"').strip("'")
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "X-Title": "autonomous-bot-trader (diagnostic)"}


def get(path, auth=True):
    req = urllib.request.Request(BASE + path, headers=H if auth else {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def post(body, timeout=240):
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(body).encode(), headers=H, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            return r.status, json.loads(r.read()), time.time() - t0
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read(4000)), time.time() - t0
        except Exception:  # noqa: BLE001
            return e.code, None, time.time() - t0
    except Exception as e:  # noqa: BLE001
        return -1, {"error": type(e).__name__}, time.time() - t0


def nums(d):
    return {k: v for k, v in (d or {}).items() if isinstance(v, (int, float, bool)) or v is None}


report = {}
st, cat = get("/models", auth=False)
models = cat["data"]
rows = []
for m in models:
    p = m.get("pricing") or {}
    try:
        pin, pout = float(p.get("prompt") or 0) * 1e6, float(p.get("completion") or 0) * 1e6
    except ValueError:
        continue
    if m["id"].endswith(":free") or pin <= 0 or ":batch" in m["id"]:
        continue
    aa = ((m.get("benchmarks") or {}).get("artificial_analysis") or {}) if isinstance(m.get("benchmarks"), dict) else {}
    ins = (m.get("architecture") or {}).get("input_modalities") or []
    rows.append({"id": m["id"], "in": round(pin, 3), "out": round(pout, 3), "image": "image" in ins,
                 "ii": aa.get("intelligence_index"), "aa": {k: v for k, v in aa.items() if isinstance(v, (int, float))},
                 "pricing": p, "context": m.get("context_length"), "created": m.get("created"),
                 "reasoning": "reasoning" in (m.get("supported_parameters") or []),
                 "expires": m.get("expiration_date")})
# a decision's two calls: about 15k tokens in and up to 6k out each (measured on the free traders)
for r in rows:
    r["usd_per_call"] = round((15000 * r["in"] + 6000 * r["out"]) / 1e6, 5)
cheap = sorted([r for r in rows if r["usd_per_call"] <= 0.02 and r["ii"] is not None], key=lambda r: -r["ii"])
report["cheap_ranked"] = [{k: r[k] for k in ("id", "ii", "in", "out", "image", "reasoning", "usd_per_call", "context", "expires")}
                          for r in cheap[:30]]
report["frontier_ii"] = sorted([(r["ii"], r["id"]) for r in rows if r["ii"] is not None], reverse=True)[:8]

stk, key = get("/key")
report["key_http"] = stk
report["key_fields"] = nums((key or {}).get("data"))
stc, cr = get("/credits")
report["credits_http"] = stc
report["credits"] = nums((cr or {}).get("data"))

# one trading-style question per shortlisted model: real reasoning, real tokens, real cost
random.seed(7)
px, bars = 1.1650, []
for i in range(96):
    o = px; px += random.gauss(0, 0.0006); h = max(o, px) + abs(random.gauss(0, 0.0003)); l = min(o, px) - abs(random.gauss(0, 0.0003))
    bars.append(f"{i:02d} o={o:.5f} h={h:.5f} l={l:.5f} c={px:.5f}")
prompt = ("You are a forex trader. EURUSD M15 bars, oldest first:\n" + "\n".join(bars) +
          f"\nBid {px:.5f}. " + "Decide BUY or SELL for the next 8 hours with a stop and a target. Reply with ONLY a JSON "
          "object: {\"direction\": \"BUY\"|\"SELL\", \"confidence\": 50-90, \"stop_loss\": price, \"take_profit\": price, "
          "\"reason\": \"one sentence\"}")
short = [r for r in cheap if r["image"]][:6]
for extra in ("deepseek/deepseek-v4.1-flash-1017", "anthropic/claude-haiku-5.5", "openai/gpt-6-luna", "qwen/qwen3.8-flash"):
    r = next((x for x in rows if x["id"] == extra), None)
    if r and r not in short:
        short.append(r)
tests = []
for r in short[:9]:
    body = {"model": r["id"], "messages": [{"role": "user", "content": prompt}], "temperature": 0.2,
            "max_tokens": 12000, "usage": {"include": True}}
    if r["reasoning"]:
        body["reasoning"] = {"effort": "medium"}
    code, pay, sec = post(body)
    u = (pay or {}).get("usage") or {}
    text = None
    try:
        text = pay["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001
        pass
    tests.append({"id": r["id"], "ii": r["ii"], "http": code, "seconds": round(sec, 1), "served": (pay or {}).get("model"),
                  "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
                  "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                  "cost": u.get("cost"), "answer": (text or "")[:300] if isinstance(text, str) else str(text)[:300],
                  "error": None if code == 200 else json.dumps(pay)[:300]})
report["tests"] = tests
time.sleep(20)
stk2, key2 = get("/key")
report["key_fields_after"] = nums((key2 or {}).get("data"))

(out / "check.json").write_text(json.dumps(report, indent=1))
lines = ["# Cheap paid traders: benchmark, price, one real call each", "",
         f"key HTTP {stk}: {json.dumps(report['key_fields'])}", f"credits HTTP {stc}: {json.dumps(report['credits'])}",
         f"key after the test calls: {json.dumps(report['key_fields_after'])}", "",
         "frontier intelligence index: " + ", ".join(f"{i} {m}" for i, m in report["frontier_ii"]), "",
         "| id | intelligence | in $/M | out $/M | image | ~$/call |", "|---|---|---|---|---|---|"]
for r in report["cheap_ranked"]:
    lines.append(f"| {r['id']} | {r['ii']} | {r['in']} | {r['out']} | {r['image']} | {r['usd_per_call']} |")
lines += ["", "| id | HTTP | s | in tok | out tok | reasoning | cost $ | answer |", "|---|---|---|---|---|---|---|---|"]
for t in tests:
    lines.append(f"| {t['id']} | {t['http']} | {t['seconds']} | {t['prompt_tokens']} | {t['completion_tokens']} | "
                 f"{t['reasoning_tokens']} | {t['cost']} | {(t['answer'] or t['error'] or '').replace('|', '/')[:160]} |")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
