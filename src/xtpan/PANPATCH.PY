#!/usr/bin/env python3
"""XTPAN edits for the TR5 driver: a 320x400 logical desktop shown through a
320x200 viewport on the Tandy 1000 EX/HX (docs/PAN.MD).

  python3 src/xtpan/PANPATCH.PY --check     text self-test (no emulator)

BUILDPAN.PY applies patch_staged() to BUILD88's fully staged sources for
profile 320x200x16, after every TR5 port step and before the first
assembly. Every edit must match an exact count or nothing is written.

TSOFT.ASM
- SCREEN_HEIGHT 400; shadow 64,000 bytes; both BITMAP descriptors 400 rows
  (plane size 16,000); GDIINFO vertical resolution, size and mapping
  extents doubled (pixel aspect unchanged); Enable clears 64,000 bytes and
  starts at the top.
- pan_top (Data): first logical row shown. Every flush first clips its
  logical rows to [pan_top, pan_top+200), then converts rows to video rows
  row-pan_top. Cursor-retaining flushes pass video rows to TCURSOR.
- pan_set (far): move the viewport (hide cursor, convert the 200 rows,
  show cursor). Called only from Control, i.e. in task time.
- Control escape XTPAN_ESC (5850h, 'XP'): input word = new top (0FFFFh only
  queries), output 3 words = top in effect, viewport rows (200), logical
  rows (400). QUERYESCSUPPORT reports it.
TCURSOR.ASM
- The cursor origin is computed in video rows (logical y - pan_top); the
  existing clipping to 200 video rows hides a cursor outside the viewport.
SDIB88.ASM
- The DIB-to-screen bottom clip follows the 400-row surface.
TSOFT.DEF
- Description names XTPAN; aspect fields unchanged.
"""
import argparse
import sys
from pathlib import Path

VIEW_ROWS = 200
LOGICAL_ROWS = 400          # set_rows() changes it before patch_staged()
XTPAN_ESC = 0x5850


def set_rows(rows):
    """Logical height: 200 < rows <= 409 (the shadow, rows x 160 bytes, must
    stay below 64KB), a multiple of 4 so every derived size is whole."""
    global LOGICAL_ROWS
    if not (200 < rows <= 409 and rows % 4 == 0):
        raise SystemExit("PANPATCH: rows must be a multiple of 4 in 204..408")
    LOGICAL_ROWS = rows


def scaled(v):
    """A GDIINFO vertical quantity of the 200-row driver, scaled."""
    if (v * LOGICAL_ROWS) % 200:
        raise SystemExit(f"PANPATCH: {v} does not scale to {LOGICAL_ROWS} rows exactly")
    return v * LOGICAL_ROWS // 200


def crlf(s):
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def replace_n(text, old, new, want, name):
    old, new = crlf(old), crlf(new)
    n = text.count(old)
    if n != want:
        raise SystemExit(f"PANPATCH: '{name}' matched {n} times, expected {want}")
    return text.replace(old, new)


# Clip AX (first) / BX (exclusive last) logical rows to the viewport.
# DS = Data. Preserves everything else.
PAN_CLIP = """    ; PANPATCH: only rows inside the viewport reach video memory
    cmp ax,pan_top
    jge @@@_first
    mov ax,pan_top
@@@_first:
    push cx
    mov cx,pan_top
    add cx,VIEW_ROWS
    cmp bx,cx
    jle @@@_last
    mov bx,cx
@@@_last:
    pop cx
"""


def pan_clip(tag):
    return PAN_CLIP.replace("@@@", "pan_" + tag)


DATA_ANCHOR = "diag_markers dw 0,0,0,0\n"
DATA_NEW = """; PANPATCH: first logical row shown in the 200-row viewport.
public pan_top
pan_top dw 0
"""

PAN_SET = """
; PANPATCH: move the viewport. AX = requested first row. Returns AX = first
; row in effect (clamped to 0..LOGICAL-VIEW). Task time only (Control): it
; converts all 200 visible rows. Preserves all other registers.
public pan_set
pan_set proc far
    push bx
    push ds
    mov bx,seg pan_top
    mov ds,bx
    or ax,ax
    jns pan_set_low
    xor ax,ax
pan_set_low:
    cmp ax,SCREEN_HEIGHT-VIEW_ROWS
    jle pan_set_high
    mov ax,SCREEN_HEIGHT-VIEW_ROWS
pan_set_high:
    cmp ax,pan_top
    je pan_set_done
    cmp enabled_flag,0
    jne pan_set_move
    mov pan_top,ax
    jmp short pan_set_done
pan_set_move:
    call cursor_hide
    mov pan_top,ax
    call FlushShadow
    call cursor_show
pan_set_done:
    mov ax,pan_top
    pop ds
    pop bx
    ret
pan_set endp
"""

CONTROL_QUERY_OLD = """    cmp bx,GETCOLORTABLE
    je control_ok
    jmp control_done
control_color:
"""
CONTROL_QUERY_NEW = """    cmp bx,GETCOLORTABLE
    je control_ok
    cmp bx,XTPAN_ESC
    je control_ok
    jmp control_done
control_color:
    cmp bx,XTPAN_ESC
    jne control_not_pan
    ; PANPATCH: input word = new first row (0FFFFh: query only); output
    ; words = first row, viewport rows, logical rows.
    mov ax,es:[di]
    cmp ax,0FFFFh
    jne control_pan_move
    push ds
    mov ax,seg pan_top
    mov ds,ax
    mov ax,pan_top
    pop ds
    jmp short control_pan_out
control_pan_move:
    call pan_set
control_pan_out:
    les di,output
    mov ax,es
    or ax,di
    jz control_ok
    push ds
    mov ax,seg pan_top
    mov ds,ax
    mov ax,pan_top
    pop ds
    mov es:[di],ax
    mov word ptr es:[di+2],VIEW_ROWS
    mov word ptr es:[di+4],SCREEN_HEIGHT
    jmp control_ok
control_not_pan:
"""


def patch_tsoft(t):
    t = replace_n(t, "SCREEN_HEIGHT equ 200\n",
                  "SCREEN_HEIGHT equ %d              ; PANPATCH: logical rows\n"
                  "VIEW_ROWS equ %d                  ; PANPATCH: rows on screen\n"
                  "XTPAN_ESC equ %05Xh               ; PANPATCH: Control escape\n"
                  % (LOGICAL_ROWS, VIEW_ROWS, XTPAN_ESC), 1, "screen height")
    rows = LOGICAL_ROWS
    t = replace_n(t, "shadow_bits db 32000 dup (0)\n", "shadow_bits db %d dup (0)\n" % (rows * 160), 1,
                  "shadow size")
    t = replace_n(t, "BITMAP <0,320,200,40,4,1,0,8000,0,0,0,0,0,0>",
                  "BITMAP <0,320,%d,40,4,1,0,%d,0,0,0,0,0,0>" % (rows, rows * 40), 1, "shadow descriptor")
    t = replace_n(t, "BITMAP <1,320,200,40,4,1,0,8000,0,0,0,0,0,0>",
                  "BITMAP <1,320,%d,40,4,1,0,%d,0,0,0,0,0,0>" % (rows, rows * 40), 1, "physical descriptor")
    t = replace_n(t, "    dw 0300h,DT_RASDISPLAY,240,180,320,200,1,4\n",
                  "    dw 0300h,DT_RASDISPLAY,240,%d,320,%d,1,4\n" % (scaled(180), rows), 1,
                  "GDIINFO size/resolution")
    for wx, wy, vx, vy in ((2400, 1800, 320, -200), (24000, 18000, 320, -200), (1200, 900, 406, -254),
                           (12000, 9000, 406, -254), (17280, 12960, 406, -254)):
        old = "%d,%d,%d,%d" % (wx, wy, vx, vy)
        t = replace_n(t, "    dw %s\n" % old, "    dw %d,%d,%d,%d\n" % (wx, scaled(wy), vx, scaled(vy)), 1,
                      "mapping extents " + old)
    t = replace_n(t, "    mov cx,16000\n    cld\n    rep stosw\n",
                  "    mov cx,%d\n    cld\n    rep stosw\n" % (rows * 80), 1, "enable clears shadow")
    t = replace_n(t, DATA_ANCHOR, DATA_ANCHOR + DATA_NEW, 1, "pan_top")
    # every flush: clip to the viewport after its own clamps
    for label, tag in (("\nflush_last_clamped:\n", "fr"), ("\nkeep_last_clamped:\n", "kr"),
                       ("\nkcols_last_row:\n", "kc"), ("\ncols_last_row:\n", "fc")):
        t = replace_n(t, label, label + pan_clip(tag), 1, "viewport clip " + tag)
    # whole-row conversions: row counter and limit in video rows (SI from logical)
    t = replace_n(t, "    mov bp,ax\n    push bx\n    mov cx,SCREEN_W_BYTES*4\n    mul cx\n    mov si,ax\n",
                  "    mov bp,ax\n    sub bp,pan_top             ; PANPATCH: video row\n"
                  "    sub bx,pan_top\n    push bx\n    mov cx,SCREEN_W_BYTES*4\n    mul cx\n    mov si,ax\n",
                  2, "row loops in video rows")
    # column conversions keep their row locals in video rows
    t = replace_n(t, "    mov ss:[bp-2],ax\n    mov ss:[bp-4],bx\n",
                  "    mov ss:[bp-2],ax\n    mov ss:[bp-4],bx\n    push ax                    ; PANPATCH: video rows\n"
                  "    mov ax,pan_top\n    sub ss:[bp-2],ax\n    sub ss:[bp-4],ax\n    pop ax\n",
                  2, "column loops in video rows")
    # cursor retention compares video rows
    t = replace_n(t, "    mov dx,160\n    call cursor_begin_retain\n",
                  "    mov dx,160\n    sub ax,pan_top             ; PANPATCH: video rows\n    sub bx,pan_top\n"
                  "    call cursor_begin_retain\n    add ax,pan_top\n    add bx,pan_top\n", 1, "retain rows")
    t = replace_n(t, "    lea si,[bp-12]\n    call cursor_begin_retain\n",
                  "    lea si,[bp-12]\n    sub ax,pan_top             ; PANPATCH: video rows\n    sub bx,pan_top\n"
                  "    call cursor_begin_retain\n    add ax,pan_top\n    add bx,pan_top\n", 1, "retain columns")
    t = replace_n(t, "FlushColumns endp\n", "FlushColumns endp\n" + PAN_SET, 1, "pan_set")
    t = replace_n(t, CONTROL_QUERY_OLD, CONTROL_QUERY_NEW, 1, "Control escape")
    return t


def patch_tcursor(t):
    t = replace_n(t, "    externB enabled_flag\n", "    externB enabled_flag\n    externW pan_top\n", 1,
                  "pan_top extern")
    t = replace_n(t, "    mov ax,tc_y\n    sub ax,tc_hot_y\n    mov tc_origin_y,ax\n",
                  "    mov ax,tc_y\n    sub ax,tc_hot_y\n    sub ax,pan_top             ; PANPATCH: video rows\n"
                  "    mov tc_origin_y,ax\n", 1, "cursor origin")
    return t


def patch_sdib(t):
    return replace_n(t, "    cmp bx,200\n    jle sd_clip_bottom\n    mov bx,200\n",
                     "    cmp bx,%d                  ; PANPATCH: logical rows\n    jle sd_clip_bottom\n"
                     "    mov bx,%d\n" % (LOGICAL_ROWS, LOGICAL_ROWS), 1, "DIB bottom clip")


def patch_def(t):
    return replace_n(t, "Tandy 320x200 16-color software raster",
                     "XTPAN Tandy 320x400 panned 16-color (experimental)", 1, "description")


def patch_staged(ega_dir):
    ega = Path(ega_dir)
    jobs = ((ega / "TSOFT.ASM", patch_tsoft), (ega / "TCURSOR.ASM", patch_tcursor),
            (ega.parent / "SDIB88.ASM", patch_sdib), (ega / "TSOFT.DEF", patch_def))
    done = {}
    for p, fn in jobs:
        new = fn(p.read_bytes().decode("latin-1"))
        if "\n" in new.replace("\r\n", ""):
            raise SystemExit(f"PANPATCH: bare LF in {p.name}")
        done[p] = new
    for p, new in done.items():
        p.write_bytes(new.encode("latin-1"))
    return {p.name: new for p, new in done.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--staged", type=Path, help="dry run against a staged EGA dir (nothing written)")
    ap.add_argument("--rows", type=int, default=400, help="logical rows (default 400)")
    a = ap.parse_args()
    assert "pan_fr_first" in pan_clip("fr") and LOGICAL_ROWS * 160 == 64000
    ap_rows = a.rows if hasattr(a, "rows") else 400
    set_rows(ap_rows)
    if a.staged:
        for name, fn in (("TSOFT.ASM", patch_tsoft), ("TCURSOR.ASM", patch_tcursor),
                         ("TSOFT.DEF", patch_def)):
            fn((a.staged / name).read_bytes().decode("latin-1"))
        patch_sdib((a.staged.parent / "SDIB88.ASM").read_bytes().decode("latin-1"))
        print("PANPATCH: every edit matches the staged sources")
    print("PANPATCH: check PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
