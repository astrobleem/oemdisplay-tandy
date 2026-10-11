#!/usr/bin/env python3
"""Host verifier for T2PROBE output (see docs/TGA2.MD).

Usage: python3 src/tga2/T2CHECK.PY <dir-with-T2PROBE.TXT> [--png <out.png>]
       python3 src/tga2/T2CHECK.PY <dir> --expect-unmapped   (negative control)

Exit 0 only for a verified pattern written under a report that proves the
mapping safe (SAFE_TO_WRITE=01, PATTERN_RAN=01, MAPPED_PARAS=1000,
MAP_INCONSISTENT=00); a matching image under any other report is a FAIL.
(Or, with --expect-unmapped, for a
complete report showing zero mapped paragraphs and no write). A report
without a pattern is exit 2, "not tested", never success.

Prints the probe's mapping verdict. When T2VRAM.BIN exists (the probe only
writes it after proving every window paragraph maps onto its own DOS
block), checks every byte of the 640x200x16 LINEAR hypothesis:
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
    rf = d / "T2PROBE.TXT"
    for tok in (rf.read_text(errors="replace").split() if rf.exists() else []):
        if "=" in tok:
            k, v = tok.split("=", 1)
            rep[k] = v
    out = {"report": rep}
    if rep.get("COMPLETE") != "1":
        out["verdict"] = "FAIL: T2PROBE.TXT missing or incomplete"
        print(json.dumps(out, indent=1, sort_keys=True))
        return 1
    dump = d / "T2VRAM.BIN"
    if "--expect-unmapped" in argv:
        ok = (rep.get("MAPPED_PARAS") == "0000" and rep.get("PATTERN_RAN") == "00"
              and rep.get("SAFE_TO_WRITE") == "00" and not dump.exists())
        out["verdict"] = "PASS: unmapped negative control" if ok else "FAIL: expected an unmapped window"
        print(json.dumps(out, indent=1, sort_keys=True))
        return 0 if ok else 1
    safe = (rep.get("SAFE_TO_WRITE") == "01" and rep.get("PATTERN_RAN") == "01"
            and rep.get("MAPPED_PARAS") == "1000" and rep.get("MAP_INCONSISTENT") == "00")
    if dump.exists() and (not safe or dump.stat().st_size != 0x10000):
        out["verdict"] = "FAIL: dump present but report does not prove a safe mapping, or size wrong"
        print(json.dumps(out, indent=1, sort_keys=True))
        return 1
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
        out["verdict"] = "NOT TESTED"
        print(json.dumps(out, indent=1, sort_keys=True))
        return 2
    out["verdict"] = "PASS" if out["pattern_mismatches"] == 0 else "FAIL"
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
