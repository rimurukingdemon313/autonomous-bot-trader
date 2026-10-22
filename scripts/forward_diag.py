"""One-off diagnostic (side branch only): OpenRouter's public model catalog (no key is sent), the models that
read images, with their published prices, to choose a stronger trader for a paper test. Never trades."""
import json, sys, urllib.request
from pathlib import Path

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60) as r:  # noqa: S310 - public catalog
    data = json.loads(r.read())["data"]
rows = []
for m in data:
    arch = m.get("architecture") or {}
    ins = arch.get("input_modalities") or []
    p = m.get("pricing") or {}
    try:
        pin, pout = float(p.get("prompt") or 0) * 1e6, float(p.get("completion") or 0) * 1e6
    except ValueError:
        continue
    rows.append({"id": m["id"], "name": m.get("name"), "image": "image" in ins, "in_per_m": round(pin, 3),
                 "out_per_m": round(pout, 3), "image_each": p.get("image"), "context": m.get("context_length"),
                 "created": m.get("created"), "params": m.get("supported_parameters")})
(out / "catalog.json").write_text(json.dumps(rows, indent=1))
keep = ("anthropic/", "openai/", "google/", "x-ai/", "qwen/", "meta-llama/", "mistralai/", "deepseek/", "moonshotai/", "z-ai/")
vis = sorted([r for r in rows if r["image"] and r["id"].startswith(keep) and r["in_per_m"] > 0],
             key=lambda r: -(r["created"] or 0))
lines = [f"models in the catalog: {len(rows)}; paid, image input, major labs: {len(vis)}", "",
         "| id | in $/M | out $/M | context | created |", "|---|---|---|---|---|"]
from datetime import datetime, timezone
for r in vis[:80]:
    lines.append(f"| {r['id']} | {r['in_per_m']} | {r['out_per_m']} | {r['context']} | "
                 f"{datetime.fromtimestamp(r['created'] or 0, timezone.utc):%Y-%m-%d} |")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines[:12]))
