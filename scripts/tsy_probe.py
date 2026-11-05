"""Which public sources can give TSY-1 its auction calendar and its prices? Metadata only: for each source, whether it
answers, its field names, and for each series how many rows it has and its first and last dates. For the auctions it
counts dates by security term and by year, and reads no yield, price or amount. TSY-1 is frozen only after this, on
the sources chosen here. Run on GitHub's runner (the sources are blocked here)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (research; aitrader TSY-1 probe)"}
OUT = Path(__file__).resolve().parent.parent / "research" / "results" / "TSY-probe.json"
YAHOO = ("IEF", "TLT", "^TNX", "^IRX", "ZN=F")
FISCAL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
TDIRECT = "https://www.treasurydirect.gov/TA_WS/securities/search"
#: the only fields read from an auction record: when it was announced and held, and what was sold
CALENDAR_FIELDS = ("auction_date", "announcemt_date", "issue_date", "security_type", "security_term",
                   "original_security_term", "reopening", "inflation_index_security", "floating_rate", "cusip")


def get(url: str) -> tuple[int | None, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception as exc:  # noqa: BLE001 - reported
        return None, str(exc).encode()


def yahoo_meta(sym: str) -> dict:
    status, body = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}"
                       "?period1=0&period2=1790000000&interval=1d")
    if status != 200:
        return {"status": status, "head": body[:160].decode("utf-8", "replace")}
    res = json.loads(body)["chart"]["result"][0]
    ts = res.get("timestamp") or []
    closes = res["indicators"]["quote"][0]["close"]
    adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose") or []
    f = lambda t: datetime.fromtimestamp(t, timezone.utc).date().isoformat()  # noqa: E731
    return {"status": status, "rows": len(ts), "with_close": sum(1 for c in closes if c is not None),
            "with_adjclose": sum(1 for c in adj if c is not None),
            "first": f(ts[0]) if ts else None, "last": f(ts[-1]) if ts else None,
            "timezone": res.get("meta", {}).get("exchangeTimezoneName")}


def summarize(records: list[dict], date_key: str, term_key: str) -> dict:
    terms = Counter(r.get(term_key) for r in records)
    dates = sorted(r[date_key][:10] for r in records if r.get(date_key))
    ten = [r for r in records if "10-Year" in str(r.get(term_key)) or "9-Year" in str(r.get(term_key))]
    flags = Counter((r.get("security_type") or r.get("securityType"), r.get("inflation_index_security")
                     or r.get("inflationIndexSecurity"), r.get("floating_rate") or r.get("floatingRate")) for r in ten)
    return {"records": len(records), "first": dates[0] if dates else None, "last": dates[-1] if dates else None,
            "terms": dict(terms.most_common()), "ten_year_type_inflation_floating": {str(k): v for k, v in
                                                                                    flags.most_common()},
            "ten_year_by_year": dict(sorted(Counter(r[date_key][:4] for r in ten if r.get(date_key)).items())),
            "ten_year_terms": dict(Counter(r.get(term_key) for r in ten).most_common())}


def fiscal_meta() -> dict:
    status, body = get(FISCAL + "?page%5Bsize%5D=1")
    if status != 200:
        return {"status": status, "head": body[:160].decode("utf-8", "replace")}
    fields = sorted(json.loads(body)["meta"]["labels"])  # the field names only; the one record is discarded
    wanted = [f for f in CALENDAR_FIELDS if f in fields]
    q = {"fields": ",".join(wanted), "filter": "security_type:eq:Note,auction_date:gte:1995-01-01",
         "sort": "auction_date", "page[size]": "10000"}
    status, body = get(FISCAL + "?" + urllib.parse.urlencode(q))
    if status != 200:
        return {"status": status, "fields": fields, "head": body[:160].decode("utf-8", "replace")}
    data = json.loads(body)
    return {"status": status, "fields": fields, "read": wanted, "total_count": data["meta"].get("total-count"),
            **summarize(data["data"], "auction_date", "security_term")}


def tdirect_meta() -> dict:
    q = {"format": "json", "type": "Note", "dateFieldName": "auctionDate", "startDate": "01/01/1995",
         "endDate": "12/31/2026"}
    status, body = get(TDIRECT + "?" + urllib.parse.urlencode(q))
    if status != 200:
        return {"status": status, "head": body[:160].decode("utf-8", "replace")}
    rows = json.loads(body)
    fields = sorted(rows[0]) if rows else []
    keep = ("auctionDate", "announcementDate", "issueDate", "securityType", "securityTerm", "originalSecurityTerm",
            "reopening", "inflationIndexSecurity", "floatingRate", "cusip")
    slim = [{k: r.get(k) for k in keep} for r in rows]
    return {"status": status, "fields": fields, **summarize(slim, "auctionDate", "securityTerm"),
            "original_terms": dict(Counter(r.get("originalSecurityTerm") for r in slim).most_common())}


def main() -> int:
    out = {"probed": datetime.now(timezone.utc).isoformat(), "yahoo": {}}
    for sym in YAHOO:
        out["yahoo"][sym] = yahoo_meta(sym)
        print(sym, json.dumps(out["yahoo"][sym]), flush=True)
    out["fiscaldata"] = fiscal_meta()
    print("fiscaldata", json.dumps(out["fiscaldata"])[:3000], flush=True)
    out["treasurydirect"] = tdirect_meta()
    print("treasurydirect", json.dumps(out["treasurydirect"])[:3000], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
