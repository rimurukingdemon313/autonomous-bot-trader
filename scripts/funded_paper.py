"""FUNDED-P: TRND-1's rule on a $200,000 funded-account paper track, under FTMO-style limits (docs/FUNDED_PAPER.md).

PAPER ONLY: no broker, no account, no order and no key. Public daily closes and fixed rules, recomputed from the same
start on every run, so the record is this code plus the data and nothing else.

The owner, 2026-11-07: the $200K account is a funded (prop-firm) account; everything is on paper first ("we want to
make sure"), and only then a real one. TRND-1 is the only rule that passed its test and its holdout here. This
measures, forward, how it fares against a funded account's rules. It is not a promise, and TRND-1 is not an edge over
the market: month by month it earned slightly less than holding the index, with about half the worst fall.

The rules, fixed before the first day:
- two tracks, each its own $200,000 account: HALF holds $25,000 of each of the four indices when the rule says hold
  ($100,000 at most in all), FULL $50,000 ($200,000 at most);
- the rule is TRND-1's, unchanged (scripts/trnd1.py): an index is held for a month if the last month-end close before
  it is above the mean of the ten month-end closes before it, that one included; it never sells short. A decision
  whose ten closes are not all there is unknown, and unknown is flat;
- costs: 0.05% of the position for each switch in or out, booked at the first close after it; no swap (an Islamic
  account) and no dividends;
- HALF carries a one-day catastrophe stop: an index that closes 6% or more below its previous close is out, booked at
  -8% (2 points of slippage), and flat until the next month's decision. A crash day like 1987-10-19 is then a loss of
  about $8,000, inside the $10,000 daily limit, where without it the account would end. FULL has no stop: its daily
  limit is 5% of its position, which no workable stop keeps;
- each day after the closes: equity is the phase's start plus every closed and open P&L. A day that loses $10,000 or
  more (5% of the start), or equity at or below $180,000 (10% below it), ends the track as FAILED, as a funded
  account's rules would. Equity at $220,000 (+10%) passes phase 1, and phase 2 then starts a fresh $200,000 with a
  $10,000 (+5%) target; after it the track is FUNDED, with no target and the same limits;
- a phase passes no earlier than its 4th trading day, as FTMO's rules require. The rule trades a few times a year, so
  each phase's first 4 days carry one minimal trade each, opened and closed the same day at a cost of $5: what a
  trader does to meet that rule. It changes nothing else;
- a close is used only once it is final: 30 minutes after its exchange's close.

Approximations, declared: closes only (a fall inside a day that recovers by the close is not seen), and the day is
close to close where FTMO measures from midnight in Prague.

    python scripts/funded_paper.py run          # fetch the closes (GitHub's runner) and write out/REPORT.md, state.json
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.trnd1 as T  # noqa: E402

VERSION = "funded-paper-1.1.0"  # 1.1.0: HALF carries a one-day catastrophe stop at 6%
START = date(2026, 11, 9)  # the first close of the record: the rule's positions are opened at it
BALANCE = 200_000.0
DAILY_LOSS = 10_000.0  # 5% of the start
MAX_LOSS = 20_000.0  # 10%: equity at or below $180,000 fails
TARGETS = {1: 20_000.0, 2: 10_000.0}  # phase 1 +10%, phase 2 +5%; then FUNDED, with no target
MIN_TRADING_DAYS = 4
COMPLIANCE_COST = 5.0  # one minimal trade, opened and closed the same day
#: each track: the share of the balance in the market when the rule holds all four, and its one-day stop. FULL has
#: none: its $10,000 daily limit is 5% of its $200,000, which only a stop near 3% could keep, and such a stop would
#: be hit every few months
TRACKS = {"HALF": {"expo": 0.5, "stop": 0.06}, "FULL": {"expo": 1.0, "stop": None}}
STOP_SLIPPAGE = 0.02  # a stop is booked 2 points beyond its level: closes cannot show where it really filled
FETCH_FROM = date(2025, 9, 1)  # ten month-ends before the first decision, and more
#: when each index's close is final: the exchange's close, plus 30 minutes
CLOSE = {"^GSPC": ("America/New_York", time(16, 0)), "^NDX": ("America/New_York", time(16, 0)),
         "^GDAXI": ("Europe/Berlin", time(17, 30)), "^FTSE": ("Europe/London", time(16, 30))}
OUT = ROOT / "out"


def decisions(closes: dict[date, float]) -> dict[tuple[int, int], bool | None]:
    """TRND-1's decision for each month: held if the last month-end close before it is above the mean of the ten
    month-end closes before it (that one included); None when those ten are not all there. A month's decision reads
    only closes from the months before it."""
    ends = T.month_ends(closes)
    out: dict[tuple[int, int], bool | None] = {}
    for i, (d, c) in enumerate(ends):
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        if i + 1 < T.MONTHS or T.months_between(ends[i + 1 - T.MONTHS][0], nxt) != T.MONTHS:
            out[(nxt.year, nxt.month)] = None
            continue
        window = [x for _, x in ends[i + 1 - T.MONTHS:i + 1]]
        out[(nxt.year, nxt.month)] = c > sum(window) / T.MONTHS
    return out


def final_only(sym: str, closes: dict[date, float], now: datetime) -> dict[date, float]:
    """The closes that are final at `now`."""
    tz, at = CLOSE[sym]
    return {d: c for d, c in closes.items()
            if now >= datetime.combine(d, at, ZoneInfo(tz)) + timedelta(minutes=30)}


def run(closes: dict[str, dict[date, float]], expo: float, start: date = START, until: date | None = None,
        swap_pa: float = 0.0, stop: float | None = None) -> dict:
    """One funded-account track from `start` (positions opened at its first close), through `until`. `stop`: an index
    that closes that fraction or more below its previous close is out at the stop plus STOP_SLIPPAGE, and flat until
    the next month's decision. `swap_pa` is for the descriptive replay only: a yearly swap on a held position's
    notional, charged per calendar day. The live tracks are swap-free (0)."""
    syms = list(closes)
    notional = expo * BALANCE / len(syms)
    dates = sorted({d for s in syms for d in closes[s] if d >= start and (until is None or d <= until)})
    dec = {s: decisions(closes[s]) for s in syms}
    phase, base, equity, trading_days, phase_days = 1, BALANCE, BALANCE, 0, 0
    held: dict[str, bool] = {s: False for s in syms}
    last: dict[str, float | None] = {s: None for s in syms}
    seen: dict[str, date] = {}
    stopped: dict[str, tuple[int, int]] = {}
    stops = 0
    events, history, unknown = [], [], set()
    status = "PHASE 1"
    for d in dates:
        pl, traded = 0.0, False
        for s in syms:
            c = closes[s].get(d)
            if c is None:
                continue  # this index did not trade today
            want = dec[s].get((d.year, d.month))
            if want is None:
                unknown.add(f"{s} {d.year}-{d.month:02d}")
                want = False
            if stopped.get(s) == (d.year, d.month):
                want = False  # stopped out earlier this month: flat until the next decision
            if last[s] is not None and want != held[s]:  # switched at the previous close (a month-end)
                pl -= notional * T.COST_SIDE
                traded = True
            if last[s] is None and want:  # the record's first close: opened at it
                pl -= notional * T.COST_SIDE
                traded = True
            elif last[s] is not None and want:
                move = c / last[s] - 1.0
                if stop is not None and move <= -stop:  # the one-day catastrophe stop
                    pl -= notional * (stop + STOP_SLIPPAGE) + notional * T.COST_SIDE
                    stopped[s], want, traded, stops = (d.year, d.month), False, True, stops + 1
                    events.append({"date": str(d), "event": f"STOP: {s} closed {move:.1%}; out at "
                                                            f"-{stop + STOP_SLIPPAGE:.0%} until the next decision"})
                else:
                    pl += notional * move
                pl -= notional * swap_pa * (d - seen[s]).days / 365.0
            held[s], last[s], seen[s] = want, c, d
        if phase in TARGETS and phase_days < MIN_TRADING_DAYS:  # the minimal trade that meets the 4-day rule
            pl -= COMPLIANCE_COST
            traded = True
        phase_days += 1
        equity += pl
        trading_days += 1 if traded else 0
        history.append({"date": str(d), "phase": phase, "equity": round(equity, 2), "pl": round(pl, 2)})
        if pl <= -DAILY_LOSS:
            status = "FAILED"
            events.append({"date": str(d), "event": f"FAILED in phase {phase if phase < 3 else 'FUNDED'}: a day "
                                                    f"lost ${-pl:,.0f} (the limit is ${DAILY_LOSS:,.0f})"})
            break
        if equity <= base - MAX_LOSS:
            status = "FAILED"
            events.append({"date": str(d), "event": f"FAILED in phase {phase if phase < 3 else 'FUNDED'}: equity "
                                                    f"${equity:,.0f} reached the maximum loss"})
            break
        if phase in TARGETS and equity >= base + TARGETS[phase]:
            if trading_days < MIN_TRADING_DAYS:
                continue  # the target is reached; the phase passes once the trading days are there too
            events.append({"date": str(d), "event": f"PHASE {phase} PASSED at ${equity:,.0f}, "
                                                    f"{sum(1 for h in history if h['phase'] == phase)} days"})
            phase += 1
            status = f"PHASE {phase}" if phase in TARGETS else "FUNDED"
            n_open = sum(1 for s in syms if held[s])  # the new account opens the same positions at this close
            equity = BALANCE - n_open * notional * T.COST_SIDE
            base, trading_days, phase_days = BALANCE, 1 if n_open else 0, 0
    return {"status": status, "phase": phase, "equity": round(equity, 2), "base": base,
            "target": base + TARGETS[phase] if phase in TARGETS else None, "trading_days": trading_days,
            "held": {s: held[s] for s in syms}, "notional_each": notional, "stop": stop, "stops": stops,
            "events": events, "history": history,
            "unknown_decisions": sorted(unknown), "last_date": history[-1]["date"] if history else None}


# ── the live record ──────────────────────────────────────────────────────

def fetch(now: datetime) -> dict[str, dict[date, float]]:
    out = {}
    for sym in T.HOLDOUT_INDICES:
        rows = T._yahoo(sym, now)
        out[sym] = final_only(sym, {date.fromisoformat(d): c for d, c in rows if date.fromisoformat(d) >= FETCH_FROM},
                              now)
    return out


def last_trading_day(month: date) -> str:
    """The month's last weekday, which is when the next decision is taken (after the close)."""
    nxt = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
    d = nxt - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return str(d)


def report(tracks: dict[str, dict], now: datetime) -> str:
    names = {"^GSPC": "US500", "^NDX": "NAS100", "^GDAXI": "GER40", "^FTSE": "UK100"}
    ar_status = {"PHASE 1": "المرحلة الأولى (الهدف +10%)", "PHASE 2": "المرحلة الثانية (الهدف +5%)",
                 "FUNDED": "ممول (بدون هدف)", "FAILED": "فشل"}
    month = date(now.year, now.month, 1)
    lines = ["# FUNDED-P — a funded-account paper track of TRND-1 · PAPER ONLY, NOT REAL MONEY", "",
             f"Updated {now:%Y-%m-%d %H:%M} UTC · {VERSION} · started {START} · public daily closes · no broker", "",
             "## ملخص بالعربي", ""]
    for name, r in tracks.items():
        pl = r["equity"] - r["base"]
        held = "، ".join(names[s] for s, h in r["held"].items() if h) or "ولا مؤشر"
        if r["last_date"] is None:
            lines.append(f"- مسار {'نص الحجم' if name == 'HALF' else 'الحجم الكامل'}: يبدي بإغلاق {START}.")
            continue
        lines.append(f"- مسار {'نص الحجم' if name == 'HALF' else 'الحجم الكامل'}: {ar_status[r['status']]}، "
                     f"الرصيد ${r['equity']:,.0f} (من ${r['base']:,.0f}: {pl:+,.0f})، ماسك: {held}.")
    lines += [f"- القرار الجاي: آخر يوم تداول بالشهر ({last_trading_day(month)})، بعد الإغلاق.",
              "- حساب ورقي للقياس، مو فلوس حقيقية، والماضي مو وعد.", "",
              "## The tracks", "",
              "| Track | Status | Equity | Phase P&L | Target | Trading days | Held | Last close |",
              "|---|---|---|---|---|---|---|---|"]
    for name, r in tracks.items():
        held = ", ".join(names[s] for s, h in r["held"].items() if h) or "none"
        tgt = f"${r['target']:,.0f}" if r["target"] else "—"
        if r["last_date"] is None:
            lines.append(f"| {name} | not started: the record starts at the close of {START} | | | | | | |")
            continue
        stop = f", stop {r['stop']:.0%} a day" if r["stop"] else ", no stop"
        lines.append(f"| {name} ({TRACKS[name]['expo']:.0%} of the balance when all four are held{stop}) | **{r['status']}** | "
                     f"${r['equity']:,.2f} | {r['equity'] - r['base']:+,.2f} | {tgt} | {r['trading_days']} | {held} | "
                     f"{r['last_date']} |")
    for name, r in tracks.items():
        lines += ["", f"### {name}: events", ""] + ([f"- {e['date']}: {e['event']}" for e in r["events"]] or ["- none yet"])
        if r["unknown_decisions"]:
            lines.append(f"- decisions unknown (held flat): {', '.join(r['unknown_decisions'])}")
        lines += ["", "| Date | Phase | Equity | Day P&L |", "|---|---|---|---|"]
        lines += [f"| {h['date']} | {h['phase']} | ${h['equity']:,.2f} | {h['pl']:+,.2f} |" for h in r["history"][-15:]]
    lines += ["", "## The rules", "",
              "TRND-1's rule, unchanged, on the US 500, US Tech 100, GER 40 and UK 100: an index is held for a month if "
              "the last month-end close before it is above the mean of the ten month-end closes before it; never short. "
              "0.05% each switch; no swap; no dividends. A day losing $10,000, or equity at $180,000, fails; +10% then "
              "+5% (each with at least 4 trading days) pass the two phases. Closes only; a close counts 30 minutes "
              "after its exchange closes. `scripts/funded_paper.py`, `docs/FUNDED_PAPER.md`."]
    return "\n".join(lines) + "\n"


def cmd_run(now: datetime) -> None:
    closes = fetch(now)
    tracks = {name: run(closes, t["expo"], stop=t["stop"]) for name, t in TRACKS.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "state.json").write_text(json.dumps({"version": VERSION, "updated": now.isoformat(), "start": str(START),
                                                "tracks": tracks}, indent=1, sort_keys=True, default=str) + "\n")
    (OUT / "REPORT.md").write_text(report(tracks, now))
    for name, r in tracks.items():
        print(name, r["status"], r["equity"], r["last_date"], r["held"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"run": lambda: cmd_run(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
