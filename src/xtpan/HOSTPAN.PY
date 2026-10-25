#!/usr/bin/env python3
"""Host tests for the XTPAN experiment (no emulator, no Windows media).

  python3 src/xtpan/HOSTPAN.PY [--drv <XTPAN.DRV>]

1. FollowTop, compiled from XTPAN.C itself with the host C compiler (the
   function is pure C89 arithmetic), for every viewport top 0..200 and every
   window [wtop, wbot) inside the 400-row desktop: a window that fits must
   end up wholly visible with the smallest possible move (brute force over
   all tops), a taller one must show its top row, and a visible one must not
   move. Named cases include the review case: a 190-row window at rows
   30..220 seen from top 0 needs top 20 (50-row steps gave 50 and then 0).
2. PANCHK's exact pointer check on synthetic frames: the pattern with an
   arrow composited at a hot spot passes; the same frame checked with the
   arrow one pixel off in any direction, with no arrow, or with one mask bit
   flipped fails, as does a frame whose arrow is one pixel off.
3. With --drv: PANCHK.arrow reads the driver's OCR_NORMAL cursor and OEMBIN
   compression (32x16 from 32x32 for the TR5 320x200 drivers).
"""
import argparse
import importlib.machinery
import os
import random
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANCHK = importlib.machinery.SourceFileLoader("panchk", str(HERE / "PANCHK.PY")).load_module()
fails = []


def expect(label, ok):
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        fails.append(label)


HARNESS = r"""
#include <stdio.h>
%s
static int best(int top, int wtop, int wbot)
{
    int t, b = -1;
    for (t = 0; t <= 200; t++)
        if (wtop >= t && wbot <= t + 200 && (b < 0 || abs(t - top) < abs(b - top)))
            b = t;
    return b;
}
int main(int argc, char **argv)
{
    int top, wtop, wbot, bad = 0, n = 0;
    if (argc == 5) {
        printf("%%d\n", FollowTop(atoi(argv[1]), 200, 400, atoi(argv[2]), atoi(argv[3])));
        return 0;
    }
    for (top = 0; top <= 200; top++)
        for (wtop = 0; wtop < 400; wtop++)
            for (wbot = wtop + 1; wbot <= 400; wbot++) {
                int t = FollowTop(top, 200, 400, wtop, wbot), want;
                if (wtop >= top && wbot <= top + 200)
                    want = top;
                else if (wbot - wtop <= 200)
                    want = best(top, wtop, wbot);
                else
                    want = wtop > 200 ? 200 : wtop;
                n++;
                if (t != want) {
                    if (bad < 5)
                        printf("top %%d window %%d..%%d: got %%d want %%d\n", top, wtop, wbot, t, want);
                    bad++;
                }
            }
    printf("cases %%d bad %%d\n", n, bad);
    return bad != 0;
}
"""


def follow_tests(tmp):
    c = (HERE / "XTPAN.C").read_bytes().decode("latin-1").replace("\r\n", "\n")
    m = re.search(r"static int FollowTop\(.*?\n}\n", c, re.S)
    expect("XTPAN.C defines FollowTop", m is not None)
    if not m:
        return
    src = Path(tmp) / "follow.c"
    src.write_text("#include <stdlib.h>\n" + HARNESS % m.group(0))
    exe = Path(tmp) / "follow"
    r = subprocess.run(shlex.split(os.environ.get("CC", "cc")) +
                       ["-std=c89", "-pedantic", "-Wall", "-Werror", "-O1", "-o", str(exe), str(src)],
                       capture_output=True, text=True)
    expect("FollowTop compiles as C89 (-pedantic -Werror)", r.returncode == 0)
    if r.returncode:
        print(r.stderr)
        return

    def ft(top, a, b):
        return int(subprocess.run([str(exe), str(top), str(a), str(b), "x"], capture_output=True,
                                  text=True).stdout)
    expect("review case: 190-row window at 30..220 from top 0 -> top 20 (wholly visible)", ft(0, 30, 220) == 20)
    expect("same window from top 50 -> top 30", ft(50, 30, 220) == 30)
    expect("window already visible: no move", ft(0, 10, 150) == 0)
    expect("275-row dialog at 63..338: its top row is shown (top 63)", ft(0, 63, 338) == 63)
    expect("window hanging off the desktop bottom (380..420): clamped to 200", ft(0, 380, 420) == 200)
    expect("window above the desktop (-10..100) from top 50: clamped to 0", ft(50, -10, 100) == 0)
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    print("     " + r.stdout.strip().replace("\n", "\n     "))
    expect("exhaustive: every top 0..200 x every window in 400 rows -> visible, minimal move",
           r.returncode == 0)


def synthetic_arrow():
    """A 12x10 arrow-like glyph: black outline, white fill, one inverting pixel."""
    g = []
    for dy in range(10):
        for dx in range(12):
            if dx > dy + 1:
                a, x = 1, 0
            elif dx == 0 or dx == dy + 1 or dy == 9:
                a, x = 0, 0
            else:
                a, x = 0, 1
            if (dx, dy) == (1, 8):
                a, x = 1, 1                        # inverts the background
            g.append((dx, dy, a, x))
    return 0, 0, g


def compose(top, off, mapping, cur):
    idx = [mapping[str(PANCHK.colour(x, top + p, off))] for p in range(200) for x in range(320)]
    if cur:
        cx, cy, (hx, hy, glyph) = cur
        for dx, dy, a, x in glyph:
            px, py = cx - hx + dx, cy - hy + dy
            if 0 <= px < 320 and 0 <= py < 200:
                v = idx[py * 320 + px] if a else 0
                idx[py * 320 + px] = v ^ 0x0F if x else v
    return idx


def cursor_tests():
    rnd = random.Random(7)
    irgb = list(range(16))
    rnd.shuffle(irgb)
    mapping = {str(i): irgb[i] for i in range(16)}
    arrow = synthetic_arrow()
    for top, off, cx, cy in ((0, 0, 40, 60), (150, 0, 100, 180), (200, 168, 300, 195), (37, 0, 3, 0)):
        frame = compose(top, off, mapping, (cx, cy, arrow))
        ok = PANCHK.check_idx(frame, top, off, (), mapping, (cx, cy, arrow))["verdict"] == "PASS"
        expect(f"top {top}: exact arrow at ({cx},{cy}) passes", ok)
        bad = {k: PANCHK.check_idx(frame, top, off, (), mapping, c)["verdict"]
               for k, c in (("left", (cx - 1, cy, arrow)), ("right", (cx + 1, cy, arrow)),
                            ("up", (cx, cy - 1, arrow)), ("down", (cx, cy + 1, arrow)), ("none", None))}
        g = list(arrow[2])
        i = next(k for k, t in enumerate(g) if t[2] == 0 and t[3] == 0)
        g[i] = (g[i][0], g[i][1], 1, 0)
        bad["one bit"] = PANCHK.check_idx(frame, top, off, (), mapping, (cx, cy, (0, 0, g)))["verdict"]
        expect(f"top {top}: shifted / missing / one-bit-wrong arrows all fail {bad}",
               all(v == "FAIL" for v in bad.values()))
        moved = compose(top, off, mapping, (cx + 1, cy, arrow))
        expect(f"top {top}: a frame whose arrow is one pixel right fails",
               PANCHK.check_idx(moved, top, off, (), mapping, (cx, cy, arrow))["verdict"] == "FAIL")
    blank = compose(0, 0, mapping, None)
    expect("a frame with no pointer fails the pointer check",
           PANCHK.check_idx(blank, 0, 0, (), mapping, (40, 60, arrow))["verdict"] == "FAIL")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--drv", type=Path)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        follow_tests(tmp)
    cursor_tests()
    if a.drv:
        hx, hy, g = PANCHK.arrow(a.drv.read_bytes())
        w, h = max(t[0] for t in g) + 1, max(t[1] for t in g) + 1
        expect(f"{a.drv.name}: OCR_NORMAL is {w}x{h} after OEMBIN compression, hot spot ({hx},{hy})",
               (w, h, hx, hy) == (32, 16, 0, 0))
    print(f"{len(fails)} failed" if fails else "all passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
