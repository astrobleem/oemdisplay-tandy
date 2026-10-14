#!/usr/bin/env python3
"""Report a TPROF.LOG (src/text80/TPROF.C) as a time breakdown.

  python3 src/text80/T80PROFX.PY <TPROF.LOG> [--json <out>]

Times in the log are 1/65536 BIOS tick (54.9254 ms / 65536 = 0.838 us).
Per reading (one typed character in TYPE mode, or the whole NOTE window):
  wall        time between the two counter readings
  driver      time inside the drawing calls (TBitBlt, TOutput, TPixel,
              TScanLR, TStrBlt, TExtTextOut), including their flushes
  flush       every flush (presenter + cursor hide/show), inside or outside
              the drawing calls
  render      driver - flushes made inside the drawing calls = drawing into
              the shadow (TR5 code, unchanged)
  app/GDI     wall - driver - flushes outside drawing calls = Windows, the
              application and GDI
  verify      presenter pass 1 (re-verifying hints)
  convert     presenter pass 2 cell computation (t40_cell)
  write+loop  presenter pass 2 minus convert (video writes, loop)
  cursor etc  flush - presenter (cursor hide/show, clamping)
  cells / writes / verified / flushes and the flushed rectangles.
"""
import argparse
import json
import re
import sys

TICK_MS = 54.9254
UNIT_MS = TICK_MS / 65536
SLOTS = {0: "flush", 1: "present", 2: "verify", 3: "outpass", 4: "cell", 5: "BitBlt", 6: "Output",
         7: "Pixel", 8: "ScanLR", 9: "StrBlt", 10: "ExtTextOut", 11: "hints", 12: "hintmove",
         13: "verified", 14: "writes", 15: "snapshot", 16: "compares", 17: "diffflush"}
WRAP = (5, 6, 7, 8, 9, 10)


def parse(path):
    readings, cur, extra = [], None, []
    for ln in open(path, encoding="latin-1"):
        ln = ln.rstrip("\r\n")
        m = re.match(r"(CHAR \d+|LINE \d+|SNAP|IDLE|NOTE) stamp=(\d+) wall=(\d+)", ln)
        if m:
            cur = {"label": m.group(1), "wall": int(m.group(3)), "S": {}, "F": [], "X": []}
            readings.append(cur)
            continue
        m = re.match(r" S (\d+) (\d+) (\d+)", ln)
        if m and cur:
            cur["S"][int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
            continue
        m = re.match(r" F (-?\d+) (-?\d+) (-?\d+) (-?\d+) (\d+) (\d+)", ln)
        if m and cur:
            cur["F"].append(tuple(int(v) for v in m.groups()))
            continue
        m = re.match(r" X ((?:\s*-?\d+){15,18})$", ln)
        if m and cur:
            v = [int(x) for x in m.group(1).split()]
            x = {"clip": v[0:4], "opaque": v[4:8], "options": v[8], "count": v[9],
                 "bounds_rows": v[10:12], "bounds_cols": v[12:14], "dirty": v[14]}
            if len(v) == 18:
                x.update(font_version=v[15], font_height=v[16], font_fixed_width=v[17])
            cur["X"].append(x)
            continue
        extra.append(ln)
    return readings, extra


def ms(u):
    return round(u * UNIT_MS, 2)


def breakdown(r):
    S = r["S"]
    t = lambda i: S.get(i, (0, 0))[1]
    c = lambda i: S.get(i, (0, 0))[0]
    flush_in = sum(f[4] for f in r["F"] if f[5] in WRAP)
    flush_out = sum(f[4] for f in r["F"] if f[5] not in WRAP)
    ring_complete = c(0) <= 256
    driver = sum(t(i) for i in WRAP)
    out = {
        "wall_ms": ms(r["wall"]),
        "driver_calls_ms": ms(driver),
        "render_ms": ms(driver - flush_in) if ring_complete else None,
        "app_gdi_ms": ms(r["wall"] - driver - flush_out) if ring_complete else None,
        "flush_ms": ms(t(0)), "flushes": c(0),
        "present_ms": ms(t(1)),
        "verify_ms": ms(t(2)),
        "convert_ms": ms(t(4)), "cells": c(4),
        "write_loop_ms": ms(t(3) - t(4)), "writes": c(14),
        "cursor_etc_ms": ms(t(0) - t(1)),
        "verified": c(13),
        "hints_ms": ms(t(11)), "hint_calls": c(11), "hintmove_ms": ms(t(12)),
        "snapshot_ms": ms(t(15)), "snapshots": c(15), "compare_ms": ms(t(16)), "compares": c(16),
        "diffflush_ms": ms(t(17)), "diffflushes": c(17),
        "calls": {SLOTS[i]: [c(i), ms(t(i))] for i in WRAP if c(i)},
        "flush_rects": [{"rows": [f[0], f[1]], "bytes": [f[2], f[3]], "ms": ms(f[4]),
                         "from": SLOTS.get(f[5], "none")} for f in r["F"]],
        "ring_complete": ring_complete,
        "text_calls": r.get("X", []),
    }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log")
    ap.add_argument("--json")
    a = ap.parse_args()
    readings, extra = parse(a.log)
    rep = {"readings": [], "lines": [l for l in extra if l and not l.startswith(" ")]}
    chars, lines = [], []
    for r in readings:
        b = breakdown(r)
        b["label"] = r["label"]
        rep["readings"].append(b)
        if r["label"].startswith("CHAR"):
            chars.append(b)
        if r["label"].startswith("LINE"):
            lines.append(b)
    keys = ("wall_ms", "app_gdi_ms", "render_ms", "flush_ms", "verify_ms", "convert_ms", "write_loop_ms",
            "cursor_etc_ms", "hints_ms", "compare_ms")

    def average(group, name, title):
        avg = {k: round(sum(c[k] or 0 for c in group) / len(group), 1) for k in keys}
        avg.update({k: round(sum(c[k] for c in group) / len(group), 1)
                    for k in ("flushes", "cells", "writes", "verified")})
        rep[name] = avg
        print(title, len(group))
        for k, v in avg.items():
            print(f"  {k:14s} {v}")
    if chars:
        average(chars, "type_average_per_char", "TYPE: average per character over")
    if lines:
        # the TPROF window shows about 12 lines: later Returns scroll
        average(lines[16:] or lines, "lines_average_per_scrolling_line",
                "LINES: average per line once the edit control scrolls, over")
    for b in rep["readings"]:
        if not b["label"].startswith(("CHAR", "LINE")):
            print(b["label"], {k: v for k, v in b.items() if k not in ("flush_rects", "text_calls")})
    for l in rep["lines"]:
        print(l)
    if a.json:
        open(a.json, "w").write(json.dumps(rep, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
