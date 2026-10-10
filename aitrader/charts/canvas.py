"""An RGB raster in numpy with the few primitives a chart needs, and a PNG encoder (zlib + crc32).

Deterministic: the same calls give the same bytes, so a chart is reproducible from its bars.
"""

from __future__ import annotations

import struct
import zlib

import numpy as np

from . import font


class Canvas:
    def __init__(self, width: int, height: int, bg=(255, 255, 255)) -> None:
        self.w, self.h = width, height
        self.px = np.empty((height, width, 3), dtype=np.uint8)
        self.px[:, :] = bg

    def _clip(self, x0, y0, x1, y1):
        x0, x1 = sorted((int(round(x0)), int(round(x1))))
        y0, y1 = sorted((int(round(y0)), int(round(y1))))
        return max(0, x0), max(0, y0), min(self.w, x1), min(self.h, y1)

    def rect(self, x0, y0, x1, y1, color) -> None:
        a, b, c, d = self._clip(x0, y0, x1, y1)
        if c > a and d > b:
            self.px[b:d, a:c] = color

    def blend(self, x0, y0, x1, y1, color, alpha: float) -> None:
        a, b, c, d = self._clip(x0, y0, x1, y1)
        if c > a and d > b:
            region = self.px[b:d, a:c].astype(np.float32)
            self.px[b:d, a:c] = np.round(region * (1 - alpha) + np.array(color, np.float32) * alpha).astype(np.uint8)

    def frame(self, x0, y0, x1, y1, color, width: int = 1) -> None:
        self.rect(x0, y0, x1, y0 + width, color)
        self.rect(x0, y1 - width, x1, y1, color)
        self.rect(x0, y0, x0 + width, y1, color)
        self.rect(x1 - width, y0, x1, y1, color)

    def hline(self, y, x0, x1, color, width: int = 1, dash: int = 0) -> None:
        y = int(round(y))
        x0, x1 = sorted((int(round(x0)), int(round(x1))))
        if not dash:
            return self.rect(x0, y, x1, y + width, color)
        for x in range(x0, x1, 2 * dash):
            self.rect(x, y, min(x + dash, x1), y + width, color)

    def vline(self, x, y0, y1, color, width: int = 1) -> None:
        x = int(round(x))
        self.rect(x, y0, x + width, y1, color)

    def line(self, x0, y0, x1, y1, color, width: int = 1) -> None:
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        xs = np.round(np.linspace(x0, x1, n)).astype(int)
        ys = np.round(np.linspace(y0, y1, n)).astype(int)
        for dx in range(width):
            for dy in range(width):
                ok = (xs + dx >= 0) & (xs + dx < self.w) & (ys + dy >= 0) & (ys + dy < self.h)
                self.px[ys[ok] + dy, xs[ok] + dx] = color

    def triangle(self, x, y, size: int, color, up: bool) -> None:
        """A filled triangle with its tip at (x, y), pointing up or down."""
        for r in range(size):
            half = r * 0.6
            yy = y + r if up else y - r
            self.rect(x - half, yy, x + half + 1, yy + 1, color)

    def text(self, x, y, s: str, color, scale: int = 2, bg=None, pad: int = 2) -> int:
        """Draws `s` with its top-left at (x, y); returns the x after it. `bg` boxes it for legibility."""
        m = font.mask(s, scale)
        h, w = m.shape
        x, y = int(round(x)), int(round(y))
        if bg is not None:
            self.rect(x - pad, y - pad, x + w + pad, y + h + pad, bg)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
            region = self.px[y0:y1, x0:x1]
            region[sub] = color
        return x + w

    def png(self) -> bytes:
        return encode_png(self.px)


def encode_png(px: np.ndarray) -> bytes:
    """8-bit RGB PNG: filter 0 on every row, zlib level 9."""
    h, w, _ = px.shape
    raw = np.concatenate([np.zeros((h, 1), dtype=np.uint8), px.reshape(h, w * 3)], axis=1).tobytes()

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def decode_png_size(data: bytes) -> tuple[int, int]:
    """(width, height) from a PNG header, for checks."""
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    return struct.unpack(">II", data[16:24])
