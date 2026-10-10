"""A local `.env` file for `python -m aitrader` (docs/DUAL_AI.md): KEY=VALUE lines, read once at start.

A variable already set in the environment wins: the file only fills what is missing, so a platform's own
variables (Railway, GitHub secrets) are never overridden by a file. Values may be quoted ("..." or '...');
an unquoted value ends at " #". Nothing read here is logged or returned: the caller gets the NAMES only.
The file is in .gitignore and is never committed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


def parse(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = _LINE.match(raw)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val[:1] in ("'", '"'):
            end = val.find(val[0], 1)
            val = val[1:end] if end > 0 else val[1:]
        else:
            val = re.split(r"\s+#", val, maxsplit=1)[0].strip()
        out.setdefault(key, val)
    return out


def load(path: str | Path = ".env", environ=None) -> list[str]:
    """Fill the environment from `path` (if it exists); returns the names it set."""
    env = os.environ if environ is None else environ
    p = Path(path)
    if not p.is_file():
        return []
    loaded = []
    for k, v in parse(p.read_text(encoding="utf-8")).items():
        if k not in env:
            env[k] = v
            loaded.append(k)
    return loaded
