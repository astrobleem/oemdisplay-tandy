"""Apply merged PR 151 after XYPATCH, with XY-safe dual-band alias checks."""
from pathlib import Path
import importlib.machinery

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]


def replace_once(text, old, new, name):
    count = text.count(old)
    if count != 1:
        raise SystemExit("XRPATCH: %s anchor matched %d times, expected 1" % (name, count))
    return text.replace(old, new)


DUAL_BAND_GATE = """ORowsSpanSafe proc near
    ; Validate a far span against both actual XY shadow allocations.
    ; Preserve AX/BX/CX/DX/BP and ES:DI; return only CF.
    push bp
    mov bp,sp
    sub sp,28
    push ax
    push bx
    push cx
    push dx
    ; Reject NULL, zero-length, and 64K offset-wrapping spans.
    mov ax,es
    or ax,di
    or_require jnz,ors_bad
    mov ax,cx
    or ax,ax
    or_require jnz,ors_bad
    mov ax,cx
    dec ax
    add ax,di
    or_require jnc,ors_bad
    ; Object start = ES*16 + DI.
    mov ax,es
    mov bx,16
    mul bx
    add ax,di
    adc dx,0
    mov ss:[bp-2],ax
    mov ss:[bp-4],dx
    ; Exclusive object end must not exceed the one-megabyte boundary.
    add ax,cx
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_obj_end_ok
    or ax,ax
    or_require jz,ors_bad
ors_obj_end_ok:
    mov ss:[bp-6],ax
    mov ss:[bp-8],dx
    ; Main band's physical interval: 64,000 bytes.
    mov ax,seg shadow_bits
    mul bx
    add ax,offset shadow_bits
    adc dx,0
    mov ss:[bp-10],ax
    mov ss:[bp-12],dx
    add ax,64000
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_main_end_ok
    or ax,ax
    or_require jz,ors_bad
ors_main_end_ok:
    mov ss:[bp-14],ax
    mov ss:[bp-16],dx
    ; Disjoint from the main band?
    mov dx,ss:[bp-4]
    cmp dx,ss:[bp-16]
    ja ors_tail
    jb ors_main_objend
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-14]
    jae ors_tail
ors_main_objend:
    mov dx,ss:[bp-8]
    cmp dx,ss:[bp-12]
    jb ors_tail
    ja ors_bad
    mov ax,ss:[bp-6]
    cmp ax,ss:[bp-10]
    jbe ors_tail
    jmp short ors_bad
ors_tail:
    ; Tail band's physical interval: 17,920 bytes.
    mov ax,seg shadow_tail
    mul bx
    add ax,offset shadow_tail
    adc dx,0
    mov ss:[bp-18],ax
    mov ss:[bp-20],dx
    add ax,17920
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_tail_end_ok
    or ax,ax
    or_require jz,ors_bad
ors_tail_end_ok:
    mov ss:[bp-22],ax
    mov ss:[bp-24],dx
    ; Disjoint from the tail band?
    mov dx,ss:[bp-4]
    cmp dx,ss:[bp-24]
    ja ors_good
    jb ors_tail_objend
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-22]
    jae ors_good
ors_tail_objend:
    mov dx,ss:[bp-8]
    cmp dx,ss:[bp-20]
    jb ors_good
    ja ors_bad
    mov ax,ss:[bp-6]
    cmp ax,ss:[bp-18]
    jbe ors_good
ors_bad:
    stc
    jmp short ors_done
ors_good:
    clc
ors_done:
    pop dx
    pop cx
    pop bx
    pop ax
    mov sp,bp
    pop bp
    ret
ORowsSpanSafe endp""".replace(chr(10), chr(13) + chr(10))

GATE_STUB = """ORowsSpanSafe proc near
    ; Conservative full Output flush until a dual-band alias gate is proved.
    stc
    ret
ORowsSpanSafe endp""".replace(chr(10), chr(13) + chr(10))


def patch_tsoft(text):
    rr = importlib.machinery.SourceFileLoader(
        "rr151_patch", str(HERE / "RRPATCH.PY")
    ).load_module()
    text = rr.patch_candidate(text)
    return replace_once(text, GATE_STUB, DUAL_BAND_GATE, "dual-band ORowsSpanSafe")


def patch(renderer, batch=False):
    base = importlib.machinery.SourceFileLoader(
        "xy_patch_for_xyrrect", str(HERE.parent / "XYPAN" / "XYPATCH.PY")
    ).load_module()
    base.patch(renderer)
    p = renderer / "EGA" / "TSOFT.ASM"
    text = p.read_bytes().decode("latin1")
    bare_lf = text.replace(chr(13) + chr(10), "")
    if chr(10) in bare_lf:
        raise SystemExit("XRPATCH: refusing bare LF in TSOFT.ASM")
    p.write_bytes(patch_tsoft(text).encode("latin1"))
    if batch:
        batching = importlib.machinery.SourceFileLoader(
            "xr_batch", str(HERE / "XRBATCH.PY")).load_module()
        batching.patch(renderer)
