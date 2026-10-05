#!/usr/bin/env python3
"""Exact-pinned Trial7 short raster-label byte bounds over the Trial6 text path.

Accepts a separately transformed TOutput wrapper so BORDER7 composes cleanly.
Rendering, font metrics, clipping, return values and Trial5/6 helpers stay exact.
Only the staged text macros/wrapper locals are changed. No global state.
"""
from pathlib import Path
import hashlib

EXPECTED = {'320x200x16': '0ddc0c9eef347a8114a6cf8adcb14ae0c55f0542ec60e835d44247cc875b8ffd', '160x200x16': '71ee7068bee439a050e83f5e460e85e485956de4485d7d7aa74790f7f3620960', '320x200x4': 'fd8e2659d89e8d7caa5c81225d21da806825b1ace0f74b7ae98eebfb8864a920', '640x200x4': '4cfe58a42aa50f030f98330dfa8749f569a4926034e832ed0a9daa2d6a82ee21', '640x200x2': '71ac229a9867610eb67cb2cdecc6997f1e5342d29ba2187878851b302042e64f'}

RENDERER_PINS = {'320x200x16': {'RLSTRBLT.ASM': '91852c72510867b5316c3ca75f6f39fa106b607470ce7113b9f3891241f8406b', 'RLBLDSTR.ASM': 'e5b55a1f436d71acc48433f8e6c66b9fe8e5074543b73e21baf864af5147a1bd', 'REALFIX.ASM': '1e3147c562b7030d6604e91bac8ace22f930042eda55550ad5886f212a704eaa', 'REALPRO.ASM': 'dd37d57d044d5deeecf39546a272dc0c68dcb1c6a0f634568423c24afaa63377', 'RLSTRBLT.INC': '22f742fc5e7acd5fdb208776217d86cb7ef50f7275a6139cf6c64217fa1f3252', 'RLFNTSEG.INC': 'fa96a66f89f307fa675674e4a422dacd19751ae7cb07c711c1cdd34dd904a73d', 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a', 'EGA/TCURSOR.ASM': 'f3db33bf3b15237bb2baa378edd3b41831b08355a5d85ac09d9470915e64fc1e'}, '160x200x16': {'RLSTRBLT.ASM': '91852c72510867b5316c3ca75f6f39fa106b607470ce7113b9f3891241f8406b', 'RLBLDSTR.ASM': 'e5b55a1f436d71acc48433f8e6c66b9fe8e5074543b73e21baf864af5147a1bd', 'REALFIX.ASM': '1e3147c562b7030d6604e91bac8ace22f930042eda55550ad5886f212a704eaa', 'REALPRO.ASM': 'dd37d57d044d5deeecf39546a272dc0c68dcb1c6a0f634568423c24afaa63377', 'RLSTRBLT.INC': '22f742fc5e7acd5fdb208776217d86cb7ef50f7275a6139cf6c64217fa1f3252', 'RLFNTSEG.INC': 'fa96a66f89f307fa675674e4a422dacd19751ae7cb07c711c1cdd34dd904a73d', 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a', 'EGA/TCURSOR.ASM': '6ca256ce21fa6215d50a6bc23bd316c4b15c2eceaf1f8136165eec6fe4437bae'}, '320x200x4': {'RLSTRBLT.ASM': '91852c72510867b5316c3ca75f6f39fa106b607470ce7113b9f3891241f8406b', 'RLBLDSTR.ASM': 'e5b55a1f436d71acc48433f8e6c66b9fe8e5074543b73e21baf864af5147a1bd', 'REALFIX.ASM': '1e3147c562b7030d6604e91bac8ace22f930042eda55550ad5886f212a704eaa', 'REALPRO.ASM': 'dd37d57d044d5deeecf39546a272dc0c68dcb1c6a0f634568423c24afaa63377', 'RLSTRBLT.INC': '22f742fc5e7acd5fdb208776217d86cb7ef50f7275a6139cf6c64217fa1f3252', 'RLFNTSEG.INC': 'fa96a66f89f307fa675674e4a422dacd19751ae7cb07c711c1cdd34dd904a73d', 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a', 'EGA/TCURSOR.ASM': '7cd0588f809a4d6c7de3030656bff83b45debdfc948da0710de3c6407d8b30e0'}, '640x200x4': {'RLSTRBLT.ASM': '91852c72510867b5316c3ca75f6f39fa106b607470ce7113b9f3891241f8406b', 'RLBLDSTR.ASM': 'e5b55a1f436d71acc48433f8e6c66b9fe8e5074543b73e21baf864af5147a1bd', 'REALFIX.ASM': '1e3147c562b7030d6604e91bac8ace22f930042eda55550ad5886f212a704eaa', 'REALPRO.ASM': 'dd37d57d044d5deeecf39546a272dc0c68dcb1c6a0f634568423c24afaa63377', 'RLSTRBLT.INC': '22f742fc5e7acd5fdb208776217d86cb7ef50f7275a6139cf6c64217fa1f3252', 'RLFNTSEG.INC': 'fa96a66f89f307fa675674e4a422dacd19751ae7cb07c711c1cdd34dd904a73d', 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a', 'EGA/TCURSOR.ASM': '250d616dd39ca21708701cac6e009ebfcbac977ed179c4ce19ec984865756aaf'}, '640x200x2': {'RLSTRBLT.ASM': '91852c72510867b5316c3ca75f6f39fa106b607470ce7113b9f3891241f8406b', 'RLBLDSTR.ASM': 'e5b55a1f436d71acc48433f8e6c66b9fe8e5074543b73e21baf864af5147a1bd', 'REALFIX.ASM': '1e3147c562b7030d6604e91bac8ace22f930042eda55550ad5886f212a704eaa', 'REALPRO.ASM': 'dd37d57d044d5deeecf39546a272dc0c68dcb1c6a0f634568423c24afaa63377', 'RLSTRBLT.INC': '22f742fc5e7acd5fdb208776217d86cb7ef50f7275a6139cf6c64217fa1f3252', 'RLFNTSEG.INC': 'fa96a66f89f307fa675674e4a422dacd19751ae7cb07c711c1cdd34dd904a73d', 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a', 'EGA/TCURSOR.ASM': '4a504c3b2300a28bcb2a939f1eaeb6fbb67ba93a4d6e3303f0e0cc0109054278'}}

def normalized(path):
    return Path(path).read_bytes().replace(b'\r\n',b'\n').replace(b'\x1a',b'').decode('latin1')


def sha(text):
    return hashlib.sha256(text.encode('latin1')).hexdigest()


def once(text,old,new):
    if text.count(old)!=1:
        raise RuntimeError('TEXT7 exact anchor mismatch: '+repr(old))
    return text.replace(old,new)


def without_output(text):
    a=text.index('cProc TOutput,');b=text.index('cProc TPixel,',a)
    return text[:a]+'; TOutput is separately owned by BORDER7.\n'+text[b:]


COLUMNS = r'''; TEXT7: bounded short raster labels. dirty=3 carries byte columns;
; dirty=2 keeps the proven Trial6 row interval, all other states are unchanged.
; Validate every width used by the pinned renderer rather than trusting only
; fsMaxWidth. No glyph/string/header can alias writable canonical shadow RAM.
; Font bits may live elsewhere: pixels cannot increase the validated advance.
; No width vector, justification, negative origin, decoration or transforms.
.errnz PROP_WIDTH
.errnz PROP_OFFSET-2
.errnz (offset fsPixWidth)-(offset fsType)-dfPixWidth
.errnz (offset fsMaxWidth)-(offset fsType)-dfMaxWidth
.errnz (offset fsFirstChar)-(offset fsType)-dfFirstChar
.errnz (offset fsCharOffset)-118
.errnz CharExtra-22
.errnz TBreakExtra-12

text_columns macro extended,optr,opts
local finished,restore,font_width_ok,scan_char,valid_char,columns_ready
local opaque_left_ok,opaque_right_ok
    pushf
    cmp dirty,2
    text_require je,finished
    cmp count,64
    text_require jbe,finished
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    if extended
    mov ax,word ptr dxs
    or ax,word ptr dxs+2
    text_require jz,restore
    endif
    ; Reuse the exact Trial5 20-bit/no-shadow-alias span gate. Reject before
    ; reading any new metadata. Existing row validation already ran above.
    les di,mode
    mov cx,size DRAWMODE
    call ORowsSpanSafe
    text_require jnc,restore
    cmp word ptr es:[di].TBreakExtra,0
    text_require je,restore
    cmp word ptr es:[di].CharExtra,0
    text_require je,restore
    les di,xform
    mov cx,size TEXTXFORM
    call ORowsSpanSafe
    text_require jnc,restore
    les di,clip
    mov cx,size RECT
    call ORowsSpanSafe
    text_require jnc,restore
    les di,string
    mov cx,count
    call ORowsSpanSafe
    text_require jnc,restore
    les di,font
    xor di,di
    mov cx,offset fsCharOffset
    call ORowsSpanSafe
    text_require jnc,restore
    ; Include every table entry and the renderer's sentinel in the span.
    xor ax,ax
    mov al,es:fsLastChar
    sub al,es:fsFirstChar
    text_require jnc,restore
    cmp es:fsDefaultChar,al
    text_require jbe,restore
    mov cx,ax
    add cx,2
    shl cx,1
    shl cx,1
    add cx,offset fsCharOffset
    call ORowsSpanSafe
    text_require jnc,restore
    mov dx,es:fsMaxWidth
    or dx,dx
    text_require jg,restore
    cmp dx,SCREEN_WIDTH
    text_require jbe,restore
    ; Fixed-pitch advance and every actual table width must fit maxWidth.
    cmp es:fsPixWidth,dx
    text_require jbe,restore
    lds si,string
    mov cx,count
scan_char:
    mov bl,[si]
    inc si
    sub bl,es:fsFirstChar
    mov al,es:fsLastChar
    sub al,es:fsFirstChar
    cmp bl,al
    jbe valid_char
    mov bl,es:fsDefaultChar
valid_char:
    xor bh,bh
    shl bx,1
    shl bx,1
    mov ax,word ptr es:fsCharOffset[bx][PROP_WIDTH]
    cmp ax,dx
    text_require jbe,restore
    loop scan_char
    mov ax,dx
    mul count
    or dx,dx
    text_require jz,restore
    mov bx,x
    or bx,bx
    text_require jns,restore
    add ax,bx
    text_require jnc,restore
    cmp ax,SCREEN_WIDTH
    text_require jbe,restore
    mov colfirst,bx
    mov collast,ax
    if extended
    ; The explicit opaque fill may extend outside the text. Include its
    ; entire validated rectangle; the exact renderer still performs clipping.
    test opts,ETO_OPAQUE_FILL
    jz columns_ready
    les di,optr
    mov cx,size RECT
    call ORowsSpanSafe
    text_require jnc,restore
    mov ax,es:[di].left
    cmp colfirst,ax
    jle opaque_left_ok
    mov colfirst,ax
opaque_left_ok:
    mov ax,es:[di].right
    cmp collast,ax
    jge opaque_right_ok
    mov collast,ax
opaque_right_ok:
    endif
columns_ready:
    mov cx,colfirst
    mov dx,collast
    add dx,7
    shr cx,1
    shr cx,1
    shr cx,1
    shr dx,1
    shr dx,1
    shr dx,1
    mov colfirst,cx
    mov collast,dx
    mov dirty,3
restore:
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
finished:
    popf
endm

'''

FLUSH = r'''text_flush macro
local full,rows,done
    push ax
    push bx
    push cx
    push dx
    cmp dirty,3
    jne rows
    mov ax,rowfirst
    mov bx,rowlast
    mov cx,colfirst
    mov dx,collast
    call FlushRetainColumns
    jmp short done
 rows:
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    call FlushRetainRows
    jmp short done
 full:
    call FlushShadow
 done:
    pop dx
    pop cx
    pop bx
    pop ax
endm

'''


def transform(text):
    begin=text.index('text_flush macro\n')
    end=text.index('cProc TStrBlt,',begin)
    old_flush=text[begin:end]
    old_locals='    localW rowfirst\n    localW rowlast\n'
    new_locals=old_locals+'    localW colfirst\n    localW collast\n'
    if text.count(old_locals)!=2:
        raise RuntimeError('TEXT7 expected exactly two private text frames')
    text=text[:begin]+COLUMNS+FLUSH+text[end:]
    text=text.replace(old_locals,new_locals)
    for form in ('0,0,0','1,opaquerect,options'):
        text=once(text,'    text_bounds '+form+'\n',
                  '    text_bounds '+form+'\n    text_columns '+form+'\n')
    # Remove every owned change and demand exact reconstruction.
    inverse=text.replace(new_locals,old_locals)
    for form in ('0,0,0','1,opaquerect,options'):
        inverse=once(inverse,'    text_columns '+form+'\n','')
    inverse=once(inverse,COLUMNS+FLUSH,old_flush)
    return text,inverse


def port(renderer,mode):
    renderer=Path(renderer);path=renderer/'EGA/TSOFT.ASM'
    original=normalized(path)
    if mode not in EXPECTED or sha(without_output(original))!=EXPECTED[mode]:
        raise RuntimeError('TEXT7 requires exact Trial6 core outside the independent TOutput wrapper')
    for name,digest in RENDERER_PINS[mode].items():
        if sha(normalized(renderer/name))!=digest:
            raise RuntimeError('TEXT7 pinned raster/cursor source changed: '+name)
    text,inverse=transform(original)
    if inverse!=original:
        raise RuntimeError('TEXT7 inverse scope failure')
    path.write_bytes(text.replace('\n','\r\n').encode('latin1'))
    return {'feature':'bounded short raster-label byte columns and retained text cursor',
            'mode':mode,'changed_staged_files':['EGA/TSOFT.ASM'],
            'input_normalized_sha256':sha(original),'output_normalized_sha256':sha(text),
            'input_core_without_independent_TOutput_sha256':EXPECTED[mode],
            'inverse_scope':'EXACT_INPUT',
            'gate':'exact Trial6 row gate; 1..64 chars; null dx; zero total break and char extra; stable non-shadow descriptors/string/font table; each glyph and fixed advance <= positive maxWidth; on-screen x..x+count*maxWidth; include explicit opaque fill',
            'bounds':'original proven rows; floor(left/8)..ceil(right/8), conservative maxWidth*count plus opaque rectangle union',
            'fallback':'retained full rows for the original row gate; unchanged full-frame refresh otherwise',
            'preserved':'all renderer calls/arguments/results, text metrics and clipping, Trial5/6 conversion and cursor helpers, DIB paths, allocations and independent TOutput wrapper',
            'new_memory':'four private stack bytes in each text wrapper; no persistent state',
            'runtime':'NOT_TESTED','physical_hardware':'NOT_TESTED'}
