#!/usr/bin/env python3
"""TEXT80 tall desktops: Windows 3.0 on a 640x400 logical screen in text
mode (docs/TEXT80.MD). Measurement and experimental builds only.

  python3 src/text80/T80TALL.PY --check     self-test (no emulator)

Applied by BUILDT80.PY instead of plain T80PATCH for two profiles:

  pan  80x25 colour text on any CGA-compatible adapter (CGA, Tandy 1000,
       PCjr-class, EGA, VGA), showing 25 of 50 logical text rows. The
       desktop is 640x400; a pan (Control escape 5850h, as XTPAN's, driven
       by the unchanged XTPAN.EXE helper) moves the 25-row window in whole
       text rows. Every flush keeps the logical text of all 50 rows in RAM
       (T40_LSEG, 8,000 bytes); a pan copies 25 rows of it to B800h and
       converts nothing.
  vga  VGA 80x50 colour text (mode 03h with the 8x8 ROM font, INT 10h
       AX=1112h): all 50 rows shown, nothing pans. Enable refuses (returns
       0) unless INT 10h AX=1A00h reports a VGA (display combination 7 or
       8) and the BIOS then reports 50 rows.

Both keep TR5's 16-colour four-plane shadow, now 640x400 = 128,000 bytes:
more than one real-mode segment. It is a DDK huge bitmap: two bands of
200 scan lines (64,000 bytes) whose second starts __NEXTSEG paragraphs
after the first (bmSegmentIndex = __NEXTSEG, bmScanSegment = 200,
bmFillBytes = 1,536), allocated at Enable with GlobalAlloc (129,536 bytes,
checked: Enable returns 0 when it fails) and freed at Disable. The DDK
renderer modules handle huge destinations themselves; the presenter reads
rows 200..399 through t40_sh1 (T40PRES t40_rowes). The static 64,000-byte
shadow segment shrinks to 16 bytes.

Edits on top of T80PATCH (each must match exactly once):
  SCREEN_HEIGHT 400; shadow and device BITMAP descriptors; GDIINFO (400
  rows, vertical size and mapping extents doubled as XTPAN does); the
  ORowsSpanSafe alias check against the allocated shadow; SDIB88's bottom
  clip; the text-mode cursor's vertical limit and, panned, its origin
  (pan_top, as XTPAN); Enable/Disable allocation; the Control escape.
"""
import argparse
import importlib.machinery
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T80 = importlib.machinery.SourceFileLoader("t80patch_tall", str(HERE / "T80PATCH.PY")).load_module()
T40 = T80.T40
crlf, replace_n = T40.crlf, T40.replace_n

ROWS = 400
# fault injection (test build t80panfail only): GlobalAlloc is asked for
# 7FA00h bytes, which real-mode Windows cannot satisfy, so Enable takes its
# allocation-failure path on every machine
FAIL_ALLOC = False
PAN_ESC = 0x5850
SHADOW_BYTES = 65536 + 64000          # band 0, its fill, band 1


def geometry(kind):
    g = dict(T80.GEOMETRY)
    g.update({"T40_NROWS": 50, "T40_VISROWS": 25 if kind == "pan" else 50})
    return g


def segments(kind):
    return {"T40_SHSEG": "0", "T40_VSEG": "0b800h", "T40_LSEG": "seg t80_lbuf" if kind == "pan" else "0b800h",
            "T40_SNSEG": "seg t40_snapbuf"}


# ---- Enable / Disable ---------------------------------------------------------

# replaces the static shadow's descriptor setup at enable_device: allocate
# (once per Enable/Disable pair), then describe the huge shadow
ALLOC_OLD = ("    mov ax,seg shadow_bits\r\n    mov word ptr shadow_device.bmBits+2,ax\r\n"
             "    mov word ptr shadow_device.bmBits,offset shadow_bits\r\n")
ALLOC_NEW = crlf("""    cmp t80_shh,0             ; T80TALL: the 640x400 shadow (huge, two bands)
    jne t80a_have
    xor ax,ax                 ; GMEM_FIXED
    mov bx,ALLOC_HI
    mov cx,SHADOW_LO
    cCall GlobalAlloc,<ax,bx,cx>
    or ax,ax
    jnz t80a_got
    jmp enable_done           ; AX = 0: Enable fails, nothing was changed
t80a_got:
    mov t80_shh,ax
    cCall GlobalLock,<ax>
    or dx,dx
    jnz t80a_locked
    mov ax,t80_shh            ; cannot happen for a fixed block; fail closed
    cCall GlobalFree,<ax>
    mov t80_shh,0
    xor ax,ax
    jmp enable_done
t80a_locked:
    mov t80_shs,dx
    mov es,dx                 ; clear both bands
    xor di,di
    xor ax,ax
    mov cx,32000
    cld
    rep stosw
    mov ax,dx
    add ax,__NEXTSEG
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,32000
    rep stosw
    mov ax,seg t40_slot
    mov es,ax
    mov es:t40_sh0,dx
    add dx,__NEXTSEG
    mov es:t40_sh1,dx
t80a_have:
    mov ax,t80_shs
    mov word ptr shadow_device.bmBits+2,ax
    mov word ptr shadow_device.bmBits,0
    mov ax,__NEXTSEG
    mov shadow_device.bmSegmentIndex,ax
    les di,device             ; the caller's PDEVICE copy (rep movsb moved DI)
""")

# the old whole-shadow clear: both bands were cleared at allocation
CLEAR_OLD = ("    mov ax,seg shadow_bits\r\n    mov es,ax\r\n    xor di,di\r\n    xor ax,ax\r\n"
             "    mov cx,32000\r\n    cld\r\n    rep stosw\r\n")
CLEAR_NEW = crlf("""    mov pan_top,0             ; T80TALL: the shadow was cleared at allocation
""")

DISABLE_OLD = "    mov ax,ScratchSel\r\n    or ax,ax\r\n    jz disable_done\r\n"
DISABLE_NEW = crlf("""    mov ax,t80_shh            ; T80TALL: free the shadow
    or ax,ax
    jz t80d_none
    push ax
    cCall GlobalUnlock,<ax>
    pop ax
    cCall GlobalFree,<ax>
    mov t80_shh,0
    mov t80_shs,0
    push ds
    mov ax,seg t40_slot
    mov ds,ax
    mov ds:t40_sh0,0
    mov ds:t40_sh1,0
    pop ds
t80d_none:
    mov ax,ScratchSel
    or ax,ax
    jz disable_done
""")

# the video/text clear of T80PATCH's mode setup, for 50 logical rows
TEXT_CLEAR_OLD = "    mov cx,T40_NCELL\r\n    cld\r\n    rep stosw\r\n"
TEXT_CLEAR_PAN = crlf("""    mov cx,T40_VISROWS*T40_COLS
    cld
    rep stosw
    mov ax,T40_LSEG           ; T80TALL: the logical text of all 50 rows
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,T40_NCELL
    rep stosw
""")
TEXT_CLEAR_VGA = crlf("""    mov cx,T40_VISROWS*T40_COLS
    cld
    rep stosw
""")
VIEW_RESET = crlf("""    mov es:t40_snv,0          ; no snapshot held
    mov es:t40_vtop,0         ; T80TALL: the screen shows rows 0..
    mov es:t40_voff,0
""")

# VGA 80x50: refuse anything that is not a VGA before touching the mode
VGA_MODE_OLD = "    mov ax,3                  ; T80PATCH: BIOS 80x25 colour text\r\n    int 10h\r\n"
VGA_MODE_NEW = crlf("""    mov ax,1A00h              ; T80TALL: VGA? (display combination code)
    int 10h
    cmp al,1Ah
    jne t80v_fail
    cmp bl,7
    je t80v_ok
    cmp bl,8
    je t80v_ok
t80v_fail:
    mov ax,t80_shh            ; not a VGA: free the shadow, Enable fails
    push ax
    cCall GlobalUnlock,<ax>
    pop ax
    cCall GlobalFree,<ax>
    mov t80_shh,0
    mov t80_shs,0
    mov ax,ScratchSel
    cCall FreeSelector,<ax>
    mov ScratchSel,0
    xor ax,ax
    jmp enable_done
t80v_ok:
    mov ax,3                  ; BIOS 80x25 colour text, then the 8x8 ROM
    int 10h                   ; font: 400 scan lines / 8 = 50 rows
    mov ax,1112h
    xor bl,bl
    int 10h
    push ds
    mov ax,40h
    mov ds,ax
    cmp byte ptr ds:[84h],49  ; BIOS rows - 1
    pop ds
    je t80v_rows
    mov ax,3                  ; not 50 rows: back to 80x25, Enable fails
    int 10h
    jmp short t80v_fail
t80v_rows:
""")

DATA_NEW = crlf("""; T80TALL: the allocated shadow (handle, segment) and the first logical
; pixel row shown (pan_top, a multiple of 8; 0 when nothing pans).
t80_shh dw 0
t80_shs dw 0
public pan_top
pan_top dw 0
""")

LBUF = crlf("""; T80TALL: the logical text of all 50 rows (the screen shows 25 of them).
createSeg _T80L,T80LSeg,word,public,DATA
sBegin T80LSeg
t80_lbuf db 8000 dup (0)
sEnd T80LSeg
""")

# ---- pan ---------------------------------------------------------------------

PAN_SET = crlf("""
; T80TALL: move the 25-row window. AX = requested first pixel row (XTPAN's
; escape: the helper computes exact rows). Text moves in whole cell rows:
; a move down rounds up (the rows asked for at the bottom are shown), a
; move up rounds down (the rows asked for at the top are shown). Returns
; AX = first pixel row in effect. Task time only (Control); copies 25 rows
; of logical text to the screen, converts nothing. Preserves the rest.
public t80_panset
t80_panset proc far
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    mov bx,seg pan_top
    mov ds,bx
    or ax,ax
    jns tps_lo
    xor ax,ax
tps_lo:
    cmp ax,SCREEN_HEIGHT-T40_VISROWS*8
    jle tps_hi
    mov ax,SCREEN_HEIGHT-T40_VISROWS*8
tps_hi:
    cmp ax,pan_top
    jle tps_round
    add ax,7
tps_round:
    and ax,0FFF8h
    cmp ax,pan_top
    je tps_done
    cmp enabled_flag,0
    jne tps_move
    mov pan_top,ax            ; disabled (a DOS session): no video access
    mov cl,3
    shr ax,cl
    mov bx,seg t40_vtop
    mov es,bx
    mov es:t40_vtop,ax
    mov dx,T40_COLS*2
    mul dx
    mov es:t40_voff,ax
    jmp short tps_done
tps_move:
    call cursor_hide
    mov pan_top,ax
    mov cl,3
    shr ax,cl
    call t40_pan
    call cursor_show
tps_done:
    mov ax,pan_top
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    ret
t80_panset endp
""")

QUERY_OLD = "    mov bx,es:[di]\r\n    cmp bx,QUERYESCSUPPORT\r\n    je control_ok\r\n"
QUERY_NEW = crlf("""    mov bx,es:[di]
    cmp bx,QUERYESCSUPPORT
    je t80q_ok
    cmp bx,PAN_ESC            ; T80TALL
    jne t80q_no
t80q_ok:
    jmp control_ok
t80q_no:
""")
HANDLER_OLD = "control_color:\r\n    cmp bx,GETCOLORTABLE\r\n    jne control_done\r\n"
HANDLER_NEW = crlf("""control_color:
    cmp bx,PAN_ESC            ; T80TALL: input word = first pixel row
    jne t80_not_pan           ; (0FFFFh: query); output words = first row,
    mov ax,es:[di]            ; rows shown, logical rows
    cmp ax,0FFFFh
    je t80_pan_q
    call t80_panset
t80_pan_q:
    les di,output
    mov ax,es
    or ax,di
    jnz t80_pan_out
    jmp control_ok
t80_pan_out:
    push ds
    mov ax,seg pan_top
    mov ds,ax
    mov ax,pan_top
    pop ds
    mov es:[di],ax
    mov word ptr es:[di+2],T40_VISROWS*8
    mov word ptr es:[di+4],SCREEN_HEIGHT
    jmp control_ok
t80_not_pan:
    cmp bx,GETCOLORTABLE
    jne control_done
""")

# ORowsSpanSafe: the canonical-shadow alias check covers the allocated
# shadow (both bands and the fill between them)
ORS_OLD = ("    mov ax,seg shadow_bits\r\n    mul bx\r\n    add ax,offset shadow_bits\r\n    adc dx,0\r\n")
ORS_NEW = crlf("""    push ds                   ; T80TALL: the allocated shadow
    mov ax,seg t40_slot
    mov ds,ax
    mov ax,ds:t40_sh0
    pop ds
    mul bx
""")
ORS_SIZE_OLD = "    add ax,SCREEN_W_BYTES*4*SCREEN_HEIGHT\r\n    adc dx,0\r\n"
ORS_SIZE_NEW = crlf("""    add ax,SHADOW_LO          ; T80TALL: 129,536 bytes
    adc dx,SHADOW_HI
""")


def patch_tsoft(t, kind):
    t = replace_n(t, "SCREEN_HEIGHT equ 200\r\n",
                  "SCREEN_HEIGHT equ %d              ; T80TALL: logical rows\r\n"
                  "PAN_ESC equ %05Xh                 ; T80TALL: Control escape (XTPAN's)\r\n"
                  "SHADOW_HI equ %d                  ; T80TALL: GlobalAlloc size\r\n"
                  "SHADOW_LO equ %05Xh\r\n"
                  "ALLOC_HI equ %d                   ; T80TALL: high word of the request\r\n"
                  % (ROWS, PAN_ESC, SHADOW_BYTES >> 16, SHADOW_BYTES & 0xFFFF, 7 if FAIL_ALLOC else SHADOW_BYTES >> 16),
                  1, "screen height")
    t = replace_n(t, "externFP AllocSelector\r\n",
                  "externFP AllocSelector\r\nexternFP GlobalAlloc\r\nexternFP GlobalLock\r\n"
                  "externFP GlobalUnlock\r\nexternFP GlobalFree\r\nexternA __NEXTSEG\r\n", 1, "imports")
    t = replace_n(t, "shadow_bits db 64000 dup (0)\r\n",
                  "shadow_bits db 16 dup (0)        ; T80TALL: the shadow is allocated at Enable\r\n", 1,
                  "static shadow")
    t = replace_n(t, "BITMAP <0,640,200,80,4,1,0,16000,0,0,0,0,0,0>",
                  "BITMAP <0,640,%d,80,4,1,0,%d,0,0,200,1536,0,0>" % (ROWS, ROWS * 80), 1, "shadow descriptor")
    t = replace_n(t, "BITMAP <1,640,200,80,4,1,0,16000,0,0,0,0,0,0>",
                  "BITMAP <1,640,%d,80,4,1,0,%d,0,0,0,0,0,0>" % (ROWS, ROWS * 80), 1, "physical descriptor")
    t = replace_n(t, "    dw 0300h,DT_RASDISPLAY,240,180,640,200,1,4\r\n",
                  "    dw 0300h,DT_RASDISPLAY,240,360,640,%d,1,4\r\n" % ROWS, 1, "GDIINFO size/resolution")
    for old, new in (("2400,1800,640,-200", "2400,3600,640,-400"), ("24000,18000,640,-200", "24000,36000,640,-400"),
                     ("375,900,254,-254", "375,1800,254,-508"), ("3750,9000,254,-254", "3750,18000,254,-508"),
                     ("5400,6480,254,-127", "5400,12960,254,-254")):
        t = replace_n(t, "    dw %s\r\n" % old, "    dw %s\r\n" % new, 1, "mapping extents " + old)
    t = replace_n(t, ALLOC_OLD, ALLOC_NEW, 1, "allocation")
    t = replace_n(t, CLEAR_OLD, CLEAR_NEW, 1, "shadow clear")
    t = replace_n(t, DISABLE_OLD, DISABLE_NEW, 1, "disable frees")
    t = replace_n(t, TEXT_CLEAR_OLD, TEXT_CLEAR_PAN if kind == "pan" else TEXT_CLEAR_VGA, 1, "text clear")
    t = replace_n(t, "    mov es:t40_snv,0          ; no snapshot held\r\n", VIEW_RESET, 1, "viewport reset")
    if kind == "vga":
        t = replace_n(t, VGA_MODE_OLD, VGA_MODE_NEW, 1, "VGA 80x50 mode")
    t = replace_n(t, T40.DATA_ANCHOR, T40.DATA_ANCHOR + DATA_NEW, 1, "data")
    t = replace_n(t, ORS_OLD, ORS_NEW, 1, "alias check base")
    t = replace_n(t, ORS_SIZE_OLD, ORS_SIZE_NEW, 1, "alias check size")
    if kind == "pan":
        t = replace_n(t, T40.SEG_ANCHOR, T40.SEG_ANCHOR + LBUF, 1, "logical text buffer")
        t = replace_n(t, "FlushColumns endp\r\n", "FlushColumns endp\r\n" + PAN_SET, 1, "pan")
        t = replace_n(t, QUERY_OLD, QUERY_NEW, 1, "escape query")
        t = replace_n(t, HANDLER_OLD, HANDLER_NEW, 1, "escape handler")
    return t


def patch_tcursor(t, kind):
    t = replace_n(t, "    cmp bx,200\r\n    jl tcd_y1\r\n",
                  "    cmp bx,%d                  ; T80TALL: text rows shown x 8\r\n    jl tcd_y1\r\n"
                  % (200 if kind == "pan" else 400), 1, "cursor rows")
    if kind == "pan":
        t = replace_n(t, "    externB enabled_flag\r\n", "    externB enabled_flag\r\n    externW pan_top\r\n", 1,
                      "pan_top extern")
        t = replace_n(t, "    mov ax,tc_y\r\n    sub ax,tc_hot_y\r\n    mov tc_origin_y,ax\r\n",
                      "    mov ax,tc_y\r\n    sub ax,tc_hot_y\r\n    sub ax,pan_top             ; T80TALL: screen rows\r\n"
                      "    mov tc_origin_y,ax\r\n", 1, "cursor origin")
    return t


def patch_sdib(t):
    return replace_n(t, "    cmp bx,200\r\n    jle sd_clip_bottom\r\n    mov bx,200\r\n",
                     "    cmp bx,%d                  ; T80TALL: logical rows\r\n    jle sd_clip_bottom\r\n"
                     "    mov bx,%d\r\n" % (ROWS, ROWS), 1, "DIB bottom clip")


DESCRIPTION = {"pan": "TEXT80 80x25 text over a 640x400 desktop, panned (experimental)",
               "vga": "TEXT80 VGA 80x50 text, 640x400 (experimental)"}


def patch_def(t, kind):
    t = replace_n(t, "TEXT80 80x25 color text, 640x200 (experimental)", DESCRIPTION[kind], 1, "description")
    t = replace_n(t, "IMPORTS\r\n", "IMPORTS\r\n GlobalAlloc=KERNEL.15\r\n GlobalFree=KERNEL.17\r\n"
                  " GlobalLock=KERNEL.18\r\n GlobalUnlock=KERNEL.19\r\n", 1, "imports")
    if kind == "pan":
        t = replace_n(t, " _T40 PRELOAD FIXED\r\n", " _T40 PRELOAD FIXED\r\n _T80L PRELOAD FIXED\r\n", 1,
                      "segment list")
    return t


def configure(kind):
    T80.configure()
    T40.GEOMETRY = geometry(kind)
    T40.SEGMENTS = segments(kind)
    real_tsoft, real_def = T40.patch_tsoft, T40.patch_def
    T40.patch_tsoft = lambda t: patch_tsoft(real_tsoft(t), kind)
    T40.patch_def = lambda t: patch_def(real_def(t), kind)
    real_tc = T40.patch_tcursor
    T40.patch_tcursor = lambda t: patch_tcursor(real_tc(t), kind)


def patch_staged(ega_dir, kind):
    global FAIL_ALLOC
    if kind == "panfail":
        FAIL_ALLOC, kind = True, "pan"
    configure(kind)
    done = T40.patch_staged(ega_dir)
    sd = Path(ega_dir).parent / "SDIB88.ASM"
    t = patch_sdib(T80.patch_sdib(sd.read_bytes().decode("latin-1")))
    sd.write_bytes(t.encode("latin-1"))
    done["SDIB88.ASM"] = t
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    assert SHADOW_BYTES == 129536 and (SHADOW_BYTES >> 16, SHADOW_BYTES & 0xFFFF) == (1, 0xFA00)
    for s in (ALLOC_NEW, CLEAR_NEW, DISABLE_NEW, PAN_SET, HANDLER_NEW, VGA_MODE_NEW, ORS_NEW):
        assert s.count("\r\n") == s.count("\n")
    print("T80TALL: check PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
