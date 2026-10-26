#!/usr/bin/env python3
"""Summarise an RRBENCH run: timings from RRBENCH.LOG and the Output calls
in each TRnn.BIN (written only under a test-only RRTRACE driver).

  python3 src/rrect/RRTRACE.PY <RRRUN out dir> [--json <file>]

Styles: 4 OS_SCANLINES, 18 OS_POLYLINE (others printed by number).
'bounded' calls refresh only their rows; the rest run the full-screen
FlushShadow. Prints one block per stage.
"""
import argparse
import collections
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("rrpatch", str(HERE / "RRPATCH.PY")).load_module()
STYLE = {4: "SCANLINES", 18: "POLYLINE", 20: "POLYGON", 22: "RECTANGLE"}


def stages(log_text):
    out, cur = [], None
    for line in log_text.replace("\r", "").split("\n"):
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k == "STAGE":
            cur = {"stage": int(v), "repaint_ms": []}
            out.append(cur)
        elif cur is not None:
            if k == "REPAINT_MS":
                cur["repaint_ms"].append(int(v))
            elif k == "NAME":
                cur[k.lower()] = v
            else:
                try:
                    cur[k.lower()] = int(v)
                except ValueError:
                    cur[k.lower()] = v
    return out


def summarise(records):
    by = collections.Counter()
    counts = collections.Counter()
    rows = 0
    for r in records:
        key = (STYLE.get(r["style"], str(r["style"])), "bounded" if r["bounded"] else
               ("FULL" if r["screen"] else "memory"))
        by[key] += 1
        counts[(key[0], r["count"])] += 1
        if r["style"] == 18 and r["walked"]:
            rows += r["y"][1] - r["y"][0] + 1
    return {"calls": len(records),
            "by_style_and_refresh": {f"{a}/{b}": n for (a, b), n in sorted(by.items())},
            "count_histogram": {f"{a}:{c}": n for (a, c), n in sorted(counts.items())},
            "rop2": dict(collections.Counter(r["rop2"] for r in records)),
            "pen_style": dict(collections.Counter(r["pen_style"] for r in records)),
            "brush40": dict(collections.Counter(r["brush40"] for r in records))}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    st = stages((a.run / "RRBENCH.LOG").read_text(errors="replace"))
    report = []
    for s in st:
        tr = a.run / f"TR{s['stage']:02d}.BIN"
        if tr.exists():
            s["trace"] = summarise(P.decode_records(tr.read_bytes()))
        report.append(s)
        print(f"== {s['stage']:2d} {s.get('name')}: {s.get('elapsed_ms', s.get('repaint_ms'))} ms, "
              f"count {s.get('count')}")
        if "trace" in s:
            t = s["trace"]
            print(f"   calls {t['calls']} (lost {s.get('trace_lost')}): {t['by_style_and_refresh']}")
            print(f"   counts: {t['count_histogram']}")
    if a.json:
        a.json.write_text(json.dumps(report, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
