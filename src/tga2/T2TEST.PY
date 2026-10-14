#!/usr/bin/env python3
"""Generate T2SHOW.ASM from the driver's own Video II text (T2PATCH.PY).

  python3 src/tga2/T2TEST.PY --out <dir>        writes <dir>/T2SHOW.ASM
  python3 src/tga2/T2TEST.PY --shot <86Box screenshot> [--json <out>]
                                                 judges a capture of T2SHOW's bars

T2SHOW.COM (build with src/pcjr/BUILDCOM.PY) runs on a Tandy with Video II,
after T2RESV. Before anything else it checks that T2RESV's reservation is in
place: the last DOS block is MCB 8FFFh, 0C00h paragraphs, owned by a PSP
whose resident record (offset 103h) is 'TNDYV2R1', 9000h, 0C00h, exactly as
T2RESV leaves it. Otherwise it exits 3 with a message and touches no video
register or memory: the enable text clears 64,000 bytes at physical 90000h,
which without the reservation can belong to DOS or another program.
T2SHOW /G stops after that check (exit 0) for the DOS tests. Then it fills a 640x200 four-plane shadow (64,000 bytes, its own
DOS block) with 16 vertical bars of 40 pixels, bar c in IRGB colour c, then
uses the exact enable text and t2_row macro the driver build inserts to
switch to 640x200x16 and copy every row. It waits for a key with the bars
on screen, then leaves 640x200x16 and sets BIOS mode 03h. Exit 0; 1 if its
DOS block cannot be had; 3 without T2RESV's reservation (nothing is drawn
in either case).
"""
import argparse
import importlib.machinery
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader("t2patch", str(HERE / "T2PATCH.PY")).load_module()

BODY = r"""
.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start
shadow_seg dw 0
msg_mem db 'T2SHOW: no 64000-byte DOS block. Nothing drawn.',13,10,'$'
msg_resv db 'T2SHOW: no T2RESV reservation at 9000h. Run T2RESV first. Nothing drawn.',13,10,'$'
msg_gate db 'T2SHOW: T2RESV reservation found.',13,10,'$'
t2resv_id db 'TNDYV2R1'

@MACROS@

start:
 mov sp,offset stack_end
 mov bx,(stack_end-entry+100h+15)/16
 mov ah,4ah
 int 21h
@GATE@
 mov bx,0fa0h                    ; 64,000 bytes
 mov ah,48h
 int 21h
 jnc have_mem
 mov dx,offset msg_mem
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
have_mem:
 mov shadow_seg,ax
 ; bars: byte column k belongs to bar k/5 (40 pixels); plane p of the
 ; shadow (R,G,B,I at +0,+80,+160,+240 in each 320-byte row) is FFh where
 ; the bar's colour has that bit
 mov es,ax
 xor di,di
 xor dx,dx                       ; row
fill_row:
 xor bx,bx                       ; plane 0..3
fill_plane:
 xor cx,cx                       ; byte column 0..79
fill_byte:
 mov ax,cx
 push dx
 xor dx,dx
 push bx
 mov bx,5
 div bx
 pop bx                          ; AL = bar colour (0..15)
 pop dx
 push cx
 mov cl,plane_bit[bx]
 test al,cl
 pop cx
 mov al,0
 jz fill_put
 mov al,0ffh
fill_put:
 stosb
 inc cx
 cmp cx,80
 jb fill_byte
 inc bx
 cmp bx,4
 jb fill_plane
 inc dx
 cmp dx,200
 jb fill_row

@MODE@
 ; copy every row through t2_row
 push ds
 mov ax,0a000h
 mov es,ax
 mov ds,shadow_seg
 xor dx,dx
 xor si,si
 xor di,di
 cld
copy_row:
 mov bx,80
 push dx
 t2_row
 pop dx
 add si,240                      ; t2_row advanced SI by 80 within the row
 inc dx
 cmp dx,200
 jb copy_row
 pop ds
 xor ah,ah
 int 16h
@DISABLE@
 mov ax,0003h
 int 10h
 mov ax,4c00h
 int 21h

plane_bit db 4,2,1,8              ; shadow plane R,G,B,I -> IRGB bit

@TABLE@
even
 db 256 dup(0)
stack_end label byte
code ends
end entry
"""


# The reservation gate: nothing before it may touch video, and the enable
# text (which clears the page) must come after it. generate() checks both.
GATE = r"""
 ; T2RESV GATE: the last DOS block must be T2RESV's own 9000h/0C00h block.
 mov ah,52h
 int 21h
 mov ax,es:[bx-2]                ; first MCB
 mov cx,1000h
gate_walk:
 mov es,ax
 cmp byte ptr es:[0],'Z'
 je gate_last
 cmp byte ptr es:[0],'M'
 jne gate_fail
 add ax,es:[3]
 jc gate_fail
 inc ax
 loop gate_walk
 jmp short gate_fail
gate_last:
 cmp ax,8fffh
 jne gate_fail
 cmp word ptr es:[3],0c00h
 jne gate_fail
 mov ax,es:[1]                   ; owner PSP
 or ax,ax
 jz gate_fail
 mov es,ax
 cmp word ptr es:[0],20cdh       ; a PSP starts with INT 20h
 jne gate_fail
 mov si,offset t2resv_id         ; T2RESV's resident record at 103h
 mov di,103h
 mov cx,8
 cld
 repe cmpsb
 jne gate_fail
 cmp word ptr es:[10bh],9000h
 jne gate_fail
 cmp word ptr es:[10dh],0c00h
 jne gate_fail
 push cs
 pop es
 jmp short gate_ok
gate_fail:
 push cs
 pop es
 mov dx,offset msg_resv
 mov ah,9
 int 21h
 mov ax,4c03h
 int 21h
gate_ok:
 mov si,81h                      ; /G: stop after the check
gate_arg:
 lodsb
 cmp al,13
 je gate_go
 or al,20h
 cmp al,'g'
 jne gate_arg
 mov dx,offset msg_gate
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
gate_go:
"""


# Mutation control for T2RESV.PY --mutate no_gate: the /G handling only, no
# reservation check. Never used for a build that draws.
NO_GATE = GATE[:GATE.index(" ; T2RESV GATE")] + " ; T2RESV GATE (MUTATION: removed)\n" + GATE[GATE.index("gate_ok:"):]


def generate(gate=GATE):
    b = BODY.replace("@GATE@", gate)
    first = b.index("T2RESV GATE")
    for later in ("@MODE@", "fill_row:", "int 10h", "0a000h"):
        if b.index(later) < first:
            raise SystemExit(f"T2TEST: {later} comes before the T2RESV gate")
    t = b.replace("\n", "\r\n")
    t = t.replace("@MACROS@", P.ROW_MACRO).replace("@MODE@", P.MODE_TEXT)
    t = t.replace("@DISABLE@", P.DISABLE_TEXT).replace("@TABLE@", P.table_text())
    return "; T2SHOW.ASM - GENERATED by src/tga2/T2TEST.PY from T2PATCH.PY's driver text.\r\n" + t


def check_shot(path):
    """Every one of the 128,000 pixels decodes (SHOTDEC, 640 wide) to its
    bar's colour: x // 40. Exit 0 only then."""
    D = importlib.machinery.SourceFileLoader("shotdec", str(HERE.parent / "pcp" / "SHOTDEC.PY")).load_module()
    idx, worst, bad, size, geom = D.decode(path, 640)
    wrong = [(x, y, idx[y * 640 + x]) for y in range(200) for x in range(640) if idx[y * 640 + x] != x // 40]
    res = {"capture": str(path), "size": list(size), "geometry": geom, "worst_colour_distance": worst,
           "undecodable": bad, "pixels": 128000, "wrong": len(wrong), "first_wrong": wrong[:10],
           "verdict": "PASS" if not bad and not wrong else "FAIL"}
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--shot", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    if a.shot:
        import json
        res = check_shot(a.shot)
        print(json.dumps(res, indent=1))
        if a.json:
            a.json.write_text(json.dumps(res, indent=1) + "\n")
        return 0 if res["verdict"] == "PASS" else 1
    if not a.out:
        ap.error("--out or --shot")
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "T2SHOW.ASM").write_bytes(generate().encode("ascii"))
    print("T2TEST: wrote", a.out / "T2SHOW.ASM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
