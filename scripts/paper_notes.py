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
    "MOM (Neuhierl & Weber, Monetary Momentum)": (
        ["https://nber.org/system/files/working_papers/w24748/w24748.pdf",
         "https://www.lawfin.uni-frankfurt.de/fileadmin/user_upload/ANeuhierl_paper_09252020.pdf"],
        r"sharpe|trading strateg|fed funds futures|slope|25 days|15 days|expansionary|contractionary|"
        r"surprise is|we define|we measure|basis points|bps|per year|annual|sample|transaction cost"),
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
