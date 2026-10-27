#!/usr/bin/env python3
"""Host model of the CGAPAN converters: a 160x100 viewport on a 320x200 shadow.

It mirrors the arithmetic CGAPAN.PY stages into TSOFT.ASM, not the 8086 code
itself: the viewport clip order, the physical row counter, the shadow address
taken from logical coordinates, and the 8-byte-per-source-byte DEh output. The
check compares incremental dirty flushes and pans with a full repaint, so it
proves the algorithm; native Windows runs prove the assembly. No hardware I/O.
Planes are the retained DDK R/G/B/I order, interleaved per row.
"""
import random

LOGICAL_W, LOGICAL_H, VIEW_W, VIEW_H = 320, 200, 160, 100
STRIDE, VIEW_BYTES, SHADOW, ROW = 40, 20, 32000, 160      # ROW: 4 planes * stride
PLANES = ((0, 4), (STRIDE, 2), (STRIDE * 2, 1), (STRIDE * 3, 8))


def pixel(shadow, x, y):
    base, mask = y * ROW + x // 8, 0x80 >> (x % 8)
    return sum(bit for off, bit in PLANES if shadow[base + off] & mask)


def reference(shadow, left, top):
    """What the screen must show: the 160x100 window at (left, top)."""
    vram = fresh_vram()
    for y in range(VIEW_H):
        for x in range(0, VIEW_W, 2):
            off = y * 160 + x
            vram[off + 1] = (pixel(shadow, left + x, top + y) << 4) | pixel(shadow, left + x + 1, top + y)
    return vram


def fresh_vram():
    """Enable fills 16,000 bytes with 00DEh words and leaves the padding."""
    vram = bytearray(16384)
    for i in range(0, 16000, 2):
        vram[i] = 0xde
    return vram


class Driver:
    def __init__(self):
        self.shadow = bytearray(SHADOW)
        self.vram = fresh_vram()
        self.reads = []                       # (low, high) shadow offsets touched
        self.reset()

    def reset(self):
        self.x = self.top = 0                 # pan_x, pan_top
        self.xb, self.xr, self.bottom = 0, VIEW_BYTES, VIEW_H

    def _convert(self, si, di, count):
        for k in range(count):
            for pair in range(4):
                nib = []
                for bit in (2 * pair, 2 * pair + 1):
                    mask = 0x80 >> bit
                    nib.append(sum(b for off, b in PLANES if self.shadow[si + k + off] & mask))
                assert 0 <= di < 16000
                self.vram[di + 1] = (nib[0] << 4) | nib[1]
                self.vram[di] = 0xde
                di += 2
        self.reads.append((si, si + count - 1 + STRIDE * 3))

    def _clip_rows(self, a, b):
        a, b = max(a, 0), min(b, LOGICAL_H)                       # upstream clamps
        a = max(a, self.top)
        a = min(a, self.bottom)
        b = min(b, self.bottom)
        return a, max(b, a)

    def flush_rows(self, a, b):
        a, b = self._clip_rows(a, b)
        if a >= b:
            return
        row, limit = a - self.top, b - self.top                   # physical counter
        si = a * ROW + self.xb
        while row < limit:
            self._convert(si, row * 160, VIEW_BYTES)
            si += VIEW_BYTES + (ROW - VIEW_BYTES)
            row += 1

    def flush_columns(self, a, b, c, d):
        a, b = self._clip_rows(a, b)
        c, d = max(c, 0), min(d, STRIDE)
        c = min(max(c, self.xb), self.xr)
        d = max(min(d, self.xr), c)
        if a >= b or c >= d:
            return
        count, row, limit = d - c, a - self.top, b - self.top
        si = a * ROW + c
        while row < limit:
            self._convert(si, row * 160 + (c - self.xb) * 8, count)
            si += ROW
            row += 1

    def pan_set(self, left, top):
        left = min(max(left, 0), LOGICAL_W - VIEW_W) & ~7
        top = min(max(top, 0), LOGICAL_H - VIEW_H)
        if (left, top) == (self.x, self.top):
            return
        self.x, self.top = left, top
        self.xb, self.xr, self.bottom = left // 8, left // 8 + VIEW_BYTES, top + VIEW_H
        self.flush_rows(0, LOGICAL_H)                             # FlushShadow


def draw(driver, rng, x0, y0, x1, y1):
    """Fill a logical rectangle with random pixels, then flush as GDI would."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = rng.randrange(16)
            base, mask = y * ROW + x // 8, 0x80 >> (x % 8)
            for off, bit in PLANES:
                if v & bit:
                    driver.shadow[base + off] |= mask
                else:
                    driver.shadow[base + off] &= ~mask & 255
    if rng.random() < .5:
        driver.flush_rows(y0, y1)
    else:
        driver.flush_columns(y0, y1, x0 // 8, (x1 + 7) // 8)


CORNERS = ((0, 0), (160, 0), (0, 100), (160, 100), (80, 50), (-9, -9), (999, 999), (13, 7), (167, 3))


def check(seeds=6, steps=40):
    """Raise AssertionError on any mismatch; return coverage counts."""
    stats = dict(draws=0, pans=0, pad_ok=True)
    for seed in range(seeds):
        rng = random.Random(seed)
        d = Driver()
        for step in range(steps):
            if rng.random() < .35:
                d.pan_set(*(CORNERS[rng.randrange(len(CORNERS))] if rng.random() < .5
                            else (rng.randrange(-8, 180), rng.randrange(-8, 120))))
                stats['pans'] += 1
            else:
                x0, y0 = rng.randrange(-4, LOGICAL_W), rng.randrange(-4, LOGICAL_H)
                w, h = rng.randrange(1, 40), rng.randrange(1, 24)
                draw(d, rng, max(x0, 0), max(y0, 0), min(x0 + w, LOGICAL_W), min(y0 + h, LOGICAL_H))
                stats['draws'] += 1
            assert d.vram == reference(d.shadow, d.x, d.top), (seed, step, d.x, d.top)
            assert d.vram[16000:] == bytes(384), 'padding written'
        assert all(lo >= 0 and hi < SHADOW for lo, hi in d.reads), 'read outside the shadow'
    # Offscreen drawing must appear when revealed.
    d = Driver()
    rng = random.Random(99)
    draw(d, rng, 200, 120, 240, 150)
    assert d.vram == fresh_vram(), 'offscreen draw reached the screen'
    d.pan_set(160, 100)
    assert d.vram == reference(d.shadow, 160, 100) and d.vram != fresh_vram()
    # Pans reset to the origin together with Enable/Disable.
    d.reset()
    assert (d.x, d.top, d.xb, d.xr, d.bottom) == (0, 0, 0, VIEW_BYTES, VIEW_H)
    return stats


if __name__ == '__main__':
    print(check())
