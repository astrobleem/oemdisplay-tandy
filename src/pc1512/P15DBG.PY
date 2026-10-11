#!/usr/bin/env python3
"""Diagnostic PC1512 driver build: cursor-call counters shown on screen.

NOT a driver to use. It answers one question from the 86Box session
(docs/PC1512.MD, "Pointer landing"): where does Windows tell the display
driver to put the cursor, and does the driver draw it there?

  python3 src/pc1512/P15DBG.PY build --repo <view> --dosbox <dosbox-x> --out <fresh> [--defer]
  python3 src/pc1512/P15DBG.PY read <decoded 640x200 frame.png> ...

build: BUILD15.PY exactly, plus these TCURSOR additions after P15PATCH:
  counters (bytes, wrap at 256): 0 SetCursor calls, 1 SetCursor refused
  busy, 2 refused invalid, 3 null shape, 4 MoveCursor calls, 5 MoveCursor
  deferred, 6 CheckCursor calls, 7 CheckCursor redraws, 8 tc_draw calls,
  9 not enabled, 10 no shape, 11/12 clipped away, 13 drawn; then words
  tc_x, tc_y, depth/have bytes, origin x/y; then a ring of the last 16
  MoveCursor (x, y) arguments and its write index.
  Every cursor write-back (tc_put) copies those 90 bytes into the blue
  plane at B800:0000 (screen row 0, x 0-639) and B800:0050 (row 2,
  x 0-79), so any 86Box screenshot carries them.
  --defer: MoveCursor only records the position and never draws at
  interrupt time (CheckCursor or the next cursor_show draws it).
read: prints the counters and the MoveCursor ring, oldest first.

The result is OUT/P15DBG.DRV with OUT/P15DBG.JSN; OUT/PC1512.DRV is
removed so the diagnostic build cannot be mistaken for the driver.
"""
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def instrument(t, defer=False):
    def rep(old, new):
        nonlocal t
        if t.count(old) != 1:
            raise SystemExit("P15DBG: anchor not found exactly once: " + old.splitlines()[0])
        t = t.replace(old, new)
    rep("    tc_plane_size   dw 0\r\n",
        "    tc_plane_size   dw 0\r\n    dbg_c           db 24 dup (0)\r\n"
        "    dbg_ring        dw 32 dup (0)\r\n    dbg_idx         dw 0\r\n")
    rep("    shl bl,1\r\n    cmp bl,10h\r\n    jb tcp_plane\r\n    mov dx,3ddh\r\n    mov al,0fh\r\n",
        "    shl bl,1\r\n    cmp bl,10h\r\n    jb tcp_plane\r\n    mov dx,3ddh\r\n    mov al,1\r\n    out dx,al\r\n"
        "    mov ax,tc_x\r\n    mov word ptr dbg_c[14],ax\r\n    mov ax,tc_y\r\n    mov word ptr dbg_c[16],ax\r\n"
        "    mov ax,tc_depth\r\n    mov dbg_c[18],al\r\n    mov al,tc_have\r\n    mov dbg_c[19],al\r\n"
        "    mov ax,tc_origin_x\r\n    mov word ptr dbg_c[20],ax\r\n"
        "    mov ax,tc_origin_y\r\n    mov word ptr dbg_c[22],ax\r\n"
        "    mov si,offset dbg_c\r\n    xor di,di\r\n    mov cx,90\r\n    cld\r\n    rep movsb\r\n"
        "    mov dx,3ddh\r\n    mov al,0fh\r\n")
    rep("    pushf\r\n    cli\r\n    cmp tc_busy,0\r\n    je tcset_acquire\r\n",
        "    pushf\r\n    cli\r\n    inc dbg_c[0]\r\n    cmp tc_busy,0\r\n    je tcset_acquire\r\n")
    rep("tcset_busy:\r\n    popf\r\n", "tcset_busy:\r\n    inc dbg_c[1]\r\n    popf\r\n")
    rep("tcset_invalid:\r\n", "tcset_invalid:\r\n    inc dbg_c[2]\r\n")
    rep("    jnz tcset_nonnull\r\n    jmp tcset_finish\r\n",
        "    jnz tcset_nonnull\r\n    inc dbg_c[3]\r\n    jmp tcset_finish\r\n")
    rep("    mov tc_pending,1\r\n    cmp tc_depth,0\r\n    jne tcm_defer\r\n",
        "    mov tc_pending,1\r\n    inc dbg_c[4]\r\n    push bx\r\n    mov bx,dbg_idx\r\n"
        "    mov ax,tc_x\r\n    mov dbg_ring[bx],ax\r\n    mov ax,tc_y\r\n    mov dbg_ring[bx+2],ax\r\n"
        "    add bx,4\r\n    and bx,63\r\n    mov dbg_idx,bx\r\n    pop bx\r\n"
        + ("    jmp tcm_defer\r\n" if defer else "")
        + "    cmp tc_depth,0\r\n    jne tcm_defer\r\n")
    rep("tcm_defer:\r\n    popf\r\n", "tcm_defer:\r\n    inc dbg_c[5]\r\n    popf\r\n")
    rep("cProc CheckCursor,<FAR,PUBLIC,WIN,PASCAL>,<si,di>\r\ncBegin\r\n    pushf\r\n    cli\r\n",
        "cProc CheckCursor,<FAR,PUBLIC,WIN,PASCAL>,<si,di>\r\ncBegin\r\n    pushf\r\n    cli\r\n    inc dbg_c[6]\r\n")
    rep("tcc_refresh:\r\n", "tcc_refresh:\r\n    inc dbg_c[7]\r\n")
    rep("tc_draw proc near\r\n    cmp enabled_flag,0\r\n    jne tcd_enabled\r\n    ret\r\n",
        "tc_draw proc near\r\n    inc dbg_c[8]\r\n    cmp enabled_flag,0\r\n    jne tcd_enabled\r\n"
        "    inc dbg_c[9]\r\n    ret\r\n")
    rep("    cmp tc_have,0\r\n    jne tcd_have\r\n    ret\r\n",
        "    cmp tc_have,0\r\n    jne tcd_have\r\n    inc dbg_c[10]\r\n    ret\r\n")
    rep("    jl tcd_width_ok\r\n    ret\r\n", "    jl tcd_width_ok\r\n    inc dbg_c[11]\r\n    ret\r\n")
    rep("    jl tcd_visible\r\n    ret\r\n", "    jl tcd_visible\r\n    inc dbg_c[12]\r\n    ret\r\n")
    rep("    mov si,offset tc_work     ; P15PATCH: write the composite\r\n",
        "    inc dbg_c[13]\r\n    mov si,offset tc_work     ; P15PATCH: write the composite\r\n")
    return t


NAMES = ("set_cursor", "set_refused_busy", "set_refused_invalid", "set_null", "move_cursor",
         "move_deferred", "check_cursor", "check_redraw", "draw_calls", "draw_not_enabled",
         "draw_no_shape", "draw_clipped_x", "draw_clipped_y", "drawn")


def read(path):
    from PIL import Image
    with Image.open(path) as im:
        if im.size != (640, 200):
            raise SystemExit("P15DBG: expects a decoded 640x200 frame (SHOTDEC)")
        f = im.tobytes()

    def byte(o):
        y, x = (0, o * 8) if o < 80 else (2, (o - 80) * 8)
        return sum((f[y * 640 + x + b] & 1) << (7 - b) for b in range(8))
    v = [byte(o) for o in range(90)]
    w = lambda k: v[k] | v[k + 1] << 8
    ring = [(w(24 + 4 * i), w(26 + 4 * i)) for i in range(16)]
    start = w(88) // 4
    return {"counters": dict(zip(NAMES, v[:14])),
            "tc_x": w(14), "tc_y": w(16), "depth": v[18], "have_shape": v[19],
            "move_cursor_ring_oldest_first": [list(ring[(start + i) % 16]) for i in range(16)]}


def build(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--dosbox", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--defer", action="store_true")
    a = ap.parse_args(argv)
    b15 = importlib.machinery.SourceFileLoader("build15_dbg", str(HERE / "BUILD15.PY")).load_module()
    original = b15.P15.patch_tcursor
    b15.P15.patch_tcursor = lambda t: instrument(original(t), a.defer)
    sys.argv = ["BUILD15.PY", "--repo", a.repo, "--dosbox", a.dosbox, "--out", a.out]
    rc = b15.main()
    out = Path(a.out)
    drv = out / "PC1512.DRV"
    data = drv.read_bytes()
    drv.rename(out / "P15DBG.DRV")
    import hashlib
    (out / "P15DBG.JSN").write_text(json.dumps({
        "driver": "P15DBG.DRV", "purpose": "diagnostic only; never install as a display driver",
        "defer_interrupt_draw": a.defer, "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest()}, indent=1) + "\n")
    print("P15DBG:", hashlib.sha256(data).hexdigest())
    return rc


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "build":
        return build(sys.argv[2:])
    if len(sys.argv) >= 3 and sys.argv[1] == "read":
        for p in sys.argv[2:]:
            print(Path(p).name, json.dumps(read(p)))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
