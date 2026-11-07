"""Descriptive only, computed after TRND-1's verdict from the data it judged: how its rule would have fared against
a funded account's rules (FUNDED-P's own engine, scripts/funded_paper.py), started on the first trading day of every
month. It is not a test and changes no verdict; the past is not a forecast.

    python scripts/trnd1_funded_sim.py <the TRND-1 data folder>   # -> research/results/TRND-1-funded.json
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.funded_paper as P  # noqa: E402
import scripts.trnd1 as T  # noqa: E402

OUT = ROOT / "research" / "results" / "TRND-1-funded.json"
SWAP = 0.065  # an illustrative yearly swap on the position, as a non-Islamic CFD account charges


def outcome(r: dict) -> dict:
    ev = " ".join(e["event"] for e in r["events"])
    p1 = "PASS" if "PHASE 1 PASSED" in ev else "FAIL" if "FAILED in phase 1" in ev else "UNRESOLVED"
    days1 = sum(1 for h in r["history"] if h["phase"] == 1)
    both = "PHASE 2 PASSED" in ev
    return {"phase1": p1, "days_in_phase1": days1, "funded": both}


def failures_by_year(runs: list[dict]) -> dict[str, int]:
    """In which year each failed start failed, whatever its phase."""
    out: dict[str, int] = {}
    for r in runs:
        if r["status"] == "FAILED":
            y = r["events"][-1]["date"][:4]
            out[y] = out.get(y, 0) + 1
    return dict(sorted(out.items()))


def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    # (each run continues to the data's end; `alive_at_end` counts the runs no limit had ended by then)
    passed = sorted(x["days_in_phase1"] for x in rows if x["phase1"] == "PASS")
    return {"starts": n, "phase1_passed": sum(x["phase1"] == "PASS" for x in rows),
            "phase1_failed": sum(x["phase1"] == "FAIL" for x in rows),
            "phase1_unresolved": sum(x["phase1"] == "UNRESOLVED" for x in rows),
            "reached_funded": sum(x["funded"] for x in rows),
            "median_trading_days_to_pass_phase1": passed[len(passed) // 2] if passed else None}


def main() -> int:
    T.DATA = Path(sys.argv[1])
    spx = T.load((T.JUDGED_INDEX,), T.FIRST, T.JUDGE[1])
    four = T.load(T.HOLDOUT_INDICES, T.WARMUP_FROM, T.HOLD[1])
    report = {"note": "descriptive, after the verdict, on data TRND-1 already judged; not a test", "runs": {}}
    for label, data, months, until in (
            ("S&P 500 1929-1989", spx, [date(y, m, 1) for y in range(1929, 1990) for m in range(1, 13)],
             date(1989, 12, 31)),
            ("four index CFDs 2021-2026", four, [date(y, m, 1) for y in range(2021, 2027) for m in range(1, 13)
                                                 if date(y, m, 1) < T.HOLD[1]], date(2026, 9, 30))):
        variants = {name: (tr["expo"], tr["stop"]) for name, tr in P.TRACKS.items()}
        variants["HALF without its stop"] = (P.TRACKS["HALF"]["expo"], None)  # the comparison
        for name, (expo, stop) in variants.items():
            for swap in (0.0, SWAP):
                runs = [P.run(data, expo, start=m0, until=until, swap_pa=swap, stop=stop) for m0 in months]
                key = f"{label}, {name}" + ("" if swap == 0 else f", with a {SWAP:.1%} yearly swap")
                report["runs"][key] = summarise([outcome(r) for r in runs])
                report["runs"][key]["failures_by_year"] = failures_by_year(runs)
                report["runs"][key]["alive_at_end"] = sum(r["status"] != "FAILED" for r in runs)
                report["runs"][key]["stops_hit_median"] = sorted(r["stops"] for r in runs)[len(runs) // 2]
                print(key, json.dumps(report["runs"][key]))
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
