#!/usr/bin/env python3
"""TEXT80 edits: Windows 3.0 in 80x25 colour text from a 640x200x16 shadow
(docs/TEXT80.MD). Measurement and experimental builds only.

  python3 src/text80/T80PATCH.PY --check     self-test (no emulator)

BUILDT80.PY runs BUILD88's accepted 320x200x16 pipeline and, after every
port step and before the first assembly, applies:

1. geometry640(): the 640x200 edits of the audited 640x200x4 profile
   (src/tandysw/MODEPROF.PY) that are about geometry, not colour: screen
   width and shadow (64,000 bytes, four 80-byte planes per row), BITMAP
   descriptors, GDIINFO size and 96x48 aspect, line-style distances, the
   shadow clear, and SDIB88's screen bounds. The 16-colour mapper stays.
   The 640x200x4 profile's palette and four-colour flush are not used.
2. T40PATCH, configured for 80 columns: the same presenter source
   (T40PRES/T40DATA with T40_COLS=80, 14-byte hint slots so two hints per
   cell and the state fit one segment), text-call hints, hint moves,
   snapshot-diff flushes and clip-bounded text flushes.
3. Mode: BIOS mode 03h (80x25 colour), blink off on every adapter class
   that has it: CGA-compatible mode register 3D8h = 09h (and BIOS 40:65h),
   and on EGA/VGA (detected with INT 10h AH=12h BL=10h) the attribute
   controller via INT 10h AX=1003h BL=0. Hardware cursor hidden.
4. Cursor: the hot spot's cell, attribute XOR 77h, at 80 columns.

Resources: BUILDT80 stages the CGA (96x48) font resources and 2-pixel
borders exactly as the 640x200 profiles do and requires the result to be
their pinned resource hash.
"""
import argparse
import importlib.machinery
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T40 = importlib.machinery.SourceFileLoader("t40patch_t80", str(HERE.parent / "txt40" / "T40PATCH.PY")).load_module()
crlf, replace_n = T40.crlf, T40.replace_n

COLS = 80
GEOMETRY = {"T40_COLS": 80, "T40_NROWS": 25, "T40_SLOTB": 14, "T40_SNAPB": 8192}

# (old, new) on the final staged TSOFT.ASM, each exactly once; from the
# 640x200x4 profile's list without its colour-specific entries.
GEOM640 = [
    ("SCREEN_WIDTH equ 320", "SCREEN_WIDTH equ 640"),
    ("SCREEN_W_BYTES equ 40", "SCREEN_W_BYTES equ 80"),
    ("shadow_bits db 32000 dup (0)", "shadow_bits db 64000 dup (0)"),
    ("BITMAP <0,320,200,40,4,1,0,8000", "BITMAP <0,640,200,80,4,1,0,16000"),
    ("BITMAP <1,320,200,40,4,1,0,8000", "BITMAP <1,640,200,80,4,1,0,16000"),
    ("dw 0300h,DT_RASDISPLAY,240,180,320,200,1,4", "dw 0300h,DT_RASDISPLAY,240,180,640,200,1,4"),
    ("2400,1800,320,-200", "2400,1800,640,-200"),
    ("24000,18000,320,-200", "24000,18000,640,-200"),
    ("mov cx,16000", "mov cx,32000"),
    ("HYPOTENUSE\t=\t61", "HYPOTENUSE\t=\t13"),
    ("Y_MAJOR_DIST\t=\t48", "Y_MAJOR_DIST\t=\t12"),
    ("X_MAJOR_DIST\t=\t38", "X_MAJOR_DIST\t=\t5"),
    ("dw 1200,900,406,-254", "dw 375,900,254,-254"),
    ("dw 12000,9000,406,-254", "dw 3750,9000,254,-254"),
    ("dw 17280,12960,406,-254", "dw 5400,6480,254,-127"),
    ("dw 96,72,DC_IgnoreDFNP", "dw 96,48,DC_IgnoreDFNP"),
]

ENABLE_NEW = crlf("""    mov ax,3                  ; T80PATCH: BIOS 80x25 colour text
    int 10h
    mov dx,3d8h
    mov al,09h                ; CGA/Tandy: 80 columns, colour, video on, blink off
    out dx,al
    push ds
    mov ax,40h
    mov ds,ax
    mov byte ptr ds:[65h],09h ; BIOS copy of the mode register
    pop ds
    mov ah,12h                ; EGA/VGA present? (BL stays 10h otherwise)
    mov bl,10h
    int 10h
    cmp bl,10h
    je t80e_noega
    mov ax,1003h              ; EGA/VGA: attribute bit 7 = bright background
    xor bl,bl
    int 10h
t80e_noega:
    mov ah,1
    mov cx,2000h              ; hide the hardware cursor
    int 10h
    mov ax,0b800h
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,T40_NCELL
    cld
    rep stosw
    mov ax,seg t40_slot       ; forget every hint and shown state
    mov es,ax                 ; (t40_reset inline: TEnable is in
    xor di,di                 ; another code segment)
    xor ax,ax
    mov cx,T40_NCELL*(T40_CELLB+2)/2
    rep stosw
    mov es:t40_snv,0          ; no snapshot held
""")

TC_NEW = T40.TC_NEW.replace("    cmp ax,320\r\n", "    cmp ax,640\r\n").replace(
    "    mov dx,40\r\n", "    mov dx,80\r\n").replace("; T40PATCH: text-mode cursor.", "; T80PATCH: text-mode cursor (80 columns).")


def geometry640(t):
    for old, new in GEOM640:
        t = replace_n(t, old, new, 1, "640: " + old)
    return t


def patch_sdib(t):
    import re
    n = len(re.findall(r"(?m)^(\s*(?:cmp|mov)\s+\w+,)320(\s*(?:;[^\r\n]*)?)\r$", t))
    if n != 2:
        raise SystemExit(f"T80PATCH: SDIB88 screen-width bounds: {n} lines, expected 2")
    return re.sub(r"(?m)^(\s*(?:cmp|mov)\s+\w+,)320(\s*(?:;[^\r\n]*)?)\r$", r"\g<1>640\2\r", t)


def configure():
    """Point T40PATCH's module-level parts at the 80-column values."""
    T40.GEOMETRY = dict(GEOMETRY)
    T40.ENABLE_NEW = ENABLE_NEW
    T40.TC_NEW = TC_NEW
    real_def = T40.patch_def

    def patch_def(t):
        t = real_def(t)
        return replace_n(t, "TXT40 CGA 40x25 color text (experimental)",
                         "TEXT80 80x25 color text, 640x200 (experimental)", 1, "description")
    T40.patch_def = patch_def
    real_tsoft = T40.patch_tsoft
    T40.patch_tsoft = lambda t: geometry640(real_tsoft(t))


def patch_staged(ega_dir):
    configure()
    done = T40.patch_staged(ega_dir)
    sd = Path(ega_dir).parent / "SDIB88.ASM"
    t = patch_sdib(sd.read_bytes().decode("latin-1"))
    sd.write_bytes(t.encode("latin-1"))
    done["SDIB88.ASM"] = t
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    assert "cmp ax,640" in TC_NEW and "mov dx,80" in TC_NEW and "cmp ax,320" not in TC_NEW
    assert ENABLE_NEW.count("\r\n") == ENABLE_NEW.count("\n")
    print("T80PATCH: check PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
