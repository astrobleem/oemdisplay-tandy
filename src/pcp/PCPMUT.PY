#!/usr/bin/env python3
"""Mutation test for PCPCHK.PY: broken sessions must fail.

  python3 src/pcp/PCPMUT.PY --vm <run dir>            (frames in <vm>/dec)
  python3 src/pcp/PCPMUT.PY --evidence docs/pcp       (committed frames)

Builds a frames-only copy of a passing PCPWIN session, checks that PCPCHK
--no-disk passes it, then applies one fault at a time and requires the
targeted checks to FAIL:
  arrow_one_pixel   every wallpaper-arrow frame shows a 1-pixel "cursor"
  arrow_missing     one wallpaper-arrow frame shows no cursor at all
  calc_not_moved    the "dragged" Calculator frame equals the frame before
  drift_short       one drift frame has the arrow 5 px left and 3 px up
  drift_no_cursor   one drift frame has no cursor
  dialog_not_open   the About frame equals the desktop
  restore_off       one pixel differs after the About box closes
  cross_one_pixel   every inverting-cursor frame inverts a single pixel
Exit 0 only if the clean copy passes and every mutation is caught.
"""
import argparse
import importlib.machinery
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SHOTDEC = importlib.machinery.SourceFileLoader("shotdec", str(HERE / "SHOTDEC.PY")).load_module()
W = importlib.machinery.SourceFileLoader("pcpwin", str(HERE / "PCPWIN.PY")).load_module()


def load(d, name):
    return bytearray(Image.open(d / "dec" / (name + ".png")).tobytes())


def save(d, name, frame):
    SHOTDEC.save(bytes(frame), str(d / "dec" / (name + ".png")))


def run_chk(d):
    r = subprocess.run([sys.executable, str(HERE / "PCPCHK.PY"), "--vm", str(d), "--no-disk"],
                       capture_output=True, text=True)
    out = json.loads(r.stdout)
    return {c["check"]: c["result"] for c in out["checks"]}


def arrow_glyph(d):
    """Cursor pixels of warrow_00 relative to its hotspot."""
    wall, f = load(d, "wall_parked"), load(d, "warrow_00")
    hx, hy = 10, 100
    return [(i % 320 - hx, i // 320 - hy, f[i]) for i in range(64000) if f[i] != wall[i]]


def mutations(d):
    bar = 20
    wall = load(d, "wall_parked")
    glyph = arrow_glyph(d)

    def place(hx, hy):
        f = bytearray(wall)
        for dx, dy, v in glyph:
            x, y = hx + dx, hy + dy
            if 0 <= x < 320 and 0 <= y < 200:
                f[y * 320 + x] = v
        return f

    def arrow_one_pixel():
        for c in range(16):
            f = bytearray(wall)
            i = 100 * 320 + c * bar + bar // 2
            f[i] = 15 if f[i] != 15 else 0
            save(d, f"warrow_{c:02d}", f)
        return ["arrow_full_glyph_over_bars"]

    def arrow_missing():
        save(d, "warrow_07", wall)
        return ["arrow_over_bar_07"]

    def calc_not_moved():
        save(d, "calc_moved", load(d, "calc_over_pm_notepad"))
        return ["calc_dragged_by_mouse"]

    def drift_short():
        save(d, "drift_0", place(195, 117))
        return ["mouse_drift_drift_0"]

    def drift_no_cursor():
        save(d, "drift_1", wall)
        return ["mouse_drift_drift_1"]

    def dialog_not_open():
        save(d, "about", load(d, "s1_desktop"))
        return ["about_restores"]

    def restore_off():
        f = load(d, "about_closed")
        f[150 * 320 + 200] ^= 1
        save(d, "about_closed", f)
        return ["about_restores"]

    def cross_one_pixel():
        ref = load(d, "cross_parked")
        for c in range(16):
            x0, y0, x1, y1 = W.rect(c)
            f = bytearray(ref)
            i = ((y0 + y1) // 2) * 320 + (x0 + x1) // 2
            f[i] ^= 15
            save(d, f"cross_{c:02d}", f)
        return ["cursor_xor_over_colour_00"]

    return [arrow_one_pixel, arrow_missing, calc_not_moved, drift_short, drift_no_cursor,
            dialog_not_open, restore_off, cross_one_pixel]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--vm")
    g.add_argument("--evidence")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "clean"
        (base / "dec").mkdir(parents=True)
        if a.vm:
            vm = Path(a.vm)
            for p in (vm / "dec").glob("*.png"):
                shutil.copyfile(p, base / "dec" / p.name)
            shutil.copyfile(vm / "DRIFT.JSN", base / "DRIFT.JSN")
        else:
            ev = Path(a.evidence)
            index = json.loads((ev / "P86RAW.JSN").read_bytes())
            for e in index["frames"]:
                if "repo_file" in e:
                    shutil.copyfile(ev / e["repo_file"], base / "dec" / (e["frame"] + ".png"))
            shutil.copyfile(ev / "P86DRIFT.JSN", base / "DRIFT.JSN")
        clean = run_chk(base)
        bad = sorted(k for k, v in clean.items() if v == "FAIL")
        print(("ok   " if not bad else "FAIL ") + f"clean frames pass ({len(clean)} checks)" + (f": {bad}" if bad else ""))
        fails = 1 if bad else 0
        for m in mutations(base):
            d = Path(tmp) / m.__name__
            shutil.copytree(base, d)
            fn = next(f for f in mutations(d) if f.__name__ == m.__name__)
            targets = fn()
            res = run_chk(d)
            caught = all(res.get(t) == "FAIL" for t in targets)
            print(("ok   " if caught else "FAIL ") + f"{m.__name__}: " +
                  ", ".join(f"{t}={res.get(t)}" for t in targets))
            fails += 0 if caught else 1
    print("PCPMUT: " + ("PASS" if not fails else f"FAIL ({fails})"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
