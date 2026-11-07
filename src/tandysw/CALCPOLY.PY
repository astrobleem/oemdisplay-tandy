#!/usr/bin/env python3
"""Bound thin multi-point polyline copies after CALCFAST, without renderer edits."""
from pathlib import Path
import hashlib
import importlib.machinery

HERE = Path(__file__).resolve().parent
MODES = ('320x200x16', '640x200x4', '160x200x16', '320x200x4', '640x200x2')


def module(name):
    return importlib.machinery.SourceFileLoader(
        'calcpoly_' + name, str(HERE / (name + '.PY'))).load_module()

VALIDATION = """    les di,points
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
"""

CHANGES = (
    ("""TOutput_thin_count:
    cmp style,18
    or_require je,TOutput_render
    cmp count,2
    or_require je,TOutput_render
TOutput_style_ok:
""", """TOutput_thin_count:
    cmp style,18
    or_require je,TOutput_render
    cmp count,2
    or_require jae,TOutput_render
    cmp count,64
    or_require jbe,TOutput_render
TOutput_style_ok:
"""),
    ("""TOutput_polyline:
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
""", """TOutput_polyline:
    ; CALCPOLY: every point is in screen; adjacent duplicates fall back.
    ; Keep original segment rendering, clipping, style state, and row copier.
    mov cx,count
    mov firstrow,SCREEN_HEIGHT
    mov lastrow,0
TOutput_poly_point:
    mov dx,es:[di]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp cx,count
    je TOutput_poly_unique
    cmp dx,es:[di-4]
    jne TOutput_poly_unique
    cmp ax,es:[di-2]
    or_require jne,TOutput_render
TOutput_poly_unique:
    cmp ax,firstrow
    jae TOutput_poly_min_done
    mov firstrow,ax
TOutput_poly_min_done:
    cmp ax,lastrow
    jbe TOutput_poly_max_done
    mov lastrow,ax
TOutput_poly_max_done:
    add di,4
    loop TOutput_poly_point
    inc lastrow
"""),
)


def port(renderer, mode, repo):
    renderer, repo = Path(renderer), Path(repo)
    if mode not in MODES:
        raise ValueError('CALCPOLY: unsupported mode ' + str(mode))
    fast = module('CALCFAST')
    fast.validate_dispatch(renderer, repo)
    rows = module('OUTROWS')
    # These are the existing accepted renderer checks, not new report output.
    for name, expected in rows.RENDERER_PINS.items():
        if hashlib.sha256(rows.normalized(renderer / name).encode('latin1')).hexdigest() != expected:
            raise ValueError('CALCPOLY: renderer changed: ' + name)
    path = renderer / 'EGA/TSOFT.ASM'
    source = fast.normalized(path)
    if source.count(VALIDATION) != 1:
        raise ValueError('CALCPOLY: existing validation changed')
    # Require the complete prior CALCFAST result, then verify that undoing it
    # gives a source to which its original one-time edits apply unambiguously.
    inverse = source
    for old, new, count in reversed(fast.CHANGES):
        if inverse.count(new) != count:
            raise ValueError('CALCPOLY: expected CALCFAST candidate')
        inverse = inverse.replace(new, old)
    for old, new, count in fast.CHANGES:
        if inverse.count(old) != count:
            raise ValueError('CALCPOLY: changed CALCFAST anchors')
        inverse = inverse.replace(old, new)
    if inverse != source:
        raise ValueError('CALCPOLY: CALCFAST inverse differs')
    for old, new in CHANGES:
        if source.count(old) != 1:
            raise ValueError('CALCPOLY: changed or already applied anchor')
        source = source.replace(old, new)
    path.write_bytes(source.replace('\n', '\r\n').encode('latin1'))
