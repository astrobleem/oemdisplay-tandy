#!/usr/bin/env python3
"""TEXT80 compact UI profile: window-control bitmaps one text cell each.

  python3 src/text80/T80UI.PY --show          print the bitmaps as text
  (BUILDT80.PY --variant t80c stages them into the driver's resources)

The stock resources were drawn for pixels: on the CGA-resolution set a
minimize button is 27x14, more than three text cells by two, and the
presenter can only approximate it with blocks and shades. Here every
caption button, scroll arrow, menu check and submenu arrow is an 8x8
bitmap drawn from the first-party OEM font's own glyph (XTCOEM.FON,
T40MODEL.UIGLYPHS), black on white; the pressed versions are the same
glyph white on black. When USER draws one on a cell boundary, the
presenter's exact-glyph rule shows that character.

  minimize   down triangle 1Fh      maximize   up triangle 1Eh
  restore    up-down arrow 12h      system menu three bars F0h
  scroll     1Eh 1Fh 11h 10h        menu check  check mark FBh
  submenu    right triangle 10h     combo box  down triangle 1Fh
  size box   blank

CONFIG.ASM (the OEM machine-dependent parameters) gets 8-pixel scroll
thumbs and 1-pixel vertical lines (cxBorder), so that a sizing frame is
(BorderWidth + 1) pixels both ways: with WIN.INI BorderWidth=7, one cell.
Everything else (colours, fonts) is the CGA-resolution set TEXT80 uses.
(Experimental: the metrics this gives are measured with TPROF METRICS.)
"""
import argparse
import importlib.machinery
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = importlib.machinery.SourceFileLoader("t40model_ui", str(HERE.parent / "txt40" / "T40MODEL.PY")).load_module()
UI = {code: rows for code, rows in M.UIGLYPHS}
BLANK = [0] * 8


def bmp(rows, width, inverse=False):
    """1-bit Windows 3.0 bitmap file (BITMAPCOREHEADER, palette black,
    white) of the given rows (bit 1 = ink, leftmost pixel = bit 7 of the
    first byte); ink is black, or white when inverse."""
    height = len(rows)
    stride = (width + 31) // 32 * 4
    bits = bytearray()
    for r in reversed(rows):                       # bottom-up
        line = bytearray(stride)
        for x in range(width):
            ink = (r >> (width - 1 - x)) & 1
            white = ink if inverse else 1 - ink
            if white:
                line[x >> 3] |= 0x80 >> (x & 7)
        bits += line
    header = struct.pack("<IHHHH", 12, width, height, 1, 1)
    palette = bytes([0, 0, 0, 255, 255, 255])
    off = 14 + len(header) + len(palette)
    return struct.pack("<2sIHHI", b"BM", off + len(bits), 0, 0, off) + header + palette + bits


def side_by_side(a, b):
    return [(x << 8) | y for x, y in zip(a, b)]


def bitmaps():
    """{file name in the resources folder: BMP bytes} (RC_LOW.RC names)."""
    one = lambda code, inv=False: bmp(UI[code], 8, inv)
    return {
        "MIN.BMP": one(0x1F), "MIND.BMP": one(0x1F, True),
        "MAX.BMP": one(0x1E), "MAXD.BMP": one(0x1E, True),
        "RESTORE.BMP": one(0x12), "RESTORED.BMP": one(0x12, True),
        "SYSMENU.BMP": bmp(side_by_side(UI[0xF0], UI[0xF0]), 16),
        "UP.BMP": one(0x1E), "UPD.BMP": one(0x1E, True),
        "DOWN.BMP": one(0x1F), "DOWND.BMP": one(0x1F, True),
        "LEFT.BMP": one(0x11), "LEFTD.BMP": one(0x11, True),
        "RIGHT.BMP": one(0x10), "RIGHTD.BMP": one(0x10, True),
        "OCHECK.BMP": one(0xFB),
        "MNARROW.BMP": one(0x10),
        "COMBO.BMP": one(0x1F),
        "OBTSIZE.BMP": bmp(BLANK, 8),
    }


CONFIG_EDITS = [
    ("\tdw\t2\t\t\t;cxBorder", "\tdw\t1\t\t\t;cxBorder (T80UI: frames of whole cells with BorderWidth=7)"),
    ("        dw      11                      ;Height of vertical thumb",
     "        dw      8                       ;Height of vertical thumb (T80UI: one cell)"),
    ("        dw      23                      ;Width of horizontal thumb",
     "        dw      8                       ;Width of horizontal thumb (T80UI: one cell)"),
]


def stage(resources, mp):
    """Write the compact bitmaps and CONFIG edits into a staged resources
    folder (after BUILDT80's res640). mp: MODEPROF's read/write/replace."""
    for name, data in bitmaps().items():
        (Path(resources) / name).write_bytes(data)
    cfg = mp.read(Path(resources) / "CONFIG.ASM")
    for old, new in CONFIG_EDITS:
        cfg = mp.replace(cfg, old, new)
    mp.write(Path(resources) / "CONFIG.ASM", cfg)


def show():
    for name, data in bitmaps().items():
        off = struct.unpack_from("<I", data, 10)[0]
        w, h = struct.unpack_from("<HH", data, 18)
        stride = (w + 31) // 32 * 4
        print(name, w, h)
        for r in range(h - 1, -1, -1):
            row = data[off + r * stride:off + r * stride + stride]
            bits = "".join(format(b, "08b") for b in row)[:w]
            print("   ", bits.replace("0", "#").replace("1", "."))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    if a.show:
        show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
