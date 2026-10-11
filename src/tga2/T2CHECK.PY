#!/usr/bin/env python3
"""Host verifier for T2PROBE output (see docs/TGA2.MD).

Usage: python3 src/tga2/T2CHECK.PY <dir-with-T2PROBE.TXT> [--png <out.png>]

Prints the probe's mapping verdict. When T2VRAM.BIN exists (the probe only
writes it after proving the window maps onto its own RAM or RAM above the
DOS arena), checks every byte of the 640x200x16 LINEAR hypothesis:
offset = y*320 + xb, high nibble = left pixel, 64,000 bytes, 1,536 tail
bytes not judged. --png decodes the dump with an illustrative IRGB palette;
it is a raw-VRAM decode, not a photo or emulator screenshot of the display.
"""
import json
import sys
from pathlib import Path


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    d = Path(argv[1])
    rep = {}
    for tok in (d / "T2PROBE.TXT").read_text(errors="replace").split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            rep[k] = v
    out = {"report": rep}
    dump = d / "T2VRAM.BIN"
    if dump.exists():
        v = dump.read_bytes()
        bad = 0
        first = None
        for y in range(200):
            for xb in range(320):
                c = ((xb >> 4) + y) & 15
                o = y * 320 + xb
                if v[o] != ((c << 4) | (c ^ 15)):
                    bad += 1
                    first = o if first is None else first
        out.update(pattern_bytes=64000, pattern_mismatches=bad, first_mismatch=first)
        if "--png" in argv:
            from PIL import Image
            pal = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
                   (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
                   (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
                   (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
            img = Image.new("RGB", (640, 200))
            px = img.load()
            for y in range(200):
                for xb in range(320):
                    b = v[y * 320 + xb]
                    px[2 * xb, y] = pal[b >> 4]
                    px[2 * xb + 1, y] = pal[b & 15]
            img.save(argv[argv.index("--png") + 1])
    else:
        out["pattern"] = "not run (window unmapped or not provably safe)"
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0 if out.get("pattern_mismatches", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
