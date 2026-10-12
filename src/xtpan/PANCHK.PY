#!/usr/bin/env python3
"""Check an 86Box capture of the PANTEST PATTERN window pixel by pixel.

  python3 src/xtpan/PANCHK.PY <capture.png> --top T [--off O] [--drv <XTPAN.DRV> --cursor X,VY]
      [--exclude x0,y0,x1,y1 ...] [--map <json>] [--json <out>]

The capture is decoded to exact 320x200 IRGB pixels by SHOTDEC.PY (any
off-palette sample fails). Video row p must show logical row T+p of the
pattern PANTEST draws: colour index c(x,y) = ((y+O)/8 + x/32) mod 16, and
12 + ((y+O)/8)/16 mod 4 in the rightmost 32 columns, so every 8-row band
of the 400-row desktop is distinct and a viewport that is off by any
number of rows fails. Colour indexes are Windows' (the driver's colour
table order); the IRGB value each one shows as is learnt once and must be
the same for every pixel and every capture (--map carries it between
captures).

The pointer is checked as a shape, not skipped: with --drv the standard
arrow (OCR_NORMAL) is read from the driver binary under test (its NE
resource table; hot spot, 32x32 AND and XOR masks) and composited the way
TCURSOR.ASM draws it, pixel by pixel on the IRGB nibble in video memory:
AND bit 0 -> 0 (black), then XOR bit 1 -> nibble XOR 0Fh. --cursor X,VY puts
the hot spot at column X, video row VY. Every pixel of the frame must then
equal the expectation, so a cursor that is missing, shifted by one pixel,
the wrong shape or drawn twice fails. --exclude rectangles (any other
known-variable region) are skipped.
"""
import argparse
import importlib.machinery
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOTDEC = importlib.machinery.SourceFileLoader("shotdec", str(HERE / "SHOTDEC.PY")).load_module()


def colour(x, y, off=0):
    band = (y + off) >> 3
    if x >= 288:
        return 12 + ((band >> 4) & 3)
    return (band + (x >> 5)) & 15


OCR_NORMAL = 32512
RT_CURSOR, RT_GROUP_CURSOR = 1, 12


def ne_resources(drv):
    """{(type, id): bytes} of an NE executable's integer-named resources."""
    ne = struct.unpack_from("<H", drv, 0x3C)[0]
    if drv[ne:ne + 2] != b"NE":
        raise ValueError("not an NE executable")
    p = ne + struct.unpack_from("<H", drv, ne + 0x24)[0]
    shift = struct.unpack_from("<H", drv, p)[0]
    p += 2
    out = {}
    while True:
        rtype, count = struct.unpack_from("<HH", drv, p)
        p += 8
        if rtype == 0:
            return out
        for _ in range(count):
            off, length, _flags, rid = struct.unpack_from("<HHHH", drv, p)
            p += 12
            if rtype & 0x8000 and rid & 0x8000:
                out[(rtype & 0x7FFF, rid & 0x7FFF)] = drv[off << shift:(off << shift) + (length << shift)]


RT_OEMBIN = 0x7006              # NE type word F006h: the driver's CONFIG.ASM block (OEM segment)


def compression(res):
    """(horizontal, vertical) cursor compression factors from the driver's
    OEM configuration resource: words 4 and 5 of OEMBIN 1 (CONFIG.ASM:
    thumb heights, icon factors, then cursor factors)."""
    oem = res[(RT_OEMBIN, 1)]
    h, v = struct.unpack_from("<HH", oem, 8)
    if not (1 <= h <= 4 and 1 <= v <= 4):
        raise ValueError(f"implausible cursor compression {h}x{v}")
    return h, v


def arrow(drv):
    """(hot_x, hot_y, glyph) of the driver's OCR_NORMAL cursor as the driver
    receives it; glyph is a list of (dx, dy, and_bit, xor_bit) from the
    cursor's top-left corner.

    USER does not pass the 32x32 resource unchanged: it shrinks it by the
    cursor compression factors in the driver's OEMBIN (1 x 2 for the TR5
    320x200 drivers, so 32x16). Each output pixel combines its h x v block
    of source pixels by AND, for the AND mask and the XOR mask alike: it is
    opaque if any source pixel is opaque, white only if all are white,
    inverted only if all invert. That combination rule was identified by
    comparing the 86Box capture PTOP0 with the resource; it is one fixed
    rule applied to every capture, and the hot spot is divided likewise."""
    res = ne_resources(drv)
    hf, vf = compression(res)
    group = res[(RT_GROUP_CURSOR, OCR_NORMAL)]
    reserved, gtype, count = struct.unpack_from("<HHH", group, 0)
    if gtype != 2 or count < 1:
        raise ValueError("OCR_NORMAL is not a cursor group")
    cid = struct.unpack_from("<H", group, 6 + 12)[0]          # first entry's id
    cur = res[(RT_CURSOR, cid)]
    hx, hy = struct.unpack_from("<HH", cur, 0)
    size, w, h2, planes, bits = struct.unpack_from("<IiiHH", cur, 4)
    h = h2 // 2
    if size != 40 or planes != 1 or bits != 1 or w != 32 or h != 32:
        raise ValueError(f"unexpected cursor format {w}x{h}x{bits}")
    stride = 4
    xor_at = 4 + size + 8                                     # after the 2-entry palette
    and_at = xor_at + stride * h

    def bit(at, dx, dy):
        src = h - 1 - dy                                      # DIB rows are bottom-up
        return 1 if cur[at + src * stride + (dx >> 3)] & (0x80 >> (dx & 7)) else 0

    glyph = []
    for oy in range(h // vf):
        for ox in range(w // hf):
            block = [(ox * hf + i, oy * vf + j) for j in range(vf) for i in range(hf)]
            a = min(bit(and_at, dx, dy) for dx, dy in block)
            x = min(bit(xor_at, dx, dy) for dx, dy in block)
            glyph.append((ox, oy, a, x))
    return hx // hf, hy // vf, glyph


def check_idx(idx, top, off=0, exclude=(), mapping=None, cursor=None, width=320):
    """Check decoded IRGB pixels. cursor = (x, vy, (hot_x, hot_y, glyph)): the
    hot spot's column and video row; the glyph is composited on the pattern."""
    mapping = dict(mapping or {})
    over = {}
    if cursor:
        cx, cvy, (hx, hy, glyph) = cursor
        for dx, dy, a, x in glyph:
            px, py = cx - hx + dx, cvy - hy + dy
            if 0 <= px < width and 0 <= py < 200 and not (a and not x):
                over[py * width + px] = (a, x)

    def skip(x, p):
        return any(x0 <= x < x1 and y0 <= p < y1 for x0, y0, x1, y1 in exclude)

    # learn the colour map from pattern pixels only (never from cursor pixels)
    for p in range(200):
        for x in range(width):
            if skip(x, p) or p * width + x in over:
                continue
            want, got = colour(x, top + p, off), idx[p * width + x]
            if str(want) not in mapping and got not in mapping.values():
                mapping[str(want)] = got
    mism = checked = cur_px = cur_bad = changed = 0
    first = None
    for p in range(200):
        for x in range(width):
            if skip(x, p):
                continue
            i = p * width + x
            bg = mapping.get(str(colour(x, top + p, off)))
            exp = bg
            if i in over:
                a, xr = over[i]
                exp = None if bg is None and a else (bg if a else 0)
                if exp is not None and xr:
                    exp ^= 0x0F
                cur_px += 1
                changed += exp != bg
            checked += 1
            if idx[i] != exp:
                mism += 1
                if i in over:
                    cur_bad += 1
                if first is None:
                    first = {"x": x, "video_row": p, "logical_row": top + p, "want_irgb": exp,
                             "got_irgb": idx[i], "cursor_pixel": i in over}
    ok = mism == 0 and checked > 0 and (not cursor or changed > 0)
    return {"top": top, "off": off, "pixels_checked": checked, "mismatches": mism,
            "first_mismatch": first, "cursor": list(cursor[:2]) if cursor else None,
            "cursor_pixels": cur_px, "cursor_pixels_differing_from_pattern": changed,
            "cursor_mismatches": cur_bad, "map": mapping, "verdict": "PASS" if ok else "FAIL"}


def check(path, top, off=0, exclude=(), mapping=None, cursor=None):
    from PIL import Image
    with Image.open(path) as im:                  # already decoded by SHOTDEC: IRGB indexes
        if im.size == (320, 200) and im.mode == "P":
            res = check_idx(list(im.tobytes()), top, off, exclude, mapping, cursor)
            res.update(capture=str(path), decoded=True, geometry="decoded 320x200")
            return res
    idx, worst, bad, size, geom = SHOTDEC.decode(str(path), 320)
    if bad:
        return {"capture": str(path), "decoded": False, "samples_off_palette": bad, "verdict": "FAIL"}
    res = check_idx(idx, top, off, exclude, mapping, cursor)
    res.update(capture=str(path), decoded=True, geometry=geom)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture", type=Path)
    ap.add_argument("--top", type=int, required=True)
    ap.add_argument("--off", type=int, default=0)
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--map", type=Path)
    ap.add_argument("--drv", type=Path, help="driver binary whose OCR_NORMAL arrow is expected")
    ap.add_argument("--cursor", help="X,VY: hot spot column and video row (needs --drv)")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    ex = [tuple(int(v) for v in e.split(",")) for e in a.exclude]
    mapping = json.loads(a.map.read_text()) if a.map and a.map.exists() else None
    cur = None
    if a.cursor:
        if not a.drv:
            ap.error("--cursor needs --drv")
        cx, cvy = (int(v) for v in a.cursor.split(","))
        cur = (cx, cvy, arrow(a.drv.read_bytes()))
    res = check(a.capture, a.top, a.off, ex, mapping, cur)
    if a.map and res.get("verdict") == "PASS":
        a.map.write_text(json.dumps(res["map"]) + "\n")
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res.get(k) for k in ("capture", "top", "pixels_checked", "mismatches",
                                               "cursor", "cursor_pixels", "cursor_mismatches",
                                               "first_mismatch", "verdict")}))
    return 0 if res.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
