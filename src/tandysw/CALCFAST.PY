#!/usr/bin/env python3
"""Apply the tested Calculator copy reductions after WIDESCAN.

Only the staged EGA/TSOFT.ASM is written. All validation and transformation
finish in memory before that write. No build, publication, or report output.
"""
from pathlib import Path
import re

MODES = ('320x200x16', '640x200x4', '160x200x16', '320x200x4', '640x200x2')


def normalized(path):
    return Path(path).read_bytes().replace(b'\r\n', b'\n').decode('latin1')


def semantic(source):
    return '\n'.join(''.join(line.split(';', 1)[0].split()).lower()
                     for line in source.splitlines()
                     if line.split(';', 1)[0].strip())

EXPECTED_OUTPUT = """page,132
incoutput=1
.xlist
includecmacros.inc
includegdidefs.inc
includemacros.inc
includemflags.inc
.list
??_outoutput
externfpdo_scanlines
externfpdo_polylines
sbegincode
assumescs,code
page
assumesds,data
assumeses,nothing
cprocoutput,<far,public,win,pascal>,<si,di>
parmdlp_dst_dev
parmwstyle
parmwcount
parmdlp_points
parmdlp_phys_pen
parmdlp_phys_brush
parmdlp_draw_mode
parmdlp_clip_rect
cbegin<nogen>
movbx,sp
movax,wptrss:[bx][26]
cmpax,os_polyline
jeshortdispatch_lines
cmpax,os_scanlines
jneshortoutput_return_error
dispatch_scanlines:
jmpdo_scanlines
dispatch_lines:
jmpdo_polylines
output_return_error:
xorax,ax
decax
ret28
cend<nogen>
sendcode
ifmasmflagsandpubdefs
publicdispatch_scanlines
publicdispatch_lines
publicoutput_return_error
endif
end"""

CHANGES = (
    ("""    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp dirty,0
""", """    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    ; Unsupported Output styles return -1 without drawing in the exact renderer.
    ; Keep the renderer call and result; skip only the redundant hardware copy.
    pushf
    cmp style,18
    je short TOutput_draw_style
    cmp style,4
    je short TOutput_draw_style
    popf
    jmp TOutput_done
TOutput_draw_style:
    popf
    cmp dirty,0
""", 1),
    ("""    text_rectangle clip,restore
    ; Prove signed y+h cannot overflow and is wholly on screen.
""", """    text_rectangle clip,restore
    ; Original clip bounds contain both glyph writes and clipped opaque fills.
    ; Snapshot while ES:DI still names clip; later validation may load optr.
    ; Bounds are nonnegative and <=SCREEN_WIDTH (at most 640 pixels).
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
""", 1),
    ("""    localW rowfirst
    localW rowlast
cBegin
""", """    localW rowfirst
    localW rowlast
    localW colfirst
    localW collast
cBegin
""", 2),
    ("""text_flush macro
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
""", """text_flush macro
local full,done
    pushf
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
    popf
endm
""", 1),
    ("""; dirty=0 means no flush, 1 full flush, and 2 proven full-width row interval.""", """; dirty=0 means no flush, 1 full flush, and 2 proven row/clip-column bounds.""", 1),
)


def validate_dispatch(renderer, repo):
    # Match every non-comment token, including prologue and directives, so a
    # new dispatch case, a changed fallback, or an injected side effect fails.
    if semantic(normalized(renderer / 'OUTPUT.ASM')) != EXPECTED_OUTPUT:
        raise ValueError('CALCFAST: Output dispatcher semantics changed')
    definitions = normalized(repo / 'DDK/286/INC/GDIDEFS.INC')
    definitions = '\n'.join(line.split(';', 1)[0] for line in definitions.splitlines())
    for name, expected in (('OS_POLYLINE', '18'), ('OS_SCANLINES', '4')):
        asm = re.findall(r'^\s*' + name + r'\s+equ\s+(.*?)\s*$', definitions, re.M | re.I)
        c = re.findall(r'^\s*#define\s+' + name + r'\s+(.*?)\s*$', definitions, re.M | re.I)
        if asm != [expected] or c != [expected]:
            raise ValueError('CALCFAST: unexpected numeric definition for ' + name)


def port(renderer, mode, repo):
    """Return None after applying both changes once to a supported staged mode."""
    renderer, repo = Path(renderer), Path(repo)
    if mode not in MODES:
        raise ValueError('CALCFAST: unsupported mode ' + str(mode))
    validate_dispatch(renderer, repo)
    path = renderer / 'EGA/TSOFT.ASM'
    source = normalized(path)
    for old, new, count in CHANGES:
        if source.count(old) != count:
            raise ValueError('CALCFAST: changed or already patched wrapper: ' + repr(old[:70]))
        source = source.replace(old, new)
    path.write_bytes(source.replace('\n', '\r\n').encode('latin1'))
