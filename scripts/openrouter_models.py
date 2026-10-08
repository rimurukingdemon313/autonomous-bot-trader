"""Fetch OpenRouter's public model catalog (no key needed) and show the FREE models the dual-AI trader would select.

    python scripts/openrouter_models.py --out research/results/openrouter-free-models.json

The selection is aitrader/llm/free_models.py, the same code the running system uses.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aitrader.llm.free_models import free_candidates, is_free, select  # noqa: E402

URL = "https://openrouter.ai/api/v1/models"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    req = urllib.request.Request(URL, headers={"User-Agent": "aitrader-free-model-probe"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        catalog = json.loads(r.read())["data"]
    sel = select(catalog, now=time.time())
    free = [m for m in catalog if is_free(m)]
    cands = free_candidates(catalog)
    out = {"fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "catalog_models": len(catalog),
           "free_models": len(free), "free_vision": len(cands["vision"]), "selection": sel.as_dict(),
           "free_catalog": free}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("catalog_models", "free_models", "free_vision")}))
    for role in ("vision", "judge", "verifier"):
        print(role, [(r["id"], r["score"]) for r in sel.as_dict()[role][:5]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
