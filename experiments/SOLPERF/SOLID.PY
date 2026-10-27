"""Private HPXY solid eight-pixel conversion experiment; no package changes.

Apply after the ordinary XRBUILD overlay. Keep all clipping, bank wrap,
cursor exclusion, staging, and mixed-pixel conversion exactly as before.
"""
from pathlib import Path


def patch(renderer):
    path = Path(renderer) / "EGA/TSOFT.ASM"
    raw = path.read_bytes()
    old = b"    mov dh,[si+240]\r\n    rept 4\r\n"
    new = """    mov dh,[si+240]
    ; Each plane must be entirely zero or entirely one. INC maps those
    ; two values to 1 and 0; every other input is above 1 (unsigned).
    mov al,ah
    inc al
    cmp al,1
    ja xyc_mixed
    mov al,bl
    inc al
    cmp al,1
    ja xyc_mixed
    mov al,bh
    inc al
    cmp al,1
    ja xyc_mixed
    mov al,dh
    inc al
    cmp al,1
    ja xyc_mixed
    ; All eight pixels have the same RGBI value. Convert once and emit
    ; four identical bytes. A group is four-byte aligned within its bank.
    get_nibble
    mov dl,al
    shl al,1
    shl al,1
    shl al,1
    shl al,1
    or al,dl
    mov ah,al
    stosw
    stosw
    jmp xyc_converted
xyc_mixed:
    rept 4
""".replace("\n", "\r\n").encode("ascii")
    if raw.count(old) != 1:
        raise RuntimeError("Expected one current XY group converter")
    raw = raw.replace(old, new)
    old = b"    endm\r\n    cmp word ptr ss:[bp-18],0\r\n"
    if raw.count(old) != 1:
        raise RuntimeError("Expected one XY post-conversion branch")
    raw = raw.replace(old, b"    endm\r\nxyc_converted:\r\n    cmp word ptr ss:[bp-18],0\r\n")
    path.write_bytes(raw)
