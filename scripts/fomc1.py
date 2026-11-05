"""FOMC-1: the pre-FOMC announcement drift, on the US 500 index CFD (research/preregistrations/FOMC-1.md).

The owner, 2026-11-05: "don't fixate on the AI trading; anything that makes us a profit; never stop". Lucca & Moench
(2015, "The Pre-FOMC Announcement Drift", Journal of Finance) found that from 1994 to 2011 the S&P 500 rose about
49 bps on average in the 24 hours before scheduled FOMC announcements: a large share of the equity premium of the
period, earned on eight days a year. The paper circulated from 2011 (New York Fed Staff Report 512). Kurov, Wolfe &
Gilbert (2021) report that the drift faded later. FOMC-1 asks one question: did it survive its publication, at a
retail CFD's real costs?

The rule, fixed before any FOMC-1 price was fetched:
- events: the scheduled FOMC meetings whose statement was released at 2:00 pm New York time, 2013-01 to 2026-09
  (EVENTS). Each is checked against the Fed's own press release before any price is fetched (`calendar`): its page
  must exist, be the FOMC statement and say 2:00 p.m. One that fails stops everything after it;
- buy the US 500 CFD at the ASK at 14:00 New York on the weekday before the statement (the close of the minute that
  ends then), and sell at the BID at 13:55 New York on the statement's day, five minutes before it;
- costs: the quoted spread at both fills, slippage of a quarter of the quoted spread at each fill, and overnight
  financing at the US policy rate public that day plus 2.5% a year, day count 360, for each night held;
- a missing quote at either time is no trade, never filled;
- the control: the same clock window on the same weekdays one week before and one week after each event, with the
  same costs. The drift must beat it, or it is only the market's rise.

    python scripts/fomc1.py calendar     # verify EVENTS on federalreserve.gov (reads no price)
    python scripts/fomc1.py spec         # freeze the design (reads no price)
    python scripts/fomc1.py preregister  # register FOMC-1 in research/registry.jsonl
    python scripts/fomc1.py fetch        # Dukascopy minute quotes (on GitHub's runner: blocked here)
    python scripts/fomc1.py judge        # 2013..2021: development, validation, the gates
    python scripts/fomc1.py holdout      # only if FOMC-1 PASSED: 2022-01..2026-09, once

Each command after `spec` refuses to run if the code or the spec changed since registration. Nothing here changes the
bot.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time as _time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.research.registry import Holdout, Registry, Trial, Use, Verdict, bonferroni_t  # noqa: E402
from scripts.xts1 import stats  # noqa: E402

R = ROOT / "research"
PID, HID = "FOMC-1", "FOMC-1-H"
DOC = "research/preregistrations/FOMC-1.md"
SPEC = R / "specs" / "FOMC-1.json"
OUT = R / "knowledge"
DATA = ROOT / "data" / "fomc"
CODE = ("scripts/fomc1.py", "scripts/xts1.py", "scripts/ingest_dukascopy_candles.py")
UNIVERSE = "index-cfd-intraday"
SYMBOL, BAND = "USA500IDXUSD", (500.0, 9000.0)
NEW_YORK = ZoneInfo("America/New_York")
ENTRY_NY, EXIT_NY = (14, 0), (13, 55)  # the close of the minute that ENDS at these New York times
DEV = (date(2013, 1, 1), date(2018, 1, 1))
VAL = (date(2018, 1, 1), date(2022, 1, 1))
JUDGE = (DEV[0], VAL[1])
HOLD = (date(2022, 1, 1), date(2026, 10, 1))
SLIP_SPREAD = 0.25     # slippage at each fill, as a share of the spread quoted then
MARKUP_PA = 2.5        # the CFD's financing over the US policy rate, % a year, day count 360
TESTS = 2              # the mean's t (G1) and the event-against-control t (G6)
UA = {"User-Agent": "Mozilla/5.0 (research; aitrader FOMC-1)"}
FED = "https://www.federalreserve.gov/newsevents/pressreleases/monetary{d:%Y%m%d}a.htm"

#: the statement days of the scheduled meetings, 2:00 pm New York. 2020 has seven: its March meeting was replaced by
#: the unscheduled Sunday decision of 15 March, which had no 2:00 pm statement
EVENTS = tuple(date.fromisoformat(d) for d in """
2013-01-30 2013-03-20 2013-05-01 2013-06-19 2013-07-31 2013-09-18 2013-10-30 2013-12-18
2014-01-29 2014-03-19 2014-04-30 2014-06-18 2014-07-30 2014-09-17 2014-10-29 2014-12-17
2015-01-28 2015-03-18 2015-04-29 2015-06-17 2015-07-29 2015-09-17 2015-10-28 2015-12-16
2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16
""".split())

GATES = {
    "t": "t of the mean net return per event over 2013..2021 >= the threshold",
    "development": "mean net per event > 0 in 2013..2017",
    "validation": "mean net per event > 0 in 2018..2021",
    "costs_x2": "mean net per event > 0 with every cost doubled",
    "top_year": "no calendar year supplies more than 50% of the total net",
    "timing": "the events beat the same window a week before and after: mean difference > 0, Welch t >= 2.0",
}
HOLDOUT_RULE = ("2022-01..2026-09: mean net per event > 0 with one-sided t >= 1.645, mean net > 0 with every cost "
                "doubled, and the events' mean above the controls' mean")


def code_hash() -> str:
    h = hashlib.sha256()
    for p in CODE:
        h.update((ROOT / p).read_bytes())
    return h.hexdigest()


def spec_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()


def threshold(reg: Registry) -> float:
    return max(3.0, bonferroni_t(reg.tests_on(UNIVERSE, JUDGE[0], HOLD[1]) + TESTS))


def spec(reg: Registry) -> dict:
    return {"program": PID, "question": "is the US 500 CFD's return from 14:00 New York on the day before a "
                                        "scheduled FOMC statement to 13:55 on its day positive after real costs, "
                                        "and above the same window on ordinary weeks?",
            "instrument": SYMBOL, "events": [str(d) for d in EVENTS], "entry_ny": "14:00 (day before, ask)",
            "exit_ny": "13:55 (statement day, bid)", "slippage_share_of_spread": SLIP_SPREAD,
            "financing": f"US policy rate public that day + {MARKUP_PA}%/yr, day count 360, per night held",
            "control": "the same window, same weekdays, one week before and one week after each event",
            "data": "Dukascopy minute bid and ask candles (datafeed), the two minutes of each day kept, the file's "
                    "sha256 in the manifest; events verified on federalreserve.gov first",
            "periods": {"development": [str(d) for d in DEV], "validation": [str(d) for d in VAL],
                        "holdout": [str(d) for d in HOLD]},
            "gates": GATES, "holdout_rule": HOLDOUT_RULE, "threshold_t": round(threshold(reg), 4), "tests": TESTS,
            "after": {"PASSED and VALIDATED": "proposed to the owner as a paper strategy of its own (rule 14), sized "
                                              "by the risk engine, followed forward on paper; never real money",
                      "otherwise": "reported as it is; nothing changes"}}


def _dump(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def _write(name: str, body: dict) -> dict:
    body = json.loads(json.dumps(body, sort_keys=True, default=str))
    body["sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(_dump(body))
    return body


# ── the windows ──────────────────────────────────────────────────────────

def previous_weekday(d: date) -> date:
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def windows(events=EVENTS) -> list[dict]:
    """Each event's window, and its two controls: the same weekdays a week before and a week after."""
    out = []
    for e in events:
        for kind, shift in (("event", 0), ("control", -7), ("control", 7)):
            d = e + timedelta(days=shift)
            out.append({"kind": kind, "event": e, "entry_day": previous_weekday(d), "exit_day": d})
    return out


def minute_end(d: date, hm: tuple[int, int]) -> int:
    """The epoch at which the minute ENDING at New York time `hm` on `d` starts: its close is the last quote
    before hm."""
    end = datetime(d.year, d.month, d.day, hm[0], hm[1], tzinfo=NEW_YORK)
    return int(end.timestamp()) - 60


# ── the calendar, checked at its source ─────────────────────────────────

RELEASE = re.compile(r"for\s+(?:immediate\s+)?release(?:\s+at\s+[0-9:]{1,5}\s*[ap]\.?\s*m\.?(?:\s*E[SD]T)?)?", re.I)


def page_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|&nbsp;", " ", html))


def release_phrase(html: str) -> str | None:
    """The page's own words for when it was released ("For release at 2:00 p.m. EDT"), or None."""
    m = RELEASE.search(page_text(html))
    return m.group(0) if m else None


def verify_page(html: str) -> str | None:
    """None if the page is the FOMC statement and says it was released at 2:00 p.m., else why not."""
    if "FOMC statement" not in page_text(html):
        return "not the FOMC statement"
    if not re.search(r"2:00\s*p\.?\s*m", release_phrase(html) or ""):
        return f"not released at 2:00 p.m. (the page says: {release_phrase(html)!r})"
    return None


def cmd_calendar() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in EVENTS:
        url, why, said = FED.format(d=d), None, None
        for k in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                    html = r.read().decode("utf-8", "replace")
                why, said = verify_page(html), release_phrase(html)
                break
            except urllib.error.HTTPError as exc:
                why = f"HTTP {exc.code}"
                if exc.code == 404:
                    break
            except Exception as exc:  # noqa: BLE001 - retried, then recorded
                why = f"{type(exc).__name__}: {exc}"
            _time.sleep(5 * 2 ** k)
        rows.append({"date": str(d), "url": url, "ok": why is None, "why": why, "release": said})
        print(d, "ok" if why is None else why, flush=True)
        _time.sleep(1.0)
    per_year: dict = {}
    for d in EVENTS:
        per_year[d.year] = per_year.get(d.year, 0) + 1
    body = {"checked": datetime.now(timezone.utc).isoformat(), "events": rows, "per_year": per_year,
            "all_ok": all(r["ok"] for r in rows)}
    (DATA / "calendar.json").write_text(_dump(body))
    print("all ok" if body["all_ok"] else f"FAILED: {[r['date'] for r in rows if not r['ok']]}")


def _calendar_ok() -> None:
    cal = json.loads((DATA / "calendar.json").read_text())
    if [r["date"] for r in cal["events"]] != [str(d) for d in EVENTS] or not cal["all_ok"]:
        raise SystemExit("the calendar was not verified as listed: nothing is fetched or judged")


# ── the prices ───────────────────────────────────────────────────────────

def cmd_fetch() -> None:
    """For every day a window needs, the minutes that end at 14:00 and at 13:55 New York, bid and ask closes."""
    from scripts.ingest_dukascopy_candles import day_minutes, scale_for
    _calendar_ok()
    days = sorted({w[k] for w in windows() for k in ("entry_day", "exit_day")})
    raw, failed = [], []
    for d in days:
        m, status = day_minutes(SYMBOL, d, pace=0.5)
        if m is None:
            failed.append(str(d))
            continue
        for hm in (ENTRY_NY, EXIT_NY):
            hit = m[m[:, 0] == minute_end(d, hm)] if len(m) else m
            if len(hit):
                raw.append((d, hm, float(hit[0, 4]), float(hit[0, 8])))
        print(d, status, flush=True)
    if failed:
        raise SystemExit(f"{len(failed)} days could not be fetched ({failed[:5]}...): nothing is filled")
    scale = scale_for(sorted(r[2] for r in raw)[len(raw) // 2], BAND)
    body = "date,time_ny,bid,ask\n" + "".join(f"{d},{h:02d}:{m:02d},{b * scale!r},{a * scale!r}\n"
                                               for d, (h, m), b, a in raw)
    (DATA / "quotes.csv").write_text(body)
    (DATA / "manifest.json").write_text(_dump({
        "retrieved": datetime.now(timezone.utc).isoformat(), "symbol": SYMBOL, "scale": scale, "days": len(days),
        "rows": len(raw), "file": "quotes.csv", "sha256": hashlib.sha256(body.encode()).hexdigest()}))
    print("days", len(days), "quotes", len(raw), "scale", scale)


def load(until: date) -> dict[tuple[date, str], tuple[float, float]]:
    """The quotes of the days before `until`, only if the file matches its manifest: the judge never reads the
    holdout."""
    man = json.loads((DATA / "manifest.json").read_text())
    body = (DATA / man["file"]).read_text()
    if hashlib.sha256(body.encode()).hexdigest() != man["sha256"]:
        raise SystemExit(f"{man['file']} does not match its manifest: nothing is judged on it")
    out = {}
    for ln in body.strip().splitlines()[1:]:
        d, t, b, a = ln.split(",")
        day, bid, ask = date.fromisoformat(d), float(b), float(a)
        if day >= until:
            continue
        if not (BAND[0] <= bid <= ask <= BAND[1]):
            raise SystemExit(f"{d} {t}: an implausible or crossed quote ({bid}, {ask}): refused, never repaired")
        out[(day, t)] = (bid, ask)
    return out


# ── the rule, and what it earned ─────────────────────────────────────────

def window_net(quotes: dict, w: dict, rate_pct, cost_x: float = 1.0) -> dict | None:
    """One window's mid-to-mid return and its net after the spread, slippage and financing; None if a quote is
    missing (no trade, never filled)."""
    a = quotes.get((w["entry_day"], f"{ENTRY_NY[0]:02d}:{ENTRY_NY[1]:02d}"))
    b = quotes.get((w["exit_day"], f"{EXIT_NY[0]:02d}:{EXIT_NY[1]:02d}"))
    if a is None or b is None:
        return None
    mid_in, mid_out = (a[0] + a[1]) / 2, (b[0] + b[1]) / 2
    gross = mid_out / mid_in - 1
    spread = (a[1] - a[0]) / mid_in + (b[1] - b[0]) / mid_out
    rate = rate_pct(w["entry_day"])
    if rate is None or not math.isfinite(rate):
        return None  # financing unknown: no trade, never assumed
    nights = (w["exit_day"] - w["entry_day"]).days
    cost = spread / 2 + SLIP_SPREAD * spread + nights * (rate + MARKUP_PA) / 100 / 360
    return {"gross": gross, "cost": cost, "net": gross - cost_x * cost}


def book(quotes: dict, start: date, end: date, rate_pct, cost_x: float = 1.0) -> dict[str, list]:
    """The events' and the controls' windows in [start, end), by the exit day, with their nets."""
    out: dict[str, list] = {"event": [], "control": []}
    for w in windows():
        if not start <= w["exit_day"] < end or not start <= w["event"] < end:
            continue
        r = window_net(quotes, w, rate_pct, cost_x)
        if r is not None:
            out[w["kind"]].append({**w, **r})
    return out


def welch(a: list[float], b: list[float]) -> dict:
    if len(a) < 2 or len(b) < 2:
        return {"mean": None, "t": None}
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    return {"mean": ma - mb, "t": (ma - mb) / se if se > 0 else None, "events": len(a), "controls": len(b)}


def gates(quotes: dict, rate_pct, thr: float) -> dict:
    b = book(quotes, *JUDGE, rate_pct)
    ev = b["event"]
    x = [w["net"] for w in ev]
    s = stats(x)
    dev = stats([w["net"] for w in ev if w["exit_day"] < VAL[0]])
    val = stats([w["net"] for w in ev if w["exit_day"] >= VAL[0]])
    x2 = stats([w["net"] for w in book(quotes, *JUDGE, rate_pct, cost_x=2.0)["event"]])
    by_year: dict = {}
    for w in ev:
        by_year[w["exit_day"].year] = by_year.get(w["exit_day"].year, 0.0) + w["net"]
    total = sum(x)
    top = max(by_year.values()) / total if total > 0 and by_year else None
    tm = welch(x, [w["net"] for w in b["control"]])
    ok = {"t": s["t"] is not None and s["t"] >= thr,
          "development": (dev["mean"] or 0) > 0, "validation": (val["mean"] or 0) > 0,
          "costs_x2": (x2["mean"] or 0) > 0, "top_year": top is not None and top <= 0.5,
          "timing": (tm["mean"] or 0) > 0 and tm["t"] is not None and tm["t"] >= 2.0}
    per_event = {k: s.get(k) for k in ("n", "mean", "t", "sd")}
    return {"net_per_event": per_event, "development": dev, "validation": val, "costs_x2": x2,
            "gross_mean": sum(w["gross"] for w in ev) / len(ev) if ev else None,
            "cost_mean": sum(w["cost"] for w in ev) / len(ev) if ev else None,
            "hit_rate": sum(1 for v in x if v > 0) / len(x) if x else None,
            "controls": stats([w["net"] for w in b["control"]]), "timing": tm,
            "by_year": {str(k): round(v, 5) for k, v in sorted(by_year.items())},
            "top_year_share": None if top is None else round(top, 3),
            "events_listed": sum(1 for d in EVENTS if JUDGE[0] <= d < JUDGE[1]),
            "events": [{"day": str(w["exit_day"]), "gross": round(w["gross"], 6), "net": round(w["net"], 6)}
                       for w in ev],
            "threshold_t": thr, "gates": ok, "failed_gates": [g for g, v in ok.items() if not v],
            "passed": all(ok.values())}


# ── the commands ─────────────────────────────────────────────────────────

def _registry() -> Registry:
    return Registry.load(R / "registry.jsonl", Holdout.load(R / "holdout.json"))


def _rates():
    from aitrader.research.discovery.rc import Rates
    rates = Rates(ROOT / "data" / "rc" / "policy_rates.csv")
    return lambda d: rates.at("US", d)


def _check_frozen(reg: Registry) -> dict:
    trial = reg.get(PID)
    frozen = json.loads(SPEC.read_text())
    if trial.design.get("spec_sha256") != frozen["sha256"] or frozen["code_sha256"] != code_hash():
        raise SystemExit("the spec or the code differs from what was preregistered")
    return frozen


def cmd_spec() -> None:
    reg = _registry()
    if any(t.id == PID for t in reg.trials):
        raise SystemExit(f"{PID} is registered; its spec is frozen")
    _calendar_ok()
    s = spec(reg)
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(_dump({"spec": s, "sha256": spec_sha(s), "code_sha256": code_hash()}))
    print(spec_sha(s), "threshold", s["threshold_t"])


def cmd_preregister(now: datetime) -> None:
    reg = _registry()
    frozen = json.loads(SPEC.read_text())
    s = spec(reg)
    if spec_sha(s) != frozen["sha256"] or code_hash() != frozen["code_sha256"]:
        raise SystemExit("the spec or the code changed since `spec`")
    if frozen["sha256"] not in (ROOT / DOC).read_text():
        raise SystemExit(f"{DOC} must quote the spec sha256 {frozen['sha256']}")
    reg.register(Trial(id=PID, registered=now, title="FOMC-1: the pre-FOMC announcement drift, US 500 CFD",
                       hypothesis=s["question"], uses=(Use(UNIVERSE, JUDGE[0], JUDGE[1], "judge"),), tests=TESTS,
                       configurations=TESTS, preregistration=DOC,
                       design={"spec_sha256": frozen["sha256"], "code_sha256": frozen["code_sha256"],
                               "threshold_t": s["threshold_t"]}))
    print("registered", PID, "threshold", s["threshold_t"])


def cmd_judge(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    if reg.verdict_of(PID) is not None:
        raise SystemExit(f"{PID} already has a verdict")
    _calendar_ok()
    res = gates(load(JUDGE[1]), _rates(), frozen["spec"]["threshold_t"])
    body = _write(PID, {"program": PID, "verdict": "PASSED" if res["passed"] else "FAILED", **res,
                        "periods": frozen["spec"]["periods"], "spec_sha256": frozen["sha256"],
                        "code_sha256": frozen["code_sha256"], "data": json.loads((DATA / "manifest.json").read_text())})
    reg.record_verdict(Verdict(PID, now, body["verdict"], {"artifact": f"research/knowledge/{PID}.json",
                                                           "artifact_sha256": body["sha256"]}))
    print(body["verdict"], "failed:", res["failed_gates"], "per event", json.dumps(res["net_per_event"]),
          "gross", res["gross_mean"], "cost", res["cost_mean"], "timing", json.dumps(res["timing"]))


def cmd_holdout(now: datetime) -> None:
    reg = _registry()
    frozen = _check_frozen(reg)
    judged = json.loads((OUT / f"{PID}.json").read_text())
    if judged["verdict"] != "PASSED":
        raise SystemExit("FOMC-1 did not pass: the holdout stays unread")
    if any(t.id == HID for t in reg.trials):
        raise SystemExit("the holdout was opened once already")
    reg.register(Trial(id=HID, registered=now, title="FOMC-1 holdout: 2022-01..2026-09", hypothesis=HOLDOUT_RULE,
                       uses=(Use(UNIVERSE, HOLD[0], HOLD[1], "judge"),), tests=1, configurations=1,
                       preregistration=DOC, design={"spec_sha256": frozen["sha256"]}))
    quotes, rates = load(HOLD[1]), _rates()
    b = book(quotes, *HOLD, rates)
    x = [w["net"] for w in b["event"]]
    s = stats(x)
    s2 = stats([w["net"] for w in book(quotes, *HOLD, rates, cost_x=2.0)["event"]])
    tm = welch(x, [w["net"] for w in b["control"]])
    ok = bool(s["mean"] and s["mean"] > 0 and s["t"] is not None and s["t"] >= NormalDist().inv_cdf(0.95)
              and (s2["mean"] or 0) > 0 and (tm["mean"] or 0) > 0)
    verdict = "PASSED" if ok else "FAILED"
    body = _write(HID, {"program": HID, "holdout_of": PID, "period": [str(d) for d in HOLD],
                        "net_per_event": {k: s.get(k) for k in ("n", "mean", "t", "sd")}, "costs_x2": s2,
                        "timing": tm, "rule": HOLDOUT_RULE, "classification": "VALIDATED" if ok else "REJECTED",
                        "verdict": verdict})
    reg.record_verdict(Verdict(HID, now, verdict, {"artifact": f"research/knowledge/{HID}.json",
                                                   "artifact_sha256": body["sha256"]}))
    print(verdict, json.dumps(body["net_per_event"]), "x2", s2["mean"], "timing", tm["mean"])


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now(timezone.utc)  # the command line's clock: every function above takes its dates as arguments
    {"calendar": cmd_calendar, "spec": cmd_spec, "preregister": lambda: cmd_preregister(now), "fetch": cmd_fetch,
     "judge": lambda: cmd_judge(now), "holdout": lambda: cmd_holdout(now)}.get(cmd, lambda: print(__doc__))()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
