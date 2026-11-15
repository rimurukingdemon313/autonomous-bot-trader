"""The funding radar's frozen decision code, replayed on the radar's own stored quotes under other parameters.

`aitrader.radar.core.step` is a pure function of the book and of one hour's quotes. It is imported here and never
changed: RADAR-1's code hash is untouched, and its forward test is read on 2026-12-06 as registered. What changes in a
replay is only the `Rules` passed in, so an original and a variant differ by declared numbers and by nothing else:
the same quotes, the same fees and slippage, the same ten slots of 2N.

Three things are built on that:

- an **archive** of the radar's hourly quotes. The radar keeps 240 hours of them and forgets the rest; a day is copied
  here once, when it is over, and is never rewritten;
- a **chronological validation**: the declared variants are compared on the earlier half of the archive, the best of
  them is named there, and only the later half judges it. A later half too short to judge says so;
- **forward challengers**: a variant registered at an hour is judged only on hours after it, once, at a look date
  fixed with it. Nothing here replaces the original: a challenger that passes is proposed to the owner.

Research only: no order, no account, no key.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from aitrader.radar import core as R
from aitrader.radar.venues import Quote

from .radar import SLOTS, YEAR_S, daily_excess, fills_bp, net_bp
from .stats import mean_t

ROW = ("t", "venue", "coin", "scale", "rate", "mark", "vol")
HOUR, DAY = 3600, 86400

#: The variants, declared at DECLARED and before any replay was run. Each changes one thing the audit of the radar's
#: ledger pointed at (docs/PERFORMANCE_ENGINEERING.md); the last holds all three together. Parameters only.
VARIANTS: dict[str, dict] = {
    "original": {},
    # the entry reads the same 24 hours the exit reads: a spread that is already gone is not entered
    "same-window": {"trailing_entry_h": 24},
    # the entry asks twice the spread: the carry must pay for the round trip in days, not in a week
    "thick-entry": {"entry_trailing_apr": 0.50, "entry_now_apr": 0.30},
    # one bad hour does not close a position: the 24-hour mean decides, unless the hour is extreme
    "patient-exit": {"exit_now_apr": -1.00},
    "all-three": {"trailing_entry_h": 24, "entry_trailing_apr": 0.50, "entry_now_apr": 0.30, "exit_now_apr": -1.00},
}
#: 2026-11-14 20:00 UTC. Hours from this one on had not happened when the variants were declared.
DECLARED = 1794686400
#: What a variant must show on the judging part before it is proposed as a registered challenger.
GATES = {"min_days": 30, "min_positions": 30, "min_t": 3.0, "min_paired_t": 3.0}
#: A registered challenger's single look, and what it must also show there (the original's own gates, at a harder t).
FORWARD = {"look_days": 60, "min_ann_excess_deployed_pct": 10.0, "max_dd_pct": 10.0}
WARMUP_H = 72  # the longest window any variant's entry reads: every variant starts where the original can


def rules(name: str) -> R.Rules:
    if name not in VARIANTS:
        raise KeyError(f"unknown variant {name!r}: a variant is declared in code before it is replayed")
    return R.Rules(**VARIANTS[name])


# ── the archive ─────────────────────────────────────────────────────────────

def day_of(t: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(t))


def _pack(rows: list[dict]) -> bytes:
    return gzip.compress("\n".join(json.dumps([r[k] for k in ROW], separators=(",", ":")) for r in rows).encode(), mtime=0)


def _unpack(blob: bytes) -> list[dict]:
    return [dict(zip(ROW, json.loads(line))) for line in gzip.decompress(blob).decode().splitlines() if line]


def _digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps([[r[k] for k in ROW] for r in rows], separators=(",", ":")).encode()).hexdigest()


def merge(archive: Path, history: list[dict]) -> dict:
    """Copy the radar's stored hours into the archive. A day is written once, when it is over (the radar holds an
    hour of a later day), and never rewritten: on a later run its rows are compared with what the radar still holds,
    and a difference is reported, not repaired. Returns what was added and every problem found."""
    archive.mkdir(parents=True, exist_ok=True)
    mf = archive / "manifest.json"
    manifest = json.loads(mf.read_text()) if mf.exists() else {"days": {}}
    by_day: dict[str, list[dict]] = {}
    for h in history:
        by_day.setdefault(day_of(h["t"]), []).append({k: h[k] for k in ROW})
    if not by_day:
        return {"added": [], "problems": [], "days": len(manifest["days"])}
    newest = max(by_day)
    first_t = min(h["t"] for h in history)
    added, problems = [], []
    for day in sorted(by_day):
        rows = by_day[day]
        if day in manifest["days"]:
            old = {(r["t"], r["venue"], r["coin"], r["scale"]): r for r in _unpack((archive / f"{day}.jsonl.gz").read_bytes())}
            diff = sum(1 for r in rows if (k := (r["t"], r["venue"], r["coin"], r["scale"])) in old and old[k] != r)
            extra = sum(1 for r in rows if (r["t"], r["venue"], r["coin"], r["scale"]) not in old)
            if diff or extra:
                problems.append(f"{day}: the radar's stored rows differ from the archived day ({diff} changed, {extra} not archived)")
            continue
        if day == newest:
            continue  # the day is not over: it is copied by a later run
        hours = sorted({r["t"] for r in rows})
        (archive / f"{day}.jsonl.gz").write_bytes(_pack(rows))
        manifest["days"][day] = {"rows": len(rows), "hours": len(hours), "first_t": hours[0], "last_t": hours[-1],
                                 "sha256": _digest(rows),
                                 "starts_late": bool(day == day_of(first_t) and first_t % DAY != 0)}
        added.append(day)
    manifest["days"] = dict(sorted(manifest["days"].items()))
    mf.write_text(json.dumps(manifest, indent=1) + "\n")
    return {"added": added, "problems": problems, "days": len(manifest["days"])}


def load(archive: Path) -> tuple[list[dict], list[str]]:
    """Every archived row, oldest day first, each day checked against the hash recorded when it was written."""
    mf = archive / "manifest.json"
    if not mf.exists():
        return [], []
    rows, problems = [], []
    for day, meta in sorted(json.loads(mf.read_text())["days"].items()):
        f = archive / f"{day}.jsonl.gz"
        if not f.exists():
            problems.append(f"{day}: named in the manifest and missing from the archive")
            continue
        got = _unpack(f.read_bytes())
        if _digest(got) != meta["sha256"]:
            problems.append(f"{day}: the archived rows no longer match their recorded hash")
            continue
        rows += got
    return rows, problems


def with_pending(archived: list[dict], history: list[dict]) -> list[dict]:
    """The archive, then whatever the radar holds that is newer than it (the day in progress)."""
    last = max((r["t"] for r in archived), default=-1)
    return archived + [{k: h[k] for k in ROW} for h in history if h["t"] > last]


# ── the replay ──────────────────────────────────────────────────────────────

def by_hour(rows: list[dict]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for r in rows:
        out.setdefault(r["t"], []).append(r)
    return out


def start_of(rows: list[dict]) -> int | None:
    """The first hour every variant can decide at: the hour the longest entry window is first full (the radar reads a
    72-hour window as full once its first snapshot is 71 hours old)."""
    ts = sorted({r["t"] for r in rows})
    return ts[0] + (WARMUP_H - 1) * HOUR if ts else None


def replay(rows: list[dict], rule: R.Rules, start: int, end: int | None = None) -> R.State:
    """A new, empty book stepped by the radar's own `step` through every stored hour from `start` (to `end`,
    exclusive). The hours before `start` are history only, as the radar would have held them: nothing is traded or
    marked there."""
    state = R.State()
    hours = by_hour(rows)
    for t in sorted(hours):
        if end is not None and t >= end:
            break
        if t < start:
            state.history += [dict(r) for r in hours[t]]
            continue
        quotes = [Quote(r["venue"], r["coin"], r["scale"], r["rate"], r["mark"], r["vol"]) for r in hours[t]]
        R.step(state, quotes, {}, t, rule)
    return state


def ledger_of(state: R.State) -> dict:
    """A replayed book in the shape of the radar's public ledger, so the audit's arithmetic reads both alike."""
    return {"open": [asdict(p) for p in state.open], "closed": [asdict(p) for p in state.closed], "marks": state.marks,
            "runs": state.runs}


def fidelity(replayed: dict, real: dict, start: int, end: int | None = None) -> dict:
    """How closely the replay of the ORIGINAL rules reproduces the radar's real ledger on the same hours. A replay
    starts with an empty book, so a coin the radar already held at `start` is the one expected difference."""
    def ids(led, lo, hi):
        return {p["id"]: p for p in led["closed"] + led["open"] if p["opened"] >= lo and (hi is None or p["opened"] < hi)}
    held = {p["coin"] for p in real["closed"] + real["open"]
            if p["opened"] < start and (p.get("closed") is None or p["closed"] > start)}
    a, b = ids(replayed, start, end), ids(real, start, end)
    both = sorted(set(a) & set(b))
    same_exit = [i for i in both if a[i].get("closed") == b[i].get("closed") and a[i].get("reason") == b[i].get("reason")]
    same_net = [i for i in same_exit if abs(net_bp(a[i]) - net_bp(b[i])) < 0.01]
    only_real = sorted(set(b) - set(a))
    only_replay = sorted(set(a) - set(b))
    explained = [i for i in only_real + only_replay if (a.get(i) or b.get(i))["coin"] in held]
    n = len(b)
    return {"real_positions": n, "matched": len(both), "matched_share": len(both) / n if n else None,
            "same_exit": len(same_exit), "same_net": len(same_net),
            "only_in_the_real_ledger": only_real, "only_in_the_replay": only_replay,
            "explained_by_a_position_held_at_the_start": len(explained), "held_at_the_start": sorted(held),
            "trustworthy": bool(n) and (len(same_net) + sum(1 for i in only_real if b[i]["coin"] in held)) / n >= 0.9}


# ── measuring a book on a window ────────────────────────────────────────────

def window(led: dict, rf_apr: float, t0: int, t1: int) -> dict:
    """A book's figures for the hours in [t0, t1): its daily excess over cash there, and the positions OPENED there
    (an open one valued as if closed at the book's last mark). All in percent of the book."""
    inside = [m for m in led["marks"] if t0 <= m["t"] < t1]
    before = [m for m in led["marks"] if m["t"] < t0]
    marks = before[-1:] + inside  # the mark before the window: the first hour's change is measured from it
    daily = daily_excess(marks, rf_apr) if len(marks) > 1 else {}
    days = sorted(daily)
    m, t = mean_t([daily[d] for d in days])
    last = led["marks"][-1]["t"] if led["marks"] else t0
    end = min(last, t1)
    cap = 2.0 * SLOTS
    by_coin: dict[str, float] = {}
    exc = cost = cap_y = 0.0
    n = closed = 0
    for p in led["closed"] + led["open"]:
        if not t0 <= p["opened"] < t1:
            continue
        still = p.get("closed") is None
        leave = fills_bp(p) if still else 0.0
        dur_y = ((end if still else p["closed"]) - p["opened"]) / YEAR_S
        e = (net_bp(p) - leave) / 1e4 - rf_apr * 2 * dur_y
        by_coin[p["coin"]] = by_coin.get(p["coin"], 0.0) + e
        exc, cost, cap_y, n, closed = exc + e, cost + (p["cost_bp"] + leave) / 1e4, cap_y + 2 * dur_y, n + 1, closed + (not still)
    best = max(by_coin, key=by_coin.get) if by_coin else None
    cum, peak, dd = 0.0, 0.0, 0.0
    for d in days:
        cum += daily[d]
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return {"days": len(days), "book_excess_pct": round(sum(daily.values()) * 100, 4),
            "mean_daily_excess_pct": None if m is None else round(m * 100, 5), "t_daily": None if t is None else round(t, 2),
            "max_dd_pct_daily": round(dd * 100, 4),
            "positions": n, "closed": closed, "positions_excess_pct": round(exc / cap * 100, 4),
            "costs_pct": round(cost / cap * 100, 4),
            "excess_costs_x1.5_pct": round((exc - 0.5 * cost) / cap * 100, 4),
            "ann_excess_deployed_pct": round(exc / cap_y * 100, 2) if cap_y > 0 else None,
            "best_coin": best, "excess_without_best_coin_pct": round((exc - by_coin[best]) / cap * 100, 4) if best else None,
            "daily": {str(d): daily[d] for d in days}}


def paired(a: dict, b: dict) -> dict:
    """A variant's daily excess less the original's, on the days both have: the mean difference and its t."""
    days = sorted(set(a["daily"]) & set(b["daily"]))
    m, t = mean_t([a["daily"][d] - b["daily"][d] for d in days])
    return {"days": len(days), "mean_daily_difference_pct": None if m is None else round(m * 100, 5),
            "t": None if t is None else round(t, 2),
            "sum_difference_pct": round(sum(a["daily"][d] - b["daily"][d] for d in days) * 100, 4)}


def gates(w: dict, pair: dict) -> dict:
    """What the judging part must show. A short part fails on its length first, and says so."""
    g = GATES
    return {"enough_days": w["days"] >= g["min_days"], "enough_positions": w["closed"] >= g["min_positions"],
            "excess_over_cash": w["book_excess_pct"] > 0 and w["t_daily"] is not None and w["t_daily"] >= g["min_t"],
            "beats_the_original": pair["t"] is not None and pair["t"] >= g["min_paired_t"],
            "costs_x1.5": w["excess_costs_x1.5_pct"] > 0,
            "without_best_coin": w["excess_without_best_coin_pct"] is not None and w["excess_without_best_coin_pct"] > 0}


def validate(rows: list[dict], rf_apr: float) -> dict:
    """Every declared variant replayed on the same stored hours, the hours cut in two by time. The variant with the
    best excess on the EARLIER part is the candidate, and only the LATER part judges it. No variant is chosen on the
    part that judges it, and a part too short to judge anything proposes nothing."""
    start = start_of(rows)
    ts = sorted({r["t"] for r in rows})
    if start is None or ts[-1] <= start + 2 * DAY:
        return {"status": "NOT ENOUGH HOURS", "why": "fewer than two days of stored hours after the 72-hour warm-up",
                "hours": len(ts)}
    end = ts[-1] + HOUR
    cut = (start + (end - start) // 2) // DAY * DAY  # a day boundary, so no day is split between the parts
    if not start < cut < end:
        cut = start + (end - start) // 2
    books = {name: ledger_of(replay(rows, rules(name), start)) for name in VARIANTS}
    out = {"start": start, "cut": cut, "end": end, "configurations_compared": len(VARIANTS) - 1, "variants": {}}
    for name, led in books.items():
        d, j, w = window(led, rf_apr, start, cut), window(led, rf_apr, cut, end), window(led, rf_apr, start, end)
        od, oj = window(books["original"], rf_apr, start, cut), window(books["original"], rf_apr, cut, end)
        out["variants"][name] = {"parameters": VARIANTS[name], "earlier": _slim(d), "later": _slim(j), "whole": _slim(w),
                                 "against_original_earlier": paired(d, od), "against_original_later": paired(j, oj)}
    names = [n for n in VARIANTS if n != "original"]
    cand = max(names, key=lambda n: out["variants"][n]["earlier"]["book_excess_pct"])
    v = out["variants"][cand]
    g = gates(window(books[cand], rf_apr, cut, end), paired(window(books[cand], rf_apr, cut, end),
                                                         window(books["original"], rf_apr, cut, end)))
    short = not (g["enough_days"] and g["enough_positions"])
    out["candidate"] = cand
    out["candidate_chosen_on"] = "the earlier part only: its book excess there"
    out["gates_on_the_later_part"] = g
    out["status"] = ("INCONCLUSIVE" if short else "PROPOSED" if all(g.values()) else "REJECTED")
    out["why"] = (f"the later part holds {v['later']['days']} days and {v['later']['closed']} closed positions: "
                  f"{GATES['min_days']} and {GATES['min_positions']} are needed before anything is judged" if short else
                  "every gate held on the later part" if all(g.values()) else
                  "failed on the later part: " + ", ".join(k for k, ok in g.items() if not ok))
    out["books"] = books
    return out


def _slim(w: dict) -> dict:
    return {k: v for k, v in w.items() if k != "daily"}


# ── a registered challenger, judged forward and once ────────────────────────

def forward(ch: dict, rows: list[dict], rf_apr: float, now: int) -> dict:
    """A registered challenger against the original, on hours at or after its registration only: both start from an
    empty book at that hour, on the same quotes. WAIT until the look date; then one verdict, on every gate."""
    t0 = ch["registered_t"]
    look = t0 + int(ch.get("look_days", FORWARD["look_days"]) * DAY)
    end = min(look, now + 1)
    led = {n: ledger_of(replay(rows, rules(n), t0, end)) for n in ("original", ch["variant"])}
    w = {n: window(led[n], rf_apr, t0, end) for n in led}
    pair = paired(w[ch["variant"]], w["original"])
    out = {"id": ch["id"], "variant": ch["variant"], "registered_t": t0, "look_t": look,
           "challenger": _slim(w[ch["variant"]]), "original": _slim(w["original"]), "challenger_less_original": pair}
    if now < look:
        return {**out, "status": "WAIT"}
    g = gates(w[ch["variant"]], pair)
    c = w[ch["variant"]]
    g["ann_excess_on_deployed"] = c["ann_excess_deployed_pct"] is not None and c["ann_excess_deployed_pct"] >= FORWARD["min_ann_excess_deployed_pct"]
    g["max_drawdown"] = c["max_dd_pct_daily"] <= FORWARD["max_dd_pct"]
    if not (g["enough_days"] and g["enough_positions"]):
        return {**out, "status": "INCONCLUSIVE", "gates": g}
    return {**out, "status": "PASSED" if all(g.values()) else "FAILED", "gates": g}


def freeze(out_dir: Path, result: dict) -> dict:
    """A challenger's look is written once and read back ever after: never recomputed on a later, luckier day."""
    f = out_dir / f"challenger-{result['id']}-look.json"
    if f.exists():
        return json.loads(f.read_text())
    if result["status"] == "WAIT":
        return result
    f.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return result


__all__ = ["DECLARED", "FORWARD", "GATES", "ROW", "VARIANTS", "by_hour", "fidelity", "forward", "freeze", "gates",
           "ledger_of", "load", "merge", "paired", "replay", "rules", "start_of", "validate", "window", "with_pending"]
