#!/usr/bin/env python3
"""Compare two RRBENCH runs frame for frame (exact video memory).

  python3 src/rrect/RRCMP.PY <reference run> <candidate run> [--png <dir>] [--json <file>]

Each run directory holds RRBENCH.LOG and RBnn.BIN (the 32 KB B800h frame
buffer after stage nn; mode 09h: offset (y%4)*8192+(y//4)*160+x//2, even X
in the high nibble). Every stage present in either run must be present in
both with byte-identical 32,768-byte dumps (all banks, including the padding
bytes after each bank's 8,000 displayed bytes), the same stage names and the
same API success counts. Differences are reported as a pixel count and
bounding box per stage; --png writes reference/candidate/difference images.
Timings are reported but never compared. Exit 0 only if everything matches.
"""
import argparse
import json
import sys
from pathlib import Path

IRGB = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0),
        (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85),
        (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def pixels(dump):
    """320x200 colour indices from a mode 09h dump."""
    out = bytearray(64000)
    for y in range(200):
        base = (y % 4) * 8192 + (y // 4) * 160
        for x in range(320):
            v = dump[base + x // 2]
            out[y * 320 + x] = (v >> 4) if x % 2 == 0 else (v & 15)
    return bytes(out)


def stages(log_text):
    out, cur = {}, None
    for line in log_text.replace("\r", "").split("\n"):
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k == "STAGE":
            cur = out.setdefault(int(v), {"repaint_ms": []})
        elif cur is not None:
            if k == "REPAINT_MS":
                cur["repaint_ms"].append(int(v))
            elif k in ("NAME", "TITLE"):
                cur[k.lower()] = v
            elif k in ("ELAPSED_MS", "API_SUCCESSES", "LAUNCH_TO_PAINTED_MS", "APP_FOUND", "CALC_FOUND"):
                cur[k.lower()] = int(v)
    return out


def compare_dumps(a, b):
    if len(a) != 32768 or len(b) != 32768:
        return {"equal": False, "error": f"dump sizes {len(a)}, {len(b)}"}
    if a == b:
        return {"equal": True, "differing_pixels": 0, "differing_bytes": 0}
    pa, pb = pixels(a), pixels(b)
    d = [i for i in range(64000) if pa[i] != pb[i]]
    box = None
    if d:
        xs, ys = [i % 320 for i in d], [i // 320 for i in d]
        box = [min(xs), min(ys), max(xs), max(ys)]
    return {"equal": False, "differing_bytes": sum(x != y for x, y in zip(a, b)),
            "differing_pixels": len(d), "bbox": box}


def image(px, path, diff_with=None):
    from PIL import Image
    im = Image.new("RGB", (320, 200))
    data = []
    for i, c in enumerate(px):
        if diff_with is not None:
            data.append((255, 0, 0) if c != diff_with[i] else tuple(v // 3 for v in IRGB[c]))
        else:
            data.append(IRGB[c])
    im.putdata(data)
    im.resize((640, 400), Image.NEAREST).save(path)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ref", type=Path)
    ap.add_argument("cand", type=Path)
    ap.add_argument("--png", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    sa = stages((a.ref / "RRBENCH.LOG").read_text(errors="replace"))
    lb = a.cand / "RRBENCH.LOG"
    sb = stages(lb.read_text(errors="replace")) if lb.exists() else {}
    ok = bool(sa) and sorted(sa) == sorted(sb)
    rows = []
    for n in sorted(set(sa) | set(sb)):
        ra, rb = sa.get(n, {}), sb.get(n, {})
        fa, fb = a.ref / f"RB{n:02d}.BIN", a.cand / f"RB{n:02d}.BIN"
        if fa.exists() and fb.exists():
            c = compare_dumps(fa.read_bytes(), fb.read_bytes())
        else:
            c = {"equal": False, "error": "dump missing"}
        same_meta = (ra.get("name") == rb.get("name") and ra.get("api_successes") == rb.get("api_successes"))
        row = {"stage": n, "name": ra.get("name"), "frame": c, "same_name_and_api_results": same_meta,
               "ref_ms": ra.get("elapsed_ms", ra.get("repaint_ms")),
               "cand_ms": rb.get("elapsed_ms", rb.get("repaint_ms"))}
        ok = ok and c["equal"] and same_meta
        rows.append(row)
        print(f"{n:2d} {str(ra.get('name')):18s} {'EQUAL' if c['equal'] else 'DIFFERS'} "
              f"{c.get('differing_pixels', '-')} px {c.get('bbox', '')}  ref {row['ref_ms']}  cand {row['cand_ms']}")
        if a.png and not c["equal"] and "error" not in c:
            a.png.mkdir(parents=True, exist_ok=True)
            pa, pb = pixels(fa.read_bytes()), pixels(fb.read_bytes())
            image(pa, a.png / f"S{n:02d}_REF.PNG")
            image(pb, a.png / f"S{n:02d}_CAND.PNG")
            image(pb, a.png / f"S{n:02d}_DIFF.PNG", diff_with=pa)
    res = {"reference": str(a.ref.name), "candidate": str(a.cand.name), "all_frames_equal": ok, "stages": rows}
    if a.json:
        a.json.write_text(json.dumps(res, indent=1) + "\n")
    print("ALL FRAMES EQUAL" if ok else "FRAMES DIFFER")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
