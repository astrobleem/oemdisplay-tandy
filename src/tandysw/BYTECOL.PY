#!/usr/bin/env python3
"""Exact-pinned, synchronous byte-column conversion over the safe-copy baseline.

Only EGA/TSOFT.ASM is changed, after MODEPROF and REPCOPY88. FlushShadow and
FlushRows retain their exact source; only TBitBlt and TPixel select the new
FlushColumns path. Build success does not establish benefit or acceptance.
"""
from pathlib import Path
import hashlib

EXPECTED = {
    "320x200x16": "52e0b385cd05899cce7e5d443b9f04d0084a00eb2eea5c77b741a394d29cafdf",
    "640x200x4": "396c8ca5c742697f33e1fc1d97000f56ac95dfd41cc92065a6e7322351a74e97",
    "160x200x16": "9936a30c5b31b80745024bd8c990d0f1e1fae05b4ebe16ab05e9d5ccaa4fe230",
    "320x200x4": "697c650365020d8959f0e86b26343c8ff4ada9b01e41910a652516a6cbafd350",
    "640x200x2": "a0b9dc8ac38047fcd7ec01a40f4e78fe4e7d0019b3bfc9edd3483acf1ea81d11",
}
PHYSICAL_BYTES = {"320x200x16": 4, "640x200x4": 2,
                  "160x200x16": 4, "320x200x4": 2, "640x200x2": 1}


def normalized(path):
    return Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\x1a", b"").decode("latin1")


def sha(text):
    return hashlib.sha256(text.encode("latin1")).hexdigest()


def write_dos(path, text):
    Path(path).write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1"))


def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Expected exactly one BYTECOL anchor: " + repr(old))
    return text.replace(old, new)


def helper(original, mode):
    # Reuse the exact profiled bank formula and conversion body, changing
    # only row/column bounds and names. The original helper is not edited.
    row = original.split("flush_row:\n", 1)[1].split("flush_next_row:\n", 1)[0]
    row = row.replace("    mov ax,bp\n", "    mov ax,ss:[bp-2]\n")
    width_bytes = int(mode.split("x")[0]) // 8
    row = once(row, "    mov cx," + str(width_bytes) + "\nflush_byte:\n",
               "    mov ax,ss:[bp-6]\n" +
               "    shl ax,1\n" * (PHYSICAL_BYTES[mode].bit_length()-1) +
               "    add di,ax\n    mov cx,ss:[bp-8]\ncols_byte:\n")
    row = row.replace("flush_byte", "cols_byte").replace("flush_next_row", "cols_next_row")
    return """
; BYTECOL: synchronous logical-byte rectangle, independently clamped.
; AX=first row, BX=exclusive last row, CX=first byte, DX=exclusive last byte.
; Signed bounds; one logical byte represents eight horizontal pixels.
; Preserve all GPRs/segments/SP; CLD and enabled/empty behavior match FlushRows.
; Private SS:BP locals: -2 row, -4 last row, -6 first byte, -8 byte count,
; -10 shadow stride minus byte count. Never assume DS equals SS.
public FlushColumns
FlushColumns proc near
    cmp enabled_flag,0
    jne cols_start
    ret
cols_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bp,sp
    sub sp,10
    cmp ax,0
    jge cols_first_row
    xor ax,ax
cols_first_row:
    cmp bx,SCREEN_HEIGHT
    jle cols_last_row
    mov bx,SCREEN_HEIGHT
cols_last_row:
    cmp cx,0
    jge cols_first_byte
    xor cx,cx
cols_first_byte:
    cmp dx,SCREEN_W_BYTES
    jle cols_last_byte
    mov dx,SCREEN_W_BYTES
cols_last_byte:
    call cursor_hide
    cld
    cmp ax,bx
    jl cols_check_bytes
    jmp cols_finished
cols_check_bytes:
    cmp cx,dx
    jl cols_nonempty
    jmp cols_finished
cols_nonempty:
    mov ss:[bp-2],ax
    mov ss:[bp-4],bx
    mov ss:[bp-6],cx
    sub dx,cx
    mov ss:[bp-8],dx
    mov bx,SCREEN_W_BYTES*4
    sub bx,dx
    mov ss:[bp-10],bx
    mov bx,SCREEN_W_BYTES*4
    mul bx
    mov si,ax
    add si,cx
    mov ax,seg shadow_bits
    mov ds,ax
    mov ax,0b800h
    mov es,ax
cols_row:
""" + row + """cols_next_row:
    add si,ss:[bp-10]
    inc word ptr ss:[bp-2]
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jae cols_finished
    jmp cols_row
cols_finished:
    mov sp,bp
    pop es
    pop ds
    call cursor_show
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
FlushColumns endp
"""


def port(renderer, mode):
    path = Path(renderer) / "EGA/TSOFT.ASM"
    original = normalized(path)
    if sha(original) != EXPECTED[mode]:
        raise RuntimeError("Unaudited BYTECOL input " + str(path) + ": " + sha(original))
    added_helper = helper(original, mode)
    text = once(original, "FlushShadow endp\n", "FlushShadow endp\n" + added_helper)
    begin, end = text.index("cProc TBitBlt,"), text.index("cProc TOutput,")
    blt = text[begin:end]
    blt = once(blt, "    je TBitBlt_done\n", "    jne TBitBlt_dirty\n    jmp TBitBlt_done\nTBitBlt_dirty:\n")
    blt = once(blt, "    push ax\n    push bx\n", "    push ax\n    push bx\n    push cx\n    push dx\n")
    blt = once(blt, "    cmp ax,SCREEN_WIDTH\n    jg TBitBlt_full\n", "    cmp ax,SCREEN_WIDTH\n    jg TBitBlt_full\n    mov dx,ax\n")
    blt = once(blt, "    call FlushRows\n", """    ; Proven in-screen geometry cannot overflow the byte rounding.
    ; Full-width spans retain the original FlushRows fast path.
    add dx,7
    shr dx,1
    shr dx,1
    shr dx,1
    mov cx,dstx
    shr cx,1
    shr cx,1
    shr cx,1
    or cx,cx
    jne TBitBlt_columns
    cmp dx,SCREEN_W_BYTES
    jne TBitBlt_columns
    call FlushRows
    jmp short TBitBlt_flushed
TBitBlt_columns:
    call FlushColumns
""")
    blt = once(blt, "    pop bx\n    pop ax\n", "    pop dx\n    pop cx\n    pop bx\n    pop ax\n")
    text = text[:begin] + blt + text[end:]
    begin, end = text.index("cProc TPixel,"), text.index("cProc TScanLR,")
    pixel = text[begin:end]
    pixel = once(pixel, "    push ax\n    push bx\n", "    push ax\n    push bx\n    push cx\n    push dx\n")
    pixel = once(pixel, "    xor ax,ax\n    xor bx,bx\n", "    xor ax,ax\n    xor bx,bx\n    xor cx,cx\n    xor dx,dx\n")
    pixel = once(pixel, "    inc bx\nTPixel_flush:\n    call FlushRows\n", """    inc bx
    mov cx,x
    shr cx,1
    shr cx,1
    shr cx,1
    mov dx,cx
    inc dx
TPixel_flush:
    call FlushColumns
""")
    pixel = once(pixel, "    pop bx\n    pop ax\n", "    pop dx\n    pop cx\n    pop bx\n    pop ax\n")
    text = text[:begin] + pixel + text[end:]
    old_helper = original.split("public FlushShadow,FlushRows\n", 1)[1].split("FlushShadow endp\n", 1)[0]
    if text.split("public FlushShadow,FlushRows\n", 1)[1].split("FlushShadow endp\n", 1)[0] != old_helper:
        raise RuntimeError("BYTECOL modified the original full-width helper")
    # All validation finishes before the sole staged-file write.
    write_dos(path, text)
    return {"feature": "synchronous logical-byte columns", "mode": mode,
            "changed_staged_files": ["EGA/TSOFT.ASM"],
            "input_normalized_sha256": EXPECTED[mode],
            "output_normalized_sha256": sha(text),
            "helper_normalized_sha256": sha(added_helper),
            "physical_bytes_per_logical_byte": PHYSICAL_BYTES[mode],
            "preserved": ["FlushShadow", "FlushRows", "identity SRCCOPY full resync",
                          "unknown BitBlt full resync", "GetPixel read-only", "DX:AX returns",
                          "text/output/DIB/mode restore", "REPCOPY88 source and audit"],
            "contract": "AX/BX signed half-open rows, CX/DX signed half-open logical-byte columns; independent clamping; GPR/DS/ES/SP preserved; existing CLD behavior; no FLAGS guarantee; 10-byte SS:BP locals; no new CLI or multi-prefix REP",
            "runtime": "NOT_TESTED", "native_benefit": "NOT_MEASURED"}
