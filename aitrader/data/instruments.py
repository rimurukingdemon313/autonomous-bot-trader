"""The instrument universe and the facts about each instrument.

Plausible price bands are narrower than a power of ten on purpose: a raw
feed in points (109305 for 1.09305) must fit exactly one scale or be
refused. A wrong scale raises nothing downstream; it silently measures the
wrong magnitude everywhere (docs/HISTORICAL_ARCHIVE.md).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Instrument:
    symbol: str
    asset_class: str  # "fx" or "metal"
    pip: float  # the conventional pip, in price units
    band: tuple[float, float]  # plausible price range, used to validate scale
    quote: str  # quote currency

    def in_band(self, price: float) -> bool:
        return self.band[0] <= price <= self.band[1]


def _fx(symbol: str) -> Instrument:
    jpy = symbol.endswith("JPY")
    return Instrument(
        symbol=symbol,
        asset_class="fx",
        pip=0.01 if jpy else 0.0001,
        band=(40.0, 400.0) if jpy else (0.4, 3.0),
        quote=symbol[3:],
    )


UNIVERSE: dict[str, Instrument] = {
    s: _fx(s)
    for s in (
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
        "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY",
    )
}
UNIVERSE["XAUUSD"] = Instrument("XAUUSD", "metal", 0.1, (200.0, 5000.0), "USD")
UNIVERSE["XAGUSD"] = Instrument("XAGUSD", "metal", 0.001, (8.0, 60.0), "USD")

#: The name used in the experiment registry for data drawn from this
#: universe. Contamination is a property of MARKET PERIODS, not of files:
#: a second copy of the same prices from another vendor is not unseen.
UNIVERSE_KEY = "fx-majors"


@dataclass(frozen=True, slots=True)
class IndexCFD:
    """An equity-index CFD the trend desk trades (aitrader/position/trend_desk.py). It is kept apart from UNIVERSE on
    purpose: the research registry's "fx-majors" universe and its contamination record are not touched by it.

    One lot is one unit of the index: a 1-point move is worth one unit of the quote currency per lot. The spread is
    a declared typical CFD spread in index points, not a measured one."""

    symbol: str
    source: str  # the cash index the price comes from (Yahoo symbol)
    quote: str  # the currency the index is priced in
    spread: float  # points
    exchange_tz: str
    open_local: tuple[int, int]  # the exchange's opening time, local (hour, minute)
    close_local: tuple[int, int]  # its closing time


INDEX_CFDS: dict[str, IndexCFD] = {
    "US500": IndexCFD("US500", "^GSPC", "USD", 0.5, "America/New_York", (9, 30), (16, 0)),
    "NAS100": IndexCFD("NAS100", "^NDX", "USD", 1.5, "America/New_York", (9, 30), (16, 0)),
    "GER40": IndexCFD("GER40", "^GDAXI", "EUR", 1.5, "Europe/Berlin", (9, 0), (17, 30)),
    "UK100": IndexCFD("UK100", "^FTSE", "GBP", 1.0, "Europe/London", (8, 0), (16, 30)),
}
#: an index CFD's pip, for spreads, slippage and commission allowances: one index point
INDEX_POINT = 1.0


def is_index(symbol: str) -> bool:
    return symbol in INDEX_CFDS


def quote_currency(symbol: str) -> str:
    """The currency an instrument's price is quoted in: an index CFD's own, a pair's second leg."""
    return INDEX_CFDS[symbol].quote if symbol in INDEX_CFDS else symbol[3:]


def get(symbol: str) -> Instrument:
    try:
        return UNIVERSE[symbol.upper()]
    except KeyError:
        raise KeyError(f"unknown instrument {symbol!r}; known: {', '.join(sorted(UNIVERSE))}") from None


def price_scale(symbol: str, raw_median: float) -> float:
    """The single power of ten that puts a raw median price inside the band.

    Exactly one must fit. None, or more than one, is an error: a wrong scale
    raises nothing downstream and silently measures the wrong magnitude
    everywhere (costs in pips, spreads, the band checks themselves).
    """
    inst = get(symbol)
    fits = [10.0 ** k for k in range(-6, 5) if inst.in_band(raw_median * 10.0 ** k)]
    if len(fits) != 1:
        raise ValueError(f"{symbol}: raw median {raw_median:g} fits {len(fits)} scales {fits}; refusing to guess")
    return fits[0]
