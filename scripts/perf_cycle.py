"""One performance cycle of the paper systems (docs/PERFORMANCE_ENGINEERING.md). Run by .github/workflows/perf-cycle.yml.

    python scripts/perf_cycle.py --trend DIR --radar DIR --out DIR [--radar-state DIR] [--challengers FILE]

Each cycle:

1. reads the latest paper data: the trend desk's ledger, equity history, state and database (`--trend`, a checkout
   of `trend-desk-data`), and the funding radar's ledger and report (`--radar`, a checkout of `radar-data`);
2. reconciles both accounts: every figure recomputed by a second route and compared (aitrader/perf/trend.py, radar.py);
3. says where the profit and the loss came from, and names the largest weakness;
4. states the hypothesis that weakness supports, if a declared variant tests it;
5. copies the radar's stored quotes into the archive and replays the radar's frozen rules and every declared variant
   on them: the best on the earlier half is judged on the later half only (aitrader/perf/replay.py);
6. steps every registered challenger forward beside the original, and freezes its look once;
7. writes PERF_REPORT.md, paper_audit.json, replay.json and one line of cycles.jsonl into `--out`.

It exits 1 after writing everything if a reconciliation failed or the archive has a problem: the failure is published
and the run is red. Research and presentation only: it places no order and changes no system.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.perf import PERF_VERSION, radar, replay, trend  # noqa: E402

RF = 0.03875  # the cash rate RADAR-1 declared (US policy rate, BIS, 2026-09-22); used for both systems
#: The declared variant that tests each weakness the attribution can name. A weakness outside this map gets no
#: experiment from the cycle: a new variant is declared in code by the director, never invented by a run.
LEVERS = {
    ("entry spread", "under 50%/yr"): (
        "thick-entry", "Positions opened on a trailing spread under 50%/yr do not earn their round trip. Asking twice "
                       "the spread at the entry removes them; whether the entries that remain earn more than cash is "
                       "what the replay measures."),
    ("time since the coin's previous position", "within 6 hours of the coin's previous exit"): (
        "same-window", "Re-entries soon after an exit lose more than the rest. The entry reads 72 hours and the exit "
                       "24: reading the same 24 hours at the entry does not enter a spread that has already decayed."),
}


def _fmt(x, nd=2, unit=""):
    return "n/a" if x is None else f"{x:,.{nd}f}{unit}"


def _usd(x):
    return "n/a" if x is None else (f"-${-x:,.2f}" if x < 0 else f"${x:,.2f}")


def _signed(x):
    return "n/a" if x is None else "$0.00" if abs(x) < 0.005 else (f"-${-x:,.2f}" if x < 0 else f"+${x:,.2f}")


def _when(t):
    return "n/a" if t is None else datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def audit_trend(d: Path) -> dict | None:
    need = [d / "ledger.csv", d / "equity.csv", d / "state.json"]
    if not all(f.exists() for f in need):
        return None
    record = chains = None
    gz = d / "desk.db.gz"
    if gz.exists():
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "desk.db"
            try:
                db.write_bytes(gzip.decompress(gz.read_bytes()))
                record = trend.points(db)
                chains = [trend.chain(db, "events"), trend.chain(db, "risk_gate_log")]
            except (OSError, EOFError, sqlite3.Error):  # a record that cannot be read is a failed check, never a pass
                record, chains = None, [{"table": "events (the database could not be read)", "rows": 0, "ok": False}]
    rep = d / "TRADING_REPORT.md"
    return trend.audit(trend.rows(need[0].read_text()), trend.rows(need[1].read_text()), json.loads(need[2].read_text()),
                       rf_apr=RF, record=record, chains=chains, report=rep.read_text() if rep.exists() else None)


def audit_radar(d: Path) -> tuple[dict | None, dict | None]:
    f = d / "ledger.json"
    if not f.exists():
        return None, None
    led = json.loads(f.read_text())
    rep = d / "REPORT.md"
    return radar.audit(led, rf_apr=RF, report=rep.read_text() if rep.exists() else None), led


def engine(state_dir: Path | None, out: Path, real: dict | None, challengers: list[dict], now: int) -> dict:
    """The archive, the replay of every declared variant, and every registered challenger."""
    res: dict = {"archive": None, "validation": None, "fidelity": None, "challengers": [], "problems": []}
    history: list[dict] = []
    f = state_dir / "state.json.gz" if state_dir else None
    if f is not None and f.exists():
        history = json.loads(gzip.decompress(f.read_bytes())).get("history", [])
        res["archive"] = replay.merge(out / "quotes", history)
        res["problems"] += res["archive"]["problems"]
    else:
        res["archive"] = {"added": [], "problems": [], "days": None,
                          "note": "the radar's stored quotes were not available to this run: nothing was archived"}
    rows, problems = replay.load(out / "quotes")
    res["problems"] += problems
    rows = replay.with_pending(rows, history)
    res["hours"] = len({r["t"] for r in rows})
    res["first_hour"], res["last_hour"] = (min(r["t"] for r in rows), max(r["t"] for r in rows)) if rows else (None, None)
    prev_f = out / "replay.json"
    prev = json.loads(prev_f.read_text()) if prev_f.exists() else {}
    unchanged = (prev.get("version") == PERF_VERSION and prev.get("variants") == replay.VARIANTS
                 and all(prev.get(k) == res[k] for k in ("hours", "first_hour", "last_hour"))
                 and "variants" in (prev.get("validation") or {}) and (out / "books" / "original.json.gz").exists())
    if unchanged:  # a replay is a pure function of the stored hours: the same hours give the same books
        v, res["replayed_this_cycle"] = prev["validation"], False
    else:
        v = replay.validate(rows, RF)
        res["replayed_this_cycle"] = True
        books = v.pop("books", {})
        if books:
            (out / "books").mkdir(parents=True, exist_ok=True)
            for name, led in books.items():  # every book of the replay, kept small: the branch is rewritten every cycle
                (out / "books" / f"{name}.json.gz").write_bytes(gzip.compress(json.dumps(led, separators=(",", ":")).encode(), mtime=0))
    res["validation"] = v
    if "variants" in v and real is not None:
        original = json.loads(gzip.decompress((out / "books" / "original.json.gz").read_bytes()))
        res["fidelity"] = replay.fidelity(original, real, v["start"], v["end"])
    for ch in challengers:
        res["challengers"].append(replay.freeze(out, replay.forward(ch, rows, RF, now)))
    return res


def hypothesis(a_radar: dict | None, eng: dict) -> dict:
    """The largest weakness, the hypothesis it supports and the declared variant that tests it: or why there is none."""
    if a_radar is None:
        return {"weakness": None, "why": "the radar's ledger was not available"}
    w = a_radar["attribution"]["largest_weakness"]
    if w is None:
        return {"weakness": None, "why": "no class of at least ten positions did worse than the rest of the book by a difference told from noise"}
    lever = LEVERS.get((w["dimension"], w["class"]))
    out = {"weakness": {k: w[k] for k in ("dimension", "class", "positions", "sum_bp", "mean_bp", "t", "rest_mean_bp", "excess_loss_bp",
                                          "t_against_the_rest")}}
    if lever is None:
        return {**out, "variant": None, "why": "no declared variant tests this weakness: declaring one is the director's decision"}
    out["variant"], out["hypothesis"] = lever
    v = (eng.get("validation") or {}).get("variants", {}).get(lever[0])
    if v is not None:
        out["replay"] = {"earlier": v["earlier"], "later": v["later"], "against_original_later": v["against_original_later"]}
    return out


# ── the report ──────────────────────────────────────────────────────────────

def _checks(a: dict) -> list[str]:
    n, bad = len(a["checks"]), a["failed_checks"]
    if not bad:
        return [f"**Reconciled: {n} of {n} checks hold.** Each compares two routes to the same figure."]
    return [f"**NOT RECONCILED: {len(bad)} of {n} checks failed.**", ""] + [
        f"- {c['check']}: expected `{c['expected']}`, found `{c['found']}`" for c in bad]


def report_trend(a: dict) -> list[str]:
    f = a["figures"]
    ct, dd = f["closed_trades"], f["max_drawdown_inside_a_day"]
    und = ct["undefined"]

    def ratio(k, text):
        return f"undefined: {und[k]}" if ct[k] is None else text
    o = ["## 1. TRND-1: the trend desk's paper account", "", *_checks(a), "",
         f"Last session: {f['last_session']}. Paper only: no real money.", "", "| | |", "|---|---|",
         f"| Initial capital | {_usd(f['initial_capital'])} |",
         f"| Equity now | {_usd(f['equity_now'])} |",
         f"| **Realized** P&L (closed trades, after every cost) | {_signed(f['realized_net'])} from {_signed(f['realized_gross'])} gross |",
         f"| **Unrealized** P&L (open trades at the last close: a valuation, not a profit) | {_signed(f['unrealized'])} |",
         f"| Net after all costs (realized plus unrealized) | {_signed(f['net_after_all_costs'])} ({_fmt((f['net_return'] or 0) * 100, 3)}%) |",
         f"| Open positions | {f['open_positions']} |",
         f"| Closed trades | {ct['closed']}: {ct['won']} won, {ct['lost']} lost |",
         f"| Win rate | {ratio('win_rate', _fmt((ct['win_rate'] or 0) * 100, 1) + '%')} |",
         f"| Average win / average loss | {ratio('average_win', _usd(ct['average_win']))} / {ratio('average_loss', _usd(ct['average_loss']))} |",
         f"| Profit factor | {ratio('profit_factor', _fmt(ct['profit_factor']))} |",
         f"| Maximum drawdown, session closes | {_usd(f['max_drawdown_session_closes'])} |",
         f"| Maximum drawdown, inside a day | {_usd(dd['value']) if dd['value'] is not None else 'unavailable: ' + dd['why']} |",
         f"| Below the peak now | {_usd(f['below_the_peak_now'])} |",
         f"| Gross exposure | {_usd(f['gross_exposure'])}, {_fmt(f['leverage'], 2)}x the equity |",
         f"| Loss if every stop were hit from here | {_usd(f['open_risk_at_stops'])} (limit {_usd(trend.LIMITS['open_together'])}) |",
         f"| Losing days | {f['losing_days']} of {f['days']} |", ""]
    if ct["sample"] != "ok":
        o += [f"Trade statistics: sample **{ct['sample']}** ({ct['closed']} closed). A ratio over no closed trade does not "
              "exist and is not shown as zero.", ""]
    o += ["### Open positions and where the risk sits", "",
          "| Index | Units | Entry | Mark | Move | Unrealized | Notional | Share of gross | Stop | Loss at the stop from here |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for p in a["positions"]:
        o.append(f"| {p['instrument']} | {p['units']} | {_fmt(p['entry'])} | {_fmt(p['mark'])} | {_fmt(p['move_since_entry'] * 100)}% | "
                 f"{_signed(p['unrealized_usd'])} | {_usd(p['notional_usd'])} | {_fmt((p['share_of_gross'] or 0) * 100, 1)}% | "
                 f"{_fmt(p['stop'])} | {_usd(p['loss_at_stop_from_here_usd'])} |")
    c = f["concentration"]
    o += ["", f"Concentration: {c['positions']} positions, the largest {_fmt((c['largest_share_of_gross'] or 0) * 100, 1)}% of the gross; "
          f"by size that is {_fmt(c['effective_positions'], 1)} equal positions, and by risk it is **one**: {c['note']}.", "",
          "### Against a benchmark", "", "| | Since the start | What it is |", "|---|---|---|",
          f"| The desk | {_signed(f['net_after_all_costs'])} | realized plus unrealized, after costs |"]
    for name, label in (("cash", "Cash"), ("same_indices_bought_and_held_at_the_desk_size", "The same indices bought and held"),
                        ("same_positions_fully_invested", "The same positions at one times the account")):
        b = f["benchmarks"][name]
        o.append(f"| {label} | {_signed(b['usd']) if b.get('usd') is not None else 'n/a'} | {b.get('what') or b.get('why')} |")
    o += ["", "### Month by month, against the $4,000 target (a target, never a quota)", "",
          "| Month | Days | Net | Of $4,000 |", "|---|---|---|---|"]
    o += [f"| {m['month']} | {m['days']} | {_signed(m['net'])} | {_fmt(m['of_target'] * 100, 1)}% |" for m in f["monthly"]]
    return o + [""]


def _table(rows: list[dict], first: str) -> list[str]:
    o = [f"| {first} | Positions | Won | Sum | Mean | t | Funding | Price | Costs |", "|---|---|---|---|---|---|---|---|---|"]
    o += [f"| {r['class']} | {r['positions']} | {r['won']} | {_fmt(r['sum_bp'], 0)} bp | {_fmt(r['mean_bp'], 1)} bp | {_fmt(r['t'])} | "
          f"{_fmt(r['funding_bp'], 0)} | {_fmt(r['price_bp'], 0)} | {_fmt(r['cost_bp'], 0)} |" for r in rows]
    return o


def report_radar(a: dict) -> list[str]:
    f, at = a["figures"], a["attribution"]
    ct, pf, ill = f["closed_trades"], f["performance"], f["illustration_usd"]
    s = at["sources"]
    o = ["## 2. RADAR-1: the funding radar's paper ledger", "", *_checks(a), "",
         f"Marks from {_when(f['first_mark'])} to {_when(f['last_mark'])} ({_fmt(f['days'])} days). Paper only: no order is ever sent. "
         "Its preregistered single look is on 2026-12-06 and is read as registered, whatever this audit says.", "",
         f"Capital: {f['capital']}. P&L is in basis points (bp) of one leg's notional; 2,000 bp summed over positions is 1% of the book.",
         "", "| | In bp of N | In % of the book | " + f"On a ${ill['book']:,.0f} book (illustration) |", "|---|---|---|---|",
         f"| **Realized** (closed positions, after every fill) | {_fmt(f['realized_bp'], 1)} | {_fmt(f['realized_pct_of_book'], 4)}% | {_signed(ill['realized'])} |",
         f"| **Unrealized** (open positions at their marks, entry fills paid) | {_fmt(f['unrealized_bp'], 1)} | {_fmt(f['unrealized_pct_of_book'], 4)}% | {_signed(ill['unrealized'])} |",
         f"| The book if every open position were closed now | {_fmt(f['realized_bp'] + f['unrealized_if_closed_now_bp'], 1)} | {_fmt(f['book_pnl_if_closed_now_pct'], 4)}% | {_signed(ill['net_if_closed_now'])} |",
         "", "| | |", "|---|---|",
         f"| Closed positions | {ct['closed']}: {ct['won']} won, {ct['lost']} lost |",
         f"| Win rate | {_fmt((ct['win_rate'] or 0) * 100, 1)}% |" if ct["win_rate"] is not None else f"| Win rate | undefined: {ct['undefined']['win_rate']} |",
         f"| Average win / average loss | {_fmt(ct['average_win'], 1)} bp / {_fmt(ct['average_loss'], 1)} bp |",
         f"| Profit factor | {_fmt(ct['profit_factor'])} |",
         f"| Mean net a position | {_fmt(ct['expectancy'], 1)} bp (t {_fmt(ct['t'])}) |",
         f"| Open positions | {f['open_positions']} of {f['exposure']['slots']} slots; on average {_fmt((f['exposure']['average_share_deployed'] or 0) * 100, 1)}% of the capital was deployed |",
         f"| Book P&L | {_fmt(pf.get('book_pnl_pct'), 4)}% |",
         f"| Book excess over cash ({_fmt(RF * 100, 3)}%/yr on the capital in use) | {_fmt(pf.get('book_excess_pct'), 4)}% |",
         f"| Annualised excess on the capital deployed | {_fmt(pf.get('ann_excess_deployed_pct'), 1)}%/yr |",
         f"| The same with costs x1.5 / x2 | {_fmt(pf.get('ann_excess_deployed_costs_x1.5_pct'), 1)}% / {_fmt(pf.get('ann_excess_deployed_costs_x2_pct'), 1)}% |",
         f"| Maximum drawdown of the book (hourly marks) | {_fmt(pf.get('max_dd_pct'), 4)}% |",
         f"| t of the daily excess | {_fmt(pf.get('t_excess_daily'))} |",
         f"| Best coin, and the book's excess without it | {pf.get('best_coin')}: {_fmt(pf.get('book_excess_without_best_coin_pct'), 4)}% |", "",
         "### Where it came from", "",
         f"Funding received **{_fmt(s['funding_bp'], 0)} bp**, price moves between the legs **{_fmt(s['price_bp'], 0)} bp**, fills "
         f"**-{_fmt(s['cost_bp'], 0)} bp**: net **{_fmt(s['net_bp'], 0)} bp**. A position earned {_fmt(s['gross_per_position_bp'], 1)} bp before "
         f"costs and paid {_fmt(s['cost_per_position_bp'], 1)} bp"
         + (f": the costs are {_fmt(s['cost_over_gross'], 2)} times the gross." if s["cost_over_gross"] is not None else ".")
         + f" Half the positions were closed within {_fmt(at['median_hold_hours'], 1)} hours.", "",
         *_table(at["by_holding_time"], "Held for"), "", *_table(at["by_exit_reason"], "Closed for"), ""]
    for dim, rows in at["known_at_entry"].items():
        o += [*_table(rows, f"Known at the entry: {dim}"), ""]
    cs = at["coins"]
    o += [f"{cs['traded']} coins were traded and {cs['losing']} of them lost. The five worst and the five best:", "",
          *_table(cs["worst"] + cs["best"], "Coin"), ""]
    cn = f["concentration"]
    o += [f"Concentration: the most traded coin ({cn['most_traded_coin']}) is {_fmt((cn['its_share_of_positions'] or 0) * 100, 1)}% of the "
          f"positions; by count the book is {_fmt(cn['effective_coins'], 1)} equal coins. Venue pairs: "
          + ", ".join(f"{k} {v}" for k, v in cn["venue_pairs"].items()) + ".", ""]
    if a["open"]:
        o += ["| Open now | Short / long | Opened | Entry spread | Funding | Price | Fills paid | Net at the marks | Net if closed now |",
              "|---|---|---|---|---|---|---|---|---|"]
        o += [f"| {p['coin']} | {p['short']} / {p['long']} | {_when(p['opened'])} | {_fmt(p['entry_spread_apr'] * 100, 1)}%/yr | {p['funding_bp']} | "
              f"{p['price_bp']} | {p['cost_bp']} | {p['net_bp']} bp | {p['net_if_closed_now_bp']} bp |" for p in a["open"]]
        o += [""]
    return o


def report_engine(eng: dict, hyp: dict) -> list[str]:
    o = ["## 3. The weakness, the hypothesis and the experiment", ""]
    w = hyp.get("weakness")
    if w is None:
        o += [f"No weakness is named this cycle: {hyp.get('why')}.", ""]
    else:
        o += [f"**Largest weakness** (a class known when a position is opened, measured against the rest of the book): "
              f"{w['dimension']}, *{w['class']}*: {w['positions']} positions, mean {_fmt(w['mean_bp'], 1)} bp (t {_fmt(w['t'])}) against "
              f"{_fmt(w['rest_mean_bp'], 1)} bp for the rest (t of the difference {_fmt(w['t_against_the_rest'])}); "
              f"{_fmt(-w['excess_loss_bp'], 0)} bp lost beyond what the rest would have.", ""]
        if hyp.get("variant") is None:
            o += [f"No experiment: {hyp.get('why')}.", ""]
        else:
            o += [f"**Hypothesis.** {hyp['hypothesis']}", "", f"**Tested by** the declared variant `{hyp['variant']}` in the replay below.", ""]
    ar, v = eng.get("archive") or {}, eng.get("validation") or {}
    o += ["### The replay: the radar's frozen rules and the declared variants on the same stored quotes", ""]
    if ar.get("note"):
        o += [f"Archive: {ar['note']}.", ""]
    o += [f"Stored hours in hand: {eng.get('hours', 0)} ({_when(eng.get('first_hour'))} to {_when(eng.get('last_hour'))}); days archived: "
          f"{ar.get('days')}; added this cycle: {', '.join(ar.get('added') or []) or 'none'}.", ""]
    if "variants" not in v:
        o += [f"**{v.get('status', 'NO REPLAY')}**: {v.get('why', 'no stored quotes')}.", ""]
        return o
    fd = eng.get("fidelity")
    if fd:
        o += [f"Fidelity: the replay of the original rules reproduces {fd['same_net']} of the radar's {fd['real_positions']} real positions "
              f"opened in these hours to the hundredth of a basis point ({fd['matched']} matched by entry). Differences: "
              f"{len(fd['only_in_the_real_ledger'])} only in the real ledger, {len(fd['only_in_the_replay'])} only in the replay; "
              f"{fd['explained_by_a_position_held_at_the_start']} of them on a coin the radar already held when the replay began "
              f"({', '.join(fd['held_at_the_start']) or 'none'}). "
              + ("The replay is taken as faithful." if fd["trustworthy"] else "**The replay is NOT faithful enough: read nothing from the table below.**"), ""]
    o += [f"Earlier part {_when(v['start'])} to {_when(v['cut'])}; later part to {_when(v['end'])}. Excess over cash in % of the book.", "",
          "| Variant | What changes | Earlier: excess | positions | Later: excess | positions | closed | t (daily) | Later, less the original | its t |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, x in v["variants"].items():
        e, la, pr = x["earlier"], x["later"], x["against_original_later"]
        what = ", ".join(f"{k}={val}" for k, val in x["parameters"].items()) or "nothing: the registered rules"
        o.append(f"| `{name}` | {what} | {_fmt(e['book_excess_pct'], 4)}% | {e['positions']} | {_fmt(la['book_excess_pct'], 4)}% | {la['positions']} | "
                 f"{la['closed']} | {_fmt(la['t_daily'])} | {_fmt(pr['sum_difference_pct'], 4)}% | {_fmt(pr['t'])} |")
    g = v["gates_on_the_later_part"]
    o += ["", f"Candidate, chosen on the earlier part only: `{v['candidate']}` ({v['configurations_compared']} variants compared). "
          f"**{v['status']}**: {v['why']}.", "",
          "Gates on the later part: " + ", ".join(f"{k.replace('_', ' ')} {'yes' if ok else 'no'}" for k, ok in g.items()) + ".", "",
          "A variant is proposed as a registered challenger only when every gate holds. A proposal is a request for a "
          "preregistered forward test, never a replacement of the original.", "",
          "### Registered challengers, judged forward", ""]
    if not eng["challengers"]:
        o += ["None is registered. RADX-1, the diagnosis these variants came from, failed as registered (one of its two parts "
              "did not hold on the later positions), and by its own rule no challenger follows from it. One is registered only "
              "after a variant passes the gates above.", ""]
    for c in eng["challengers"]:
        o += [f"- `{c['id']}` (`{c['variant']}`), registered {_when(c['registered_t'])}, look {_when(c['look_t'])}: **{c['status']}**. "
              f"Challenger {_fmt(c['challenger']['book_excess_pct'], 4)}% on {c['challenger']['positions']} positions, original "
              f"{_fmt(c['original']['book_excess_pct'], 4)}% on {c['original']['positions']}; difference "
              f"{_fmt(c['challenger_less_original']['sum_difference_pct'], 4)}% (t {_fmt(c['challenger_less_original']['t'])})."]
    return o + [""]


def write_report(out: Path, now: datetime, a_trend, a_radar, eng, hyp, problems: list[str], cycles: int) -> None:
    ok = not problems and all(a is None or a["reconciled"] for a in (a_trend, a_radar))
    ar = []
    if a_trend:
        f = a_trend["figures"]
        ar.append(f"مكتب TRND-1: الرصيد {_usd(f['equity_now'])}، المحقّق {_signed(f['realized_net'])}، غير المحقّق {_signed(f['unrealized'])}، "
                  f"الصفقات المسكّرة {f['closed_trades']['closed']}.")
    if a_radar:
        f = a_radar["figures"]
        ar.append(f"رادار RADAR-1: دفتره {_fmt(f['book_pnl_pct'], 2)}% من رأس ماله الورقي، {f['closed_positions']} صفقة مسكّرة، "
                  f"الرابح منها {f['closed_trades']['won']}.")
    v = (eng.get("validation") or {})
    ar.append("المطابقة: " + ("كل الأرقام تطابقت من مصدرين." if ok else "أكو رقم ما تطابق: شوف القسم المعلّم بالأسفل."))
    status = {"NOT ENOUGH HOURS": "الأسعار المخزونة ما تكفي بعد", "INCONCLUSIVE": "غير حاسمة لأن العيّنة صغيرة",
              "REJECTED": "البديل انرفض", "PROPOSED": "أكو بديل مقترح للتسجيل"}.get(v.get("status"), "ما اشتغلت")
    n = len(eng.get("challengers") or [])
    ar.append(f"تجربة التحسين: {status}. المنافسين المسجّلين: {n}. النظام الأصلي ما انلمس.")
    o = ["# Paper systems: the performance audit and the optimization cycle", "",
         "**PAPER ONLY · NOT REAL MONEY · NOTHING HERE IS A PROFIT CLAIM.** Written by the performance cycle on GitHub's runner "
         "(`scripts/perf_cycle.py`), with no person in the loop. It reads the paper systems' own ledgers, recomputes every "
         "figure by a second route, and changes neither system.", "", "**بالعربي:** " + " ".join(ar), "",
         f"Updated {now:%Y-%m-%d %H:%M} UTC · {PERF_VERSION} · cycles so far: {cycles}", ""]
    if problems:
        o += ["## PROBLEMS THIS CYCLE", ""] + [f"- {p}" for p in problems] + [""]
    o += report_trend(a_trend) if a_trend else ["## 1. TRND-1", "", "The trend desk's files were not available to this run.", ""]
    o += report_radar(a_radar) if a_radar else ["## 2. RADAR-1", "", "The radar's ledger was not available to this run.", ""]
    o += report_engine(eng, hyp)
    o += ["## 4. What is not claimed", "",
          "- An unrealized gain is a valuation at the last close. It is not profit until the trade is closed.",
          "- A variant that loses less than the original has not been shown to earn anything.",
          "- No figure here is a backtest, and none is added to a research result.", ""]
    (out / "PERF_REPORT.md").write_text("\n".join(o))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trend", required=True)
    ap.add_argument("--radar", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--radar-state", default=None)
    ap.add_argument("--challengers", default=str(ROOT / "research" / "perf" / "challengers.json"))
    ap.add_argument("--now", default=None)
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    a_trend = audit_trend(Path(a.trend))
    a_radar, real = audit_radar(Path(a.radar))
    chf = Path(a.challengers)
    challengers = json.loads(chf.read_text()) if chf.exists() else []
    eng = engine(Path(a.radar_state) if a.radar_state else None, out, real, challengers, int(now.timestamp()))
    hyp = hypothesis(a_radar, eng)
    problems = list(eng["problems"])
    for name, au in (("TRND-1", a_trend), ("RADAR-1", a_radar)):
        if au is None:
            problems.append(f"{name}: its files were not available")
        elif not au["reconciled"]:
            problems += [f"{name}: {c['check']}: expected {c['expected']}, found {c['found']}" for c in au["failed_checks"]]
    log = out / "cycles.jsonl"
    cycles = (len(log.read_text().splitlines()) if log.exists() else 0) + 1
    v = eng.get("validation") or {}
    line = {"at": now.isoformat(), "version": PERF_VERSION, "problems": problems,
            "trend": None if a_trend is None else {k: a_trend["figures"][k] for k in ("equity_now", "realized_net", "unrealized", "open_positions")}
            | {"closed": a_trend["figures"]["closed_trades"]["closed"], "checks": len(a_trend["checks"]), "reconciled": a_trend["reconciled"]},
            "radar": None if a_radar is None else {k: a_radar["figures"][k] for k in ("realized_bp", "unrealized_bp", "book_pnl_pct", "closed_positions", "open_positions")}
            | {"checks": len(a_radar["checks"]), "reconciled": a_radar["reconciled"]},
            "weakness": hyp.get("weakness"), "variant": hyp.get("variant"),
            "experiment": {k: v.get(k) for k in ("status", "candidate", "why", "start", "cut", "end")},
            "archive": {k: (eng.get("archive") or {}).get(k) for k in ("added", "days")}, "hours": eng.get("hours"),
            "challengers": [{k: c.get(k) for k in ("id", "variant", "status")} for c in eng["challengers"]]}
    with log.open("a") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
    (out / "paper_audit.json").write_text(json.dumps({"at": now.isoformat(), "version": PERF_VERSION, "trend": a_trend, "radar": a_radar},
                                                     indent=1, sort_keys=True, default=str) + "\n")
    (out / "replay.json").write_text(json.dumps({"at": now.isoformat(), "version": PERF_VERSION, "declared": replay.DECLARED,
                                                 "variants": replay.VARIANTS, "gates": replay.GATES, **eng, "hypothesis": hyp},
                                                indent=1, sort_keys=True, default=str) + "\n")
    write_report(out, now, a_trend, a_radar, eng, hyp, problems, cycles)
    print(json.dumps({"cycle": cycles, "problems": problems, "experiment": line["experiment"]["status"]}))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
