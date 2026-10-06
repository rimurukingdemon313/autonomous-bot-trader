"""FT-1: does IX-2's last-hour index momentum pay today's CFD spreads? Judged once on 2025-01 → 2026-09
(research/preregistrations/FT-1.md).

    python scripts/ft1.py spec          # freeze the design (writes research/specs/FT-1.json)
    python scripts/ft1.py preregister   # register the trial (after the document quotes the spec hash)
    python scripts/ft1.py run           # judged once -> gates -> tier -> report (refuses a second run)

The rule, the stress tests and the gates are IX-2's, imported unchanged from scripts/ix2.py (frozen by
IX-2's code hash). Only the period and the data directory differ. The 2021-2024 index-CFD holdout is
neither fetched nor read: the bars here start on 2025-01-01, so the first 60 trading days of 2025 build
the volatility estimates.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import ix2 as IX2  # noqa: E402
from aitrader.research.discovery import ixmom as IX  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID = "FT-1"
R = ROOT / "research"
DOC = "research/preregistrations/FT-1.md"
SPEC = R / "specs" / "FT-1.json"
OUT = R / "knowledge" / "FT-1.json"
CODE = ("aitrader/research/discovery/ixmom.py", "scripts/ix2.py", "scripts/ft1.py")
DATA = ROOT / "data" / "ft1"
JUDGE = ("2025-01-01", "2026-10-01")
US = ("USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD")
#: Labels, decided now. PROMISING never means validated: it only admits the rule to the paper forward test.
TIERS = {
    "PASSED": "every IX-2 gate, t_day >= the Bonferroni threshold",
    "PROMISING": "net > 0, costs x1.5 > 0, late entry > 0, >= 300 trades and t_day >= 2.0, but not PASSED",
    "FAILED": "anything else",
}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def registry() -> Registry:
    return Registry.load(R / "registry.jsonl")


def spec(reg: Registry) -> dict:
    return {"program": PID, "rule": "IX-2 unchanged (ixmom " + IX.IX_VERSION + ", scripts/ix2.py)",
            "symbols": IX2.SYMBOLS, "judge": list(JUDGE), "variants": IX2.VARIANTS, "offset_min": IX2.OFFSET_MIN,
            "vol_days": IX2.VOL_DAYS, "stop_sd": IX2.STOP_SD, "slip_spread_fraction": IX2.SLIP_SPREAD_FRACTION,
            "bars": "H1 bid/ask, Dukascopy hour candles 2025-01 onward (scripts/ingest_dukascopy_candles.py --hourly)",
            "gates": IX2.GATES, "tiers": TIERS, "reported_not_gated": ["US-only subset", "spread by symbol"],
            "tests": IX2.tests(), "t_required": IX2.threshold(reg), "code_sha256": code_hash()}


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if IX2.spec_sha(f["spec"]) != f["sha256"]:
        raise SystemExit("spec hash mismatch")
    if f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("code changed after the spec was frozen")
    return f


def tier(r: dict) -> str:
    if r["passed"]:
        return "PASSED"
    s, g = r["summary"], r["gates"]
    ok = (s.get("trades", 0) >= IX2.GATES["min_trades"] and s.get("net_bps", -1) > 0 and g.get("costs_x1.5")
          and g.get("late_entry") and (s.get("t_day") or 0) >= 2.0)
    return "PROMISING" if ok else "FAILED"


def spreads(period: tuple[str, str]) -> dict:
    """Median quoted spread at the entry bar, in bp of the mid: the cost the hypothesis is about."""
    out = {}
    for s in IX2.SYMBOLS:
        b, _, _ = IX2.load(s, period)
        out[s] = round(float(np.median((b.ao - b.bo) / ((b.ao + b.bo) / 2)) * 1e4), 3)
    return out


def cmd_spec() -> int:
    s = spec(registry())
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps({"spec": s, "sha256": IX2.spec_sha(s)}, indent=1, default=str) + "\n")
    print("spec", IX2.spec_sha(s), "t_required", s["t_required"], "tests", s["tests"])
    return 0


def cmd_preregister() -> int:
    f = _frozen()
    if f["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {f['sha256']}")
    reg = registry()
    reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                       title="FT-1: IX-2 last-hour index momentum at 2025-2026 CFD spreads",
                       hypothesis="Index-CFD spreads have narrowed since 2012-2020, so IX-2's unchanged rule, whose "
                                  "gross edge was smaller than the old spread, is net positive at today's quoted costs.",
                       uses=(Use(IX2.UNIVERSE, date.fromisoformat(JUDGE[0]), date.fromisoformat(JUDGE[1]), "judge"),),
                       tests=len(f["spec"]["tests"]), configurations=len(f["spec"]["tests"]), preregistration=DOC,
                       design={"spec_sha256": f["sha256"], "code_sha256": code_hash(),
                               "threshold_t": f["spec"]["t_required"]}))
    print("registered", PID)
    return 0


def cmd_run() -> int:
    f = _frozen()
    reg = registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict: it is judged once")
    IX2.DATA = DATA
    res = IX2.evaluate(JUDGE, f["spec"]["t_required"])
    for k, r in res.items():
        r["tier"] = tier(r)
        us = {s: v for s, v in r["summary"]["by_symbol"].items() if s in US}
        n = sum(v["trades"] for v in us.values())
        r["us_only_reported_not_gated"] = {"trades": n, "net_bps": round(sum(v["trades"] * v["net_bps"]
                                           for v in us.values()) / n, 3) if n else None}
    tiers = {k: r["tier"] for k, r in res.items()}
    verdict = "PASSED" if "PASSED" in tiers.values() else "PROMISING" if "PROMISING" in tiers.values() else "FAILED"
    out = {"program": PID, "spec_sha256": f["sha256"], "code_sha256": code_hash(), "t_required": f["spec"]["t_required"],
           "spread_bps_median": spreads(JUDGE), "results": res, "tiers": tiers, "verdict": verdict,
           "ai_component": "none: a deterministic rule"}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    status = {"PASSED": "PASSED", "PROMISING": "INCONCLUSIVE"}.get(verdict, "FAILED")
    reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), status,
                               {"tiers": tiers, "failed": {k: v["failed"] for k, v in res.items()},
                                "net_bps": {k: v["summary"].get("net_bps") for k, v in res.items()},
                                "t_day": {k: v["summary"].get("t_day") for k, v in res.items()}}))
    print("verdict", verdict, tiers)
    return 0


if __name__ == "__main__":
    cmds = {"spec": cmd_spec, "preregister": cmd_preregister, "run": cmd_run}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    raise SystemExit(cmds[sys.argv[1]]())
