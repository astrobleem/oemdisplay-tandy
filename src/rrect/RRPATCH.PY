#!/usr/bin/env python3
"""Staged-source edits for the RoundRect investigation (src/rrect).

TRACE (test-only, never shipped): TOutput records every call it receives
into a 1,024-entry table in the driver's data segment, and TControl answers
two private escapes so a probe can read it:
  7F01h  input: WORD first record; output: WORD total, WORD lost, then up
         to 64 records of RR_SIZE bytes. Returns copied+1.
  7F02h  clears the table. Returns 1.
Record (RR_SIZE = 20 bytes):
  +0 style  +2 count  +4 flags (bit0 screen/shadow write, bit1 bounded rows)
  +5 ROP2 (mode[0])  +6 background mode (mode[2])  +7 pen style (pen+4)
  +8 brush word +40 (the gate's solid-brush test)  +10 min Y  +12 max Y
  +14 min X  +16 max X  +18 point records walked (at most 512)
For OS_SCANLINES the Y comes from points[0].y and X from the intervals.
Missing objects are FFh/FFFFh. Nothing else in the driver changes.

Every edit matches an exact anchor an exact number of times or nothing is
written (RRBUILD.PY applies them to the BUILD88 staging copy only).
"""

RR_MAX = 1024
RR_SIZE = 20


class PatchError(SystemExit):
    pass


def replace_n(text, old, new, want, name):
    n = text.count(old)
    if n != want:
        raise PatchError(f"RRPATCH: '{name}' matched {n} times, expected {want}")
    return text.replace(old, new)


TRACE_DATA_OLD = "sBegin Data\r\npublic enabled_flag,ScratchSel,is_protected,_cstods,diag_markers\r\n"
TRACE_DATA_NEW = (TRACE_DATA_OLD +
                  "; RRTRACE (test-only build): Output call table, see src/rrect/RRPATCH.PY\r\n"
                  "public rr_count,rr_lost,rr_buf\r\n"
                  "rr_count dw 0\r\n"
                  "rr_lost dw 0\r\n"
                  f"rr_buf db {RR_MAX * RR_SIZE} dup (0)\r\n")

# Inserted after the gate's register restore, immediately before the
# renderer call: the gate's dirty/outrows decisions are final here, and the
# renderer has not yet run. DS is the driver data segment (map_device).
TRACE_OUTPUT_ANCHOR = ("    popf\r\n"
                       "    cCall Output,<dst,style,count,points,pen,brush,mode,clip>\r\n")
TRACE_OUTPUT_BLOCK = """    ; RRTRACE: record this Output call (test-only build).
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    mov si,rr_count
    cmp si,RR_MAX_N
    jb rrt_room
    inc rr_lost
    jmp rrt_exit
rrt_room:
    inc rr_count
    mov ax,RR_SIZE_N
    mul si
    mov si,ax
    add si,offset rr_buf
    mov ax,style
    mov [si],ax
    mov ax,count
    mov [si+2],ax
    xor al,al
    cmp dirty,0
    je rrt_nodirty
    or al,1
rrt_nodirty:
    cmp outrows,0
    je rrt_nobound
    or al,2
rrt_nobound:
    mov [si+4],al
    mov word ptr [si+5],0ffffh
    mov byte ptr [si+7],0ffh
    mov word ptr [si+8],0ffffh
    mov word ptr [si+10],7fffh
    mov word ptr [si+12],8000h
    mov word ptr [si+14],7fffh
    mov word ptr [si+16],8000h
    mov word ptr [si+18],0
    les di,mode
    mov ax,es
    or ax,di
    jz rrt_nomode
    mov al,es:[di]
    mov [si+5],al
    mov al,es:[di+2]
    mov [si+6],al
rrt_nomode:
    les di,pen
    mov ax,es
    or ax,di
    jz rrt_nopen
    mov al,es:[di+4]
    mov [si+7],al
rrt_nopen:
    les di,brush
    mov ax,es
    or ax,di
    jz rrt_nobrush
    mov ax,es:[di+40]
    mov [si+8],ax
rrt_nobrush:
    les di,points
    mov ax,es
    or ax,di
    jnz rrt_haspts
    jmp rrt_exit
rrt_haspts:
    mov cx,count
    cmp cx,512
    jbe rrt_cntok
    mov cx,512
rrt_cntok:
    mov [si+18],cx
    jcxz rrt_exit
    cmp style,4
    jne rrt_point
    mov ax,es:[di+2]
    mov [si+10],ax
    mov [si+12],ax
    dec cx
    jcxz rrt_exit
rrt_interval:
    add di,4
    mov ax,es:[di]
    cmp ax,[si+14]
    jge rrt_i1
    mov [si+14],ax
rrt_i1:
    mov ax,es:[di+2]
    cmp ax,[si+16]
    jle rrt_i2
    mov [si+16],ax
rrt_i2:
    loop rrt_interval
    jmp short rrt_exit
rrt_point:
    mov ax,es:[di]
    cmp ax,[si+14]
    jge rrt_p1
    mov [si+14],ax
rrt_p1:
    cmp ax,[si+16]
    jle rrt_p2
    mov [si+16],ax
rrt_p2:
    mov ax,es:[di+2]
    cmp ax,[si+10]
    jge rrt_p3
    mov [si+10],ax
rrt_p3:
    cmp ax,[si+12]
    jle rrt_p4
    mov [si+12],ax
rrt_p4:
    add di,4
    loop rrt_point
rrt_exit:
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
""".replace("\n", "\r\n").replace("RR_MAX_N", str(RR_MAX)).replace("RR_SIZE_N", str(RR_SIZE))

TRACE_CONTROL_ANCHOR = ("    parmD output\r\n"
                        "cBegin\r\n"
                        "    xor ax,ax\r\n"
                        "    les di,input\r\n"
                        "    mov bx,function\r\n")
TRACE_CONTROL_BLOCK = """    ; RRTRACE: private escapes 7F01h (read) and 7F02h (clear), test-only.
    cmp function,7F01h
    je rrc_read
    cmp function,7F02h
    jne rrc_none
    push ds
    mov ax,seg rr_count
    mov ds,ax
    mov rr_count,0
    mov rr_lost,0
    pop ds
    mov ax,1
    jmp control_done
rrc_read:
    push ds
    mov ax,seg rr_count
    mov ds,ax
    les di,input
    mov bx,es:[di]
    les di,output
    mov ax,rr_count
    mov es:[di],ax
    mov ax,rr_lost
    mov es:[di+2],ax
    add di,4
    mov cx,rr_count
    xor dx,dx
    cmp bx,cx
    jae rrc_copied
    sub cx,bx
    cmp cx,64
    jbe rrc_n
    mov cx,64
rrc_n:
    push cx
    mov ax,RR_SIZE_N
    mul bx
    mov si,ax
    add si,offset rr_buf
    pop cx
    mov dx,cx
    push dx
    mov ax,RR_SIZE_N / 2
    mul cx
    mov cx,ax
    cld
    rep movsw
    pop dx
rrc_copied:
    mov ax,dx
    inc ax
    pop ds
    jmp control_done
rrc_none:
""".replace("\n", "\r\n").replace("RR_SIZE_N", str(RR_SIZE))


def patch_trace(tsoft):
    t = replace_n(tsoft, TRACE_DATA_OLD, TRACE_DATA_NEW, 1, "trace data")
    t = replace_n(t, TRACE_OUTPUT_ANCHOR, TRACE_OUTPUT_ANCHOR.replace(
        "    popf\r\n", "    popf\r\n" + TRACE_OUTPUT_BLOCK, 1), 1, "trace Output")
    t = replace_n(t, TRACE_CONTROL_ANCHOR, TRACE_CONTROL_ANCHOR + TRACE_CONTROL_BLOCK, 1, "trace Control")
    return t


# Ablations (test-only measurement builds, never shipped). They change only
# TOutput, after the gate: NOFLUSH skips the shadow-to-screen copy for
# Output calls (the screen is not updated); NODRAW also skips the renderer
# and returns 1, leaving GDI's own work plus the call itself.
ABL_FLUSH_OLD = ("    cmp dirty,0\r\n    je TOutput_done\r\n"
                 "    ; Preserve the actual renderer result and all post-render GPRs.\r\n")
ABL_FLUSH_NEW = ("    jmp TOutput_done             ; RR ablation: no screen copy\r\n"
                 "    ; Preserve the actual renderer result and all post-render GPRs.\r\n")
ABL_DRAW_OLD = "    cCall Output,<dst,style,count,points,pen,brush,mode,clip>\r\n"
ABL_DRAW_NEW = "    mov ax,1                     ; RR ablation: renderer not called\r\n"


def patch_noflush(tsoft):
    return replace_n(tsoft, ABL_FLUSH_OLD, ABL_FLUSH_NEW, 1, "ablation flush")


def patch_nodraw(tsoft):
    t = patch_noflush(tsoft)
    return replace_n(t, ABL_DRAW_OLD, ABL_DRAW_NEW, 1, "ablation draw")


# --- candidate --------------------------------------------------------------
# Two gate changes in TOutput; the renderer, its arguments and its order are
# untouched, so every shadow pixel is as before; only the copy to the screen
# changes:
# 1. GDI's OS_BEGINNSCAN (80) and OS_ENDNSCAN (81) markers: OUTPUT.ASM
#    returns -1 for every style but 4 and 18 before touching anything, so
#    the shadow did not change and nothing needs copying. dirty=0 skips the
#    copy (and its cursor hide/show) for exactly these two styles.
# 2. OS_POLYLINE with 3..RR_POLY_MAX points: like the existing two-point
#    case, every point must lie on the screen; the copy is then the rows from
#    the lowest to the highest point (a thin polyline never leaves them). Any
#    point off screen, or more points, keeps the full refresh.
RR_POLY_MAX = 1024

CAND_STYLE_OLD = ("TOutput_thin_count:\r\n"
                  "    cmp style,18\r\n"
                  "    or_require je,TOutput_render\r\n"
                  "    cmp count,2\r\n"
                  "    or_require je,TOutput_render\r\n"
                  "TOutput_style_ok:\r\n")
CAND_STYLE_NEW = ("TOutput_thin_count:\r\n"
                  "    ; RRECT: GDI's OS_BEGINNSCAN/OS_ENDNSCAN markers draw nothing (the\r\n"
                  "    ; renderer returns -1 for them untouched): no copy, no cursor work.\r\n"
                  "    cmp style,80\r\n"
                  "    je TOutput_marker\r\n"
                  "    cmp style,81\r\n"
                  "    jne TOutput_not_marker\r\n"
                  "TOutput_marker:\r\n"
                  "    mov dirty,0\r\n"
                  "    jmp TOutput_render\r\n"
                  "TOutput_not_marker:\r\n"
                  "    cmp style,18\r\n"
                  "    or_require je,TOutput_render\r\n"
                  "    ; RRECT: two-point lines as before, and 3..N-point polylines.\r\n"
                  "    cmp count,2\r\n"
                  "    or_require jae,TOutput_render\r\n"
                  f"    cmp count,{RR_POLY_MAX}\r\n"
                  "    or_require jbe,TOutput_render\r\n"
                  "TOutput_style_ok:\r\n")
CAND_POLY_OLD = "TOutput_polyline:\r\n    mov cx,es:[di]\r\n"
CAND_POLY_NEW = ("TOutput_polyline:\r\n"
                 "    cmp count,2\r\n"
                 "    je TOutput_two_point\r\n"
                 "    ; RRECT: every point on the screen; rows = lowest..highest Y.\r\n"
                 "    mov cx,count\r\n"
                 "    mov ax,7fffh\r\n"
                 "    xor bx,bx\r\n"
                 "TOutput_poly_point:\r\n"
                 "    mov dx,es:[di]\r\n"
                 "    cmp dx,SCREEN_WIDTH\r\n"
                 "    or_require jb,TOutput_render\r\n"
                 "    mov dx,es:[di+2]\r\n"
                 "    cmp dx,SCREEN_HEIGHT\r\n"
                 "    or_require jb,TOutput_render\r\n"
                 "    cmp dx,ax\r\n"
                 "    jae TOutput_poly_notmin\r\n"
                 "    mov ax,dx\r\n"
                 "TOutput_poly_notmin:\r\n"
                 "    cmp dx,bx\r\n"
                 "    jbe TOutput_poly_notmax\r\n"
                 "    mov bx,dx\r\n"
                 "TOutput_poly_notmax:\r\n"
                 "    add di,4\r\n"
                 "    loop TOutput_poly_point\r\n"
                 "    mov firstrow,ax\r\n"
                 "    inc bx\r\n"
                 "    mov lastrow,bx\r\n"
                 "    jmp TOutput_bounded\r\n"
                 "TOutput_two_point:\r\n"
                 "    mov cx,es:[di]\r\n")


def patch_candidate(tsoft):
    t = replace_n(tsoft, CAND_STYLE_OLD, CAND_STYLE_NEW, 1, "candidate style gate")
    return replace_n(t, CAND_POLY_OLD, CAND_POLY_NEW, 1, "candidate polyline bounds")


def decode_records(data):
    """Records from the probe's TRACEnn.BIN (concatenated 20-byte records)."""
    import struct
    out = []
    for i in range(0, len(data) - RR_SIZE + 1, RR_SIZE):
        style, count, flags, rop2, bk, pen, brush, miny, maxy, minx, maxx, walked = struct.unpack_from(
            "<HHBBBBHhhhhH", data, i)
        out.append({"style": style, "count": count, "screen": bool(flags & 1), "bounded": bool(flags & 2),
                    "rop2": rop2, "bkmode": bk, "pen_style": pen, "brush40": brush,
                    "y": [miny, maxy], "x": [minx, maxx], "walked": walked})
    return out
