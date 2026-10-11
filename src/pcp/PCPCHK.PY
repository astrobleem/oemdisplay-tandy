#!/usr/bin/env python3
"""Judge a PCPWIN.PY session from its exact frames and the guest disk.

  python3 src/pcp/PCPCHK.PY --vm <vm dir> [--json <out>]

Every check compares exact 320x200 IRGB frames (SHOTDEC) or files read back
from the guest disk with mtools after Windows has exited. Exit 0 only if
every check passes. The 86Box VM must be stopped (the disk is read).
"""
import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import importlib.machinery  # noqa: E402

W = importlib.machinery.SourceFileLoader("pcpwin", str(HERE / "PCPWIN.PY")).load_module()
PAL = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
       (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
       (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
       (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
CANVAS = (37, 49, 290, 170)     # x0, y0, x1, y1 inclusive, inside the drawing area
PARKED = lambda x, y: x >= 316 and y >= 196   # where the parked cursor can show


class Frames:
    def __init__(self, d):
        self.d = Path(d)

    def __getitem__(self, name):
        return Image.open(self.d / (name + ".png")).tobytes()


def diff(a, b, skip=PARKED):
    return [i for i in range(64000) if a[i] != b[i] and not skip(i % 320, i // 320)]


def bbox(idx):
    if not idx:
        return None
    xs = [i % 320 for i in idx]
    ys = [i // 320 for i in idx]
    return [min(xs), min(ys), max(xs), max(ys)]


def mt(img, *args):
    env = dict(os.environ, MTOOLS_SKIP_CHECK="1")
    return subprocess.run(["mtype", "-i", f"{img}@@8704", *args], env=env,
                          capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", required=True)
    ap.add_argument("--json")
    args = ap.parse_args()
    vm = Path(args.vm)
    F = Frames(vm / "dec")
    res = []

    def check(name, ok, **detail):
        res.append(dict(check=name, result="PASS" if ok else "FAIL", **detail))

    # 1. PCPSHOW bars, before Windows: 16 bars of 20 pixels, colours 0..15.
    f = F["bars"]
    bad = [i for i in range(64000) if f[i] != (i % 320) // 20]
    check("pcpshow_16_bars", not bad, mismatches=len(bad), first=bbox(bad[:1]))

    # 2. Menus and dialogs restore the desktop exactly.
    d1 = F["s1_desktop"]
    for opened, closed in (("menu_file_kbd", "menu_closed"), ("about", "about_closed"),
                           ("menu_file_mouse", "menu_mouse_closed")):
        shown = bbox(diff(F[opened], d1))
        left = diff(F[closed], d1)
        check(f"{opened}_restores", shown is not None and not left,
              opened_changed=shown, left_after_close=len(left), where=bbox(left))

    # 3. Overlapping windows, moved by mouse, then closed: desktop exact.
    # Calculator (176 pixels wide at x=0) dragged +60,+40: its frame must now
    # reach past x=176 and below y=165.
    moved = bbox(diff(F["calc_moved"], F["calc_over_pm_notepad"]))
    check("calc_dragged_by_mouse", moved is not None and moved[2] > 200 and moved[3] > 170, changed=moved)
    left = diff(F["overlap_closed"], d1)
    check("overlap_closed_restores", not left, left_after_close=len(left), where=bbox(left))

    # 4. Paintbrush boxes. Paintbrush fills from the press point up to, but
    #    not including, the release point: box c covers x0..x1-1, y0..y1-1.
    f = F["pb_drawn"]
    def inbox(x, y, c):
        x0, y0, x1, y1 = W.rect(c)
        return x0 <= x < x1 and y0 <= y < y1
    for c in range(16):
        x0, y0, x1, y1 = W.rect(c)
        px = [f[y * 320 + x] for y in range(y0, y1) for x in range(x0, x1)]
        wrong = sum(1 for v in px if v != c)
        check(f"box_{c:02d}_colour", wrong == 0, pixels=len(px), wrong=wrong)
    empty = F["pb_empty"]
    outside = [i for i in diff(f, empty)
               if not any(inbox(i % 320, i // 320, c) for c in range(16))
               and CANVAS[0] <= i % 320 <= CANVAS[2] and CANVAS[1] <= i // 320 <= CANVAS[3]]
    check("canvas_outside_boxes_untouched", not outside, changed=len(outside), where=bbox(outside))

    # 5. Arrow cursor over each palette colour: opaque black/white glyph,
    #    identical everywhere, background untouched, exact restore.
    ref = F["arrow_parked"]
    glyph = {}
    conflict = 0
    frames = {}
    for c in range(16):
        r, k = W.PALETTE[c]
        hx, hy = W.PAL_X0 + W.PAL_PITCH * k, W.PAL_Y[r]
        fr = F[f"arrow_{c:02d}"]
        frames[c] = (hx, hy, fr)
        for i in diff(fr, ref):
            off = (i % 320 - hx, i // 320 - hy)
            if off in glyph and glyph[off] != fr[i]:
                conflict += 1
            glyph[off] = fr[i]
    span = [min(o[0] for o in glyph), min(o[1] for o in glyph), max(o[0] for o in glyph), max(o[1] for o in glyph)] if glyph else None
    colours = sorted(set(glyph.values()))
    check("arrow_glyph_consistent", conflict == 0 and colours and set(colours) <= {0, 15}
          and span[0] >= 0 and span[1] >= 0 and span[2] < 16 and span[3] < 16,
          glyph_pixels=len(glyph), colours=colours, offsets_span=span, conflicts=conflict)
    for c, (hx, hy, fr) in frames.items():
        exp = bytearray(ref)
        for (dx, dy), v in glyph.items():
            x, y = hx + dx, hy + dy
            if 0 <= x < 320 and 0 <= y < 200:
                exp[y * 320 + x] = v
        wrong = diff(fr, bytes(exp))
        check(f"arrow_over_colour_{c:02d}", not wrong, hotspot=[hx, hy], wrong=len(wrong), where=bbox(wrong))
    left = diff(ref, F["pb_drawn"])
    check("arrow_moves_restore_exactly", not left, left=len(left), where=bbox(left))

    # 6. Tool cursor over each box: every changed pixel is the box colour
    #    XOR 15 (inverted), and nothing outside the cursor changes.
    cref = F["cross_parked"]
    for c in range(16):
        x0, y0, x1, y1 = W.rect(c)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        fr = F[f"cross_{c:02d}"]
        ch = diff(fr, cref)
        notxor = [i for i in ch if fr[i] != cref[i] ^ 15]
        far = [i for i in ch if abs(i % 320 - cx) > 16 or abs(i // 320 - cy) > 16]
        check(f"cursor_xor_over_colour_{c:02d}", ch and not notxor and not far,
              changed=len(ch), not_inverted=len(notxor), outside_cursor=len(far), box=bbox(ch))
    left = diff(cref, F["pb_drawn"])
    check("cross_moves_restore_exactly", not left, left=len(left), where=bbox(left))

    # 7. Save, close, reopen: canvas identical; saved BMP equals the screen.
    a, b = F["pb_drawn"], F["pb_reopened"]
    x0, y0, x1, y1 = CANVAS
    cdiff = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if a[y * 320 + x] != b[y * 320 + x]]
    check("reopened_canvas_identical", not cdiff, differing=len(cdiff), first=cdiff[:1])
    # The BMP stores the driver's colour-table indexes (the DDK table this
    # driver inherits: bit 0 red, 1 green, 2 blue, 3 intensity); its IRGB
    # screen colour is I<<3 | R<<2 | G<<1 | B. Every visible canvas pixel
    # must equal its BMP pixel through that mapping.
    data = mt(vm / "pcp.img", "::/WINDOWS/TEST16.BMP")
    if data[:2] == b"BM":
        bmp = Image.open(io.BytesIO(data))
        idx = bmp.load()
        irgb = lambda v: ((v >> 3) & 1) << 3 | (v & 1) << 2 | ((v >> 1) & 1) << 1 | ((v >> 2) & 1)
        found = None
        for ox in range(20, 60):
            for oy in range(30, 70):
                bad = 0
                for y in range(y0, y1 + 1, 2):
                    for x in range(x0, x1 + 1, 2):
                        bx, by = x - ox, y - oy
                        if not (0 <= bx < bmp.width and 0 <= by < bmp.height) or irgb(idx[bx, by]) != a[y * 320 + x]:
                            bad += 1
                            break
                    if bad:
                        break
                if not bad:
                    found = (ox, oy)
                    break
            if found:
                break
        full = None
        if found:
            ox, oy = found
            full = sum(1 for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
                       if irgb(idx[x - ox, y - oy]) != a[y * 320 + x])
        counts = sorted(c for c, _ in bmp.getcolors())
        check("saved_bmp_matches_screen", found is not None and full == 0,
              bmp_size=[bmp.width, bmp.height], bmp_mode=bmp.mode, image_origin_on_screen=found,
              canvas_pixels_compared=(x1 - x0 + 1) * (y1 - y0 + 1), mismatches=full,
              palette=[tuple(bmp.getpalette()[i:i + 3]) for i in range(0, 48, 3)])
    else:
        check("saved_bmp_matches_screen", False, error="TEST16.BMP not found or not a BMP")

    # 8. Exit to DOS and second launch.
    txt = mt(vm / "pcp.img", "::/WINDOWS/PCPID.TXT").decode(errors="replace").split()
    lines = [t for t in mt(vm / "pcp.img", "::/WINDOWS/PCPID.TXT").decode(errors="replace").splitlines() if t.strip()]
    check("pcpid_after_each_exit", len(lines) == 2 and all(
        "MODE_BEFORE=03" in l and "COLS=0050" in l and "COLORPLUS=01" in l for l in lines), lines=lines)
    boot = [t for t in mt(vm / "pcp.img", "::/PCP/PCPID.TXT").decode(errors="replace").splitlines() if t.strip()]
    check("pcpid_at_boot_sees_colorplus", bool(boot) and all("COLORPLUS=01" in l for l in boot), lines=boot)
    left = diff(F["s2_desktop"], d1)
    check("second_launch_desktop_identical", not left, differing=len(left), where=bbox(left))

    out = {"vm": str(vm), "checks": res,
           "passed": sum(r["result"] == "PASS" for r in res), "total": len(res)}
    out["verdict"] = "PASS" if out["passed"] == out["total"] else "FAIL"
    text = json.dumps(out, indent=1)
    if args.json:
        Path(args.json).write_text(text + "\n")
    print(text)
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
