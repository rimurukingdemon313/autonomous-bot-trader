"""EX-1: exploratory screen of FX session/order-flow families on development data only (2007-03 to 2012).

Recorded so the multiple-testing denominator is honest: every configuration below was LOOKED AT, and the
registry counts them as tests on fx-majors 2007-2012 (role "select"). Nothing here is a verdict on unseen
data. Every trade is priced at the real bid/ask of the M15 bar it enters and exits on, plus 0.7 pip
commission and 0.1 pip slippage per fill; t is computed on daily sums across instruments.

Families (economic reason in brackets):
- E1: Asian-session USD drift, and reversal of the illiquid 20:00-01:00 UTC move [temporary price pressure
  in thin markets reverts when liquidity returns: Grossman-Miller]
- F4: intraday session momentum / reversal [Elaut et al. 2018 intraday momentum in FX]
- F1: activity-conditioned continuation (high tick activity) / reversal (low) [Llorente et al. 2002]

    python scripts/ex1_fx_session.py        # writes research/results/EX-1.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.data import instruments  # noqa: E402
from aitrader.data.store import DataStore  # noqa: E402
from aitrader.research.registry import Holdout  # noqa: E402

DEV_END = 1356998400  # 2013-01-01 UTC
COMM_PIPS, SLIP_PIPS = 0.7, 0.1
H = 3600
ALL = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "EURJPY", "GBPJPY", "AUDJPY",
       "EURGBP", "EURCHF", "XAUUSD"]
USD_LEGS = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "NZDUSD": -1, "USDCAD": 1, "USDCHF": 1, "USDJPY": 1}
DS = DataStore(ROOT / "data" / "processed", Holdout.load(ROOT / "research" / "holdout.json"))


class P:
    def __init__(s, sym, end=DEV_END, start=0):
        b=DS.load(sym); m=(b.open_time<end)&(b.open_time>=start)
        s.sym=sym; s.pip=instruments.get(sym).pip
        s.t=b.open_time[m]; s.bo=b.bid_open[m]; s.ao=b.ask_open[m]; s.bc=b.bid_close[m]; s.ac=b.ask_close[m]
        s.mo=(s.bo+s.ao)/2; s.mc=(s.bc+s.ac)/2; s.ticks=b.ticks[m]
        s.idx={int(x):i for i,x in enumerate(s.t)}
    def at(s, t):
        """index of the bar opening exactly at t (or -1)"""
        return s.idx.get(int(t),-1)

def trade_cost_and_pnl(p, i_in, i_out, side):
    """Enter at the open of bar i_in, exit at the open of bar i_out (both real quotes).
    Returns gross (mid-to-mid) bps, net bps, cost bps."""
    mid_in=p.mo[i_in]; mid_out=p.mo[i_out]
    if side>0: px_in=p.ao[i_in]+SLIP_PIPS*p.pip; px_out=p.bo[i_out]-SLIP_PIPS*p.pip
    else:      px_in=p.bo[i_in]-SLIP_PIPS*p.pip; px_out=p.ao[i_out]+SLIP_PIPS*p.pip
    gross=side*(mid_out-mid_in)/mid_in*1e4
    net=side*(px_out-px_in)/mid_in*1e4 - COMM_PIPS*p.pip/mid_in*1e4
    return gross, net, gross-net

def summarize(rows, label=""):
    """rows: list of (day, sym, gross, net). t on daily sums (cross-instrument dependence)."""
    if not rows: print(label, "no trades"); return None
    a=np.array([(r[0],r[2],r[3]) for r in rows])
    days=np.unique(a[:,0]); dn=np.array([a[a[:,0]==d,2].sum() for d in days])
    n=len(a); g=a[:,1].mean(); ne=a[:,2].mean()
    t=dn.mean()/dn.std(ddof=1)*np.sqrt(len(dn)) if len(dn)>2 else np.nan
    yrs={}
    for d,x in zip(days,dn): yrs.setdefault(int(1970+d//365.2425),[]).append(x)
    ys=" ".join(f"{y}:{np.sum(v):+.0f}" for y,v in sorted(yrs.items()))
    print(f"{label:38} n={n:6d} gross={g:+6.2f}bp cost={g-ne:5.2f}bp net={ne:+6.2f}bp tday={t:+5.2f} | {ys}", flush=True)
    return dict(n=int(n), gross_bps=round(float(g), 3), cost_bps=round(float(g - ne), 3), net_bps=round(float(ne), 3),
                t_day=round(float(t), 3), by_year_bps={y: round(float(np.sum(v)), 1) for y, v in sorted(yrs.items())})


def family_e1(PS):
    out = {}
    for (h_in, h_out, usd_side, lab) in [(1, 4, -1, "E1 short USD 01->04"), (1, 3, -1, "E1 short USD 01->03"),
                                         (20, 23, +1, "E1 long USD 20->23")]:
        rows = []
        for s, sg in USD_LEGS.items():
            p = PS[s]
            for d in np.unique(p.t // 86400):
                i = p.at(d * 86400 + h_in * H); j = p.at(d * 86400 + h_out * H)
                if i < 0 or j < 0:
                    continue
                g, n, _ = trade_cost_and_pnl(p, i, j, sg * usd_side)
                rows.append((d, s, g, n))
        out[lab] = summarize(rows, lab)
    for k in (0.0, 0.5, 1.0, 1.5):
        rows = []
        for s in ALL:
            p = PS[s]; cand = []
            for d in np.unique(p.t // 86400):
                a = p.at((d - 1) * 86400 + 20 * H); i = p.at(d * 86400 + 1 * H); j = p.at(d * 86400 + 4 * H)
                if a < 0 or i < 0 or j < 0:
                    continue
                cand.append((d, i, j, float(np.log(p.mo[i] / p.mo[a]))))
            for q, (d, i, j, x) in enumerate(cand):
                if q < 60:
                    continue
                sd = np.std([c[3] for c in cand[q - 60:q]])
                if abs(x) > k * sd and x != 0:
                    g, n, _ = trade_cost_and_pnl(p, i, j, -int(np.sign(x)))
                    rows.append((d, s, g, n))
        lab = f"E1 reversal of 20->01 move |x|>{k}sd"
        out[lab] = summarize(rows, lab)
    return out


def family_f4(PS):
    out = {}
    for (a, b, c, lab) in [(7, 12, 16, "London 07-12 -> 12-16"), (7, 12, 20, "London 07-12 -> 12-20"),
                           (1, 7, 12, "Asia 01-07 -> 07-12"), (7, 13, 19, "07-13 -> 13-19"), (13, 17, 20, "13-17 -> 17-20")]:
        for sign, nm in ((1, "momentum"), (-1, "reversal")):
            rows = []
            for s in ALL:
                p = PS[s]
                for d in np.unique(p.t // 86400):
                    ia = p.at(d * 86400 + a * H); ib = p.at(d * 86400 + b * H); ic = p.at(d * 86400 + c * H)
                    if min(ia, ib, ic) < 0:
                        continue
                    x = p.mo[ib] - p.mo[ia]
                    if x == 0:
                        continue
                    g, n, _ = trade_cost_and_pnl(p, ib, ic, sign * int(np.sign(x)))
                    rows.append((d, s, g, n))
            out[f"F4 {lab} {nm}"] = summarize(rows, f"F4 {lab} {nm}")
    return out


def family_f1(PS):
    out = {}
    for (look, hold, at) in [(8, 8, (8, 16)), (24, 24, (12,))]:
        for cond in ("hi", "lo"):
            rows = []
            for s in ALL:
                p = PS[s]
                ct = np.concatenate([[0], np.cumsum(p.ticks.astype(float))])
                hist: dict = {}
                for d in np.unique(p.t // 86400):
                    for hh in at:
                        t0 = d * 86400 + hh * H
                        i = p.at(t0); a = p.at(t0 - look * H); j = p.at(t0 + hold * H)
                        if min(i, a, j) < 0:
                            continue
                        act = ct[i] - ct[a]; x = p.mo[i] - p.mo[a]
                        h = hist.setdefault(hh, [])
                        if len(h) >= 40:
                            z = (act - np.mean(h[-60:])) / np.std(h[-60:])
                            if x != 0 and ((cond == "hi" and z > 1.0) or (cond == "lo" and z < -0.75)):
                                side = int(np.sign(x)) if cond == "hi" else -int(np.sign(x))
                                g, n, _ = trade_cost_and_pnl(p, i, j, side)
                                rows.append((d, s, g, n))
                        h.append(act)
            lab = f"F1 look{look}h hold{hold}h {cond}-activity"
            out[lab] = summarize(rows, lab)
    return out


def main() -> int:
    PS = {s: P(s) for s in ALL}
    res = {"program": "EX-1", "period": ["2007-03-30", "2013-01-01"], "costs": {"commission_pips": COMM_PIPS,
           "slippage_pips_per_fill": SLIP_PIPS, "spread": "measured bid/ask of the bar"}}
    res["results"] = {**family_e1(PS), **family_f4(PS), **family_f1(PS)}
    res["configurations"] = len(res["results"])
    res["positive_net_t_above_2"] = [k for k, v in res["results"].items() if v and v["t_day"] > 2 and v["net_bps"] > 0]
    (ROOT / "research" / "results" / "EX-1.json").write_text(json.dumps(res, indent=1) + "\n")
    print(res["configurations"], "configurations;", "positive with t > 2:", res["positive_net_t_above_2"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
