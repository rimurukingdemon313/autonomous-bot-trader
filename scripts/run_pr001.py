"""Run PR-001 exactly as pre-registered: variants A, B, C, R on 2010-2016.

    python scripts/run_pr001.py            # all four variants, in parallel
    python scripts/run_pr001.py --only C

Reads bars through the DataStore, which truncates at the sealed holdout.
Writes full results to data/results/PR-001/ (not committed: large) and a
summary to research/results/PR-001-summary.json (committed).
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.backtest.runner import BacktestConfig, epoch, run  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.decision.synthesis import SynthesisConfig  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
           "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY"]
VARIANTS = {
    "A": dict(synthesis=SynthesisConfig(mode="rules"), learning_enabled=False),
    "B": dict(synthesis=SynthesisConfig(mode="evidence"), learning_enabled=False),
    "C": dict(synthesis=SynthesisConfig(mode="evidence"), learning_enabled=True),
    "R": dict(synthesis=SynthesisConfig(mode="random", random_trade_prob=0.03, seed=7), learning_enabled=False),
}


def one(name: str) -> dict:
    store = DataStore(ROOT / "data" / "processed", Holdout.load(ROOT / "research" / "holdout.json"))
    series = {s: store.load(s, "H1") for s in SYMBOLS}
    cfg = BacktestConfig(name=name, symbols=SYMBOLS, warmup_start=epoch(2007), start=epoch(2010), end=epoch(2017),
                         every=4, **VARIANTS[name])
    res = run(cfg, series, progress=lambda m: print(m, flush=True))
    out = ROOT / "data" / "results" / "PR-001"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.json").write_text(json.dumps(res, default=str))
    return {k: v for k, v in res.items() if k != "trades"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="")
    args = p.parse_args()
    names = [n for n in VARIANTS if not args.only or n in args.only.split(",")]
    with ProcessPoolExecutor(max_workers=min(4, len(names))) as pool:
        results = dict(zip(names, pool.map(one, names)))
    summary_path = ROOT / "research" / "results" / "PR-001-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    prev = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    prev.update({n: {k: r[k] for k in ("name", "counts", "metrics", "learning", "knowledge_version", "lessons",
                                       "loss_causes", "seeded_patterns", "final_patterns", "chains_ok", "seconds", "versions")}
                 for n, r in results.items()})
    for n in prev:
        prev[n]["metrics"]["equity"].pop("curve", None)
    summary_path.write_text(json.dumps(prev, indent=1, default=str))
    for n, r in results.items():
        o = r["metrics"]["overall"]
        print(n, o.get("n"), o.get("avg_R"), o.get("t"), r["metrics"]["equity"].get("max_drawdown_pct"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
