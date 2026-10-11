#!/usr/bin/env python3
"""Decode an 86Box screenshot of a 320x200x16 screen to exact pixels.

Usage:
  python3 src/pcp/SHOTDEC.PY <86box-screenshot.png> <out-320x200.png> [--json <out.json>]

86Box (v6.0) scales the 640x400 picture of a 320x200 mode, plus its 8-pixel
CGA border in graphics modes, by the window factor, smoothing pixel edges. This samples each logical pixel at
its centre and snaps it to the nearest of the 16 IRGB colors. It FAILS
(exit 1) unless every one of the 64,000 samples lies within 24 (max channel
difference) of a palette color, so a blurred, shifted or wrongly sized
capture is rejected instead of silently decoded. The output PNG is a
paletted 320x200 image whose index equals the IRGB color number.
"""
import json
import sys

from PIL import Image

PAL = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
       (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
       (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
       (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
TOL = 24


def decode(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # Text-mode captures are 640x400; graphics-mode captures add the 8-pixel
    # CGA overscan border on every side (656x416). Pick the uniform one.
    for bw, bh, ox, oy in ((656, 416, 8, 8), (640, 400, 0, 0)):
        sx, sy = w / float(bw), h / float(bh)
        if abs(sx - sy) <= 0.005 and sx >= 1.5:
            break
    else:
        raise SystemExit(f"SHOTDEC: {w}x{h} is not a uniform >=1.5x scale of 656x416 or 640x400")
    px = im.load()
    idx = bytearray(64000)
    worst = 0
    bad = 0
    for y in range(200):
        cy = int((oy + 2 * y + 1) * sy)
        for x in range(320):
            cx = int((ox + 2 * x + 1) * sx)
            c = px[cx, cy]
            best, dist = 0, 999
            for i, p in enumerate(PAL):
                d = max(abs(c[0] - p[0]), abs(c[1] - p[1]), abs(c[2] - p[2]))
                if d < dist:
                    best, dist = i, d
            worst = max(worst, dist)
            if dist > TOL:
                bad += 1
            idx[y * 320 + x] = best
    return idx, worst, bad, (w, h), f"{bw}x{bh}+{ox}+{oy} x{sx:.4f}"


def save(idx, out):
    img = Image.frombytes("P", (320, 200), bytes(idx))
    flat = [v for p in PAL for v in p] + [0] * (768 - 48)
    img.putpalette(flat)
    img.save(out)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    idx, worst, bad, size, geom = decode(argv[1])
    counts = [0] * 16
    for v in idx:
        counts[v] += 1
    res = {"geometry": geom, "source": argv[1].split("/")[-1], "size": list(size), "worst_distance": worst,
           "samples_over_tolerance": bad, "color_counts": counts,
           "verdict": "PASS" if bad == 0 else "FAIL"}
    if bad == 0:
        save(idx, argv[2])
    if "--json" in argv:
        with open(argv[argv.index("--json") + 1], "w") as f:
            json.dump(res, f, indent=1)
    print(json.dumps(res))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
