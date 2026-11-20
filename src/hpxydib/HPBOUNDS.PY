"""Synchronous Output/text columns over the exact historical HPXY source stage."""
from pathlib import Path
import hashlib

SOURCE_SHA256 = "43e7e2c9a9404396fccd72cb9d04b4074fa260425425d675cc301696ac3673c3"


def _dos(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n")

OUTPUT_EDITS = (
    (_dos("""    localW lastrow
cBegin
    mov dirty,0
    mov outrows,0"""), _dos("""    localW lastrow
    localW firstcol
    localW lastcol
cBegin
    mov dirty,0
    mov outrows,0"""), 1),
    (_dos("""TOutput_objects_ok:
    les di,points"""), _dos("""TOutput_objects_ok:
    ; Capture a conservative pixel X interval before converting to byte columns.
    mov firstcol,SCREEN_WIDTH
    mov lastcol,0
    les di,points"""), 1),
    (_dos("""    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    loop TOutput_scan_interval"""), _dos("""    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    cmp bx,firstcol
    jae TOutput_scan_notleft
    mov firstcol,bx
TOutput_scan_notleft:
    cmp dx,lastcol
    jbe TOutput_scan_notright
    mov lastcol,dx
TOutput_scan_notright:
    loop TOutput_scan_interval"""), 1),
    (_dos("""TOutput_poly_point:
    mov dx,es:[di]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov dx,es:[di+2]"""), _dos("""TOutput_poly_point:
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
    mov dx,es:[di+2]"""), 1),
    (_dos("""    mov lastrow,bx
    jmp TOutput_bounded
TOutput_two_point:"""), _dos("""    mov lastrow,bx
    inc lastcol               ; point maximum was inclusive
    jmp TOutput_bounded
TOutput_two_point:"""), 1),
    (_dos("""    mov lastrow,bx
TOutput_bounded:
    mov outrows,1"""), _dos("""    mov lastrow,bx
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
    mov outrows,1"""), 1),
    (_dos("""    ; Preserve the actual renderer result and all post-render GPRs.
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
TOutput_done:"""), _dos("""    ; Preserve the actual renderer result and all post-render GPRs.
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
TOutput_done:"""), 1),
    (_dos("""; WIDESCAN: bounded scan lists only. Thin-line gate stays count=2."""), _dos("""; Bounded scan lists and validated thin polylines; all other calls stay FULL."""), 1),
)

TEXT_EDITS = (
    (_dos("""; Snapshot only final row endpoints before the unchanged renderer call.
; dirty=0 means no flush, 1 full flush, and 2 proven full-width row interval.
; The last three macro arguments are explicit even for ordinary StrBlt.
"""), _dos("""; Snapshot final row endpoints and the original clip's byte columns.
; dirty=0 means no flush, 1 full flush, and 2 proven bounded presentation.
; All original text gates and renderer calls remain unchanged.
; The last three macro arguments are explicit even for ordinary StrBlt.
"""), 1),
    (_dos("""    text_rectangle clip,restore
    ; Prove signed y+h cannot overflow and is wholly on screen.
"""), _dos("""    text_rectangle clip,restore
    ; TEXTCOL: get_clip confines glyphs and any opaque fill to this RECT.
    ; Capture X now, before an optional opaque RECT replaces ES:DI.
    ; Round outward to complete logical bytes; empty clips remain safe.
    mov ax,es:[di].left
    shr ax,1
    shr ax,1
    shr ax,1
    mov colfirst,ax
    mov ax,es:[di].right
    add ax,7
    shr ax,1
    shr ax,1
    shr ax,1
    mov collast,ax
    ; Prove signed y+h cannot overflow and is wholly on screen.
"""), 1),
    (_dos("""    localW rowfirst
    localW rowlast
cBegin
"""), _dos("""    localW rowfirst
    localW rowlast
    localW colfirst
    localW collast
cBegin
"""), 2),
    (_dos("""text_flush macro
local full,done
    push ax
    push bx
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    call FlushRows
    jmp short done
 full:
    call FlushShadow
 done:
    pop bx
    pop ax
endm
"""), _dos("""text_flush macro
local full,done
    push ax
    push bx
    push cx
    push dx
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    mov cx,colfirst
    mov dx,collast
    call FlushRetainColumns
    jmp short done
 full:
    call FlushShadow
 done:
    pop dx
    pop cx
    pop bx
    pop ax
endm
"""), 1),
)


def _crlf(source):
    if b"\n" in source.replace(b"\r\n", b"") or b"\r" in source.replace(b"\r\n", b""):
        raise ValueError("HPXY source must retain CRLF")


def transform(source, output=True, text=True):
    """Return source only; the caller owns separate native qualification."""
    _crlf(source)
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError("HPXY bounds require the exact historical baseline stage")
    edits = (OUTPUT_EDITS if output else ()) + (TEXT_EDITS if text else ())
    candidate = source.decode("latin1")
    for old, new, count in edits:
        if candidate.count(old) != count or new in candidate:
            raise ValueError("HPXY bounds anchor mismatch: " + old.splitlines()[0])
        candidate = candidate.replace(old, new)
    result = candidate.encode("latin1")
    _crlf(result)
    inverse = candidate
    for old, new, count in reversed(edits):
        if inverse.count(new) != count:
            raise ValueError("HPXY bounds inverse mismatch")
        inverse = inverse.replace(new, old)
    if inverse.encode("latin1") != source:
        raise ValueError("HPXY bounds changed source outside the bounded replacements")
    original = source.decode("latin1")
    for start, end in (("ORowsSpanSafe proc near", "ORowsSpanSafe endp"),
                       ("FlushColumns proc near", "FlushColumns endp"),
                       ("xy_row proc near", "xy_row endp")):
        before = original[original.index(start):original.index(end)+len(end)]
        after = candidate[candidate.index(start):candidate.index(end)+len(end)]
        if before != after:
            raise ValueError("HPXY bounds changed a protected procedure")
    return result


def port(renderer, output=True, text=True):
    path = Path(renderer) / "EGA" / "TSOFT.ASM"
    source = path.read_bytes()
    result = transform(source, output=output, text=text)
    path.write_bytes(result)
    return {"output_columns": output, "text_columns": text,
            "added_data_bytes": 0, "extra_local_stack_bytes_per_wrapper": 4}


def selftest(source):
    combined = transform(source)
    for output, text in ((True, False), (False, True), (False, False)):
        transform(source, output=output, text=text)
    for bad in (combined, source + b"; changed\r\n", source.replace(b"\r\n", b"\n")):
        try:
            transform(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong source unexpectedly accepted")
    return {"inverse": True, "protected_procedures": True,
            "variants": 4, "wrong_source_rejections": 3}
