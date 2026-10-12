#!/usr/bin/env python3
"""Reference model of the TXT40 presenter: 320x200x16 shadow -> 40x25 text.

  python3 src/txt40/T40MODEL.PY <frame.png> <out.png> [--json <cells.json>]
      [--font <cga font: 2048 bytes>]
  python3 src/txt40/T40MODEL.PY --check

Presenter is the specification the driver's T40PRES.ASM must reproduce
byte for byte (T40TEST.PY runs the assembled driver code against it).

Pixels: the TR5 shadow, 200 rows of four 40-byte planes (red, green, blue,
intensity at +0, +40, +80, +120; bit 7 = leftmost pixel). A pixel's colour
is the IRGB nibble I<<3|R<<2|G<<1|B, which is also a CGA text attribute
nibble, so no colour conversion is needed. Cell (cx, cy) covers pixels
8cx..8cx+7 x 8cy..8cy+7; cell index = cy*40 + cx; text word = attr<<8|code.

Hints are what the driver recorded when Windows drew text in an 8x8 font
on the screen: (x, y, glyph, code) = the glyph's exact top-left pixel, its
8 rows, and the CP437 character to show. A hint belongs to the cell holding
its centre pixel (x+4, y+4); hints whose centre is off screen are dropped.
Each cell keeps at most two hints, newest first (add()). A screen-to-screen
copy (blit()) re-adds every hint wholly inside the source at its new place.

For every cell (ideal()):
1. The newest hint whose glyph is still exactly in the pixels is shown
   (verify()): within its 8x8 window, on-screen pixels only, every glyph
   pixel has one colour F, every other pixel one colour B, F != B; or the
   glyph is blank and all pixels share one colour. If the glyph's row 7 is
   empty, row 7 need only be one solid colour (a mnemonic underline).
   Shows (code, B<<4|F) and claims its window's pixels for neighbours too.
2. Otherwise approximate from the cell's own pixels that no shown hint of
   the 3x3 neighbourhood claims: background = most frequent colour (lowest
   index on ties), foreground = the next; pick_char() turns the foreground
   mask into a space, block, half block, shade or box-drawing character.
   No unclaimed pixels: a space in the background colour of the first
   claiming neighbour in row-major order.
present(ay, by, cx, dx) rewrites only the cells a change of pixel rows
ay..by-1, byte columns cx..dx-1 can affect. A glyph window spans at most
two cell rows and columns, so that is the dirty cells plus one cell each
way; shown hints are re-verified one cell beyond that.
"""
import json
import sys
from pathlib import Path

W, H, COLS, ROWS = 320, 200, 40, 25
NCELL = COLS * ROWS
POP = [bin(i).count("1") for i in range(256)]

# Half blocks in trial order: (code, 8 rows). The foreground is never the
# majority colour, so a full block or dark shade can never be the answer.
SHAPES = [
    (0xDF, [0xFF] * 4 + [0] * 4),    # upper half
    (0xDC, [0] * 4 + [0xFF] * 4),    # lower half
    (0xDD, [0xF0] * 8),              # left half
    (0xDE, [0x0F] * 8),              # right half
]
# Box-drawing junction by index left<<3 | right<<2 | up<<1 | down.
BOX16 = [0xC5, 0xB3, 0xB3, 0xB3, 0xC4, 0xDA, 0xC0, 0xC3,
         0xC4, 0xBF, 0xD9, 0xB4, 0xC4, 0xC2, 0xC1, 0xC5]


def pick_char(mask, live):
    """mask (foreground, within live), live (unclaimed): 8 row bytes each."""
    n = sum(POP[r] for r in live)
    on = sum(POP[m] for m in mask)
    if on == 0:
        return 0x20
    rows = [i for i in range(8) if live[i] == 0xFF and mask[i] == 0xFF]
    nr = len(rows)
    colmask = 0xFF
    for m, l in zip(mask, live):
        colmask &= (m | (~l & 0xFF))
    nc = POP[colmask]
    if (nr or nc) and nr <= 2 and nc <= 2:
        stray = on - 8 * nr - 8 * nc + nr * nc
        if stray <= 2:
            if nr and nc:
                left = 1 if not (colmask & 0x80) else 0
                right = 1 if not (colmask & 0x01) else 0
                up = 1 if rows[0] > 0 and (mask[0] & colmask) else 0
                down = 1 if rows[-1] < 7 and (mask[7] & colmask) else 0
                return BOX16[left << 3 | right << 2 | up << 1 | down]
            return 0xC4 if nr else 0xB3
    best, best_d = 0, 65
    for code, srows in SHAPES:
        d = sum(POP[(m ^ s) & l] for m, s, l in zip(mask, srows, live))
        if d < best_d:
            best, best_d = code, d
    if best_d * 8 <= n:
        return best
    q = on * 8 // n                  # 0..4: foreground is at most half
    return 0x20 if q == 0 else 0xB0 if q <= 2 else 0xB1


def pixel(shadow, x, y):
    base = y * 160 + (x >> 3)
    bit = 7 - (x & 7)
    return (((shadow[base + 120] >> bit) & 1) << 3 | ((shadow[base] >> bit) & 1) << 2
            | ((shadow[base + 40] >> bit) & 1) << 1 | ((shadow[base + 80] >> bit) & 1))


def shadow_from_frame(frame):
    sh = bytearray(32000)
    for y in range(H):
        for x in range(W):
            v = frame[y * W + x]
            b = 0x80 >> (x & 7)
            base = y * 160 + (x >> 3)
            for p, bitv in ((0, 4), (40, 2), (80, 1), (120, 8)):
                if v & bitv:
                    sh[base + p] |= b
    return sh


def verify(shadow, hint):
    """Attribute B<<4|F if the hint's glyph is exactly present, else None."""
    x, y, glyph, code = hint
    fg = bg = None
    for r in range(8):
        yy = y + r
        if not 0 <= yy < H:
            continue
        if r == 7 and glyph[7] == 0:
            continue
        for c in range(8):
            xx = x + c
            if not 0 <= xx < W:
                continue
            v = pixel(shadow, xx, yy)
            if (glyph[r] >> (7 - c)) & 1:
                if fg is None:
                    fg = v
                elif v != fg:
                    return None
            else:
                if bg is None:
                    bg = v
                elif v != bg:
                    return None
    if glyph[7] == 0 and 0 <= y + 7 < H:
        row7 = set(pixel(shadow, x + c, y + 7) for c in range(8) if 0 <= x + c < W)
        if len(row7) != 1:
            return None
        if bg is None:
            bg = row7.pop()
    if not any(glyph):
        return None if bg is None else bg << 4 | bg
    if fg is None or bg is None or fg == bg:
        return None
    return bg << 4 | fg


def hint_cell(x, y):
    cx, cy = (x + 4) >> 3, (y + 4) >> 3
    if 0 <= cx < COLS and 0 <= cy < ROWS:
        return cy * COLS + cx
    return None


class Presenter:
    def __init__(self):
        self.slots = [[] for _ in range(NCELL)]     # newest first, at most 2
        self.text = [0] * NCELL                      # attr<<8 | code

    def add(self, x, y, glyph, code):
        k = hint_cell(x, y)
        if k is None:
            return
        s = self.slots[k]
        h = (x, y, list(glyph), code)
        if s and s[0][0] == x and s[0][1] == y:
            s[0] = h
        else:
            s.insert(0, h)
            del s[2:]

    def blit(self, sx, sy, w, h, ddx, ddy):
        rows = range(ROWS - 1, -1, -1) if ddy > 0 else range(ROWS)
        cols = range(COLS - 1, -1, -1) if ddx > 0 else range(COLS)
        for cy in rows:
            for cx in cols:
                snap = list(self.slots[cy * COLS + cx])
                for (x, y, g, c) in reversed(snap):       # older first
                    if sx <= x and x + 8 <= sx + w and sy <= y and y + 8 <= sy + h:
                        self.add(x + ddx, y + ddy, g, c)

    def shown(self, shadow, k):
        for h in self.slots[k]:
            a = verify(shadow, h)
            if a is not None:
                return h, a
        return None

    def cell(self, shadow, cy, cx, shown):
        own = shown[cy * COLS + cx]
        if own is not None:
            h, a = own
            return a << 8 | h[3]
        claim = [0] * 8
        claim_bg = None
        for ny in (cy - 1, cy, cy + 1):
            for nx in (cx - 1, cx, cx + 1):
                if not (0 <= ny < ROWS and 0 <= nx < COLS):
                    continue
                s = shown[ny * COLS + nx]
                if s is None:
                    continue
                (x, y, _, _), a = s
                dxo = x - 8 * cx
                if dxo >= 8 or dxo <= -8:
                    continue
                bits = (0xFF >> dxo) if dxo >= 0 else (0xFF << -dxo) & 0xFF
                hit = False
                for r in range(8):
                    if y <= 8 * cy + r < y + 8:
                        claim[r] |= bits
                        hit = True
                if hit and claim_bg is None:
                    claim_bg = a >> 4
        live = [~c & 0xFF for c in claim]
        counts = [0] * 16
        for r in range(8):
            for c in range(8):
                if live[r] & (0x80 >> c):
                    counts[pixel(shadow, 8 * cx + c, 8 * cy + r)] += 1
        bg = fg = None
        for k in range(16):
            if counts[k] and (bg is None or counts[k] > counts[bg]):
                bg = k
        if bg is None:
            b = claim_bg or 0
            return (b << 4 | b) << 8 | 0x20
        for k in range(16):
            if k != bg and counts[k] and (fg is None or counts[k] > counts[fg]):
                fg = k
        if fg is None:
            return (bg << 4 | bg) << 8 | 0x20
        mask = [0] * 8
        for r in range(8):
            for c in range(8):
                b = 0x80 >> c
                if live[r] & b and pixel(shadow, 8 * cx + c, 8 * cy + r) == fg:
                    mask[r] |= b
        return (bg << 4 | fg) << 8 | pick_char(mask, live)

    def ideal(self, shadow):
        shown = [self.shown(shadow, k) for k in range(NCELL)]
        return [self.cell(shadow, k // COLS, k % COLS, shown) for k in range(NCELL)]

    def present(self, shadow, ay, by, cx, dx):
        """Flush of pixel rows ay..by-1, byte columns cx..dx-1 (clamped)."""
        ay, by = max(ay, 0), min(by, H)
        cx, dx = max(cx, 0), min(dx, COLS)
        if ay >= by or cx >= dx:
            return
        r0, r1 = max((ay >> 3) - 1, 0), min(((by - 1) >> 3) + 1, ROWS - 1)
        c0, c1 = max(cx - 1, 0), min(dx - 1 + 1, COLS - 1)
        shown = [None] * NCELL
        for cy in range(max(r0 - 1, 0), min(r1 + 1, ROWS - 1) + 1):
            for x in range(max(c0 - 1, 0), min(c1 + 1, COLS - 1) + 1):
                shown[cy * COLS + x] = self.shown(shadow, cy * COLS + x)
        for cy in range(r0, r1 + 1):
            for x in range(c0, c1 + 1):
                self.text[cy * COLS + x] = self.cell(shadow, cy, x, shown)


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


def render(text, font):
    """40x25 text words drawn with an 8x8 CP437 font as a 320x200 RGB image."""
    from PIL import Image
    im = Image.new("RGB", (W, H))
    px = im.load()
    for k, word in enumerate(text):
        cy, cx = divmod(k, COLS)
        code, attr = word & 255, word >> 8
        fg, bg = PAL[attr & 15], PAL[attr >> 4]
        for r in range(8):
            bits = font[code * 8 + r]
            for c in range(8):
                px[cx * 8 + c, cy * 8 + r] = fg if (bits >> (7 - c)) & 1 else bg
    return im


def oracle_hints(frame, fonts):
    """Hints found by searching a picture for runs of exact glyphs.

    Stands in for the driver's text recording when only a picture exists
    (reference frames from the Plantronics driver). Only letters, digits
    and punctuation with 6+ pixels, in runs of 2+ on an 8-pixel pitch,
    count, so that lines are not mistaken for '-' or '|'.
    """
    import importlib.machinery
    F = importlib.machinery.SourceFileLoader(
        "fntread", str(Path(__file__).with_name("FNTREAD.PY"))).load_module()
    table = {}
    for path, oem in fonts:
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
    for (x, y) in list(found):
        if (x + 16, y) in found and (x + 8, y) not in found:
            t = set(frame[(y + r) * W + x + 8 + c] for r in range(8) for c in range(8))
            if len(t) == 1:
                hints.append((x + 8, y, [0] * 8, 0x20))
    return hints


def check():
    """Self-test of properties the driver relies on (no emulator)."""
    import random
    rnd = random.Random(40)
    p = Presenter()
    sh = bytearray(32000)
    g = [0x18, 0x3C, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00]
    spots = ((13, 21), (0, 0), (192, 312), (100, 4))
    for y0, x0 in spots:
        for r in range(8):
            for c in range(8):
                v = 15 if (g[r] >> (7 - c)) & 1 else 1
                x, yy = x0 + c, y0 + r
                for pl, bitv in ((0, 4), (40, 2), (80, 1), (120, 8)):
                    if v & bitv:
                        sh[yy * 160 + pl + (x >> 3)] |= 0x80 >> (x & 7)
        p.add(x0, y0, g, ord("A"))
    t = p.ideal(sh)
    for y0, x0 in spots:
        k = hint_cell(x0, y0)
        assert t[k] == (0x1F << 8 | 0x41), (x0, y0, hex(t[k]))
    p.present(sh, 0, 200, 0, 40)
    assert p.text == t
    # Partial presents keep the text equal to the ideal after pixel edits.
    for _ in range(40):
        y = rnd.randrange(200)
        xb = rnd.randrange(40)
        sh[y * 160 + xb + 40 * rnd.randrange(4)] ^= 1 << rnd.randrange(8)
        p.present(sh, y, y + 1, xb, xb + 1)
        assert p.text == p.ideal(sh)
    print("T40MODEL: check PASS")
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    from PIL import Image
    if len(argv) < 3:
        print(__doc__)
        return 2
    frame = Image.open(argv[1]).tobytes()
    if len(frame) != W * H:
        raise SystemExit("T40MODEL: expects a decoded 320x200 frame")
    root = Path(__file__).resolve().parents[2] / "distributions" / "WINXT"
    fonts = [(root / "XTTSYS.FON", False), (root / "XTCOEM.FON", True)]
    p = Presenter()
    for h in oracle_hints(frame, fonts):
        p.add(*h)
    text = p.ideal(shadow_from_frame(frame))
    if "--font" in argv:
        font = Path(argv[argv.index("--font") + 1]).read_bytes()
        render(text, font).save(argv[2])
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(text))
    shown = sum(1 for w in text if 32 < (w & 255) < 127)
    print(f"T40MODEL: {shown} cells show letters/digits/punctuation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
