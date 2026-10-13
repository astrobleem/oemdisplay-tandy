#!/usr/bin/env python3
"""Amstrad PC1512 640x200x16 edits for the TR5 driver (docs/PC1512.MD).

Usage:
  python3 src/pc1512/P15PATCH.PY --check     model self-test (no emulator)

BUILD15.PY runs BUILD88's unchanged 640x200 pipeline (geometry, CGA fonts,
byte columns, cursor retention, output rows, wide scanlines) with the
profile marked 16-colour, so the four-colour mapper (MODECOL) is skipped and
the full sixteen-colour mapper stays. patch_staged() then edits the staged
EGA/TSOFT.ASM and EGA/TCURSOR.ASM before the first assembly. Every edit
must match an exact count or nothing is written.

Hardware (seasip.info "PC1512 display notes"; 86Box src/machine/m_amstrad.c):
  ROS mode 6 (CGA 640x200), then 3D9h = 0Fh to display all four planes
  (the ROS leaves 7: intensity hidden). Four 16KB bit-planes share the CGA
  window at B800h: even rows at +0000h, odd rows at +2000h, 80 bytes per
  row, leftmost pixel in bit 7. Plane bits: 0 blue, 1 green, 2 red,
  3 intensity. Port 3DDh (write-only) is a write mask: a CPU write lands in
  every selected plane. Port 3DEh (write-only, low 2 bits) selects the one
  plane CPU reads return (0 blue .. 3 intensity).

Driver: the shadow keeps four 80-byte planes per row in DDK order 0=red,
1=green, 2=blue, 3=intensity. Each shadow plane row is copied unchanged
into its hardware plane: red -> mask 4, green -> 2, blue -> 1, intensity
-> 8. The cursor saves the four planes under it through 3DEh, composites
in a private copy and writes each plane back through 3DDh. Every path
leaves 3DDh = 0Fh and 3DEh = 0.
"""
import argparse
import re
import sys
from pathlib import Path

# --- TSOFT ----------------------------------------------------------------

ROW_MACROS = (
    "; P15PATCH: copy one shadow row segment into the four PC1512 planes.\r\n"
    "; DS:SI = shadow red byte, ES:DI = VRAM byte, BX = byte count.\r\n"
    "; Shadow planes are 80 bytes apart (R,G,B,I); hardware write masks are\r\n"
    "; red 4, green 2, blue 1, intensity 8. Returns SI advanced by BX and\r\n"
    "; 3DDh = 0Fh. Clobbers AX, CX, DX.\r\n"
    "p15_plane macro off,mask\r\n"
    "    push si\r\n"
    "    push di\r\n"
    "    add si,off\r\n"
    "    mov al,mask\r\n"
    "    out dx,al\r\n"
    "    mov cx,bx\r\n"
    "    rep movsb\r\n"
    "    pop di\r\n"
    "    pop si\r\n"
    "endm\r\n"
    "p15_row macro\r\n"
    "    mov dx,3ddh\r\n"
    "    p15_plane 0,4\r\n"
    "    p15_plane 80,2\r\n"
    "    p15_plane 160,1\r\n"
    "    p15_plane 240,8\r\n"
    "    mov al,0fh\r\n"
    "    out dx,al\r\n"
    "    add si,bx\r\n"
    "endm\r\n"
)
MACRO_ANCHOR = "public FlushShadow,FlushRows\r\n"

FOURCOL_NOTE = ("    ; The low two logical planes are the actual four-color pixel index.\r\n"
                "    ; Plane 2/3 are redundant for normal colors, preserving all DDK ROPs.\r\n")
BYTE_LOOP = re.compile(
    r"    mov cx,(80|ss:\[bp-8\])\r\n(\w+)_byte:\r\n    mov al,\[si\]\r\n    mov ah,\[si\+80\]\r\n"
    r"    stosw\r\n    inc si\r\n    loop \2_byte\r\n")


def tandy_row(row):
    return ("    mov ax,%s\r\n    and ax,3\r\n    mov cl,13\r\n    shl ax,cl\r\n"
            "    mov di,ax\r\n    mov ax,%s\r\n    shr ax,1\r\n    shr ax,1\r\n"
            "    mov cx,160\r\n    mul cx\r\n    add di,ax\r\n") % (row, row)


def cga_row(row):
    return ("    mov ax,%s\r\n    and ax,1                  ; P15PATCH: CGA even/odd banks\r\n"
            "    mov cl,13\r\n    shl ax,cl\r\n"
            "    mov di,ax\r\n    mov ax,%s\r\n    shr ax,1\r\n"
            "    mov cx,80\r\n    mul cx\r\n    add di,ax\r\n") % (row, row)


TANDY_MODE = ("    mov ax,000ah\r\n    int 10h\r\n"
              "    mov ax,1000h\r\n    mov bx,0000h\r\n    int 10h\r\n"
              "    mov ax,1000h\r\n    mov bx,0c01h\r\n    int 10h\r\n"
              "    mov ax,1000h\r\n    mov bx,0a02h\r\n    int 10h\r\n"
              "    mov ax,1000h\r\n    mov bx,0f03h\r\n    int 10h\r\n"
              "    mov ax,1001h\r\n    xor bx,bx\r\n    int 10h\r\n")
P15_MODE = (
    "    mov ax,6                  ; P15PATCH: ROS mode 6, CGA 640x200\r\n"
    "    int 10h\r\n"
    "    ; seasip.info: with interrupts off, in vertical flyback, show all\r\n"
    "    ; four planes (3D9h = 0Fh; the ROS leaves 7) and write all planes.\r\n"
    "    pushf\r\n"
    "    cli\r\n"
    "    mov dx,3dah\r\n"
    "    xor cx,cx\r\n"
    "p15_wait_end:\r\n"
    "    in al,dx\r\n"
    "    test al,8\r\n"
    "    loopnz p15_wait_end\r\n"
    "    xor cx,cx\r\n"
    "p15_wait_start:\r\n"
    "    in al,dx\r\n"
    "    test al,8\r\n"
    "    loopz p15_wait_start\r\n"
    "    mov dx,3d9h\r\n"
    "    mov al,0fh\r\n"
    "    out dx,al\r\n"
    "    mov dx,3ddh\r\n"
    "    out dx,al\r\n"
    "    mov dx,3deh\r\n"
    "    xor al,al\r\n"
    "    out dx,al\r\n"
    "    popf\r\n"
    "    push es\r\n"
    "    mov ax,0b800h\r\n"
    "    mov es,ax\r\n"
    "    xor di,di\r\n"
    "    xor ax,ax\r\n"
    "    mov cx,2000h\r\n"
    "    cld\r\n"
    "    rep stosw\r\n"
    "    pop es\r\n")

DISABLE_OLD = "    mov al,old_mode\r\n    xor ah,ah\r\n    int 10h\r\n"
DISABLE_NEW = ("    mov dx,3ddh               ; P15PATCH: default plane access\r\n"
               "    mov al,0fh\r\n    out dx,al\r\n"
               "    mov dx,3deh\r\n    xor al,al\r\n    out dx,al\r\n"
               "    mov dx,3d9h\r\n    mov al,7\r\n    out dx,al\r\n" + DISABLE_OLD)


def replace_n(text, old, new, want, name):
    n = text.count(old)
    if n != want:
        raise SystemExit(f"P15PATCH: '{name}' matched {n} times, expected {want}")
    return text.replace(old, new)


def patch_tsoft(t):
    t = replace_n(t, MACRO_ANCHOR, ROW_MACROS + MACRO_ANCHOR, 1, "row macros")
    t = replace_n(t, "    dw -1,20,0,0,4,size BITMAP", "    dw -1,80,0,0,16,size BITMAP", 1, "GDI 16 colours")
    t = replace_n(t, tandy_row("bp"), cga_row("bp"), 2, "row address (bp)")
    t = replace_n(t, tandy_row("ss:[bp-2]"), cga_row("ss:[bp-2]"), 2, "row address (local)")
    t = replace_n(t, "    mov ax,ss:[bp-6]\r\n    shl ax,1\r\n    add di,ax\r\n",
                  "    mov ax,ss:[bp-6]          ; P15PATCH: one VRAM byte per logical byte\r\n    add di,ax\r\n",
                  2, "column offset")
    t = replace_n(t, FOURCOL_NOTE, "    ; P15PATCH: all four shadow planes go to their hardware planes.\r\n",
                  4, "four-colour note")
    n = len(BYTE_LOOP.findall(t))
    if n != 4:
        raise SystemExit(f"P15PATCH: byte loops matched {n} times, expected 4")
    t = BYTE_LOOP.sub(lambda m: "    mov bx,%s\r\n    p15_row\r\n" % m.group(1), t)
    # Cursor retention footprints are physical bytes of one plane row.
    t = replace_n(t, "    xor cx,cx\r\n    mov dx,160\r\n    call cursor_begin_retain\r\n",
                  "    xor cx,cx\r\n    mov dx,80                 ; P15PATCH: plane row bytes\r\n    call cursor_begin_retain\r\n",
                  1, "retain rows width")
    t = replace_n(t, "    push cx\r\n    push dx\r\n    shl cx,1\r\n    shl dx,1\r\n    lea si,[bp-12]\r\n",
                  "    push cx\r\n    push dx\r\n    ; P15PATCH: logical bytes are physical bytes\r\n    lea si,[bp-12]\r\n",
                  1, "retain columns scale")
    t = replace_n(t, TANDY_MODE, P15_MODE, 1, "enable mode")
    t = replace_n(t, DISABLE_OLD, DISABLE_NEW, 1, "disable mode")
    if re.search(r"(?m)^\s+mov (cx|dx),160\r$", t):
        raise SystemExit("P15PATCH: Tandy 160-byte row stride left in TSOFT")
    return t


# --- TCURSOR --------------------------------------------------------------

TC_SCAN_OLD = ("    mov bx,ax\r\n    and bx,3\r\n    mov cl,13\r\n    shl bx,cl\r\n"
               "    shr ax,1\r\n    shr ax,1\r\n    mov dx,160\r\n    mul dx\r\n")
TC_SCAN_NEW = ("    mov bx,ax                 ; P15PATCH: CGA even/odd banks\r\n"
               "    and bx,1\r\n    mov cl,13\r\n    shl bx,cl\r\n"
               "    shr ax,1\r\n    mov dx,80\r\n    mul dx\r\n")

TC_DATA_OLD = "    tc_saved        db 544 dup (0)\r\n"
TC_DATA_NEW = ("    tc_saved        db 640 dup (0)    ; P15PATCH: 4 planes x 32 rows x 5 bytes\r\n"
               "    tc_work         db 640 dup (0)    ; P15PATCH: composite before write-back\r\n"
               "    tc_plane_size   dw 0\r\n")

TC_HELPERS = (
    "; P15PATCH: SI = plane-major buffer (blue, green, red, intensity), each\r\n"
    "; tc_save_rows x tc_save_bytes. tc_get reads the saved rectangle through\r\n"
    "; 3DEh, tc_put writes it through 3DDh. Both leave the default 3DDh = 0Fh,\r\n"
    "; 3DEh = 0. Clobber AX, BX, CX, DX, SI, DI, BP, ES.\r\n"
    "tc_get proc near\r\n"
    "    mov ax,0B800h\r\n    mov es,ax\r\n    xor bl,bl\r\n"
    "tcg_plane:\r\n"
    "    mov dx,3deh\r\n    mov al,bl\r\n    out dx,al\r\n"
    "    push bx\r\n    mov bx,tc_save_y\r\n    mov bp,tc_save_rows\r\n"
    "tcg_row:\r\n"
    "    mov ax,bx\r\n    call tc_scan\r\n    add di,tc_save_xbyte\r\n    mov cx,tc_save_bytes\r\n"
    "tcg_byte:\r\n"
    "    mov al,es:[di]\r\n    mov [si],al\r\n    inc si\r\n    inc di\r\n    loop tcg_byte\r\n"
    "    inc bx\r\n    dec bp\r\n    jnz tcg_row\r\n"
    "    pop bx\r\n    inc bl\r\n    cmp bl,4\r\n    jb tcg_plane\r\n"
    "    mov dx,3deh\r\n    xor al,al\r\n    out dx,al\r\n"
    "    ret\r\n"
    "tc_get endp\r\n"
    "\r\n"
    "tc_put proc near\r\n"
    "    mov ax,0B800h\r\n    mov es,ax\r\n    mov bl,1\r\n"
    "tcp_plane:\r\n"
    "    mov dx,3ddh\r\n    mov al,bl\r\n    out dx,al\r\n"
    "    push bx\r\n    mov bx,tc_save_y\r\n    mov bp,tc_save_rows\r\n"
    "tcp_row:\r\n"
    "    mov ax,bx\r\n    call tc_scan\r\n    add di,tc_save_xbyte\r\n    mov cx,tc_save_bytes\r\n"
    "    cld\r\n    rep movsb\r\n"
    "    inc bx\r\n    dec bp\r\n    jnz tcp_row\r\n"
    "    pop bx\r\n    shl bl,1\r\n    cmp bl,10h\r\n    jb tcp_plane\r\n"
    "    mov dx,3ddh\r\n    mov al,0fh\r\n    out dx,al\r\n"
    "    ret\r\n"
    "tc_put endp\r\n"
    "\r\n"
)
TC_HELPER_ANCHOR = "; Restore only the byte rectangle saved under the previous cursor.\r\n"

TC_ERASE_OLD = ("    mov ax,0B800h\r\n    mov es,ax\r\n    mov si,offset tc_saved\r\n"
                "    mov bx,tc_save_y\r\n    mov bp,tc_save_rows\r\ntce_row:\r\n"
                "    mov ax,bx\r\n    call tc_scan\r\n    add di,tc_save_xbyte\r\n"
                "    mov cx,tc_save_bytes\r\n    cld\r\n    rep movsb\r\n"
                "    inc bx\r\n    dec bp\r\n    jnz tce_row\r\n")
TC_ERASE_NEW = ("    mov si,offset tc_saved    ; P15PATCH: all four planes\r\n"
                "    call tc_put\r\n")

TC_GEOM_OLD = ("    ; Cover complete adjacent plane-byte pairs for the clipped cursor.\r\n"
               "    mov ax,tc_left\r\n    shr ax,1\r\n    shr ax,1\r\n    shr ax,1\r\n    shl ax,1\r\n"
               "    mov tc_save_xbyte,ax\r\n"
               "    mov bx,tc_right\r\n    dec bx\r\n    shr bx,1\r\n    shr bx,1\r\n    shr bx,1\r\n    shl bx,1\r\n"
               "    sub bx,ax\r\n    add bx,2\r\n    mov tc_save_bytes,bx\r\n")
TC_GEOM_NEW = ("    ; P15PATCH: one byte per eight pixels in each plane.\r\n"
               "    mov ax,tc_left\r\n    shr ax,1\r\n    shr ax,1\r\n    shr ax,1\r\n"
               "    mov tc_save_xbyte,ax\r\n"
               "    mov bx,tc_right\r\n    dec bx\r\n    shr bx,1\r\n    shr bx,1\r\n    shr bx,1\r\n"
               "    sub bx,ax\r\n    inc bx\r\n    mov tc_save_bytes,bx\r\n"
               "    mov ax,tc_save_rows\r\n    mul bx\r\n    mov tc_plane_size,ax\r\n")

TC_SAVE_OLD = ("    mov ax,0B800h\r\n    mov es,ax\r\n    mov si,offset tc_saved\r\n"
               "    mov bx,tc_save_y\r\n    mov bp,tc_save_rows\r\ntcd_save_row:\r\n"
               "    mov ax,bx\r\n    call tc_scan\r\n    add di,tc_save_xbyte\r\n    mov cx,tc_save_bytes\r\n"
               "tcd_save_byte:\r\n    mov al,es:[di]\r\n    mov [si],al\r\n    inc si\r\n    inc di\r\n"
               "    loop tcd_save_byte\r\n    inc bx\r\n    dec bp\r\n    jnz tcd_save_row\r\n"
               "    mov tc_drawn,1\r\n")
TC_SAVE_NEW = ("    mov si,offset tc_saved    ; P15PATCH: save all four planes\r\n"
               "    call tc_get\r\n"
               "    mov tc_drawn,1\r\n"
               "    ; Composite in tc_work, a copy of the saved planes.\r\n"
               "    push es\r\n    push ds\r\n    pop es\r\n"
               "    mov si,offset tc_saved\r\n    mov di,offset tc_work\r\n"
               "    mov cx,tc_plane_size\r\n    shl cx,1\r\n    shl cx,1\r\n"
               "    cld\r\n    rep movsb\r\n    pop es\r\n")

TC_ROW_OLD = ("    mov ax,tc_work_y\r\n    call tc_scan\r\n    mov tc_row_offset,di\r\n")
TC_ROW_NEW = ("    mov ax,tc_work_y          ; P15PATCH: row start in tc_work\r\n"
              "    sub ax,tc_save_y\r\n    mul tc_save_bytes\r\n    mov tc_row_offset,ax\r\n")

TC_PIXEL_START = "    ; BL is the cursor-mask bit. BH is the physical screen-pixel bit.\r\n"
TC_PIXEL_END = "    mov es:[di],ax\r\n"
TC_PIXEL_NEW = (
    "    ; P15PATCH: BL is the cursor-mask bit, BH the screen-pixel bit. AND\r\n"
    "    ; forces colour 0 and XOR flips all four colour bits, so apply each\r\n"
    "    ; bitwise to the pixel's bit in every plane of tc_work.\r\n"
    "    mov ax,tc_work_x\r\n    mov cx,ax\r\n    and cx,7\r\n    mov bh,80h\r\n    shr bh,cl\r\n"
    "    shr ax,1\r\n    shr ax,1\r\n    shr ax,1\r\n"
    "    sub ax,tc_save_xbyte\r\n    add ax,tc_row_offset\r\n    mov di,ax\r\n"
    "    test tc_and[si],bl\r\n    jnz tcd_and_done\r\n"
    "    mov dl,bh\r\n    not dl\r\n    push di\r\n    mov cx,4\r\n"
    "tcd_and_plane:\r\n    and tc_work[di],dl\r\n    add di,tc_plane_size\r\n    loop tcd_and_plane\r\n"
    "    pop di\r\n"
    "tcd_and_done:\r\n"
    "    test tc_xor[si],bl\r\n    jz tcd_xor_done\r\n"
    "    mov cx,4\r\n"
    "tcd_xor_plane:\r\n    xor tc_work[di],bh\r\n    add di,tc_plane_size\r\n    loop tcd_xor_plane\r\n"
    "tcd_xor_done:\r\n")
TC_FINISH_OLD = "tcd_finished:\r\n    ret\r\ntc_draw endp\r\n"
TC_FINISH_NEW = ("tcd_finished:\r\n"
                 "    mov si,offset tc_work     ; P15PATCH: write the composite\r\n"
                 "    call tc_put\r\n"
                 "    ret\r\ntc_draw endp\r\n")


def patch_tcursor(t):
    t = t.replace("Tandy 640x200 four-color", "Amstrad PC1512 640x200 sixteen-colour")
    t = replace_n(t, TC_DATA_OLD, TC_DATA_NEW, 1, "save buffers")
    t = replace_n(t, TC_SCAN_OLD, TC_SCAN_NEW, 1, "tc_scan")
    t = replace_n(t, TC_HELPER_ANCHOR, TC_HELPERS + TC_HELPER_ANCHOR, 1, "plane helpers")
    t = replace_n(t, TC_ERASE_OLD, TC_ERASE_NEW, 1, "tc_erase")
    t = replace_n(t, TC_GEOM_OLD, TC_GEOM_NEW, 1, "save geometry")
    t = replace_n(t, TC_SAVE_OLD, TC_SAVE_NEW, 1, "save planes")
    t = replace_n(t, TC_ROW_OLD, TC_ROW_NEW, 1, "row offset")
    if t.count(TC_PIXEL_START) != 1 or t.count(TC_PIXEL_END) != 1:
        raise SystemExit("P15PATCH: pixel block anchors not unique")
    a = t.index(TC_PIXEL_START)
    b = t.index(TC_PIXEL_END, a) + len(TC_PIXEL_END)
    t = t[:a] + TC_PIXEL_NEW + t[b:]
    t = replace_n(t, TC_FINISH_OLD, TC_FINISH_NEW, 1, "write composite")
    # Retain lease checks: physical columns are one plane row (80 bytes);
    # the saved length is per plane, rows*bytes <= 160 (640 / 4).
    t = replace_n(t, "    cmp dx,160\r\n    ck_require jbe,ckb_legacy\r\n",
                  "    cmp dx,80                 ; P15PATCH\r\n    ck_require jbe,ckb_legacy\r\n",
                  2, "retain column limits")
    t = replace_n(t, "    cmp cx,160\r\n    ck_require jb,ckb_legacy\r\n",
                  "    cmp cx,80                 ; P15PATCH\r\n    ck_require jb,ckb_legacy\r\n",
                  1, "retain column origin")
    t = replace_n(t, "    cmp ax,544\r\n", "    cmp ax,160                ; P15PATCH: per plane\r\n",
                  1, "retain buffer length")
    if re.search(r"(?m)^\s+(mov dx,160|cmp dx,160|cmp cx,160)\r$|\b544\b", t):
        raise SystemExit("P15PATCH: a Tandy 160/544 constant is left in TCURSOR")
    if "es:[di],ax" in t:
        raise SystemExit("P15PATCH: direct Tandy pixel write left in TCURSOR")
    return t


# --- sixteen-colour restore ------------------------------------------------
# MODECOL (the 640x200x4 profile's four-colour mapper) rewrites these files
# and TSOFT sections. After MODECOL, only REPCOPY88 (mode-independent) edits
# any of the files, so BUILD88's accepted 320x200x16 stage holds exactly the
# sixteen-colour versions this 640-wide build needs.
MODECOL_FILES = ("COLORS.ASM", "ROBJECT.ASM", "ENUM.ASM", "BMC_ITE.ASM", "CBLT.ASM", "SCANLR.ASM")
TSOFT_SECTIONS = (
    ("PAccelTable label   byte", "PColorTable label   byte"),
    ("PColorTable label   byte", ";----------------------------------------------------------------------------;\n; define two hack routines"),
    ("PixelSeg_color_table\tlabel\tdword", "sEnd\tPixelSeg"),
    ("BlueMoonSeg_color_table label\tdword", "sEnd\tBlueMoonSeg"),
    ("DIMapSeg_color_table label\tdword", "sEnd\tDIMapSeg"),
)
TSOFT_LINES = (
    ("COLOR_TBL_SIZE equ 4 ;four distinct colors for escape/enumeration",
     "COLOR_TBL_SIZE\tequ\t16\t\t;16 entries in the table"),
    ("    cmp si,COLOR_TBL_SIZE\n    jae control_done", "    cmp si,16\n    jae control_done"),
)


def _span(text, first, last):
    if text.count(first) != 1:
        raise SystemExit(f"P15PATCH: section start {first!r} found {text.count(first)} times")
    a = text.index(first)
    b = text.index(last, a)
    return text[a:b]


def restore_sixteen(t640, t320):
    """Replace MODECOL's four-colour TSOFT sections with the 320x200x16 ones."""
    lf640 = t640.replace("\r\n", "\n")
    lf320 = t320.replace("\r\n", "\n")
    for first, last in TSOFT_SECTIONS:
        lf640 = lf640.replace(_span(lf640, first, last), _span(lf320, first, last))
        if _span(lf640, first, last) != _span(lf320, first, last):
            raise SystemExit("P15PATCH: section restore failed: " + first)
    for four, sixteen in TSOFT_LINES:
        if lf640.count(four) != 1 or lf320.count(sixteen) != 1:
            raise SystemExit(f"P15PATCH: colour line {four!r} not found exactly once")
        lf640 = lf640.replace(four, sixteen)
    return lf640.replace("\n", "\r\n")


def patch_staged(ega_dir):
    ega = Path(ega_dir)
    done = {}
    for name, fn in (("TSOFT.ASM", patch_tsoft), ("TCURSOR.ASM", patch_tcursor)):
        p = ega / name
        old = p.read_bytes().decode("latin-1")
        new = fn(old)
        assert "\n" not in new.replace("\r\n", ""), "bare LF"
        p.write_bytes(new.encode("latin-1"))
        done[name] = new
    return done


# --- host models -----------------------------------------------------------

HW_MASK = (4, 2, 1, 8)    # shadow plane R,G,B,I -> PC1512 write mask


def shadow_pixel(shadow, y, x):
    """IRGB colour of pixel (x,y) in the 640-wide four-plane shadow."""
    base = y * 320 + (x >> 3)
    bit = 7 - (x & 7)
    r = (shadow[base] >> bit) & 1
    g = (shadow[base + 80] >> bit) & 1
    b = (shadow[base + 160] >> bit) & 1
    i = (shadow[base + 240] >> bit) & 1
    return (i << 3) | (r << 2) | (g << 1) | b


def model_flush(shadow):
    """The p15_row macro over all rows: 64KB of plane memory, plane p at p*16K."""
    vram = bytearray(0x10000)
    for y in range(200):
        di = (y & 1) * 0x2000 + (y >> 1) * 80
        for k, mask in enumerate(HW_MASK):
            for p in range(4):
                if mask & (1 << p):
                    vram[p * 0x4000 + di:p * 0x4000 + di + 80] = shadow[y * 320 + 80 * k:y * 320 + 80 * k + 80]
    return vram


def p1512_pixel(vram, y, x, colour_select=0x0F):
    """86Box ams1512_render: colour = plane bits (B,G,R,I) AND 3D9h."""
    off = (y & 1) * 0x2000 + (y >> 1) * 80 + (x >> 3)
    bit = 7 - (x & 7)
    c = 0
    for p in range(4):
        c |= ((vram[p * 0x4000 + off] >> bit) & 1) << p
    return c & colour_select


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    import random
    rnd = random.Random(1512)
    shadow = bytes(rnd.randrange(256) for _ in range(64000))
    vram = model_flush(shadow)
    bad = sum(p1512_pixel(vram, y, x) != shadow_pixel(shadow, y, x)
              for y in range(200) for x in range(640))
    assert bad == 0, bad
    hidden = sum(p1512_pixel(vram, y, x, 7) != shadow_pixel(shadow, y, x)
                 for y in range(200) for x in range(640))
    assert hidden > 0
    print("P15PATCH: model PASS (plane copy reproduces every shadow colour through the "
          "86Box PC1512 decode, 128,000 pixels; the ROS default 3D9h=7 would not)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
