#!/usr/bin/env python3
"""Host verifier for JRPROBE output (see docs/PCJR.MD).

Usage: python3 src/pcjr/JRCHECK.PY <dir-with-JRPROBE.TXT> [--png <out.png>]

Checks, without trusting the guest's own conclusions:
  1. JRVRAM.BIN (the page the probe wrote through its target segment)
     exactly matches the TANDY88 320x200x16 bank formula at all 32,000
     pattern bytes. The 768 padding bytes are not judged: the probe does
     not clear them first.
  2. Whether the B800h window is a 16KB window aliased at BC00h
     (PCjr-style) or a full distinct 32KB window (Tandy-style), and
     whether it shows the same bytes as the physical page.
Writes a JSON verdict to stdout. --png renders an ILLUSTRATIVE preview of
JRVRAM.BIN decoded with the formula and a standard IRGB palette; it is a
raw-VRAM decode, not an emulator screenshot.
"""
import json
import sys
from pathlib import Path

ROWS, XBYTES = 200, 160


def expected():
    out = {}
    for y in range(ROWS):
        base = (y & 3) * 8192 + (y >> 2) * 160
        for xb in range(XBYTES):
            c = ((xb >> 3) + y) & 15
            out[base + xb] = (c << 4) | (c ^ 15)
    return out


def parse_report(text):
    vals = {}
    for token in text.split():
        if "=" in token:
            k, v = token.split("=", 1)
            vals[k] = v
    return vals


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    d = Path(argv[1])
    rep = parse_report((d / "JRPROBE.TXT").read_text(errors="replace"))
    vram = (d / "JRVRAM.BIN").read_bytes()
    b800 = (d / "JRB800.BIN").read_bytes()
    exp = expected()
    mism = [o for o, v in exp.items() if vram[o] != v]
    lo, hi = b800[:0x4000], b800[0x4000:]
    alias16 = lo == hi
    same_as_page = b800 == vram
    same_as_low16 = lo == vram[:0x4000] or lo == vram[0x4000:]
    verdict = {
        "report": rep,
        "pattern_bytes": len(exp),
        "pattern_mismatches": len(mism),
        "first_mismatch": mism[0] if mism else None,
        "b800_low_equals_high_16k": alias16,
        "b800_equals_written_page": same_as_page,
        "b800_low_16k_equals_a_page_half": same_as_low16,
    }
    if rep.get("MODEL") == "FD":
        if mism:
            verdict["interpretation"] = "PCjr: physical-segment write FAILED"
        elif alias16 and not same_as_page:
            verdict["interpretation"] = (
                "PCjr: physical-segment write correct; B800 shows one 16KB "
                "CPU page aliased at BC00 (documented PCjr behavior)")
        elif same_as_page:
            verdict["interpretation"] = (
                "PCjr: physical-segment write correct; this emulator also "
                "maps the full 32KB at B800 (more lenient than real PCjr)")
        else:
            verdict["interpretation"] = "PCjr: unexpected B800 contents; inspect dumps"
    else:
        verdict["interpretation"] = (
            "Non-PCjr control: full 32KB at B800"
            if same_as_page and not mism else "Control: unexpected; inspect dumps")
    print(json.dumps(verdict, indent=1, sort_keys=True))
    if "--png" in argv:
        from PIL import Image
        pal = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
               (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
               (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
               (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
        img = Image.new("RGB", (320, 200))
        px = img.load()
        for y in range(ROWS):
            base = (y & 3) * 8192 + (y >> 2) * 160
            for xb in range(XBYTES):
                b = vram[base + xb]
                px[2 * xb, y] = pal[b >> 4]
                px[2 * xb + 1, y] = pal[b & 15]
        img.save(argv[argv.index("--png") + 1])
    return 0 if not mism else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
