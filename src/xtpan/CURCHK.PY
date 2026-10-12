#!/usr/bin/env python3
"""Re-check the pointer in a kept XTPAN run as an exact shape (no emulator).

  python3 src/xtpan/CURCHK.PY --run docs/pan/FINAL --drv <XTPAN.DRV> [--json <out>]

For every pattern capture of the run (XPWIN.JSN: logged pointer, viewport
top, pattern offset) the whole 320x200 frame must equal the pattern with
the driver's own arrow (PANCHK.arrow, read from --drv, whose SHA-256 must be
the one PREP.JSN recorded) composited at the logged hot spot. Negative
controls on the same frame must fail: the arrow one pixel left, right, up
or down, no arrow at all, and the arrow with one mask bit flipped (an
outline pixel made transparent). A check that cannot tell those apart is
not a cursor check.
"""
import argparse
import hashlib
import importlib.machinery
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANCHK = importlib.machinery.SourceFileLoader("panchk", str(HERE / "PANCHK.PY")).load_module()

SHORT = {"pat_top0": "PTOP0", "pat_key200": "PKEY200", "pat_key150": "PKEY150", "pat_keytop": "PKEYTOP",
         "pat_dwell50": "PDWELL", "pat_out150": "POUT150", "pat_scroll_top0": "PSCRL0",
         "pat_scroll_top200": "PSCRL20", "pat_repeat": "PREPEAT", "pat_repeat_top": "PREPTOP",
         "relaunch_top0": "RELTOP0", "relaunch_top100": "REL100"}


def flipped(arrow):
    """The arrow with its first outline pixel (AND 0, XOR 0) made transparent."""
    hx, hy, glyph = arrow
    g = list(glyph)
    i = next(k for k, (dx, dy, a, x) in enumerate(g) if not a and not x)
    dx, dy, _, _ = g[i]
    g[i] = (dx, dy, 1, 0)
    return hx, hy, g


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--drv", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    drv = a.drv.read_bytes()
    prep = json.loads((a.run / "PREP.JSN").read_text())
    sha = hashlib.sha256(drv).hexdigest()
    if sha != prep.get("driver_sha256"):
        raise SystemExit(f"CURCHK: {a.drv} is not the driver of this run ({sha[:12]} != "
                         f"{str(prep.get('driver_sha256'))[:12]})")
    arrow = PANCHK.arrow(drv)
    run = json.loads((a.run / "XPWIN.JSN").read_text())
    out, fails, mapping = [], 0, {}
    for c in run["checks"]:
        if "pointer" not in c:
            continue
        name = c["check"].split(":")[0]
        off = int(re.search(r"\(off (\d+)\)", c["check"]).group(1))
        x, y = c["pointer"]
        top = c["top"]
        cap = a.run / (SHORT[name] + ".PNG")
        vy = y - top
        res = PANCHK.check(cap, top, off, (), mapping, (x, vy, arrow))
        if res["verdict"] == "PASS":
            mapping = res["map"]
        controls = {}
        for label, cur in (("left", (x - 1, vy, arrow)), ("right", (x + 1, vy, arrow)),
                           ("up", (x, vy - 1, arrow)), ("down", (x, vy + 1, arrow)),
                           ("no arrow", None), ("one mask bit flipped", (x, vy, flipped(arrow)))):
            r = PANCHK.check(cap, top, off, (), mapping, cur)
            controls[label] = {"verdict": r["verdict"], "mismatches": r["mismatches"]}
        ok = res["verdict"] == "PASS" and all(v["verdict"] == "FAIL" for v in controls.values())
        fails += not ok
        out.append({"capture": cap.name, "top": top, "off": off, "hot_spot": [x, vy],
                    "frame_pixels": res["pixels_checked"], "mismatches": res["mismatches"],
                    "arrow_pixels_in_view": res["cursor_pixels"],
                    "arrow_pixels_differing_from_pattern": res["cursor_pixels_differing_from_pattern"],
                    "negative_controls": controls, "result": "PASS" if ok else "FAIL",
                    "first_mismatch": res["first_mismatch"]})
        print(("PASS " if ok else "FAIL ") + f"{cap.name} hot spot ({x},{vy}) top {top}: "
              f"{res['mismatches']} mismatches, {res['cursor_pixels']} arrow pixels; controls "
              + ", ".join(f"{k} {v['mismatches']}" for k, v in controls.items()), flush=True)
    rec = {"run": str(a.run), "driver_sha256": sha, "arrow_hot_spot": list(arrow[:2]),
           "arrow_size": [max(g[0] for g in arrow[2]) + 1, max(g[1] for g in arrow[2]) + 1], "captures": out, "passed": len(out) - fails, "failed": fails}
    if a.json:
        a.json.write_text(json.dumps(rec, indent=1) + "\n")
    return 0 if out and not fails else 1


if __name__ == "__main__":
    sys.exit(main())
