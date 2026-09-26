"""Bid/ask bars: the one market-data representation every layer reads.

A bar is labelled by its OPEN time and becomes available at its CLOSE
(DATA_CONTRACT.md §3). `available_at` is therefore the only time any
consumer may compare with a decision time. Mixing the two is a one-bar
look-ahead leak, so the container makes the safe comparison the easy one:
`as_of(T)` returns exactly the bars known at T.

Arrays are numpy, columnar, and read-only once built.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PERIOD_SECONDS = {"M15": 900, "H1": 3600, "H4": 14400, "D1": 86400}

FIELDS = (
    "open_time",
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
    "ticks", "spread_mean", "spread_max",
)
PRICE_FIELDS = FIELDS[1:9]


@dataclass(frozen=True)
class BarSeries:
    """Columnar bars for one instrument and timeframe, oldest first.

    `ticks` is a count of price updates, NOT traded volume: spot FX has no
    centralised volume, and this field is never to be presented as one.
    `spread_mean` / `spread_max` are measured from the ticks inside the bar.
    """

    symbol: str
    timeframe: str
    source: str
    open_time: np.ndarray  # int64, epoch seconds UTC
    bid_open: np.ndarray
    bid_high: np.ndarray
    bid_low: np.ndarray
    bid_close: np.ndarray
    ask_open: np.ndarray
    ask_high: np.ndarray
    ask_low: np.ndarray
    ask_close: np.ndarray
    ticks: np.ndarray
    spread_mean: np.ndarray
    spread_max: np.ndarray

    def __post_init__(self) -> None:
        if self.timeframe not in PERIOD_SECONDS:
            raise ValueError(f"unknown timeframe {self.timeframe!r}")
        n = len(self.open_time)
        for name in FIELDS:
            arr = getattr(self, name)
            if len(arr) != n:
                raise ValueError(f"{name} has {len(arr)} rows, open_time has {n}")
            arr.setflags(write=False)

    # ── time ────────────────────────────────────────────────────────────

    @property
    def period(self) -> int:
        return PERIOD_SECONDS[self.timeframe]

    @property
    def available_at(self) -> np.ndarray:
        """When each bar could first be known: its close."""
        return self.open_time + self.period

    def __len__(self) -> int:
        return len(self.open_time)

    def as_of(self, t: int) -> "BarSeries":
        """Exactly the bars whose close is at or before `t`."""
        k = int(np.searchsorted(self.available_at, t, side="right"))
        return self.take(slice(0, k))

    def between(self, start: int, end: int) -> "BarSeries":
        """Bars whose OPEN time is in [start, end)."""
        a = int(np.searchsorted(self.open_time, start, side="left"))
        b = int(np.searchsorted(self.open_time, end, side="left"))
        return self.take(slice(a, b))

    def take(self, index) -> "BarSeries":
        return BarSeries(
            self.symbol, self.timeframe, self.source,
            *(np.asarray(getattr(self, f)[index]).copy() for f in FIELDS),
        )

    # ── derived prices ──────────────────────────────────────────────────

    @property
    def mid_open(self) -> np.ndarray:
        return (self.bid_open + self.ask_open) / 2.0

    @property
    def mid_high(self) -> np.ndarray:
        return (self.bid_high + self.ask_high) / 2.0

    @property
    def mid_low(self) -> np.ndarray:
        return (self.bid_low + self.ask_low) / 2.0

    @property
    def mid_close(self) -> np.ndarray:
        return (self.bid_close + self.ask_close) / 2.0

    # ── persistence ─────────────────────────────────────────────────────

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        np.savez_compressed(
            buf,
            meta=np.array([self.symbol, self.timeframe, self.source]),
            **{f: getattr(self, f) for f in FIELDS},
        )
        return buf.getvalue()

    def content_hash(self) -> str:
        """Hash of the values themselves, independent of file compression."""
        h = hashlib.sha256()
        h.update(f"{self.symbol}|{self.timeframe}|{self.source}".encode())
        for f in FIELDS:
            arr = np.ascontiguousarray(getattr(self, f))
            h.update(f.encode())
            h.update(str(arr.dtype).encode())
            h.update(arr.tobytes())
        return h.hexdigest()

    def save(self, path: Path | str) -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(self.to_bytes())
        return self.content_hash()

    @classmethod
    def load(cls, path: Path | str) -> "BarSeries":
        with np.load(Path(path), allow_pickle=False) as z:
            symbol, timeframe, source = (str(x) for x in z["meta"])
            return cls(symbol, timeframe, source, *(z[f].copy() for f in FIELDS))

    @classmethod
    def from_columns(cls, symbol: str, timeframe: str, source: str, **cols) -> "BarSeries":
        missing = [f for f in FIELDS if f not in cols]
        if missing:
            raise ValueError(f"missing columns: {missing}")
        arrays = {}
        for f in FIELDS:
            dtype = np.int64 if f in ("open_time", "ticks") else np.float64
            arrays[f] = np.asarray(cols[f], dtype=dtype)
        return cls(symbol, timeframe, source, *(arrays[f] for f in FIELDS))

    @classmethod
    def concat(cls, parts: list["BarSeries"]) -> "BarSeries":
        if not parts:
            raise ValueError("nothing to concatenate")
        first = parts[0]
        for p in parts[1:]:
            if (p.symbol, p.timeframe, p.source) != (first.symbol, first.timeframe, first.source):
                raise ValueError("cannot concatenate series of different identity")
        return cls(
            first.symbol, first.timeframe, first.source,
            *(np.concatenate([getattr(p, f) for p in parts]) for f in FIELDS),
        )
