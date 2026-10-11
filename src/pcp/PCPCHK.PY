#!/usr/bin/env python3
"""Judge a PCPWIN.PY session from its exact frames and the guest disk.

  python3 src/pcp/PCPCHK.PY --vm <vm dir> [--json <out>]

Every check compares exact 320x200 IRGB frames (SHOTDEC) or files read back
from the guest disk with mtools after Windows has exited. Exit 0 only if no
check fails; the verdict is PASS only if none was skipped either. The 86Box
VM must be stopped (the disk is read). --no-disk judges the frames alone
(PCPMUT.PY uses it on the committed frames).
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
WD = 320                        # frame width; main() sets it (320 or 640)
PARKED = lambda x, y: x >= WD - 4 and y >= 196   # where the parked cursor can show
TARGETS = {"pcp": ("PCP", "PCPID", "COLORPLUS=01"), "pc1512": ("P15", "P15ID", "PC1512=01")}


def cursor_oracle(path):
    """Expected on-screen glyph of a 32x32 monochrome .CUR on a 200-line
    display: Windows halves the cursor height by ANDing scanline pairs in
    both masks (AND = AND(2k) & AND(2k+1), XOR likewise). Returns
    {(dx, dy): colour} for opaque pixels relative to the hotspot (dy halved),
    colour 0 for AND=0/XOR=0 and 15 for AND=0/XOR=1, plus the file hash."""
    import hashlib
    import struct
    d = Path(path).read_bytes()
    hx, hy = struct.unpack_from("<HH", d, 10)
    off = struct.unpack_from("<I", d, 18)[0]
    w, h = struct.unpack_from("<ii", d, off + 4)
    if (w, h) != (32, 64) or struct.unpack_from("<H", d, off + 14)[0] != 1:
        raise SystemExit("PCPCHK: expected a 32x32 monochrome cursor")
    xor = d[off + 48:off + 176]
    andm = d[off + 176:off + 304]

    def bit(mask, x, y):
        r = 31 - y
        return (mask[r * 4 + x // 8] >> (7 - x % 8)) & 1
    out = {}
    for k in range(16):
        for x in range(32):
            a = bit(andm, x, 2 * k) & bit(andm, x, 2 * k + 1)
            v = bit(xor, x, 2 * k) & bit(xor, x, 2 * k + 1)
            if a == 0:
                out[(x - hx, k - hy // 2)] = 15 if v else 0
    return out, hashlib.sha256(d).hexdigest()


class Frames:
    def __init__(self, d):
        self.d = Path(d)

    def __getitem__(self, name):
        return Image.open(self.d / (name + ".png")).tobytes()


def diff(a, b, skip=PARKED):
    return [i for i in range(WD * 200) if a[i] != b[i] and not skip(i % WD, i // WD)]


def bbox(idx):
    if not idx:
        return None
    xs = [i % WD for i in idx]
    ys = [i // WD for i in idx]
    return [min(xs), min(ys), max(xs), max(ys)]


def mt(img, *args):
    env = dict(os.environ, MTOOLS_SKIP_CHECK="1")
    return subprocess.run(["mtype", "-i", f"{img}@@8704", *args], env=env,
                          capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", required=True)
    ap.add_argument("--json")
    ap.add_argument("--no-disk", action="store_true",
                    help="judge frames only; disk-based checks are reported SKIPPED (for mutation tests)")
    ap.add_argument("--width", type=int, default=320, choices=sorted(W.LAYOUTS))
    ap.add_argument("--target", default="pcp", choices=sorted(TARGETS))
    ap.add_argument("--cursor", help="driver arrow resource NORMAL.CUR from the pinned DDK build "
                                     "(BUILD88 resources); without it the oracle check is SKIPPED")
    args = ap.parse_args()
    global WD
    WD = args.width
    W.use_width(WD)
    tdir, tid, tok = TARGETS[args.target]
    vm = Path(args.vm)
    F = Frames(vm / "dec")
    res = []

    def check(name, ok, **detail):
        res.append(dict(check=name, result="PASS" if ok else "FAIL", **detail))

    def skipped(name, reason="--no-disk"):
        res.append(dict(check=name, result="SKIPPED", reason=reason))

    # 1. PCPSHOW bars, before Windows: 16 bars of 20 pixels, colours 0..15.
    f = F["bars"]
    bad = [i for i in range(WD * 200) if f[i] != (i % WD) // (WD // 16)]
    check("pcpshow_16_bars", not bad, mismatches=len(bad), first=bbox(bad[:1]))

    # 2. Menus and dialogs restore the desktop exactly.
    d1 = F["s1_desktop"]
    for opened, closed in (("menu_file_kbd", "menu_closed"), ("about", "about_closed"),
                           ("menu_file_mouse", "menu_mouse_closed")):
        opened_px = diff(F[opened], d1)
        left = diff(F[closed], d1)
        # A menu or dialog repaints thousands of pixels; require >= 1000 so a
        # frame that merely moved the cursor cannot count as "opened".
        check(f"{opened}_restores", len(opened_px) >= 1000 and not left,
              opened_changed=len(opened_px), opened_box=bbox(opened_px),
              left_after_close=len(left), where=bbox(left))

    # 2b. Wallpaper, arrow over every bar, mouse drift, restore.
    bar = WD // 16
    expected_bars = bytes((i % WD) // bar for i in range(WD * 200))
    icon = lambda x, y: x < W.ICON[0] and y >= W.ICON[1]   # minimized Program Manager
    wall = F["wall_parked"]
    off = [i for i in diff(wall, expected_bars) if not icon(i % WD, i // WD)]
    check("wallpaper_bars_exact", not off, differing_outside_icon=len(off), where=bbox(off),
          icon_area_changed=len(diff(wall, expected_bars)) - len(off))
    glyph, conflict, per_frame = {}, 0, {}
    for c in range(16):
        hx, hy = c * bar + bar // 2, 100
        fr = F[f"warrow_{c:02d}"]
        ch = diff(fr, wall)
        per_frame[c] = len(ch)
        for i in ch:
            o = (i % WD - hx, i // WD - hy)
            if o in glyph and glyph[o] != fr[i]:
                conflict += 1
            glyph[o] = fr[i]
    xs = [o[0] for o in glyph] or [0]
    ys = [o[1] for o in glyph] or [0]
    black = sum(1 for v in glyph.values() if v == 0)
    white = sum(1 for v in glyph.values() if v == 15)
    # The driver's arrow resource is 12x20 (NORMAL.CUR), shown at half height
    # on 200 lines: require that full span and at least 60 opaque pixels.
    size_ok = (len(glyph) >= 60 and max(xs) - min(xs) + 1 >= 12 and max(ys) - min(ys) + 1 >= 10
               and black >= 20 and white >= 20 and black + white == len(glyph)
               and min(xs) >= 0 and min(ys) >= 0 and max(xs) < 32 and max(ys) < 32)
    check("arrow_full_glyph_over_bars", size_ok and conflict == 0 and min(per_frame.values()) >= 20,
          glyph_pixels=len(glyph), black=black, white=white,
          span=[min(xs), min(ys), max(xs), max(ys)], conflicts=conflict,
          fewest_changed_in_a_frame=min(per_frame.values()))
    # Independent oracle: the driver's own arrow resource (NORMAL.CUR from
    # the pinned DDK resources), halved as Windows does on 200 lines.
    if args.cursor:
        expect, cur_sha = cursor_oracle(args.cursor)
        missing = [o for o in expect if glyph.get(o) != expect[o]]
        extra = [o for o in glyph if o not in expect]
        check("arrow_equals_driver_cursor_resource", not missing and not extra,
              resource_sha256=cur_sha, expected_pixels=len(expect), drawn_pixels=len(glyph),
              missing_or_wrong=len(missing), extra=len(extra))
    else:
        skipped("arrow_equals_driver_cursor_resource", "no --cursor resource given")

    def composite(base, hx, hy):
        exp = bytearray(base)
        for (dx, dy), v in glyph.items():
            x, y = hx + dx, hy + dy
            if 0 <= x < WD and 0 <= y < 200:
                exp[y * WD + x] = v
        return bytes(exp)

    for c in range(16):
        hx = c * bar + bar // 2
        wrong = diff(F[f"warrow_{c:02d}"], composite(wall, hx, 100))
        check(f"arrow_over_bar_{c:02d}", not wrong and per_frame[c] >= 20,
              hotspot=[hx, 100], changed=per_frame[c], wrong=len(wrong), where=bbox(wrong))
    drift = json.loads((vm / "DRIFT.JSN").read_text())
    for t in drift:
        hx, hy = t["expected_hotspot"]
        wrong = diff(F[t["frame"]], composite(wall, hx, hy))
        check("mouse_drift_" + t["frame"], not wrong,
              trial=t["trial"], expected_hotspot=[hx, hy], wrong=len(wrong), where=bbox(wrong))
    left = diff(F["pm_restored"], d1)
    check("program_manager_restored_exactly", not left, differing=len(left), where=bbox(left))

    # 3. Overlapping windows, moved by mouse, then closed: desktop exact.
    # Calculator opens at (0,0) and is dragged +60,+40. Its title bar
    # (rows 1-9, x 2-170 of the window) must appear exactly at the new
    # position and no longer at the old one.
    before, after = F["calc_over_pm_notepad"], F["calc_moved"]
    tx0, ty0, tx1, ty1 = W.CALC_TPL
    CX, CY = W.CALC_DRAG
    tpl = [(x, y, before[y * WD + x]) for y in range(ty0, ty1 + 1) for x in range(tx0, tx1 + 1)]
    # The pointer is left on the moved title bar at the release point; leave
    # out exactly its pixels (the arrow glyph verified above).
    px, py = W.CALC_TITLE[0] + CX, W.CALC_TITLE[1] + CY
    pointer = {(px + dx, py + dy) for (dx, dy) in glyph}
    tpl_new = [(x, y, v) for x, y, v in tpl if (x + CX, y + CY) not in pointer]
    at_new = sum(1 for x, y, v in tpl_new if after[(y + CY) * WD + x + CX] != v)
    at_old = sum(1 for x, y, v in tpl if after[y * WD + x] != v)
    check("calc_dragged_by_mouse", at_new == 0 and len(tpl_new) > len(tpl) * 9 // 10 and at_old > len(tpl) // 4,
          title_pixels=len(tpl), compared_at_new=len(tpl_new), pointer_pixels_excluded=len(tpl) - len(tpl_new),
          mismatches_at_new_position=at_new, mismatches_at_old_position=at_old)
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
        px = [f[y * WD + x] for y in range(y0, y1) for x in range(x0, x1)]
        wrong = sum(1 for v in px if v != c)
        check(f"box_{c:02d}_colour", wrong == 0, pixels=len(px), wrong=wrong)
    empty = F["pb_empty"]
    outside = [i for i in diff(f, empty)
               if not any(inbox(i % WD, i // WD, c) for c in range(16))
               and W.CANVAS[0] <= i % WD <= W.CANVAS[2] and W.CANVAS[1] <= i // WD <= W.CANVAS[3]]
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
            off = (i % WD - hx, i // WD - hy)
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
            if 0 <= x < WD and 0 <= y < 200:
                exp[y * WD + x] = v
        wrong = diff(fr, bytes(exp))
        check(f"arrow_over_colour_{c:02d}", not wrong, hotspot=[hx, hy], wrong=len(wrong), where=bbox(wrong))
    left = diff(ref, F["pb_drawn"])
    check("arrow_moves_restore_exactly", not left, left=len(left), where=bbox(left))

    # 6. Tool cursor over each box: every changed pixel is the box colour
    #    XOR 15 (inverted), and nothing outside the cursor changes.
    cref = F["cross_parked"]
    shapes = []
    for c in range(16):
        x0, y0, x1, y1 = W.rect(c)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        fr = F[f"cross_{c:02d}"]
        ch = diff(fr, cref)
        notxor = [i for i in ch if fr[i] != cref[i] ^ 15]
        far = [i for i in ch if abs(i % WD - cx) > 16 or abs(i // WD - cy) > 16]
        shape = frozenset((i % WD - cx, i // WD - cy) for i in ch)
        shapes.append(shape)
        check(f"cursor_xor_over_colour_{c:02d}", len(ch) >= 30 and not notxor and not far,
              changed=len(ch), not_inverted=len(notxor), outside_cursor=len(far), box=bbox(ch))
    check("cursor_xor_same_footprint_all_colours", len(set(shapes)) == 1,
          distinct_footprints=len(set(shapes)), pixels=len(shapes[0]) if shapes else 0)
    left = diff(cref, F["pb_drawn"])
    check("cross_moves_restore_exactly", not left, left=len(left), where=bbox(left))

    # 7. Save, close, reopen: canvas identical; saved BMP equals the screen.
    a, b = F["pb_drawn"], F["pb_reopened"]
    x0, y0, x1, y1 = W.CANVAS
    cdiff = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if a[y * WD + x] != b[y * WD + x]]
    check("reopened_canvas_identical", not cdiff, differing=len(cdiff), first=cdiff[:1])
    # The BMP stores the driver's colour-table indexes (the DDK table this
    # driver inherits: bit 0 red, 1 green, 2 blue, 3 intensity); its IRGB
    # screen colour is I<<3 | R<<2 | G<<1 | B. Every visible canvas pixel
    # must equal its BMP pixel through that mapping.
    data = b"" if args.no_disk else mt(vm / "pcp.img", "::/WINDOWS/TEST16.BMP")
    if args.no_disk:
        skipped("saved_bmp_matches_screen")
    elif data[:2] == b"BM":
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
                        if not (0 <= bx < bmp.width and 0 <= by < bmp.height) or irgb(idx[bx, by]) != a[y * WD + x]:
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
                       if irgb(idx[x - ox, y - oy]) != a[y * WD + x])
        counts = sorted(c for c, _ in bmp.getcolors())
        check("saved_bmp_matches_screen", found is not None and full == 0,
              bmp_size=[bmp.width, bmp.height], bmp_mode=bmp.mode, image_origin_on_screen=found,
              canvas_pixels_compared=(x1 - x0 + 1) * (y1 - y0 + 1), mismatches=full,
              palette=[tuple(bmp.getpalette()[i:i + 3]) for i in range(0, 48, 3)])
    else:
        check("saved_bmp_matches_screen", False, error="TEST16.BMP not found or not a BMP")

    # 8. Exit to DOS and second launch.
    if args.no_disk:
        skipped("pcpid_after_each_exit")
        skipped("pcpid_at_boot_sees_card")
    else:
        lines = [t for t in mt(vm / "pcp.img", f"::/WINDOWS/{tid}.TXT").decode(errors="replace").splitlines() if t.strip()]
        check("pcpid_after_each_exit", len(lines) == 2 and all(
            "MODE_BEFORE=03" in l and "COLS=0050" in l and tok in l for l in lines), lines=lines)
        boot = [t for t in mt(vm / "pcp.img", f"::/{tdir}/{tid}.TXT").decode(errors="replace").splitlines() if t.strip()]
        check("pcpid_at_boot_sees_card", bool(boot) and all(tok in l for l in boot), lines=boot)
    left = diff(F["s2_desktop"], d1)
    check("second_launch_desktop_identical", not left, differing=len(left), where=bbox(left))

    out = {"vm": str(vm), "checks": res,
           "passed": sum(r["result"] == "PASS" for r in res),
           "failed": sum(r["result"] == "FAIL" for r in res),
           "skipped": sum(r["result"] == "SKIPPED" for r in res), "total": len(res)}
    out["verdict"] = "PASS" if out["failed"] == 0 and out["skipped"] == 0 else (
        "FRAMES-ONLY PASS" if out["failed"] == 0 else "FAIL")
    text = json.dumps(out, indent=1)
    if args.json:
        Path(args.json).write_text(text + "\n")
    print(text)
    return 0 if out["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
