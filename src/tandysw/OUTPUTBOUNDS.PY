"""Synchronous fixed-profile Output bounds over each exact accepted TR5 stage."""
from pathlib import Path
import hashlib

EXPECTED = {
    '160x200x16': '89749ad0c1163ca87aee2b775abbd3da1a328ce024a49bed89197c4822294c04',
    '320x200x16': '361b5ba3df9e98a4894d991e45a54069917f174acf58fb97368c42f2d4d31cc5',
    '640x200x4': 'a0e03445fa0353b7052d1e4a5bd3674d5c22ef580c089b09c9f37bc13059c75b',
    '320x200x4': 'bdf5a9ef4d6fd32a44afd20fcb584274cdfab4cdaf23848323db773e955785b8',
    '640x200x2': 'aa3bd535163b8a2ea1116fea1c500c435721bc4e506ed4466af9737f171a67c6',
}

def _dos(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n")

OLD_GATE = _dos("""cProc TOutput,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW style
    parmW count
    parmD points
    parmD pen
    parmD brush
    parmD mode
    parmD clip
    localW dirty
    localW outrows
    localW firstrow
    localW lastrow
cBegin
    mov dirty,0
    mov outrows,0
    map_device dst,1
    ; Capture bounds before rendering. FULL is the fail-closed default.
    ; Restore all validation scratch state before the exact renderer call.
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    cmp dirty,0
    or_require jne,TOutput_render
    ; WIDESCAN: bounded scan lists only. Thin-line gate stays count=2.
    cmp style,4
    jne TOutput_thin_count
    cmp count,2
    or_require jae,TOutput_render
    cmp count,64
    or_require jbe,TOutput_render
    jmp short TOutput_style_ok
TOutput_thin_count:
    cmp style,18
    or_require je,TOutput_render
    cmp count,2
    or_require je,TOutput_render
TOutput_style_ok:
    les di,points
    mov cx,count
    shl cx,1
    shl cx,1
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    les di,mode
    mov cx,32
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    dec ax
    cmp ax,15
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    dec ax
    cmp ax,1
    or_require jbe,TOutput_render
    ; SCANLINE never reads clip. Do not newly dereference an ignored input.
    cmp style,4
    je TOutput_clip_ok
    les di,clip
    mov ax,es
    or ax,di
    jz TOutput_clip_ok
    mov cx,8
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    mov bx,es:[di+4]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    mov bx,es:[di+6]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_HEIGHT
    or_require jbe,TOutput_render
TOutput_clip_ok:
    cmp style,18
    je TOutput_check_pen
    les di,brush
    mov ax,es
    or ax,di
    jz TOutput_check_pen
    mov cx,54
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+40],0
    or_require je,TOutput_render
    jmp short TOutput_objects_ok
TOutput_check_pen:
    les di,pen
    mov cx,6
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+4],4
    or_require jbe,TOutput_render
TOutput_objects_ok:
    les di,points
    cmp style,18
    je TOutput_polyline
    ; One Y shared by count-1 intervals. Rendering order/overlap unchanged.
    ; Validate the complete far span above, then every exclusive-X pair.
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov firstrow,ax
    inc ax
    mov lastrow,ax
    mov cx,count
    dec cx
TOutput_scan_interval:
    add di,4
    mov bx,es:[di]
    mov dx,es:[di+2]
    cmp bx,dx
    or_require jb,TOutput_render
    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    loop TOutput_scan_interval
    jmp short TOutput_bounded
TOutput_polyline:
    mov cx,es:[di]
    cmp cx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov dx,es:[di+4]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov bx,es:[di+6]
    cmp bx,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp ax,bx
    jne TOutput_line_nonempty
    cmp cx,dx
    or_require jne,TOutput_render
TOutput_line_nonempty:
    cmp ax,bx
    jbe TOutput_line_ordered
    xchg ax,bx
TOutput_line_ordered:
    mov firstrow,ax
    inc bx
    mov lastrow,bx
TOutput_bounded:
    mov outrows,1
TOutput_render:
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp dirty,0
    je TOutput_done
    ; Preserve the actual renderer result and all post-render GPRs.
    push ax
    push bx
    cmp outrows,0
    je TOutput_full
    mov ax,firstrow
    mov bx,lastrow
    call FlushRetainRows
    jmp short TOutput_flushed
TOutput_full:
    call FlushShadow
TOutput_flushed:
    pop bx
    pop ax
TOutput_done:
cEnd

""")

NEW_GATE = _dos("""cProc TOutput,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW style
    parmW count
    parmD points
    parmD pen
    parmD brush
    parmD mode
    parmD clip
    localW dirty
    localW outrows
    localW firstrow
    localW lastrow
    localW firstcol
    localW lastcol
cBegin
    mov dirty,0
    mov outrows,0
    map_device dst,1
    ; Capture bounds before rendering. FULL is the fail-closed default.
    ; Restore all validation scratch state before the exact renderer call.
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    cmp dirty,0
    or_require jne,TOutput_render
    ; Bounded scan lists and validated thin polylines; all other calls stay FULL.
    cmp style,4
    jne TOutput_thin_count
    cmp count,2
    or_require jae,TOutput_render
    cmp count,64
    or_require jbe,TOutput_render
    jmp short TOutput_style_ok
TOutput_thin_count:
    ; RRECT: GDI's OS_BEGINNSCAN/OS_ENDNSCAN markers draw nothing (the
    ; renderer returns -1 for them untouched): no copy, no cursor work.
    cmp style,80
    je TOutput_marker
    cmp style,81
    jne TOutput_not_marker
TOutput_marker:
    mov dirty,0
    jmp TOutput_render
TOutput_not_marker:
    cmp style,18
    or_require je,TOutput_render
    ; RRECT: two-point lines as before, and 3..N-point polylines.
    cmp count,2
    or_require jae,TOutput_render
    cmp count,1024
    or_require jbe,TOutput_render
TOutput_style_ok:
    les di,points
    mov cx,count
    shl cx,1
    shl cx,1
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    les di,mode
    mov cx,32
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    dec ax
    cmp ax,15
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    dec ax
    cmp ax,1
    or_require jbe,TOutput_render
    ; SCANLINE never reads clip. Do not newly dereference an ignored input.
    cmp style,4
    je TOutput_clip_ok
    les di,clip
    mov ax,es
    or ax,di
    jz TOutput_clip_ok
    mov cx,8
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    mov bx,es:[di+4]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    mov bx,es:[di+6]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_HEIGHT
    or_require jbe,TOutput_render
TOutput_clip_ok:
    cmp style,18
    je TOutput_check_pen
    les di,brush
    mov ax,es
    or ax,di
    jz TOutput_check_pen
    mov cx,54
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+40],0
    or_require je,TOutput_render
    jmp short TOutput_objects_ok
TOutput_check_pen:
    les di,pen
    mov cx,6
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+4],4
    or_require jbe,TOutput_render
TOutput_objects_ok:
    ; Capture a conservative pixel X interval before converting to byte columns.
    mov firstcol,SCREEN_WIDTH
    mov lastcol,0
    les di,points
    cmp style,18
    je TOutput_polyline
    ; One Y shared by count-1 intervals. Rendering order/overlap unchanged.
    ; Validate the complete far span above, then every exclusive-X pair.
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov firstrow,ax
    inc ax
    mov lastrow,ax
    mov cx,count
    dec cx
TOutput_scan_interval:
    add di,4
    mov bx,es:[di]
    mov dx,es:[di+2]
    cmp bx,dx
    or_require jb,TOutput_render
    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    cmp bx,firstcol
    jae TOutput_scan_notleft
    mov firstcol,bx
TOutput_scan_notleft:
    cmp dx,lastcol
    jbe TOutput_scan_notright
    mov lastcol,dx
TOutput_scan_notright:
    loop TOutput_scan_interval
    jmp TOutput_bounded
TOutput_polyline:
    cmp count,2
    je TOutput_two_point
    ; RRECT: every point on the screen; rows = lowest..highest Y.
    mov cx,count
    mov ax,7fffh
    xor bx,bx
TOutput_poly_point:
    mov dx,es:[di]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    cmp dx,firstcol
    jae TOutput_poly_notleft
    mov firstcol,dx
TOutput_poly_notleft:
    cmp dx,lastcol
    jbe TOutput_poly_notright
    mov lastcol,dx
TOutput_poly_notright:
    mov dx,es:[di+2]
    cmp dx,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp dx,ax
    jae TOutput_poly_notmin
    mov ax,dx
TOutput_poly_notmin:
    cmp dx,bx
    jbe TOutput_poly_notmax
    mov bx,dx
TOutput_poly_notmax:
    add di,4
    loop TOutput_poly_point
    mov firstrow,ax
    inc bx
    mov lastrow,bx
    inc lastcol               ; point maximum was inclusive
    jmp TOutput_bounded
TOutput_two_point:
    mov cx,es:[di]
    cmp cx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov dx,es:[di+4]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov bx,es:[di+6]
    cmp bx,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp ax,bx
    jne TOutput_line_nonempty
    cmp cx,dx
    or_require jne,TOutput_render
TOutput_line_nonempty:
    cmp ax,bx
    jbe TOutput_line_ordered
    xchg ax,bx
TOutput_line_ordered:
    mov firstrow,ax
    inc bx
    mov lastrow,bx
    cmp cx,dx
    jbe TOutput_line_cols_ordered
    xchg cx,dx
TOutput_line_cols_ordered:
    mov firstcol,cx
    inc dx
    mov lastcol,dx
TOutput_bounded:
    ; Complete logical bytes cover every affected pixel and adjacent plane pair.
    mov cx,firstcol
    shr cx,1
    shr cx,1
    shr cx,1
    mov firstcol,cx
    mov dx,lastcol
    add dx,7
    shr dx,1
    shr dx,1
    shr dx,1
    mov lastcol,dx
    mov outrows,1
TOutput_render:
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp dirty,0
    je TOutput_done
    ; Preserve the actual renderer result and all post-render GPRs.
    push ax
    push bx
    push cx
    push dx
    cmp outrows,0
    je TOutput_full
    mov ax,firstrow
    mov bx,lastrow
    mov cx,firstcol
    mov dx,lastcol
    call FlushRetainColumns
    jmp short TOutput_flushed
TOutput_full:
    call FlushShadow
TOutput_flushed:
    pop dx
    pop cx
    pop bx
    pop ax
TOutput_done:
cEnd

""")

def transform(source, mode="640x200x4"):
    if mode not in EXPECTED or hashlib.sha256(source).hexdigest() != EXPECTED[mode]:
        raise ValueError("Output bounds require the exact accepted TR5 source stage for " + mode)
    text = source.decode("latin1")
    if text.count(OLD_GATE) != 1:
        raise ValueError("Output gate anchor does not match exactly once")
    result = text.replace(OLD_GATE, NEW_GATE).encode("latin1")
    if b"\n" in result.replace(b"\r\n", b""):
        raise ValueError("DOS source must retain CRLF")
    return result

def port(renderer, mode):
    if mode not in EXPECTED:
        return {"changed": False, "mode": mode}
    path = Path(renderer) / "EGA" / "TSOFT.ASM"
    path.write_bytes(transform(path.read_bytes(), mode))
    return {"changed": True, "mode": mode, "added_data_bytes": 0, "extra_local_stack_bytes": 4, "extra_flush_save_bytes": 4}
