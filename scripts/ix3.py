"""IX-3: the overnight drift of US equity-index CFDs at the European cash open, judged once
(research/preregistrations/IX-3.md).

    python scripts/ix3.py spec | preregister | run | holdout

Rule (aitrader/research/discovery/ixdrift.py): long at 09:00 Frankfurt, out one hour later; variant COND
only after a US session whose last hour fell. Data, loader, gates and cost conventions are IX-2's
(scripts/ix2.py, imported, not modified).
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import ix2  # noqa: E402
from aitrader.research.discovery import ixdrift as D  # noqa: E402
from aitrader.research.discovery import ixmom as IX  # noqa: E402
from aitrader.research.registry import Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402

PID, HID = "IX-3", "IX-3-H"
R = ROOT / "research"
DOC = "research/preregistrations/IX-3.md"
SPEC = R / "specs" / "IX-3.json"
OUT = R / "knowledge" / "IX-3.json"
HOUT = R / "knowledge" / "IX-3-H.json"
CODE = ("aitrader/research/discovery/ixdrift.py", "aitrader/research/discovery/ixmom.py", "scripts/ix2.py",
        "scripts/ix3.py")
SYMBOLS = ["USA500IDXUSD", "USATECHIDXUSD", "USA30IDXUSD"]
JUDGE, HOLD = ix2.JUDGE, ix2.HOLD
VARIANTS = {"ALL": False, "COND": True}
HOLD_H = 1


def code_hash() -> str:
    h = hashlib.sha256()
    for f in CODE:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()


def tests() -> list[str]:
    return [f"DRIFT-{v}" for v in VARIANTS]


def spec(reg: Registry) -> dict:
    t_req = round(max(3.0, bonferroni_t(sum(t.tests for t in reg.trials) + len(tests()))), 4)
    return {"program": PID, "version": D.IXD_VERSION, "universe": ix2.UNIVERSE, "symbols": SYMBOLS,
            "entry": [D.ENTRY_TZ, D.ENTRY_AT.isoformat()], "hold_hours": HOLD_H,
            "condition": "previous US session 15:00 -> 16:00 New York mid change < 0", "judge": list(JUDGE),
            "holdout": list(HOLD), "variants": VARIANTS, "vol_days": ix2.VOL_DAYS, "stop_sd": ix2.STOP_SD,
            "slip_spread_fraction": ix2.SLIP_SPREAD_FRACTION, "gates": {**ix2.GATES, "min_trades": 300},
            "late_entry": "entry at the typical price (O+H+L+C)/4 of the entry hour plus half its opening spread",
            "tests": tests(), "t_required": t_req, "code_sha256": code_hash()}


def late(ts: list[IX.Trade], b: IX.Bars, bc, ac, slip: float) -> list[IX.Trade]:
    idx = b.index()
    out = []
    for x in ts:
        i = idx[D.entry_epoch(x.day)]
        typ = ((b.bo[i] + b.bh[i] + b.bl[i] + bc[i]) / 4 + (b.ao[i] + b.ah[i] + b.al[i] + ac[i]) / 4) / 2
        entry = typ + (b.ao[i] - b.bo[i]) / 2 + slip
        mid_in = (b.bo[i] + b.ao[i]) / 2
        net = (x.exit - entry) / mid_in * 1e4
        out.append(replace(x, entry=float(entry), net_bps=float(net), cost_bps=float(x.gross_bps - net),
                           r=float((x.exit - entry) / abs(x.entry - x.stop))))
    return out


def evaluate(period, t_req: float) -> dict:
    data = {s: ix2.load(s, period) for s in SYMBOLS}
    slips = {s: ix2.slip_for(d[0]) for s, d in data.items()}
    res = {}
    for v, cond in VARIANTS.items():
        def run(**kw):
            out = []
            for s, (b, _, _) in data.items():
                out += D.trades(b, hold_h=HOLD_H, conditional=cond, slip_pts=slips[s], vol_days=ix2.VOL_DAYS,
                                stop_sd=ix2.STOP_SD, **kw)
            return out
        base = run()
        lt = []
        for s, (b, bc, ac) in data.items():
            lt += late([x for x in base if x.symbol == s], b, bc, ac, slips[s])
        res[f"DRIFT-{v}"] = {"period": list(period), "slippage_pts": slips,
                             **ix2.judge(base, {"x1.5": run(cost_mult=1.5), "x2": run(cost_mult=2.0), "late": lt}, t_req)}
        print(f"DRIFT-{v}: {res[f'DRIFT-{v}']['summary']}\n   failed: {res[f'DRIFT-{v}']['failed']}", flush=True)
    return res


def _frozen() -> dict:
    f = json.loads(SPEC.read_text())
    if ix2.spec_sha(f["spec"]) != f["sha256"] or f["spec"]["code_sha256"] != code_hash():
        raise SystemExit("spec or code changed after freezing")
    return f


def main(cmd: str) -> int:
    reg = Registry.load(R / "registry.jsonl")
    if cmd == "spec":
        s = spec(reg)
        SPEC.write_text(json.dumps({"spec": s, "sha256": ix2.spec_sha(s)}, indent=1, default=str) + "\n")
        print("spec", ix2.spec_sha(s), "t_required", s["t_required"])
        return 0
    f = _frozen()
    if cmd == "preregister":
        if f["sha256"] not in (ROOT / DOC).read_text():
            raise SystemExit(f"{DOC} must quote {f['sha256']}")
        reg.register(Trial(id=PID, registered=datetime.now(timezone.utc),
                           title="IX-3: overnight drift of US index CFDs at the European cash open",
                           hypothesis="US index CFDs rise in the hour after the Xetra open (dealer inventory "
                                      "compensation), more so after a falling US last hour, after real costs.",
                           uses=(Use(ix2.UNIVERSE, date.fromisoformat(JUDGE[0]), date.fromisoformat(JUDGE[1]), "judge"),),
                           tests=len(f["spec"]["tests"]), configurations=len(f["spec"]["tests"]), preregistration=DOC,
                           design={"spec_sha256": f["sha256"], "code_sha256": code_hash(),
                                   "threshold_t": f["spec"]["t_required"]}))
        print("registered", PID)
        return 0
    if cmd == "run":
        if reg.status_of(PID) != "PENDING":
            raise SystemExit("judged once")
        res = evaluate(JUDGE, f["spec"]["t_required"])
        passers = [k for k, v in res.items() if v["passed"]]
        out = {"program": PID, "spec_sha256": f["sha256"], "results": res, "passers": passers,
               "verdict": "PASSED" if passers else "FAILED", "ai_component": "none (Track A only)"}
        OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
        reg.record_verdict(Verdict(PID, datetime.now(timezone.utc), out["verdict"],
                                   {"passers": passers, "failed": {k: v["failed"] for k, v in res.items()},
                                    "net_bps": {k: v["summary"].get("net_bps") for k, v in res.items()},
                                    "t_day": {k: v["summary"].get("t_day") for k, v in res.items()}}))
        print("verdict", out["verdict"], passers)
        return 0
    if cmd == "holdout":
        v = reg.verdict_of(PID)
        if v is None or v.status != "PASSED":
            raise SystemExit("holdout only for passers")
        passers = v.result["passers"]
        if HID not in [t.id for t in reg.trials]:
            reg.register(Trial(id=HID, registered=datetime.now(timezone.utc), title="IX-3 holdout 2021-2024",
                               hypothesis="IX-3 passers hold on 2021-2024",
                               uses=(Use(ix2.UNIVERSE, date.fromisoformat(HOLD[0]), date.fromisoformat(HOLD[1]), "judge"),),
                               tests=len(passers), configurations=len(passers), preregistration=DOC))
        elif reg.status_of(HID) != "PENDING":
            raise SystemExit("the holdout was already judged")
        t_req = round(bonferroni_t(len(passers)), 4)
        res = {k: r for k, r in evaluate(HOLD, t_req).items() if k in passers}
        ok = [k for k, r in res.items() if r["summary"].get("net_bps", -1) > 0 and (r["summary"].get("t_day") or 0) >= t_req
              and r["gates"]["costs_x1.5"] and r["gates"]["late_entry"]]
        out = {"program": HID, "t_required": t_req, "results": res, "passers": ok, "verdict": "PASSED" if ok else "FAILED"}
        HOUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
        reg.record_verdict(Verdict(HID, datetime.now(timezone.utc), out["verdict"], {"passers": ok}))
        print("holdout verdict", out["verdict"], ok)
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) == 2 else ""))
