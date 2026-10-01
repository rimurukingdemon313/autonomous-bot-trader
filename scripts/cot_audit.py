"""Audit the CFTC Traders in Financial Futures (TFF) files: DATA AUDIT ONLY, no hypothesis, no signal.

    python scripts/cot_audit.py          # -> data/cot/manifest.json (and prints the summary)

Inputs are the two official CFTC bulk files supplied by the user, kept byte-for-byte under data/cot/:

    fin_fut_txt_2006_2016.zip  -> F_TFF_2006_2016.txt
    fut_fin_txt_2017.zip       -> FinFutYY.txt

Neither ZIP nor its extracted member is modified or committed; the manifest is. Everything the
manifest says is recomputed here from the raw bytes, so it can be re-derived by anyone with the
same two files.

Publication timing (the rule a future study must apply; nothing here uses it to trade):
positions are as of a Tuesday and are normally released the following Friday at 15:30 New York.
A holiday moves the release to the next business day. The release date is NOT in the file, so the
rule is conservative: an observation is available from 17:00 New York on the first weekday on or
after as_of + 6 calendar days (the Monday after a normal Friday release), which also covers the
one-business-day holiday delays. Reports whose release was disrupted by the October 2013 US
government shutdown carry no verifiable release date and are marked UNAVAILABLE, never assigned
a guessed one.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COT = ROOT / "data" / "cot"

COT_AUDIT_VERSION = "cot-audit-1.0.0"
FILES = {"fin_fut_txt_2006_2016.zip": "F_TFF_2006_2016.txt", "fut_fin_txt_2017.zip": "FinFutYY.txt"}
#: the universe's currency futures (CME) and the ICE dollar index; codes as published by the CFTC
FX = {"099741": "EUR", "097741": "JPY", "096742": "GBP", "092741": "CHF", "090741": "CAD", "232741": "AUD",
      "112741": "NZD", "098662": "DXY"}
#: cross-rate futures that exist in the files; recorded so their (in)adequacy is evidence, not assertion
CROSSES = {"299741": "EURGBP (CME)", "399741": "EURJPY (CME)", "299661": "EURJPY small (ICE)",
           "599661": "EURGBP small (ICE)"}
CATEGORIES = ("Dealer", "Asset_Mgr", "Lev_Money", "Other_Rept")
JUDGED = (date(2008, 7, 11), date(2017, 1, 1))  # the frozen judged period of every round so far
HOLDOUT_FROM = date(2017, 1, 1)  # sealed
LAG_DAYS = 6
AVAILABLE_AT_NY = "17:00"
#: October 2013 shutdown: as-of dates whose release was delayed by an unknown amount. Wide on purpose:
#: the CFTC's catch-up schedule is not in the file and could not be fetched, so the window runs from
#: the first missed report until the release schedule is certainly normal again.
UNAVAILABLE = (date(2013, 10, 1), date(2013, 12, 24))


def available_on(as_of: date) -> date | None:
    """The New York date from whose 17:00 an as-of observation may be used, or None if unavailable."""
    if UNAVAILABLE[0] <= as_of <= UNAVAILABLE[1]:
        return None
    d = as_of + timedelta(days=LAG_DAYS)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _as_of(r: dict) -> date:
    return datetime.strptime(r["As_of_Date_In_Form_YYMMDD"].strip(), "%y%m%d").date()


def _report_date(r: dict) -> date:
    s = r["Report_Date_as_YYYY-MM-DD"].strip().split(" ")[0]
    return datetime.strptime(s, "%Y-%m-%d" if "-" in s else "%m/%d/%Y").date()


def audit() -> dict:
    files, rows = {}, []
    for zname, member in FILES.items():
        zb = (COT / zname).read_bytes()
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            if z.testzip() is not None:
                raise SystemExit(f"{zname}: corrupt member")
            names = z.namelist()
            if names != [member]:
                raise SystemExit(f"{zname}: expected only {member}, found {names}")
            info = z.getinfo(member)
            mb = z.read(member)
        ext = COT / "extracted" / member
        if ext.exists() and _sha(ext.read_bytes()) != _sha(mb):
            raise SystemExit(f"{ext} differs from the ZIP member")
        text = mb.decode("latin-1")
        rd = list(csv.DictReader(io.StringIO(text, newline="")))
        kinds = sorted({r.get("FutOnly_or_Combined", "").strip() for r in rd})
        files[zname] = {"zip_sha256": _sha(zb), "zip_bytes": len(zb), "member": member, "member_bytes": len(mb),
                        "member_sha256": _sha(mb), "zip_member_date": datetime(*info.date_time).isoformat(),
                        "rows": len(rd), "columns": len(rd[0]), "report_type": kinds,
                        "as_of": [min(_as_of(r) for r in rd).isoformat(), max(_as_of(r) for r in rd).isoformat()]}
        rows += [(zname, r) for r in rd]

    fx = {}
    for zname, r in rows:
        code = r["CFTC_Contract_Market_Code"].strip()
        if code in FX:
            fx.setdefault(FX[code], []).append((zname, r))

    contracts, all_dates = {}, set()
    for ccy, rs in sorted(fx.items()):
        dates = sorted(_as_of(r) for _, r in rs)
        if len(dates) != len(set(dates)):
            raise SystemExit(f"{ccy}: duplicate as-of dates")
        all_dates |= set(dates)
        problems = {"report_date_mismatch": 0, "missing_or_negative": 0, "identity_long": 0, "identity_short": 0,
                    "categories_vs_total": 0}
        for _, r in rs:
            problems["report_date_mismatch"] += _report_date(r) != _as_of(r)
            num = [k for k in r if k.endswith("_All") and ("Positions" in k or k == "Open_Interest_All")]
            vals = {k: r[k].strip() for k in num}
            if any(v in ("", ".") or float(v) < 0 for v in vals.values()):
                problems["missing_or_negative"] += 1
                continue
            g = {k: float(v) for k, v in vals.items()}
            for side in ("Long", "Short"):
                tot = g[f"Tot_Rept_Positions_{side}_All"]
                problems[f"identity_{side.lower()}"] += abs(tot + g[f"NonRept_Positions_{side}_All"]
                                                            - g["Open_Interest_All"]) > 0.5
                parts = sum(g[f"{c}_Positions_{side}_All"] + g[f"{c}_Positions_Spread_All"] for c in CATEGORIES)
                problems["categories_vs_total"] += abs(parts - tot) > 0.5
        gaps = [(a.isoformat(), b.isoformat(), (b - a).days) for a, b in zip(dates, dates[1:]) if (b - a).days != 7]
        judged = [d for d in dates if JUDGED[0] <= d < JUDGED[1]]
        contracts[ccy] = {
            "code": rs[0][1]["CFTC_Contract_Market_Code"].strip(),
            "market": sorted({r["Market_and_Exchange_Names"].strip() for _, r in rs}),
            "first_as_of": dates[0].isoformat(), "last_as_of": dates[-1].isoformat(), "reports": len(dates),
            "reports_judged_period": len(judged),
            "reports_judged_period_available": sum(available_on(d) is not None for d in judged),
            "reports_holdout": sum(d >= HOLDOUT_FROM for d in dates),
            "gaps_not_7_days": gaps, "non_tuesday_as_of": [d.isoformat() for d in dates if d.weekday() != 1],
            "checks": problems}

    crosses = {}
    for name in CROSSES.values():
        crosses[name] = None  # absent from both files unless found below
    for _, r in rows:
        code = r["CFTC_Contract_Market_Code"].strip()
        if code in CROSSES:
            c = crosses[CROSSES[code]] or {"code": code, "market": r["Market_and_Exchange_Names"].strip(), "as_of": []}
            c["as_of"].append(_as_of(r))
            crosses[CROSSES[code]] = c
    for name, c in crosses.items():
        if c:
            ds = sorted(c.pop("as_of"))
            c.update(first_as_of=ds[0].isoformat(), last_as_of=ds[-1].isoformat(), reports=len(ds),
                     reports_judged_period=sum(JUDGED[0] <= d < JUDGED[1] for d in ds))

    # weeks present for some currency but missing for another: reported, never filled
    union = sorted(all_dates)
    missing = {c: [d.isoformat() for d in union if d.isoformat() not in
                   {x for x in [_as_of(r).isoformat() for _, r in fx[c]]}] for c in sorted(fx)}
    return {
        "version": COT_AUDIT_VERSION,
        "source": "CFTC Traders in Financial Futures, Futures-Only, historical bulk files supplied by the user; "
                  "kept unmodified, not committed",
        "files": files,
        "date_field": "As_of_Date_In_Form_YYMMDD (authoritative; Report_Date_as_YYYY-MM-DD mixes two formats "
                      "and agrees with it on every FX row)",
        "contracts": contracts,
        "cross_rate_futures": crosses,
        "missing_weeks_vs_union": {c: v for c, v in missing.items() if v},
        "publication_rule": {
            "positions": "as of Tuesday (holiday weeks: another weekday)",
            "normal_release": "Friday 15:30 New York; next business day after a holiday",
            "rule": f"available from {AVAILABLE_AT_NY} New York on the first weekday >= as_of + {LAG_DAYS} days",
            "unavailable_as_of": [UNAVAILABLE[0].isoformat(), UNAVAILABLE[1].isoformat()],
            "unavailable_reason": "October 2013 US government shutdown: release dates delayed and not verifiable "
                                  "offline; excluded, never assigned a guessed date",
            "release_dates_in_file": False},
        "holdout": f"as-of >= {HOLDOUT_FROM.isoformat()} (all of fut_fin_txt_2017.zip) is sealed",
        "interpolation": "none: a missing week is missing",
    }


def main() -> int:
    m = audit()
    (COT / "manifest.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    for ccy, c in m["contracts"].items():
        print(f"{ccy:4} {c['code']} {c['first_as_of']} -> {c['last_as_of']} n={c['reports']} "
              f"judged={c['reports_judged_period']} avail={c['reports_judged_period_available']} "
              f"holdout={c['reports_holdout']} gaps={len(c['gaps_not_7_days'])} checks={c['checks']}")
    for name, c in m["cross_rate_futures"].items():
        print(name, c and {k: c[k] for k in ("first_as_of", "last_as_of", "reports", "reports_judged_period")})
    print("missing vs union:", m["missing_weeks_vs_union"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
