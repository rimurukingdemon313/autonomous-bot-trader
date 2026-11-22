"""UDL-1's data probe: are Upbit's delisting notices reachable, and how many dated exits do they give?
(docs/ORIGINAL_EDGE_HUNT_2.md, B1). Runs on GitHub's runner (.github/workflows/udl1.yml): Upbit is not reachable
from the research director's session.

    python scripts/udl1.py probe [--out FILE]

Titles, notice dates and the termination times written in the notices only: no price is read, and nothing is
judged. UDL-1 is preregistered only if this probe finds enough dated exits of coins Binance also quotes; otherwise
it waits for data, and is not failed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aitrader.research.dlab.feeds import get  # noqa: E402
import scripts.sqz1 as Z  # noqa: E402  (the S3 listing reader)

R = ROOT / "research"
PROBE = R / "results" / "UDL-1-probe.json"
UDL_PROBE_VERSION = "udl-probe-1.0.0"
#: the notice lists Upbit's own pages read, tried in turn (Upbit has moved them before); the first that answers is used
LISTS = ("https://api-manager.upbit.com/api/v1/announcements?os=web&page={page}&per_page=20&category=trade",
         "https://api-manager.upbit.com/api/v1/announcements?os=web&page={page}&per_page=20&category=all",
         "https://api-manager.upbit.com/api/v1/notices?page={page}&per_page=20&thread_name=general")
DETAILS = ("https://api-manager.upbit.com/api/v1/announcements/{id}",
           "https://api-manager.upbit.com/api/v1/notices/{id}")
END = ("거래지원 종료", "거래 지원 종료")  # "end of trading support"
NOT_AN_EXIT = ("연기", "철회", "취소", "유지")  # postponed, withdrawn, cancelled, kept
TICKER = re.compile(r"\(([A-Z0-9][A-Z0-9 ,/·]{1,80})\)")
WHEN = re.compile(r"(20\d\d)[.\-/년 ]+\s*(\d{1,2})[.\-/월 ]+\s*(\d{1,2})[일 ]*[^0-9]{0,12}?(\d{1,2}):(\d{2})")


def _items(obj) -> list[dict]:
    """Every dict with a title, wherever the list sits in the response."""
    if isinstance(obj, dict):
        if "title" in obj and isinstance(obj.get("title"), str):
            return [obj]
        out = []
        for v in obj.values():
            out += _items(v)
        return out
    if isinstance(obj, list):
        out = []
        for v in obj:
            out += _items(v)
        return out
    return []


def _date(n: dict) -> str | None:
    for k in ("listed_at", "first_listed_at", "created_at", "updated_at", "date"):
        v = n.get(k)
        if isinstance(v, str) and v[:4].isdigit():
            return v
    return None


def tickers(title: str) -> list[str]:
    out = []
    for g in TICKER.findall(title):
        for tok in re.split(r"[ ,/·]+", g):
            if re.fullmatch(r"[A-Z0-9]{2,12}", tok) and not tok.isdigit():
                out.append(tok)
    return sorted(set(out))


def termination(text: str) -> str | None:
    """The first full date and time written in a notice (its termination time, KST), as ISO, or None."""
    m = WHEN.search(text or "")
    if not m:
        return None
    y, mo, d, hh, mm = (int(x) for x in m.groups())
    try:
        return datetime(y, mo, d, hh, mm).isoformat() + "+09:00"
    except ValueError:
        return None


def notices(fetch=get, pages: int = 200, pause: float = 0.2) -> tuple[str | None, list[dict], dict]:
    shape = {}
    for tmpl in LISTS:
        got, ok = [], False
        for page in range(1, pages + 1):
            try:
                body = fetch(tmpl.format(page=page))
            except RuntimeError as e:
                shape[tmpl] = f"error: {str(e)[:160]}"
                break
            if body is None:
                shape[tmpl] = "404"
                break
            try:
                js = json.loads(body)
            except ValueError:
                shape[tmpl] = "not JSON"
                break
            items = _items(js)
            if page == 1:
                shape[tmpl] = {"keys": sorted(js) if isinstance(js, dict) else type(js).__name__, "items": len(items)}
            if not items:
                break
            ok = True
            got += items
            time.sleep(pause)
        if ok:
            return tmpl, got, shape
    return None, [], shape


def probe(fetch=get, now: datetime | None = None, detail_pause: float = 0.2) -> dict:
    now = now or datetime.now(timezone.utc)
    used, items, shape = notices(fetch)
    exits = []
    for n in items:
        title = n.get("title", "")
        if not any(k in title for k in END):
            continue
        e = {"id": n.get("id"), "title": title, "posted": _date(n), "tickers": tickers(title),
             "flagged": [w for w in NOT_AN_EXIT if w in title], "termination_kst": termination(title)}
        if e["termination_kst"] is None and e["id"] is not None:
            for tmpl in DETAILS:
                try:
                    body = fetch(tmpl.format(id=quote(str(e["id"]), safe="")))
                except RuntimeError:
                    continue
                if body:
                    try:
                        text = json.dumps(json.loads(body), ensure_ascii=False)
                    except ValueError:
                        text = body.decode("utf-8", "replace")
                    e["termination_kst"] = termination(text.split("종료", 1)[-1]) or termination(text)
                    if e["termination_kst"]:
                        break
            time.sleep(detail_pause)
        exits.append(e)
    codes = sorted({t for e in exits for t in e["tickers"]})
    binance = {}
    for c in codes:
        keys = Z.listing(f"data/spot/monthly/klines/{c}USDT/1h/", fetch)[1]
        ms = sorted(k.rsplit("-1h-", 1)[1][:7] for k in keys if k.endswith(".zip") and "-1h-" in k)
        if ms:
            binance[c] = ms
    dated = [e for e in exits if e["termination_kst"] and not e["flagged"]]
    usable = [(e, t) for e in dated for t in e["tickers"] if t in binance
              and e["termination_kst"][:7] in binance[t]]
    by_year: dict[str, int] = {}
    for e, _t in usable:
        by_year[e["termination_kst"][:4]] = by_year.get(e["termination_kst"][:4], 0) + 1
    return {"retrieved": now.isoformat(), "version": UDL_PROBE_VERSION,
            "what": "notice titles, notice dates and the termination times they state; file names on Binance's "
                    "archive. No price was read",
            "list_used": used, "list_shapes": shape, "notices_read": len(items), "exit_notices": len(exits),
            "dated_exits": len(dated), "codes": codes, "binance_1h": binance,
            "usable_coin_exits": len(usable), "usable_by_year": dict(sorted(by_year.items())), "exits": exits}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("probe",))
    ap.add_argument("--out", default=str(PROBE))
    a = ap.parse_args(argv)
    body = probe(now=datetime.now(timezone.utc))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({k: body[k] for k in ("list_used", "notices_read", "exit_notices", "dated_exits",
                                           "usable_coin_exits", "usable_by_year")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
