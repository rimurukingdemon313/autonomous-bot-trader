"""RADX-1: the funding radar's losses, diagnosed on its earlier positions and checked once on its later ones
(research/preregistrations/RADX-1.md).

    python scripts/radx1.py hash                      # the code hash the preregistration quotes
    python scripts/radx1.py preregister               # register RADX-1 in research/registry.jsonl (reads no ledger)
    python scripts/radx1.py judge LEDGER.json         # once: the pinned snapshot of radar-data's ledger.json

RADAR-1's own forward test is untouched: its code is not read here, its verdict is frozen by its own runner on
2026-12-06, and nothing in this script changes what the radar does. RADX-1 judges a diagnosis, not a remedy.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.perf import radx  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict  # noqa: E402

PID = "RADX-1"
DOC = "research/preregistrations/RADX-1.md"
OUT = ROOT / "research" / "knowledge" / "RADX-1.json"
CODE = ("aitrader/perf/radx.py", "aitrader/perf/stats.py", "scripts/radx1.py")
UNIVERSE = "crypto-perp-live-xvenue"
#: The later part: positions opened from the cut to the pinned snapshot.
WINDOW = ("2026-10-30", "2026-11-15")
#: The snapshot judged: ledger.json at commit 274a965 of the radar-data branch (marks to 2026-11-14 18:00 UTC).
SNAPSHOT = {"branch": "radar-data", "commit": "274a965", "last_mark": 1794679200}
#: sha256 of the snapshot's JSON, keys sorted: the judge refuses any other ledger.
SNAPSHOT_SHA256 = "e5685649f89f14cd8c1149f989b7f6c522240f270067f5971b0c034fa87edee1"
TESTS = 2  # P1 and P2
LABELS = {"PASSED": "DIAGNOSIS HOLDS OUT OF SAMPLE (no remedy is validated by this)",
          "FAILED": "DIAGNOSIS DOES NOT HOLD OUT OF SAMPLE"}


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def registry() -> Registry:
    return Registry.load(ROOT / "research" / "registry.jsonl")


def judge(ledger: dict, now: datetime, reg: Registry | None = None, out: Path = OUT) -> dict:
    """The one look. Refuses a second one, a changed code, and a ledger that is not the pinned snapshot."""
    reg = reg or registry()
    if reg.status_of(PID) != "PENDING":
        raise SystemExit(f"{PID} already has a verdict: it is looked at once")
    if reg.get(PID).design["code_sha256"] != code_hash():
        raise SystemExit("the code changed since registration: this would not be the registered test")
    raw = json.dumps(ledger, sort_keys=True).encode()
    if reg.get(PID).design["ledger_sha256"] != hashlib.sha256(raw).hexdigest():
        raise SystemExit("this is not the ledger snapshot named in the preregistration")
    res = radx.evaluate(ledger)
    body = {"program": PID, "kind": "diagnosis", "verdict": res["verdict"], "label": LABELS[res["verdict"]],
            "code_sha256": code_hash(), "ledger": {**SNAPSHOT, "sha256": hashlib.sha256(raw).hexdigest()},
            "judged": now.isoformat(), **res,
            "positions": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
                          for r in radx.classify(ledger["closed"])],
            "meaning": "the verdict is about where the radar's losses came from on positions opened after the cut. "
                       "It validates no change to the radar and no strategy."}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
    reg.record_verdict(Verdict(PID, now, res["verdict"], {
        "label": LABELS[res["verdict"]], "artifact": str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out),
        "gates": res["gates"], "later": {k: res["later"][k] for k in ("positions", "sum_bp", "mean_bp", "t")}}))
    return body


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "hash":
        print(code_hash())
        return 0
    if cmd == "preregister":
        h = code_hash()
        doc = (ROOT / DOC).read_text()
        if h not in doc or SNAPSHOT_SHA256 not in doc:
            raise SystemExit(f"{DOC} must quote the code sha256 {h} and the ledger sha256 {SNAPSHOT_SHA256}")
        registry().register(Trial(
            id=PID, registered=datetime.now(timezone.utc),
            title="RADX-1: the funding radar's losses are its thin entries and its churn after a decayed spread",
            hypothesis="On the radar's positions opened after 2026-10-30 11:00 UTC, those opened on a trailing spread "
                       "under 50%/yr lose on average, and so do those opened within six hours after the same coin's "
                       "previous position was closed for a decayed spread: each at t <= -3.0 and without its worst "
                       "coin. Stated from the positions opened before that hour.",
            uses=(Use(UNIVERSE, date.fromisoformat(WINDOW[0]), date.fromisoformat(WINDOW[1]), "judge"),),
            tests=TESTS, configurations=TESTS, preregistration=DOC,
            design={"code_sha256": h, "ledger_sha256": SNAPSHOT_SHA256, "ledger_commit": SNAPSHOT["commit"],
                    "cut": radx.CUT, "thin_apr": radx.THIN_APR, "churn_hours": radx.CHURN_H, "bar": radx.BAR}))
        print("registered", PID)
        return 0
    if cmd == "judge":
        body = judge(json.loads(Path(sys.argv[2]).read_text()), datetime.now(timezone.utc))
        print(PID, body["verdict"], json.dumps(body["gates"]))
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
