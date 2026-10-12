#!/usr/bin/env python3
"""Read an 86Box screenshot of the CGA 40x25 text screen back as text.

  python3 src/txt40/T40SHOT.PY <86box-screenshot.png> --font <CGA 8x8 font>
      [--json <out.json>]

The capture is first decoded to exact 320x200 IRGB pixels by
src/pcp/SHOTDEC.PY (any sample off the palette fails the decode). Each
8x8 cell is then read: one colour is a blank cell; two colours are matched
against the 8x8 font of the CGA character ROM (2048 bytes, characters
0-255; for 86Box it is roms/video/mda/mda.rom at offset 1800h, which is
not part of this repository). Only printable ASCII (20h-7Eh) is reported
as a character; every other cell is reported as '.' (a block, shade or
line approximation) or ' ' (blank).

rows(frame, font) -> 25 strings of 40 characters
cells(frame, font) -> 1000 (char or None, foreground, background)
"""
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOTDEC = importlib.machinery.SourceFileLoader(
    "shotdec", str(HERE.parent / "pcp" / "SHOTDEC.PY")).load_module()
W = 320


def decode(path):
    idx, worst, bad, size, geom = SHOTDEC.decode(str(path), 320)
    if bad:
        raise SystemExit(f"T40SHOT: {path} did not decode exactly ({bad} samples)")
    return bytes(idx)


def cells(frame, font):
    table = {}
    for c in range(0x20, 0x7F):
        table.setdefault(bytes(font[c * 8:c * 8 + 8]), chr(c))
    out = []
    for k in range(1000):
        cy, cx = divmod(k, 40)
        px = [[frame[(8 * cy + r) * W + 8 * cx + c] for c in range(8)] for r in range(8)]
        cols = sorted(set(v for row in px for v in row))
        if len(cols) == 1:
            out.append((" ", cols[0], cols[0]))
            continue
        if len(cols) == 2:
            hit = None
            for fg, bg in ((cols[0], cols[1]), (cols[1], cols[0])):
                m = bytes(sum(0x80 >> c for c in range(8) if px[r][c] == fg) for r in range(8))
                if m in table:
                    hit = (table[m], fg, bg)
                    break
            if hit:
                out.append(hit)
                continue
        out.append((None, cols[-1], cols[0]))
    return out


def rows(frame, font):
    cs = cells(frame, font)
    return ["".join(cs[r * 40 + c][0] or "." for c in range(40)) for r in range(25)]


def main(argv):
    if len(argv) < 2 or "--font" not in argv:
        print(__doc__)
        return 2
    font = Path(argv[argv.index("--font") + 1]).read_bytes()
    if len(font) != 2048:
        raise SystemExit("T40SHOT: the font must be 2048 bytes (256 characters x 8 rows)")
    frame = decode(argv[1])
    text = rows(frame, font)
    for line in text:
        print("|" + line + "|")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(text, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
