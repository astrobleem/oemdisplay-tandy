#!/usr/bin/env python3
"""Tandy 1000 SL/TL/RL Video II 640x200x16 edits for the TR5 driver (docs/TGA2.MD).

Usage:
  python3 src/tga2/T2PATCH.PY --check     model self-test (no emulator)

Hardware model (86Box src/video/vid_tandy.c, SL2; confirmed in 86Box with
the owner's SL2 BIOS ROMs by T2PROBE, T2MODES and T2SHOW, never yet on a
real machine):
  The BIOS has no mode for it (T2MODES: modes 00h-0Ah only). From BIOS
  mode 0Ah (640x200, 80-column CRTC timing, memory control 3DFh selecting
  the top 64KB of the 640KB shared RAM): video array register 5 bit 0 (index
  to 3DAh, value to 3DEh) switches to 640x200x16 and maps the 64KB page at
  A000h; CRTC R4=FFh, R5=06h, R6=C8h, R7=E0h, R9=00h give 200 one-line
  rows (262 lines). The page is linear: row y at y*320, packed 4 bits per
  pixel, high nibble first; the nibble selects palette (array) register
  10h+n, set here to n, so the nibble is the IRGB colour (bit 3 intensity,
  2 red, 1 green, 0 blue). The page is physical 90000h-9FFFFh: T2RESV
  keeps 90000h-9BFFFh from DOS (the BIOS keeps the rest).

Driver: the shadow keeps four 80-byte planes per row in DDK order red,
green, blue, intensity. t2_row turns each shadow byte column (8 pixels)
into 4 VRAM bytes: nibble = I<<3 | R<<2 | G<<1 | B, through a 1KB table
(t2x: byte -> four bytes, each pixel bit as a 0/1 nibble).
"""
import argparse
import sys

# --- shared assembly text (driver and T2SHOW) --------------------------------


def table_text():
    """t2x: for each byte v, four bytes; byte k holds pixel 2k (bit 7-2k of v)
    in its high nibble and pixel 2k+1 in its low nibble, each as 0 or 1."""
    lines = ["; T2PATCH: byte -> four packed-nibble bytes, one 0/1 nibble per pixel.\r\n",
             "t2x label word\r\n"]
    for v in range(256):
        out = []
        for k in range(4):
            hi = (v >> (7 - 2 * k)) & 1
            lo = (v >> (6 - 2 * k)) & 1
            out.append("%03Xh" % (hi << 4 | lo))
        lines.append("    db " + ",".join(out) + "\r\n")
    return "".join(lines)


ROW_MACRO = (
    "; T2PATCH: one shadow row segment to Video II packed pixels.\r\n"
    "; DS:SI = shadow red byte, ES:DI = VRAM byte (4 per shadow byte), BX =\r\n"
    "; shadow byte count. Shadow planes are 80 bytes apart (R,G,B,I); each\r\n"
    "; pixel's nibble is I<<3 | R<<2 | G<<1 | B. Returns SI advanced by BX, DI\r\n"
    "; by 4*BX; BX kept. Clobbers AX, CX, DX.\r\n"
    "t2_plane macro off\r\n"
    "    mov bl,[si+off]\r\n"
    "    xor bh,bh\r\n"
    "    shl bx,1\r\n"
    "    shl bx,1\r\n"
    "endm\r\n"
    "t2_row macro\r\n"
    "    local t2r_byte, t2r_done\r\n"
    "    push bx\r\n"
    "    mov cx,bx\r\n"
    "    jcxz t2r_done\r\n"
    "t2r_byte:\r\n"
    "    t2_plane 240\r\n"
    "    mov ax,cs:t2x[bx]\r\n"
    "    mov dx,cs:t2x[bx+2]\r\n"
    "    shl ax,1\r\n"
    "    shl dx,1\r\n"
    "    t2_plane 0\r\n"
    "    or ax,cs:t2x[bx]\r\n"
    "    or dx,cs:t2x[bx+2]\r\n"
    "    shl ax,1\r\n"
    "    shl dx,1\r\n"
    "    t2_plane 80\r\n"
    "    or ax,cs:t2x[bx]\r\n"
    "    or dx,cs:t2x[bx+2]\r\n"
    "    shl ax,1\r\n"
    "    shl dx,1\r\n"
    "    t2_plane 160\r\n"
    "    or ax,cs:t2x[bx]\r\n"
    "    or dx,cs:t2x[bx+2]\r\n"
    "    stosw\r\n"
    "    mov ax,dx\r\n"
    "    stosw\r\n"
    "    inc si\r\n"
    "    loop t2r_byte\r\n"
    "t2r_done:\r\n"
    "    pop bx\r\n"
    "endm\r\n"
)

# Enable: BIOS mode 0Ah, identity palette, border 0, CRTC to 200 one-line
# rows, array register 5 bit 0, clear the 64,000 visible bytes.
MODE_TEXT = (
    "    mov ax,000ah              ; T2PATCH: BIOS mode 0Ah (640x200 timing)\r\n"
    "    int 10h\r\n"
    "    xor bl,bl                 ; palette register 10h+n = n: nibble = IRGB\r\n"
    "t2m_pal:\r\n"
    "    mov dx,3dah\r\n"
    "    mov al,bl\r\n"
    "    or al,10h\r\n"
    "    out dx,al\r\n"
    "    mov dx,3deh\r\n"
    "    mov al,bl\r\n"
    "    out dx,al\r\n"
    "    inc bl\r\n"
    "    cmp bl,16\r\n"
    "    jb t2m_pal\r\n"
    "    mov dx,3dah               ; border colour (array register 2) black\r\n"
    "    mov al,2\r\n"
    "    out dx,al\r\n"
    "    mov dx,3deh\r\n"
    "    xor al,al\r\n"
    "    out dx,al\r\n"
    "    mov dx,3d4h               ; CRTC: 256+6 lines, 200 shown, one line per row\r\n"
    "    mov ax,0ff04h\r\n"
    "    out dx,ax\r\n"
    "    mov ax,00605h\r\n"
    "    out dx,ax\r\n"
    "    mov ax,0c806h\r\n"
    "    out dx,ax\r\n"
    "    mov ax,0e007h\r\n"
    "    out dx,ax\r\n"
    "    mov ax,00009h\r\n"
    "    out dx,ax\r\n"
    "    mov ax,0000ch\r\n"
    "    out dx,ax\r\n"
    "    mov ax,0000dh\r\n"
    "    out dx,ax\r\n"
    "    mov dx,3dah               ; array register 5 bit 0: 640x200x16, page at A000h\r\n"
    "    mov al,5\r\n"
    "    out dx,al\r\n"
    "    mov dx,3deh\r\n"
    "    mov al,1\r\n"
    "    out dx,al\r\n"
    "    push es\r\n"
    "    mov ax,0a000h\r\n"
    "    mov es,ax\r\n"
    "    xor di,di\r\n"
    "    xor ax,ax\r\n"
    "    mov cx,32000\r\n"
    "    cld\r\n"
    "    rep stosw\r\n"
    "    pop es\r\n"
)
# Before the BIOS sets the old mode again: leave 640x200x16.
DISABLE_TEXT = (
    "    mov dx,3dah               ; T2PATCH: array register 5 = 0\r\n"
    "    mov al,5\r\n"
    "    out dx,al\r\n"
    "    mov dx,3deh\r\n"
    "    xor al,al\r\n"
    "    out dx,al\r\n"
)

# --- host model -------------------------------------------------------------


def t2x():
    t = []
    for v in range(256):
        t.append([((v >> (7 - 2 * k)) & 1) << 4 | ((v >> (6 - 2 * k)) & 1) for k in range(4)])
    return t


def model_row(shadow, row, vram):
    """t2_row over a whole row (BX = 80): the macro's arithmetic, word by word."""
    T = t2x()
    si, di = row * 320, row * 320
    for _ in range(80):
        def words(v):
            b = T[v]
            return b[0] | b[1] << 8, b[2] | b[3] << 8
        ax, dx = words(shadow[si + 240])
        for off in (0, 80, 160):
            ax, dx = (ax << 1) & 0xffff, (dx << 1) & 0xffff
            a2, d2 = words(shadow[si + off])
            ax, dx = ax | a2, dx | d2
        vram[di:di + 4] = bytes((ax & 255, ax >> 8, dx & 255, dx >> 8))
        si += 1
        di += 4


def shadow_pixel(shadow, y, x):
    base = y * 320 + (x >> 3)
    bit = 7 - (x & 7)
    r = (shadow[base] >> bit) & 1
    g = (shadow[base + 80] >> bit) & 1
    b = (shadow[base + 160] >> bit) & 1
    i = (shadow[base + 240] >> bit) & 1
    return (i << 3) | (r << 2) | (g << 1) | b


def sl2_pixel(vram, y, x, palette=tuple(range(16))):
    """86Box vid_render, 640x200x16: word at memaddr*2 big-endian, four
    pixels from bit 12 down; colour = array[nibble + 16]."""
    word_index = x >> 2
    hi, lo = vram[y * 320 + word_index * 2], vram[y * 320 + word_index * 2 + 1]
    dat = hi << 8 | lo
    return palette[(dat >> (12 - 4 * (x & 3))) & 0xf]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    import random
    rnd = random.Random(2)
    shadow = bytes(rnd.randrange(256) for _ in range(64000))
    vram = bytearray(64000)
    for y in range(200):
        model_row(shadow, y, vram)
    bad = sum(sl2_pixel(vram, y, x) != shadow_pixel(shadow, y, x) for y in range(200) for x in range(640))
    assert bad == 0, bad
    # negative control: planes in the wrong order are caught
    swapped = bytes(shadow[(i // 320) * 320 + ((i % 320) + 80) % 320] for i in range(64000))
    vram2 = bytearray(64000)
    for y in range(200):
        model_row(swapped, y, vram2)
    assert sum(sl2_pixel(vram2, y, x) != shadow_pixel(shadow, y, x) for y in range(4) for x in range(640)) > 0
    assert table_text().count("\r\n") == 258
    print("T2PATCH: model PASS (t2_row reproduces every shadow colour through the 86Box SL2 "
          "640x200x16 decode, 128,000 pixels; a plane-order error is caught)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
