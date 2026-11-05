"""Short excerpts from public research papers, for designing a preregistration: each line of a paper's text that
matches one of its keywords is printed to the log (not committed), at most LIMIT lines per paper. Run on GitHub's
runner (the papers' hosts are blocked here)."""

from __future__ import annotations

import io
import re
import sys
import urllib.request

from pypdf import PdfReader

UA = {"User-Agent": "Mozilla/5.0 (research reader)"}
LIMIT = 140
PAPERS = {
    "RBL (Harvey, Mazzoleni & Melone 2025)": (
        ["https://www.edhec.edu/sites/default/files/2026-03/Scientific%20paper.%20ssrn-5122748.pdf",
         "https://www.nber.org/system/files/working_papers/w33554/w33554.pdf"],
        r"calendar signal|month-end|month end|last (trading )?day|next day|basis points|bps|60/40|t-stat|sharpe|"
        r"signal is|we define|trading strategy|days before|day before|turn of the month"),
    "FCY (Cieslak, Morse & Vissing-Jorgensen 2019)": (
        ["https://stern.nyu.edu/sites/default/files/assets/documents/cycle_paper_cieslak_morse_vissingjorgensen.pdf",
         "https://conference.nber.org/conf_papers/f74573/f74573.pdf"],
        r"week 0|even week|odd week|days? -1|day -1|excess return|basis points|bps|trading days|sample|post-|"
        r"out of sample|out-of-sample|sharpe|strategy"),
}


def text_of(url: str) -> str | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            body = r.read()
        reader = PdfReader(io.BytesIO(body))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:  # noqa: BLE001 - reported
        print(f"  {url}: {exc}"[:300])
        return None


def main() -> int:
    for name, (urls, pattern) in PAPERS.items():
        print(f"===== {name}")
        for url in urls:
            text = text_of(url)
            if not text:
                continue
            print(f"  source: {url} ({len(text)} characters)")
            rx = re.compile(pattern, re.I)
            n = 0
            for line in text.splitlines():
                if rx.search(line):
                    print("  | " + line.strip()[:220])
                    n += 1
                    if n >= LIMIT:
                        break
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
