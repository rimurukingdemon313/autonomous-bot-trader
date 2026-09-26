"""Build the production knowledge base from research data before the holdout.

    python scripts/build_knowledge.py

Writes models/artifacts/{memory.npz, regime.json, knowledge_card.json}.
Uses only bars the sealed DataStore will serve (before 2017-01-01), so the
knowledge base never contains the final holdout. The running system then
grows the memory from its own forward experience.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.backtest.runner import EMBARGO_S, seed_memory  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.features.store import FEATURE_VERSION, compute_matrix  # noqa: E402
from aitrader.memory.patterns import MEMORY_VERSION  # noqa: E402
from aitrader.regime.model import RegimeModel  # noqa: E402
from aitrader.research.labels import LABEL_VERSION, CostModel  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
           "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY"]


def main() -> int:
    holdout = Holdout.load(ROOT / "research" / "holdout.json")
    store = DataStore(ROOT / "data" / "processed", holdout)
    series = {s: store.load(s, "H1") for s in SYMBOLS}
    mats = {s: compute_matrix(v) for s, v in series.items()}
    cutoff = holdout.start_epoch() - EMBARGO_S
    rows, times = [], []
    for s, m in mats.items():
        t = series[s].available_at
        rows.append(m[t <= cutoff])
        times.append(t[t <= cutoff])
    regime = RegimeModel.fit(np.concatenate(rows), np.concatenate(times), trained_until=cutoff)
    start = min(int(v.available_at[0]) for v in series.values())
    memory = seed_memory(series, mats, start, holdout.start_epoch(), 4, CostModel())
    out = ROOT / "models" / "artifacts"
    out.mkdir(parents=True, exist_ok=True)
    memory.save(out / "memory.npz", compact=True)
    (out / "regime.json").write_text(regime.to_json())
    digest = hashlib.sha256((out / "memory.npz").read_bytes() + (out / "regime.json").read_bytes()).hexdigest()
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    card = {
        "id": "kb-fx12-h1", "version": "kb-1.0.0", "hash": digest[:16], "sha256": digest,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"), "code_commit": commit,
        "data": {"source": "dukascopy-via-fx-data", "symbols": SYMBOLS,
                 "from": datetime.fromtimestamp(start, timezone.utc).date().isoformat(),
                 "until_exclusive": str(holdout.start), "timeframe": "H1 (complete bars from M15)",
                 "manifest_hashes": {s: manifest["datasets"][s]["content_sha256"][:16] for s in SYMBOLS}},
        "features": FEATURE_VERSION, "labels": LABEL_VERSION, "memory": MEMORY_VERSION,
        "regime": {"version": regime.version, "trained_until": regime.trained_until, "n_train": regime.n_train},
        "patterns": len(memory), "decision_every_bars": 4,
        "status": "RESEARCH_CANDIDATE",
        "status_note": "Not validated. Its research verdict is PR-001 (research/preregistrations). "
                       "Paper/demo use is forward testing, not evidence of an edge.",
    }
    (out / "knowledge_card.json").write_text(json.dumps(card, indent=2))
    print(json.dumps({k: card[k] for k in ("hash", "patterns", "regime")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
