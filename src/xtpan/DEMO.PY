#!/usr/bin/env python3
"""Make the before/after demonstration of the panned desktop.

  python3 src/xtpan/DEMO.PY --out <demo.gif> --frame <capture.png> "<caption>" [--frame ...]

Each 86Box capture is decoded to its exact 320x200 pixels (SHOTDEC.PY;
a capture already decoded by it, a paletted 320x200 PNG, is taken as is),
doubled to 640x400 and given a caption bar; the frames become an animated
GIF (2.5 s per frame) and the first frame is also written as PNG beside
it. The pictures are the emulator's output, not mock-ups.
"""
import argparse
import importlib.machinery
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SHOTDEC = importlib.machinery.SourceFileLoader("shotdec", str(HERE / "SHOTDEC.PY")).load_module()


def frame(path, caption):
    with Image.open(path) as src:
        decoded = src.size == (320, 200) and src.mode == "P"
        if decoded:                         # already decoded: index = IRGB
            idx = list(src.tobytes())
    if not decoded:
        idx, worst, bad, size, geom = SHOTDEC.decode(str(path), 320)
        if bad:
            raise SystemExit(f"DEMO: {path} does not decode exactly")
    im = Image.new("RGB", (320, 200))
    im.putdata([SHOTDEC.PAL[i] for i in idx])
    im = im.resize((640, 400), Image.NEAREST)
    out = Image.new("RGB", (640, 440), (24, 24, 24))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:                       # older Pillow: fixed small font
        font = ImageFont.load_default()
    d.text((10, 412), caption, fill=(255, 255, 255), font=font)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--frame", nargs=2, action="append", required=True, metavar=("CAPTURE", "CAPTION"))
    a = ap.parse_args()
    frames = [frame(Path(p), c) for p, c in a.frame]
    frames[0].save(a.out.with_suffix(".PNG"))
    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=2500, loop=0)
    print(f"DEMO: {len(frames)} frames -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
