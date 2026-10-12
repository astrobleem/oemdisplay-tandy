#!/usr/bin/env python3
"""Check an 86Box capture of the PANTEST PATTERN window pixel by pixel.

  python3 src/xtpan/PANCHK.PY <capture.png> --top T [--off O] [--exclude x0,y0,x1,y1 ...]
      [--map <json>] [--json <out>]

The capture is decoded to exact 320x200 IRGB pixels by SHOTDEC.PY (any
off-palette sample fails). Video row p must show logical row T+p of the
pattern PANTEST draws: colour index c(x,y) = ((y+O)/8 + x/32) mod 16, and
12 + ((y+O)/8)/16 mod 4 in the rightmost 32 columns, so every 8-row band
of the 400-row desktop is distinct and a viewport that is off by any
number of rows fails. Colour indexes are Windows' (the driver's colour
table order); the IRGB value each one shows as is learnt once and must be
the same for every pixel and every capture (--map carries it between
captures). Rectangles given with --exclude (the pointer) are skipped.
"""
import argparse
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOTDEC = importlib.machinery.SourceFileLoader("shotdec", str(HERE / "SHOTDEC.PY")).load_module()


def colour(x, y, off=0):
    band = (y + off) >> 3
    if x >= 288:
        return 12 + ((band >> 4) & 3)
    return (band + (x >> 5)) & 15


def check(path, top, off=0, exclude=(), mapping=None):
    idx, worst, bad, size, geom = SHOTDEC.decode(str(path), 320)
    if bad:
        return {"capture": str(path), "decoded": False, "samples_off_palette": bad}
    mapping = dict(mapping or {})
    mism = 0
    first = None
    checked = 0
    for p in range(200):
        for x in range(320):
            if any(x0 <= x < x1 and y0 <= p < y1 for x0, y0, x1, y1 in exclude):
                continue
            want = colour(x, top + p, off)
            got = idx[p * 320 + x]
            checked += 1
            if str(want) not in mapping and got not in mapping.values():
                mapping[str(want)] = got
            if mapping.get(str(want)) != got:
                mism += 1
                if first is None:
                    first = {"x": x, "video_row": p, "logical_row": top + p, "want_index": want, "got_irgb": got}
    return {"capture": str(path), "decoded": True, "geometry": geom, "top": top, "off": off,
            "pixels_checked": checked, "mismatches": mism, "first_mismatch": first,
            "map": mapping, "verdict": "PASS" if mism == 0 and checked > 0 else "FAIL"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture", type=Path)
    ap.add_argument("--top", type=int, required=True)
    ap.add_argument("--off", type=int, default=0)
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--map", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    ex = [tuple(int(v) for v in e.split(",")) for e in a.exclude]
    mapping = json.loads(a.map.read_text()) if a.map and a.map.exists() else None
    res = check(a.capture, a.top, a.off, ex, mapping)
    if a.map and res.get("verdict") == "PASS":
        a.map.write_text(json.dumps(res["map"]) + "\n")
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res.get(k) for k in ("capture", "top", "pixels_checked", "mismatches",
                                               "first_mismatch", "verdict")}))
    return 0 if res.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
