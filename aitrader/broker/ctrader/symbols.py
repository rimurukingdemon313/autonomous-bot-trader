"""The names brokers give the trend desk's four indices (docs/CTRADER.md)."""

from __future__ import annotations

#: the names brokers give the desk's indices, upper-case without punctuation ("US500.cash" -> US500CASH)
NAMES = {
    "US500": {"US500", "US500CASH", "SPX500", "SP500", "USA500", "USSPX500", "US500C"},
    "NAS100": {"NAS100", "NAS100CASH", "US100", "US100CASH", "USTEC", "USTECH", "USTECH100", "USTECCASH", "NDX100",
               "NASDAQ100"},
    "GER40": {"GER40", "GER40CASH", "DE40", "DE40CASH", "DAX40", "GERMANY40", "GER30", "GER30CASH", "DE30", "DAX30"},
    "UK100": {"UK100", "UK100CASH", "FTSE100", "GB100", "UKX100"},
}


def norm(name: str) -> str:
    return "".join(c for c in name.upper() if c.isalnum())


def match_symbols(light: list[dict]) -> dict[str, list[dict]]:
    """For each desk index, the broker's symbols whose name is one of its known names."""
    out: dict[str, list[dict]] = {k: [] for k in NAMES}
    for s in light:
        n = norm(s.get("symbolName") or "")
        for desk, names in NAMES.items():
            if n in names:
                out[desk].append(s)
    return out
