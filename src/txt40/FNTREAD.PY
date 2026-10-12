#!/usr/bin/env python3
"""Read 8x8 glyph bitmaps from a Windows 3.x .FON (NE resource, FNT 2.0/3.0).

  python3 src/txt40/FNTREAD.PY <font.FON>      prints a summary

glyphs(path) -> {char_code: 8 bytes (row 0 first, bit 7 = leftmost pixel)}
for every character of the font's first FONT resource, which must be 8
pixels high and at most 8 wide (narrower glyphs are left-aligned).
"""
import struct
import sys
from pathlib import Path


def fnt_resources(data):
    ne = struct.unpack_from("<I", data, 0x3C)[0]
    rt = ne + struct.unpack_from("<H", data, ne + 0x24)[0]
    shift = struct.unpack_from("<H", data, rt)[0]
    p = rt + 2
    out = []
    while True:
        typ, n = struct.unpack_from("<HH", data, p)
        p += 8
        if typ == 0:
            break
        for _ in range(n):
            off, length = struct.unpack_from("<HH", data, p)
            if typ == 0x8008:
                out.append(data[off << shift:(off << shift) + (length << shift)])
            p += 12
    return out


def glyphs(path):
    fnt = fnt_resources(Path(path).read_bytes())[0]
    version = struct.unpack_from("<H", fnt, 0)[0]
    height = struct.unpack_from("<H", fnt, 88)[0]
    first, last = fnt[95], fnt[96]
    if height != 8:
        raise SystemExit(f"FNTREAD: {path} is {height} pixels high, not 8")
    table = 118 if version == 0x200 else 148
    entry = 4 if version == 0x200 else 6
    out = {}
    for i in range(last - first + 2):            # last+1 is the sentinel
        if version == 0x200:
            w, off = struct.unpack_from("<HH", fnt, table + entry * i)
        else:
            w, off = struct.unpack_from("<HI", fnt, table + entry * i)
        if w > 8 or i > last - first:
            continue
        out[first + i] = bytes(fnt[off + r] for r in range(8))
    return out


if __name__ == "__main__":
    g = glyphs(sys.argv[1])
    print(len(g), "glyphs", min(g), "..", max(g))
    for c in (ord("A"), ord("g")):
        for row in g[c]:
            print(format(row, "08b").replace("0", ".").replace("1", "#"))
