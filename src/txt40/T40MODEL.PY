#!/usr/bin/env python3
"""Reference model of the TXT40 presenter: 320x200x16 pixels -> 40x25 text.

  python3 src/txt40/T40MODEL.PY <frame.png> <out.png> [--json <cells.json>]
      [--font <cga font: 2048 bytes>]

present(frame, hints) is the specification the driver's presenter must
reproduce exactly (src/txt40/T40TEST.PY runs the driver code against it).

frame: 64000 IRGB colour indexes (row-major, 320 wide); a CGA text
attribute nibble is the same IRGB value, so no colour conversion is needed.
hints: what the driver recorded when Windows drew text in an 8x8 font:
(x, y, glyph, code): the glyph's exact top-left pixel, its 8 bitmap rows
(bit 7 = left) and the CP437 character to show. At most one hint per cell;
the cell is the one holding the glyph's centre pixel (x + 4, y + 4).

For every cell, in this order:
1. Hint check. A hint is shown only if the pixels still hold its glyph
   exactly: within its 8x8 window (clipped to the screen), every glyph pixel
   has one colour F, every other pixel has one colour B, F != B; or the
   glyph is blank and all pixels share one colour. Row 7 may instead be one
   solid colour when the glyph's row 7 is empty (a mnemonic underline). A
   verified hint shows (code, B << 4 | F) and claims its 8x8 window.
2. Otherwise the cell is approximated from its own pixels that no verified
   hint claims:
   - none, or one colour: a space in that colour (all claimed: the colour
     of the claiming hints' background);
   - otherwise background = most frequent colour (lowest index on ties),
     foreground = second most frequent; each unclaimed pixel is
     foreground if it equals the foreground colour, else background; the
     8x8 mask then picks a character (pick_char).
"""
import json
import sys
from pathlib import Path

W, H, COLS, ROWS = 320, 200, 40, 25

POP = [bin(i).count("1") for i in range(256)]

# Block and shade characters: (code, 8 rows) in the CGA ROM's CP437 order.
SHAPES = [
    (0xDB, [0xFF] * 8),              # full block
    (0xDF, [0xFF] * 4 + [0] * 4),    # upper half
    (0xDC, [0] * 4 + [0xFF] * 4),    # lower half
    (0xDD, [0xF0] * 8),              # left half
    (0xDE, [0x0F] * 8),              # right half
]
# Box-drawing by (left, right, up, down) line ends present.
BOX = {
    (1, 1, 0, 0): 0xC4, (0, 0, 1, 1): 0xB3, (1, 1, 1, 1): 0xC5,
    (0, 1, 0, 1): 0xDA, (1, 0, 0, 1): 0xBF, (0, 1, 1, 0): 0xC0, (1, 0, 1, 0): 0xD9,
    (0, 1, 1, 1): 0xC3, (1, 0, 1, 1): 0xB4, (1, 1, 0, 1): 0xC2, (1, 1, 1, 0): 0xC1,
    (1, 0, 0, 0): 0xC4, (0, 1, 0, 0): 0xC4, (0, 0, 1, 0): 0xB3, (0, 0, 0, 1): 0xB3,
}


def pick_char(mask, live):
    """mask, live: 8 row bytes. live marks unclaimed pixels. Returns code."""
    n = sum(POP[r] for r in live)
    on = sum(POP[m & l] for m, l in zip(mask, live))
    if on == 0:
        return 0x20
    if on == n:
        return 0xDB
    # Thin lines: full rows / full columns of foreground, little else.
    full_rows = [i for i in range(8) if live[i] == 0xFF and mask[i] == 0xFF]
    colmask = 0xFF
    for m, l in zip(mask, live):
        colmask &= (m | ~l) & 0xFF
    full_cols = POP[colmask]
    if (full_rows or full_cols) and len(full_rows) <= 2 and full_cols <= 2:
        stray = on - 8 * len(full_rows) - 8 * full_cols + len(full_rows) * full_cols
        if stray <= 2:
            if full_rows and full_cols:
                r0, r1 = full_rows[0], full_rows[-1]
                c = colmask
                left = 1 if any((mask[r] & 0x80) for r in full_rows) and not (c & 0x80) else 0
                right = 1 if any((mask[r] & 0x01) for r in full_rows) and not (c & 0x01) else 0
                up = 1 if r0 > 0 and (mask[0] & c) else 0
                down = 1 if r1 < 7 and (mask[7] & c) else 0
                left = 1 if (c & 0x80) == 0 else left
                right = 1 if (c & 0x01) == 0 else right
                key = (left, right, up, down)
                return BOX.get(key, 0xC5)
            return 0xC4 if full_rows else 0xB3
    best, best_d = None, 65
    for code, rows in SHAPES:
        d = sum(POP[(m ^ s) & l] for m, s, l in zip(mask, rows, live))
        if d < best_d:
            best, best_d = code, d
    if best_d * 8 <= n:
        return best
    q = on * 8 // n                  # density in eighths
    return 0x20 if q == 0 else 0xB0 if q <= 2 else 0xB1 if q <= 5 else 0xB2 if q <= 6 else 0xDB


def window(frame, x, y):
    """Pixels of the 8x8 window at (x, y); None for off-screen pixels."""
    out = []
    for r in range(8):
        yy = y + r
        row = []
        for c in range(8):
            xx = x + c
            row.append(frame[yy * W + xx] if 0 <= xx < W and 0 <= yy < H else None)
        out.append(row)
    return out


def verify(frame, hint):
    """(fg, bg) if the hint's glyph is exactly present, else None."""
    x, y, glyph, code = hint
    win = window(frame, x, y)
    fg = bg = None
    blank = not any(glyph)
    for r in range(8):
        for c in range(8):
            v = win[r][c]
            if v is None:
                continue
            on = (glyph[r] >> (7 - c)) & 1
            if r == 7 and glyph[7] == 0:
                continue                      # judged below
            if on:
                if fg is None:
                    fg = v
                elif v != fg:
                    return None
            else:
                if bg is None:
                    bg = v
                elif v != bg:
                    return None
    row7 = [v for v in win[7] if v is not None]
    if glyph[7] == 0 and row7:
        if bg is None:
            bg = row7[0]
        if len(set(row7)) != 1:
            return None
    if blank:
        return (bg, bg) if bg is not None else None
    if fg is None or bg is None or fg == bg:
        return None
    return fg, bg


def present(frame, hints):
    cells = [[(0x20, 0)] * COLS for _ in range(ROWS)]
    claimed = bytearray(W * H)
    claim_bg = [[None] * COLS for _ in range(ROWS)]
    by_cell = {}
    for h in hints:
        cx, cy = (h[0] + 4) >> 3, (h[1] + 4) >> 3
        if 0 <= cx < COLS and 0 <= cy < ROWS:
            by_cell[(cx, cy)] = h
    shown = {}
    for (cx, cy), h in sorted(by_cell.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        v = verify(frame, h)
        if v is None:
            continue
        fg, bg = v
        shown[(cx, cy)] = (h[3], (bg << 4) | fg)
        x, y = h[0], h[1]
        for r in range(8):
            for c in range(8):
                xx, yy = x + c, y + r
                if 0 <= xx < W and 0 <= yy < H:
                    claimed[yy * W + xx] = 1
                    tx, ty = xx >> 3, yy >> 3
                    if claim_bg[ty][tx] is None:
                        claim_bg[ty][tx] = bg
    for cy in range(ROWS):
        for cx in range(COLS):
            if (cx, cy) in shown:
                cells[cy][cx] = shown[(cx, cy)]
                continue
            counts = [0] * 16
            pix = []
            for r in range(8):
                for c in range(8):
                    i = (cy * 8 + r) * W + cx * 8 + c
                    if not claimed[i]:
                        counts[frame[i]] += 1
                        pix.append((r, c, frame[i]))
            used = [k for k in range(16) if counts[k]]
            if not used:
                b = claim_bg[cy][cx] or 0
                cells[cy][cx] = (0x20, (b << 4) | b)
                continue
            order = sorted(used, key=lambda k: (-counts[k], k))
            bg = order[0]
            if len(order) == 1:
                cells[cy][cx] = (0x20, (bg << 4) | bg)
                continue
            fg = order[1]
            mask = [0] * 8
            live = [0] * 8
            for r, c, v in pix:
                live[r] |= 0x80 >> c
                if v == fg:
                    mask[r] |= 0x80 >> c
            code = pick_char(mask, live)
            cells[cy][cx] = (code, (bg << 4) | fg)
    return cells


# ---- previews and oracle hints (host only) --------------------------------

PAL = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170),
       (170, 85, 0), (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85),
       (85, 255, 255), (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def ansi_to_cp437(c):
    if c < 128:
        return c
    try:
        return bytes([c]).decode("cp1252").encode("cp437")[0]
    except (UnicodeDecodeError, UnicodeEncodeError):
        return ord("?")


def render(cells, font):
    """40x25 cells drawn with an 8x8 CP437 font as a 320x200 RGB image."""
    from PIL import Image
    im = Image.new("RGB", (W, H))
    px = im.load()
    for cy in range(ROWS):
        for cx in range(COLS):
            code, attr = cells[cy][cx]
            fg, bg = PAL[attr & 15], PAL[attr >> 4]
            for r in range(8):
                bits = font[code * 8 + r]
                for c in range(8):
                    px[cx * 8 + c, cy * 8 + r] = fg if (bits >> (7 - c)) & 1 else bg
    return im


def oracle_hints(frame, fonts):
    """Hints found by searching the frame for runs of exact glyphs.

    Stands in for the driver's text recording when only a picture exists
    (reference frames from the Plantronics driver). Only letters, digits
    and punctuation with 6+ pixels, in runs of 2+ on an 8-pixel pitch,
    count, so that lines are not mistaken for '-' or '|'.
    """
    table = {}
    for path, oem in fonts:
        import importlib.machinery
        F = importlib.machinery.SourceFileLoader(
            "fntread", str(Path(__file__).with_name("FNTREAD.PY"))).load_module()
        for c, g in F.glyphs(path).items():
            code = c if oem else ansi_to_cp437(c)
            if (32 < c < 127 or c >= 160) and sum(POP[b] for b in g) >= 6:
                table.setdefault(bytes(g), code)
    found = {}
    for y in range(H - 7):
        for x in range(W - 7):
            t = [frame[(y + r) * W + x:(y + r) * W + x + 8] for r in range(8)]
            cols = set(v for row in t for v in row)
            if len(cols) != 2:
                continue
            for fgc in cols:
                m = bytes(sum(1 << (7 - c) for c in range(8) if row[c] == fgc) for row in t)
                if m in table:
                    found[(x, y)] = (x, y, list(m), table[m])
                    break
    hints = []
    for (x, y), h in found.items():
        if (x - 8, y) in found or (x + 8, y) in found:
            hints.append(h)
    # Spaces between words in a run: blank glyph where both neighbours are text.
    for (x, y) in list(found):
        if (x + 16, y) in found and (x + 8, y) not in found:
            t = window(frame, x + 8, y)
            if len(set(v for row in t for v in row if v is not None)) == 1:
                hints.append((x + 8, y, [0] * 8, 0x20))
    return hints


def main(argv):
    from PIL import Image
    if len(argv) < 3:
        print(__doc__)
        return 2
    frame = Image.open(argv[1]).tobytes()
    if len(frame) != W * H:
        raise SystemExit("T40MODEL: expects a decoded 320x200 frame")
    root = Path(__file__).resolve().parents[2] / "distributions" / "WINXT"
    fonts = [(root / "XTTSYS.FON", False), (root / "XTCOEM.FON", True)]
    hints = oracle_hints(frame, fonts)
    cells = present(frame, hints)
    if "--font" in argv:
        font = Path(argv[argv.index("--font") + 1]).read_bytes()
        render(cells, font).save(argv[2])
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(
            {"hints": hints, "cells": cells}))
    shown = sum(1 for row in cells for c in row if 32 < c[0] < 127)
    print(f"T40MODEL: {len(hints)} hints, {shown} cells show letters/digits/punctuation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
