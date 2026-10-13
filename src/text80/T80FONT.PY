#!/usr/bin/env python3
"""Build TEXT80's added font faces from the first-party 8x8 XT strike.

  python3 src/text80/T80FONT.PY --out <dir>

TEXT80 recognises text only in fonts whose glyphs are 8x8 pixels. Windows
3.0's dialogs and many applications ask for "Helv" (and some for
"Courier"); on this 640x200 device (96x48 dpi) the installed EGA-resolution
faces (96x72) are proportional or taller and would show only as
approximation. Instead of erasing WIN.INI's [fonts] list, the TEXT80 setup
ADDS two faces at exactly the device's resolution, which the font mapper
then prefers for those names:
  T80HELV.FON  face "Helv"     family Swiss
  T80COUR.FON  face "Courier"  family Modern
Both are the strike of distributions/WINXT/XTTSYS.FON (first-party, 8x8,
96x48, 12 points) with only the face name and family changed; the FON
container is written by tools/XTFONTS/BUILD.PY's fon(). Removing the two
[fonts] lines (T80OFF.BAT restores the saved WIN.INI) undoes it.
"""
import argparse
import hashlib
import importlib.machinery
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# face, family, module name, variable pitch. Dialogs ask for "Helv" with
# VARIABLE_PITCH: a fixed-pitch Helv loses to the installed EGA-resolution
# HELVB.FON on the pitch penalty (seen in 86Box: the Run dialog's labels in
# HELVB's 10-pixel strike, two text rows tall, unreadable). So the Helv
# face is marked variable pitch (dfPixWidth 0); every glyph is still 8
# pixels wide, so it lays out exactly like the fixed strike. It is also
# marked bold (dfWeight 700): Windows 3.0 dialogs ask for bold Helv, and
# for a normal-weight face GDI simulates bold by drawing every string twice,
# one pixel apart (seen in 86Box with the ExtTextOut trace: each dialog
# label drawn twice, the glyphs smeared, so no cell matched its hint). The
# strike's pixels are unchanged; only the weight it is offered at.
FACES = {"T80HELV.FON": ("Helv", 0x20, "T80HELV", True, 700),
         "T80COUR.FON": ("Courier", 0x30, "T80COUR", False, 400)}
XTTSYS_SHA = "dbc26ad717340070b4da1948d97eb5ba24528e0a5cd0853199884d6cca8d51aa"


def strike(fon):
    ne = struct.unpack_from("<H", fon, 0x3C)[0]
    rt = ne + struct.unpack_from("<H", fon, ne + 0x24)[0]
    sh = struct.unpack_from("<H", fon, rt)[0]
    p = rt + 2
    while True:
        t, n = struct.unpack_from("<HH", fon, p)
        p += 8
        if t == 0:
            raise SystemExit("T80FONT: no font resource")
        for _ in range(n):
            off, ln, _fl, rid = struct.unpack_from("<HHHH", fon, p)
            p += 12
            if t == 0x8008:
                f = fon[off << sh:(off << sh) + (ln << sh)]
                return f[:struct.unpack_from("<I", f, 2)[0]], rid & 0x7FFF


def renamed(fnt, face, family, variable=False, weight=400):
    fo = struct.unpack_from("<I", fnt, 105)[0]
    body = bytearray(fnt[:fo]) + face.encode("ascii") + b"\0"
    struct.pack_into("<I", body, 2, len(body))
    body[90] = (fnt[90] & 0x0F) | family          # keep pitch bits, set family
    struct.pack_into("<H", body, 83, weight)       # dfWeight
    if variable:
        body[90] |= 1                             # variable pitch
        struct.pack_into("<H", body, 86, 0)       # dfPixWidth 0: widths from the table
    return bytes(body)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    src = (ROOT / "distributions" / "WINXT" / "XTTSYS.FON").read_bytes()
    if hashlib.sha256(src).hexdigest() != XTTSYS_SHA:
        raise SystemExit("T80FONT: XTTSYS.FON hash mismatch")
    sys.modules["GLYPHS"] = importlib.machinery.SourceFileLoader(
        "GLYPHS", str(ROOT / "tools" / "XTFONTS" / "GLYPHS.PY")).load_module()
    build = importlib.machinery.SourceFileLoader("xtfontbuild", str(ROOT / "tools" / "XTFONTS" / "BUILD.PY")).load_module()
    fnt, rid = strike(src)
    for v, want in ((66, 0), (70, 48), (72, 96), (86, 8), (88, 8)):
        if struct.unpack_from("<H", fnt, v)[0] != want:
            raise SystemExit(f"T80FONT: XTTSYS header field at {v} is not {want}")
    a.out.mkdir(parents=True, exist_ok=True)
    rec = {"source": "distributions/WINXT/XTTSYS.FON", "source_sha256": XTTSYS_SHA, "fonts": {}}
    for name, (face, family, module, variable, weight) in FACES.items():
        data = build.fon(renamed(fnt, face, family, variable, weight), module, rid,
                         f"TEXT80 {face} 8x8 (XT Pixels strike), 96x48")
        rec_pitch = "variable (all glyphs 8 wide)" if variable else "fixed"
        (a.out / name).write_bytes(data)
        rec["fonts"][name] = {"face": face, "pitch": rec_pitch, "weight": weight, "bytes": len(data),
                              "sha256": hashlib.sha256(data).hexdigest()}
    (a.out / "T80FONT.JSN").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
