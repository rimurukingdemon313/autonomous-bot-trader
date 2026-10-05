"""EX-2: exploratory look at intraday momentum into the futures settlement, FX and gold, development only.

Recorded so the multiple-testing denominator is honest: 4 configurations were LOOKED AT on fx-majors
2007-2012 (gold from 2011) before IX-1 was preregistered. Signal: mid return from the previous settlement to
30 minutes before today's (FX: CME 15:00 New York; gold: COMEX 13:30 New York); trade its direction for
the last 30 minutes at the real bid/ask of the M15 bars, plus 0.7 pip commission and 0.1 pip slippage per
fill. Variants: every day, and |signal| > 1 standard deviation of the previous 60 signals.

    python scripts/ex2_close_momentum.py     # writes research/results/EX-2.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from ex1_fx_session import P, summarize, trade_cost_and_pnl  # noqa: E402

NY = ZoneInfo("America/New_York")
FX = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "EURGBP",
      "EURCHF"]


def ep(d, hm) -> int:
    return int(datetime.combine(d, hm, tzinfo=NY).astimezone(timezone.utc).timestamp())


def main() -> int:
    res = {}
    for syms, close, lab in [(FX, time(15, 0), "FX into CME settle 15:00 ET"),
                             (["XAUUSD"], time(13, 30), "Gold into COMEX close 13:30 ET")]:
        for zmin in (0.0, 1.0):
            rows = []
            for s in syms:
                p = P(s)
                prev, hist = None, []
                d = datetime.fromtimestamp(int(p.t[0]), timezone.utc).date()
                d1 = datetime.fromtimestamp(int(p.t[-1]), timezone.utc).date()
                while d <= d1:
                    if d.weekday() < 5:
                        c = ep(d, close)
                        i, j = p.at(c - 1800), p.at(c)
                        if i >= 0 and j >= 0:
                            if prev is not None:
                                sig = p.mo[i] / prev - 1
                                if len(hist) >= 60 and sig != 0 and abs(sig) > zmin * np.std(hist[-60:]):
                                    g, n, _ = trade_cost_and_pnl(p, i, j, 1 if sig > 0 else -1)
                                    rows.append((c // 86400, s, g, n))
                                hist.append(sig)
                            prev = p.mo[j]
                        else:
                            prev = None
                    d += timedelta(days=1)
            res[f"{lab} z>{zmin}"] = summarize(rows, f"{lab} z>{zmin}")
    out = {"program": "EX-2", "period": ["2007-03-30", "2013-01-01"], "results": res, "configurations": len(res)}
    (ROOT / "research" / "results" / "EX-2.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
