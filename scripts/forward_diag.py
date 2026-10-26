"""One-off diagnostic (side branch only): the full pricing record the PUBLIC catalog lists for the paid trial's two
models. No key is read or sent, nothing is asked of any model, nothing is spent: safe while a shift runs."""
import json, sys, urllib.request
from pathlib import Path

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 - the public catalog
    data = json.loads(r.read())["data"]
keep = {m["id"]: {k: m.get(k) for k in ("id", "pricing", "architecture", "supported_parameters", "context_length",
                                        "top_provider")}
        for m in data if m.get("id") in ("xiaomi/mimo-v2.6-pro", "anthropic/claude-haiku-5.5")}
keys = sorted({k for m in data for k in (m.get("pricing") or {})})
(out / "check.json").write_text(json.dumps({"models": keep, "every_pricing_key_in_the_catalog": keys}, indent=1))
(out / "REPORT.md").write_text("# The paid trial's models, as the public catalog prices them\n\n"
                               + "every pricing key in the catalog: " + ", ".join(keys) + "\n\n"
                               + "\n".join(f"- `{i}`: {json.dumps(m['pricing'])}" for i, m in keep.items()) + "\n")
print((out / "REPORT.md").read_text())
