"""Build the history desk's reference memory: every complete H1 bar before the holdout.

    python scripts/build_history.py

Writes models/artifacts/{history.npz, history_card.json}.

The knowledge base (memory.npz, one situation every 4 bars) is what PR-001
tested and stays untouched. This is a SEPARATE, denser reference for the
language-model traders' history desk: one situation per hour, each with the
realised result, after spread and costs, of every declared trade (T1/T2 x
BUY/SELL). It uses only bars the sealed DataStore serves (before
2017-01-01): the holdout is never read.

Consecutive hours overlap: neighbouring situations share most of their
future. The desk therefore reports how many DISTINCT episodes (pair, day)
its neighbours come from; the raw count overstates the evidence.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.backtest.runner import seed_memory  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.features.store import FEATURE_VERSION, compute_matrix  # noqa: E402
from aitrader.memory.patterns import MEMORY_VERSION  # noqa: E402
from aitrader.research.labels import LABEL_VERSION, TEMPLATES, CostModel  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
           "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY"]
HISTORY_VERSION = "history-1.0.0"


def main() -> int:
    t0 = time.time()
    holdout = Holdout.load(ROOT / "research" / "holdout.json")
    store = DataStore(ROOT / "data" / "processed", holdout)
    series = {s: store.load(s, "H1") for s in SYMBOLS}
    mats = {s: compute_matrix(v) for s, v in series.items()}
    start = min(int(v.available_at[0]) for v in series.values())
    memory = seed_memory(series, mats, start, holdout.start_epoch(), 1, CostModel())
    out = ROOT / "models" / "artifacts"
    memory.save(out / "history.npz", compact=True)
    digest = hashlib.sha256((out / "history.npz").read_bytes()).hexdigest()
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    card = {
        "id": "history-fx12-h1", "version": HISTORY_VERSION, "hash": digest[:16], "sha256": digest,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"), "code_commit": commit,
        "data": {"source": "dukascopy-via-fx-data", "symbols": SYMBOLS,
                 "from": datetime.fromtimestamp(start, timezone.utc).date().isoformat(),
                 "until_exclusive": str(holdout.start), "timeframe": "H1 (complete bars from M15), every bar",
                 "manifest_hashes": {s: manifest["datasets"][s]["content_sha256"][:16] for s in SYMBOLS}},
        "features": FEATURE_VERSION, "labels": LABEL_VERSION, "memory": MEMORY_VERSION,
        "situations": len(memory), "trades": len(memory) * len(memory.action_keys),
        "trade_types": {t.key: {"stop_atr": t.stop_atr, "target_atr": t.target_atr, "max_hours": t.max_bars}
                        for t in TEMPLATES},
        "purpose": "Reference for the language-model traders' history desk. Not used by the evidence system; "
                   "not evidence of an edge (PR-001 found none in this kind of memory).",
    }
    (out / "history_card.json").write_text(json.dumps(card, indent=2))
    print(json.dumps({k: card[k] for k in ("hash", "situations", "trades")}), f"{time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
