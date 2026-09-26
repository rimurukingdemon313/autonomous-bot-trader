"""Judge PR-001 by the rules pre-registered in
research/preregistrations/PR-001-multi-agent-ablation.md, and nothing else.

    python scripts/judge_pr001.py            # print the judgement, write research/results/PR-001-judgement.json
    python scripts/judge_pr001.py --record   # also append the verdicts to research/registry.jsonl

Committed before any judged-period result existed, so the reading of the
rules cannot have been chosen after seeing the numbers. Readings fixed here:

- R per trade is the realised R of every closed trade, after costs.
- A calendar year counts as positive only if it has at least one trade and
  its mean R is > 0; a year with no trades is not positive.
- Any comparison with fewer than 2 trades on either side cannot be computed
  and therefore FAILS; it never passes by default.
- The exploratory no-halt arm (Amendment 1) is summarised but produces no
  verdict.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.registry import Holdout, Registry, Verdict  # noqa: E402

RESULTS = ROOT / "data" / "results" / "PR-001"
YEARS = range(2010, 2017)
H1_T = 3.02
H1_VS_RANDOM_T = 2.0
SECONDARY_T = 2.24
MIN_TRADES = 200
MAX_DD_PCT = 25.0


def rs_of(res: dict) -> np.ndarray:
    return np.asarray([t["r"] for t in res["trades"] if t.get("r") is not None and math.isfinite(t["r"])], float)


def t_stat(x: np.ndarray) -> float | None:
    if len(x) < 2 or x.std(ddof=1) == 0:
        return None
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def welch(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 2 or len(b) < 2:
        return None
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else None


def year_means(res: dict) -> dict[int, dict]:
    out = {}
    for y in YEARS:
        x = np.asarray([t["r"] for t in res["trades"] if t.get("r") is not None
                        and datetime.fromtimestamp(t["opened"], timezone.utc).year == y], float)
        out[y] = {"n": int(len(x)), "mean_R": round(float(x.mean()), 4) if len(x) else None}
    return out


def describe(res: dict) -> dict:
    x = rs_of(res)
    m = res["metrics"]
    return {
        "trades": int(len(x)), "mean_R": round(float(x.mean()), 4) if len(x) else None,
        "t": round(t_stat(x), 3) if t_stat(x) is not None else None,
        "win_rate": m["overall"].get("win_rate"), "profit_factor_R": m["overall"].get("profit_factor_R"),
        "max_drawdown_pct": m["equity"].get("max_drawdown_pct"), "return_pct": m["equity"].get("return_pct"),
        "risk_rejected": res["counts"].get("risk_rejected"), "decisions": res["counts"].get("decisions"),
        "years": year_means(res), "chains_ok": res.get("chains_ok"),
    }


def comparison(name: str, a: np.ndarray, b: np.ndarray, threshold: float) -> dict:
    w = welch(a, b)
    diff = float(a.mean() - b.mean()) if len(a) and len(b) else None
    ok = w is not None and diff is not None and diff > 0 and w > threshold
    return {"test": name, "diff_mean_R": round(diff, 4) if diff is not None else None,
            "welch_t": round(w, 3) if w is not None else None, "threshold": threshold,
            "verdict": "PASS" if ok else "FAIL",
            "why": ("computed" if w is not None else "fewer than 2 trades on a side: cannot be computed, so FAIL")}


def judge(primary: dict[str, dict]) -> dict:
    r = {k: rs_of(v) for k, v in primary.items()}
    c = describe(primary["C"])
    pos_years = sum(1 for y in c["years"].values() if y["n"] > 0 and y["mean_R"] is not None and y["mean_R"] > 0)
    vs_r = comparison("C > R", r["C"], r["R"], H1_VS_RANDOM_T)
    conds = {
        "1_mean_R_positive_and_t_gt_3.02": bool(c["mean_R"] is not None and c["mean_R"] > 0
                                                and c["t"] is not None and c["t"] > H1_T),
        "2_C_beats_random_welch_gt_2.0": vs_r["verdict"] == "PASS",
        "3_positive_in_4_of_7_years": pos_years >= 4,
        "4_at_least_200_trades": c["trades"] >= MIN_TRADES,
        "5_max_drawdown_lt_25pct": bool(c["max_drawdown_pct"] is not None and abs(c["max_drawdown_pct"]) < MAX_DD_PCT),
    }
    h1 = {"verdict": "PASS" if all(conds.values()) else "FAIL", "conditions": conds,
          "positive_years": pos_years, "C_vs_R": vs_r}
    return {
        "H1_C_has_an_edge": h1,
        "H2_learning_adds_value": comparison("C > B", r["C"], r["B"], SECONDARY_T),
        "H3_memory_adds_value": comparison("B > A", r["B"], r["A"], SECONDARY_T),
        "H4_agents_beat_random": comparison("A > R", r["A"], r["R"], SECONDARY_T),
    }


def load(names) -> dict[str, dict]:
    out = {}
    for n in names:
        p = RESULTS / f"{n}.json"
        if p.exists():
            out[n] = json.loads(p.read_text())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args()
    primary = load("ABCR")
    missing = [n for n in "ABCR" if n not in primary]
    if missing:
        print(f"missing primary results: {missing}; nothing is judged on a partial run")
        return 1
    verdicts = judge(primary)
    explo = load([f"{n}-nohalt" for n in "ABCR"])
    out = {
        "preregistration": "research/preregistrations/PR-001-multi-agent-ablation.md",
        "judged": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "primary": {n: describe(v) for n, v in primary.items()},
        "verdicts": verdicts,
        "exploratory_nohalt": ({n: describe(v) for n, v in explo.items()} | (
            {"comparisons_no_verdict": {
                "C-B": comparison("C > B", rs_of(explo["C-nohalt"]), rs_of(explo["B-nohalt"]), SECONDARY_T),
                "B-A": comparison("B > A", rs_of(explo["B-nohalt"]), rs_of(explo["A-nohalt"]), SECONDARY_T),
                "A-R": comparison("A > R", rs_of(explo["A-nohalt"]), rs_of(explo["R-nohalt"]), SECONDARY_T),
                "C-R": comparison("C > R", rs_of(explo["C-nohalt"]), rs_of(explo["R-nohalt"]), SECONDARY_T),
            }} if len(explo) == 4 else {})) if explo else None,
    }
    path = ROOT / "research" / "results" / "PR-001-judgement.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps({"verdicts": verdicts, "C": out["primary"]["C"]}, indent=1))
    if args.record:
        reg = Registry.load(ROOT / "research" / "registry.jsonl", Holdout.load(ROOT / "research" / "holdout.json"))
        now = datetime.now(timezone.utc).replace(microsecond=0)
        h1 = verdicts["H1_C_has_an_edge"]["verdict"]
        reg.record_verdict(Verdict("PR-001-multi-agent-ablation", now, "PASSED" if h1 == "PASS" else "FAILED",
                                   {"H1": h1, "H2": verdicts["H2_learning_adds_value"]["verdict"],
                                    "H3": verdicts["H3_memory_adds_value"]["verdict"],
                                    "H4": verdicts["H4_agents_beat_random"]["verdict"],
                                    "C": {k: out["primary"]["C"][k] for k in ("trades", "mean_R", "t", "max_drawdown_pct")},
                                    "detail": "research/results/PR-001-judgement.json"}))
        if len(explo) == 4:
            reg.record_verdict(Verdict("PR-001x-nohalt-exploratory", now, "INCONCLUSIVE",
                                       {"note": "exploratory by design: no verdict",
                                        "detail": "research/results/PR-001-judgement.json"}))
        print("recorded in research/registry.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
