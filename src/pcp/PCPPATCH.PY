#!/usr/bin/env python3
"""Plantronics ColorPlus 320x200x16 edits for the TR5 driver (docs/PCP.MD).

Usage:
  python3 src/pcp/PCPPATCH.PY --check     model self-test (no emulator)

BUILDPCP.PY applies patch_staged() to BUILD88's fully staged EGA/TSOFT.ASM
and EGA/TCURSOR.ASM after every TR5 port step. PCPTEST.PY assembles the
exact same conversion text into a DOS harness. Every edit must match an
exact count or nothing is written.

Hardware model (86Box vid_cga_colorplus.c, seasip.info notes, WINPCP notes):
  CGA mode 04h, then port 3DDh = 10h. 32KB at B800h. Plane 0 at 0000h,
  plane 1 at 4000h; each is CGA 320x200 2bpp: even rows at +0000h, odd rows
  at +2000h, 80 bytes per row, leftmost pixel in bits 7-6.
  Plane 0 field = (R << 1) | G, plane 1 field = (B << 1) | I.

Driver model: the shadow keeps four 40-byte planes per row in DDK order
0=red, 1=green, 2=blue, 3=intensity (see get_nibble in V1.ASM). So one
shadow byte column becomes two VRAM bytes per plane:
  plane 0 word = spread(R) << 1 | spread(G)
  plane 1 word = spread(B) << 1 | spread(I)
where spread() moves bit k to bit 2k. High byte is stored first.
"""
import argparse
import sys
from pathlib import Path


def spread(b):
    v = 0
    for k in range(8):
        if b & (1 << k):
            v |= 1 << (2 * k)
    return v


def spread_table_text():
    lines = ["; PCPPATCH: bit k -> bit 2k, for interleaving two shadow planes.\r\n",
             "pp_spread label word\r\n"]
    for row in range(0, 256, 8):
        vals = ",".join("%05Xh" % spread(b) for b in range(row, row + 8))
        lines.append("    dw " + vals + "\r\n")
    return "".join(lines)


CONVERT_MACROS = (
    "; PCPPATCH: one shadow byte column -> Plantronics plane words.\r\n"
    "; DS:SI = shadow byte (planes at +0,+40,+80,+120), ES:DI = plane 0.\r\n"
    "; Writes ES:DI and ES:DI+4000h, advances DI by 2. Clobbers AX, BX.\r\n"
    "pp_half macro planeA,planeB\r\n"
    "    mov bl,[si+planeA]\r\n"
    "    xor bh,bh\r\n"
    "    shl bx,1\r\n"
    "    mov ax,cs:pp_spread[bx]\r\n"
    "    shl ax,1\r\n"
    "    mov bl,[si+planeB]\r\n"
    "    xor bh,bh\r\n"
    "    shl bx,1\r\n"
    "    or ax,cs:pp_spread[bx]\r\n"
    "    xchg ah,al\r\n"
    "endm\r\n"
    "pp_byte macro\r\n"
    "    pp_half 0,40\r\n"
    "    stosw\r\n"
    "    pp_half 80,120\r\n"
    "    mov es:[di+3ffeh],ax\r\n"
    "endm\r\n"
)

TANDY_CONVERT = (
    "    mov ah,[si]\r\n"
    "    mov bl,[si+40]\r\n"
    "    mov bh,[si+80]\r\n"
    "    mov dh,[si+120]\r\n"
    "    rept 4\r\n"
    "      get_nibble\r\n"
    "      shl al,1\r\n"
    "      shl al,1\r\n"
    "      shl al,1\r\n"
    "      shl al,1\r\n"
    "      mov dl,al\r\n"
    "      get_nibble\r\n"
    "      or al,dl\r\n"
    "      stosb\r\n"
    "    endm\r\n"
)


def row_block(row):
    return ("    mov ax,%s\r\n    and ax,3\r\n    mov cl,13\r\n    shl ax,cl\r\n"
            "    mov di,ax\r\n    mov ax,%s\r\n    shr ax,1\r\n    shr ax,1\r\n"
            "    mov cx,160\r\n    mul cx\r\n    add di,ax\r\n") % (row, row)


def pcp_row_block(row):
    return ("    mov ax,%s\r\n    and ax,1\r\n    mov cl,13\r\n    shl ax,cl\r\n"
            "    mov di,ax\r\n    mov ax,%s\r\n    shr ax,1\r\n"
            "    mov cx,80\r\n    mul cx\r\n    add di,ax\r\n") % (row, row)


ENABLE_OLD = "    mov ax,9\r\n    int 10h\r\n"
ENABLE_NEW = ("    mov ax,4                  ; PCPPATCH: CGA 320x200 graphics\r\n"
              "    int 10h\r\n"
              "    mov dx,3ddh\r\n"
              "    mov al,10h                ; Plantronics 320x200x16 on\r\n"
              "    out dx,al\r\n")
DISABLE_OLD = ("    mov al,old_mode\r\n    xor ah,ah\r\n    int 10h\r\n")
DISABLE_NEW = ("    mov dx,3ddh               ; PCPPATCH: Plantronics extensions off\r\n"
               "    xor al,al\r\n"
               "    out dx,al\r\n" + DISABLE_OLD)

MACRO_ANCHOR = "public FlushShadow,FlushRows\r\n"


def replace_n(text, old, new, want, name):
    n = text.count(old)
    if n != want:
        raise SystemExit(f"PCPPATCH: '{name}' matched {n} times, expected {want}")
    return text.replace(old, new)


def patch_tsoft(t):
    t = replace_n(t, MACRO_ANCHOR, CONVERT_MACROS + spread_table_text() + MACRO_ANCHOR, 1, "macros/table")
    t = replace_n(t, row_block("bp"), pcp_row_block("bp"), 2, "row address (bp)")
    t = replace_n(t, row_block("ss:[bp-2]"), pcp_row_block("ss:[bp-2]"), 2, "row address (local)")
    t = replace_n(t, "    mov ax,ss:[bp-6]\r\n    shl ax,1\r\n    shl ax,1\r\n    add di,ax\r\n",
                  "    mov ax,ss:[bp-6]\r\n    shl ax,1                  ; PCPPATCH: 2 bytes per column\r\n    add di,ax\r\n",
                  2, "column offset")
    t = replace_n(t, TANDY_CONVERT, "    pp_byte\r\n", 4, "byte conversion")
    # Cursor retention footprints are physical byte columns of one plane row.
    t = replace_n(t, "    xor cx,cx\r\n    mov dx,160\r\n    call cursor_begin_retain\r\n",
                  "    xor cx,cx\r\n    mov dx,80                 ; PCPPATCH: plane row bytes\r\n    call cursor_begin_retain\r\n",
                  1, "retain rows width")
    t = replace_n(t, "    shl cx,1\r\n    shl dx,1\r\n    shl cx,1\r\n    shl dx,1\r\n    lea si,[bp-12]\r\n",
                  "    shl cx,1                  ; PCPPATCH: 2 plane bytes per column\r\n    shl dx,1\r\n    lea si,[bp-12]\r\n",
                  1, "retain columns scale")
    t = replace_n(t, ENABLE_OLD, ENABLE_NEW, 1, "enable mode")
    t = replace_n(t, DISABLE_OLD, DISABLE_NEW, 1, "disable mode")
    if "mov cx,160\r\n" in t or "mov dx,160\r\n" in t:
        raise SystemExit("PCPPATCH: Tandy row stride left in TSOFT")
    return t


TC_SCAN_OLD = ("    mov bx,ax\r\n    and bx,3\r\n    mov cl,13\r\n    shl bx,cl\r\n"
               "    shr ax,1\r\n    shr ax,1\r\n    mov dx,160\r\n    mul dx\r\n")
TC_SCAN_NEW = ("    mov bx,ax                 ; PCPPATCH: CGA even/odd banks\r\n"
               "    and bx,1\r\n    mov cl,13\r\n    shl bx,cl\r\n"
               "    shr ax,1\r\n    mov dx,80\r\n    mul dx\r\n")

TC_ERASE_OLD = ("    add di,tc_save_xbyte\r\n    mov cx,tc_save_bytes\r\n    cld\r\n    rep movsb\r\n")
TC_ERASE_NEW = ("    add di,tc_save_xbyte\r\n    mov dx,di                 ; PCPPATCH: plane 0 then plane 1\r\n"
                "    mov cx,tc_save_bytes\r\n    cld\r\n    rep movsb\r\n"
                "    mov di,dx\r\n    add di,4000h\r\n    mov cx,tc_save_bytes\r\n    rep movsb\r\n")

TC_GEOM_OLD = ("    mov ax,tc_left\r\n    shr ax,1\r\n    mov tc_save_xbyte,ax\r\n"
               "    mov bx,tc_right\r\n    dec bx\r\n    shr bx,1\r\n")
TC_GEOM_NEW = ("    mov ax,tc_left\r\n    shr ax,1\r\n    shr ax,1                  ; PCPPATCH: 4 pixels per byte\r\n"
               "    mov tc_save_xbyte,ax\r\n"
               "    mov bx,tc_right\r\n    dec bx\r\n    shr bx,1\r\n    shr bx,1\r\n")

TC_SAVE_OLD = ("    add di,tc_save_xbyte\r\n    mov cx,tc_save_bytes\r\ntcd_save_byte:\r\n"
               "    mov al,es:[di]\r\n    mov [si],al\r\n    inc si\r\n    inc di\r\n    loop tcd_save_byte\r\n")
TC_SAVE_NEW = ("    add di,tc_save_xbyte\r\n    mov cx,tc_save_bytes\r\ntcd_save_byte:\r\n"
               "    mov al,es:[di]\r\n    mov [si],al\r\n    inc si\r\n    inc di\r\n    loop tcd_save_byte\r\n"
               "    sub di,tc_save_bytes      ; PCPPATCH: same bytes of plane 1\r\n"
               "    add di,4000h\r\n    mov cx,tc_save_bytes\r\ntcd_save_byte1:\r\n"
               "    mov al,es:[di]\r\n    mov [si],al\r\n    inc si\r\n    inc di\r\n    loop tcd_save_byte1\r\n")

TC_PIXEL_OLD = (
    "    mov ax,tc_work_x\r\n    shr ax,1\r\n    mov di,tc_row_offset\r\n    add di,ax\r\n"
    "    mov dl,es:[di]\r\n    mov al,dl\r\n    test tc_work_x,1\r\n    jnz tcd_low_read\r\n"
    "    mov cl,4\r\n    shr al,cl\r\ntcd_low_read:\r\n    and al,0Fh\r\n"
    "    test tc_and[si],bl\r\n    jnz tcd_and_done\r\n    xor al,al\r\ntcd_and_done:\r\n"
    "    test tc_xor[si],bl\r\n    jz tcd_xor_done\r\n    xor al,0Fh\r\ntcd_xor_done:\r\n"
    "    test tc_work_x,1\r\n    jnz tcd_low_write\r\n    mov cl,4\r\n    shl al,cl\r\n"
    "    and dl,0Fh\r\n    jmp short tcd_write\r\ntcd_low_write:\r\n    and dl,0F0h\r\n"
    "tcd_write:\r\n    or al,dl\r\n    mov es:[di],al\r\n")
TC_PIXEL_NEW = (
    "    ; PCPPATCH: AND->color 0 and XOR->color^0Fh act bitwise, so apply\r\n"
    "    ; them to the pixel's 2-bit field in both planes without decoding.\r\n"
    "    mov ax,tc_work_x\r\n    mov cx,ax\r\n    shr ax,1\r\n    shr ax,1\r\n"
    "    mov di,tc_row_offset\r\n    add di,ax\r\n"
    "    and cl,3\r\n    shl cl,1\r\n    mov dl,0C0h\r\n    shr dl,cl\r\n"
    "    mov al,es:[di]\r\n    mov ah,es:[di+4000h]\r\n"
    "    test tc_and[si],bl\r\n    jnz tcd_and_done\r\n"
    "    mov dh,dl\r\n    not dh\r\n    and al,dh\r\n    and ah,dh\r\ntcd_and_done:\r\n"
    "    test tc_xor[si],bl\r\n    jz tcd_xor_done\r\n    xor al,dl\r\n    xor ah,dl\r\ntcd_xor_done:\r\n"
    "    mov es:[di],al\r\n    mov es:[di+4000h],ah\r\n")


def patch_tcursor(t):
    t = replace_n(t, "    tc_saved        db 544 dup (0)\r\n",
                  "    tc_saved        db 576 dup (0)    ; PCPPATCH: 32 rows x 9 bytes x 2 planes\r\n",
                  1, "save buffer")
    t = replace_n(t, TC_SCAN_OLD, TC_SCAN_NEW, 1, "tc_scan")
    t = replace_n(t, TC_ERASE_OLD, TC_ERASE_NEW, 1, "tc_erase")
    t = replace_n(t, TC_GEOM_OLD, TC_GEOM_NEW, 1, "save geometry")
    t = replace_n(t, TC_SAVE_OLD, TC_SAVE_NEW, 1, "save planes")
    t = replace_n(t, TC_PIXEL_OLD, TC_PIXEL_NEW, 1, "pixel ops")
    # Retain lease checks: physical columns are one plane row (80 bytes);
    # saved length per plane is rows*bytes <= 288 (576 / 2).
    t = replace_n(t, "    cmp dx,160\r\n    ck_require jbe,ckb_legacy\r\n",
                  "    cmp dx,80                 ; PCPPATCH\r\n    ck_require jbe,ckb_legacy\r\n",
                  2, "retain column limits")
    t = replace_n(t, "    cmp cx,160\r\n    ck_require jb,ckb_legacy\r\n",
                  "    cmp cx,80                 ; PCPPATCH\r\n    ck_require jb,ckb_legacy\r\n",
                  1, "retain column origin")
    t = replace_n(t, "    cmp ax,544\r\n", "    cmp ax,288                ; PCPPATCH: per plane\r\n",
                  1, "retain buffer length")
    if "160" in t.replace("tc_x            dw 160", ""):
        raise SystemExit("PCPPATCH: a Tandy 160 constant is left in TCURSOR")
    return t


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


# ---- host reference models (used by --check and PCPTEST.PY) -------------
IRGB_FROM_IDX = [0, 2, 4, 6, 8, 10, 12, 14, 1, 3, 5, 7, 9, 11, 13, 15]  # 86Box cols16


def shadow_pixel(shadow, y, x):
    """IRGB nibble the TR5 Tandy flush would emit for pixel (x,y)."""
    base = y * 160 + (x >> 3)
    bit = 7 - (x & 7)
    r = (shadow[base] >> bit) & 1
    g = (shadow[base + 40] >> bit) & 1
    b = (shadow[base + 80] >> bit) & 1
    i = (shadow[base + 120] >> bit) & 1
    return (i << 3) | (r << 2) | (g << 1) | b


def pcp_pixel(vram, y, x):
    """IRGB color 86Box's ColorPlus renderer shows for pixel (x,y)."""
    off = (y & 1) * 0x2000 + (y >> 1) * 80 + (x >> 2)
    sh = (3 - (x & 3)) * 2
    f0 = (vram[off] >> sh) & 3
    f1 = (vram[off + 0x4000] >> sh) & 3
    return IRGB_FROM_IDX[f0 | (f1 << 2)]


def model_flush(shadow):
    vram = bytearray(0x8000)
    for y in range(200):
        di = (y & 1) * 0x2000 + (y >> 1) * 80
        for xb in range(40):
            s = y * 160 + xb
            w0 = (spread(shadow[s]) << 1) | spread(shadow[s + 40])
            w1 = (spread(shadow[s + 80]) << 1) | spread(shadow[s + 120])
            vram[di] = w0 >> 8
            vram[di + 1] = w0 & 255
            vram[di + 0x4000] = w1 >> 8
            vram[di + 0x4001] = w1 & 255
            di += 2
    return vram


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    import random
    rnd = random.Random(1512)
    shadow = bytes(rnd.randrange(256) for _ in range(32000))
    vram = model_flush(shadow)
    bad = sum(pcp_pixel(vram, y, x) != shadow_pixel(shadow, y, x)
              for y in range(200) for x in range(320))
    assert bad == 0, bad
    print("PCPPATCH: model PASS (spread/interleave reproduces every shadow color "
          "through the 86Box ColorPlus decode, 64,000 pixels)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
