#!/usr/bin/env python3
"""Profiling edits for the TXT40/TEXT80 drivers (measurement builds only).

Applied after T40PATCH (or T80PATCH) to the staged EGA/TSOFT.ASM. Nothing
here changes what the driver draws; it adds timers and counters, read by a
Windows program through Control escape 5450h ('TP'):

- Fine time: PIT channel 0 is switched to mode 2 (rate generator) with
  the same 65536 divisor at Enable, so IRQ 0 keeps its 18.2 Hz rate and
  BIOS time is unchanged, but the count falls linearly over the whole
  55 ms tick (mode 3 falls twice per tick by 2s). Time = BIOS tick (low
  word) : 65535 - count, in 1/65536 tick = 0.838 us units. A tick whose
  interrupt is pending (IRR bit 0) while the count has just wrapped is
  counted. Disable restores mode 3.
- Timers (count and total, 32-bit): 0 FlushColumns (all flushes,
  including cursor hide/show), 1 presenter, 2 presenter verify pass,
  3 presenter output pass, 4 one cell (t40_cell), 5 TBitBlt, 6 TOutput,
  7 TPixel, 8 TScanLR, 9 TStrBlt, 10 TExtTextOut, 11 hint recording
  (t40_text), 12 hint moves (t40_blit), 13 cells re-verified (count only),
  14 video writes (count only), 15 snapshot (t40_save), 16 cell
  compares of a diff flush (t40_changed), 17 diff flushes (t40_pdiff).
- A ring of the last 256 flushes: clamped rows and byte columns, the
  duration and the drawing call (5..10, 0 none) it came from.
- A ring of the last 64 ExtTextOut calls (version 2): the caller's clip
  and opaque rectangles (left, top, right, bottom; -32768 when the
  pointer is NULL), options, count, then the flush bounds the driver
  derived (rowfirst, rowlast, colfirst, collast) and dirty (0 not the
  screen, 1 whole flush, 2 these bounds).

Escape 5450h: input word 1 = copy and reset, 0 = copy; output = the block
(T80PROF_BYTES), whose first dword after the header is the current time.
"""
import sys
from pathlib import Path


def crlf(s):
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def rep(t, old, new, want, what):
    n = t.count(old)
    if n != want:
        raise SystemExit(f"T80PROF: '{what}' matched {n} times, expected {want}")
    return t.replace(old, new)


NSLOT = 20
RING = 256
XRING = 64
# header 4 + stamp 4 + counts + totals + ring index 2 + pad 2 + ring 16*256
# + text-call ring index 2 + pad 2 + text-call ring 32*64
T80PROF_BYTES = 4 + 4 + 4 * NSLOT * 2 + 4 + 16 * RING + 4 + 32 * XRING
WRAPPERS = {"TBitBlt": 5, "TOutput": 6, "TPixel": 7, "TScanLR": 8, "TStrBlt": 9, "TExtTextOut": 10}

DATA = crlf(f"""; T80PROF: profiling block (measurement builds only).
createSeg _T80P,T80PSeg,word,public,DATA
sBegin T80PSeg
public t80_block
t80_block label byte
t80_magic dw 5450h
t80_version dw 2
t80_stamp dd 0
t80_count dd {NSLOT} dup (0)
t80_total dd {NSLOT} dup (0)
t80_ri dw 0
t80_cur db 0
t80_pad db 0
t80_ring db {16 * RING} dup (0)
t80_xi dw 0
t80_xpad dw 0
t80_xring db {32 * XRING} dup (0)
t80_block_end label byte
t80_start dd {NSLOT} dup (0)
t80_rect dw 4 dup (0)
t80_last dd 0
sEnd T80PSeg

; DX:AX = fine time (tick low word : 65535 - PIT count). IF must be clear
; or is cleared here; the caller restores it. Clobbers nothing else.
t80_now macro
local nok
    cli
    xor al,al
    out 43h,al
    in al,40h
    mov ah,al
    in al,40h
    xchg ah,al
    not ax
    push ds
    mov dx,40h
    mov ds,dx
    mov dx,ds:[6ch]
    pop ds
    push ax
    mov al,0ah
    out 20h,al
    in al,20h
    test al,1
    pop ax
    jz nok
    test ax,8000h
    jnz nok
    inc dx
nok:
endm

; ExtTextOut trace: caller's rectangles, options and count (before clamping)
t80_xrect macro rp,off
local null,done
    les di,rp
    mov ax,es
    or ax,ax
    jz null
    mov ax,es:[di]
    mov ds:[si+off],ax
    mov ax,es:[di+2]
    mov ds:[si+off+2],ax
    mov ax,es:[di+4]
    mov ds:[si+off+4],ax
    mov ax,es:[di+6]
    mov ds:[si+off+6],ax
    jmp short done
null:
    mov word ptr ds:[si+off],8000h
done:
endm

t80_xslot macro
    mov si,ds:t80_xi
    mov cl,5
    shl si,cl
    add si,offset t80_xring
endm

t80_xin macro
    pushf
    push ax
    push cx
    push si
    push di
    push ds
    push es
    mov ax,seg t80_block
    mov ds,ax
    t80_xslot
    t80_xrect clip,0
    t80_xrect opaquerect,8
    mov ax,options
    mov ds:[si+16],ax
    mov ax,count
    mov ds:[si+18],ax
    pop es
    pop ds
    pop di
    pop si
    pop cx
    pop ax
    popf
endm

t80_xout macro
    pushf
    push ax
    push cx
    push si
    push ds
    mov ax,seg t80_block
    mov ds,ax
    t80_xslot
    mov ax,rowfirst
    mov ds:[si+20],ax
    mov ax,rowlast
    mov ds:[si+22],ax
    mov ax,colfirst
    mov ds:[si+24],ax
    mov ax,collast
    mov ds:[si+26],ax
    mov ax,dirty
    mov ds:[si+28],ax
    mov ax,ds:t80_xi
    inc ax
    and ax,{XRING - 1}
    mov ds:t80_xi,ax
    pop ds
    pop si
    pop cx
    pop ax
    popf
endm

t80_tbeg macro idx
    pushf
    push ax
    push dx
    push ds
    t80_now
    push ax
    mov ax,seg t80_block
    mov ds,ax
    pop ax
    mov word ptr ds:t80_start[(idx)*4],ax
    mov word ptr ds:t80_start[(idx)*4+2],dx
    pop ds
    pop dx
    pop ax
    popf
endm

t80_tend macro idx
    pushf
    push ax
    push dx
    push ds
    t80_now
    push ax
    mov ax,seg t80_block
    mov ds,ax
    pop ax
    sub ax,word ptr ds:t80_start[(idx)*4]
    sbb dx,word ptr ds:t80_start[(idx)*4+2]
    mov word ptr ds:t80_last,ax
    mov word ptr ds:t80_last+2,dx
    add word ptr ds:t80_total[(idx)*4],ax
    adc word ptr ds:t80_total[(idx)*4+2],dx
    add word ptr ds:t80_count[(idx)*4],1
    adc word ptr ds:t80_count[(idx)*4+2],0
    pop ds
    pop dx
    pop ax
    popf
endm

t80_cnt macro idx
    pushf
    push ax
    push ds
    mov ax,seg t80_block
    mov ds,ax
    add word ptr ds:t80_count[(idx)*4],1
    adc word ptr ds:t80_count[(idx)*4+2],0
    pop ds
    pop ax
    popf
endm

t80_setcur macro val
    push ax
    push ds
    mov ax,seg t80_block
    mov ds,ax
    mov byte ptr ds:t80_cur,val
    pop ds
    pop ax
endm

; AX,BX,CX,DX = clamped flush rows and byte columns
t80_keeprect macro
    push ds
    push si
    mov si,seg t80_block
    mov ds,si
    mov ds:t80_rect,ax
    mov ds:t80_rect+2,bx
    mov ds:t80_rect+4,cx
    mov ds:t80_rect+6,dx
    pop si
    pop ds
endm

; one ring entry from t80_rect, t80_last, t80_cur
t80_ringput macro
    pushf
    push ax
    push cx
    push si
    push di
    push ds
    push es
    mov ax,seg t80_block
    mov ds,ax
    mov es,ax
    mov di,ds:t80_ri
    mov cl,4
    shl di,cl
    add di,offset t80_ring
    mov si,offset t80_rect
    cld
    movsw
    movsw
    movsw
    movsw
    mov si,offset t80_last
    movsw
    movsw
    mov al,ds:t80_cur
    stosb
    mov ax,ds:t80_ri
    inc ax
    and ax,{RING - 1}
    mov ds:t80_ri,ax
    pop es
    pop ds
    pop di
    pop si
    pop cx
    pop ax
    popf
endm
""")

ENABLE_PIT = crlf("""    mov al,34h                ; T80PROF: PIT 0 mode 2, divisor 65536
    out 43h,al
    xor al,al
    out 40h,al
    out 40h,al
""")
DISABLE_PIT = crlf("""    mov al,36h                ; T80PROF: PIT 0 back to mode 3
    out 43h,al
    xor al,al
    out 40h,al
    out 40h,al
""")

CONTROL_QUERY_OLD = "    cmp bx,GETCOLORTABLE\r\n    je control_ok\r\n    jmp control_done\r\ncontrol_color:\r\n"
CONTROL_QUERY_NEW = crlf("""    cmp bx,GETCOLORTABLE
    je control_ok
    cmp bx,5450h              ; T80PROF
    je control_ok
    jmp control_done
control_color:
    cmp bx,5450h
    jne t80_not_prof
    mov dx,es:[di]            ; 1 = reset after copying
    les di,output
    call t80_escape
    mov ax,1
    jmp control_done
t80_not_prof:
""")

# DX = 1 to reset after copying; ES:DI = output. Clobbers AX-DI.
ESCAPE_PROC = crlf("""t80_escape proc near
    push ds
    mov ax,seg t80_block
    mov ds,ax
    push dx
    pushf
    t80_now
    popf
    mov word ptr ds:t80_stamp,ax
    mov word ptr ds:t80_stamp+2,dx
    pop dx
    mov si,offset t80_block
    mov cx,offset t80_block_end - offset t80_block
    cld
    rep movsb
    cmp dx,1
    jne t80e_done
    push ds
    pop es
    mov di,offset t80_count
    mov cx,offset t80_block_end - offset t80_count
    xor al,al
    rep stosb
t80e_done:
    pop ds
    ret
t80_escape endp

""")


def patch(t):
    t = rep(t, "sEnd T40Seg\r\n", "sEnd T40Seg\r\n" + DATA, 1, "data and macros")
    # PIT mode 2 at enable (after the mode set), mode 3 at disable
    t = rep(t, "    mov ax,0b800h\r\n    mov es,ax\r\n    xor di,di\r\n    xor ax,ax\r\n",
            ENABLE_PIT + "    mov ax,0b800h\r\n    mov es,ax\r\n    xor di,di\r\n    xor ax,ax\r\n", 1, "enable PIT")
    t = rep(t, "    mov al,old_mode\r\n    xor ah,ah\r\n    int 10h\r\n",
            DISABLE_PIT + "    mov al,old_mode\r\n    xor ah,ah\r\n    int 10h\r\n", 1, "disable PIT")
    t = rep(t, CONTROL_QUERY_OLD, CONTROL_QUERY_NEW, 1, "escape 5450h")
    t = rep(t, "cProc TControl,", ESCAPE_PROC + "cProc TControl,", 1, "escape proc")
    # flushes
    t = rep(t, "t40f_start:\r\n", "t40f_start:\r\n    t80_tbeg 0\r\n", 1, "flush begin")
    t = rep(t, "t40f_right:\r\n", "t40f_right:\r\n    t80_keeprect\r\n", 1, "flush rect")
    t = rep(t, "    pop bx\r\n    pop ax\r\n    ret\r\nFlushColumns endp",
            "    pop bx\r\n    pop ax\r\n    t80_tend 0\r\n    t80_ringput\r\n    ret\r\nFlushColumns endp", 1, "flush end")
    # presenter
    t = rep(t, "t40_present proc near\r\n", "t40_present proc near\r\n    t80_tbeg 1\r\n    t80_tbeg 2\r\n", 1,
            "present begin")
    t = rep(t, "    ; output range\r\n", "    t80_tend 2\r\n    t80_tbeg 3\r\n    ; output range\r\n", 1, "verify end")
    t = rep(t, "    jle tpr_orow\r\n    ret\r\nt40_present endp",
            "    jg t80_po\r\n    jmp tpr_orow\r\nt80_po:\r\n    t80_tend 3\r\n    t80_tend 1\r\n    ret\r\n"
            "t40_present endp", 1, "present end")
    t = rep(t, "    jle tpr_ocol\r\n", "    jg t80_pc\r\n    jmp tpr_ocol\r\nt80_pc:\r\n", 1, "cell loop (long jump)")
    t = rep(t, "    call t40_cell\r\n", "    t80_tbeg 4\r\n    call t40_cell\r\n    t80_tend 4\r\n", 1, "cell")
    t = rep(t, "tpr_verify:\r\n    call t40_shown\r\n", "tpr_verify:\r\n    t80_cnt 13\r\n    call t40_shown\r\n",
            1, "verify count")
    t = rep(t, "    pop ax\r\n  if T40_PANNED\r\n    mov si,T40_LSEG",
            "    pop ax\r\n    t80_cnt 14\r\n  if T40_PANNED\r\n    mov si,T40_LSEG", 1, "cell write count")
    # hints
    t = rep(t, "t40_text proc near\r\n", "t40_text proc near\r\n    t80_tbeg 11\r\n", 1, "text begin")
    i, j = t.index("t40_save proc near\r\n"), t.index("t40_save endp")
    if t[i:j].count("    ret\r\n") != 1:
        raise SystemExit("T80PROF: t40_save has more than one ret")
    t = rep(t, "t40_save proc near\r\n", "t40_save proc near\r\n    t80_tbeg 15\r\n", 1, "save begin")
    t = rep(t, "tsn_done:\r\n", "tsn_done:\r\n    t80_tend 15\r\n", 1, "save end")
    t = rep(t, "    call t40_changed\r\n", "    t80_tbeg 16\r\n    call t40_changed\r\n    t80_tend 16\r\n", 1,
            "compare")
    t = rep(t, "t40_pdiff proc near\r\n", "t40_pdiff proc near\r\n    t80_tbeg 17\r\n", 1, "pdiff begin")
    t = rep(t, "tpd_full:\r\n    jmp t40_present\r\n", "tpd_full:\r\n    t80_tend 17\r\n    jmp t40_present\r\n", 1,
            "pdiff full")
    t = rep(t, "tpd_done:\r\n    ret\r\nt40_pdiff endp", "tpd_done:\r\n    t80_tend 17\r\n    ret\r\nt40_pdiff endp", 1,
            "pdiff end")
    t = rep(t, "tt_ret:\r\n    ret\r\nt40_text endp", "tt_ret:\r\n    t80_tend 11\r\n    ret\r\nt40_text endp", 1,
            "text end")
    i, j = t.index("t40_blit proc near\r\n"), t.index("t40_blit endp")
    if t[i:j].count("    ret\r\n") != 1:
        raise SystemExit("T80PROF: t40_blit has more than one ret")
    t = rep(t, "t40_blit proc near\r\n", "t40_blit proc near\r\n    t80_tbeg 12\r\n", 1, "blit begin")
    t = rep(t, "tb_done:\r\n", "tb_done:\r\n    t80_tend 12\r\n", 1, "blit end")
    # ExtTextOut trace
    t = rep(t, "    t40_record 1\r\n    t40_clamp 1\r\n", "    t40_record 1\r\n    t80_xin\r\n    t40_clamp 1\r\n", 1,
            "text trace in")
    t = rep(t, "    t40_bounds 1\r\n", "    t40_bounds 1\r\n    t80_xout\r\n", 1, "text trace out")
    # drawing entry points: whole call (render into the shadow + flushes)
    for name, idx in WRAPPERS.items():
        i = t.index(f"cProc {name},")
        j = t.find("cProc ", i + 6)
        body = t[i:j]
        if body.count("cBegin\r\n") != 1 or body.count("cEnd\r\n") != 1:
            raise SystemExit(f"T80PROF: {name} needs exactly one cBegin and one cEnd")
        body = body.replace("cBegin\r\n", f"cBegin\r\n    t80_setcur {idx}\r\n    t80_tbeg {idx}\r\n")
        body = body.replace("cEnd\r\n", f"    t80_tend {idx}\r\n    t80_setcur 0\r\ncEnd\r\n")
        t = t[:i] + body + t[j:]
    return t


def patch_def(t):
    return rep(t, " _T40 PRELOAD FIXED\r\n", " _T40 PRELOAD FIXED\r\n _T80P PRELOAD FIXED\r\n", 1, "def segment")


def patch_staged(ega_dir):
    ega_dir = Path(ega_dir)
    out = {}
    for name, fn in (("TSOFT.ASM", patch), ("TSOFT.DEF", patch_def)):
        p = ega_dir / name
        t = p.read_bytes().decode("latin-1")
        t = fn(t)
        p.write_bytes(t.encode("latin-1"))
        out[name] = t
    return out


if __name__ == "__main__":
    print("T80PROF: block", T80PROF_BYTES, "bytes")
