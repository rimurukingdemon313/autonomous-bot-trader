"""Round 3: genuine interest-rate information and carry. Frozen before any rate data beyond EUR exists here.

    python scripts/round3.py status        # rate coverage per currency and whether Round 3 may run
    python scripts/round3.py freeze        # write research/specs/R3.json (the frozen design) -- done once
    python scripts/round3.py draft         # (only when the coverage gate passes) catalog + leakage + DRAFTs
    python scripts/round3.py preregister   # registry trial; threshold from the registry at that moment
    python scripts/round3.py run           # once

The design below (SPEC) was committed BEFORE any Round 3 outcome could be computed: the rates it
needs are not reachable in this environment (docs/ROUND3_PREREGISTRATION.md). Every later command
verifies that the design it runs is byte-for-byte the frozen one (its sha256), so nothing can be
tuned once data arrives. Pairs are included or excluded by coverage alone, decided before any outcome
is read; the gate needs at least MIN_PAIRS pairs with both currencies covered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aitrader.data.rates import RateStore, coverage  # noqa: E402
from aitrader.research.registry import Holdout, Registry  # noqa: E402

R = ROOT / "research"
SPEC_PATH = R / "specs" / "R3.json"
FX = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF",
      "AUDJPY")
MIN_PAIRS = 6

SPEC = {
    "id": "R3",
    "title": "Genuine interest-rate information and FX carry",
    "question": "Does point-in-time interest-rate information (the level, change, acceleration of the policy-rate "
                "differential, and policy moves) improve directional prediction on the FX pairs, and does carry "
                "(spot + RATE-DIFFERENTIAL CARRY PROXY - financing - costs) have positive net expectancy?",
    "rate_type": "POLICY",
    "rate_type_rule": "policy rates only (central-bank target/official rates; not revised). If the data obtained is "
                      "not policy rates, Round 3 is re-preregistered as a new version; the type is never switched "
                      "silently, and two rate types are never mixed within a pair.",
    "universe_rule": f"every pair of the 12 whose BOTH currencies have policy-rate coverage over the whole judged "
                     f"period; decided from coverage alone before any outcome is read; at least {MIN_PAIRS} pairs "
                     f"or Round 3 does not run",
    "fit": ["2007-04-02", "2008-07-01"], "judge": ["2008-07-11", "2017-01-01"],
    "fit_use": "regime medians for the battery only; every condition is a fixed-level state, nothing is fitted",
    "exit": "D4 (20 trading days, 3 ATR protective stop): carry is a monthly-horizon premium",
    "costs": {"spread": "measured bid/ask", "slippage_pips": 0.1, "commission_pips_rt": 0.7,
              "swap": "NOT charged: replaced by the carry proxy and the financing markup",
              "carry": "RATE-DIFFERENTIAL CARRY PROXY: side x differential in force each day x days/365 x price/risk",
              "financing_markup_pct_per_year": 0.5,
              "sensitivity": "costs lower/normal/higher; markup 0 / 0.5 / 1.0"},
    "hypotheses": [
        {"id": "R3-A", "condition": "rate_level=high", "side": "BUY",
         "claim": "buying a pair whose base out-yields its quote by >= 1pp (carry long) has positive net expectancy",
         "rationale": "the forward-premium anomaly (Fama 1984) and the carry premium (Lustig & Verdelhan 2007)"},
        {"id": "R3-B", "condition": "rate_level=low", "side": "SELL",
         "claim": "selling a pair whose quote out-yields its base by >= 1pp (carry long via the quote) has positive "
                  "net expectancy", "rationale": "the mirror of R3-A"},
        {"id": "R3-C", "condition": "rate_change=high", "side": "BUY",
         "claim": "after the differential widened >= 0.25pp in the base's favour over 91 days, buying has positive "
                  "net expectancy", "rationale": "capital follows a widening differential slowly (Engel 1996)"},
        {"id": "R3-D", "condition": "rate_change=low", "side": "SELL",
         "claim": "after the differential narrowed >= 0.25pp over 91 days, selling has positive net expectancy",
         "rationale": "the mirror of R3-C"},
        {"id": "R3-E", "condition": "rate_accel=high", "side": "BUY",
         "claim": "when the widening of the differential accelerates (>= 0.25pp), buying has positive net "
                  "expectancy", "rationale": "an accelerating policy divergence is repriced slowly (inferred)"},
        {"id": "R3-F", "condition": "policy_move=high", "side": "BUY",
         "claim": "after a policy move in the base's favour within 30 days (base hike or quote cut, >= 0.10pp), "
                  "buying has positive net expectancy",
         "rationale": "policy surprises are absorbed over weeks (post-announcement drift; inferred from Engel 1996)"},
        {"id": "R3-G", "condition": "rate_level=high&vix_state=low", "side": "BUY",
         "claim": "carry long (>= 1pp) only while VIX < 20 has positive net expectancy",
         "rationale": "carry crashes in risk-off (Brunnermeier, Nagel & Pedersen 2008; Menkhoff et al. 2012)"},
        {"id": "R3-H", "condition": "rate_level=high&policy_move=mid", "side": "BUY",
         "claim": "carry long (>= 1pp) only when neither central bank moved in the last 30 days has positive net "
                  "expectancy", "rationale": "event filter: carry is exposed to repricing around policy decisions"},
    ],
    "not_repeated": {"R2A-1/R2A-2": "static carry SIGN on 3 pairs conditioned on VIX: Round 3 uses the measured "
                                    "differential on every covered pair", "R2B": "US 10y change only: Round 3 uses "
                                    "the two-sided policy differential"},
    "comparisons": {"random_direction": "the battery's random-entry baseline (Welch t >= 2 required)",
                    "price_only": "the spot component of the same trades, reported beside the combined R",
                    "previously_rejected": "R2A-1 (-0.119R) and CP-001 (trend) for reference"},
    "report": ["P(direction correct)", "gross R", "carry R", "spot R", "costs", "financing", "net R", "MFE", "MAE",
               "holding", "by instrument", "by year", "by VIX regime"],
    "pass": "the existing 12-check battery at the registry's frozen threshold, then the board; PROMISING / "
            "UNCERTAIN / REJECTED otherwise (aitrader/research/discovery/edges.py)",
}


def spec_sha256(spec: dict = SPEC) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def frozen() -> dict:
    stored = json.loads(SPEC_PATH.read_text())
    if stored["sha256"] != spec_sha256(stored["spec"]) or stored["spec"] != SPEC:
        raise SystemExit("the Round 3 design differs from the frozen one; a change needs a new preregistered version")
    return stored["spec"]


#: published policy rates in force on these dates (single-value targets only; the Fed and the SNB set
#: ranges, whose BIS representation is checked for plausibility instead). A file that disagrees is refused.
KNOWN_POLICY = (("AUD", "2008-07-01", 7.25), ("NZD", "2008-07-01", 8.25), ("EUR", "2012-01-02", 1.00),
                ("GBP", "2010-01-04", 0.50), ("JPY", "2010-01-04", 0.10), ("CAD", "2010-01-04", 0.25))
PLAUSIBLE = (("USD", "2012-01-03", 0.0, 0.25), ("CHF", "2012-01-03", 0.0, 0.25))


def validate(rates: dict) -> list[str]:
    """Known published values and plausibility ranges; the list of failures (empty = passed)."""
    bad = []

    def at(ccy, day):
        s = rates.get((ccy, "POLICY"))
        if s is None:
            return None
        t = int(datetime.fromisoformat(day).replace(hour=23, tzinfo=timezone.utc).timestamp())
        return float(s.asof([t])[0])

    for ccy, day, want in KNOWN_POLICY:
        got = at(ccy, day)
        if got is not None and abs(got - want) > 0.005:
            bad.append(f"{ccy} {day}: file {got} vs published {want}")
    for ccy, day, lo, hi in PLAUSIBLE:
        got = at(ccy, day)
        if got is not None and not lo <= got <= hi:
            bad.append(f"{ccy} {day}: file {got} outside [{lo}, {hi}]")
    return bad


def gate(holdout) -> tuple[list[str], dict]:
    rates = RateStore(ROOT / "data" / "rates", holdout).load()
    failures = validate(rates)
    if failures:
        raise SystemExit("the rate file fails validation against published values: " + "; ".join(failures))
    j0, j1 = (date.fromisoformat(x) for x in SPEC["judge"])
    cov = coverage(rates, date.fromisoformat(SPEC["fit"][0]), j1)
    ok = {c for c, v in cov.items() if v["types"].get(SPEC["rate_type"], {}).get("covers_period")}
    pairs = [p for p in FX if p[:3] in ok and p[3:] in ok]
    return pairs, cov


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("status", "freeze", "draft", "preregister", "run"))
    a = ap.parse_args()
    holdout = Holdout.load(R / "holdout.json")
    if a.cmd == "freeze":
        if SPEC_PATH.exists():
            raise SystemExit("already frozen")
        SPEC_PATH.write_text(json.dumps({"spec": SPEC, "sha256": spec_sha256(),
                                         "frozen": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                                        indent=1, sort_keys=True) + "\n")
        print("frozen", spec_sha256())
        return 0
    frozen()
    pairs, cov = gate(holdout)
    if a.cmd == "status":
        print(json.dumps({c: {"status": v["status"], "types": {k: {x: y for x, y in t.items() if x != "source"}
                                                                for k, t in v["types"].items()}}
                          for c, v in cov.items()}, indent=1))
        print(f"pairs with {SPEC['rate_type']} coverage on both sides: {pairs or 'none'}; gate needs {MIN_PAIRS}")
        return 0
    if len(pairs) < MIN_PAIRS:
        raise SystemExit(f"Round 3 cannot run: {len(pairs)} pair(s) have {SPEC['rate_type']} rates for both "
                         f"currencies ({pairs}); the frozen design needs {MIN_PAIRS}. Nothing is substituted.")
    raise SystemExit("coverage is sufficient: implement the draft/preregister/run steps against the frozen spec "
                     "(scripts/round2.py is the template) and commit before running")


if __name__ == "__main__":
    raise SystemExit(main())
