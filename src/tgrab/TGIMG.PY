#!/usr/bin/env python3
"""The grabber/clipboard test picture: 64x40, all sixteen colours.

  python3 src/tgrab/TGIMG.PY --palette <a 4-bit BMP whose palette to copy> --out TGIMG.BMP

f(x, y) is the same picture TGPAT.COM draws: a white (15) border, a
light-red (12) marker in the top-left corner (x 2-9, y 2-5), sixteen bars
x/4 in the top half and 15 - x/4 in the bottom half. Every colour appears,
and no flip or rotation maps the picture onto itself.
"""
import argparse
import struct
from pathlib import Path

W, H = 64, 40
# The display driver's colour table as Windows writes it in a 4-bit BMP
# (BGR0 per entry, Windows device index order). The reference colours.
WINPAL = bytes.fromhex("00000000000080000080000000808000800000008000800080800000808080004040400"
                       "00000ff0000ff000000ffff00ff000000ff00ff00ffff0000ffffff00")


def f(x, y):
    if x in (0, W - 1) or y in (0, H - 1):
        return 15
    if 2 <= x < 10 and 2 <= y < 6:
        return 12
    return x // 4 if y < 20 else 15 - x // 4


def pixels():
    return [[f(x, y) for x in range(W)] for y in range(H)]


def bmp(palette):
    row = (W // 2 + 3) & ~3
    bits = bytearray()
    for y in range(H - 1, -1, -1):
        r = bytearray(row)
        for x in range(W):
            r[x // 2] |= f(x, y) << (0 if x & 1 else 4)
        bits += r
    off = 14 + 40 + 64
    return (b"BM" + struct.pack("<IHHI", off + len(bits), 0, 0, off) +
            struct.pack("<IiiHHIIiiII", 40, W, H, 1, 4, 0, len(bits), 0, 0, 16, 16) + palette + bits)


def read_bmp(data):
    """(width, height, rows of 4-bit indices, palette bytes) of a 4-bit BI_RGB BMP."""
    off = struct.unpack_from("<I", data, 10)[0]
    hs, w, h, planes, bpp, comp = struct.unpack_from("<IiiHHI", data, 14)
    if bpp != 4 or comp != 0:
        raise SystemExit(f"TGIMG: {bpp}-bit compression {comp} BMP, expected 4-bit BI_RGB")
    pal = data[14 + hs:14 + hs + 64]
    row = ((w * 4 + 31) // 32) * 4
    rows = []
    for y in range(abs(h)):
        src = (abs(h) - 1 - y) if h > 0 else y
        r = data[off + src * row: off + (src + 1) * row]
        rows.append([(r[x // 2] >> (0 if x & 1 else 4)) & 15 for x in range(w)])
    return w, abs(h), rows, pal


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--palette", type=Path, help="default: WINPAL")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    pal = read_bmp(a.palette.read_bytes())[3] if a.palette else WINPAL
    a.out.write_bytes(bmp(pal))


if __name__ == "__main__":
    main()
