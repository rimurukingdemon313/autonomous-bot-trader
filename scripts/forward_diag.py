"""Diagnostic (side branch): OpenRouter's live model catalog, read from its public endpoint. No key is sent, no model
is asked and nothing is spent, so it is safe while a paper-forward shift runs. The whole catalog is saved for the
seat choice (dual-ai, 2026-11-02: the owner allowed stronger models, "but make them know")."""

import json
import sys
import time
import urllib.request
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers={"User-Agent": "aitrader-catalog-probe"})
with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 - the public catalog, no key
    catalog = json.loads(r.read())["data"]
(out / "catalog.json").write_text(json.dumps(catalog))
(out / "REPORT.md").write_text(f"# OpenRouter catalog\n\nRead {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}: "
                               f"{len(catalog)} models, public endpoint, no key sent, nothing asked or spent.\n")
print(len(catalog), "models")
