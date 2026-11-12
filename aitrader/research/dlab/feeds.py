"""What the lab fetches by itself, on a machine that can reach the sources (GitHub's runner; not the development box).

- `crypto_daily`: Binance USDT-M perpetuals from data.binance.vision: daily klines and funding settlements, month by
  month, each file checked against its published CHECKSUM. Only the months not yet held are fetched.
- `etf_daily`: adjusted daily closes of US-listed ETFs, and the VIX, from Yahoo's chart endpoint.
- `papers`: recent papers from arXiv's quantitative-finance listings and from OpenAlex searches, for the
  research-source database. Titles, dates, links and abstracts only: nothing is claimed about a paper that was not read.

Every fetch is a read with no side effect, so it retries with bounded backoff. A file that is not there (a coin not yet
listed, or delisted) is not an error. A file that fails its checksum stops the fetch: nothing is filled. A file the
archive did not answer for is counted as failed and asked for again by the next fetch; what did arrive is kept, and
the dataset is not complete until none has failed. Each dataset gets a manifest with its content hash and a quality
report (rows, first and last day, missing days, suspect moves).

A manifest's `incomplete` says, in words, why the files are not a whole panel, or is None. Nothing is scanned, judged
or marked forward on an incomplete panel (scripts/lab_cycle.py). Two ways a panel can be whole in its files and holed
in its newest rows are looked for here: a month the archive has published for some instruments and not yet for the
others, and a fund the source served with a series that stops early.

A perpetual is alive on a day it is both priced and funded. The archive goes on printing a delisted contract's last
price, day after day, long after its funding stopped (nine of the fifty-five on 2026-11-12, one for 499 days): those
closes are kept as they came and make no return, because a day without funding has none (datasets.crypto_daily). A
contract that was not alive at the end of last month is not waited for this month.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (compatible; research-data-fetch/1.0)"}  # generic: it names no person and no project
PAUSE = 0.4  # seconds between two requests to the fund source: thirty-two in a row, asked for politely
VISION = "https://data.binance.vision/data/futures/um/monthly/"
#: USDT-M perpetuals listed on Binance by the end of September 2020, as far as is known: chosen by listing date, not
#: by what became of them, so the coins that later died are in the panel too. A symbol with no files is simply absent.
PERPS = ("BTCUSDT", "ETHUSDT", "BCHUSDT", "XRPUSDT", "EOSUSDT", "LTCUSDT", "TRXUSDT", "ETCUSDT", "LINKUSDT", "XLMUSDT",
         "ADAUSDT", "XMRUSDT", "DASHUSDT", "ZECUSDT", "XTZUSDT", "BNBUSDT", "ATOMUSDT", "ONTUSDT", "IOTAUSDT",
         "BATUSDT", "VETUSDT", "NEOUSDT", "QTUMUSDT", "IOSTUSDT", "THETAUSDT", "ALGOUSDT", "ZILUSDT", "KNCUSDT",
         "ZRXUSDT", "COMPUSDT", "OMGUSDT", "DOGEUSDT", "SXPUSDT", "KAVAUSDT", "BANDUSDT", "RLCUSDT", "WAVESUSDT",
         "MKRUSDT", "SNXUSDT", "DOTUSDT", "YFIUSDT", "BALUSDT", "CRVUSDT", "TRBUSDT", "RUNEUSDT", "SUSHIUSDT",
         "SRMUSDT", "EGLDUSDT", "SOLUSDT", "ICXUSDT", "STORJUSDT", "BLZUSDT", "UNIUSDT", "AVAXUSDT", "FTMUSDT")
#: ETFs that traded before 2007, across asset classes: chosen by age. Bond funds are left out as instruments (the
#: owner's account holds nothing that bears interest).
ETFS = ("SPY", "QQQ", "IWM", "DIA", "MDY", "EFA", "EEM", "EWJ", "EWZ", "EWG", "EWU", "EWC", "EWA", "EWH", "EWT", "EWY",
        "FXI", "XLE", "XLF", "XLK", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "IYR", "GLD", "SLV", "USO", "DBC")
ARXIV = "http://export.arxiv.org/api/query?search_query={q}&sortBy=submittedDate&sortOrder=descending&max_results={n}"
ARXIV_CATS = ("q-fin.TR", "q-fin.ST", "q-fin.PM", "q-fin.CP")
OPENALEX = "https://api.openalex.org/works?search={q}&filter=from_publication_date:{since},type:article&per-page={n}"
#: one query a week, in turn: the directions this project has not explored, and the ones its record says matter
QUERIES = ("transfer entropy information flow asset returns predictability out-of-sample",
           "cross-asset lead-lag return predictability trading costs",
           "regime switching hidden Markov trading strategy out-of-sample transaction costs",
           "order flow imbalance price impact return predictability",
           "perpetual futures funding rate basis return predictability cryptocurrency",
           "commodity futures inventory term structure return predictability",
           "causal discovery financial time series return prediction",
           "liquidity provision short-term reversal returns after forced selling",
           "option implied volatility surface information predicts returns",
           "machine learning asset pricing out-of-sample transaction costs replication",
           "intraday periodicity volume volatility return predictability",
           "cross-sectional cryptocurrency factors returns out-of-sample")


def get(url: str, tries: int = 4, timeout: int = 60) -> bytes | None:
    """The body, or None when the file is not there (404). Any other failure is retried, then raised."""
    last: Exception | None = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
        except Exception as e:  # a read with no side effect: bounded retries
            last = e
        time.sleep(2 * (k + 1))
    raise RuntimeError(f"{url}: {last}")


def checked(url: str) -> bytes | None:
    """A Binance archive, refused unless it matches its published CHECKSUM. None if the month does not exist."""
    raw = get(url)
    if raw is None:
        return None
    want = get(url + ".CHECKSUM")
    if want is None:
        raise RuntimeError(f"{url}: no CHECKSUM is published for it")
    if hashlib.sha256(raw).hexdigest() != want.decode().split()[0].strip().lower():
        raise SystemExit(f"{url}: its sha256 differs from its CHECKSUM: stopped, nothing is filled")
    return raw


def _rows(raw: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return list(csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8")))


def _ms(x: str) -> datetime:
    """A Binance timestamp, in milliseconds or (the newer files) microseconds, written as an integer or a float."""
    v = int(float(x))
    return datetime.fromtimestamp(v / (1e6 if v > 1e14 else 1e3), timezone.utc)


def parse_daily_klines(raw: bytes) -> dict[str, float]:
    """{day: close} of a month of 1d klines. A header row, or a row that cannot be read, is skipped, never repaired."""
    out = {}
    for r in _rows(raw):
        if len(r) > 4 and r[0].strip()[:1].isdigit():
            try:
                c, day = float(r[4]), _ms(r[0]).strftime("%Y-%m-%d")
            except ValueError:
                continue
            if c > 0:
                out[day] = c
    return out


def parse_funding(raw: bytes) -> dict[str, float]:
    """{day: the sum of that UTC day's funding rates}: what a long paid, as a fraction of notional."""
    out: dict[str, float] = {}
    for r in _rows(raw):
        if len(r) > 2 and r[0].strip()[:1].isdigit():
            try:
                rate, d = float(r[2]), _ms(r[0]).strftime("%Y-%m-%d")
            except ValueError:
                continue
            out[d] = out.get(d, 0.0) + rate
    return out


#: A month's archives are asked for from this day of the next month. They appear some days after the month ends, and
#: not all at once: a month fetched while only some instruments have theirs is a panel with holes in its newest rows.
PUBLISHED_BY_DAY = 10
STALE_DAYS = 7  # a fund whose series stops this many days before the calendar's last day was not served whole


def due_month(now: datetime) -> str:
    """The newest month `crypto_daily` asks for: last month from the tenth on, the month before it until then."""
    y, m = now.year, now.month - (1 if now.day >= PUBLISHED_BY_DAY else 2)
    if m < 1:
        y, m = y - 1, m + 12
    return f"{y:04d}-{m:02d}"


def month_end(month: str) -> str:
    """The last calendar day of a month written YYYY-MM."""
    y, m = int(month[:4]), int(month[5:7])
    return date.fromordinal(date(y + (m == 12), 1 if m == 12 else m + 1, 1).toordinal() - 1).isoformat()


def months(first: date, last: date) -> list[str]:
    out, y, m = [], first.year, first.month
    while (y, m) <= (last.year, last.month):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def quality(series: dict[str, dict[str, float]]) -> dict:
    """Per instrument: rows, first and last day, days missing between them (weekends not counted unless the instrument
    trades on them), and one-day moves beyond 50%, which are flagged, never removed."""
    out = {}
    for s, d in sorted(series.items()):
        days = sorted(d)
        if not days:
            out[s] = {"rows": 0}
            continue
        a, b = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
        weekend = any(date.fromisoformat(x).weekday() >= 5 for x in days[:60])
        span = sum(1 for i in range((b - a).days + 1) if weekend or (a.toordinal() + i) % 7 not in (6, 0))
        vals = [d[x] for x in days]
        jumps = sum(1 for i in range(1, len(vals)) if abs(vals[i] / vals[i - 1] - 1.0) > 0.5)
        out[s] = {"rows": len(days), "first": days[0], "last": days[-1], "missing_days": max(0, span - len(days)),
                  "moves_beyond_50pct": jumps}
    return out


def _save(data: Path, name: str, body: dict, manifest: dict) -> None:
    data.mkdir(parents=True, exist_ok=True)
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    (data / f"{name}.json").write_text(text)
    manifest["files"][name] = {"sha256": hashlib.sha256(text.encode()).hexdigest()}


def crypto_daily(data: Path, now: datetime, first: date = date(2019, 9, 1), symbols: tuple = PERPS, fetch=checked,
                 workers: int = 8) -> dict:
    """Bring data/crypto_daily up to the newest month the archive should hold whole (`due_month`). Returns the
    manifest. What arrives is kept even when the fetch is not complete: the next one asks only for what is missing."""
    data = Path(data)
    old = json.loads((data / "manifest.json").read_text()) if (data / "manifest.json").exists() else {"months": {}}
    closes = json.loads((data / "close.json").read_text()) if (data / "close.json").exists() else {}
    funding = json.loads((data / "funding.json").read_text()) if (data / "funding.json").exists() else {}
    due = due_month(now)
    want = months(first, date(int(due[:4]), int(due[5:7]), 1))
    todo = [(s, m, k) for s in symbols for m in want for k in ("klines", "fundingRate")
            if m not in old["months"].get(f"{s}:{k}", [])]

    def one(job):
        s, m, k = job
        url = f"{VISION}{k}/{s}/" + (f"1d/{s}-1d-{m}.zip" if k == "klines" else f"{s}-fundingRate-{m}.zip")
        try:
            return job, fetch(url), None
        except RuntimeError as e:  # the archive did not answer for this file: the next fetch asks again
            return job, None, str(e)[:160]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        got = list(pool.map(one, todo))
    absent, failed = 0, []
    for (s, m, k), raw, err in got:
        if err is not None:
            failed.append(f"{s}:{k}:{m}")
            continue
        if raw is None:
            absent += 1
            continue
        part = parse_daily_klines(raw) if k == "klines" else parse_funding(raw)
        (closes if k == "klines" else funding).setdefault(s, {}).update(part)
        old["months"].setdefault(f"{s}:{k}", []).append(m)
    # An instrument ALIVE (priced and funded) on the last day of the month before the newest one, and without the
    # newest month's prices or funding: delisted exactly at the month's end, or (far more likely) its files are not
    # published yet. A contract delisted earlier is priced there and not funded: it is not waited for.
    have, late = old["months"], []
    if len(want) > 1:
        day = month_end(want[-2])
        late = sorted(s for s in symbols if day in closes.get(s, {}) and day in funding.get(s, {})
                      and not (due in have.get(f"{s}:klines", []) and due in have.get(f"{s}:fundingRate", [])))
    end = month_end(due)
    ended = {s: max(funding[s]) for s in sorted(funding) if funding[s] and max(funding[s]) < end}
    why = None
    if failed:
        why = (f"the archive did not answer for {len(failed)} files (the first: {', '.join(failed[:5])}). What arrived "
               "is kept")
    elif late:
        why = (f"{len(late)} instruments are priced and funded to the end of {want[-2]} and have no whole {due} (the "
               f"first: {', '.join(late[:5])}): the month looks half-published. What arrived is kept")
    man = {"dataset": "crypto_daily", "retrieved": now.isoformat(), "source": VISION, "months": old["months"],
           "newest_month": due, "fetched_now": len(todo) - absent - len(failed), "absent_now": absent,
           "failed_count": len(failed), "failed_now": failed[:40], "late": late[:40], "incomplete": why,
           "alive_at_the_end": sum(1 for s in symbols if end in closes.get(s, {}) and end in funding.get(s, {})),
           "funding_ended": ended, "files": {}, "quality": quality(closes)}
    _save(data, "close", closes, man)
    _save(data, "funding", funding, man)
    (data / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    return man


def parse_yahoo(res: dict) -> dict[str, float]:
    """{day: adjusted close} from one Yahoo chart result, by the exchange's own calendar day."""
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName") or "America/New_York")
    adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose") or res["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(res.get("timestamp") or [], adj):
        if isinstance(c, (int, float)) and c == c and c > 0:
            out[datetime.fromtimestamp(t, timezone.utc).astimezone(tz).strftime("%Y-%m-%d")] = float(c)
    return out


def etf_daily(data: Path, now: datetime, first: date = date(2005, 1, 1), symbols: tuple = ETFS, fetch=get) -> dict:
    """Write data/etf_daily: each ETF's adjusted closes and the VIX's closes, up to yesterday (a day's last bar is
    final only after its close). All or nothing: if a fund was not served, or was served with a series that stops
    early, nothing on file changes, and the manifest returned says why."""
    data = Path(data)
    p1 = int(datetime(first.year, first.month, first.day, tzinfo=timezone.utc).timestamp())
    today = now.strftime("%Y-%m-%d")
    out, missing = {}, []
    for s in symbols + ("^VIX",):
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(s)}?period1={p1}"
               f"&period2={int(now.timestamp())}&interval=1d&events=div%2Csplits")
        raw = fetch(url)
        if fetch is get:
            time.sleep(PAUSE)
        try:
            series = parse_yahoo(json.loads(raw)["chart"]["result"][0]) if raw else {}
        except (KeyError, IndexError, TypeError, ValueError):
            series = {}
        series = {d: v for d, v in series.items() if d < today}
        if series:
            out[s] = series
        else:
            missing.append(s)
    ref = max(out["SPY"]) if "SPY" in out else None  # the panel's calendar
    stale = sorted(s for s, v in out.items()
                   if ref and (date.fromisoformat(ref) - date.fromisoformat(max(v))).days > STALE_DAYS)
    why = None
    if missing:
        why = f"the source did not serve {', '.join(missing)}. Nothing on file was changed"
    elif stale:
        why = (f"{', '.join(stale)} stop more than {STALE_DAYS} days before the calendar's last day ({ref}). Nothing on "
               "file was changed")
    man = {"dataset": "etf_daily", "retrieved": now.isoformat(), "source": "query1.finance.yahoo.com (adjusted closes)",
           "not_served": missing, "stale": stale, "incomplete": why, "files": {}, "quality": quality(out)}
    if why is None:
        _save(data, "close", out, man)
        (data / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    return man


# ── the research-source database ────────────────────────────────────────────

def parse_arxiv(xml: bytes, query: str, fetched: str) -> list[dict]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        url = (e.findtext("a:id", "", ns) or "").strip()
        if not url:
            continue
        out.append({"id": "arxiv:" + url.rsplit("/abs/", 1)[-1].split("v")[0], "origin": "arxiv", "url": url,
                    "title": " ".join((e.findtext("a:title", "", ns) or "").split()),
                    "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)][:6],
                    "published": (e.findtext("a:published", "", ns) or "")[:10],
                    "abstract": " ".join((e.findtext("a:summary", "", ns) or "").split())[:1800],
                    "query": query, "fetched": fetched, "status": "UNREAD", "reproducibility": "not attempted"})
    return out


def parse_openalex(body: bytes, query: str, fetched: str) -> list[dict]:
    out = []
    for w in json.loads(body).get("results", []):
        inv = w.get("abstract_inverted_index") or {}
        words = sorted((i, t) for t, idx in inv.items() for i in idx)
        loc = (w.get("primary_location") or {}).get("landing_page_url") or w.get("doi") or w.get("id")
        if not w.get("id") or not w.get("display_name"):
            continue
        out.append({"id": "openalex:" + w["id"].rsplit("/", 1)[-1], "origin": "openalex", "url": loc,
                    "doi": w.get("doi"), "title": " ".join(w["display_name"].split()),
                    "authors": [(a.get("author") or {}).get("display_name") for a in w.get("authorships", [])][:6],
                    "published": w.get("publication_date"), "cited_by": w.get("cited_by_count"),
                    "abstract": " ".join(t for _, t in words)[:1800], "query": query, "fetched": fetched,
                    "status": "UNREAD", "reproducibility": "not attempted"})
    return out


def papers(known: set[str], now: datetime, week: int, fetch=get, per_query: int = 25) -> list[dict]:
    """New sources only: arXiv's latest in quantitative finance, and this week's OpenAlex query."""
    fetched = now.isoformat()
    out: list[dict] = []
    q = "+OR+".join(f"cat:{c}" for c in ARXIV_CATS)
    raw = fetch(ARXIV.format(q=q, n=60))
    if raw:
        out += parse_arxiv(raw, "arXiv q-fin, newest", fetched)
    query = QUERIES[week % len(QUERIES)]
    raw = fetch(OPENALEX.format(q=urllib.parse.quote(query), since=f"{now.year - 3}-01-01", n=per_query))
    if raw:
        out += parse_openalex(raw, query, fetched)
    seen, new = set(known), []
    for s in out:
        if s["id"] not in seen and s["title"]:
            seen.add(s["id"])
            new.append(s)
    return new


__all__ = ["ETFS", "PERPS", "PUBLISHED_BY_DAY", "QUERIES", "STALE_DAYS", "checked", "crypto_daily", "due_month",
           "etf_daily", "get", "month_end", "months", "papers", "parse_arxiv", "parse_daily_klines", "parse_funding",
           "parse_openalex", "parse_yahoo", "quality"]
